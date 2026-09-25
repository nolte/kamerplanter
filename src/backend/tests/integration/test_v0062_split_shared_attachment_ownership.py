"""#1770 — v0062 against a real ArangoDB, then the erasure it exists for.

Legacy data from before #1770: one attachment record per stored object, owned
by whoever uploaded the bytes first, with pest-image contributions of other
members (or of other categories) pointing at it. The migration must

* drop the unique ``storage_key`` index an existing volume carries,
* give every contribution that is not the record's own a record of its own,
* turn a ``pest_reference`` record a documentation carrier references into a
  documentation record,
* write nothing in a dry run, and change nothing on a second run —

and after it, erasing the original uploader must leave the other members'
images in place, which is the point of all of it.
"""

from __future__ import annotations

import asyncio
import hashlib
import io
from unittest.mock import MagicMock

import pytest
from arango import ArangoClient
from PIL import Image

from app.data_access.arango import collections as col
from app.data_access.arango.attachment_repository import PHOTO_REF_COLLECTIONS, ArangoAttachmentRepository
from app.data_access.arango.erasure_executor import ArangoErasureExecutor
from app.data_access.arango.membership_repository import ArangoMembershipRepository
from app.data_access.storage.local_fs_adapter import LocalFsStorageAdapter
from app.data_access.vectordb.noop_reference_index_store import NoopReferenceIndexStore
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.services.privacy_service import PrivacyService
from app.migrations.versions.v0062_split_shared_attachment_ownership import CARRIER_CATEGORY, migration, split_key
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name
from tests.support.tenant_erasure_wiring import tenant_erasure_service

TEST_DATABASE = run_database_name("v0062_split_shared_attachment")
TENANT = "t-v0062"
SALT = "v0062-test-salt-not-a-secret-0123456789"

pytestmark = pytest.mark.usefixtures("arango_db")


def test_every_photo_ref_carrier_has_a_documentation_category():
    assert set(CARRIER_CATEGORY) == set(PHOTO_REF_COLLECTIONS)


def _jpeg(shade: int) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (40, 30), color=(shade, 40, 200 - shade)).save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    # An existing volume: the unique index from before #1770, then the startup
    # ``ensure_collections`` of this release (which adds the non-unique one).
    db.create_collection(col.ATTACHMENTS).add_persistent_index(fields=["storage_key"], unique=True)
    col.ensure_collections(db)
    yield db
    system.delete_database(TEST_DATABASE)


@pytest.fixture(scope="module")
def storage(database, tmp_path_factory) -> LocalFsStorageAdapter:
    return LocalFsStorageAdapter(
        root=str(tmp_path_factory.mktemp("storage")),
        public_base_url="http://localhost",
        signing_secret="v0062-test-signing-secret",
        max_object_size_bytes=10 * 1024 * 1024,
        attachment_repo=ArangoAttachmentRepository(database),
    )


def _record(database, storage, key: str, owner: str, category: str, shade: int, device: str = "unknown") -> str:
    photo = _jpeg(shade)
    storage_key = f"t/{TENANT}/{category}/2026/01/{key}.jpg"
    storage._write_sync(storage._path_for(storage_key), photo, "image/jpeg", {})
    database.collection(col.ATTACHMENTS).insert(
        {
            "_key": key,
            "tenant_key": TENANT,
            "mime_type": "image/jpeg",
            "byte_size": len(photo),
            "sha256": hashlib.sha256(photo).hexdigest(),
            "original_filename": f"{owner}-private-name.jpg",
            "created_by": owner,
            "category": category,
            "storage_key": storage_key,
            "capture_device": device,
            "created_at": "2026-01-01T00:00:00+00:00",
        }
    )
    return storage_key


