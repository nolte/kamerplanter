"""v0098 — REQ-053 issue 75 (WP 3.9, #2399): ``frost_exposed`` → ``site_conditions.microclimate.frost_risk``.

**What.** REQ-053 §10.2 replaces the boolean ``Location.frost_exposed`` (Issue #706) by the
four-step ``site_conditions.microclimate.frost_risk`` (``low`` | ``normal`` | ``high`` |
``unknown``). The code side — the embedded ``SiteConditions`` model, ``PATCH /locations`` and the
sun tiles — ships in the same change; this version copies the **stored** override over:

* ``frost_exposed == true``  → ``frost_risk = high`` (the spec's mapping, §10.2),
* ``frost_exposed == false`` → ``frost_risk = low`` (the override meant "forced protected";
  ``low`` is the nearest step — an operator question, see the needs-decision issue of WP 3.9),
* ``frost_exposed == null``/absent → untouched (it meant "inherit from the site type"; there is no
  step for that, ``unknown`` is the default and nothing is written).

**Additive (prod point P-2).** ``frost_exposed`` is **not** removed or rewritten: the winter readers
(``frost_exposure_resolver``, the season-state service, ``find_site_keys_with_frost_exposed_location``)
still read it, and the write paths keep the two fields in step (``PUT``/``PATCH /locations``). Only
the nested key ``site_conditions.microclimate.frost_risk`` is created, merged into whatever
``site_conditions`` already holds (a sun window entered through the new UI survives).

**Idempotent (M-3).** Only locations whose ``frost_risk`` is missing or ``unknown`` match; a second run
matches nothing. A location whose ``frost_risk`` is already set (``low``/``normal``/``high``) is never
overwritten — when it disagrees with ``frost_exposed`` it is **counted and listed** as a conflict, not
guessed (the readers keep using ``frost_exposed`` until they are moved over).

**Dry run (M-5).** Full report, nothing written. Operators read ``location_site_conditions_dry_run``
before the production run (plan §8, P-2): ``will_update`` split by target value, the first
:data:`_LISTED` location keys, ``untouched_inherit`` (the ``null`` overrides) and ``conflicts``.

**Not reversible (M-6).** ``frost_exposed`` stays, so nothing is lost; but after the readers move over
the two fields diverge by design, and an inverse would have to guess which one is right.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, cast

import structlog
from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)

#: ``frost_exposed → frost_risk``. Frozen here (M-7) — ``FrostRisk`` may grow.
FROST_RISK_MAP: dict[bool, str] = {True: "high", False: "low"}

#: Risks that count as "nobody has entered a risk yet".
_UNSET_RISKS = (None, "unknown")

#: How many location keys a report lists before it only counts.
_LISTED = 25

#: Documents per ``UPDATE`` statement.
_BATCH_SIZE = 500

_SCAN = """
FOR l IN @@collection
  FILTER l.frost_exposed != null
  RETURN {
    _key: l._key,
    frost_exposed: l.frost_exposed,
    frost_risk: l.site_conditions.microclimate.frost_risk
  }
"""

_INHERIT_COUNT = """
RETURN LENGTH(FOR l IN @@collection FILTER l.frost_exposed == null RETURN 1)
"""

# A nested object in the patch is merged into the stored one (``mergeObjects`` is the default), so the
# other keys of ``site_conditions`` and ``microclimate`` survive.
_APPLY = """
FOR u IN @updates
  UPDATE u._key WITH { site_conditions: { microclimate: { frost_risk: u.frost_risk } } } IN @@collection
"""


def _rows(db: StandardDatabase, query: str) -> list[dict[str, Any]]:
    return list(cast(Cursor, db.aql.execute(query, bind_vars={"@collection": col.LOCATIONS})))


def _count(db: StandardDatabase, query: str) -> int:
    """The one number a ``RETURN LENGTH(…)`` query answers (0 on the empty cursor of a bare fake)."""
    cursor = cast(Cursor, db.aql.execute(query, bind_vars={"@collection": col.LOCATIONS}))
    return next((int(value) for value in cursor), 0)


def _apply(db: StandardDatabase, updates: Sequence[dict[str, Any]]) -> None:
    for start in range(0, len(updates), _BATCH_SIZE):
        chunk = list(updates[start : start + _BATCH_SIZE])
        db.aql.execute(_APPLY, bind_vars={"@collection": col.LOCATIONS, "updates": chunk})


def _plan(db: StandardDatabase) -> tuple[list[dict[str, Any]], dict[str, Any], int]:
    updates: list[dict[str, Any]] = []
    by_value: dict[str, int] = {"high": 0, "low": 0}
    conflicts: list[str] = []
    conflict_count = 0
    already_in_step = 0
    scanned = 0
    scan: list[dict[str, Any]] = _rows(db, _SCAN)
    for row in scan:
        scanned += 1
        target = FROST_RISK_MAP[bool(row["frost_exposed"])]
        current = row["frost_risk"]
        if current in _UNSET_RISKS:
            updates.append({"_key": row["_key"], "frost_risk": target})
            by_value[target] += 1
        elif current == target:
            already_in_step += 1
        else:
            conflict_count += 1
            if len(conflicts) < _LISTED:
                conflicts.append(str(row["_key"]))
    inherit = _count(db, _INHERIT_COUNT)
    details: dict[str, Any] = {
        "scanned_with_frost_exposed": scanned,
        "by_target": by_value,
        "listed_keys": [str(u["_key"]) for u in updates[:_LISTED]],
        "already_in_step": already_in_step,
        "conflicts": {"count": conflict_count, "listed": conflicts},
        "untouched_inherit": inherit,
    }
    return updates, details, scanned


class LocationSiteConditionsMigration(Migration):
    version = "0098"
    name = "location_site_conditions"
    description = (
        "REQ-053 issue 75: copy Location.frost_exposed (true → high, false → low) into "
        "site_conditions.microclimate.frost_risk; additive — frost_exposed stays, a set frost_risk is never "
        "overwritten (conflicts listed), null overrides untouched (#2399)."
    )
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        if not db.has_collection(col.LOCATIONS):
            return MigrationReport(
                version=self.version, name=self.name, scanned=0, changed=0, dry_run=dry_run, details={}
            )
        updates, details, scanned = _plan(db)
        details["will_update" if dry_run else "updated"] = len(updates)
        if dry_run:
            logger.info("location_site_conditions_dry_run", pending_changes=len(updates), details=details)
            return MigrationReport(
                version=self.version, name=self.name, scanned=scanned, changed=0, dry_run=True, details=details
            )
        _apply(db, updates)
        logger.info("location_site_conditions_applied", changed=len(updates), details=details)
        return MigrationReport(
            version=self.version, name=self.name, scanned=scanned, changed=len(updates), dry_run=False, details=details
        )


migration = LocationSiteConditionsMigration()
