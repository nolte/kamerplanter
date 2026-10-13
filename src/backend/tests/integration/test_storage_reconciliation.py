"""#1834 — objects no attachment record holds are found by the reconciliation.

Every deletion path decides about a stored object by asking the ``attachments``
catalogue, so an object whose last record is gone without its bytes was never
looked at again. Four independent paths end there, and each is reproduced here
against a real ArangoDB (production indexes) and the real
``LocalFsStorageAdapter``; the object is read back from disk, not from a double:

1. a storage call that fails after the erasure plan committed;
2. a record created inside the erasure's window (after the subject's objects were
   read, before the plan ran) — the plan deletes the record, nothing holds the bytes;
3. a pest reference uploaded through the generic route in a tenant the user later
   left without a contribution — the erasure never walks that tenant;
4. a storage delete that fails after its record was removed elsewhere (the
   concurrent-delete re-check in ``AttachmentService.delete``).

Each test first asserts the defect on the object store (bytes present, no record
holds them — true on ``develop`` without this change), then drives the Celery task
the beat calls, ``reconcile_orphaned_storage_objects``: report-only by default,
deleting only when ``STORAGE_RECONCILE_DELETE_ENABLED`` is on, and never an object
a record holds, a rendition of a held original, or one younger than the floor.

S3 has no emulator in this tier; the service only uses the adapter interface
(``list_objects`` / ``head_object`` / ``delete_object``), and the S3 adapter's own
paging contract is covered in ``tests/unit/data_access/storage``.
"""

from __future__ import annotations

import asyncio
import io
import os
import time
from unittest.mock import MagicMock, patch

import pytest
from arango import ArangoClient
from PIL import Image

from app.common.enums import AttachmentCategory
from app.config.settings import Settings, settings
from app.data_access.arango import collections as col
from app.data_access.arango.attachment_repository import ArangoAttachmentRepository
from app.data_access.arango.erasure_executor import ArangoErasureExecutor
from app.data_access.arango.membership_repository import ArangoMembershipRepository
from app.data_access.arango.pest_image_repository import ArangoPestImageRepository
from app.data_access.storage.local_fs_adapter import LocalFsStorageAdapter
from app.data_access.vectordb.noop_reference_index_store import NoopReferenceIndexStore
from app.data_access.vectordb.pest_prototype_stores import NoopPestPrototypeStore
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.engines.storage.thumbnail_generator import thumbnail_key
from app.domain.services.attachment_service import AttachmentService
from app.domain.services.privacy_service import PrivacyService
from app.tasks.storage_tasks import reconcile_orphaned_storage_objects
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name
from tests.support.tenant_erasure_wiring import tenant_erasure_service

TEST_DATABASE = run_database_name("storage_reconciliation")
TENANT = "t-recon"
SALT = "recon-test-salt-not-a-secret-0123456789"
LONG_AGO_HOURS = 72

pytestmark = pytest.mark.usefixtures("arango_db")


def _photo() -> bytes:
    """A JPEG no other call returns. Random pixels: neighbouring solid colours quantise to
    the *same* JPEG, which deduplicates a second upload onto the first's record."""
    buffer = io.BytesIO()
    Image.frombytes("RGB", (24, 24), os.urandom(24 * 24 * 3)).save(buffer, format="JPEG")
    return buffer.getvalue()


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


@pytest.fixture(scope="module")
def repo(database) -> ArangoAttachmentRepository:
    return ArangoAttachmentRepository(database)


@pytest.fixture
def storage(repo, tmp_path) -> LocalFsStorageAdapter:
    # Function-scoped: the reconciliation walks the whole of ``t/``, so each test
    # gets a store holding only its own objects and the counts are exact.
    return LocalFsStorageAdapter(
        root=str(tmp_path),
        public_base_url="http://localhost",
        signing_secret="recon-test-signing-secret",
        max_object_size_bytes=10 * 1024 * 1024,
        attachment_repo=repo,
    )


