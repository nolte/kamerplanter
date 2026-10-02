"""Detection and repair of references written through the #1871 holes (#1878).

Before #1876 a handful of tenant routes stored a caller-supplied reference
without resolving it under the tenant (B1 slot location, B2 equipment location,
B3 location assignment, B4 watering-log slot, B5 tank feed source, B10 shared
workflow template, B11 planting-run entry species). The fixes stop new rows; they
do not touch the rows the holes already produced. This module is the one place
that knows what such a row looks like.

**One predicate per class, shared by the count and the repair.** Every class is
one AQL ``ROWS`` query that returns a verdict per candidate row. The operator's
pre-deploy count query is that same query wrapped in a ``COLLECT`` (:func:`count_query`),
and the migration repairs exactly the rows the query verdicts name — so the number
an operator reads before the deploy is the number the migration acts on.

**Verdicts are conservative.** A row is repaired only when every side of the
decision is known and non-empty; anything else is ``unclassified`` and left alone
(and counted). Over-deleting would destroy a tenant's own data, which is worse than
a stale edge. In particular:

* ``""`` (and an absent ``tenant_key``) is the *global catalogue* value (#324 class).
  A target carrying it is legitimate and is never judged foreign.
* A tenant that was explicitly granted a species (``tenant_has_access``) may hold
  edges to it.
* Location and slot carry no usable ``tenant_key`` of their own; their tenant is
  the site's (``location.site_key`` -> ``sites``), the same two-hop anchor the
  runtime uses (``resolve_owned_location`` / ``resolve_owned_slot``). A slot's
  tenant goes through its ``location_key`` **field**, which is what that anchor
  reads.

Nothing here logs or returns a key, a name or a tenant: callers get counts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.data_access.arango import collections as col

#: When #1876 (the #1871 B-fixes) merged to ``develop`` (2026-09-26 05:41 +01:00). No hole row
#: is younger; a grant-revocable class uses it to tell a hole product from a withdrawn grant.
FIX_MERGED_AT: Final = "2026-09-26T04:41:51Z"

# -- AQL fragments -------------------------------------------------------------

#: ``@`` free expression helpers; ``{x}`` is an AQL expression yielding an id/key.
_LOCATION_TENANT = (
    "FIRST(LET _l = DOCUMENT({id}) "
    "LET _s = (_l == null OR _l.site_key == null) ? null : DOCUMENT(CONCAT('" + col.SITES + "/', _l.site_key)) "
    "RETURN _s.tenant_key)"
)
_SLOT_TENANT = (
    "FIRST(LET _sl = DOCUMENT({id}) "
    "LET _fl = (_sl == null OR _sl.location_key == null OR _sl.location_key == '') ? null "
    "  : DOCUMENT(CONCAT('" + col.LOCATIONS + "/', _sl.location_key)) "
    "LET _fs = (_fl == null OR _fl.site_key == null) ? null : DOCUMENT(CONCAT('" + col.SITES + "/', _fl.site_key)) "
    "LET _edges = (FOR _e IN " + col.HAS_SLOT + " FILTER _e._to == CONCAT('" + col.SLOTS + "/', _sl._key) RETURN _e) "
    "LET _el = LENGTH(_edges) == 1 ? DOCUMENT(_edges[0]._from) : null "
    "LET _es = (_el == null OR _el.site_key == null) ? null : DOCUMENT(CONCAT('" + col.SITES + "/', _el.site_key)) "
    "RETURN (IS_STRING(_fs.tenant_key) AND _fs.tenant_key == _es.tenant_key) ? _fs.tenant_key : null)"
)
#: A tenant value that names exactly one tenant (not absent, not the global ``""``).
_KNOWN = "(IS_STRING({v}) AND {v} != '')"


def _location_tenant(id_expr: str) -> str:
    return _LOCATION_TENANT.format(id=id_expr)


def _slot_tenant(id_expr: str) -> str:
    return _SLOT_TENANT.format(id=id_expr)


def _known(expr: str) -> str:
    return _KNOWN.format(v=expr)


def _edge_rows(edge: str, source_tenant: str, target_tenant: str) -> str:
    """Rows of ``edge`` whose two endpoint tenants are known and differ (``drop``) or unknown (``unclassified``)."""
    return f"""
    FOR e IN {edge}
      LET a = {source_tenant}
      LET b = {target_tenant}
      LET verdict = ({_known("a")} AND {_known("b")}) ? (a != b ? 'drop' : 'keep') : 'unclassified'
      FILTER verdict != 'keep'
      RETURN {{key: e._key, verdict: verdict}}
    """


#: 1. Shared (``tenant_key == ""``) generated plans named after a private species.
#: Left alone when the owner already holds a generated plan for the species (a re-owned
#: duplicate could shadow the owner's edited copy) or when the species is granted to any
#: tenant (a grantee reads the shared plan and would lose it).
WORKFLOW_TEMPLATE_ROWS: Final = f"""
FOR t IN {col.WORKFLOW_TEMPLATES}
  FILTER t.auto_generated == true AND t.is_system != true
  FILTER t.tenant_key == null OR t.tenant_key == ''
  LET sp = t.species_key == null ? null : DOCUMENT(CONCAT('{col.SPECIES}/', t.species_key))
  LET owner = sp == null ? null : (sp.tenant_key == null ? '' : sp.tenant_key)
  FILTER owner != ''
  LET owner_has_plan = IS_STRING(owner) AND LENGTH(
    FOR o IN {col.WORKFLOW_TEMPLATES}
      FILTER o.auto_generated == true AND o.species_key == t.species_key AND o.tenant_key == owner
      LIMIT 1 RETURN 1
  ) > 0
  LET granted = LENGTH(
    FOR g IN {col.TENANT_HAS_ACCESS} FILTER g._to == CONCAT('{col.SPECIES}/', t.species_key) LIMIT 1 RETURN 1
  ) > 0
  LET verdict = NOT IS_STRING(owner) ? 'unclassified'
    : granted ? 'left_granted'
    : owner_has_plan ? 'left_owner_has_plan'
    : 'reown'
  RETURN {{key: t._key, verdict: verdict, owner: owner}}
