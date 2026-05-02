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

The actual data-walk, manifest-build, soft/hard-delete and expiry
logic lives in ``PrivacyService``; these tasks are thin schedulers
that bridge Celery to the async service layer.
"""

import asyncio
from datetime import UTC, datetime

import structlog

from app.tasks import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(name="retention.process_data_export")
def process_data_export(export_key: str) -> dict:
    """Build the export bundle and flip the request to completed.

    Triggered by ``PrivacyService.request_data_export`` via
    ``celery_app.send_task`` once the request record exists.
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


@celery_app.task(name="retention.execute_scheduled_erasures")
def execute_scheduled_erasures() -> dict:
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


@celery_app.task(name="retention.expire_email_change_requests")
def expire_email_change_requests() -> dict:
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


@celery_app.task(name="retention.expire_data_exports")
def expire_data_exports() -> dict:
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
