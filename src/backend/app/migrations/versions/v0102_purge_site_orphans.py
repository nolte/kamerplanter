"""v0102 — #2513 / #2528 (REQ-053): purge what a site delete before the cascade fix left behind, and release beds
whose bed template is gone.

**What.** Until #2513 ``delete_site`` removed the site and its ``contains`` tree only, and ``delete_location``
cut a hand list of edges. What they left is removed here, in this order:

1. every row of ``garden_objects``, ``season_states``, ``weather_forecasts``, ``climate_normals``,
   ``weather_source_configs``, ``irrigation_demands`` and ``irrigation_zones`` whose non-empty ``site_key`` names no
   ``sites`` document;
2. every garden object without a ``site_key`` that ``has_garden_object`` edges reach from missing sites only — the
   edge is its only link, and step 5 cuts it;
3. every location whose non-empty ``site_key`` names no site and every location without a ``site_key`` whose
   parent is gone — at least one ``contains`` edge reaches it from a vertex that does not exist, and none from one
   that does — unless a ``contains`` edge reaches it from a vertex that stays; plus the locations below them that
   name no live site and hang under nothing that stays;
4. the slots of those locations: by ``location_key``, and by ``has_slot`` when the slot names no location (a slot
   naming another location is that location's; only the stale edge goes in step 5);
5. every edge of the derived edge sets (:data:`_EDGE_ENDS`) whose end in one of those vertex collections names a
   vertex that does not exist or is removed by steps 1–4;
6. (#2528, a *nulling* step, after every removal) ``template_key`` is unset on every location whose non-empty
   ``template_key`` names no ``bed_templates`` document and that steps 1–5 do not remove. Until #2528 deleting a
   bed template left that key behind, and a dangling one made a tenant-archive re-import refuse the archive.

**Never guesses.** A row whose site exists is never touched; neither is a location that names a live site or that a
``contains`` edge from a surviving vertex reaches — nor an unsited location that *no* ``contains`` edge reaches:
``create_location`` writes none for a location given neither a parent nor a site, so such a standalone location was
never attached and its missing edge is no evidence of a gone parent (it stays, with its slots and their edges).
``care_events`` and ``garden_plan_audit`` are history (REQ-053 GP-FR-101, §20.13 SR-011) and are not in any list
here — nor are their own edges (``belongs_to_tenant`` is only checked on its ``sites`` / ``irrigation_zones`` end).
An edge is judged on the end that touches one of the listed vertex collections only. A database without a
``sites`` collection is left alone: every ``site_key`` would look dangling there — the early return also skips
step 6. Step 6 unsets nothing but ``template_key`` and only when *no* bed template of that key exists: a key naming
any existing template — even another tenant's — is not touched (who may use which template is not this migration's
question); a database without ``bed_templates`` is left alone in that step (every key would look dangling).

**Frozen lists.** :data:`_SITE_KEYED_ROWS` and :data:`_EDGE_ENDS` are literals: they are the derivation
(``edges_touching(...)``, ``ZONE_EDGES``, ``_SITE_DEPENDENTS``) at the time of writing, pinned by
``tests/unit/migrations/versions/test_v0102_purge_site_orphans.py``. When the graph grows, that test fails — update
the test's expectation and write a new migration for the new relation; never edit this one (it has run).

**Idempotent (M-3).** Every step matches only rows or edges that are dangling; after a run none are, so a second run
matches nothing and changes nothing.

**Counted, not assumed (D1).** ``REMOVE … OPTIONS {ignoreErrors: true}`` skips a document that is gone by the time
it runs, so ``removed`` counts the keys the statement actually returned — it may be lower than ``matched``. Step 6's
``UPDATE`` does the same and re-checks the dangling condition at write time (a bed given a live template between plan
and apply keeps it): ``nulled`` counts what the statement returned.

**Dry run (M-5).** The whole removal set is planned before the first write — each step sees what the earlier steps
would remove as gone — so a dry run reports the same ``matched`` counts as the run that applies them, and writes
nothing. ``details[<step>] = {matched, removed, keys}``, ``keys`` the first :data:`_LISTED` (row keys; edge ids);
step 6 reports ``{matched, nulled, keys}``.

**Not reversible (M-6).** The rows are gone with their site; nothing would know where to put them back — nor which
template a released bed once named.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from functools import partial
from typing import Any, cast

import structlog
from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)

#: How many keys a step lists before it only counts.
_LISTED = 25

#: Documents per ``REMOVE`` statement.
_BATCH_SIZE = 500

_SITES = "sites"
_LOCATIONS = "locations"
_SLOTS = "slots"
_CONTAINS = "contains"
_HAS_SLOT = "has_slot"
_GARDEN_OBJECTS = "garden_objects"
_HAS_GARDEN_OBJECT = "has_garden_object"
_BED_TEMPLATES = "bed_templates"

#: Rows that exist only for one site, selected by ``site_key`` — garden objects and ``site_repository._SITE_DEPENDENTS``
#: (irrigation zones included) as of #2513. Frozen; see the module docstring.
_SITE_KEYED_ROWS: tuple[str, ...] = (
    "garden_objects",
    "season_states",
    "weather_forecasts",
    "climate_normals",
    "weather_source_configs",
    "irrigation_demands",
    "irrigation_zones",
)

#: ``(vertex collection, ((edge collection, end), ...))`` — ``edges_touching(vertex)`` for every vertex collection a
#: site delete removes, and ``ZONE_EDGES`` for ``irrigation_zones``, as of #2513. Frozen; see the module docstring.
_EDGE_ENDS: tuple[tuple[str, tuple[tuple[str, str], ...]], ...] = (
    (
        "sites",
        (
            ("contains", "_from"),
            ("belongs_to_tenant", "_from"),
            ("has_season_state", "_from"),
            ("located_at", "_to"),
            ("has_forecast", "_from"),
            ("has_weather_source_config", "_from"),
            ("has_climate_normal", "_from"),
            ("located_in_zone", "_from"),
            ("has_irrigation_demand", "_from"),
            ("has_garden_object", "_from"),
            ("has_irrigation_zone", "_from"),
        ),
    ),
    (
        "locations",
        (
            ("contains", "_from"),
            ("contains", "_to"),
            ("has_slot", "_from"),
            ("run_at_location", "_to"),
            ("succession_at", "_to"),
            ("has_tank", "_from"),
            ("supplies", "_to"),
            ("has_task", "_from"),
            ("wf_executing", "_from"),
            ("assigned_to_location", "_to"),
            ("overwinters_at", "_to"),
            ("located_at", "_to"),
            ("equipment_at", "_to"),
            ("has_actuator", "_from"),
            ("actuator_controls_location", "_to"),
            ("location_profile", "_from"),
            ("care_event_at", "_to"),
            ("zone_covers", "_to"),
        ),
    ),
    (
        "slots",
        (
            ("has_slot", "_to"),
            ("filled_with", "_from"),
            ("placed_in", "_to"),
            ("adjacent_to", "_from"),
            ("adjacent_to", "_to"),
            ("log_slot", "_to"),
            ("system_has_growbed", "_to"),
            ("run_planned_at", "_to"),
        ),
    ),
    ("garden_objects", (("has_task", "_from"), ("has_garden_object", "_to"), ("zone_supplied_by", "_to"))),
    ("season_states", (("has_season_state", "_to"),)),
    ("weather_forecasts", (("has_forecast", "_to"),)),
    ("climate_normals", (("has_climate_normal", "_to"),)),
    ("weather_source_configs", (("has_weather_source_config", "_to"),)),
    ("irrigation_demands", (("has_irrigation_demand", "_to"), ("demand_for_run", "_to"))),
    (
        "irrigation_zones",
        (
            ("belongs_to_tenant", "_from"),
            ("has_irrigation_zone", "_to"),
            ("zone_covers", "_from"),
            ("zone_supplied_by", "_from"),
            ("zone_actuated_by", "_from"),
        ),
    ),
)

_ROWS_OF_MISSING_SITES = """
FOR d IN @@col
  FILTER IS_STRING(d.site_key) AND d.site_key != "" AND DOCUMENT(@sites, d.site_key) == null
  SORT d._key
  RETURN d._id