"""

#: 2. Slots whose ``location_key`` field and ``has_slot`` edge disagree.
SLOT_EDGE_ROWS: Final = f"""
FOR s IN {col.SLOTS}
  FILTER IS_STRING(s.location_key) AND s.location_key != ''
  LET edges = (FOR e IN {col.HAS_SLOT} FILTER e._to == CONCAT('{col.SLOTS}/', s._key) RETURN e)
  FILTER LENGTH(edges) != 1 OR edges[0]._from != CONCAT('{col.LOCATIONS}/', s.location_key)
  LET field_tenant = {_location_tenant("CONCAT('" + col.LOCATIONS + "/', s.location_key)")}
  LET edge_tenant = LENGTH(edges) == 1 ? {_location_tenant("edges[0]._from")} : null
  LET verdict = LENGTH(edges) != 1 ? 'unclassified'
    : ({_known("field_tenant")} AND field_tenant == edge_tenant) ? 'move_edge'
    : 'unclassified'
  RETURN {{key: s._key, verdict: verdict, edge_key: LENGTH(edges) == 1 ? edges[0]._key : null,
           location_key: s.location_key}}
"""

#: 3a. ``equipment_at``: equipment -> location.
EQUIPMENT_AT_ROWS: Final = _edge_rows(
    col.EQUIPMENT_AT,
    "DOCUMENT(e._from).tenant_key",
    _location_tenant("e._to"),
)

#: 3b. ``assigned_to_location``: location assignment -> location.
ASSIGNED_TO_LOCATION_ROWS: Final = _edge_rows(
    col.ASSIGNED_TO_LOCATION,
    "DOCUMENT(e._from).tenant_key",
    _location_tenant("e._to"),
)

#: 3c. ``log_slot``: watering log -> slot.
LOG_SLOT_ROWS: Final = _edge_rows(
    col.LOG_SLOT,
    "DOCUMENT(e._from).tenant_key",
    _slot_tenant("e._to"),
)

#: 3d. ``feeds_from``: tank -> tank.
FEEDS_FROM_ROWS: Final = _edge_rows(
    col.FEEDS_FROM,
    "DOCUMENT(e._from).tenant_key",
    "DOCUMENT(e._to).tenant_key",
)

#: 3e. ``entry_for_species``: planting-run entry -> species. The entry's tenant is its
#: run's (the entry's own stamp predates #1112 on old rows); a global species and a
#: granted one are legitimate targets. A grant is revocable, so an edge that fails the
#: grant test today may have been legitimate under a grant that was later withdrawn:
#: only an edge created **before** the #1876 fix merged can be a hole product, and an
#: edge without a creation time cannot be placed — both of the others are left.
ENTRY_FOR_SPECIES_ROWS: Final = f"""
FOR e IN {col.ENTRY_FOR_SPECIES}
  LET entry = DOCUMENT(e._from)
  LET run = (entry == null OR entry.run_key == null) ? null
    : DOCUMENT(CONCAT('{col.PLANTING_RUNS}/', entry.run_key))
  LET a = run != null ? run.tenant_key : entry.tenant_key
  LET sp = DOCUMENT(e._to)
  LET b = sp == null ? null : (sp.tenant_key == null ? '' : sp.tenant_key)
  LET granted = {_known("a")} AND LENGTH(
    FOR g IN {col.TENANT_HAS_ACCESS} FILTER g._from == CONCAT('{col.TENANTS}/', a) AND g._to == e._to LIMIT 1 RETURN 1
  ) > 0
  LET created = IS_STRING(e.created_at) ? DATE_TIMESTAMP(e.created_at) : null
  LET before_fix = IS_NUMBER(created) AND created < DATE_TIMESTAMP('{FIX_MERGED_AT}')
  LET verdict = (NOT {_known("a")} OR NOT IS_STRING(b)) ? 'unclassified'
    : (b == '' OR a == b OR granted) ? 'keep'
    : before_fix ? 'drop' : 'unclassified'
  FILTER verdict != 'keep'
  RETURN {{key: e._key, verdict: verdict}}
