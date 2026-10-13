"""Detection and repair of the reference *fields* v0067 left behind (#1963).

v0067 (#1878) removes a cross-tenant edge a #1871 hole wrote, and leaves the source
document alone: every source mirrors the same key in a field of its own. After it the
edge and the field disagree. This module is the one place that knows what such a row
looks like, for the four mirrored fields (``feeds_from`` has none — it is edge-only):

* ``equipment.location_key`` — optional, so the repair **nulls** it;
* ``watering_logs.slot_keys`` — a list, so the repair **removes the foreign slot keys**,
  unless that would leave a log that names neither a slot nor a plant (the model
  refuses such a log on read), which is left and counted;
* ``location_assignments.location_key`` and ``planting_run_entries.species_key`` — both
  required on their model, so nothing can be written in their place. They are
  **report-only**: counted so an operator knows how many assignments are dead and how
  many entries a run can no longer start from. The readers of the entry's species
  resolve it under the tenant (``PlantingRunService``, ``irrigation_tasks``), which is
  what keeps a legacy entry from reaching the foreign species.

**One predicate per class, shared by the count and the repair**, exactly as in
:mod:`app.migrations.support.legacy_foreign_references`, whose tenant helpers this
module reuses: the operator's pre-deploy count is the same ``ROWS`` query wrapped in a
``COLLECT``, and the migration repairs the rows the query verdicts name.

**Verdicts are conservative.** A field is touched only when both tenants are known and
differ. A dangling target (a location or slot that no longer exists), an unstamped row
and a slot whose two anchors disagree are ``unclassified``: left and counted.

Nothing here logs or returns a key, a name or a tenant: callers get counts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.data_access.arango import collections as col
from app.migrations.support.legacy_foreign_references import _known, _location_tenant, _slot_tenant

#: 1. ``equipment.location_key`` names a location of another tenant.
EQUIPMENT_LOCATION_ROWS: Final = f"""
FOR q IN {col.EQUIPMENT}
  FILTER IS_STRING(q.location_key) AND q.location_key != ''
  LET a = q.tenant_key
  LET b = {_location_tenant("CONCAT('" + col.LOCATIONS + "/', q.location_key)")}
  LET verdict = ({_known("a")} AND {_known("b")}) ? (a != b ? 'null_field' : 'keep') : 'unclassified'
  FILTER verdict != 'keep'
  RETURN {{key: q._key, verdict: verdict}}
"""

#: 2. ``watering_logs.slot_keys`` names a slot of another tenant. ``kept`` is what the
#: repair writes back; a log whose every slot is foreign and that names no plant is
#: ``left_would_orphan`` (the model needs a slot or a plant).
WATERING_LOG_SLOT_ROWS: Final = f"""
FOR l IN {col.WATERING_LOGS}
  FILTER IS_ARRAY(l.slot_keys) AND LENGTH(l.slot_keys) > 0
  LET foreign = (
    FOR k IN l.slot_keys
      LET t = {_slot_tenant("CONCAT('" + col.SLOTS + "/', k)")}
      FILTER {_known("l.tenant_key")} AND {_known("t")} AND t != l.tenant_key
      RETURN k
  )
  FILTER LENGTH(foreign) > 0
  LET kept = (FOR k IN l.slot_keys FILTER k NOT IN foreign RETURN k)
  LET names_a_plant = IS_ARRAY(l.plant_keys) AND LENGTH(l.plant_keys) > 0
  LET verdict = (LENGTH(kept) == 0 AND NOT names_a_plant) ? 'left_would_orphan' : 'drop_foreign_slots'
  RETURN {{key: l._key, verdict: verdict, kept: kept}}
"""

#: 3. ``location_assignments.location_key`` names a location of another tenant (report-only).
ASSIGNMENT_LOCATION_ROWS: Final = f"""
FOR s IN {col.LOCATION_ASSIGNMENTS}
  FILTER IS_STRING(s.location_key) AND s.location_key != ''
  LET a = s.tenant_key
  LET b = {_location_tenant("CONCAT('" + col.LOCATIONS + "/', s.location_key)")}
  FILTER {_known("a")} AND {_known("b")} AND a != b
  RETURN {{key: s._key, verdict: 'left_required_field'}}
