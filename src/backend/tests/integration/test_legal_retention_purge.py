"""#1789 / #1793 — NFR-011 R-16/R-17/R-18 and R-06a purges against a real ArangoDB.

The rows R-16 (harvest, CanG), R-17 (treatments, PflSchG) and R-18 (inspections)
keep survive a tenant deletion pseudonymised (NFR-011 §2.3, Q-R1/Q-R2). Until
#1789 nothing removed them once their period had run out, and until #1793 nothing
removed the ``tenant_erasure_records`` proof either (R-06a).

The path is the production one end to end: the tenant is erased by
``TenantService.erase_personal_tenant_of`` (the account-erasure entry of the
tenant-erasure inventory, #1788), and the purges run through the
``PrivacyService`` methods the beat tasks call, over the real repositories. Only
the clock is supplied.

No personal data: every value is synthetic.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.legal_retention_repository import ArangoLegalRetentionRepository
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.engines.tenant_erasure_engine import TenantErasureEngine
from app.domain.services.privacy_service import PrivacyService
from app.domain.services.retention_service import RetentionService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name
from tests.support.tenant_erasure_wiring import tenant_erasure_service

TEST_DATABASE = run_database_name("legal_retention_purge")
SALT = "legal-retention-salt-not-a-secret-0123456"
MEMBER = "member-lr1"
ERASED = "t-erased"
EMPTY = "t-erased-empty"
LIVING = "t-living"
#: The tenant is erased on this day; the rows' dates lie before it.
ERASED_AT = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
#: The first purge day: R-16 (5 y) is over for 2021 harvests, R-17/R-18 (3 y) for 2023 records.
PURGE_DAY = datetime(2026, 9, 30, 4, 45, tzinfo=UTC)

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


def _insert(database, collection: str, doc: dict[str, Any]) -> str:
    return database.collection(collection).insert(doc)["_id"]


def _seed_personal_tenant(database, tenant: str) -> None:
    database.collection(col.TENANTS).insert(
        {
            "_key": tenant,
            "name": f"Garden {tenant}",
            "slug": tenant,
            "tenant_type": "personal",
            "owner_user_key": MEMBER,
            "is_active": True,
        }
    )


def _seed_rows(database, tenant: str, prefix: str) -> dict[str, str]:
    """An expired and a young row of each rule, their children and their edges; returns ``name -> _id``."""
    ids: dict[str, str] = {}
    for age, harvest_date, record_date in (
        ("old", "2021-06-01T08:00:00Z", "2023-06-01T08:00:00+00:00"),
        ("young", "2024-06-01T08:00:00.500000Z", "2025-06-01T08:00:00Z"),
    ):
        batch = _insert(
            database,
            col.HARVEST_BATCHES,
            {
                "_key": f"{prefix}-hb-{age}",
                "tenant_key": tenant,
                "harvest_date": harvest_date,
                "harvested_by_key": MEMBER,
                "harvester": "Display name",
            },
        )
        batch_key = batch.split("/", 1)[1]
        ids[f"hb-{age}"] = batch
        ids[f"qa-{age}"] = _insert(
            database,
            col.QUALITY_ASSESSMENTS,
            {"_key": f"{prefix}-qa-{age}", "batch_key": batch_key, "assessed_by_key": MEMBER},
        )
        ids[f"ym-{age}"] = _insert(database, col.YIELD_METRICS, {"_key": f"{prefix}-ym-{age}", "batch_key": batch_key})
        ids[f"ta-{age}"] = _insert(
            database,
            col.TREATMENT_APPLICATIONS,
            {"_key": f"{prefix}-ta-{age}", "tenant_key": tenant, "applied_at": record_date, "applied_by_key": MEMBER},
        )
        ids[f"in-{age}"] = _insert(
            database,
            col.INSPECTIONS,
            {
                "_key": f"{prefix}-in-{age}",
                "tenant_key": tenant,
                "inspected_at": record_date,
                "inspected_by_key": MEMBER,
            },
        )
        # Edges onto rows that outlive the tenant: the batch's children and the global catalogue.
        ids[f"e-qa-{age}"] = _insert(database, col.ASSESSED_BY_QUALITY, {"_from": batch, "_to": ids[f"qa-{age}"]})
        ids[f"e-ym-{age}"] = _insert(database, col.HAS_YIELD_METRIC, {"_from": batch, "_to": ids[f"ym-{age}"]})
        ids[f"e-tu-{age}"] = _insert(
            database, col.TREATMENT_USES, {"_from": ids[f"ta-{age}"], "_to": "treatments/global-neem"}
        )
        ids[f"e-dp-{age}"] = _insert(
            database, col.DETECTED_PEST, {"_from": ids[f"in-{age}"], "_to": "pests/global-aphid"}
        )
    # A row whose age cannot be established is never destroyed (NFR-011 §3.2).
    ids["ta-undated"] = _insert(
        database,
        col.TREATMENT_APPLICATIONS,
        {"_key": f"{prefix}-ta-undated", "tenant_key": tenant, "applied_at": None, "applied_by_key": MEMBER},
    )
    return ids


def _read(database, doc_id: str) -> dict[str, Any] | None:
    collection, key = doc_id.split("/", 1)
    return database.collection(collection).get(key)


def _privacy_service(database) -> PrivacyService:
    """The purge half of ``get_privacy_service``: real repositories, every unrelated collaborator a mock."""
    return PrivacyService(
        export_repo=MagicMock(),
        consent_repo=MagicMock(),
        restriction_repo=MagicMock(),
        erasure_repo=MagicMock(),
        email_change_repo=MagicMock(),
        user_repo=MagicMock(),
        refresh_token_repo=MagicMock(),
        data_export_engine=MagicMock(),
        erasure_engine=ErasureEngine(),
        consent_engine=MagicMock(),
        password_engine=MagicMock(),
        token_engine=MagicMock(),
        email_service=MagicMock(),
        frontend_url="https://kamerplanter.example",
        tombstone_salt=SALT,
        retention=RetentionService(),
        legal_retention_repo=ArangoLegalRetentionRepository(database),
    )


@pytest.fixture(scope="module")
def world(database):
    database.collection(col.TREATMENTS).insert({"_key": "global-neem", "tenant_key": ""})
    database.collection(col.PESTS).insert({"_key": "global-aphid"})
    _seed_personal_tenant(database, ERASED)
    _seed_personal_tenant(database, EMPTY)
    database.collection(col.TENANTS).insert({"_key": LIVING, "slug": LIVING, "tenant_type": "organization"})
    erased = _seed_rows(database, ERASED, "er")
    living = _seed_rows(database, LIVING, "lv")
    legacy = _insert(
        database,
        col.HARVEST_BATCHES,
        {"_key": "legacy-hb", "tenant_key": "", "harvest_date": "2015-01-01T00:00:00Z"},
    )
    tenants = tenant_erasure_service(database, SALT)
    for tenant in (ERASED, EMPTY):
        outcome = tenants.erase_personal_tenant_of(MEMBER, tenant, now=ERASED_AT)
        assert outcome.outcome == "erased"
    return {"erased": erased, "living": living, "legacy": legacy}


class TestTheRowsSurviveTheTenantDeletion:
    """Measured before the purge exists: Q-R1 keeps the rows, pseudonymised."""

    def test_every_rule_row_of_the_erased_tenant_is_still_there_under_the_tombstone(self, database, world):
        tombstone = ErasureEngine.compute_tombstone_hash(MEMBER, SALT)
        for name in ("hb-old", "hb-young", "ta-old", "ta-young", "in-old", "in-young", "qa-old", "ym-old"):
            row = _read(database, world["erased"][name])
            assert row is not None, name
        assert _read(database, world["erased"]["hb-old"])["harvested_by_key"] == tombstone
        assert _read(database, world["erased"]["ta-old"])["applied_by_key"] == tombstone
        assert database.collection(col.TENANTS).get(ERASED) is None


class TestThePurge:
    """R-16/R-17/R-18 (#1789) then R-06a (#1793), in the beat's order."""

    @pytest.fixture(scope="class")
    def first_run(self, database, world):
        service = _privacy_service(database)
        import asyncio

        rows = asyncio.run(service.purge_expired_legal_retention_rows(now=PURGE_DAY))
        records = asyncio.run(service.purge_expired_tenant_erasure_records(now=PURGE_DAY))
        return {"rows": rows, "records": records}

    def test_expired_rows_of_the_erased_tenant_go_with_their_children_and_edges(self, database, world, first_run):
        for name in ("hb-old", "qa-old", "ym-old", "ta-old", "in-old"):
            assert _read(database, world["erased"][name]) is None, name
        for name in ("e-qa-old", "e-ym-old", "e-tu-old", "e-dp-old"):
            assert _read(database, world["erased"][name]) is None, name
        assert first_run["rows"] == {
            "R-16": {"rows": 1, "children": 2, "edges": 2},
            "R-17": {"rows": 1, "children": 0, "edges": 1},
            "R-18": {"rows": 1, "children": 0, "edges": 1},
        }

    def test_young_rows_and_an_undated_row_stay(self, database, world, first_run):
        for name in ("hb-young", "qa-young", "ym-young", "ta-young", "in-young", "ta-undated"):
            assert _read(database, world["erased"][name]) is not None, name
        for name in ("e-qa-young", "e-tu-young"):
            assert _read(database, world["erased"][name]) is not None, name

    def test_a_living_tenant_and_a_row_without_a_tenant_are_untouched(self, database, world, first_run):
        for doc_id in world["living"].values():
            assert _read(database, doc_id) is not None, doc_id
        assert _read(database, world["legacy"]) is not None

    def test_the_proof_stays_while_a_retained_row_is_still_running(self, database, world, first_run):
        assert database.collection(col.TENANT_ERASURE_RECORDS).get(TenantErasureEngine.record_key(ERASED)) is not None

    def test_a_proof_that_retained_nothing_stays_until_the_cap(self, database, world, first_run):
        assert first_run["records"] == 0
        assert database.collection(col.TENANT_ERASURE_RECORDS).get(TenantErasureEngine.record_key(EMPTY)) is not None


class TestTheLastRetainedRowGoes:
    """Once the longest R-16..R-18 period of the tenant has run out, the proof goes (R-06a, AK-R06a)."""

    def test_rows_then_proof(self, database, world):
        import asyncio

        service = _privacy_service(database)
        later = datetime(2028, 7, 1, 4, 45, tzinfo=UTC)  # 2025 records + 3 y are over; 2024 harvest + 5 y is not
        asyncio.run(service.purge_expired_legal_retention_rows(now=later))
        assert _read(database, world["erased"]["ta-young"]) is None
        assert _read(database, world["erased"]["hb-young"]) is not None
        assert asyncio.run(service.purge_expired_tenant_erasure_records(now=later)) == 0

        last = datetime(2029, 7, 1, 4, 45, tzinfo=UTC)  # every dated period is over
        asyncio.run(service.purge_expired_legal_retention_rows(now=last))
        for name in ("hb-young", "qa-young", "ym-young", "ta-young", "in-young"):
            assert _read(database, world["erased"][name]) is None, name
        # The undated treatment keeps its tenant's proof until the cap (its age is not established).
        assert asyncio.run(service.purge_expired_tenant_erasure_records(now=last)) == 0

        capped = datetime(2031, 9, 2, 4, 50, tzinfo=UTC)  # five years after ERASED_AT
        assert asyncio.run(service.purge_expired_tenant_erasure_records(now=capped)) == 2
        assert database.collection(col.TENANT_ERASURE_RECORDS).get(TenantErasureEngine.record_key(ERASED)) is None
        assert database.collection(col.TENANT_ERASURE_RECORDS).get(TenantErasureEngine.record_key(EMPTY)) is None


class TestTheRowPurgeRunsInBatches:
    """Security review SEC-003: one transaction per batch, looped until nothing expired is left."""

    def test_more_rows_than_one_batch_all_go(self, database, world):
        from app.data_access.arango.legal_retention_repository import ArangoLegalRetentionRepository

        gone_tenant = "t-never-there"
        keys = [f"batch-in-{i}" for i in range(5)]
        for key in keys:
            ids = _insert(
                database,
                col.INSPECTIONS,
                {"_key": key, "tenant_key": gone_tenant, "inspected_at": "2020-01-01T00:00:00Z"},
            )
            _insert(database, col.DETECTED_PEST, {"_from": ids, "_to": "pests/global-aphid"})
        rule = next(r for r in TenantErasureEngine.LEGAL_RETENTION_RULES if r.rule == "R-18")

        count = ArangoLegalRetentionRepository(database, batch_size=2).delete_expired_rows_of_deleted_tenants(
            rule, cutoff_iso="2023-01-01T00:00:00+00:00"
        )

        assert (count.rows, count.edges) == (5, 5)
        assert all(database.collection(col.INSPECTIONS).get(key) is None for key in keys)
