"""NFR-013 §5.1 — AttachmentService upload-pipeline tests.

The service is exercised against BOTH real storage backends — local-fs
(``tmp_path``) and S3 (``moto``) — through a parametrized ``service`` fixture,
with an in-memory attachment repository double. The Celery thumbnail dispatch
is patched so no broker is required.
"""

from __future__ import annotations

import io
from unittest.mock import patch

import httpx
import pytest
from PIL import Image

from app.common.enums import AttachmentCategory
from app.common.exceptions import (
    FileTooLargeError,
    InvalidFileTypeError,
    StorageQuotaExceededError,
    VirusScanRejectedError,
)
from app.config.settings import Settings
from app.data_access.storage.local_fs_adapter import LocalFsStorageAdapter
from app.data_access.storage.s3_adapter import S3StorageAdapter
from app.domain.models.attachment import Attachment
from app.domain.services.attachment_service import AttachmentService

MAX_SIZE = 25 * 1024 * 1024


def _make_jpeg(size: tuple[int, int] = (320, 240)) -> bytes:
    img = Image.new("RGB", size, color=(200, 100, 50))
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()


class _FakeAttachmentRepo:
    """In-memory IAttachmentRepository double."""

    def __init__(self) -> None:
        self._store: dict[str, Attachment] = {}
        self._seq = 0
        self.create_calls = 0

    def create(self, attachment: Attachment) -> Attachment:
        self.create_calls += 1
        self._seq += 1
        key = f"att{self._seq}"
        stored = attachment.model_copy(update={"key": key})
        self._store[key] = stored
        return stored

    def get(self, key: str, tenant_key: str) -> Attachment | None:
        att = self._store.get(key)
        if att is None or att.tenant_key != tenant_key:
            return None
        return att

    def delete(self, key: str, tenant_key: str) -> bool:
        att = self._store.get(key)
        if att is None or att.tenant_key != tenant_key:
            return False
        del self._store[key]
        return True

    def find_by_user(self, tenant_key, user_key, categories=None):
        return [a for a in self._store.values() if a.tenant_key == tenant_key and a.created_by == user_key]

    def find_by_sha256(self, tenant_key: str, sha256: str) -> Attachment | None:
        for a in self._store.values():
            if a.tenant_key == tenant_key and a.sha256 == sha256:
                return a
        return None

    def count_by_tenant(self, tenant_key: str) -> int:
        return sum(1 for a in self._store.values() if a.tenant_key == tenant_key)

    def sum_bytes_by_tenant(self, tenant_key: str) -> int:
        return sum(a.byte_size for a in self._store.values() if a.tenant_key == tenant_key)

    def list_by_tenant(self, tenant_key, category=None, offset=0, limit=50):
        items = [a for a in self._store.values() if a.tenant_key == tenant_key]
        if category is not None:
            items = [a for a in items if a.category == category]
        total = len(items)
        return items[offset : offset + limit], total


@pytest.fixture
def settings() -> Settings:
    return Settings()


@pytest.fixture(params=["local-fs", "s3"])
def adapter(request, tmp_path):
    if request.param == "local-fs":
        yield LocalFsStorageAdapter(
            root=str(tmp_path),
            public_base_url="http://localhost:8000/api/v1/attachments/token",
            signing_secret="test-secret-please-change",
            max_object_size_bytes=MAX_SIZE,
        )
        return
    moto = pytest.importorskip("moto")
    import boto3

    with moto.mock_aws():
        boto3.client("s3", region_name="eu-central-1").create_bucket(
            Bucket="test-bucket",
            CreateBucketConfiguration={"LocationConstraint": "eu-central-1"},
        )
        yield S3StorageAdapter(
            endpoint_url="",
            region="eu-central-1",
            bucket="test-bucket",
            access_key_id="testing",
            secret_access_key="testing",
        )


@pytest.fixture
def repo() -> _FakeAttachmentRepo:
    return _FakeAttachmentRepo()


@pytest.fixture
def service(adapter, repo, settings) -> AttachmentService:
    return AttachmentService(storage=adapter, attachment_repo=repo, settings=settings)


async def _collect(stream) -> bytes:
    out = bytearray()
    async for chunk in stream:
        out.extend(chunk)
    return bytes(out)


