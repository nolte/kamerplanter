"""v0093 — REQ-053 migration M1: garden-plan collections, edges, indexes; dimensions/position → geometry (#2323).

**Structure (§20.14).** Creates the five document collections (``garden_objects``,
``care_events``, ``irrigation_zones``, ``garden_plan_audit``, ``bed_templates``) and
the eight edge collections (``has_garden_object``, ``run_planned_at``, ``care_event_at``,
``task_logged_as``, ``has_irrigation_zone``, ``zone_covers``, ``zone_supplied_by``,
``zone_actuated_by``), wires them into ``kamerplanter_graph``, widens the existing
definitions ``belongs_to_tenant`` (+ ``care_events``, ``irrigation_zones``,
``bed_templates`` — **not** ``garden_objects``, E-01), ``care_event_for`` (+
``care_events``) and ``has_task`` (+ ``garden_objects``), and adds the §20.14 indexes.
No ``tenant_key`` index on ``locations`` / ``slots`` / ``garden_objects`` (E-01, #2107):
their tenant is their site's. Fresh databases get the identical shape from
``ensure_collections``; this migration brings existing volumes — and the standalone
``python -m app.migrations`` path, which does not call ``ensure_collections`` — to it.

**Data (§9.2a, §20.8, O-01/O-02).** Every location without ``geometry`` whose
``dimensions ≠ (0, 0, 0)`` gets a ``rect`` at ``origin (0, 0)`` with ``width_m`` = B
and ``length_m`` = L, and ``height_m`` = H when it has none. Every slot without
``geometry`` gets a bed-frame ``point`` at ``(col × pitch, row × pitch)`` from its
``position`` with ``pitch`` = its location's ``pitch_m`` (default 0.30 m when the
location declares none — the report counts how often that assumption was made),
``row_index``, a 1-based ``sequence`` within the location and ``geometry_source =
migrated_grid``. The derivation lives in
:mod:`app.migrations.support.garden_plan_geometry`. ``dimensions`` and ``position``
are **kept**; WP 1.5 removes them with their readers.

**One-time, by design (M-1).** The migration derives once, for the rows present when
it runs. Until WP 1.7 lands the models that write ``geometry`` themselves, a slot or
location created after this version applied carries no geometry — the window is
the gap between WP 1.4 and WP 1.7 on an installation that boots in between (a
``develop`` deployment), and the remedy is a later version that calls the same
support module again, not a re-run of this one.

**Idempotent (M-3).** A collection, edge, definition entry or index that exists is
not touched; a document that carries ``geometry`` (``height_m``) is not touched. A
second run reports ``changed == 0``.

**Dry run (M-5).** Computes the full report — the pending structure and, per
collection, the affected counts, the locations whose slots all share one cell (the
measured real-volume case) and the keys of rows the derivation refuses — and
writes nothing. Operators read the ``garden_plan_geometry_dry_run`` log line before
the production run (plan §8, P-1); the CLI summary carries only the totals.

**Not reversible (M-6).** The new collections may hold data by the time anyone asks;
``ensure_collections`` re-creates the structure on every boot, so dropping it would
not restore the pre-migration state; and the derived geometries are estimates the
user is expected to correct in the editor (R-08) — an inverse would discard those
corrections, while the legacy fields they were derived from are still present.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from typing import Any, cast

import structlog
from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport
from app.migrations.support.garden_plan_geometry import (
    MIGRATED_GRID,
    effective_pitch,
    grid_cell,
    has_dimensions,
    height_from_dimensions,
    height_is_unset,
    point_from_grid,
    rect_from_dimensions,
    sequence_ranks,
)
from app.migrations.support.legacy_indexes import IndexShape

logger = structlog.get_logger(__name__)

# ── The target structure, frozen here so a later change of collections.py does not
# change what this applied version did. The unit test pins these to literals and
# asserts the bootstrap is a superset; when the bootstrap moves on, the test moves,
# never this module (M-7).

_DOC_COLLECTIONS: tuple[str, ...] = (
    "garden_objects",
    "care_events",
    "irrigation_zones",
    "garden_plan_audit",
    "bed_templates",
)


def _edge(name: str, source: str, target: str) -> dict[str, Any]:
    return {"edge_collection": name, "from_vertex_collections": [source], "to_vertex_collections": [target]}


_NEW_EDGE_DEFINITIONS: tuple[dict[str, Any], ...] = (
    _edge("has_garden_object", "sites", "garden_objects"),
    _edge("run_planned_at", "planting_runs", "slots"),
    _edge("care_event_at", "care_events", "locations"),
    _edge("task_logged_as", "tasks", "care_events"),
    _edge("has_irrigation_zone", "sites", "irrigation_zones"),
    _edge("zone_covers", "irrigation_zones", "locations"),
    _edge("zone_supplied_by", "irrigation_zones", "garden_objects"),
    _edge("zone_actuated_by", "irrigation_zones", "actuators"),
)

_EDGE_COLLECTIONS: tuple[str, ...] = tuple(definition["edge_collection"] for definition in _NEW_EDGE_DEFINITIONS)

#: Existing definitions this migration widens: ``edge → (added from-vertices, to-vertices)``.
_WIDENED_EDGES: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "belongs_to_tenant": (("care_events", "irrigation_zones", "bed_templates"), ("tenants",)),
    "care_event_for": (("care_events",), ("plant_instances",)),
    "has_task": (("garden_objects",), ("tasks",)),
}

#: ``(collection, shape)`` — REQ-053 §20.14 / §20.10. Matched by the full shape
#: (fields, unique, sparse), so a non-unique twin never stands in for the constraint.
_INDEXES: tuple[tuple[str, IndexShape], ...] = (
    ("locations", IndexShape(("site_key", "bed_status"), unique=False)),
    ("garden_objects", IndexShape(("site_key", "object_type"), unique=False)),
    ("slots", IndexShape(("location_key", "slot_role"), unique=False)),
    ("care_events", IndexShape(("tenant_key", "location_key", "performed_at"), unique=False)),
    ("care_events", IndexShape(("tenant_key", "performed_at"), unique=False)),
    ("care_events", IndexShape(("task_key",), unique=False)),
    ("care_events", IndexShape(("tenant_key", "source_ref.collection", "source_ref.key"), unique=True, sparse=True)),
)

#: How many refused keys a report lists per reason before it only counts.
_LISTED_KEYS = 25

#: Documents per ``UPDATE`` statement.
_BATCH_SIZE = 500

# ``!= null`` rather than ``HAS``: a model that stores ``geometry: null`` must not
# read as "already derived".
_LOCATION_SCAN = """
FOR d IN @@collection
  FILTER IS_LIST(d.dimensions) AND LENGTH(d.dimensions) == 3
  FILTER d.dimensions[0] != 0 OR d.dimensions[1] != 0 OR d.dimensions[2] != 0
  RETURN { _key: d._key, dimensions: d.dimensions, has_geometry: d.geometry != null, has_height: d.height_m != null }
