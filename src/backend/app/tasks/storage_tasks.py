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
from datetime import UTC, datetime, timedelta

import structlog

from app.common.dependencies import get_attachment_repo, get_object_storage
from app.config.settings import settings
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


async def _delete_attachments(attachment_ids: list[str], tenant_key: str) -> dict:
    """Delete each id through the tenant-scoped service, tolerating the already-gone.

    **Only the ids nothing still references.** ``AttachmentService.upload``
    deduplicates by sha256 across the whole tenant and across categories, so the same
    stored object can sit in a second task's ``photo_refs`` or be a plant gallery's
    cover. Deleting a task's list verbatim destroyed those too and left the other
    references dangling — the shared-object case the caller cannot see from where it
    stands.

    An id that is still linked is simply left alone: whoever holds that link owns it,
    and the nightly sweep collects the photo if the link later goes away.
    """
    from app.common.dependencies import get_attachment_repo, get_attachment_service

    requested = list(attachment_ids)
    attachment_ids = get_attachment_repo().unreferenced_among(requested, tenant_key)
    still_referenced = len(requested) - len(attachment_ids)

    service = get_attachment_service()
    deleted = 0
    failed = 0
    skipped = 0
    for attachment_id in attachment_ids:
        # Idempotent by contract: an unknown id returns False rather than raising,
        # which is what lets this task be retried and lets a task deletion race a
        # manual one without either failing.
        #
        # Isolated per row: one unreachable storage object must not abort the batch.
        # Without this a single bad row takes its siblings down with it on every
        # retry, and they are never collected.
        try:
            if await service.delete(attachment_id, tenant_key):
                deleted += 1
            else:
                # Already gone, or an id that never resolved — a legacy URI still
                # sitting in `photo_refs` on an un-migrated installation reaches here
                # verbatim. Counted so the audit line adds up rather than quietly
                # losing rows between `requested` and `deleted`.
                skipped += 1
        except Exception as exc:  # noqa: BLE001 — one bad row, not a bad batch
            failed += 1
            logger.warning(
                "delete_attachment_failed",
                tenant_key=tenant_key,
                attachment_id=attachment_id,
                error=str(exc),
            )
    return {
        "requested": len(requested),
        "deleted": deleted,
        "failed": failed,
        "skipped": skipped,
        "still_referenced": still_referenced,
        "tenant_key": tenant_key,
    }


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)  # type: ignore[misc]
def delete_attachments(self, attachment_ids: list[str], tenant_key: str) -> dict:  # type: ignore[no-untyped-def]
    """Delete a known set of attachments, storage objects and thumbnails included (#1393).

    Dispatched by ``TaskService.delete_task`` so a deleted task does not leave its
    photos behind, counting against the tenant's quota with no surface that reaches
    them. Out of band because the service is synchronous and deletion is not: the
    same lazy-import-and-``delay`` shape ``AttachmentService._dispatch_thumbnails``
    already uses.

    If the dispatch or the task is lost, ``cleanup_orphaned_task_photos`` collects
    the same rows on its next run — this makes the deletion prompt, the sweep makes
    it certain.
    """
    if not attachment_ids:
        return {
            "requested": 0,
            "deleted": 0,
            "failed": 0,
            "skipped": 0,
            "still_referenced": 0,
            "tenant_key": tenant_key,
        }
    try:
        return asyncio.run(_delete_attachments(list(attachment_ids), tenant_key))
    except Exception as exc:  # noqa: BLE001 — retry on any transient failure
        logger.error(
            "delete_attachments_failed",
            tenant_key=tenant_key,
            count=len(attachment_ids),
            error=str(exc),
        )
        raise self.retry(exc=exc) from exc


async def _cleanup_orphaned_task_photos(older_than_hours: int, limit: int) -> dict:
    from app.common.dependencies import get_attachment_repo, get_attachment_service

    cutoff = datetime.now(UTC) - timedelta(hours=older_than_hours)
    orphans = get_attachment_repo().find_orphaned_task_photos(older_than=cutoff, limit=limit)

    service = get_attachment_service()
    deleted = 0
    failed = 0
    freed_bytes = 0
    skipped = 0
    for attachment in orphans:
        if attachment.key is None:
            # Counted, not silently dropped: `found` and `deleted + failed + skipped`
            # have to add up, or a row the sweep can never process leaves no trace in
            # the audit line and the job looks like it did more than it did.
            skipped += 1
            continue
        # Isolated per row, and this one matters more than the batch above.
        # The query is ``SORT att.created_at ASC``, so a retry re-fetches the same
        # head rows: one permanently unhealthy attachment would starve every younger
        # orphan behind it for ever, and the sweep would look like it was merely
        # retrying while it had in fact stopped working.
        try:
            if await service.delete(attachment.key, attachment.tenant_key):
                deleted += 1
                freed_bytes += attachment.byte_size
        except Exception as exc:  # noqa: BLE001 — keep the batch draining
            failed += 1
            logger.warning(
                "orphan_photo_delete_failed",
                attachment_id=attachment.key,
                tenant_key=attachment.tenant_key,
                error=str(exc),
            )
    return {
        "found": len(orphans),
        "deleted": deleted,
        "failed": failed,
        "skipped": skipped,
        "freed_bytes": freed_bytes,
        "cutoff": cutoff.isoformat(),
    }


@celery_app.task(bind=True, max_retries=3, default_retry_delay=600)  # type: ignore[misc]
def cleanup_orphaned_task_photos(self, *, limit: int = 500) -> dict:  # type: ignore[no-untyped-def]
    """Collect task photos that nothing references any more (#1393).

    Three paths produce them, and this covers all three: an upload whose form was
    never submitted, a photo removed from the staging area before submitting (the
    remove button drops local state), and a photo whose task was deleted.

    They are not an exposure — every orphan stays tenant-scoped, permission-gated
    and inside the NFR-011 retention scope — but ``AttachmentService._enforce_quota``
    counts every attachment row against ``STORAGE_TENANT_QUOTA_MB``, linked or not.
    So the bytes accumulate in exactly the installations that use task photos most,
    and no UI reaches them for the ``task`` category.

    **Disabled by setting ``STORAGE_TASK_PHOTO_ORPHAN_HOURS`` to 0**, which returns
    without querying rather than sweeping with a zero-hour floor — a floor of zero
    would delete the photo a user is at that moment filling a form around.
    """
    hours = settings.storage_task_photo_orphan_hours
    if hours <= 0:
        logger.info("cleanup_orphaned_task_photos_disabled")
        return {"found": 0, "deleted": 0, "failed": 0, "skipped": 0, "freed_bytes": 0, "disabled": True}

    try:
        result = asyncio.run(_cleanup_orphaned_task_photos(hours, limit))
    except Exception as exc:  # noqa: BLE001 — retry on any transient failure
        logger.error("cleanup_orphaned_task_photos_failed", error=str(exc))
        raise self.retry(exc=exc) from exc

    logger.info("cleanup_orphaned_task_photos_audit", **result)
    return result