@pytest.fixture
def service(storage, repo) -> AttachmentService:
    return AttachmentService(storage=storage, attachment_repo=repo, settings=Settings())


@pytest.fixture
def privacy(database, storage, repo) -> PrivacyService:
    return PrivacyService(
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
        pest_image_repo=ArangoPestImageRepository(database),
        pest_prototype_store=NoopPestPrototypeStore(),
        reference_index_store=NoopReferenceIndexStore(),
        erasure_executor=ArangoErasureExecutor(database),
        tenant_service=tenant_erasure_service(database, SALT),
        tombstone_salt=SALT,
    )


class _FakeRedis:
    """Just the three calls the cursor store makes; in-process, like the cursor's own use."""

    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    def get(self, key):
        return self.values.get(key)

    def set(self, key, value, ex=None):
        self.values[key] = value

    def delete(self, key):
        self.values.pop(key, None)


@pytest.fixture
def reconcile(storage, repo):
    """Run the beat's task — report-only unless ``delete`` — against the fixtures."""
    redis = _FakeRedis()

    def run(*, delete: bool = False, min_age_hours: int = 24, max_objects: int = 200_000) -> dict:
        with (
            patch("app.tasks.storage_tasks.get_object_storage", return_value=storage),
            patch("app.tasks.storage_tasks.get_attachment_repo", return_value=repo),
            patch("app.common.dependencies._get_redis_client", return_value=redis),
            patch.object(settings, "storage_reconcile_delete_enabled", delete),
            patch.object(settings, "storage_reconcile_min_age_hours", min_age_hours),
            patch.object(settings, "storage_reconcile_max_objects_per_run", max_objects),
        ):
            return reconcile_orphaned_storage_objects()

    return run


def _member(database, user_key: str, tenant_key: str = TENANT) -> str:
    database.collection(col.USERS).insert({"_key": user_key, "email": f"{user_key}@example.com"})
    database.collection(col.MEMBERSHIPS).insert({"user_key": user_key, "tenant_key": tenant_key, "role": "grower"})
    return user_key


async def _upload(service, *, user_key, data, category, tenant_key=TENANT):
    with patch("app.tasks.storage_tasks.generate_thumbnails.delay"):
        return await service.upload(
            tenant_key=tenant_key,
            user_key=user_key,
            data=data,
            mime_type="image/jpeg",
            original_filename=f"{user_key}.jpg",
            category=category,
        )


def _on_disk(storage, key: str) -> bool:
    path = storage._path_for(key)
    return path.exists() and path.stat().st_size > 0


def _age(storage, *keys: str, hours: int = LONG_AGO_HOURS) -> None:
    """Back-date objects: the safety floor reads the store's own modification time."""
    then = time.time() - hours * 3600
    for key in keys:
        os.utime(storage._path_for(key), (then, then))


def _assert_stranded(storage, repo, key: str) -> None:
    """The defect itself: the bytes are on disk and no record holds them."""
    assert _on_disk(storage, key), "the path under test was expected to leave the bytes behind"
    assert repo.held_storage_keys([key]) == set(), "a record still holds the object — nothing is stranded"


def _assert_found_then_deleted(storage, reconcile, key: str) -> None:
    _age(storage, key)
    report_only = reconcile()
    assert report_only["report_only"] is True
    assert report_only["found"] == 1
    assert report_only["would_delete"] == 1
    assert report_only["deleted"] == 0
    assert _on_disk(storage, key), "report-only mode deleted an object"

    armed = reconcile(delete=True)
    assert armed["deleted"] == 1
    assert armed["failed"] == 0
    assert not _on_disk(storage, key)


# --- the four paths ------------------------------------------------------


