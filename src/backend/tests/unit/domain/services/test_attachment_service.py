"""NFR-013 §5.1 — AttachmentService upload-pipeline tests.

The service is exercised against BOTH real storage backends — local-fs
(``tmp_path``) and S3 (``moto``) — through a parametrized ``service`` fixture,
with an in-memory attachment repository double. The Celery thumbnail dispatch
is patched so no broker is required.
"""

from __future__ import annotations

import asyncio
import io
import threading
from collections.abc import Callable
from unittest.mock import patch

import httpx
import pytest
from PIL import Image
from structlog.testing import capture_logs

from app.common.enums import AttachmentCategory
from app.common.exceptions import (
    AttachmentNotFoundError,
    FileTooLargeError,
    InvalidFileTypeError,
    StorageQuotaExceededError,
    VirusScanRejectedError,
    WriteConflictError,
)
from app.config.settings import Settings
from app.data_access.storage.local_fs_adapter import LocalFsStorageAdapter
from app.data_access.storage.s3_adapter import S3StorageAdapter
from app.domain.models.attachment import Attachment
from app.domain.services.attachment_service import AttachmentService, ObjectReleaseError

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
        #: How often ``remove_if_unreferenced`` ran - each call is one transaction.
        self.remove_calls = 0
        #: How often ``remove_unreferenced`` ran - one transaction for the whole batch (#2715 item 6).
        self.batch_remove_calls = 0
        self._rivals: list[Callable[[], None]] = []

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
        # One charge per stored object, as the repository counts it (#1770).
        return sum({a.storage_key: a.byte_size for a in self._store.values() if a.tenant_key == tenant_key}.values())

    def find_own_by_sha256(self, *, tenant_key, sha256, created_by, category):  # type: ignore[no-untyped-def]
        # As the repository answers it (#1770): the uploader's own record for these
        # bytes in this category — never another member's.
        for att in self._store.values():
            if (att.tenant_key, att.sha256, att.created_by, att.category) == (tenant_key, sha256, created_by, category):
                return att
        return None

    #: Per attachment id, what ``task_photo_delete_state`` answers; "missing" for an id nobody set (and not stored).
    states: dict[str, str] = {}

    def task_photo_delete_state(self, attachment_id, tenant_key, *, task_key):  # type: ignore[no-untyped-def]
        stored = self.get(attachment_id, tenant_key)
        if stored is None:
            return "missing", None
        return self.states.get(attachment_id, "staged"), stored.created_by

    def overtake_next_removals(self, *rivals: Callable[[], None]) -> None:
        """Queue writers that commit inside the next ``remove_if_unreferenced`` transactions, one per call.

        As in ArangoDB (``ArangoAttachmentRepository.remove_if_unreferenced``, #2545): the rival commits a write on
        the record after this transaction's scan, so the remove meets it and the transaction fails with ``1200``.
        A call with no rival queued is a transaction nobody overtakes and decides on the state it reads.
        """
        self._rivals.extend(rivals)

    def remove_if_unreferenced(self, attachment_id, tenant_key):  # type: ignore[no-untyped-def]
        # One call standing for the repository's one transaction: the scan's answer and the remove.
        self.remove_calls += 1
        state, _created_by = self.task_photo_delete_state(attachment_id, tenant_key, task_key="")
        if self._rivals:
            self._rivals.pop(0)()  # a write on the record commits between this scan and this remove
            raise WriteConflictError("attachments")
        if state != "staged":
            return None
        return self._store.pop(attachment_id)

    def remove_unreferenced(self, attachment_ids, tenant_key, *, category):  # type: ignore[no-untyped-def]
        # One call standing for the batch's one transaction (#2715 item 6): one scan, every remove, or a conflict.
        self.remove_calls += 1
        self.batch_remove_calls += 1
        if self._rivals:
            self._rivals.pop(0)()
            raise WriteConflictError("attachments")
        removed = []
        for attachment_id in dict.fromkeys(attachment_ids):
            stored = self.get(attachment_id, tenant_key)
            if stored is None or stored.category != category or self.states.get(attachment_id, "staged") != "staged":
                continue
            removed.append(self._store.pop(attachment_id))
        return removed

    def mark_renditions_failed(self, tenant_key: str, storage_key: str) -> int:
        """Updates every record holding the object, names none of them (#2108) - a writer that is not a carrier."""
        held = [a for a in self._store.values() if a.tenant_key == tenant_key and a.storage_key == storage_key]
        for att in held:
            self._store[att.key] = att.model_copy(update={"renditions_failed": True})
        return len(held)

    def storage_keys_held_elsewhere(self, *, tenant_key, storage_keys, excluding):  # type: ignore[no-untyped-def]
        return {
            a.storage_key
            for a in self._store.values()
            if a.tenant_key == tenant_key and a.storage_key in storage_keys and a.key not in excluding
        }

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
    # Plain imports. ``moto[s3]`` and ``boto3`` are both declared and pinned, so
    # their absence is a broken environment, not an optional feature — and
    # ``importorskip`` reported exactly that as a pass. Measured on 2026-09-14: run
    # against an interpreter without them, this file and its two siblings dropped 28
    # cases into the skip count while the summary stayed green (#1435, #1434).
    import boto3
    import moto

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

    async def test_another_member_gets_their_own_record_over_the_stored_object(self, service, repo, adapter):
        """#1770 — the record is an owner's claim; only the bytes are shared."""
        jpeg = _make_jpeg()
        with patch("app.tasks.storage_tasks.generate_thumbnails.delay") as delay:
            first = await service.upload(
                tenant_key="t-1",
                user_key="u-1",
                data=jpeg,
                mime_type="image/jpeg",
                original_filename="mine.jpg",
                category=AttachmentCategory.PEST_REFERENCE,
            )
            second = await service.upload(
                tenant_key="t-1",
                user_key="u-2",
                data=jpeg,
                mime_type="image/jpeg",
                original_filename="theirs.jpg",
                category=AttachmentCategory.PEST_REFERENCE,
            )
        assert second.key != first.key
        assert (second.created_by, second.original_filename) == ("u-2", "theirs.jpg")
        assert second.storage_key == first.storage_key
        # One object written, renditions dispatched once — for the object.
        assert len((await adapter.list_objects("t/t-1/"))["keys"]) == 1
        delay.assert_called_once_with(first.key, "t-1")

    async def test_the_same_member_in_another_category_gets_a_second_record(self, service, repo):
        """#1770 — retention differs per category, so a record never spans two."""
        jpeg = _make_jpeg()
        with patch("app.tasks.storage_tasks.generate_thumbnails.delay"):
            diary = await service.upload(
                tenant_key="t-1",
                user_key="u-1",
                data=jpeg,
                mime_type="image/jpeg",
                original_filename="a.jpg",
                category=AttachmentCategory.DIARY,
            )
            pest = await service.upload(
                tenant_key="t-1",
                user_key="u-1",
                data=jpeg,
                mime_type="image/jpeg",
                original_filename="a.jpg",
                category=AttachmentCategory.PEST_REFERENCE,
            )
        assert pest.key != diary.key
        assert pest.category == AttachmentCategory.PEST_REFERENCE
        assert pest.storage_key == diary.storage_key

    async def test_deleting_one_record_keeps_the_object_another_record_holds(self, service, adapter):
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
                user_key="u-2",
                data=jpeg,
                mime_type="image/jpeg",
                original_filename="b.jpg",
                category=AttachmentCategory.DIARY,
            )

        assert await service.delete(second.key, "t-1") is True
        assert (await adapter.list_objects("t/t-1/"))["keys"] == [first.storage_key]

        assert await service.delete(first.key, "t-1") is True
        assert (await adapter.list_objects("t/t-1/"))["keys"] == []

    async def test_bytes_stored_under_another_type_are_not_linked_to(self, service, repo, adapter):
        """#1770 review SEC-003 — a linked record is served with the object's type, so it must be this upload's."""
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
        repo._store[first.key] = first.model_copy(update={"mime_type": "image/png"})
        with patch("app.tasks.storage_tasks.generate_thumbnails.delay"):
            second = await service.upload(
                tenant_key="t-1",
                user_key="u-2",
                data=jpeg,
                mime_type="image/jpeg",
                original_filename="b.jpg",
                category=AttachmentCategory.DIARY,
            )
        assert second.storage_key != first.storage_key
        assert second.mime_type == "image/jpeg"

    async def test_two_deletes_of_the_last_two_holders_do_not_strand_the_object(self, service, repo, adapter):
        """#1770 review SEC-001 — each delete saw the other record; the one asking again after its own sees none."""
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
                user_key="u-2",
                data=jpeg,
                mime_type="image/jpeg",
                original_filename="b.jpg",
                category=AttachmentCategory.DIARY,
            )
        real = repo.storage_keys_held_elsewhere
        calls = 0

        def concurrent_delete_of_the_other(**kwargs):  # type: ignore[no-untyped-def]
            nonlocal calls
            calls += 1
            answer = real(**kwargs)
            if calls == 1:
                # The other request removes its record right after this one asked.
                repo._store.pop(second.key)
            return answer

        repo.storage_keys_held_elsewhere = concurrent_delete_of_the_other
        assert await service.delete(first.key, "t-1") is True
        assert (await adapter.list_objects("t/t-1/"))["keys"] == []

    async def test_a_record_whose_object_is_gone_is_not_linked_to(self, service, repo, adapter):
        """#1770 — a held record whose object vanished is no object to share; the upload stores its own."""
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
            # The object is gone, the record still there (the delete's storage call
            # ran, its record delete did not yet).
            await adapter.delete_object(first.storage_key)
            second = await service.upload(
                tenant_key="t-1",
                user_key="u-2",
                data=jpeg,
                mime_type="image/jpeg",
                original_filename="b.jpg",
                category=AttachmentCategory.DIARY,
            )
        assert second.storage_key != first.storage_key
        stored = await _collect(await service.open_stream(second))
        assert len(stored) > 0

    async def test_an_object_deleted_while_the_link_is_written_is_written_back(self, service, adapter, monkeypatch):
        """#1770 — the last other holder's delete removed the object after the lookup saw it."""
        jpeg = _make_jpeg()
        with patch("app.tasks.storage_tasks.generate_thumbnails.delay") as delay:
            first = await service.upload(
                tenant_key="t-1",
                user_key="u-1",
                data=jpeg,
                mime_type="image/jpeg",
                original_filename="a.jpg",
                category=AttachmentCategory.DIARY,
            )
            real_exists = service._object_exists
            answers = iter([True])

            async def _exists_then_deleted(storage_key):  # type: ignore[no-untyped-def]
                # The lookup sees the object; by the re-check a concurrent delete removed it.
                seen = next(answers, None)
                if seen is None:
                    await adapter.delete_object(storage_key)
                    return await real_exists(storage_key)
                return seen

            monkeypatch.setattr(service, "_object_exists", _exists_then_deleted)
            second = await service.upload(
                tenant_key="t-1",
                user_key="u-2",
                data=jpeg,
                mime_type="image/jpeg",
                original_filename="b.jpg",
                category=AttachmentCategory.DIARY,
            )
        assert second.storage_key == first.storage_key
        stored = await _collect(await service.open_stream(second))
        assert len(stored) > 0
        assert delay.call_args_list[-1].args == (second.key, "t-1")


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