"""

_PITCH_SCAN = """
FOR d IN @@collection
  FILTER d.pitch_m != null
  RETURN { _key: d._key, pitch_m: d.pitch_m }
"""

_SLOT_SCAN = """
FOR s IN @@collection
  RETURN {
    _key: s._key, slot_id: s.slot_id, location_key: s.location_key, position: s.position,
    has_geometry: s.geometry != null
  }
"""

_APPLY = """
FOR u IN @updates
  UPDATE u._key WITH u.patch IN @@collection OPTIONS { keepNull: false }
"""

_LOCATION_COUNTERS = (
    "geometry_derived",
    "geometry_already_present",
    "height_derived",
    "height_already_present",
    "height_unset",
)
_LOCATION_REFUSALS = ("dimensions_invalid", "geometry_not_derivable", "height_not_derivable")
_SLOT_COUNTERS = (
    "point_derived",
    "geometry_already_present",
    "pitch_default_assumed",
    "locations_without_pitch",
    "at_grid_origin",
    "slots_sharing_a_cell",
    "locations_with_collapsed_grid",
)
_SLOT_REFUSALS = ("position_invalid", "location_missing", "point_not_derivable")


def _rows(db: StandardDatabase, query: str, collection: str) -> list[dict[str, Any]]:
    return list(cast(Cursor, db.aql.execute(query, bind_vars={"@collection": collection})))


def _chunks(items: Sequence[dict[str, Any]]) -> Iterator[Sequence[dict[str, Any]]]:
    for start in range(0, len(items), _BATCH_SIZE):
        yield items[start : start + _BATCH_SIZE]


def _index_present(db: StandardDatabase, collection: str, shape: IndexShape) -> bool:
    rows = db.collection(collection).indexes()
    return isinstance(rows, list) and any(isinstance(idx, dict) and shape.matches(idx) for idx in rows)


@dataclass
class _StructurePlan:
    document_collections: list[str] = field(default_factory=list)
    edge_collections: list[str] = field(default_factory=list)
    indexes: list[tuple[str, IndexShape]] = field(default_factory=list)
    graph_present: bool = True
    graph_edges: list[dict[str, Any]] = field(default_factory=list)
    #: ``edge → (from, to)`` — the full vertex lists to replace the definition with.
    graph_edges_widened: dict[str, tuple[list[str], list[str]]] = field(default_factory=dict)

    @property
    def changes(self) -> int:
        return (
            len(self.document_collections)
            + len(self.edge_collections)
            + len(self.indexes)
            + len(self.graph_edges)
            + len(self.graph_edges_widened)
        )

    def report(self) -> dict[str, Any]:
        return {
            "document_collections": list(self.document_collections),
            "edge_collections": list(self.edge_collections),
            "indexes": [
                {"collection": name, "fields": list(shape.fields), "unique": shape.unique, "sparse": shape.sparse}
                for name, shape in self.indexes
            ],
            "graph_present": self.graph_present,
            "graph_edges": [definition["edge_collection"] for definition in self.graph_edges],
            "graph_edges_widened": {
                edge: {"from": fr, "to": to} for edge, (fr, to) in self.graph_edges_widened.items()
            },
        }


def _plan_structure(db: StandardDatabase) -> _StructurePlan:
    plan = _StructurePlan()
    plan.document_collections = [name for name in _DOC_COLLECTIONS if not db.has_collection(name)]
    plan.edge_collections = [name for name in _EDGE_COLLECTIONS if not db.has_collection(name)]
    # An index is pending when its collection lacks it — or when the collection is one
    # this migration creates (it gets the index right after). A bootstrap-owned
    # collection (locations, slots) that is absent is the bootstrap's to create, with
    # the index, on the next boot.
    plan.indexes = [
        (name, shape)
        for name, shape in _INDEXES
        if (name in _DOC_COLLECTIONS if not db.has_collection(name) else not _index_present(db, name, shape))
    ]
    plan.graph_present = bool(db.has_graph(col.GRAPH_NAME))
    if not plan.graph_present:
        # The bootstrap creates the graph with every definition; nothing to wire here.
        return plan
    graph = db.graph(col.GRAPH_NAME)
    # Migrations run on a synchronous database, so the driver returns the list itself.
    definitions = cast(list[dict[str, Any]], graph.edge_definitions())
    existing = {definition["edge_collection"]: definition for definition in definitions}
    plan.graph_edges = [d for d in _NEW_EDGE_DEFINITIONS if d["edge_collection"] not in existing]
    for edge in _WIDENED_EDGES:
        added_from, target_to = _WIDENED_EDGES[edge]
        current = existing.get(edge)
        if current is None:
            # Never bootstrapped — an older volume than any this repository shipped; the
            # bootstrap adds the full definition on the next boot.
            continue
        current_from = list(current.get("from_vertex_collections") or [])
        current_to = list(current.get("to_vertex_collections") or [])
        missing_from = [name for name in added_from if name not in current_from]
        missing_to = [name for name in target_to if name not in current_to]
        if missing_from or missing_to:
            plan.graph_edges_widened[edge] = (current_from + missing_from, current_to + missing_to)
    return plan


def _apply_structure(db: StandardDatabase, plan: _StructurePlan) -> None:
    for name in plan.document_collections:
        db.create_collection(name)
    for name in plan.edge_collections:
        db.create_collection(name, edge=True)
    for name, shape in plan.indexes:
        db.collection(name).add_persistent_index(
            fields=list(shape.fields), unique=shape.unique, sparse=shape.sparse, in_background=True
        )
    if not plan.graph_present:
        return
    graph = db.graph(col.GRAPH_NAME)
    for definition in plan.graph_edges:
        graph.create_edge_definition(**definition)
    for edge, (from_vertices, to_vertices) in plan.graph_edges_widened.items():
        graph.replace_edge_definition(
            edge_collection=edge, from_vertex_collections=from_vertices, to_vertex_collections=to_vertices
        )


class _Refusals:
    """Keys the derivation refused, listed up to a cap and always counted."""

    def __init__(self) -> None:
        self.count = 0
        self.keys: list[str] = []

    def add(self, key: str) -> None:
        self.count += 1
        if len(self.keys) < _LISTED_KEYS:
            self.keys.append(key)

    def report(self) -> dict[str, Any]:
        return {"count": self.count, "keys": list(self.keys)}


@dataclass
class _DataPlan:
    """The pending document patches of one collection, with a report of fixed shape.

    Every counter and every refusal reason is present in the report (zero when
    nothing happened), so a log query can rely on the keys.
    """

    counter_names: tuple[str, ...]
    refusal_names: tuple[str, ...]
    scanned: int = 0
    updates: list[dict[str, Any]] = field(default_factory=list)
    counters: dict[str, int] = field(default_factory=dict)
    refusals: dict[str, _Refusals] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.counters = {name: 0 for name in self.counter_names}
        self.refusals = {name: _Refusals() for name in self.refusal_names}

    def count(self, name: str, by: int = 1) -> None:
        self.counters[name] += by

    def refuse(self, reason: str, key: str) -> None:
        self.refusals[reason].add(key)

    def report(self, *, dry_run: bool) -> dict[str, Any]:
        verb = "will_update" if dry_run else "updated"
        return {
            "scanned": self.scanned,
            verb: len(self.updates),
            **self.counters,
            "refused": {reason: refusal.report() for reason, refusal in self.refusals.items()},
        }


def _plan_locations(db: StandardDatabase) -> _DataPlan:
    """Every location with a non-zero ``dimensions`` that still lacks ``geometry`` or ``height_m``."""
    plan = _DataPlan(_LOCATION_COUNTERS, _LOCATION_REFUSALS)
    if not db.has_collection(col.LOCATIONS):
        return plan
    row: dict[str, Any]
    for row in _rows(db, _LOCATION_SCAN, col.LOCATIONS):
        plan.scanned += 1
        dimensions = row.get("dimensions")
        if not has_dimensions(dimensions):
            plan.refuse("dimensions_invalid", row["_key"])  # the AQL filter passed a non-numeric triple
            continue
        patch: dict[str, Any] = {}
        if row.get("has_geometry"):
            plan.count("geometry_already_present")
        else:
            geometry = rect_from_dimensions(dimensions)
            if geometry is None:
                plan.refuse("geometry_not_derivable", row["_key"])
            else:
                patch["geometry"] = geometry
                plan.count("geometry_derived")
        if row.get("has_height"):
            plan.count("height_already_present")
        elif height_is_unset(dimensions):
            plan.count("height_unset")
        else:
            height = height_from_dimensions(dimensions)
            if height is None:
                plan.refuse("height_not_derivable", row["_key"])
            else:
                patch["height_m"] = height
                plan.count("height_derived")
        if patch:
            plan.updates.append({"_key": row["_key"], "patch": patch})
    return plan


def _plan_slots(db: StandardDatabase) -> _DataPlan:
    """Every slot without ``geometry``: a bed-frame point from its grid cell and its location's pitch."""
    plan = _DataPlan(_SLOT_COUNTERS, _SLOT_REFUSALS)
    if not db.has_collection(col.SLOTS):
        return plan
    pitches: dict[str, Any] = {}
    if db.has_collection(col.LOCATIONS):
        pitches = {row["_key"]: row["pitch_m"] for row in _rows(db, _PITCH_SCAN, col.LOCATIONS)}
    slots = _rows(db, _SLOT_SCAN, col.SLOTS)
    plan.scanned = len(slots)
    ranks = sequence_ranks(slots)
    assumed_locations: set[str] = set()
    occupancy: dict[tuple[str, tuple[int, int]], int] = {}
    slot: dict[str, Any]
    for slot in slots:
        if slot.get("has_geometry"):
            plan.count("geometry_already_present")
            continue
        cell = grid_cell(slot.get("position"))
        if cell is None:
            plan.refuse("position_invalid", slot["_key"])
            continue
        location_key = slot.get("location_key")
        if not isinstance(location_key, str) or not location_key:
            plan.refuse("location_missing", slot["_key"])
            continue
        pitch, assumed = effective_pitch(pitches.get(location_key))
        if assumed:
            plan.count("pitch_default_assumed")
            assumed_locations.add(location_key)
        if cell == (0, 0):
            plan.count("at_grid_origin")
        point = point_from_grid(cell, pitch)
        if point is None:
            plan.refuse("point_not_derivable", slot["_key"])
            continue
        plan.count("point_derived")
        occupancy[(location_key, cell)] = occupancy.get((location_key, cell), 0) + 1
        plan.updates.append(
            {
                "_key": slot["_key"],
                "patch": {
                    "geometry": point,
                    "row_index": cell[0],
                    "sequence": ranks[slot["_key"]],
                    "geometry_source": MIGRATED_GRID,
                },
            }
        )
    plan.count("locations_without_pitch", len(assumed_locations))
    # The measured real-volume case: every slot of a location on one cell. Counted per
    # location and per slot so the dry-run report shows the stacking before P-1.
    plan.count("slots_sharing_a_cell", sum(n for n in occupancy.values() if n > 1))
    plan.count("locations_with_collapsed_grid", len({loc for (loc, _), n in occupancy.items() if n > 1}))
    return plan