def test_path_1_a_storage_call_failing_after_the_plan_committed_is_reconciled(
    database, service, storage, privacy, repo, reconcile
):
    first, second = _member(database, "p1-a"), _member(database, "p1-b")
    photo = _photo()
    a = asyncio.run(_upload(service, user_key=first, data=photo, category=AttachmentCategory.PEST_REFERENCE))
    b = asyncio.run(_upload(service, user_key=second, data=photo, category=AttachmentCategory.PEST_REFERENCE))

    executor = privacy._erasure_executor
    real_run = executor.run_erasure_plan
    real_delete = storage.delete_object
    storage_down = {"on": False}

    async def flaky_delete(key):
        if storage_down["on"]:
            raise OSError("storage unavailable")
        await real_delete(key)

    def run_after_b_withdrew_then_storage_fails(plan, *, tombstone):
        assert asyncio.run(service.delete(b.key, TENANT)) is True
        result = real_run(plan, tombstone=tombstone)
        storage_down["on"] = True  # the release after the committed plan hits a dead backend
        return result

    with (
        patch.object(storage, "delete_object", flaky_delete),
        patch.object(executor, "run_erasure_plan", side_effect=run_after_b_withdrew_then_storage_fails),
    ):
        report = asyncio.run(privacy.erase_account(first))

    assert report.storage_objects_released == 0
    _assert_stranded(storage, repo, a.storage_key)
    _assert_found_then_deleted(storage, reconcile, a.storage_key)


def test_path_2_a_record_created_inside_the_erasure_window_is_reconciled(
    database, service, storage, privacy, repo, reconcile
):
    user = _member(database, "p2-a")
    asyncio.run(_upload(service, user_key=user, data=_photo(), category=AttachmentCategory.PEST_REFERENCE))
    late = {}
    executor = privacy._erasure_executor
    real_run = executor.run_erasure_plan

    def upload_then_run_plan(plan, *, tombstone):
        # Phase 0 has run and the release after the plan only covers what was read
        # before; this record exists for neither, and the plan deletes it by owner.
        late["att"] = asyncio.run(
            _upload(service, user_key=user, data=_photo(), category=AttachmentCategory.PEST_REFERENCE)
        )
        return real_run(plan, tombstone=tombstone)

    with patch.object(executor, "run_erasure_plan", side_effect=upload_then_run_plan):
        asyncio.run(privacy.erase_account(user))

    assert repo.get(late["att"].key, TENANT) is None, "the plan was expected to delete the late record"
    _assert_stranded(storage, repo, late["att"].storage_key)
    _assert_found_then_deleted(storage, reconcile, late["att"].storage_key)


def test_path_3_a_pest_reference_in_a_tenant_the_user_left_is_reconciled(
    database, service, storage, privacy, repo, reconcile
):
    left_tenant = "t-recon-left"
    user = _member(database, "p3-a", left_tenant)
    _member_other = database.collection(col.MEMBERSHIPS).insert(
        {"user_key": user, "tenant_key": "t-recon-home", "role": "grower"}
    )
    att = asyncio.run(
        _upload(
            service,
            user_key=user,
            data=_photo(),
            category=AttachmentCategory.PEST_REFERENCE,
            tenant_key=left_tenant,
        )
    )
    # The user leaves that tenant; no pest-image contribution record ties them to it.
    database.collection(col.MEMBERSHIPS).delete_match({"user_key": user, "tenant_key": left_tenant})

    asyncio.run(privacy.erase_account(user))

    assert repo.get(att.key, left_tenant) is None, "the plan was expected to delete the record globally"
    _assert_stranded(storage, repo, att.storage_key)
    _assert_found_then_deleted(storage, reconcile, att.storage_key)