class TestDeleteIfUnreferenced:
    """#2400 — the care-event redaction and the R-25 sweep delete a photo only when no carrier references it."""

    async def _stored(self, service) -> Attachment:
        with patch("app.tasks.storage_tasks.generate_thumbnails.delay"):
            return await service.upload(
                tenant_key="t-1",
                user_key="u-1",
                data=_make_jpeg(),
                mime_type="image/jpeg",
                original_filename="a.jpg",
                category=AttachmentCategory.PLANT,
            )

    async def test_an_unreferenced_photo_is_deleted(self, service, repo):
        attachment = await self._stored(service)

        assert await service.delete_if_unreferenced(attachment.key, "t-1") is True

        assert repo.get(attachment.key, "t-1") is None

    async def test_the_repository_calls_run_off_the_event_loop_thread(self, service, repo, monkeypatch):
        """#2545 review LOW-1: the reference-scan transaction and the holder query are synchronous Arango calls."""
        attachment = await self._stored(service)
        threads: dict[str, int] = {}
        for name in ("remove_if_unreferenced", "storage_keys_held_elsewhere"):
            original = getattr(repo, name)

            def recording(*args, _name=name, _original=original, **kwargs):  # type: ignore[no-untyped-def]
                threads[_name] = threading.get_ident()
                return _original(*args, **kwargs)

            monkeypatch.setattr(repo, name, recording)
        loop_thread = threading.get_ident()

        assert await service.delete_if_unreferenced(attachment.key, "t-1") is True

        assert set(threads) == {"remove_if_unreferenced", "storage_keys_held_elsewhere"}
        assert loop_thread not in threads.values()

    async def test_a_photo_another_carrier_still_references_stays(self, service, repo):
        attachment = await self._stored(service)
        repo.states = {attachment.key: "shared"}

        assert await service.delete_if_unreferenced(attachment.key, "t-1") is False

        assert repo.get(attachment.key, "t-1") is not None

    async def test_an_unknown_or_foreign_id_is_a_no_op(self, service, repo):
        attachment = await self._stored(service)

        assert await service.delete_if_unreferenced("does-not-exist", "t-1") is False
        assert await service.delete_if_unreferenced(attachment.key, "t-other") is False
        assert repo.get(attachment.key, "t-1") is not None

    async def test_the_stored_object_goes_with_the_record(self, service, repo, adapter):
        attachment = await self._stored(service)

        assert await service.delete_if_unreferenced(attachment.key, "t-1") is True

        assert not await service._object_exists(attachment.storage_key)

    async def test_an_object_another_record_holds_stays(self, service, repo, adapter):
        attachment = await self._stored(service)
        twin = repo.create(attachment.model_copy(update={"key": None, "created_by": "u-2"}))

        assert await service.delete_if_unreferenced(attachment.key, "t-1") is True

        assert repo.get(twin.key, "t-1") is not None
        assert await service._object_exists(attachment.storage_key)

    async def test_a_carrier_naming_it_concurrently_keeps_record_and_object(self, service, repo, adapter):
        """#2545/#2630: the remove conflicts with a carrier binding the record; the retry's scan sees it - it stays."""
        attachment = await self._stored(service)

        def carrier_binds_it() -> None:  # e.g. another site sets this picture as its underlay
            repo.states = {attachment.key: "shared"}

        repo.overtake_next_removals(carrier_binds_it)

        assert await service.delete_if_unreferenced(attachment.key, "t-1") is False

        assert repo.remove_calls == 2  # the conflict was retried, and the retry's scan found the holder
        assert repo.get(attachment.key, "t-1") is not None
        assert await service._object_exists(attachment.storage_key)

    async def test_a_conflict_with_a_writer_that_names_nothing_still_deletes(self, service, repo, adapter):
        """#2630: a renditions-failed update conflicts with the remove but holds nothing - the photo does not stay."""
        attachment = await self._stored(service)
        repo.overtake_next_removals(lambda: repo.mark_renditions_failed("t-1", attachment.storage_key))

        assert await service.delete_if_unreferenced(attachment.key, "t-1") is True

        assert repo.remove_calls == 2
        assert repo.get(attachment.key, "t-1") is None
        assert not await service._object_exists(attachment.storage_key)

    async def test_a_conflict_on_both_attempts_keeps_the_photo_and_stops_after_two(self, service, repo, adapter):
        """#2630: one retry, no loop - a writer that keeps conflicting leaves record and object in place."""
        attachment = await self._stored(service)
        touched: list[int] = []

        def writer() -> None:
            touched.append(repo.mark_renditions_failed("t-1", attachment.storage_key))

        repo.overtake_next_removals(writer, writer, writer)

        with capture_logs() as logs:
            assert await service.delete_if_unreferenced(attachment.key, "t-1") is False

        assert repo.remove_calls == 2 and len(touched) == 2  # the third queued writer never got a transaction
        assert [e["event"] for e in logs if e["event"] == "attachment_delete_skipped_concurrent_write"] == [
            "attachment_delete_skipped_concurrent_write"
        ]
        assert repo.get(attachment.key, "t-1") is not None
        assert await service._object_exists(attachment.storage_key)