class TestUploadHappyPath:
    async def test_uploads_and_persists(self, service, repo):
        jpeg = _make_jpeg()
        with patch("app.tasks.storage_tasks.generate_thumbnails.delay") as delay:
            attachment = await service.upload(
                tenant_key="t-1",
                user_key="u-1",
                data=jpeg,
                mime_type="image/jpeg",
                original_filename="plant.jpg",
                category=AttachmentCategory.DIARY,
            )
        assert attachment.key == "att1"
        assert attachment.category == AttachmentCategory.DIARY
        assert attachment.storage_key.startswith("t/t-1/diary/")
        assert attachment.storage_key.endswith(".jpg")
        # Thumbnail task dispatched for an image.
        delay.assert_called_once_with("att1", "t-1")
        # Object bytes are retrievable.
        target = service.get_download("att1", "t-1")
        stored = await _collect(await service.open_stream(target.attachment))
        assert len(stored) > 0

    async def test_strips_exif_on_upload(self, service):
        # Build a JPEG with EXIF, upload, then read back and confirm no EXIF.
        img = Image.new("RGB", (64, 64), (1, 2, 3))
        exif = Image.Exif()
        exif[271] = "TestCam"  # Make
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", exif=exif.tobytes())
        with patch("app.tasks.storage_tasks.generate_thumbnails.delay"):
            attachment = await service.upload(
                tenant_key="t-1",
                user_key="u-1",
                data=buffer.getvalue(),
                mime_type="image/jpeg",
                original_filename="x.jpg",
                category=AttachmentCategory.DIARY,
            )
        stored = await _collect(await service.open_stream(attachment))
        with Image.open(io.BytesIO(stored)) as out:
            assert len(out.getexif()) == 0


class TestUploadGuards:
    async def test_blocks_mime_not_in_whitelist(self, service):
        with pytest.raises(InvalidFileTypeError):
            await service.upload(
                tenant_key="t-1",
                user_key="u-1",
                data=b"plain text",
                mime_type="text/plain",
                original_filename="x.txt",
                category=AttachmentCategory.DIARY,
            )

    async def test_blocks_magic_byte_mismatch(self, service):
        # Declared JPEG but the bytes are a PNG → magic-byte validator blocks.
        png = io.BytesIO()
        Image.new("RGB", (8, 8)).save(png, format="PNG")
        with pytest.raises(InvalidFileTypeError):
            await service.upload(
                tenant_key="t-1",
                user_key="u-1",
                data=png.getvalue(),
                mime_type="image/jpeg",
                original_filename="fake.jpg",
                category=AttachmentCategory.DIARY,
            )

    async def test_blocks_oversized_file(self, adapter, repo):
        tiny_settings = Settings(storage_max_file_size_mb=0)
        # 0 MB limit → any non-empty image is too large. Build the service with
        # the size limit but a generous quota so the size guard is what fires.
        tiny_settings.storage_tenant_quota_mb = 0
        svc = AttachmentService(storage=adapter, attachment_repo=repo, settings=tiny_settings)
        with pytest.raises(FileTooLargeError):
            await svc.upload(
                tenant_key="t-1",
                user_key="u-1",
                data=_make_jpeg(),
                mime_type="image/jpeg",
                original_filename="big.jpg",
                category=AttachmentCategory.DIARY,
            )

    async def test_blocks_when_quota_exceeded(self, adapter, repo):
        settings = Settings(storage_tenant_quota_mb=1)
        svc = AttachmentService(storage=adapter, attachment_repo=repo, settings=settings)
        # Pre-fill the repo so the tenant is already at quota.
        repo._store["existing"] = Attachment(
            key="existing",
            tenant_key="t-1",
            mime_type="image/jpeg",
            byte_size=1 * 1024 * 1024,
            sha256="x",
            original_filename="e.jpg",
            created_by="u-1",
            category=AttachmentCategory.DIARY,
            storage_key="t/t-1/diary/e.jpg",
        )
        with pytest.raises(StorageQuotaExceededError):
            await svc.upload(
                tenant_key="t-1",
                user_key="u-1",
                data=_make_jpeg(),
                mime_type="image/jpeg",
                original_filename="x.jpg",
                category=AttachmentCategory.DIARY,
            )

    async def test_no_orphan_bytes_on_early_failure(self, service, adapter):
        # A blocked upload must not write anything to storage.
        with pytest.raises(InvalidFileTypeError):
            await service.upload(
                tenant_key="t-1",
                user_key="u-1",
                data=b"not an image",
                mime_type="text/plain",
                original_filename="x.txt",
                category=AttachmentCategory.DIARY,
            )
        listing = await adapter.list_objects("t/t-1/")
        assert listing["keys"] == []


class TestDedup:
    async def test_second_identical_upload_reuses_existing(self, service, repo):
        jpeg = _make_jpeg()
        with patch("app.tasks.storage_tasks.generate_thumbnails.delay"):
            first = await service.upload(
                tenant_key="t-1",
                user_key="u-1",
                data=jpeg,
                mime_type="image/jpeg",
                original_filename="a.jpg",
                category=AttachmentCategory.DIARY,
            )
            second = await service.upload(
                tenant_key="t-1",
                user_key="u-1",
                data=jpeg,
                mime_type="image/jpeg",
                original_filename="b.jpg",
                category=AttachmentCategory.DIARY,
            )
        assert first.key == second.key
        # Only one catalog record was written.
        assert repo.create_calls == 1


