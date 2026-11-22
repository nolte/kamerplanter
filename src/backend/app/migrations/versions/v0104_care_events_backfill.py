"""v0104 — REQ-053 ``M4_care_events_backfill`` (GP-FR-105, GP-NFR-015, E-11; WP 8.1, #2644): log the domain events.

**What.** The bed's care log (``care_events``) started with REQ-053; the four collections that recorded care before
it — ``watering_events``, ``feeding_events``, ``treatment_applications``, ``harvest_batches`` — have no line in it.
This version writes the missing lines: one ``care_event`` per source document, ``trigger = backfill``,
``source_ref = {collection, key}``, ``performed_at`` = the source's own instant. The mapping is the pure
:mod:`app.domain.engines.care_event_backfill_mapper`; this module reads, counts and writes.

**The tenant is the bed's, never the document's alone.** The bed comes from the document's references
(``plant -> slot -> location`` or the plant's own ``location_key``; a feeding's own ``location_key``), site and
tenant from the bed's site. A document whose own ``tenant_key`` (or whose plants') differs from the bed's site is
counted and never written. A document without a resolvable bed is counted, not written: no reference at all, a
reference that points at nothing, some resolved and some not, more than one bed, a site without a tenant.

**R-25 window.** Only documents whose instant lies inside the care-log retention period (NFR-011 R-25, default five
calendar years, the expression of the retention sweep) are considered; an older line would be anonymised by the next
sweep. They are counted as ``outside_r25``. A document without a readable instant is ``no_timestamp``.

**Performer.** ``performed_by_user_key`` only from an account reference of the source (``applied_by_key``,
``harvested_by_key``); otherwise ``null``. Display texts (``performed_by``, ``harvester``, ``applied_by``) and
``notes`` are free text a person typed and are not copied (SR-006); no value is invented (E-10).

**Idempotent (M-3).** The unique-sparse index ``care_events(tenant_key, source_ref.collection, source_ref.key)``
(WP 4.1) holds "already logged": the scan reads it per document and a second run finds every line present and
writes 0 rows. Lines a task completion wrote (``trigger = task``, same ``source_ref``) count as present too.

**Dry run (M-5, prod point P-6).** ``--dry-run`` writes nothing. The report is the same scan and the same mapper:
per source ``read``, ``will_write`` (``written`` in a real run), ``without_bed`` (split by reason, the first keys
listed), ``outside_r25``, ``already_present`` and ``no_timestamp``; they add up to ``read``
(``counts_add_up``). The operator reads the report on the prod copy before P-6.

**Reversible (M-6).** A line this migration wrote carries ``trigger = backfill`` and a ``source_ref`` naming one of
the four collections (the crop-rotation backfill of WP 3.4 has no ``source_ref`` and is never touched). ``down``
deletes those lines and their edges, except a line a person has since corrected, voided or redacted — those stay and
are counted (``kept_edited``). The source documents are never changed in either direction.

**Bounded memory.** The scan is a sorted non-streaming cursor consumed row by row; events are written in batches of
:data:`_BATCH_SIZE`, one transaction per tenant and batch (all or none).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, cast

import structlog
from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.config.settings import settings
from app.data_access.arango import collections as col
from app.data_access.arango.care_event_backfill_scan import scan_candidates
from app.data_access.arango.care_event_repository import ArangoCareEventRepository
from app.data_access.arango.transactions import stream_transaction
from app.domain.engines.care_event_backfill_mapper import (
    SOURCE_COLLECTIONS,
    TIME_FIELDS,
    TREATMENT_APPLICATIONS,
    SkipReason,
    action_filter,
    map_document,
    performed_at_of,
    resolve_anchor,
    window_start,
)
from app.domain.models.care_event import CareEvent
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)

#: How many keys a report lists per reason before it only counts.
_LISTED = 25

#: Events per write transaction, and scan rows per cursor batch.
_BATCH_SIZE = 200

#: Days the window starts later than the retention cutoff (see :func:`_run`).
_WINDOW_MARGIN_DAYS = 1

#: Seconds the server keeps the scan cursor between two fetches (renewed on every fetch).
_CURSOR_TTL_SECONDS = 600

#: Counts the sources by where their instant lies; one cheap pass, no lookups.
_COUNT_BY_WINDOW = """
FOR d IN @@source
  FILTER @action == null OR d.action == @action
  LET ts = DATE_TIMESTAMP(d[@time_field])
  COLLECT bucket = (ts == null ? "no_timestamp" : (ts < @cutoff_ms ? "outside_r25" : "in_window")) WITH COUNT INTO n
  RETURN { bucket, n }
"""

#: Lines of a backfill that no person touched since; ``kept_edited`` counts the others.
_DOWN_SCAN = """
FOR e IN @@events
  FILTER e.trigger == "backfill" AND e.source_ref.collection IN @sources
  LET edited = e.supersedes_key != null OR e.superseded_by_key != null OR e.voided_at != null OR e.redacted_at != null
  SORT e._key
  RETURN { key: e._key, edited }