class TestDeleteManyIfUnreferenced:
    """#2715 item 6 - the photos a committed bed or site delete let go of go in one batch, not one scan per photo."""

    async def _stored(self, service, *, colour: int, category=AttachmentCategory.LOCATION) -> Attachment:
        image = Image.new("RGB", (32, 32), color=(colour, 10, 10))
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        with patch("app.tasks.storage_tasks.generate_thumbnails.delay"):
            return await service.upload(
                tenant_key="t-1",
                user_key="u-1",
                data=buffer.getvalue(),
                mime_type="image/jpeg",
                original_filename="beet.jpg",
                category=category,
            )

    async def test_one_transaction_removes_every_unreferenced_record_and_its_object(self, service, repo):
        photos = [await self._stored(service, colour=colour) for colour in (10, 20, 30)]

        deleted = await service.delete_many_if_unreferenced(
            [photo.key for photo in photos], "t-1", category=AttachmentCategory.LOCATION
        )

        assert deleted == 3 and repo.batch_remove_calls == 1 and repo.remove_calls == 1
        assert all(repo.get(photo.key, "t-1") is None for photo in photos)
        assert not any([await service._object_exists(photo.storage_key) for photo in photos])

    async def test_a_photo_a_carrier_still_names_stays_with_its_object(self, service, repo):
        kept, gone = await self._stored(service, colour=40), await self._stored(service, colour=50)
        repo.states = {kept.key: "shared"}

        deleted = await service.delete_many_if_unreferenced(
            [kept.key, gone.key], "t-1", category=AttachmentCategory.LOCATION
        )

        assert deleted == 1
        assert repo.get(kept.key, "t-1") is not None and await service._object_exists(kept.storage_key)
        assert repo.get(gone.key, "t-1") is None

    async def test_another_category_and_another_tenant_are_never_removed(self, service, repo):
        gallery = await self._stored(service, colour=60, category=AttachmentCategory.PLANT)
        bed = await self._stored(service, colour=70)

        assert (
            await service.delete_many_if_unreferenced([gallery.key], "t-1", category=AttachmentCategory.LOCATION) == 0
        )
        assert (
            await service.delete_many_if_unreferenced([bed.key], "t-other", category=AttachmentCategory.LOCATION) == 0
        )

        assert repo.get(gallery.key, "t-1") is not None and repo.get(bed.key, "t-1") is not None

    async def test_an_object_another_record_holds_stays(self, service, repo):
        photo = await self._stored(service, colour=80)
        twin = repo.create(
            photo.model_copy(update={"key": None, "created_by": "u-2", "category": AttachmentCategory.PLANT})
        )

        assert await service.delete_many_if_unreferenced([photo.key], "t-1", category=AttachmentCategory.LOCATION) == 1

        assert repo.get(twin.key, "t-1") is not None and await service._object_exists(photo.storage_key)

    async def test_a_conflict_is_asked_once_more_and_a_second_one_keeps_every_photo(self, service, repo):
        photos = [await self._stored(service, colour=colour) for colour in (90, 100)]
        keys = [photo.key for photo in photos]
        repo.overtake_next_removals(lambda: None, lambda: None, lambda: None)

        with capture_logs() as logs:
            assert await service.delete_many_if_unreferenced(keys, "t-1", category=AttachmentCategory.LOCATION) == 0

        assert repo.batch_remove_calls == 2  # one retry, no loop
        assert all(repo.get(key, "t-1") is not None for key in keys)
        assert "attachment_delete_skipped_concurrent_write" in [entry["event"] for entry in logs]

    async def test_a_conflict_whose_retry_succeeds_deletes(self, service, repo):
        photo = await self._stored(service, colour=110)
        repo.overtake_next_removals(lambda: repo.mark_renditions_failed("t-1", photo.storage_key))

        assert await service.delete_many_if_unreferenced([photo.key], "t-1", category=AttachmentCategory.LOCATION) == 1
        assert repo.batch_remove_calls == 2

    async def test_the_storage_deletes_are_bounded(self, service, repo, adapter, monkeypatch):
        from app.domain.services import attachment_service

        monkeypatch.setattr(attachment_service, "OBJECT_RELEASE_CONCURRENCY", 2)
        photos = [await self._stored(service, colour=colour) for colour in range(120, 200, 10)]
        in_flight = peak = 0
        original = adapter.delete_object

        async def counting(key: str) -> None:
            nonlocal in_flight, peak
            in_flight += 1
            peak = max(peak, in_flight)
            await asyncio.sleep(0)
            await original(key)
            in_flight -= 1

        adapter.delete_object = counting  # type: ignore[method-assign]

        deleted = await service.delete_many_if_unreferenced(
            [photo.key for photo in photos], "t-1", category=AttachmentCategory.LOCATION
        )

        assert deleted == len(photos) and peak == 2

    async def test_a_failed_object_delete_is_owed_and_the_rest_still_go(self, adapter, repo, settings):
        owed = _OwedReleases()
        service = AttachmentService(storage=adapter, attachment_repo=repo, settings=settings, release_retries=owed)
        broken, fine = await self._stored(service, colour=210), await self._stored(service, colour=220)
        original = adapter.delete_object

        async def failing_for_one(key: str) -> None:
            if key == broken.storage_key:
                raise OSError("storage unavailable")
            await original(key)

        adapter.delete_object = failing_for_one  # type: ignore[method-assign]

        assert (
            await service.delete_many_if_unreferenced(
                [broken.key, fine.key], "t-1", category=AttachmentCategory.LOCATION
            )
            == 2
        )

        assert owed.recorded == [("t-1", [broken.storage_key])]
        assert not await service._object_exists(fine.storage_key)

    async def test_without_a_retry_store_the_records_count_and_only_the_objects_are_the_error(
        self, adapter, repo, settings
    ):
        """#2715 review SEC-S02: the records were committed away - the error names the objects that stayed, apart."""
        service = AttachmentService(storage=adapter, attachment_repo=repo, settings=settings)
        broken, fine = await self._stored(service, colour=230), await self._stored(service, colour=240)
        tried: list[str] = []
        original = adapter.delete_object

        async def failing_for_one(key: str) -> None:
            tried.append(key)
            if key == broken.storage_key:
                raise OSError("storage unavailable")
            await original(key)

        adapter.delete_object = failing_for_one  # type: ignore[method-assign]

        with pytest.raises(ObjectReleaseError) as raised:
            await service.delete_many_if_unreferenced(
                [broken.key, fine.key], "t-1", category=AttachmentCategory.LOCATION
            )

        assert raised.value.removed == 2 and raised.value.attachment_ids == [broken.key] and raised.value.objects == 1
        assert isinstance(raised.value.__cause__, OSError)
        assert not any("/" in attachment_id for attachment_id in raised.value.attachment_ids)
        assert {broken.storage_key, fine.storage_key} <= set(tried)  # every key was tried
        assert repo.get(broken.key, "t-1") is None and repo.get(fine.key, "t-1") is None

    async def test_an_object_held_again_between_chunks_is_not_deleted(self, service, repo, adapter, monkeypatch):
        """#2715 review SEC-S01: each chunk asks for other holders right before its deletes, not once for the batch."""
        from app.domain.services import attachment_service

        monkeypatch.setattr(attachment_service, "OBJECT_RELEASE_CONCURRENCY", 1)
        first, second = await self._stored(service, colour=250), await self._stored(service, colour=5)
        original = adapter.delete_object
        linked: list[str] = []

        async def dedup_upload_meanwhile(key: str) -> None:
            await original(key)
            if not linked:  # the first storage call: another member uploads the second photo's bytes now
                linked.append(
                    repo.create(
                        second.model_copy(
                            update={"key": None, "created_by": "u-2", "category": AttachmentCategory.PLANT}
                        )
                    ).key
                )

        adapter.delete_object = dedup_upload_meanwhile  # type: ignore[method-assign]

        deleted = await service.delete_many_if_unreferenced(
            [first.key, second.key], "t-1", category=AttachmentCategory.LOCATION
        )

        assert deleted == 2
        assert not await service._object_exists(first.storage_key)
        assert await service._object_exists(second.storage_key)  # the new record holds it

    async def test_an_empty_batch_touches_nothing(self, service, repo):
        assert await service.delete_many_if_unreferenced([], "t-1", category=AttachmentCategory.LOCATION) == 0
        assert repo.batch_remove_calls == 0


