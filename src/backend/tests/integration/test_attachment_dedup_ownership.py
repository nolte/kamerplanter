"""#1770 — deduplicated attachments belong to every uploader, not to the first one.

``AttachmentService.upload`` deduplicates by sha256 within a tenant. Until this
change a second upload of the same bytes was handed the *first* uploader's
catalog record: ``created_by`` stayed the first uploader and the second got no
record of their own. Erasure selects by ``created_by``, so

* erasing the first uploader applied their storage rule to bytes the second one
  still referenced (a hard-deleted pest reference took the second uploader's
  photo with it), and
* erasing the second uploader found nothing attributed to them.

Every upload now gets its own record; identical bytes are stored once and shared
by the records that hold them, and they are deleted only when the last record
goes. Tenants never share: the lookup and the storage key are tenant-scoped.

A double cannot certify this — the defect lives in the interplay of the real
AQL selectors, the real ``storage_key`` index and the real byte deletion. This
module runs ``AttachmentService`` and ``PrivacyService.erase_account`` against a
real ArangoDB (with the production indexes from ``ensure_collections``) and the
real ``LocalFsStorageAdapter``, and reads the stored bytes back.
"""

from __future__ import annotations

import asyncio
import io
from unittest.mock import MagicMock, patch

import pytest
from arango import ArangoClient
from PIL import Image

from app.common.enums import AttachmentCategory
from app.config.settings import Settings
from app.data_access.arango import collections as col
from app.data_access.arango.attachment_repository import ArangoAttachmentRepository
from app.data_access.arango.erasure_executor import ArangoErasureExecutor
from app.data_access.arango.membership_repository import ArangoMembershipRepository
from app.data_access.storage.local_fs_adapter import LocalFsStorageAdapter
from app.data_access.vectordb.noop_reference_index_store import NoopReferenceIndexStore
from app.domain.engines.erasure_engine import ANONYMIZED_MARKER, ErasureEngine
from app.domain.services.attachment_service import AttachmentService
from app.domain.services.privacy_service import PrivacyService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("attachment_dedup_ownership")

TENANT = "t-dedup"
OTHER_TENANT = "t-dedup-other"
#: NFR-011 §4 wants >= 32 characters. Synthetic, test-only.
SALT = "dedup-test-salt-not-a-secret-0123456789"

pytestmark = pytest.mark.usefixtures("arango_db")

_colour = iter(range(1, 250))


def _photo() -> bytes:
    """A JPEG no other test in this module uploads (distinct bytes, distinct sha256)."""
    shade = next(_colour)
    buffer = io.BytesIO()
    Image.new("RGB", (48, 32), color=(shade, 255 - shade, 90)).save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    # The production collections *and indexes* — the storage-key index is part of
    # what is under test.
    col.ensure_collections(db)
    yield db
    system.delete_database(TEST_DATABASE)


@pytest.fixture(scope="module")
def repo(database) -> ArangoAttachmentRepository:
    return ArangoAttachmentRepository(database)


@pytest.fixture(scope="module")
def storage(repo, tmp_path_factory) -> LocalFsStorageAdapter:
    return LocalFsStorageAdapter(
        root=str(tmp_path_factory.mktemp("storage")),
        public_base_url="http://localhost",
        signing_secret="dedup-test-signing-secret",
        max_object_size_bytes=10 * 1024 * 1024,
        attachment_repo=repo,
    )


@pytest.fixture(scope="module")
def service(storage, repo) -> AttachmentService:
    return AttachmentService(storage=storage, attachment_repo=repo, settings=Settings())


@pytest.fixture(scope="module")
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
        reference_index_store=NoopReferenceIndexStore(),
        erasure_executor=ArangoErasureExecutor(database),
        tombstone_salt=SALT,
    )


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


def _readable(storage, storage_key: str) -> bool:
    path = storage._path_for(storage_key)
    return path.exists() and path.stat().st_size > 0


def test_a_second_uploader_gets_a_record_of_their_own(database, service, storage):
    first, second = _member(database, "own-a"), _member(database, "own-b")
    photo = _photo()

    a = asyncio.run(_upload(service, user_key=first, data=photo, category=AttachmentCategory.DIARY))
    b = asyncio.run(_upload(service, user_key=second, data=photo, category=AttachmentCategory.DIARY))

    assert b.key != a.key
    assert b.created_by == second
    assert a.created_by == first
    # The bytes are stored once.
    assert b.storage_key == a.storage_key
    assert _readable(storage, b.storage_key)


def test_the_same_uploader_re_uploading_gets_their_own_record_back(database, service):
    user = _member(database, "idem-a")
    photo = _photo()

    first = asyncio.run(_upload(service, user_key=user, data=photo, category=AttachmentCategory.TASK))
    again = asyncio.run(_upload(service, user_key=user, data=photo, category=AttachmentCategory.TASK))

    assert again.key == first.key


