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
from app.common.log_privacy import loggable_error
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

    # #1760 — an erasure or delete that ran while the renditions were rendered
    # removed the original and its renditions already; the ones just written
    # would stay with nothing pointing at them. Undo them.
    # The record outlives Phase 0 of an Art. 17 erasure (the ArangoDB plan runs
    # after it), so the original's presence is checked too.
    # #1770 — the renditions belong to the *object*, which other uploaders'
    # records may share: this record being gone discards them only when no
    # other record holds the object either.
    if not await _object_exists(storage, attachment.storage_key) or (
        repo.get(attachment_id, tenant_key) is None
        and attachment.storage_key
        not in repo.storage_keys_held_elsewhere(
            tenant_key=tenant_key, storage_keys=[attachment.storage_key], excluding=[attachment_id]
        )
    ):
        for thumb in renditions:
            await storage.delete_object(thumbnail_key(attachment.storage_key, thumb.size))
        logger.info("thumbnails_discarded_after_delete", tenant_key=tenant_key, attachment_id=attachment_id)
        return {"attachment_id": attachment_id, "generated": 0, "reason": "attachment_deleted"}

    logger.info(
        "thumbnails_generated",
        tenant_key=tenant_key,
        attachment_id=attachment_id,
        generated=generated,
    )
    return {"attachment_id": attachment_id, "generated": generated}


async def _object_exists(storage, key: str) -> bool:  # type: ignore[no-untyped-def]
    from app.common.exceptions import NotFoundError

    try:
        await storage.head_object(key)
    except NotFoundError:
        return False
    return True


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
            error=loggable_error(exc),
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
            error=loggable_error(exc),
        )
        raise self.retry(exc=exc) from exc

    result = report.as_dict()
    logger.info("storage_migrate_audit", **result)
    return result


@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)  # type: ignore[misc]
def migrate_photo_refs(self, *, dry_run: bool = True) -> dict:  # type: ignore[no-untyped-def]
    """NFR-013 §2.2 / AC-09 — rewrite legacy ``photo_refs`` API URIs to attachment ids.

    Idempotent and non-destructive: already-normalised lists are a no-op and every
    value the normaliser cannot rewrite — a storage key included — is kept
    verbatim. Returns the migration report.

    **Defaults to ``dry_run=True`` since #1438**, which changes what a manual
    trigger without arguments does: it reports instead of writing. The rewrite is
    irreversible and this migration's premise was wrong once already (it reduced
    working storage-key references to ids that resolve to nothing), so applying it
    is now an explicit ``dry_run=False``.
    """
    from app.migrations.migrate_photo_refs import run

    try:
        report = run(dry_run=dry_run)
    except Exception as exc:  # noqa: BLE001 — retry on transient DB errors
        logger.error("migrate_photo_refs_failed", error=loggable_error(exc))
        raise self.retry(exc=exc) from exc

    result = report.as_dict()
    logger.info("migrate_photo_refs_audit", **result)
    return result


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
            else:
                # Gone between the query and the delete — a manual
                # ``DELETE /attachments/{id}``, or a concurrent sweep.
                # Counted, so ``found`` and ``deleted + failed + skipped`` keep adding
                # up; the sibling task upholds the same invariant and the comment
                # above claims it.
                skipped += 1
        except Exception as exc:  # noqa: BLE001 — keep the batch draining
            failed += 1
            logger.warning(
                "orphan_photo_delete_failed",
                attachment_id=attachment.key,
                tenant_key=attachment.tenant_key,
                error=loggable_error(exc),
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

    **Off unless ``STORAGE_TASK_PHOTO_ORPHAN_HOURS`` is set to a positive number of
    hours, and 0 is the shipped default.** Four review rounds on #1424 each found a
    way this job destroyed a photo something still referenced, every one of them a
    ``photo_refs`` spelling the resolver did not know. The resolver now protects any
    photo whose key is *mentioned* by any reference, which closes the class rather
    than its fourth instance — but a job that deletes data over a reference history
    spanning every client version and a manual migration does not go live in its
    first release. Everything else in #1393 works with it off; what stays is the
    quota leak, which is where it already was.

    A disabled sweep returns without querying rather than sweeping with a zero-hour
    floor: that floor would delete the photo a user is at that moment filling a form
    around.
    """
    hours = settings.storage_task_photo_orphan_hours
    if hours <= 0:
        logger.info("cleanup_orphaned_task_photos_disabled")
        return {"found": 0, "deleted": 0, "failed": 0, "skipped": 0, "freed_bytes": 0, "disabled": True}

    try:
        result = asyncio.run(_cleanup_orphaned_task_photos(hours, limit))
    except Exception as exc:  # noqa: BLE001 — retry on any transient failure
        logger.error("cleanup_orphaned_task_photos_failed", error=loggable_error(exc))
        raise self.retry(exc=exc) from exc

    logger.info("cleanup_orphaned_task_photos_audit", **result)
    return result
