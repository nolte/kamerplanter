"""NFR-013 §8.2 — Celery tasks for thumbnail generation.

``generate_thumbnails`` runs off the upload critical path: it loads the
original object, renders three WEBP renditions (128 / 512 / 1280 px longest
edge) via :class:`ThumbnailGenerator`, and writes each next to the original
with the ``{ulid}_t{size}.webp`` key (NFR-013 §8.2).

The task is idempotent — re-running it overwrites the existing renditions and
also supports lazy regeneration when a download finds a missing rendition.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import structlog

from app.common.dependencies import get_attachment_repo, get_object_storage
from app.domain.engines.storage.thumbnail_generator import (
    ThumbnailGenerator,
    can_render,
    thumbnail_key,
)
from app.tasks import celery_app

logger = structlog.get_logger()


async def _bytes_stream(data: bytes) -> AsyncIterator[bytes]:
    yield data


async def _collect(stream: AsyncIterator[bytes]) -> bytes:
    out = bytearray()
    async for chunk in stream:
        out.extend(chunk)
    return bytes(out)


async def _generate(attachment_id: str, tenant_key: str) -> dict:
    storage = get_object_storage()
    repo = get_attachment_repo()

    attachment = repo.get(attachment_id, tenant_key)
    if attachment is None:
        logger.warning("thumbnail_attachment_missing", attachment_id=attachment_id, tenant_key=tenant_key)
        return {"attachment_id": attachment_id, "generated": 0, "reason": "attachment_not_found"}

    if not can_render(attachment.mime_type):
        return {"attachment_id": attachment_id, "generated": 0, "reason": "not_renderable"}

    original = await _collect(await storage.get_object(attachment.storage_key))
    generator = ThumbnailGenerator()
    renditions = generator.generate(original, attachment.mime_type)

    generated = 0
    for thumb in renditions:
        key = thumbnail_key(attachment.storage_key, thumb.size)
        await storage.put_object(
            key,
            _bytes_stream(thumb.data),
            thumb.mime_type,
            metadata={"tenant_key": tenant_key, "thumbnail_of": attachment_id},
        )
        generated += 1

    logger.info(
        "thumbnails_generated",
        tenant_key=tenant_key,
        attachment_id=attachment_id,
        generated=generated,
    )
    return {"attachment_id": attachment_id, "generated": generated}


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)  # type: ignore[misc]
def generate_thumbnails(self, attachment_id: str, tenant_key: str) -> dict:  # type: ignore[no-untyped-def]
    """Generate WEBP thumbnail renditions for an image attachment (NFR-013 §8.2)."""
    try:
        return asyncio.run(_generate(attachment_id, tenant_key))
    except Exception as exc:  # noqa: BLE001 — retry on any transient failure
        logger.error(
            "generate_thumbnails_failed",
            attachment_id=attachment_id,
            tenant_key=tenant_key,
            error=str(exc),
        )
        raise self.retry(exc=exc) from exc


@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)  # type: ignore[misc]
def migrate_storage(  # type: ignore[no-untyped-def]
    self,
    backend_from: str,
    backend_to: str,
    *,
    target_bucket: str | None = None,
    prefix: str = "",
    dry_run: bool = False,
    checksum_verify: bool = False,
) -> dict:
    """NFR-013 §7.3 — migrate object storage between backends (AC-07).

    Thin Celery wrapper around :class:`scripts.storage.migrate.StorageMigrator`.
    Streams every object source → target with optional SHA-256 verification,
    logs the audited outcome, and returns the migration report. Retries on
    transient backend failures (the underlying run records per-object failures
    without aborting, so a retry resumes the not-yet-copied objects).
    """
    from app.common.async_bridge import run_async
    from scripts.storage.migrate import migrate

    logger.info(
        "storage_migrate_started",
        backend_from=backend_from,
        backend_to=backend_to,
        target_bucket=target_bucket,
        prefix=prefix or None,
        dry_run=dry_run,
        checksum_verify=checksum_verify,
    )
    try:
        report = run_async(
            migrate(
                backend_from=backend_from,
                backend_to=backend_to,
                target_bucket=target_bucket,
                prefix=prefix,
                dry_run=dry_run,
                checksum_verify=checksum_verify,
            )
        )
    except Exception as exc:  # noqa: BLE001 — retry on transient backend errors
        logger.error(
            "storage_migrate_failed",
            backend_from=backend_from,
            backend_to=backend_to,
            error=str(exc),
        )
        raise self.retry(exc=exc) from exc

    result = report.as_dict()
    logger.info("storage_migrate_audit", **result)
    return result


@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)  # type: ignore[misc]
def migrate_photo_refs(self, *, dry_run: bool = False) -> dict:  # type: ignore[no-untyped-def]
    """NFR-013 §2.2 / AC-09 — normalise legacy ``photo_refs`` to attachment ids.

    Idempotent and non-destructive: already-normalised lists are a no-op and
    unresolvable values are kept verbatim. Returns the migration report.
    """
    from app.migrations.migrate_photo_refs import run

    try:
        report = run(dry_run=dry_run)
    except Exception as exc:  # noqa: BLE001 — retry on transient DB errors
        logger.error("migrate_photo_refs_failed", error=str(exc))
        raise self.retry(exc=exc) from exc

    result = report.as_dict()
    logger.info("migrate_photo_refs_audit", **result)
    return result
