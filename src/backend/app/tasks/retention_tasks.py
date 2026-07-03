"""Celery tasks for NFR-011 retention policy enforcement.

Three concerns are bundled here, all backed by REQ-025 PrivacyService:

- ``process_data_export`` — fan-out task fired when a user requests a
  GDPR Art. 15/20 export. Walks the user's data, builds a JSON manifest,
  uploads it to object storage (NFR-013), and flips the request to
  ``status=completed`` with a 72-hour expiry.
- ``execute_scheduled_erasures`` — daily beat task that hard-deletes
  users whose ErasureRequest passed the 90-day soft-delete grace period
  (REQ-025 Art. 17).
- ``expire_email_change_requests`` — hourly beat task that marks
  unconfirmed email changes older than 24 h as ``status=expired``.
- ``expire_data_exports`` — hourly beat task that flips completed
  exports past their ``expires_at`` to ``status=expired`` and removes
  the underlying download.
- ``redispatch_stale_pending_exports`` — hourly safety-net beat task
  that re-enqueues ``process_data_export`` for exports whose original
  dispatch was lost (broker outage or legacy ``pending`` records).

The actual data-walk, manifest-build, soft/hard-delete and expiry
logic lives in ``PrivacyService``; these tasks are thin schedulers
that bridge Celery to the async service layer.
"""

import asyncio
from datetime import UTC, datetime, timedelta

import structlog

from app.tasks import celery_app

logger = structlog.get_logger(__name__)

STALE_EXPORT_REDISPATCH_AFTER_MINUTES = 15


@celery_app.task(  # type: ignore[misc]
    name="retention.process_data_export",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=5,
)
def process_data_export(self, export_key: str) -> dict:  # type: ignore[no-untyped-def]
    """Build the export bundle and flip the request to completed.

    Triggered by ``PrivacyService.request_data_export`` via ``.delay`` once the
    request record exists. Idempotent — the service skips non-``pending``
    exports — so ``autoretry_for=(Exception,)`` may retry broadly (bounded by
    ``max_retries`` + backoff).
    """

    from app.common.dependencies import get_privacy_service

    service = get_privacy_service()
    try:
        result = asyncio.run(service.process_data_export(export_key))
        logger.info(
            "retention.process_data_export.completed",
            export_key=export_key,
            file_size_bytes=result.file_size_bytes if result else None,
        )
        return {
            "export_key": export_key,
            "status": result.status if result else "unknown",
        }
    except Exception as exc:  # pragma: no cover - logged + re-raised
        logger.exception(
            "retention.process_data_export.failed",
            export_key=export_key,
            error=str(exc),
        )
        raise


@celery_app.task(  # type: ignore[misc]
    name="retention.execute_scheduled_erasures",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    max_retries=3,
    default_retry_delay=300,
)
def execute_scheduled_erasures(self) -> dict:  # type: ignore[no-untyped-def]
    """Hard-delete users past their 90-day soft-delete grace period.

    Runs daily. Picks up every ``ErasureRequest`` with
    ``hard_delete_scheduled_at <= now`` and finalises the deletion via
    the PrivacyService erasure pipeline.
    """

    from app.common.dependencies import get_privacy_service

    service = get_privacy_service()
    try:
        processed = asyncio.run(service.execute_scheduled_erasures(now=datetime.now(UTC)))
        logger.info(
            "retention.execute_scheduled_erasures.completed",
            processed=processed,
        )
        return {"processed": processed}
    except Exception as exc:  # pragma: no cover
        logger.exception(
            "retention.execute_scheduled_erasures.failed",
            error=str(exc),
        )
        raise


@celery_app.task(  # type: ignore[misc]
    name="retention.expire_email_change_requests",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    max_retries=3,
    default_retry_delay=300,
)
def expire_email_change_requests(self) -> dict:  # type: ignore[no-untyped-def]
    """Flip stale email-change requests (>24 h) to ``status=expired``."""

    from app.common.dependencies import get_privacy_service

    service = get_privacy_service()
    try:
        expired = asyncio.run(service.expire_email_change_requests(now=datetime.now(UTC)))
        logger.info(
            "retention.expire_email_change_requests.completed",
            expired=expired,
        )
        return {"expired": expired}
    except Exception as exc:  # pragma: no cover
        logger.exception(
            "retention.expire_email_change_requests.failed",
            error=str(exc),
        )
        raise


@celery_app.task(  # type: ignore[misc]
    name="retention.expire_data_exports",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    max_retries=3,
    default_retry_delay=300,
)
def expire_data_exports(self) -> dict:  # type: ignore[no-untyped-def]
    """Flip completed exports past their 72-hour expiry to ``status=expired``."""

    from app.common.dependencies import get_privacy_service

    service = get_privacy_service()
    try:
        expired = asyncio.run(service.expire_data_exports(now=datetime.now(UTC)))
        logger.info(
            "retention.expire_data_exports.completed",
            expired=expired,
        )
        return {"expired": expired}
    except Exception as exc:  # pragma: no cover
        logger.exception(
            "retention.expire_data_exports.failed",
            error=str(exc),
        )
        raise


@celery_app.task(  # type: ignore[misc]
    name="retention.redispatch_stale_pending_exports",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    max_retries=3,
    default_retry_delay=300,
)
def redispatch_stale_pending_exports(self) -> dict:  # type: ignore[no-untyped-def]
    """Re-enqueue pending exports whose original dispatch was lost.

    Safety net for broker outages during ``PrivacyService.request_data_export``
    and for legacy ``pending`` records created before the dispatch existed.
    Idempotent: the worker skips non-``pending`` exports.
    """
    from app.common.dependencies import get_data_export_repo

    repo = get_data_export_repo()
    cutoff = datetime.now(UTC) - timedelta(minutes=STALE_EXPORT_REDISPATCH_AFTER_MINUTES)
    stale = repo.list_stale_pending(cutoff.isoformat())
    for export in stale:
        if export.key:
            process_data_export.delay(export.key)
    if stale:
        logger.info("retention.redispatch_stale_pending_exports", redispatched=len(stale))
    return {"redispatched": len(stale)}
