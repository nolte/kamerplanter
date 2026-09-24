"""#1645 — an erased user's retained photos lose their EXIF GPS in storage.

REQ-025 §3.1 keeps documentation photos (diary, IPM, harvest, …) attached to
the tenant record but requires the erasure to *anonymise their ownership and
strip their EXIF*. Both halves select the photos by ``created_by == user_key``.
Until 2026-09-24 the anonymisation ran first and rewrote exactly that field to
``_anonymized``, so the EXIF strip then looked the photos up by a key no
document carried any more, rewrote nothing, and the GPS position of every such
photo survived the erasure — while both steps reported having run.

A unit double cannot certify this: the defect lives in the interplay of the
real AQL selector and the real rewrite. So this module runs the real
``ArangoAttachmentRepository`` against a real database and the real
``LocalFsStorageAdapter`` against a temporary directory, and reads the stored
**bytes** back. No status field or count is taken as evidence.

Runs in CI against a service container; locally it needs a database::

    docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_erasure_exif_strip_reach.py -v
"""

from __future__ import annotations

import asyncio
import hashlib
import io
from unittest.mock import MagicMock

import pytest
from arango import ArangoClient
from PIL import Image
from PIL.ExifTags import Base as ExifBase

from app.data_access.arango import collections as col
from app.data_access.arango.attachment_repository import ArangoAttachmentRepository
from app.data_access.arango.erasure_executor import ArangoErasureExecutor
from app.data_access.arango.membership_repository import ArangoMembershipRepository
from app.data_access.storage.local_fs_adapter import LocalFsStorageAdapter
from app.data_access.vectordb.noop_reference_index_store import NoopReferenceIndexStore
from app.domain.engines.erasure_engine import ANONYMIZED_MARKER, ErasureEngine
from app.domain.services.privacy_service import PrivacyService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("privacy_erasure_exif")

SUBJECT = "user-exif-a"
OTHER = "user-exif-b"
TENANT = "t-exif"
#: NFR-011 §4 wants >= 32 characters. Synthetic, test-only.
SALT = "exif-test-salt-not-a-secret-0123456789"
#: Documentation categories the ``user_diary_attachments`` rule anonymises.
CATEGORIES = ("diary", "ipm", "harvest", "task")

pytestmark = pytest.mark.usefixtures("arango_db")


def _jpeg_with_gps() -> bytes:
    exif = Image.Exif()
    exif[ExifBase.Make.value] = "TestCam"
    gps = exif.get_ifd(ExifBase.GPSInfo.value)
    gps[1] = "N"
    gps[2] = (52.0, 31.0, 12.0)
    gps[3] = "E"
    gps[4] = (13.0, 24.0, 36.0)
    buffer = io.BytesIO()
    Image.new("RGB", (64, 48), color=(120, 200, 80)).save(buffer, format="JPEG", exif=exif.tobytes())
    return buffer.getvalue()


def _owners(database, owner: str) -> set[str]:
    attachments = database.collection(col.ATTACHMENTS)
    return {attachments.get(f"{owner}-{category}")["created_by"] for category in CATEGORIES}


def _gps_of(data: bytes) -> dict:
    with Image.open(io.BytesIO(data)) as image:
        return dict(image.getexif().get_ifd(ExifBase.GPSInfo.value))


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    for name in (col.ATTACHMENTS, col.MEMBERSHIPS, col.USERS):
        db.create_collection(name)
    yield db
    system.delete_database(TEST_DATABASE)


def _seed(database, storage: LocalFsStorageAdapter) -> dict[str, list[str]]:
    """One GPS-tagged photo per owner and category; returns the storage keys per owner."""
    photo = _jpeg_with_gps()
    assert _gps_of(photo), "the fixture must carry a GPS IFD, otherwise the test proves nothing"
    keys: dict[str, list[str]] = {SUBJECT: [], OTHER: []}
    for owner in (SUBJECT, OTHER):
        database.collection(col.USERS).insert({"_key": owner, "email": f"{owner}@example.com"})
        database.collection(col.MEMBERSHIPS).insert({"user_key": owner, "tenant_key": TENANT, "role": "grower"})
        for category in CATEGORIES:
            storage_key = f"t/{TENANT}/{category}/{owner}.jpg"
            storage._write_sync(storage._path_for(storage_key), photo, "image/jpeg", {})
            database.collection(col.ATTACHMENTS).insert(
                {
                    "_key": f"{owner}-{category}",
                    "tenant_key": TENANT,
                    "mime_type": "image/jpeg",
                    "byte_size": len(photo),
                    "sha256": hashlib.sha256(photo).hexdigest(),
                    "original_filename": f"{category}.jpg",
                    "created_by": owner,
                    "category": category,
                    "storage_key": storage_key,
                }
            )
            keys[owner].append(storage_key)
    return keys


@pytest.fixture(scope="module")
def erased(database, tmp_path_factory):
    attachment_repo = ArangoAttachmentRepository(database)
    storage = LocalFsStorageAdapter(
        root=str(tmp_path_factory.mktemp("storage")),
        public_base_url="http://localhost",
        signing_secret="exif-test-signing-secret",
        max_object_size_bytes=10 * 1024 * 1024,
        attachment_repo=attachment_repo,
    )
    keys = _seed(database, storage)
    before_other = {key: storage._path_for(key).read_bytes() for key in keys[OTHER]}
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
        attachment_repo=attachment_repo,
        # #1753 — Phase 0.5 needs a wired store; no contribution is on record here.
        reference_index_store=NoopReferenceIndexStore(),
        erasure_executor=ArangoErasureExecutor(database),
        tombstone_salt=SALT,
    )
    asyncio.run(service.erase_account(SUBJECT))
    return storage, keys, before_other


def test_no_retained_photo_of_the_erased_user_still_carries_gps(erased):
    storage, keys, _ = erased
    with_gps = [key for key in keys[SUBJECT] if _gps_of(storage._path_for(key).read_bytes())]
    assert with_gps == []


def test_the_retained_photos_are_still_there_and_anonymised(database, erased):
    storage, keys, _ = erased
    assert all(storage._path_for(key).exists() for key in keys[SUBJECT])
    assert _owners(database, SUBJECT) == {ANONYMIZED_MARKER}


def test_the_other_users_photos_are_byte_for_byte_unchanged(database, erased):
    storage, _, before_other = erased
    changed = [key for key, data in before_other.items() if storage._path_for(key).read_bytes() != data]
    assert changed == []
    assert _owners(database, OTHER) == {OTHER}