"""

#: A garden object without a ``site_key`` whose every ``has_garden_object`` source is a missing site. ``DOCUMENT``
#: on an id of a collection that does not exist returns ``null`` (measured on ArangoDB 3.12), it does not raise.
_UNSITED_OBJECTS_OF_MISSING_SITES = """
FOR o IN @@objects
  FILTER o.site_key == null OR o.site_key == ""
  LET sources = (FOR e IN @@has_object FILTER e._to == o._id RETURN e._from)
  FILTER LENGTH(sources) > 0 AND LENGTH(FOR source IN sources FILTER DOCUMENT(source) != null RETURN 1) == 0
  SORT o._key
  RETURN o._id
"""

#: A location naming a missing site, or naming no site and reached by no ``contains`` edge from an existing vertex,
#: with the parents that still exist and how many ``contains`` sources are gone. ``DOCUMENT`` of an id in a collection
#: that does not exist is ``null``, so such a parent counts as gone. Which unsited row is a seed is decided by
#: :func:`_is_orphan_seed` (an unsited one needs ``gone_parents > 0``).
_LOCATIONS_OF_MISSING_SITES = """
FOR l IN @@locations
  LET unsited = l.site_key == null OR l.site_key == ""
  FILTER unsited OR (IS_STRING(l.site_key) AND DOCUMENT(@sites, l.site_key) == null)
  LET sources = (FOR e IN @@contains FILTER e._to == l._id RETURN e._from)
  LET parents = (FOR source IN sources FILTER DOCUMENT(source) != null RETURN source)
  FILTER NOT unsited OR LENGTH(parents) == 0
  RETURN {
    id: l._id, site_live: false, unsited: unsited, gone_parents: LENGTH(sources) - LENGTH(parents), parents: parents
  }