def test_erasing_the_first_uploader_leaves_the_second_uploaders_content(database, service, storage, privacy, repo):
    first, second = _member(database, "erase-a"), _member(database, "erase-b")
    photo = _photo()
    a = asyncio.run(_upload(service, user_key=first, data=photo, category=AttachmentCategory.PEST_REFERENCE))
    b = asyncio.run(_upload(service, user_key=second, data=photo, category=AttachmentCategory.PEST_REFERENCE))

    report = asyncio.run(privacy.erase_account(first))

    kept = repo.get(b.key, TENANT)
    assert kept is not None, "the second uploader's record must survive the first uploader's erasure"
    assert kept.created_by == second
    assert _readable(storage, kept.storage_key), "bytes the second uploader holds must not be deleted"
    # The erased user's own link is gone.
    assert repo.get(a.key, TENANT) is None
    assert report.storage_objects_retained_shared == 1
    assert report.storage_objects_removed == 0


def test_erasing_the_last_holder_deletes_the_bytes(database, service, storage, privacy, repo):
    first, second = _member(database, "last-a"), _member(database, "last-b")
    photo = _photo()
    a = asyncio.run(_upload(service, user_key=first, data=photo, category=AttachmentCategory.PEST_REFERENCE))
    b = asyncio.run(_upload(service, user_key=second, data=photo, category=AttachmentCategory.PEST_REFERENCE))
    asyncio.run(privacy.erase_account(first))

    report = asyncio.run(privacy.erase_account(second))

    assert repo.get(b.key, TENANT) is None, "the second uploader's erasure must reach their own record"
    assert not _readable(storage, a.storage_key), "no record holds the bytes any more"
    assert report.storage_objects_removed == 1
    assert report.storage_objects_retained_shared == 0


def test_erasing_the_first_uploader_does_not_anonymise_the_second_uploaders_record(database, service, privacy, repo):
    first, second = _member(database, "anon-a"), _member(database, "anon-b")
    photo = _photo()
    a = asyncio.run(_upload(service, user_key=first, data=photo, category=AttachmentCategory.DIARY))
    b = asyncio.run(_upload(service, user_key=second, data=photo, category=AttachmentCategory.DIARY))

    asyncio.run(privacy.erase_account(first))

    assert repo.get(a.key, TENANT).created_by == ANONYMIZED_MARKER
    assert repo.get(b.key, TENANT).created_by == second
    assert [att.key for att in repo.find_by_user(TENANT, second)] == [b.key]


def test_deleting_one_record_keeps_bytes_another_record_holds(database, service, storage, repo):
    first, second = _member(database, "del-a"), _member(database, "del-b")
    photo = _photo()
    a = asyncio.run(_upload(service, user_key=first, data=photo, category=AttachmentCategory.PEST_REFERENCE))
    b = asyncio.run(_upload(service, user_key=second, data=photo, category=AttachmentCategory.DIARY))

    assert asyncio.run(service.delete(b.key, TENANT)) is True
    assert repo.get(a.key, TENANT) is not None
    assert _readable(storage, a.storage_key), "a pest contribution's delete destroyed a diary photo"

    assert asyncio.run(service.delete(a.key, TENANT)) is True
    assert not _readable(storage, a.storage_key)


def test_identical_bytes_are_never_shared_across_tenants(database, service, storage, privacy, repo):
    inside, outside = _member(database, "xt-a"), _member(database, "xt-c", OTHER_TENANT)
    photo = _photo()
    a = asyncio.run(_upload(service, user_key=inside, data=photo, category=AttachmentCategory.PEST_REFERENCE))
    c = asyncio.run(
        _upload(
            service, user_key=outside, data=photo, category=AttachmentCategory.PEST_REFERENCE, tenant_key=OTHER_TENANT
        )
    )

    assert c.storage_key != a.storage_key
    assert c.storage_key.startswith(f"t/{OTHER_TENANT}/")
    asyncio.run(privacy.erase_account(inside))
    assert _readable(storage, c.storage_key)
    assert repo.get(c.key, OTHER_TENANT) is not None


def test_shared_bytes_count_once_against_the_quota(database, service, repo):
    first, second = _member(database, "quota-a", "t-dedup-quota"), _member(database, "quota-b", "t-dedup-quota")
    photo = _photo()
    a = asyncio.run(
        _upload(service, user_key=first, data=photo, category=AttachmentCategory.DIARY, tenant_key="t-dedup-quota")
    )
    asyncio.run(
        _upload(service, user_key=second, data=photo, category=AttachmentCategory.DIARY, tenant_key="t-dedup-quota")
    )

    assert repo.sum_bytes_by_tenant("t-dedup-quota") == a.byte_size
