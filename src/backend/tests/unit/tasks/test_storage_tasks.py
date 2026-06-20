"""NFR-013 §8.2 — generate_thumbnails Celery task unit test."""

from __future__ import annotations

import io
from collections.abc import AsyncIterator
from unittest.mock import patch

from PIL import Image

from app.common.enums import AttachmentCategory
from app.domain.engines.storage.thumbnail_generator import THUMBNAIL_SIZES, thumbnail_key
from app.domain.models.attachment import Attachment


def _jpeg() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (300, 200), (10, 20, 30)).save(buffer, format="JPEG")
    return buffer.getvalue()


async def _one(data: bytes) -> AsyncIterator[bytes]:
    yield data


async def test_generate_thumbnails_writes_three_renditions(tmp_path):
    from app.data_access.storage.local_fs_adapter import LocalFsStorageAdapter
    from app.tasks import storage_tasks

    adapter = LocalFsStorageAdapter(
        root=str(tmp_path),
        public_base_url="http://localhost/token",
        signing_secret="s",
        max_object_size_bytes=25 * 1024 * 1024,
    )

    storage_key = "t/t-1/diary/2026/06/ULIDULIDULIDULIDULIDULID12.jpg"
    await adapter.put_object(storage_key, _one(_jpeg()), "image/jpeg")

    attachment = Attachment(
        key="att1",
        tenant_key="t-1",
        mime_type="image/jpeg",
        byte_size=100,
        sha256="x",
        original_filename="a.jpg",
        created_by="u-1",
        category=AttachmentCategory.DIARY,
        storage_key=storage_key,
    )

    class _Repo:
        def get(self, key, tenant_key):
            return attachment

    with (
        patch.object(storage_tasks, "get_object_storage", return_value=adapter),
        patch.object(storage_tasks, "get_attachment_repo", return_value=_Repo()),
    ):
        # The task body calls asyncio.run internally; invoke the inner coroutine
        # directly here so we stay on the test's event loop (no nested run()).
        result = await storage_tasks._generate("att1", "t-1")

    assert result["generated"] == 3
    for size in THUMBNAIL_SIZES:
        meta = await adapter.head_object(thumbnail_key(storage_key, size))
        assert meta.size_bytes > 0


def test_migrate_storage_task_returns_report():
    """NFR-013 §7.3 / AC-07 — the Celery wrapper returns the migration report."""
    from unittest.mock import AsyncMock

    from app.tasks import storage_tasks
    from scripts.storage.migrate import MigrationReport

    report = MigrationReport(
        backend_from="local-fs",
        backend_to="s3",
        dry_run=False,
        checksum_verify=True,
        total=4,
        copied=4,
        verified=4,
    )
    with patch("scripts.storage.migrate.migrate", new=AsyncMock(return_value=report)):
        result = storage_tasks.migrate_storage.run("local-fs", "s3", checksum_verify=True)

    assert result["copied"] == 4
    assert result["verified"] == 4
    assert result["ok"] is True


def test_migrate_photo_refs_task_returns_report():
    """NFR-013 §2.2 / AC-09 — the Celery wrapper returns the normalisation report."""
    from app.migrations.migrate_photo_refs import PhotoRefMigrationReport
    from app.tasks import storage_tasks

    report = PhotoRefMigrationReport(dry_run=False, scanned_documents=2, changed_documents=1, changed_refs=1)
    with patch("app.migrations.migrate_photo_refs.run", return_value=report):
        result = storage_tasks.migrate_photo_refs.run(dry_run=False)

    assert result["changed_documents"] == 1
    assert result["noop"] is False
