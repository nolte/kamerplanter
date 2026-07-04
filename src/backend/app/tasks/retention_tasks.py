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

from datetime import UTC, datetime, timedelta

import structlog

from app.tasks import celery_app
from app.tasks.task_bridge import run_async_task

logger = structlog.get_logger(__name__)

STALE_EXPORT_REDISPATCH_AFTER_MINUTES = 15


@run_async_task(  # type: ignore[misc]
    name="retention.process_data_export",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=5,
)
async def process_data_export(export_key: str) -> dict:
    """Build the export bundle and flip the request to completed.

    Triggered by ``PrivacyService.request_data_export`` via ``.delay`` once the
    request record exists. Idempotent — the service skips non-``pending``
    exports — so ``autoretry_for=(Exception,)`` may retry broadly (bounded by
    ``max_retries`` + backoff). The ``run_async_task`` decorator bridges the
    coroutine to Celery and logs/re-raises failures.
    """

    from app.common.dependencies import get_privacy_service

    service = get_privacy_service()
    result = await service.process_data_export(export_key)
    logger.info(
        "retention.process_data_export.completed",
        export_key=export_key,
        file_size_bytes=result.file_size_bytes if result else None,
    )
    return {
        "export_key": export_key,
        "status": result.status if result else "unknown",
    }


@run_async_task(  # type: ignore[misc]
    name="retention.execute_scheduled_erasures",
    autoretry_for=(ConnectionError, TimeoutError),
    max_retries=3,
    default_retry_delay=300,
)
async def execute_scheduled_erasures() -> dict:
    """Hard-delete users past their 90-day soft-delete grace period.

    Runs daily. Picks up every ``ErasureRequest`` with
    ``hard_delete_scheduled_at <= now`` and finalises the deletion via
    the PrivacyService erasure pipeline.
    """

    from app.common.dependencies import get_privacy_service

    service = get_privacy_service()
    processed = await service.execute_scheduled_erasures(now=datetime.now(UTC))
    logger.info(
        "retention.execute_scheduled_erasures.completed",
        processed=processed,
    )
    return {"processed": processed}


@run_async_task(  # type: ignore[misc]
    name="retention.expire_email_change_requests",
    autoretry_for=(ConnectionError, TimeoutError),
    max_retries=3,
    default_retry_delay=300,
)
async def expire_email_change_requests() -> dict:
    """Flip stale email-change requests (>24 h) to ``status=expired``."""

    from app.common.dependencies import get_privacy_service

    service = get_privacy_service()
    expired = await service.expire_email_change_requests(now=datetime.now(UTC))
    logger.info(
        "retention.expire_email_change_requests.completed",
        expired=expired,
    )
    return {"expired": expired}


@run_async_task(  # type: ignore[misc]
    name="retention.expire_data_exports",
    autoretry_for=(ConnectionError, TimeoutError),
    max_retries=3,
    default_retry_delay=300,
)
async def expire_data_exports() -> dict:
    """Flip completed exports past their 72-hour expiry to ``status=expired``."""

    from app.common.dependencies import get_privacy_service

    service = get_privacy_service()
    expired = await service.expire_data_exports(now=datetime.now(UTC))
    logger.info(
        "retention.expire_data_exports.completed",
        expired=expired,
    )
    return {"expired": expired}


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
