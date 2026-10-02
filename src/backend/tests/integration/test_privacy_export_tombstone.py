"""#1793 part 1 — Art. 15 reaches the rows a tenant deletion pseudonymised (REQ-025 §3.1.2 rule 6, AK-DE-01).

A tenant deletion keeps the tenant's R-16..R-18 rows and rewrites every account
key on them to that account's tombstone hash (NFR-011 §2.3). A member whose own
account still exists remains the data subject of those rows, but the walk keyed
only on ``*_by_key`` inside the subject's current tenants — and the subject is a
member of no tenant that no longer exists — so the rows fell out of the
disclosure the moment their tenant was deleted.

The state is produced the production way: the tenant is erased by
``TenantService.erase_personal_tenant_of`` (the real executor writes the
tombstones), and the bundle is built by ``PrivacyService.process_data_export``
over the real repository and read back through ``open_export_bundle``.

No personal data: every value is synthetic.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.data_export_repository import ArangoDataExportRepository
from app.data_access.arango.personal_data_repository import ArangoPersonalDataRepository
from app.data_access.storage.local_fs_adapter import LocalFsStorageAdapter
from app.domain.engines.consent_engine import ConsentEngine
from app.domain.engines.data_export_engine import DataExportEngine
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.models.privacy import DataExportRequest
from app.domain.services.privacy_service import PrivacyService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name
from tests.support.tenant_erasure_wiring import tenant_erasure_service

TEST_DATABASE = run_database_name("privacy_export_tombstone")
SALT = "export-tombstone-salt-not-a-secret-012345"
SUBJECT = "subject-ts1"
OTHER = "other-ts1"
ERASED = "t-gone"
LIVING = "t-alive"
FOREIGN = "t-foreign"

pytestmark = pytest.mark.usefixtures("arango_db")


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    col.ensure_collections(db)
    yield db
    system.delete_database(TEST_DATABASE)


def _rows(database, tenant: str, owner: str, marker: str) -> None:
    """One row of each retained category, keyed to *owner*, carrying *marker* in ``notes``."""
    batch = database.collection(col.HARVEST_BATCHES).insert(
        {
            "tenant_key": tenant,
            "harvested_by_key": owner,
            "harvester": "Display name",
            "harvest_date": "2025-06-01T08:00:00Z",
            "notes": f"{marker}-harvest",
        }
    )
    database.collection(col.QUALITY_ASSESSMENTS).insert(
        {"batch_key": batch["_key"], "assessed_by_key": owner, "notes": f"{marker}-quality"}
    )
    database.collection(col.TREATMENT_APPLICATIONS).insert(
        {
            "tenant_key": tenant,
            "applied_by_key": owner,
            "applied_at": "2025-06-01T08:00:00Z",
            "notes": f"{marker}-treatment",
        }
    )
    database.collection(col.INSPECTIONS).insert(
        {
            "tenant_key": tenant,
            "inspected_by_key": owner,
            "inspected_at": "2025-06-01T08:00:00Z",
            "notes": f"{marker}-inspection",
        }
    )


@pytest.fixture(scope="module")
def world(database):
    database.collection(col.USERS).insert({"_key": SUBJECT, "email": "subject@example.invalid", "display_name": "S"})
    database.collection(col.TENANTS).insert(
        {
            "_key": ERASED,
            "name": "Garden",
            "slug": ERASED,
            "tenant_type": "personal",
            "owner_user_key": SUBJECT,
            "is_active": True,
        }
    )
    database.collection(col.TENANTS).insert(
        {"_key": LIVING, "name": "Alive", "slug": LIVING, "tenant_type": "organization"}
    )
    database.collection(col.TENANTS).insert(
        {"_key": FOREIGN, "name": "Foreign", "slug": FOREIGN, "tenant_type": "organization"}
    )
    _rows(database, ERASED, SUBJECT, "erased")
    _rows(database, ERASED, OTHER, "other")
    _rows(database, LIVING, SUBJECT, "living")
    # The subject's tombstone on a row of a tenant that still exists and that the
    # subject is no member of: no tenant deletion wrote it, so it is not theirs to see.
    tombstone = ErasureEngine.compute_tombstone_hash(SUBJECT, SALT)
    _rows(database, FOREIGN, tombstone, "planted")

    outcome = tenant_erasure_service(database, SALT).erase_personal_tenant_of(
        SUBJECT, ERASED, now=datetime(2026, 9, 1, tzinfo=UTC)
    )
    assert outcome.outcome == "erased"
    assert database.collection(col.HARVEST_BATCHES).find({"harvested_by_key": tombstone}).count() == 2


def _service(database, storage_root, member_of: list[str]) -> tuple[PrivacyService, ArangoDataExportRepository]:
    export_repo = ArangoDataExportRepository(database)
    membership_repo = MagicMock()
    membership_repo.list_by_user.return_value = [MagicMock(tenant_key=t) for t in member_of]
    storage = LocalFsStorageAdapter(
        root=str(storage_root),
        public_base_url="https://storage.test",
        signing_secret="x" * 48,
        max_object_size_bytes=64 * 1024 * 1024,
    )
    service = PrivacyService(
        export_repo=export_repo,
        consent_repo=MagicMock(),
        restriction_repo=MagicMock(),
        erasure_repo=MagicMock(),
        email_change_repo=MagicMock(),
        user_repo=MagicMock(),
        refresh_token_repo=MagicMock(),
        data_export_engine=DataExportEngine(),
        erasure_engine=ErasureEngine(),
        consent_engine=ConsentEngine(),
        password_engine=MagicMock(),
        token_engine=MagicMock(),
        email_service=MagicMock(),
        frontend_url="https://app.test",
        storage_adapter=storage,
        membership_repo=membership_repo,
        personal_data_repo=ArangoPersonalDataRepository(database),
        tombstone_salt=SALT,
    )
    return service, export_repo


async def _delivered(database, tmp_path, member_of: list[str]) -> set[str]:
    service, export_repo = _service(database, tmp_path / "objects", member_of)
    created = export_repo.create(DataExportRequest(user_key=SUBJECT, status="pending"))
    await service.process_data_export(created.key)
    _, stream = await service.open_export_bundle(SUBJECT, created.key)
    bundle = json.loads(b"".join([chunk async for chunk in stream]).decode("utf-8"))
    return {str(value) for section in bundle["sections"] for row in section["records"] for value in row.values()}


RETAINED = ("harvest", "quality", "treatment", "inspection")


@pytest.mark.asyncio
async def test_a_member_of_the_deleted_tenant_still_receives_its_retained_rows(database, world, tmp_path):
    delivered = await _delivered(database, tmp_path, member_of=[LIVING])

    assert {f"erased-{kind}" for kind in RETAINED} <= delivered
    assert {f"living-{kind}" for kind in RETAINED} <= delivered, "precondition: the keyed walk still works"


@pytest.mark.asyncio
async def test_a_subject_left_without_any_tenant_still_receives_them(database, world, tmp_path):
    """The deleted tenant was the subject's only one: no membership remains, and the rows are still theirs."""
    delivered = await _delivered(database, tmp_path, member_of=[])

    assert {f"erased-{kind}" for kind in RETAINED} <= delivered


@pytest.mark.asyncio
async def test_nobody_elses_rows_and_no_planted_tombstone_are_delivered(database, world, tmp_path):
    delivered = await _delivered(database, tmp_path, member_of=[LIVING])

    assert not {f"other-{kind}" for kind in RETAINED} & delivered
    # ``quality_assessments`` carries no tenant key, so only the tenant-bearing rows are bound to a gone tenant.
    assert not {f"planted-{kind}" for kind in ("harvest", "treatment", "inspection")} & delivered
