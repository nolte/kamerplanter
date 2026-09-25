"""Celery tasks for NFR-011 retention policy enforcement.

The retention concerns bundled here, all backed by REQ-025 PrivacyService:

- ``process_data_export`` — fan-out task fired when a user requests a
  GDPR Art. 15/20 export. Walks the user's data, builds a JSON manifest,
  uploads it to object storage (NFR-013), and flips the request to
  ``status=completed`` with the NFR-011 R-05 expiry (default 72 hours,
  ``RETENTION_EXPORT_FILE_RETENTION_HOURS``).
- ``execute_scheduled_erasures`` — daily beat task that hard-deletes
  users whose ErasureRequest passed the NFR-011 R-01 soft-delete grace
  period (default 90 days, ``RETENTION_SOFT_DELETE_RETENTION_DAYS``;
  REQ-025 Art. 17).
- ``expire_email_change_requests`` — hourly beat task that marks
  unconfirmed email changes past their NFR-011 R-07 ``expires_at``
  (default 24 h, ``RETENTION_EMAIL_CHANGE_RETENTION_HOURS``) as
  ``status=expired``.
- ``expire_data_exports`` — hourly beat task that flips completed
  exports past their ``expires_at`` to ``status=expired`` and removes
  the underlying download.
- ``redispatch_stale_pending_exports`` — hourly safety-net beat task
  that re-enqueues ``process_data_export`` for exports whose original
  dispatch was lost (broker outage or legacy ``pending`` records).
- ``purge_expired_erasure_records`` — daily beat task that hard-deletes
  completed erasure records past the NFR-011 R-06 period (default one
  year after completion, ``RETENTION_ERASURE_AUDIT_RETENTION_YEARS``).

The actual data-walk, manifest-build, soft/hard-delete and expiry
logic lives in ``PrivacyService``; these tasks are thin schedulers
that bridge Celery to the async service layer.
"""

from datetime import UTC, datetime, timedelta

import structlog

from app.tasks import celery_app
from app.tasks.task_bridge import TaskAttempt, run_async_task

logger = structlog.get_logger(__name__)

STALE_EXPORT_REDISPATCH_AFTER_MINUTES = 15


@run_async_task(  # type: ignore[misc]
    name="retention.process_data_export",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=5,
)
async def process_data_export(attempt: TaskAttempt, export_key: str) -> dict:
    """Build the export bundle and flip the request to a terminal state.

    Triggered by ``PrivacyService.request_data_export`` via ``.delay`` once the
    request record exists. The ``run_async_task`` decorator bridges the
    coroutine to Celery and logs/re-raises failures.

    **Retry policy (#1666).** The service ends a request as ``failed`` at once
    only for failures a retry would repeat (no bundle can be produced, a domain
    error). An infrastructure failure — object storage, database — propagates
    while attempts remain, so ``autoretry_for`` with backoff actually runs; the
    request stays ``processing`` meanwhile and the retry resumes it
    (``is_retry``). Only the last attempt (``retries == max_retries``) records
    ``failed``. ``attempt`` is the bridge's snapshot of the retry position —
    ``self.request`` would read empty on the coroutine's thread. Before #1666
    the service swallowed every exception, so an outage ended the Art. 15
    request on the first attempt and the declared five retries never fired.
    """

    from app.common.dependencies import get_privacy_service

    service = get_privacy_service()
    result = await service.process_data_export(
        export_key,
        final_attempt=attempt.is_final,
        is_retry=attempt.is_retry,
    )
    status = result.status if result else "unknown"
    # The event name follows the outcome: an operator reading "completed" must
    # be reading a delivered bundle, not a failed or skipped request (#1666).
    if status == "completed":
        logger.info(
            "retention.process_data_export.completed",
            export_key=export_key,
            status=status,
            attempt=attempt.number,
            file_size_bytes=result.file_size_bytes if result else None,
        )
    else:
        logger.warning(
            "retention.process_data_export.not_completed",
            export_key=export_key,
            status=status,
            attempt=attempt.number,
        )
    return {
        "export_key": export_key,
        "status": status,
    }


@run_async_task(  # type: ignore[misc]
    name="retention.execute_scheduled_erasures",
    autoretry_for=(ConnectionError, TimeoutError),
    max_retries=3,
    default_retry_delay=300,
)
async def execute_scheduled_erasures() -> dict:
    """Hard-delete users past their NFR-011 R-01 soft-delete grace period.

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
    """Flip email-change requests past their R-07 ``expires_at`` to ``status=expired``."""

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
    """Delete the bundles of exports past their 72-hour expiry, then mark them ``expired``.

    The order is the point (#1767 GDPR-005): a bundle whose delete failed keeps
    its record unexpired and is retried on the next hourly run.
    """

    from app.common.dependencies import get_privacy_service

    service = get_privacy_service()
    expired = await service.expire_data_exports(now=datetime.now(UTC))
    logger.info(
        "retention.expire_data_exports.completed",
        expired=expired,
    )
    return {"expired": expired}


@run_async_task(  # type: ignore[misc]
    name="retention.purge_expired_erasure_records",
    autoretry_for=(ConnectionError, TimeoutError),
    max_retries=3,
    default_retry_delay=300,
)
async def purge_expired_erasure_records() -> dict:
    """Hard-delete completed erasure records past the NFR-011 R-06 period (#1772).

    Only ``completed`` records whose completion lies more than
    ``settings.retention_erasure_audit_retention_years`` back go; an open
    request is never touched, nor a completed one still carrying a plaintext
    ``user_key`` (held and counted, #1773 review GDPR-006). The service logs
    the counts, never a key.
    """

    from app.common.dependencies import get_privacy_service

    service = get_privacy_service()
    result = await service.purge_expired_erasure_records(now=datetime.now(UTC))
    return {"purged": result.purged, "held_without_tombstone": result.held_without_tombstone}


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