def _contribution(database, key: str, contributor: str, attachment_id: str, created_at: str) -> None:
    database.collection(col.PEST_IMAGE_CONTRIBUTIONS).insert(
        {
            "_key": key,
            "tenant_key": TENANT,
            "pest_key": "pest-1",
            "attachment_id": attachment_id,
            "contributed_by": contributor,
            "status": "pending",
            "created_at": created_at,
        }
    )


@pytest.fixture(scope="module")
def legacy(database, storage):
    for user in ("leg-a", "leg-b", "leg-c"):
        database.collection(col.USERS).insert({"_key": user, "email": f"{user}@example.com"})
        database.collection(col.MEMBERSHIPS).insert({"user_key": user, "tenant_key": TENANT, "role": "grower"})
    keys = {
        # A's pest reference, contributed by A and — deduplicated — by B.
        "shared": _record(database, storage, "r-shared", "leg-a", "pest_reference", 10, device="usb_microscope"),
        # A's diary photo, contributed by C as a pest reference.
        "diary": _record(database, storage, "r-diary", "leg-a", "diary", 60),
        # A's pest reference that a diary entry also shows.
        "shown": _record(database, storage, "r-shown", "leg-a", "pest_reference", 110),
        # A's pest reference, only A's contribution: already in shape.
        "own": _record(database, storage, "r-own", "leg-a", "pest_reference", 160),
        # A's pest reference that only a stray diary entry of *another* tenant names.
        "stray": _record(database, storage, "r-stray", "leg-a", "pest_reference", 210),
    }
    _contribution(database, "c-a1", "leg-a", "r-shared", "2026-01-02T00:00:00+00:00")
    _contribution(database, "c-b1", "leg-b", "r-shared", "2026-01-03T00:00:00+00:00")
    _contribution(database, "c-c1", "leg-c", "r-diary", "2026-01-04T00:00:00+00:00")
    _contribution(database, "c-a2", "leg-a", "r-shown", "2026-01-05T00:00:00+00:00")
    _contribution(database, "c-a3", "leg-a", "r-own", "2026-01-06T00:00:00+00:00")
    _contribution(database, "c-a4", "leg-a", "r-stray", "2026-01-07T00:00:00+00:00")
    database.collection(col.PLANT_DIARY_ENTRIES).insert(
        {"_key": "entry-foreign", "tenant_key": "t-elsewhere", "photo_refs": ["r-stray"], "created_by": "leg-x"}
    )
    database.collection(col.PLANT_DIARY_ENTRIES).insert(
        {"_key": "entry-1", "tenant_key": TENANT, "photo_refs": ["r-shown"], "created_by": "leg-b"}
    )
    return keys


def _storage_key_indexes(database) -> list[bool]:
    return sorted(
        bool(idx.get("unique"))
        for idx in database.collection(col.ATTACHMENTS).indexes()
        if idx.get("type") == "persistent" and idx.get("fields") == ["storage_key"]
    )


def _snapshot(database) -> tuple[list, list]:
    attachments = sorted(database.collection(col.ATTACHMENTS).all(), key=lambda d: d["_key"])
    contributions = sorted(database.collection(col.PEST_IMAGE_CONTRIBUTIONS).all(), key=lambda d: d["_key"])
    strip = lambda docs: [{k: v for k, v in d.items() if k != "_rev"} for d in docs]  # noqa: E731
    return strip(attachments), strip(contributions)


@pytest.fixture(scope="module")
def migrated(database, legacy):
    before = _snapshot(database)
    dry = migration.up(database, dry_run=True)
    after_dry = _snapshot(database)
    indexes_after_dry = _storage_key_indexes(database)
    applied = migration.up(database)
    second = migration.up(database)
    return {
        "before": before,
        "dry": dry,
        "after_dry": after_dry,
        "indexes_after_dry": indexes_after_dry,
        "applied": applied,
        "second": second,
    }


