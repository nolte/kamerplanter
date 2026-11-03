"""REQ-053 GP-FR-105 / GP-NFR-016 — the daily consistency job of the bed log (WP 8.2, #2645).

Its own beat task (NFR-011 §3.1: no master task). It finds the domain events of the last
``CARE_EVENTS_CONSISTENCY_WINDOW_DAYS`` days that have no care event and writes them with the mapper of the M4
backfill (``trigger = backfill``). The rules live in :class:`CareEventConsistencyService`; this module wires them and
asks the tenant gate: a tenant that is not ``active`` is not written into (REQ-056 §5.2, ``ActiveTenants``).
"""

from __future__ import annotations

from datetime import UTC, datetime

import structlog

from app.config.settings import settings
from app.tasks import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(  # type: ignore[untyped-decorator]
    name="care_events.consistency",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=1800,
    max_retries=3,
    default_retry_delay=300,
)
def run_care_events_consistency() -> dict[str, object]:
    """Close the care-event gaps of the last N days; idempotent, the next run finds none.

    Logs ``care_events_consistency.completed`` (duration, hits) and warns above 100 hits. A failure is logged with
    its type and re-raised so ``autoretry_for`` applies.
    """
    from app.common.dependencies import get_care_event_gap_reader, get_care_event_repo, get_tenant_repo
    from app.domain.services.care_event_consistency_service import CareEventConsistencyService
    from app.tasks.tenant_gate import ActiveTenants

    service = CareEventConsistencyService(
        get_care_event_gap_reader(), get_care_event_repo(), ActiveTenants(get_tenant_repo())
    )
    try:
        report = service.run(now=datetime.now(UTC), window_days=settings.care_events_consistency_window_days)
    except Exception as exc:
        logger.error("care_events.consistency.failed", error_type=type(exc).__name__)
        raise
    return {
        "hits": report.hits,
        "backfilled": dict(report.backfilled),
        "without_bed": dict(report.without_bed),
        "skipped_inactive_tenant": report.skipped_inactive_tenant,
        "already_present": report.already_present,
        "no_timestamp": report.no_timestamp,
        "errors": report.errors,
    }