"""

_DOWN_REMOVE_EDGES = """
FOR ed IN @@edges
  FILTER ed._from IN @ids
  REMOVE ed IN @@edges
  RETURN 1
"""

_DOWN_REMOVE_EVENTS = """
FOR key IN @keys
  REMOVE key IN @@events
  RETURN 1
"""


def _window_years() -> int:
    """The care-log retention period in calendar years (NFR-011 R-25); the sweep reads the same setting."""
    return int(settings.retention_care_event_retention_years)


def _empty_source() -> dict[str, Any]:
    return {
        "read": 0,
        "will_write": 0,
        "written": 0,
        "already_present": 0,
        "without_bed": 0,
        "without_bed_reasons": {},
        "outside_r25": 0,
        "no_timestamp": 0,
        "listed_keys": [],
    }


def _count_window(db: StandardDatabase, source: str, cutoff_ms: int) -> dict[str, int]:
    bind_vars: dict[str, Any] = {
        "@source": source,
        "time_field": TIME_FIELDS[source],
        "action": action_filter(source),
        "cutoff_ms": cutoff_ms,
    }
    cursor = cast(Cursor, db.aql.execute(_COUNT_BY_WINDOW, bind_vars=bind_vars))
    return {str(row["bucket"]): int(row["n"]) for row in cursor}


def _scan(db: StandardDatabase, source: str, cutoff_ms: int) -> Cursor:
    return scan_candidates(db, source, cutoff_ms, batch_size=_BATCH_SIZE, ttl_seconds=_CURSOR_TTL_SECONDS)


def _flush(
    repo: ArangoCareEventRepository, pending: list[tuple[str, CareEvent]], stats: dict[str, dict[str, Any]]
) -> None:
    """Write the pending events, one transaction per (source, tenant); fold what the unique index says into the counts.

    The scan already skipped what was logged at scan time, so ``already`` is only a line another writer logged
    in between: the document moves from ``will_write`` to ``already_present`` of its own source.
    """
    grouped: dict[tuple[str, str], list[CareEvent]] = {}
    for source, event in pending:
        grouped.setdefault((source, event.tenant_key), []).append(event)
    for (source, tenant_key), events in grouped.items():
        _, already = repo.insert_backfilled(events, tenant_key=tenant_key)
        stats[source]["will_write"] -= already
        stats[source]["already_present"] += already
    del pending[:]


def _process_source(
    db: StandardDatabase,
    repo: ArangoCareEventRepository,
    source: str,
    *,
    cutoff_ms: int,
    apply: bool,
    stats: dict[str, dict[str, Any]],
    pending: list[tuple[str, CareEvent]],
) -> None:
    """Classify every document of ``source`` and, when ``apply``, write the events batch by batch while reading.

    Dry run and real run take this one path; the only difference is the write at the batch boundary.
    """
    own = stats[source]
    windows = _count_window(db, source, cutoff_ms)
    own["outside_r25"] = windows.get("outside_r25", 0)
    own["no_timestamp"] = windows.get("no_timestamp", 0)
    own["read"] = own["outside_r25"] + own["no_timestamp"]
    row: dict[str, Any]
    for row in _scan(db, source, cutoff_ms):
        own["read"] += 1
        document: dict[str, Any] = row["doc"]
        key = str(document.get("_key"))
        if row.get("present"):
            own["already_present"] += 1
            continue
        performed_at = performed_at_of(document, source)
        if performed_at is None:  # the server read a date the mapper cannot: still never written
            own["no_timestamp"] += 1
            continue
        anchor = resolve_anchor(row, source)
        if isinstance(anchor, SkipReason):
            own["without_bed"] += 1
            reasons: dict[str, dict[str, Any]] = own["without_bed_reasons"]
            bucket = reasons.setdefault(anchor.value, {"count": 0, "listed": []})
            bucket["count"] += 1
            bucket_keys: list[str] = bucket["listed"]
            if len(bucket_keys) < _LISTED:
                bucket_keys.append(key)
            continue
        own["will_write"] += 1
        listed: list[str] = own["listed_keys"]
        if len(listed) < _LISTED:
            listed.append(key)
        # Dry run maps too: a document the mapper or the model refuses must fail the dry run, not only the real run.
        event = map_document(source, document, anchor, performed_at)
        if apply:
            pending += [(source, event)]
            if len(pending) >= _BATCH_SIZE:
                _flush(repo, pending, stats)


def _run(db: StandardDatabase, *, apply: bool, now: datetime, years: int) -> tuple[int, dict[str, Any], int]:
    """Process the four sources; returns ``(written or planned, details, read)``."""
    # One day of margin: the retention sweep runs later with a later cutoff and must not anonymise a line this run
    # just wrote. A treatment keeps the longer PflSchG period (R-17) like the sweep (``care_event_pflschg_cutoff``).
    cutoff: datetime = window_start(now, years) + timedelta(days=_WINDOW_MARGIN_DAYS)
    treatment_cutoff: datetime = window_start(
        now, max(years, int(settings.retention_treatment_min_retention_years))
    ) + timedelta(days=_WINDOW_MARGIN_DAYS)
    repo = ArangoCareEventRepository(db)
    stats: dict[str, dict[str, Any]] = {source: _empty_source() for source in SOURCE_COLLECTIONS}
    pending: list[tuple[str, CareEvent]] = []
    for source in SOURCE_COLLECTIONS:
        if not db.has_collection(source):
            continue
        source_cutoff = treatment_cutoff if source == TREATMENT_APPLICATIONS else cutoff
        _process_source(
            db, repo, source, cutoff_ms=int(source_cutoff.timestamp() * 1000), apply=apply, stats=stats, pending=pending
        )
        if apply and pending:
            _flush(repo, pending, stats)
    if apply:
        for entry in stats.values():
            entry["written"] = entry["will_write"]
    totals = {
        key: sum(int(entry[key]) for entry in stats.values())
        for key in ("read", "will_write", "written", "already_present", "without_bed", "outside_r25", "no_timestamp")
    }
    totals["counts_add_up"] = totals["read"] == (
        totals["will_write"]
        + totals["already_present"]
        + totals["without_bed"]
        + totals["outside_r25"]
        + totals["no_timestamp"]
    )
    details: dict[str, Any] = {
        "window_start": cutoff.isoformat(),
        "treatment_window_start": treatment_cutoff.isoformat(),
        "retention_years": years,
        "sources": stats,
        "totals": totals,
    }
    changed = totals["written"] if apply else totals["will_write"]
    return changed, details, totals["read"]


class CareEventsBackfillMigration(Migration):
    version = "0104"
    name = "care_events_backfill"
    description = (
        "REQ-053 M4 (GP-FR-105): log watering_events, feeding_events, treatment_applications and harvest_batches "
        "as care_events (trigger=backfill, source_ref); tenant from the bed's site, R-25 window only, no performer "
        "without an account reference; dry run reports read/written/without bed/outside R-25 per source."
    )
    reversible = True

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        if not db.has_collection(col.CARE_EVENTS):
            return MigrationReport(
                version=self.version, name=self.name, scanned=0, changed=0, dry_run=dry_run, details={}
            )
        changed, details, read = _run(db, apply=not dry_run, now=datetime.now(UTC), years=_window_years())
        if dry_run:
            logger.info("care_events_backfill_dry_run", pending_changes=changed, details=details)
            return MigrationReport(
                version=self.version, name=self.name, scanned=read, changed=0, dry_run=True, details=details
            )
        logger.info("care_events_backfill_applied", written=changed, details=details)
        return MigrationReport(
            version=self.version, name=self.name, scanned=read, changed=changed, dry_run=False, details=details
        )

    def down(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        """Delete the backfilled lines and their edges by the marker; keep a line a person edited since."""
        if not db.has_collection(col.CARE_EVENTS):
            return MigrationReport(
                version=self.version, name=self.name, scanned=0, changed=0, dry_run=dry_run, details={}
            )
        scan = cast(
            Cursor,
            db.aql.execute(
                _DOWN_SCAN,
                bind_vars={"@events": col.CARE_EVENTS, "sources": list(SOURCE_COLLECTIONS)},
                batch_size=_BATCH_SIZE,
                ttl=cast(Any, _CURSOR_TTL_SECONDS),
                stream=False,
            ),
        )
        scanned = removable = kept_edited = removed = 0
        batch: list[str] = []
        for row in scan:
            scanned += 1
            if row["edited"]:
                kept_edited += 1
                continue
            removable += 1
            if not dry_run:
                batch.append(str(row["key"]))
                if len(batch) >= _BATCH_SIZE:
                    removed += self._remove(db, batch)
                    batch = []
        if batch:
            removed += self._remove(db, batch)
        details: dict[str, Any] = {"will_remove" if dry_run else "removed": removable if dry_run else removed}
        details["kept_edited"] = kept_edited
        logger.info("care_events_backfill_reverted", dry_run=dry_run, scanned=scanned, details=details)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=scanned,
            changed=0 if dry_run else removed,
            dry_run=dry_run,
            details=details,
        )

    @staticmethod
    def _remove(db: StandardDatabase, keys: list[str]) -> int:
        """Remove the events behind ``keys`` and their ``care_event_at`` / ``care_event_for`` edges, atomically."""
        ids = [f"{col.CARE_EVENTS}/{key}" for key in keys]
        with stream_transaction(
            db, write=(col.CARE_EVENTS, col.CARE_EVENT_AT, col.CARE_EVENT_FOR), entity="care_event"
        ) as txn:
            for edges in (col.CARE_EVENT_AT, col.CARE_EVENT_FOR):
                list(txn.aql.execute(_DOWN_REMOVE_EDGES, bind_vars={"@edges": edges, "ids": ids}))
            removed = txn.aql.execute(_DOWN_REMOVE_EVENTS, bind_vars={"@events": col.CARE_EVENTS, "keys": keys})
            return sum(1 for _ in removed)


migration = CareEventsBackfillMigration()