def _apply_updates(db: StandardDatabase, collection: str, updates: Sequence[dict[str, Any]]) -> None:
    for chunk in _chunks(updates):
        db.aql.execute(_APPLY, bind_vars={"@collection": collection, "updates": list(chunk)})


class GardenPlanGeometryMigration(Migration):
    version = "0093"
    name = "garden_plan_geometry"
    description = (
        "REQ-053 M1: garden-plan collections, edges and indexes; Location.dimensions → rect geometry + "
        "height_m, Slot.position → bed-frame point (pitch_m, default 0.30) with row_index/sequence (#2323)."
    )
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        structure = _plan_structure(db)
        locations = _plan_locations(db)
        slots = _plan_slots(db)
        changes = structure.changes + len(locations.updates) + len(slots.updates)
        scanned = len(_DOC_COLLECTIONS) + len(_EDGE_COLLECTIONS) + len(_INDEXES) + locations.scanned + slots.scanned
        details = {
            "structure": structure.report(),
            col.LOCATIONS: locations.report(dry_run=dry_run),
            col.SLOTS: slots.report(dry_run=dry_run),
        }

        if dry_run:
            logger.info("garden_plan_geometry_dry_run", pending_changes=changes, details=details)
            return MigrationReport(
                version=self.version, name=self.name, scanned=scanned, changed=0, dry_run=True, details=details
            )

        _apply_structure(db, structure)
        _apply_updates(db, col.LOCATIONS, locations.updates)
        _apply_updates(db, col.SLOTS, slots.updates)
        logger.info("garden_plan_geometry_applied", changed=changes, details=details)
        return MigrationReport(
            version=self.version, name=self.name, scanned=scanned, changed=changes, dry_run=False, details=details
        )


migration = GardenPlanGeometryMigration()