def test_path_4_a_storage_delete_failing_after_its_record_was_removed_is_reconciled(
    database, service, storage, repo, reconcile
):
    first, second = _member(database, "p4-a"), _member(database, "p4-b")
    photo = _photo()
    a = asyncio.run(_upload(service, user_key=first, data=photo, category=AttachmentCategory.DIARY))
    b = asyncio.run(_upload(service, user_key=second, data=photo, category=AttachmentCategory.DIARY))
    real_repo_delete = repo.delete

    def delete_then_the_other_holder_goes(key, tenant_key):
        removed = real_repo_delete(key, tenant_key)
        # The other holder's own delete ran meanwhile and saw this record as the holder.
        real_repo_delete(b.key, tenant_key)
        return removed

    async def dead_storage(key):
        raise OSError("storage unavailable")

    with (
        patch.object(repo, "delete", delete_then_the_other_holder_goes),
        patch.object(storage, "delete_object", dead_storage),
        pytest.raises(OSError),
    ):
        asyncio.run(service.delete(a.key, TENANT))

    _assert_stranded(storage, repo, a.storage_key)
    _assert_found_then_deleted(storage, reconcile, a.storage_key)


# --- what the reconciliation must never touch ---------------------------------


def test_a_held_object_and_the_renditions_of_a_held_original_are_never_deleted(
    database, service, storage, repo, reconcile
):
    user = _member(database, "keep-a")
    held = asyncio.run(_upload(service, user_key=user, data=_photo(), category=AttachmentCategory.DIARY))
    renditions = [thumbnail_key(held.storage_key, size) for size in (128, 512, 1280)]
    for rendition in renditions:
        asyncio.run(storage.copy_object(held.storage_key, rendition))
    _age(storage, held.storage_key, *renditions)

    # One key per page: the original and its renditions are judged by different
    # catalogue queries, so a rendition is protected by the mapping, not by the
    # original happening to share its page.
    with patch("app.data_access.storage.local_fs_adapter.LIST_PAGE_SIZE", 1):
        report = reconcile(delete=True)

    assert report["found"] == 0
    assert report["deleted"] == 0
    assert all(_on_disk(storage, key) for key in [held.storage_key, *renditions])


def test_the_renditions_of_a_stranded_original_go_with_it(database, service, storage, repo, reconcile):
    user = _member(database, "rend-a")
    att = asyncio.run(_upload(service, user_key=user, data=_photo(), category=AttachmentCategory.DIARY))
    renditions = [thumbnail_key(att.storage_key, size) for size in (128, 512)]
    for rendition in renditions:
        asyncio.run(storage.copy_object(att.storage_key, rendition))
    repo.delete(att.key, TENANT)  # the record goes; the bytes and renditions stay
    _age(storage, att.storage_key, *renditions)

    report = reconcile(delete=True)

    assert report["deleted"] == 3
    assert not any(_on_disk(storage, key) for key in [att.storage_key, *renditions])


def test_an_object_younger_than_the_floor_is_left_alone(database, service, storage, repo, reconcile):
    """An upload writes the object before its record: a fresh unheld object is in flight."""
    user = _member(database, "young-a")
    att = asyncio.run(_upload(service, user_key=user, data=_photo(), category=AttachmentCategory.DIARY))
    repo.delete(att.key, TENANT)

    report = reconcile(delete=True)

    assert report["found"] == 1
    assert report["young"] == 1
    assert report["deleted"] == 0
    assert _on_disk(storage, att.storage_key)


def test_a_run_stopped_by_its_object_budget_resumes_where_it_left_off(database, service, storage, repo, reconcile):
    user = _member(database, "resume-a")
    stranded = []
    for _ in range(5):
        att = asyncio.run(_upload(service, user_key=user, data=_photo(), category=AttachmentCategory.DIARY))
        repo.delete(att.key, TENANT)
        stranded.append(att.storage_key)
    _age(storage, *stranded)

    with patch("app.data_access.storage.local_fs_adapter.LIST_PAGE_SIZE", 2):
        runs = [reconcile(delete=True, max_objects=2) for _ in range(3)]

    assert runs[0]["truncated"] is True
    assert sum(run["deleted"] for run in runs) == 5
    assert not any(_on_disk(storage, key) for key in stranded)
