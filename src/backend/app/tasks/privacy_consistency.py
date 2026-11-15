"""spec/privacy PRIV-206 / DEC-28 — the daily privacy consistency check, minimal form (E04).

Its own beat task (NFR-011 §3.1: no master task). Read-only and installation-wide: it counts
tombstones outside the allowlist per cell and changes nothing, so it asks no tenant gate. The rules
live in :class:`PrivacyConsistencyService`; this module wires them.
"""

from __future__ import annotations

import structlog

from app.tasks import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(  # type: ignore[untyped-decorator]
    name="privacy.consistency",
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_backoff_max=1800,
    max_retries=3,
    default_retry_delay=300,
)
def run_privacy_consistency() -> dict[str, object]:
    """Count the undeclared tombstones; returns the cells that hold any and their total.

    A failure is logged with its type and re-raised so ``autoretry_for`` applies to a connection
    problem; any other failure fails the run and the next day's run counts again.
    """
    from app.common.dependencies import get_tombstone_census
    from app.domain.services.privacy_consistency_service import PrivacyConsistencyService

    try:
        report = PrivacyConsistencyService(get_tombstone_census()).run()
    except Exception as exc:
        logger.error("privacy.consistency.failed", error_type=type(exc).__name__)
        raise
    return {"total": report.total, "findings": report.findings}