"""


@dataclass(frozen=True)
class LegacyClass:
    """One class of legacy row: its read-only ``ROWS`` query and where its repair writes."""

    name: str
    rows_query: str
    #: Collection the repair writes to (``None`` = report-only).
    target_collection: str
    #: The verdict that is repaired; every other verdict is left and counted.
    repair_verdict: str


CLASSES: Final[tuple[LegacyClass, ...]] = (
    LegacyClass("workflow_templates_of_private_species", WORKFLOW_TEMPLATE_ROWS, col.WORKFLOW_TEMPLATES, "reown"),
    LegacyClass("slot_field_edge_disagreement", SLOT_EDGE_ROWS, col.HAS_SLOT, "move_edge"),
    LegacyClass("equipment_at_foreign", EQUIPMENT_AT_ROWS, col.EQUIPMENT_AT, "drop"),
    LegacyClass("assigned_to_location_foreign", ASSIGNED_TO_LOCATION_ROWS, col.ASSIGNED_TO_LOCATION, "drop"),
    LegacyClass("log_slot_foreign", LOG_SLOT_ROWS, col.LOG_SLOT, "drop"),
    LegacyClass("feeds_from_foreign", FEEDS_FROM_ROWS, col.FEEDS_FROM, "drop"),
    LegacyClass("entry_for_species_foreign", ENTRY_FOR_SPECIES_ROWS, col.ENTRY_FOR_SPECIES, "drop"),
)


def count_query(rows_query: str) -> str:
    """The operator's read-only count for one class: verdict -> number of rows."""
    return f"FOR r IN ({rows_query}) COLLECT verdict = r.verdict WITH COUNT INTO n RETURN {{verdict: verdict, n: n}}"


#: ``name -> count query``. The migration's dry run and the integration test run these
#: very strings; the PR body lists them for the operator's pre-deploy check.
COUNT_QUERIES: Final[dict[str, str]] = {c.name: count_query(c.rows_query) for c in CLASSES}

#: The collections a class reads; a class whose collection is missing has nothing to count.
REQUIRED_COLLECTIONS: Final[dict[str, tuple[str, ...]]] = {
    "workflow_templates_of_private_species": (col.WORKFLOW_TEMPLATES, col.SPECIES, col.TENANT_HAS_ACCESS),
    "slot_field_edge_disagreement": (col.SLOTS, col.HAS_SLOT, col.LOCATIONS, col.SITES),
    "equipment_at_foreign": (col.EQUIPMENT_AT, col.EQUIPMENT, col.LOCATIONS, col.SITES),
    "assigned_to_location_foreign": (col.ASSIGNED_TO_LOCATION, col.LOCATION_ASSIGNMENTS, col.LOCATIONS, col.SITES),
    "log_slot_foreign": (col.LOG_SLOT, col.WATERING_LOGS, col.SLOTS, col.LOCATIONS, col.SITES),
    "feeds_from_foreign": (col.FEEDS_FROM, col.TANKS),
    "entry_for_species_foreign": (
        col.ENTRY_FOR_SPECIES,
        col.PLANTING_RUN_ENTRIES,
        col.PLANTING_RUNS,
        col.SPECIES,
        col.TENANT_HAS_ACCESS,
    ),
}