"""

#: 4. ``planting_run_entries.species_key`` names a private species of another tenant that
#: was not granted to the entry's tenant (report-only). The entry's tenant is its run's;
#: the entry's own stamp predates #1112 on old rows. A global species (``""`` or no
#: attribute), the tenant's own and a granted one are legitimate.
ENTRY_SPECIES_ROWS: Final = f"""
FOR n IN {col.PLANTING_RUN_ENTRIES}
  FILTER IS_STRING(n.species_key) AND n.species_key != ''
  LET run = (n.run_key == null) ? null : DOCUMENT(CONCAT('{col.PLANTING_RUNS}/', n.run_key))
  LET a = run != null ? run.tenant_key : n.tenant_key
  LET sp = DOCUMENT(CONCAT('{col.SPECIES}/', n.species_key))
  LET b = sp == null ? null : (sp.tenant_key == null ? '' : sp.tenant_key)
  FILTER {_known("a")} AND {_known("b")} AND a != b
  LET granted = LENGTH(
    FOR g IN {col.TENANT_HAS_ACCESS}
      FILTER g._from == CONCAT('{col.TENANTS}/', a) AND g._to == CONCAT('{col.SPECIES}/', n.species_key)
      LIMIT 1 RETURN 1
  ) > 0
  FILTER NOT granted
  RETURN {{key: n._key, verdict: 'left_required_field'}}
"""


@dataclass(frozen=True)
class LegacyFieldClass:
    """One class of legacy field: its read-only ``ROWS`` query and where its repair writes."""

    name: str
    rows_query: str
    #: Collection the repair writes to.
    target_collection: str
    #: The verdict that is repaired (``None`` = report-only); every other verdict is left and counted.
    repair_verdict: str | None


CLASSES: Final[tuple[LegacyFieldClass, ...]] = (
    LegacyFieldClass("equipment_location_foreign", EQUIPMENT_LOCATION_ROWS, col.EQUIPMENT, "null_field"),
    LegacyFieldClass("watering_log_slots_foreign", WATERING_LOG_SLOT_ROWS, col.WATERING_LOGS, "drop_foreign_slots"),
    LegacyFieldClass("location_assignment_location_foreign", ASSIGNMENT_LOCATION_ROWS, col.LOCATION_ASSIGNMENTS, None),
    LegacyFieldClass("planting_run_entry_species_unreadable", ENTRY_SPECIES_ROWS, col.PLANTING_RUN_ENTRIES, None),
)


def count_query(rows_query: str) -> str:
    """The operator's read-only count for one class: verdict -> number of rows."""
    return f"FOR r IN ({rows_query}) COLLECT verdict = r.verdict WITH COUNT INTO n RETURN {{verdict: verdict, n: n}}"


#: ``name -> count query``. The migration's dry run and the integration test run these
#: very strings; the PR body lists them for the operator's pre-deploy check.
COUNT_QUERIES: Final[dict[str, str]] = {c.name: count_query(c.rows_query) for c in CLASSES}

#: The collections a class reads; a class whose collection is missing has nothing to count.
REQUIRED_COLLECTIONS: Final[dict[str, tuple[str, ...]]] = {
    "equipment_location_foreign": (col.EQUIPMENT, col.LOCATIONS, col.SITES),
    "watering_log_slots_foreign": (col.WATERING_LOGS, col.SLOTS, col.LOCATIONS, col.SITES, col.HAS_SLOT),
    "location_assignment_location_foreign": (col.LOCATION_ASSIGNMENTS, col.LOCATIONS, col.SITES),
    "planting_run_entry_species_unreadable": (
        col.PLANTING_RUN_ENTRIES,
        col.PLANTING_RUNS,
        col.SPECIES,
        col.TENANT_HAS_ACCESS,
    ),
}
