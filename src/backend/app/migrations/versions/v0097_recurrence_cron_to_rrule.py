"""v0097 — REQ-053 migration M5: stored cron recurrence rules → RRULE (GP-ACC-038, ADR-008, #2325).

**What.** ``Task.recurrence_rule`` is an RFC 5545 RRULE (REQ-006 v3.5); the engine
has spoken RRULE since #510 and only *tolerated* a cron string through a croniter
fallback "for any historically created rule". M5 ends the tolerance: this version
rewrites every stored cron rule that has a lossless RRULE rendering
(:mod:`app.migrations.support.cron_to_rrule`) — ``0 8 * * 1`` becomes
``FREQ=WEEKLY;BYDAY=MO;BYHOUR=8;BYMINUTE=0`` — and the same change removes the
fallback from :class:`~app.domain.engines.recurrence_engine.RecurrenceEngine` and
refuses a new cron rule at the service boundary with 422
``recurrence.rrule_required``.

**Refuses rather than guesses (M-1 precondition).** A rule that is neither an
RRULE nor a convertible cron line (a ``*/15`` step, a cron that sets both
day-of-month and weekday, free text) is **listed** in the report and the migration
**does not apply**: it returns ``precondition_unmet`` with nothing written, so the
runner leaves it — and every later version — pending and retries on the next boot
(``runner.py``). The operator fixes or clears those rules first; the dry run shows
exactly which (key and rule). This is why M5 is numbered *after* M6: a refusal
here must not hold M6 back. No cron string is known to be persisted on any
installation (the engine docstring said so since #510), so on today's volumes
this version scans the RRULEs, converts nothing and records itself.

**Idempotent (M-3).** A rule that parses as an RRULE is not matched; a second run
reports ``changed == 0``.

**Dry run (M-5).** Lists the conversions (key, from, to — up to a cap, always
counted) and every refused rule; writes nothing.

**Not reversible (M-6).** The croniter fallback is gone from the code; an inverse
would re-create rules the engine can no longer read.
"""

from __future__ import annotations

from typing import Any, cast

import structlog
from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.domain.engines.recurrence_engine import RecurrenceEngine
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport
from app.migrations.support.cron_to_rrule import cron_to_rrule

logger = structlog.get_logger(__name__)

#: How many conversions a report lists before it only counts; refusals are always listed in full
#: (an operator must see every one to clear the precondition).
_LISTED_CONVERSIONS = 25

#: Documents per ``UPDATE`` statement.
_BATCH_SIZE = 500

_SCAN = """
FOR t IN @@collection
  FILTER t.recurrence_rule != null AND t.recurrence_rule != ""
  RETURN { _key: t._key, rule: t.recurrence_rule }
"""

_APPLY = """
FOR u IN @updates
  UPDATE u._key WITH { recurrence_rule: u.rule } IN @@collection
"""


def _plan(db: StandardDatabase) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, Any]]:
    """``(conversions, refusals, counters)`` over every task that carries a rule."""
    conversions: list[dict[str, str]] = []
    refusals: list[dict[str, str]] = []
    counters = {"scanned": 0, "already_rrule": 0}
    if not db.has_collection(col.TASKS):
        return conversions, refusals, counters
    row: dict[str, Any]
    for row in cast(Cursor, db.aql.execute(_SCAN, bind_vars={"@collection": col.TASKS})):
        counters["scanned"] += 1
        rule = str(row["rule"])
        if RecurrenceEngine.parses_as_rrule(rule):
            counters["already_rrule"] += 1
            continue
        converted = cron_to_rrule(rule)
        if converted is None:
            refusals.append({"_key": str(row["_key"]), "rule": rule})
        else:
            conversions.append({"_key": str(row["_key"]), "from": rule, "rule": converted})
    return conversions, refusals, counters


def _apply(db: StandardDatabase, conversions: list[dict[str, str]]) -> None:
    for start in range(0, len(conversions), _BATCH_SIZE):
        chunk: list[dict[str, Any]] = [
            {"_key": c["_key"], "rule": c["rule"]} for c in conversions[start : start + _BATCH_SIZE]
        ]
        db.aql.execute(_APPLY, bind_vars={"@collection": col.TASKS, "updates": chunk})


class RecurrenceCronToRruleMigration(Migration):
    version = "0097"
    name = "recurrence_cron_to_rrule"
    description = (
        "REQ-053 M5: convert stored cron recurrence_rule strings on tasks to RFC 5545 RRULE; "
        "refuse (precondition_unmet) while a rule has no lossless rendering (#2325)."
    )
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        conversions, refusals, counters = _plan(db)
        details: dict[str, Any] = {
            **counters,
            "convertible": {"count": len(conversions), "listed": conversions[:_LISTED_CONVERSIONS]},
            "refused": {"count": len(refusals), "listed": refusals},
        }
        scanned = int(counters["scanned"])
        if dry_run:
            logger.info("recurrence_cron_to_rrule_dry_run", pending_changes=len(conversions), details=details)
            return MigrationReport(
                version=self.version, name=self.name, scanned=scanned, changed=0, dry_run=True, details=details
            )
        if refusals:
            logger.warning("recurrence_cron_to_rrule_refused", refused=len(refusals), details=details)
            return MigrationReport(
                version=self.version,
                name=self.name,
                scanned=scanned,
                changed=0,
                dry_run=False,
                precondition_unmet=True,
                details=details,
            )
        _apply(db, conversions)
        logger.info("recurrence_cron_to_rrule_applied", changed=len(conversions), details=details)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=scanned,
            changed=len(conversions),
            dry_run=False,
            details=details,
        )


migration = RecurrenceCronToRruleMigration()