def test_the_dry_run_reports_the_plan_and_writes_nothing(migrated):
    assert migrated["after_dry"] == migrated["before"]
    assert migrated["indexes_after_dry"] == [False, True]
    assert migrated["dry"].details == {
        "unique_storage_key_indexes_dropped": 1,
        "contributions_scanned": 6,
        "contributions_unresolved": 0,
        "records_recategorised": 1,
        "records_split": 3,
    }


def test_the_unique_storage_key_index_is_gone(database, migrated):
    assert _storage_key_indexes(database) == [False]


def test_every_contribution_points_at_its_contributors_own_pest_reference(database, migrated, legacy):
    attachments = database.collection(col.ATTACHMENTS)
    for contribution in database.collection(col.PEST_IMAGE_CONTRIBUTIONS).all():
        record = attachments.get(contribution["attachment_id"])
        assert record["created_by"] == contribution["contributed_by"], contribution["_key"]
        assert record["category"] == "pest_reference", contribution["_key"]
    b_record = attachments.get(split_key("c-b1"))
    assert b_record["storage_key"] == legacy["shared"]
    assert b_record["original_filename"] == "", "another member's filename was copied"
    assert b_record["capture_device"] == "unknown", "another member's device hint was copied"
    assert database.collection(col.PEST_IMAGE_CONTRIBUTIONS).get("c-a1")["attachment_id"] == "r-shared"
    assert database.collection(col.PEST_IMAGE_CONTRIBUTIONS).get("c-a3")["attachment_id"] == "r-own"


def test_a_pest_reference_a_diary_entry_shows_becomes_a_diary_record(database, migrated):
    assert database.collection(col.ATTACHMENTS).get("r-shown")["category"] == "diary"


def test_a_reference_from_another_tenant_does_not_recategorise(database, migrated):
    """#1770 review GDPR-003 — recategorising turns a hard-delete into keep; a stray foreign ref must not."""
    assert database.collection(col.ATTACHMENTS).get("r-stray")["category"] == "pest_reference"


def test_a_second_run_changes_nothing(migrated):
    assert migrated["second"].changed == 0
    assert migrated["second"].details["records_split"] == 0
    assert migrated["second"].details["records_recategorised"] == 0


def test_erasing_the_original_uploader_after_the_migration_keeps_the_other_members_images(
    database, storage, migrated, legacy
):
    repo = ArangoAttachmentRepository(database)
    service = PrivacyService(
        export_repo=MagicMock(list_by_user=MagicMock(return_value=[])),
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
        frontend_url="http://localhost",
        membership_repo=ArangoMembershipRepository(database),
        storage_adapter=storage,
        attachment_repo=repo,
        reference_index_store=NoopReferenceIndexStore(),
        erasure_executor=ArangoErasureExecutor(database),
        # #1788 — the subject's personal tenant goes through the tenant-erasure inventory.
        tenant_service=tenant_erasure_service(database, SALT),
        tombstone_salt=SALT,
    )

    report = asyncio.run(service.erase_account("leg-a"))

    # B's contribution: record and bytes survive A's hard-delete rule.
    assert repo.get(split_key("c-b1"), TENANT).created_by == "leg-b"
    assert storage._path_for(legacy["shared"]).exists()
    # The diary entry's photo survives: its record is a documentation record now.
    assert repo.get("r-shown", TENANT) is not None
    assert storage._path_for(legacy["shown"]).exists()
    # C's contribution over A's diary photo survives, and so does the photo.
    assert repo.get(split_key("c-c1"), TENANT).created_by == "leg-c"
    assert storage._path_for(legacy["diary"]).exists()
    # A's exclusively own pest references are gone, bytes and record.
    for key in ("own", "stray"):
        assert repo.get(f"r-{key}", TENANT) is None
        assert not storage._path_for(legacy[key]).exists()
    # A's pest-reference records: r-shared (kept for B), pic-c-a2 (kept for the
    # diary record), r-own and r-stray (deleted).
    assert (report.storage_objects_removed, report.storage_objects_retained_shared) == (2, 2)
