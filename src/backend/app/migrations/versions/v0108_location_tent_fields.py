"""v0108 — REQ-053 WP 10.11 (#2832, W-016): make room for ``Location.adjacency_factor`` and ``Location.lighting``.

Both fields are new and optional; their model default is ``None`` ("the site's factor", "no lighting entered"), so
**nothing is materialised**: a stored location without them reads exactly as before, and writing ``null`` into every
document would only add a key that means what its absence means. What the new model can no longer do is *read* a
location that already carries one of the two names with a value it refuses - a factor outside ``0 < f <= 10``, a
lighting object with an unknown key, a height out of bounds, a canopy farther from the lamp than the lamp is high, a
fixture footprint that encloses no area. No code path wrote either name before this version (the PUT body ignores
unknown keys, the plan batch and the import refuse them), but the repository's merge update never strips a key it
does not know, so a document can hold anything under them; one that does would answer 500 on every read from now on.

This version therefore removes **only those values**, field by field: a value the new model accepts (including an
explicit ``null``) is left as stored. On every database written by Kamerplanter's own code it changes nothing.

**Idempotent (M-3).** After a run no location holds a refused value; a second run finds none.
**Dry run (M-5).** ``--dry-run`` counts the values it would remove and writes nothing.
**Not reversible (M-6).** A removed value is one no reader could ever load; restoring it would make the location
unreadable again, and which value it was is not recorded.

The rules are frozen copies of the model's bounds at this version (M-7): the class holds them, so the checksum covers
them. The fixture footprint is checked for its kind only; the full geometry rules stay with the model.
"""

from __future__ import annotations

import math
from typing import Any, cast

import structlog
from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)

_CANDIDATES = """
FOR l IN @@locations
  FILTER HAS(l, "adjacency_factor") OR HAS(l, "lighting")
  SORT l._key ASC
  RETURN {
    key: l._key,
    has_factor: HAS(l, "adjacency_factor"),
    factor: l.adjacency_factor,
    has_lighting: HAS(l, "lighting"),
    lighting: l.lighting
  }
"""

_CLEAR_FACTOR = """
UPDATE { _key: @key } WITH { adjacency_factor: null } IN @@locations OPTIONS { keepNull: false }
"""

_CLEAR_LIGHTING = """
UPDATE { _key: @key } WITH { lighting: null } IN @@locations OPTIONS { keepNull: false }
"""


class LocationTentFieldsMigration(Migration):
    version = "0108"
    name = "location_tent_fields"
    description = (
        "REQ-053 WP 10.11 (W-016): remove stored adjacency_factor / lighting values the new Location model "
        "cannot read; nothing is materialised (both default to null)."
    )
    reversible = False

    #: Frozen bounds (M-7): ``site.MAX_ADJACENCY_FACTOR`` and ``site.MAX_LAMP_HEIGHT_CM`` at this version.
    MAX_FACTOR = 10.0
    MAX_LAMP_HEIGHT_CM = 1000.0
    LIGHTING_KEYS = frozenset({"lamp_height_cm", "canopy_distance_cm", "fixture_geometry"})
    AREA_KINDS = frozenset({"rect", "circle", "polygon"})

    @staticmethod
    def _number(value: object) -> float | None:
        if isinstance(value, bool) or not isinstance(value, int | float):
            return None
        number = float(value)
        return number if math.isfinite(number) else None

    @classmethod
    def factor_is_readable(cls, value: object) -> bool:
        if value is None:
            return True
        number = cls._number(value)
        return number is not None and 0 < number <= cls.MAX_FACTOR

    @classmethod
    def lighting_is_readable(cls, value: object) -> bool:
        if value is None:
            return True
        if not isinstance(value, dict) or not set(value) <= cls.LIGHTING_KEYS:
            return False
        lighting: dict[str, Any] = value
        lamp_raw, canopy_raw = lighting.get("lamp_height_cm"), lighting.get("canopy_distance_cm")
        lamp, canopy = cls._number(lamp_raw), cls._number(canopy_raw)
        if lamp_raw is not None and (lamp is None or not 0 < lamp <= cls.MAX_LAMP_HEIGHT_CM):
            return False
        if canopy_raw is not None and (canopy is None or not 0 <= canopy <= cls.MAX_LAMP_HEIGHT_CM):
            return False
        if lamp is not None and canopy is not None and canopy > lamp:
            return False
        geometry = lighting.get("fixture_geometry")
        if geometry is None:
            return True
        if not isinstance(geometry, dict):
            return False
        footprint: dict[str, Any] = geometry
        return footprint.get("kind") in cls.AREA_KINDS

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        if not db.has_collection(col.LOCATIONS):
            return MigrationReport(
                version=self.version, name=self.name, scanned=0, changed=0, dry_run=dry_run, details={}
            )
        rows: list[dict[str, Any]] = list(
            cast(Cursor, db.aql.execute(_CANDIDATES, bind_vars={"@locations": col.LOCATIONS}))
        )
        factor_keys = [str(r["key"]) for r in rows if r["has_factor"] and not self.factor_is_readable(r["factor"])]
        lighting_keys = [
            str(r["key"]) for r in rows if r["has_lighting"] and not self.lighting_is_readable(r["lighting"])
        ]
        if not dry_run:
            for key in factor_keys:
                db.aql.execute(_CLEAR_FACTOR, bind_vars={"@locations": col.LOCATIONS, "key": key})
            for key in lighting_keys:
                db.aql.execute(_CLEAR_LIGHTING, bind_vars={"@locations": col.LOCATIONS, "key": key})
        prefix = "will_clear" if dry_run else "cleared"
        details = {f"{prefix}_adjacency_factor": len(factor_keys), f"{prefix}_lighting": len(lighting_keys)}
        logger.info("location_tent_fields", dry_run=dry_run, scanned=len(rows), **details)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=len(rows),
            changed=0 if dry_run else len(factor_keys) + len(lighting_keys),
            dry_run=dry_run,
            details=details,
        )


migration = LocationTentFieldsMigration()