"""

#: The locations directly below *ids*, each with whether it names a live site and its existing parents.
_CHILD_LOCATIONS = """
FOR e IN @@contains
  FILTER e._from IN @ids AND IS_SAME_COLLECTION(@locations_name, e._to)
  LET l = DOCUMENT(e._to)
  FILTER l != null
  COLLECT id = l._id, site_key = l.site_key
  RETURN {
    id: id,
    site_live: IS_STRING(site_key) AND site_key != "" AND DOCUMENT(@sites, site_key) != null,
    parents: (FOR p IN @@contains FILTER p._to == id AND DOCUMENT(p._from) != null RETURN p._from)
  }
"""

_SLOTS_OF_LOCATIONS = """
RETURN UNION_DISTINCT(
  (FOR s IN @@slots FILTER s.location_key IN @keys RETURN s._id),
  (FOR e IN @@has_slot FILTER e._from IN @ids AND IS_SAME_COLLECTION(@slots_name, e._to)
     LET s = DOCUMENT(e._to)
     FILTER s != null AND (s.location_key == null OR s.location_key == "")
     RETURN e._to)
)
"""


#: A location whose non-empty ``template_key`` names no bed template (#2528). Measured on ArangoDB 3.12.12:
#: ``DOCUMENT("bed_templates", "sites/x")`` returns ``null`` for an existing site ``x`` - a key in id form of another
#: collection never resolves across collections, so it counts as dangling (and ``"bed_templates/<key>"`` resolves).
_DANGLING_TEMPLATE_KEYS = """
FOR l IN @@locations
  FILTER IS_STRING(l.template_key) AND l.template_key != "" AND DOCUMENT(@templates, l.template_key) == null
  SORT l._key
  RETURN l._id
