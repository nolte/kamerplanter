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

**Parks rather than guesses (operator decision on #2346, 2026-10-18).** A rule that is
neither an RRULE nor a convertible cron line (free text such as ``weekly``, ``@daily``,
a six-field cron, a ``*/15`` step, a cron that sets both day-of-month and weekday) is
**moved** to ``Task.recurrence_rule_unconvertible`` (original value, unchanged) and
``recurrence_rule`` becomes ``null`` — the task stays, it simply stops recurring until
its owner sets an RRULE. Every parked rule is listed in full in the report (task key,
tenant key, original value, reason) and the version is recorded: one tenant's rule never
halts the migration chain any more (the earlier ``precondition_unmet`` refusal is gone).
The API boundary is unchanged: a *new* non-RRULE rule is still refused with 422
``recurrence.rrule_required``. No cron string is known to be persisted on any
installation, so on today's volumes this version scans the RRULEs, converts and parks
nothing and records itself.

Report format (``MigrationReport.details``, identical for a dry run and a real run)::

    {"already_rrule": <int>,
     "convertible": {"count": <int>, "listed": [{"_key", "from", "rule"}, ...]},  # capped
     "parked": {"count": <int>,
                "listed": [{"_key", "tenant_key", "rule", "reason"}, ...]}}       # never capped

``reason`` is ``not_a_five_field_cron`` (free text, ``@daily``, six fields …) or
``cron_without_lossless_rrule`` (a five-field cron with no faithful RRULE). A dry run
(``dry_run=True``) returns this report and writes nothing; ``changed`` counts converted
plus parked documents on a real run.

**Idempotent (M-3).** A rule that parses as an RRULE is not matched, and a parked task has
``recurrence_rule == null`` so it is not matched either; a second run reports
``changed == 0``.

**Dry run (M-5).** Lists the conversions (key, from, to — up to a cap, always
counted) and every rule that would be parked; writes nothing.

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
from app.migrations.support.cron_to_rrule import cron_to_rrule, looks_like_cron

logger = structlog.get_logger(__name__)

#: How many conversions a report lists before it only counts; parked rules are always listed in
#: full (an operator must see every one to restore the cadence).
_LISTED_CONVERSIONS = 25

#: Documents per ``UPDATE`` statement.
_BATCH_SIZE = 500

_SCAN = """
FOR t IN @@collection
  FILTER t.recurrence_rule != null AND t.recurrence_rule != ""
  RETURN { _key: t._key, tenant_key: t.tenant_key, rule: t.recurrence_rule }
"""

_APPLY = """
FOR u IN @updates
  LET current = DOCUMENT(@@collection, u._key)
  FILTER current != null AND current.recurrence_rule == u.from
  UPDATE u._key WITH { recurrence_rule: u.rule } IN @@collection
"""

# ``FILTER`` keeps a concurrent edit that already replaced the rule from being overwritten.
_PARK = """
FOR u IN @updates
  LET current = DOCUMENT(@@collection, u._key)
  FILTER current != null AND current.recurrence_rule == u.rule
  UPDATE u._key WITH { recurrence_rule: null, recurrence_rule_unconvertible: u.rule } IN @@collection
"""

REASON_NOT_CRON = "not_a_five_field_cron"
REASON_NO_LOSSLESS_RRULE = "cron_without_lossless_rrule"


def _plan(db: StandardDatabase) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, Any]]:
    """``(conversions, parked, counters)`` over every task that carries a rule."""
    conversions: list[dict[str, str]] = []
    parked: list[dict[str, str]] = []
    counters = {"scanned": 0, "already_rrule": 0}
    if not db.has_collection(col.TASKS):
        return conversions, parked, counters
    row: dict[str, Any]
    for row in cast(Cursor, db.aql.execute(_SCAN, bind_vars={"@collection": col.TASKS})):
        counters["scanned"] += 1
        rule = str(row["rule"])
        if RecurrenceEngine.parses_as_rrule(rule):
            counters["already_rrule"] += 1
            continue
        converted = cron_to_rrule(rule)
        if converted is None:
            parked.append(
                {
                    "_key": str(row["_key"]),
                    "tenant_key": str(row.get("tenant_key") or ""),
                    "rule": rule,
                    "reason": REASON_NO_LOSSLESS_RRULE if looks_like_cron(rule) else REASON_NOT_CRON,
                }
            )
        else:
            conversions.append({"_key": str(row["_key"]), "from": rule, "rule": converted})
    return conversions, parked, counters


def _apply(db: StandardDatabase, query: str, rows: list[dict[str, Any]]) -> None:
    for start in range(0, len(rows), _BATCH_SIZE):
        db.aql.execute(query, bind_vars={"@collection": col.TASKS, "updates": rows[start : start + _BATCH_SIZE]})


class RecurrenceCronToRruleMigration(Migration):
    version = "0097"
    name = "recurrence_cron_to_rrule"
    description = (
        "REQ-053 M5: convert stored cron recurrence_rule strings on tasks to RFC 5545 RRULE; "
        "park a rule with no lossless rendering in recurrence_rule_unconvertible (#2325, #2346)."
    )
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        conversions, parked, counters = _plan(db)
        details: dict[str, Any] = {
            **counters,
            "convertible": {"count": len(conversions), "listed": conversions[:_LISTED_CONVERSIONS]},
            "parked": {"count": len(parked), "listed": parked},
        }
        scanned = int(counters["scanned"])
        pending = len(conversions) + len(parked)
        if dry_run:
            logger.info("recurrence_cron_to_rrule_dry_run", pending_changes=pending, details=details)
            return MigrationReport(
                version=self.version, name=self.name, scanned=scanned, changed=0, dry_run=True, details=details
            )
        _apply(db, _APPLY, [{"_key": c["_key"], "from": c["from"], "rule": c["rule"]} for c in conversions])
        _apply(db, _PARK, [{"_key": p["_key"], "rule": p["rule"]} for p in parked])
        if parked:
            logger.warning("recurrence_cron_to_rrule_parked", parked=len(parked), details=details)
        logger.info("recurrence_cron_to_rrule_applied", changed=pending, details=details)
        return MigrationReport(
            version=self.version, name=self.name, scanned=scanned, changed=pending, dry_run=False, details=details
        )


migration = RecurrenceCronToRruleMigration()