class TestVirusScan:
    """SEC-006 — SSRF-validated, fail-closed virus scanning."""

    async def test_ssrf_endpoint_rejected(self, adapter, repo):
        # A non-https / metadata endpoint must be rejected (upload fails closed).
        settings = Settings(
            storage_virus_scan_enabled=True,
            storage_virus_scan_endpoint="http://169.254.169.254/scan",
        )
        svc = AttachmentService(storage=adapter, attachment_repo=repo, settings=settings)
        with pytest.raises(VirusScanRejectedError):
            await svc.upload(
                tenant_key="t-1",
                user_key="u-1",
                data=_make_jpeg(),
                mime_type="image/jpeg",
                original_filename="x.jpg",
                category=AttachmentCategory.DIARY,
            )

    async def test_missing_endpoint_fails_closed(self, adapter, repo):
        settings = Settings(storage_virus_scan_enabled=True, storage_virus_scan_endpoint="")
        svc = AttachmentService(storage=adapter, attachment_repo=repo, settings=settings)
        with pytest.raises(VirusScanRejectedError):
            await svc.upload(
                tenant_key="t-1",
                user_key="u-1",
                data=_make_jpeg(),
                mime_type="image/jpeg",
                original_filename="x.jpg",
                category=AttachmentCategory.DIARY,
            )

    async def test_scanner_unreachable_fails_closed(self, adapter, repo):
        settings = Settings(
            storage_virus_scan_enabled=True,
            storage_virus_scan_endpoint="https://scanner.example.test/scan",
        )
        svc = AttachmentService(storage=adapter, attachment_repo=repo, settings=settings)

        # Pass SSRF validation but make the HTTP call fail → upload rejected.
        with (
            patch("app.domain.services.attachment_service.validate_server_side_url", return_value="ok"),
            patch(
                "app.domain.services.attachment_service.httpx.AsyncClient.post",
                side_effect=httpx.ConnectError("refused"),
            ),
            pytest.raises(VirusScanRejectedError),
        ):
            await svc.upload(
                tenant_key="t-1",
                user_key="u-1",
                data=_make_jpeg(),
                mime_type="image/jpeg",
                original_filename="x.jpg",
                category=AttachmentCategory.DIARY,
            )

    async def test_clean_verdict_allows_upload(self, adapter, repo):
        settings = Settings(
            storage_virus_scan_enabled=True,
            storage_virus_scan_endpoint="https://scanner.example.test/scan",
        )
        svc = AttachmentService(storage=adapter, attachment_repo=repo, settings=settings)

        clean_response = httpx.Response(
            200, json={"clean": True}, request=httpx.Request("POST", "https://scanner.example.test/scan")
        )
        with (
            patch("app.domain.services.attachment_service.validate_server_side_url", return_value="ok"),
            patch(
                "app.domain.services.attachment_service.httpx.AsyncClient.post",
                return_value=clean_response,
            ),
            patch("app.tasks.storage_tasks.generate_thumbnails.delay"),
        ):
            attachment = await svc.upload(
                tenant_key="t-1",
                user_key="u-1",
                data=_make_jpeg(),
                mime_type="image/jpeg",
                original_filename="ok.jpg",
                category=AttachmentCategory.DIARY,
            )
        assert attachment.key is not None

    async def test_malware_verdict_rejected(self, adapter, repo):
        settings = Settings(
            storage_virus_scan_enabled=True,
            storage_virus_scan_endpoint="https://scanner.example.test/scan",
        )
        svc = AttachmentService(storage=adapter, attachment_repo=repo, settings=settings)

        infected = httpx.Response(
            200,
            json={"clean": False, "finding": "EICAR"},
            request=httpx.Request("POST", "https://scanner.example.test/scan"),
        )
        with (
            patch("app.domain.services.attachment_service.validate_server_side_url", return_value="ok"),
            patch(
                "app.domain.services.attachment_service.httpx.AsyncClient.post",
                return_value=infected,
            ),
            pytest.raises(VirusScanRejectedError),
        ):
            await svc.upload(
                tenant_key="t-1",
                user_key="u-1",
                data=_make_jpeg(),
                mime_type="image/jpeg",
                original_filename="bad.jpg",
                category=AttachmentCategory.DIARY,
            )


class TestDelete:
    async def test_delete_removes_original_and_thumbnails(self, service, adapter, repo):
        jpeg = _make_jpeg()
        with patch("app.tasks.storage_tasks.generate_thumbnails.delay"):
            attachment = await service.upload(
                tenant_key="t-1",
                user_key="u-1",
                data=jpeg,
                mime_type="image/jpeg",
                original_filename="a.jpg",
                category=AttachmentCategory.DIARY,
            )
        # Simulate generated thumbnails so delete must remove them too.
        from app.domain.engines.storage.thumbnail_generator import THUMBNAIL_SIZES, thumbnail_key

        async def _one(data: bytes):
            yield data

        for size in THUMBNAIL_SIZES:
            await adapter.put_object(thumbnail_key(attachment.storage_key, size), _one(b"thumb"), "image/webp")

        deleted = await service.delete(attachment.key, "t-1")
        assert deleted is True
        # Original + thumbnails all gone.
        listing = await adapter.list_objects("t/t-1/")
        assert listing["keys"] == []
        # Catalog record removed.
        assert repo.get(attachment.key, "t-1") is None

    async def test_delete_is_idempotent(self, service):
        assert await service.delete("does-not-exist", "t-1") is False