class _OwedReleases:
    """In-memory owed releases (#2630)."""

    def __init__(self) -> None:
        self.recorded: list[tuple[str, list[str]]] = []

    def owe_release(self, *, tenant_key: str, object_keys: list[str]) -> None:
        self.recorded.append((tenant_key, list(object_keys)))


class TestAFailedObjectReleaseIsOwed:
    """#2630 case 2 — the record is gone, the storage delete fails: the object is recorded for a retry, not lost."""

    async def _stored(self, service) -> Attachment:
        with patch("app.tasks.storage_tasks.generate_thumbnails.delay"):
            return await service.upload(
                tenant_key="t-1",
                user_key="u-1",
                data=_make_jpeg(),
                mime_type="image/jpeg",
                original_filename="a.jpg",
                category=AttachmentCategory.GARDEN_PLAN_UNDERLAY,
            )

    async def test_the_failed_delete_is_recorded_and_the_caller_is_not_failed(self, adapter, repo, settings):
        owed = _OwedReleases()
        service = AttachmentService(storage=adapter, attachment_repo=repo, settings=settings, release_retries=owed)
        attachment = await self._stored(service)

        async def failing(key: str) -> None:
            raise OSError(f"storage unavailable for {key}")

        adapter.delete_object = failing  # type: ignore[method-assign]

        assert await service.delete_if_unreferenced(attachment.key, "t-1") is True

        assert repo.get(attachment.key, "t-1") is None
        assert len(owed.recorded) == 1
        tenant, keys = owed.recorded[0]
        assert tenant == "t-1" and keys[0] == attachment.storage_key

    async def test_a_successful_delete_owes_nothing(self, adapter, repo, settings):
        owed = _OwedReleases()
        service = AttachmentService(storage=adapter, attachment_repo=repo, settings=settings, release_retries=owed)
        attachment = await self._stored(service)

        assert await service.delete_if_unreferenced(attachment.key, "t-1") is True

        assert owed.recorded == []

    async def test_without_a_retry_store_the_failure_propagates_as_before(self, adapter, repo, settings):
        service = AttachmentService(storage=adapter, attachment_repo=repo, settings=settings)
        attachment = await self._stored(service)

        async def failing(key: str) -> None:
            raise OSError("storage unavailable")

        adapter.delete_object = failing  # type: ignore[method-assign]

        with pytest.raises(OSError):
            await service.delete_if_unreferenced(attachment.key, "t-1")