"""

#: The write re-checks the planner's condition, so a location that got a live template between plan and apply (or
#: lost its key) is not edited and not counted.
_UNSET_TEMPLATE_KEY = """
FOR l IN @@col
  FILTER l._key IN @keys AND IS_STRING(l.template_key) AND l.template_key != ""
    AND DOCUMENT(@templates, l.template_key) == null
  UPDATE l WITH {template_key: null} IN @@col OPTIONS {keepNull: false, ignoreErrors: true}
  RETURN OLD._key
"""


def _dangling_end(end: str) -> str:
    """The scan for one edge end; *end* is one of two literals from :data:`_EDGE_ENDS`, never input.

    ``DOCUMENT`` of an id whose vertex collection does not exist returns ``null`` (no error, ArangoDB 3.12), so an edge
    into a collection missing from the database counts as dangling — its vertex does not exist.
    """
    if end not in ("_from", "_to"):
        raise ValueError(f"Not an edge endpoint: {end!r}")
    return f"""
FOR e IN @@edges
  FILTER IS_SAME_COLLECTION(@vertex, e.{end})
  FILTER e.{end} IN @removed OR DOCUMENT(e.{end}) == null
  RETURN e._id
"""


def _split_id(doc_id: str) -> tuple[str, str]:
    """``"<collection>/<key>"`` -> ``(collection, key)``."""
    collection, key = doc_id.split("/", 1)
    return collection, key


def _in_collection(doc_id: str, collection: str) -> bool:
    return doc_id.startswith(f"{collection}/")


def _ids(cursor: Any) -> list[str]:
    return [str(doc_id) for doc_id in cast(Cursor, cursor)]


def _rows_of_missing_sites(db: StandardDatabase, gone: Sequence[str], *, collection: str) -> list[str]:
    del gone  # a site-keyed row depends on its site only
    if not db.has_collection(collection):
        return []
    return _ids(db.aql.execute(_ROWS_OF_MISSING_SITES, bind_vars={"@col": collection, "sites": _SITES}))


def _unsited_objects_of_missing_sites(db: StandardDatabase, gone: Sequence[str]) -> list[str]:
    del gone  # judged on the sites alone; step 1 already took every object that names a site
    if not db.has_collection(_GARDEN_OBJECTS) or not db.has_collection(_HAS_GARDEN_OBJECT):
        return []
    return _ids(
        db.aql.execute(
            _UNSITED_OBJECTS_OF_MISSING_SITES,
            bind_vars={"@objects": _GARDEN_OBJECTS, "@has_object": _HAS_GARDEN_OBJECT},
        )
    )


def _is_orphan_seed(row: dict[str, Any]) -> bool:
    """A seed row of :data:`_LOCATIONS_OF_MISSING_SITES` is an orphan candidate (R1 of the #2513 review).

    A location naming a missing site is one. An unsited location is one only on evidence of a gone parent — a
    ``contains`` edge from a vertex that does not exist; one with no ``contains`` edge at all was never attached
    (``create_location`` writes none without parent and site) and stays.
    """
    return not row["unsited"] or int(row["gone_parents"]) > 0


def _locations_of_missing_sites(db: StandardDatabase, gone: Sequence[str]) -> list[str]:
    """Locations of a missing site no surviving ``contains`` reaches, then their subtree down to a live anchor.

    The seeds also hold every unsited location whose parent is gone (:func:`_is_orphan_seed`). A location goes when it
    names no live site and every existing parent goes too. The walk repeats until no new location qualifies; a
    location that names a live site, or that a surviving vertex contains, stays.
    """
    del gone
    if not db.has_collection(_LOCATIONS) or not db.has_collection(_CONTAINS):
        return []
    known: dict[str, dict[str, Any]] = {
        str(row["id"]): row
        for row in cast(
            Cursor,
            db.aql.execute(
                _LOCATIONS_OF_MISSING_SITES,
                bind_vars={"@locations": _LOCATIONS, "@contains": _CONTAINS, "sites": _SITES},
            ),
        )
        if _is_orphan_seed(row)
    }
    removed: dict[str, None] = {}
    while True:
        new = [
            doc_id
            for doc_id, row in known.items()
            if doc_id not in removed and not row["site_live"] and all(p in removed for p in row["parents"])
        ]
        if not new:
            break
        removed.update({doc_id: None for doc_id in new})
        for row in cast(
            Cursor,
            db.aql.execute(
                _CHILD_LOCATIONS,
                bind_vars={"@contains": _CONTAINS, "ids": new, "locations_name": _LOCATIONS, "sites": _SITES},
            ),
        ):
            known.setdefault(str(row["id"]), row)
    return sorted(removed)


def _slots_of_removed_locations(db: StandardDatabase, gone: Sequence[str]) -> list[str]:
    location_ids = [doc_id for doc_id in gone if _in_collection(doc_id, _LOCATIONS)]
    if not location_ids or not db.has_collection(_SLOTS):
        return []
    rows = cast(
        Cursor,
        db.aql.execute(
            _SLOTS_OF_LOCATIONS,
            bind_vars={
                "@slots": _SLOTS,
                "@has_slot": _HAS_SLOT,
                "slots_name": _SLOTS,
                "keys": [_split_id(doc_id)[1] for doc_id in location_ids],
                "ids": location_ids,
            },
        ),
    )
    return sorted(str(doc_id) for row in rows for doc_id in row)


def _dangling_edges(db: StandardDatabase, gone: Sequence[str]) -> list[str]:
    """Every edge of :data:`_EDGE_ENDS` whose listed end names a vertex that is missing or removed above."""
    found: dict[str, None] = {}
    for vertex, ends in _EDGE_ENDS:
        removed = [doc_id for doc_id in gone if _in_collection(doc_id, vertex)]
        for edge, end in ends:
            if not db.has_collection(edge):
                continue
            found.update(
                {
                    doc_id: None
                    for doc_id in _ids(
                        db.aql.execute(
                            _dangling_end(end), bind_vars={"@edges": edge, "vertex": vertex, "removed": removed}
                        )
                    )
                }
            )
    return sorted(found)


def _locations_with_dangling_template_key(db: StandardDatabase, gone: Sequence[str]) -> list[str]:
    """Locations whose ``template_key`` names no bed template, minus those the removal steps take anyway."""
    if not db.has_collection(_LOCATIONS) or not db.has_collection(_BED_TEMPLATES):
        return []
    removed = set(gone)
    found = _ids(
        db.aql.execute(_DANGLING_TEMPLATE_KEYS, bind_vars={"@locations": _LOCATIONS, "templates": _BED_TEMPLATES})
    )
    return [doc_id for doc_id in found if doc_id not in removed]


#: The removal steps, in order. Each sees the ids the earlier ones remove as ``gone``; reported under its name. Their
#: ids are fed to :func:`_remove` — a step that only edits a row belongs in :data:`_NULLING_STEPS`.
_STEPS: tuple[tuple[str, Callable[[StandardDatabase, Sequence[str]], list[str]]], ...] = (
    *((f"{name}_of_missing_sites", partial(_rows_of_missing_sites, collection=name)) for name in _SITE_KEYED_ROWS),
    ("unsited_garden_objects_of_missing_sites", _unsited_objects_of_missing_sites),
    ("locations_of_missing_sites", _locations_of_missing_sites),
    ("slots_of_removed_locations", _slots_of_removed_locations),
    ("dangling_edges", _dangling_edges),
)

#: The nulling steps (#2528), after every removal step: planned with the full ``gone`` of the removals (a row removed
#: anyway is not edited), applied after them, reported as ``{matched, nulled, keys}``.
_NULLING_STEPS: tuple[tuple[str, Callable[[StandardDatabase, Sequence[str]], list[str]]], ...] = (
    ("locations_with_dangling_template_key", _locations_with_dangling_template_key),
)


def _remove(db: StandardDatabase, ids: Sequence[str]) -> int:
    """Remove *ids* in batches; returns how many documents were actually removed.

    ``ignoreErrors`` skips a document that is already gone (a concurrent delete between plan and apply) instead of
    failing the batch; such a document returns no ``OLD`` row and is not counted.
    """
    by_collection: dict[str, list[str]] = {}
    for doc_id in ids:
        collection, key = _split_id(doc_id)
        by_collection.setdefault(collection, []).append(key)
    removed = 0
    for collection, keys in by_collection.items():
        for start in range(0, len(keys), _BATCH_SIZE):
            removed += len(
                list(
                    cast(
                        Cursor,
                        db.aql.execute(
                            "FOR k IN @keys REMOVE k IN @@col OPTIONS {ignoreErrors: true} RETURN OLD._key",
                            bind_vars={"@col": collection, "keys": keys[start : start + _BATCH_SIZE]},
                        ),
                    )
                )
            )
    return removed


def _unset_template_key(db: StandardDatabase, ids: Sequence[str]) -> int:
    """Unset ``template_key`` on *ids* (locations) in batches; returns how many the ``UPDATE`` actually changed.

    A location that is gone by the time the batch runs, or whose ``template_key`` names a live template by then
    (re-checked in the statement), returns no ``OLD`` row and is not counted, so ``nulled`` may be lower than
    ``matched`` (the same rule as :func:`_remove`).
    """
    keys = [_split_id(doc_id)[1] for doc_id in ids]
    nulled = 0
    for start in range(0, len(keys), _BATCH_SIZE):
        nulled += len(
            list(
                cast(
                    Cursor,
                    db.aql.execute(
                        _UNSET_TEMPLATE_KEY,
                        bind_vars={
                            "@col": _LOCATIONS,
                            "templates": _BED_TEMPLATES,
                            "keys": keys[start : start + _BATCH_SIZE],
                        },
                    ),
                )
            )
        )
    return nulled


def _listed(step: str, ids: Sequence[str]) -> list[str]:
    """Edge ids stay ids (the collection says which relation); rows are listed by key."""
    first = list(ids[:_LISTED])
    return first if step == "dangling_edges" else [_split_id(doc_id)[1] for doc_id in first]


class PurgeSiteOrphansMigration(Migration):
    version = "0102"
    name = "purge_site_orphans"
    description = (
        "#2513: remove the site-keyed rows, locations and slots of sites that no longer exist, and every derived "
        "edge whose end in those collections is gone; care events and the plan audit stay. #2528: unset a "
        "location's template_key that names no bed template."
    )
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        if not db.has_collection(_SITES):
            # Also skips the nulling step: without sites this database is not one the migration can judge.
            return MigrationReport(
                version=self.version, name=self.name, scanned=0, changed=0, dry_run=dry_run, details={}
            )
        planned: list[tuple[str, list[str]]] = []
        gone: list[str] = []
        for step, plan in _STEPS:
            ids = plan(db, tuple(gone))
            planned.append((step, ids))
            gone.extend(ids)
        to_null = [(step, plan(db, tuple(gone))) for step, plan in _NULLING_STEPS]
        details: dict[str, Any] = {}
        changed = 0
        for step, ids in planned:
            removed = 0 if dry_run else _remove(db, ids)
            changed += removed
            details[step] = {"matched": len(ids), "removed": removed, "keys": _listed(step, ids)}
        for step, ids in to_null:
            nulled = 0 if dry_run else _unset_template_key(db, ids)
            changed += nulled
            details[step] = {"matched": len(ids), "nulled": nulled, "keys": _listed(step, ids)}
        scanned = len(gone) + sum(len(ids) for _, ids in to_null)
        report = MigrationReport(
            version=self.version, name=self.name, scanned=scanned, changed=changed, dry_run=dry_run, details=details
        )
        logger.info("site_orphans_dry_run" if dry_run else "site_orphans_purged", matched=scanned, changed=changed)
        return report


migration = PurgeSiteOrphansMigration()
