"""The daily consistency job of the bed log (REQ-053 GP-FR-105, GP-NFR-016, GP-NFR-063; WP 8.2, #2645).

A domain event (``watering_events``, ``feeding_events``, ``treatment_applications``, ``harvest_batches``) written by a
path that does not log the care event itself leaves a gap in the bed log. This job finds the gaps of the last N days
and closes them with the mapper of the M4 backfill (:mod:`app.domain.engines.care_event_backfill_mapper`,
``trigger = backfill``) — the same rules, the same scan, no second mapping path.

* **Tenant.** The bed's site decides the tenant (the mapper). A tenant that is not ``active`` is left alone like by
  every other beat (REQ-056 §5.2); its gap is closed once it is active again, while it lies inside the window.
* **Idempotent.** The unique-sparse ``source_ref`` index decides "already logged"; the next run finds 0 gaps.
* **Signals.** One structlog event with the duration and the hit count (events written), the counter
  ``care_events_consistency_backfilled_total{source}``, and a warning above :data:`ALERT_THRESHOLD` hits in one run
  (GP-NFR-063): a run that has to repair that many means a writer stopped logging.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

import structlog

from app.domain.engines.care_event_backfill_mapper import (
    SOURCE_COLLECTIONS,
    SkipReason,
    map_document,
    performed_at_of,
    resolve_anchor,
)
from app.domain.interfaces.care_event_gap_reader import ICareEventGapReader
from app.domain.interfaces.care_event_repository import ICareEventRepository
from app.domain.models.care_event import CareEvent
from app.observability.garden_plan_metrics import record_care_event_backfilled

logger = structlog.get_logger(__name__)

#: A run that writes MORE than this many events logs a warning (GP-NFR-063): 100 is quiet, 101 is not.
ALERT_THRESHOLD = 100

#: Events per write transaction.
_BATCH_SIZE = 200


@dataclass
class ConsistencyReport:
    """What one run found, by source."""

    window_days: int
    backfilled: dict[str, int] = field(default_factory=lambda: dict.fromkeys(SOURCE_COLLECTIONS, 0))
    without_bed: dict[str, int] = field(default_factory=lambda: dict.fromkeys(SOURCE_COLLECTIONS, 0))
    skipped_inactive_tenant: int = 0
    already_present: int = 0
    #: A document whose instant the mapper cannot read: never written, counted so it is not invisible.
    no_timestamp: int = 0
    #: A document the mapper or the model refused, and a batch the database refused: logged, the run goes on.
    errors: int = 0

    @property
    def hits(self) -> int:
        return sum(self.backfilled.values())


class CareEventConsistencyService:
    def __init__(
        self,
        gaps: ICareEventGapReader,
        events: ICareEventRepository,
        tenant_is_active: Callable[[str], bool],
    ) -> None:
        self._gaps = gaps
        self._events = events
        self._tenant_is_active = tenant_is_active

    def run(self, *, now: datetime, window_days: int) -> ConsistencyReport:
        """Close the gaps of the last ``window_days`` days; returns what was found."""
        started = time.monotonic()
        since = now.astimezone(UTC) - timedelta(days=window_days)
        report = ConsistencyReport(window_days=window_days)
        for source in SOURCE_COLLECTIONS:
            self._close_source(source, since, report)
        duration = round(time.monotonic() - started, 3)
        logger.info(
            "care_events_consistency.completed",
            duration_seconds=duration,
            hits=report.hits,
            backfilled=report.backfilled,
            without_bed=report.without_bed,
            skipped_inactive_tenant=report.skipped_inactive_tenant,
            already_present=report.already_present,
            no_timestamp=report.no_timestamp,
            errors=report.errors,
            window_days=window_days,
        )
        if report.hits > ALERT_THRESHOLD:
            logger.warning(
                "care_events_consistency.threshold_exceeded",
                hits=report.hits,
                threshold=ALERT_THRESHOLD,
                backfilled=report.backfilled,
            )
        return report

    def _close_source(self, source: str, since: datetime, report: ConsistencyReport) -> None:
        pending: list[CareEvent] = []
        is_active = self._tenant_is_active
        row: dict[str, Any]
        for row in self._gaps.candidates(source, since):
            if row.get("present"):
                report.already_present += 1
                continue
            performed_at = performed_at_of(row["doc"], source)
            if performed_at is None:
                report.no_timestamp += 1
                continue
            anchor = resolve_anchor(row)
            if isinstance(anchor, SkipReason):
                report.without_bed[source] += 1
                continue
            if not is_active(anchor.tenant_key):
                report.skipped_inactive_tenant += 1
                continue
            try:
                pending += [map_document(source, row["doc"], anchor, performed_at)]
            except ValueError as exc:  # pydantic's ValidationError is one: a bad document must not stop the run
                report.errors += 1
                logger.error(
                    "care_events_consistency.document_refused",
                    source=source,
                    document_key=str(row["doc"].get("_key")),
                    error_type=type(exc).__name__,
                )
                continue
            if len(pending) >= _BATCH_SIZE:
                self._flush(source, pending, report)
        self._flush(source, pending, report)

    def _flush(self, source: str, pending: list[CareEvent], report: ConsistencyReport) -> None:
        by_tenant: dict[str, list[CareEvent]] = {}
        for event in pending:
            by_tenant.setdefault(event.tenant_key, []).append(event)
        for tenant_key, events in by_tenant.items():
            try:
                written, already = self._events.insert_backfilled(events, tenant_key=tenant_key)
            except Exception as exc:  # noqa: BLE001 - one refused batch must not stop the other sources
                report.errors += 1
                logger.error(
                    "care_events_consistency.batch_failed",
                    source=source,
                    size=len(events),
                    error_type=type(exc).__name__,
                )
                continue
            report.already_present += already
            if written:
                report.backfilled[source] += written
                record_care_event_backfilled(source, written)
        del pending[:]
