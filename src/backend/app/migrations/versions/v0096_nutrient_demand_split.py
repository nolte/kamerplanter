"""v0096 — REQ-053 migration M6: the NutrientDemand split (GP-FR-138/139, GP-ACC-037/049, #2325).

**What.** One enum used to mix the feeder level with nitrogen fixation and the plan
role; REQ-053 §16.3 splits it into ``NutrientDemand`` (``heavy_feeder`` |
``medium_feeder`` | ``light_feeder``), the boolean ``nitrogen_fixing`` and
``PlanRole`` (``main_crop`` | ``green_manure`` | ``fallow``). The code side of M6 —
the renamed enum, the new ``Species`` / ``BotanicalFamily`` fields, the seed schema
and the importers — ships in the same change; this version brings the **stored**
rows to it:

* ``botanical_families.typical_nutrient_demand``: ``light → light_feeder``,
  ``medium → medium_feeder``, ``heavy → heavy_feeder`` (GP-ACC-037). The enum no
  longer knows the old spelling, and the family rows are read by the seed jobs
  right after the migrations — so this rewrite is what keeps the start from the
  enum-retirement crash.
* ``species.nutrient_demand_level == nitrogen_fixer`` → ``nitrogen_fixing = true``
  when the species carries no value for it yet (GP-ACC-049). ``nutrient_demand``
  is **not** derived — not from ``nutrient_demand_level``, not from the family
  (E-10): a species whose Steckbrief has not delivered a sourced value keeps
  ``null`` and is **listed** in the report (count + the first
  :data:`_LISTED_NAMES` scientific names), which is the gap list the Steckbrief
  lane (WP 0.5b) works from. ``nutrient_demand_level`` itself stays — the EC-target
  resolver still reads it.
* ``crop_rotation_plans.demand_level`` → ``nutrient_demand`` + ``plan_role``
  (REQ-002 v4.6): a feeder value becomes ``nutrient_demand`` with
  ``plan_role = main_crop``; ``green_manure`` / ``fallow`` become the ``plan_role``
  with ``nutrient_demand = null``; ``demand_level`` is dropped. **Defensive:** no
  volume this repository shipped has that collection (the model lands with the
  rotation-plan work package), so on today's installations this part scans
  nothing; the mapping is frozen here so a volume that does carry it is converted
  the way the spec says, and an unknown value is listed, never guessed.

**Idempotent (M-3).** Every scan matches only the old spelling / the missing flag /
the legacy field; a second run reports ``changed == 0`` (the species gap list is
reported on every run — it is a report, not a change).

**Dry run (M-5).** Full report, nothing written. Operators read
``nutrient_demand_split_dry_run`` before the production run (plan §8, P-1).

**Not reversible (M-6).** The old spelling is gone from the enum; an inverse would
have to retire the new one. The gap list is the forward path.
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

#: ``old → new`` for the family feeder level. Frozen here (M-7) — ``NutrientDemand`` may move on.
FAMILY_DEMAND_MAP: dict[str, str] = {"light": "light_feeder", "medium": "medium_feeder", "heavy": "heavy_feeder"}

#: ``demand_level → (nutrient_demand, plan_role)`` for a stored rotation plan (REQ-002 v4.6).
ROTATION_DEMAND_MAP: dict[str, tuple[str | None, str]] = {
    "heavy_feeder": ("heavy_feeder", "main_crop"),
    "medium_feeder": ("medium_feeder", "main_crop"),
    "light_feeder": ("light_feeder", "main_crop"),
    "green_manure": (None, "green_manure"),
    "fallow": (None, "fallow"),
}

#: The legacy species value that becomes the boolean.
NITROGEN_FIXER = "nitrogen_fixer"

#: Collection the spec names for the rotation plan (REQ-002 §CropRotationPlan); absent on shipped volumes.
CROP_ROTATION_PLANS = "crop_rotation_plans"

#: How many species names / refused keys a report lists before it only counts.
_LISTED_NAMES = 25

#: Documents per ``UPDATE`` statement.
_BATCH_SIZE = 500

_FAMILY_SCAN = """
FOR f IN @@collection
  FILTER f.typical_nutrient_demand IN @legacy
  RETURN { _key: f._key, value: f.typical_nutrient_demand }
"""

# Both the rows to stamp and the rows to list: a species is matched when it still
# carries the legacy nitrogen-fixer value or has no feeder level yet.
_SPECIES_SCAN = """
FOR s IN @@collection
  FILTER s.nutrient_demand_level == @fixer OR s.nutrient_demand == null
  SORT s.scientific_name
  RETURN {
    _key: s._key, scientific_name: s.scientific_name,
    is_fixer: s.nutrient_demand_level == @fixer,
    has_nitrogen_fixing: s.nitrogen_fixing != null,
    has_nutrient_demand: s.nutrient_demand != null
  }
"""

_ROTATION_SCAN = """
FOR p IN @@collection
  FILTER p.demand_level != null
  RETURN { _key: p._key, demand_level: p.demand_level }
"""

_APPLY = """
FOR u IN @updates
  UPDATE u._key WITH u.patch IN @@collection OPTIONS { keepNull: false }