class TestARecordNeverReachesAnotherTenantsObject:
    """#2138 review SEC-004 (second defence) — a record whose key leaves ``t/<its tenant>/`` serves nothing.

    Every key the service builds lies under the record's own tenant. A record written by
    anything else — a crafted tenant import above all — could otherwise stream, sign or
    delete another tenant's object through the record's own routes.
    """

    def _foreign(self, repo: _FakeAttachmentRepo, storage_key: str) -> Attachment:
        record = Attachment(
            key="foreign",
            tenant_key="t-a",
            mime_type="image/jpeg",
            byte_size=4,
            sha256="x",
            original_filename="x.jpg",
            created_by="u-1",
            category=AttachmentCategory.PLANT,
            storage_key=storage_key,
        )
        repo._store["foreign"] = record
        return record

    @pytest.mark.parametrize("storage_key", ["t/t-b/plant/2026/10/x.jpg", "t/t-a/../t-b/plant/x.jpg"])
    async def test_download_stream_and_presign_are_refused(self, service, repo, adapter, storage_key) -> None:
        record = self._foreign(repo, storage_key)
        await adapter.put_object("t/t-b/plant/2026/10/x.jpg", _one_chunk(b"B's!"), "image/jpeg")
        with pytest.raises(AttachmentNotFoundError):
            service.get_download("foreign", "t-a")
        with pytest.raises(AttachmentNotFoundError):
            service.presign_download("foreign", "t-a")
        with pytest.raises(AttachmentNotFoundError):
            await service.open_stream(record)

    async def test_delete_removes_the_record_but_not_the_foreign_object(self, service, repo, adapter) -> None:
        self._foreign(repo, "t/t-b/plant/2026/10/x.jpg")
        await adapter.put_object("t/t-b/plant/2026/10/x.jpg", _one_chunk(b"B's!"), "image/jpeg")

        assert await service.delete("foreign", "t-a") is True

        assert repo.get("foreign", "t-a") is None
        assert await _collect(await adapter.get_object("t/t-b/plant/2026/10/x.jpg")) == b"B's!"


async def _one_chunk(data: bytes):
    yield data
