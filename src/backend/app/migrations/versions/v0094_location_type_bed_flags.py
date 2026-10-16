"""v0094 — REQ-053 migration M2: ``LocationType.is_bed`` / ``supports_layout`` on stored types (#2325).

**What (GP-FR-040, §9.2a / W-016.1, REQ-002 v4.6).** A bed is a location whose type
carries ``is_bed = true``; a location may carry a geometry with a slot layout when its
type carries ``supports_layout = true``. Both flags are new on ``location_types``. The
model defaults them to ``false``, so a row without them *reads* correctly — but an AQL
filter such as ``FILTER t.is_bed == true`` (GP-API-011 bed list) sees ``null`` and not
the default, and the admin UI would show every seeded type as "not a bed". This
version stamps the flags on every stored type that lacks them, **decided by key**:

* ``is_bed = true`` for the system bed seeds ``bed``, ``raised_bed``, ``planter``,
  ``greenhouse_bed``, ``cold_frame``; ``false`` for every other key;
* ``supports_layout = true`` for every bed seed **and** ``tent``, ``shelf`` (a shelf
  carries planters, which are beds themselves — O-09), **and** for any row that
  already carries ``is_bed = true`` (the invariant "every bed type supports a
  layout" holds after the run whatever the key); ``false`` otherwise.

The key sets are frozen in this module so a later change of the seed file does not
change what this applied version did (M-7). The rule reads the key and **not**
``is_system``: the PUT-rebuild defect the location-type service documents left
seeded rows with ``is_system = false`` on real volumes, and ``bed`` must become a
bed regardless; a user-defined type carries an auto-generated key, never a seed
key, so it ends up ``false`` / ``false`` unless it already carries ``is_bed``.

**The four new seeds are not written here.** ``raised_bed``, ``planter``,
``greenhouse_bed`` and ``cold_frame`` come from the fatal seed job
``location_types`` (``app/migrations/seed_location_types.py``, ``location_types.yaml``),
which runs right after the migrations under the same lock on every boot and carries
both flags for every row it inserts — the v0091 / ``plans`` pattern. On the standalone
``python -m app.migrations`` path the seeds arrive with the next application boot.

**Idempotent (M-3).** A row that carries both flags is not matched; a row that carries
one of them keeps that value and only gains the other. A second run reports
``changed == 0``. ``scanned`` counts the *candidate* rows (those lacking a flag), so a
second run also reports ``scanned == 0``.

**Dry run (M-5).** Lists, per flag, the keys that will be stamped ``true`` and counts
the rest; writes nothing. Operators read ``location_type_bed_flags_dry_run`` before the
production run (plan §8, P-1).

**Not reversible (M-6).** An older image ignores the two attributes; a ``down`` would
only discard flags a platform admin may have set on user-defined types since.
"""

from __future__ import annotations

from typing import Any, cast

import structlog
from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)

#: System seeds that are bed types (GP-FR-040). Frozen here — see the module docstring.
BED_TYPE_KEYS: frozenset[str] = frozenset({"bed", "raised_bed", "planter", "greenhouse_bed", "cold_frame"})

#: System seeds that support a slot layout without being beds (§9.2a, W-016.1).
LAYOUT_ONLY_TYPE_KEYS: frozenset[str] = frozenset({"tent", "shelf"})

#: Documents per ``UPDATE`` statement.
_BATCH_SIZE = 500

# ``== null`` matches both an absent attribute and an explicit ``null``; a stored
# ``false`` is a value the row already carries and is kept. The stored ``is_bed`` is
# returned as a value because a row that is a bed must support a layout.
_SCAN = """
FOR t IN @@collection
  FILTER t.is_bed == null OR t.supports_layout == null
  RETURN { _key: t._key, is_bed: t.is_bed, has_supports_layout: t.supports_layout != null }
"""

_APPLY = """
FOR u IN @updates
  UPDATE u._key WITH u.patch IN @@collection OPTIONS { keepNull: false }
"""


def is_bed_for(key: str) -> bool:
    """``is_bed`` the migration stamps for a type key."""
    return key in BED_TYPE_KEYS


def supports_layout_for(key: str, *, is_bed: bool = False) -> bool:
    """``supports_layout`` the migration stamps: every bed (by key or stored flag) plus tent and shelf."""
    return is_bed or key in BED_TYPE_KEYS or key in LAYOUT_ONLY_TYPE_KEYS


def _plan(db: StandardDatabase) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """The pending patches and the report of fixed shape (every key present, zero when idle)."""
    updates: list[dict[str, Any]] = []
    bed_keys: list[str] = []
    layout_keys: list[str] = []
    counters = {"scanned": 0, "is_bed_missing": 0, "supports_layout_missing": 0}
    if not db.has_collection(col.LOCATION_TYPES):
        return updates, {**counters, "bed_type_keys": bed_keys, "layout_type_keys": layout_keys}
    cursor = cast(Cursor, db.aql.execute(_SCAN, bind_vars={"@collection": col.LOCATION_TYPES}))
    row: dict[str, Any]
    for row in cursor:
        counters["scanned"] += 1
        key = str(row["_key"])
        patch: dict[str, Any] = {}
        stored_is_bed = row.get("is_bed")
        if stored_is_bed is None:
            patch["is_bed"] = is_bed_for(key)
            counters["is_bed_missing"] += 1
            if patch["is_bed"]:
                bed_keys.append(key)
        if not row.get("has_supports_layout"):
            patch["supports_layout"] = supports_layout_for(key, is_bed=stored_is_bed is True)
            counters["supports_layout_missing"] += 1
            if patch["supports_layout"]:
                layout_keys.append(key)
        if patch:
            updates.append({"_key": key, "patch": patch})
    return updates, {**counters, "bed_type_keys": sorted(bed_keys), "layout_type_keys": sorted(layout_keys)}


def _apply(db: StandardDatabase, updates: list[dict[str, Any]]) -> None:
    for start in range(0, len(updates), _BATCH_SIZE):
        chunk = updates[start : start + _BATCH_SIZE]
        db.aql.execute(_APPLY, bind_vars={"@collection": col.LOCATION_TYPES, "updates": chunk})


class LocationTypeBedFlagsMigration(Migration):
    version = "0094"
    name = "location_type_bed_flags"
    description = (
        "REQ-053 M2: stamp LocationType.is_bed (bed, raised_bed, planter, greenhouse_bed, cold_frame) and "
        "supports_layout (bed types + tent, shelf) on every stored location type lacking them (#2325)."
    )
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        updates, details = _plan(db)
        details["will_update" if dry_run else "updated"] = len(updates)
        scanned = int(details["scanned"])
        if dry_run:
            logger.info("location_type_bed_flags_dry_run", pending_changes=len(updates), details=details)
            return MigrationReport(
                version=self.version, name=self.name, scanned=scanned, changed=0, dry_run=True, details=details
            )
        _apply(db, updates)
        logger.info("location_type_bed_flags_applied", changed=len(updates), details=details)
        return MigrationReport(
            version=self.version, name=self.name, scanned=scanned, changed=len(updates), dry_run=False, details=details
        )


migration = LocationTypeBedFlagsMigration()