"""


def _rows(db: StandardDatabase, query: str, collection: str, **binds: Any) -> list[dict[str, Any]]:
    return list(cast(Cursor, db.aql.execute(query, bind_vars={"@collection": collection, **binds})))


def _apply(db: StandardDatabase, collection: str, updates: Sequence[dict[str, Any]]) -> None:
    for start in range(0, len(updates), _BATCH_SIZE):
        chunk = list(updates[start : start + _BATCH_SIZE])
        db.aql.execute(_APPLY, bind_vars={"@collection": collection, "updates": chunk})


class _Listed:
    """Names listed up to a cap and always counted."""

    def __init__(self) -> None:
        self.count = 0
        self.names: list[str] = []

    def add(self, name: str) -> None:
        self.count += 1
        if len(self.names) < _LISTED_NAMES:
            self.names.append(name)

    def report(self) -> dict[str, Any]:
        return {"count": self.count, "listed": list(self.names)}


def _plan_families(db: StandardDatabase) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    updates: list[dict[str, Any]] = []
    by_value: dict[str, int] = {legacy: 0 for legacy in FAMILY_DEMAND_MAP}  # noqa: C420
    if db.has_collection(col.BOTANICAL_FAMILIES):
        row: dict[str, Any]
        for row in _rows(db, _FAMILY_SCAN, col.BOTANICAL_FAMILIES, legacy=list(FAMILY_DEMAND_MAP)):
            value = str(row["value"])
            by_value[value] += 1
            updates.append({"_key": row["_key"], "patch": {"typical_nutrient_demand": FAMILY_DEMAND_MAP[value]}})
    return updates, {"scanned": len(updates), "renamed": by_value}


def _plan_species(db: StandardDatabase) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    updates: list[dict[str, Any]] = []
    without_demand = _Listed()
    fixers_already_flagged = 0
    scanned = 0
    if db.has_collection(col.SPECIES):
        row: dict[str, Any]
        for row in _rows(db, _SPECIES_SCAN, col.SPECIES, fixer=NITROGEN_FIXER):
            scanned += 1
            if row.get("is_fixer"):
                if row.get("has_nitrogen_fixing"):
                    fixers_already_flagged += 1
                else:
                    updates.append({"_key": row["_key"], "patch": {"nitrogen_fixing": True}})
            if not row.get("has_nutrient_demand"):
                without_demand.add(str(row.get("scientific_name") or row["_key"]))
    return updates, {
        "scanned": scanned,
        "nitrogen_fixing_stamped": len(updates),
        "nitrogen_fixer_already_flagged": fixers_already_flagged,
        "without_nutrient_demand": without_demand.report(),
    }


def _plan_rotation_plans(db: StandardDatabase) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    updates: list[dict[str, Any]] = []
    refused = _Listed()
    by_role = {"main_crop": 0, "green_manure": 0, "fallow": 0}
    present = bool(db.has_collection(CROP_ROTATION_PLANS))
    if present:
        row: dict[str, Any]
        for row in _rows(db, _ROTATION_SCAN, CROP_ROTATION_PLANS):
            legacy_level = str(row["demand_level"])
            if legacy_level not in ROTATION_DEMAND_MAP:
                refused.add(str(row["_key"]))
                continue
            nutrient_demand, plan_role = ROTATION_DEMAND_MAP[legacy_level]
            by_role[plan_role] += 1
            updates.append(
                {
                    "_key": row["_key"],
                    "patch": {"nutrient_demand": nutrient_demand, "plan_role": plan_role, "demand_level": None},
                }
            )
    return updates, {
        "collection_present": present,
        "scanned": len(updates) + refused.count,
        "converted": by_role,
        "refused_unknown_demand_level": refused.report(),
    }


class NutrientDemandSplitMigration(Migration):
    version = "0096"
    name = "nutrient_demand_split"
    description = (
        "REQ-053 M6: BotanicalFamily.typical_nutrient_demand light/medium/heavy → *_feeder; "
        "Species.nutrient_demand_level=nitrogen_fixer → nitrogen_fixing=true; species without a sourced "
        "nutrient_demand listed, never defaulted; crop_rotation_plans.demand_level → nutrient_demand + plan_role "
        "(#2325)."
    )
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        family_updates, families = _plan_families(db)
        species_updates, species = _plan_species(db)
        rotation_updates, rotation = _plan_rotation_plans(db)
        verb = "will_update" if dry_run else "updated"
        families[verb] = len(family_updates)
        species[verb] = len(species_updates)
        rotation[verb] = len(rotation_updates)
        details = {col.BOTANICAL_FAMILIES: families, col.SPECIES: species, CROP_ROTATION_PLANS: rotation}
        changes = len(family_updates) + len(species_updates) + len(rotation_updates)
        scanned = int(families["scanned"]) + int(species["scanned"]) + int(rotation["scanned"])

        if dry_run:
            logger.info("nutrient_demand_split_dry_run", pending_changes=changes, details=details)
            return MigrationReport(
                version=self.version, name=self.name, scanned=scanned, changed=0, dry_run=True, details=details
            )
        _apply(db, col.BOTANICAL_FAMILIES, family_updates)
        _apply(db, col.SPECIES, species_updates)
        _apply(db, CROP_ROTATION_PLANS, rotation_updates)
        logger.info("nutrient_demand_split_applied", changed=changes, details=details)
        return MigrationReport(
            version=self.version, name=self.name, scanned=scanned, changed=changes, dry_run=False, details=details
        )


migration = NutrientDemandSplitMigration()
