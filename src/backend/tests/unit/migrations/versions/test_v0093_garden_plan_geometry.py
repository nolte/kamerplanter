"""v0093 (#2323, REQ-053 M1): structure and data on a fake volume — idempotent, a dry run writes nothing.

The fake models exactly what the migration reads and writes: ``has_collection`` /
``create_collection``, ``indexes`` / ``add_persistent_index``, the graph's
``edge_definitions`` / ``create_edge_definition`` / ``replace_edge_definition``, and the
four AQL statements (three scans, one ``UPDATE``) dispatched on their text. The real
AQL is measured in ``tests/integration/test_v0093_garden_plan_geometry.py``.

Two fixtures: ``_legacy_volume`` holds the GP-ACC-036 tent (a 3 × 3 grid of explicit
cells) next to edge cases, and ``_real_volume`` holds what an installation actually
has — every slot at ``(0, 0)``, because no write path ever set a position.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.data_access.arango import collections as col
from app.migrations.framework.report import IrreversibleMigrationError
from app.migrations.versions import v0093_garden_plan_geometry as module
from app.migrations.versions.v0093_garden_plan_geometry import migration

_PRE_M1_EDGES: dict[str, tuple[list[str], list[str]]] = {
    col.BELONGS_TO_TENANT: (
        [col.SITES, col.PLANT_INSTANCES, col.PLANTING_RUNS, col.TANKS, col.FERTILIZERS, col.NUTRIENT_PLANS, col.TASKS],
        [col.TENANTS],
    ),
    col.CARE_EVENT_FOR: ([col.CARE_CONFIRMATIONS], [col.PLANT_INSTANCES]),
    col.HAS_TASK: ([col.PLANT_INSTANCES, col.PLANTING_RUNS, col.LOCATIONS, col.TANKS], [col.TASKS]),
}

#: What M1 leaves on a slot it derived — a fixture that claims "already migrated" carries all four.
_MIGRATED_SLOT_FIELDS = {
    "geometry": {"kind": "point", "origin": [0.6, 0.6]},
    "row_index": 2,
    "sequence": 3,
    "geometry_source": "migrated_grid",
}


class _FakeCollection:
    def __init__(self, docs: list[dict[str, Any]] | None = None, indexes: list[dict[str, Any]] | None = None) -> None:
        self.docs: dict[str, dict[str, Any]] = {doc["_key"]: dict(doc) for doc in docs or []}
        self._indexes = list(indexes or [])
        self.added_indexes: list[dict[str, Any]] = []

    def indexes(self) -> list[dict[str, Any]]:
        return list(self._indexes)

    def add_persistent_index(self, **kwargs: Any) -> None:
        self.added_indexes.append(kwargs)
        self._indexes.append({"type": "persistent", **kwargs})


class _FakeGraph:
    def __init__(self, definitions: list[dict[str, Any]]) -> None:
        self.definitions = {d["edge_collection"]: d for d in definitions}
        self.created: list[str] = []
        self.replaced: list[str] = []

    def edge_definitions(self) -> list[dict[str, Any]]:
        return [dict(d) for d in self.definitions.values()]

    def create_edge_definition(self, **definition: Any) -> None:
        self.created.append(definition["edge_collection"])
        self.definitions[definition["edge_collection"]] = definition

    def replace_edge_definition(self, **definition: Any) -> None:
        self.replaced.append(definition["edge_collection"])
        self.definitions[definition["edge_collection"]] = definition


class _InterruptedError(RuntimeError):
    """The fake's stand-in for a connection lost between two UPDATE statements."""


class _FakeAql:
    def __init__(self, db: _FakeDb) -> None:
        self.db = db
        self.updates: list[tuple[str, list[dict[str, Any]]]] = []
        #: Raise before applying the n-th UPDATE statement (1-based); ``None`` never.
        self.fail_at_update: int | None = None

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None, **_: Any) -> Any:
        bind_vars = bind_vars or {}
        docs = self.db.collections[bind_vars["@collection"]].docs
        if "UPDATE u._key" in query:
            if self.fail_at_update is not None and len(self.updates) + 1 >= self.fail_at_update:
                raise _InterruptedError("connection lost")
            self.updates.append((bind_vars["@collection"], list(bind_vars["updates"])))
            for update in bind_vars["updates"]:
                doc = docs[update["_key"]]
                for key, value in update["patch"].items():
                    if value is None:
                        doc.pop(key, None)
                    else:
                        doc[key] = value
            return iter(())
        if "dimensions" in query:
            return iter(
                {
                    "_key": d["_key"],
                    "dimensions": d["dimensions"],
                    "has_geometry": d.get("geometry") is not None,
                    "has_height": d.get("height_m") is not None,
                }
                for d in docs.values()
                if isinstance(d.get("dimensions"), list) and len(d["dimensions"]) == 3 and any(d["dimensions"])
            )
        if "pitch_m" in query:
            return iter(
                {"_key": d["_key"], "pitch_m": d["pitch_m"]} for d in docs.values() if d.get("pitch_m") is not None
            )
        if "s.position" in query:
            return iter(
                {
                    "_key": d["_key"],
                    "slot_id": d.get("slot_id"),
                    "location_key": d.get("location_key"),
                    "position": d.get("position"),
                    "has_geometry": d.get("geometry") is not None,
                }
                for d in docs.values()
            )
        raise AssertionError(f"unexpected query: {query}")


class _FakeDb:
    def __init__(
        self,
        *,
        collections: dict[str, _FakeCollection] | None = None,
        graph: _FakeGraph | None = None,
    ) -> None:
        self.collections = collections or {}
        self._graph = graph
        self.created: list[tuple[str, bool]] = []
        self.aql = _FakeAql(self)

    def has_collection(self, name: str) -> bool:
        return name in self.collections

    def collection(self, name: str) -> _FakeCollection:
        return self.collections[name]

    def create_collection(self, name: str, edge: bool = False) -> None:
        self.created.append((name, edge))
        self.collections[name] = _FakeCollection()

    def has_graph(self, name: str) -> bool:
        return self._graph is not None

    def graph(self, name: str) -> _FakeGraph:
        assert self._graph is not None
        return self._graph

    def snapshot(self) -> dict[str, dict[str, dict[str, Any]]]:
        return {name: {k: dict(d) for k, d in c.docs.items()} for name, c in self.collections.items()}


def _pre_m1_graph() -> _FakeGraph:
    return _FakeGraph(
        [
            {"edge_collection": edge, "from_vertex_collections": sources, "to_vertex_collections": targets}
            for edge, (sources, targets) in _PRE_M1_EDGES.items()
        ]
    )


def _bootstrapped_graph() -> _FakeGraph:
    return _FakeGraph([dict(d) for d in col.GRAPH_EDGE_DEFINITIONS])


def _bootstrapped_indexes() -> list[dict[str, Any]]:
    return [
        {"type": "persistent", "fields": list(shape.fields), "unique": shape.unique, "sparse": shape.sparse}
        for _, shape in module._INDEXES
    ]


def _slot(key: str, location: str, position: Any, **extra: Any) -> dict[str, Any]:
    slot_id = f"{location.upper()}_{key.upper()}"
    return {"_key": key, "slot_id": slot_id, "location_key": location, "position": position, **extra}


def _legacy_volume(*, graph: _FakeGraph | None = None) -> _FakeDb:
    """A pre-M1 volume with the GP-ACC-036 tent (explicit 3 × 3 cells) and the edge cases."""
    locations = _FakeCollection(
        [
            {"_key": "tent", "dimensions": [1.2, 1.2, 2.0]},
            {"_key": "bed", "dimensions": [2.4, 1.2, 0.0], "pitch_m": 0.25},
            {"_key": "unset", "dimensions": [0.0, 0.0, 0.0]},
            {"_key": "tall", "dimensions": [0.0, 0.0, 2.5]},
            {"_key": "sky", "dimensions": [1.0, 1.0, 1500.0]},
            {"_key": "text", "dimensions": ["1.2", 1.2, 0.0]},
            {
                "_key": "placed",
                "dimensions": [3.0, 1.0, 0.5],
                "geometry": {"kind": "circle", "origin": [2.0, 2.0], "radius_m": 1.0},
                "height_m": 0.5,
            },
        ]
    )
    slots = _FakeCollection(
        [_slot(f"t{row}{column}", "tent", [row, column]) for row in range(3) for column in range(3)]
        + [
            _slot("b01", "bed", [1, 2]),
            _slot("b00", "bed", [0, 0]),
            _slot("broken", "bed", "A1"),
            _slot("done", "bed", [2, 2], **_MIGRATED_SLOT_FIELDS),
            _slot("orphan", "", [0, 0]),
        ]
    )
    return _FakeDb(
        collections={col.LOCATIONS: locations, col.SLOTS: slots},
        graph=graph if graph is not None else _pre_m1_graph(),
    )


def _real_volume() -> _FakeDb:
    """What an installation holds: no position was ever written, every slot sits on (0, 0)."""
    locations = _FakeCollection(
        [{"_key": "tent", "dimensions": [1.2, 1.2, 2.0]}, {"_key": "bed", "dimensions": [0, 0, 0]}]
    )
    slots = _FakeCollection(
        [
            # Keys are Arango-style numeric strings in insertion order; slot ids are the grower's.
            {"_key": "9876", "slot_id": "TENT01_A1", "location_key": "tent", "position": [0, 0]},
            {"_key": "9877", "slot_id": "TENT01_A2", "location_key": "tent", "position": [0, 0]},
            {"_key": "10234", "slot_id": "TENT01_A10", "location_key": "tent", "position": [0, 0]},
            {"_key": "10235", "slot_id": "BED_1", "location_key": "bed", "position": [0, 0]},
        ]
    )
    return _FakeDb(collections={col.LOCATIONS: locations, col.SLOTS: slots}, graph=_bootstrapped_graph())


class TestStructure:
    def test_a_pre_m1_volume_gets_every_collection_edge_index_and_graph_change(self) -> None:
        db = _legacy_volume()

        report = migration.up(db)

        assert [name for name, edge in db.created if not edge] == list(module._DOC_COLLECTIONS)
        assert [name for name, edge in db.created if edge] == list(module._EDGE_COLLECTIONS)
        assert db.graph("").created == list(module._EDGE_COLLECTIONS)
        assert db.graph("").replaced == [col.BELONGS_TO_TENANT, col.CARE_EVENT_FOR, col.HAS_TASK]
        added = {(name, tuple(kw["fields"])) for name, c in db.collections.items() for kw in c.added_indexes}
        assert added == {(name, shape.fields) for name, shape in module._INDEXES}
        structure = report.details["structure"]
        assert structure["graph_present"] is True
        assert structure["graph_edges_widened"][col.BELONGS_TO_TENANT]["from"] == [
            *_PRE_M1_EDGES[col.BELONGS_TO_TENANT][0],
            col.CARE_EVENTS,
            col.IRRIGATION_ZONES,
            col.BED_TEMPLATES,
        ]
        assert structure["graph_edges_widened"][col.HAS_TASK]["to"] == [col.TASKS]
        assert structure["indexes"][0] == {
            "collection": "locations",
            "fields": ["site_key", "bed_status"],
            "unique": False,
            "sparse": False,
        }

    def test_the_widening_keeps_what_the_definition_already_had(self) -> None:
        db = _legacy_volume()
        migration.up(db)
        widened = db.graph("").definitions[col.BELONGS_TO_TENANT]

        assert set(widened["from_vertex_collections"]) == set(
            next(d for d in col.GRAPH_EDGE_DEFINITIONS if d["edge_collection"] == col.BELONGS_TO_TENANT)[
                "from_vertex_collections"
            ]
        )
        assert widened["to_vertex_collections"] == [col.TENANTS]

    def test_garden_objects_never_join_the_tenant_edge(self) -> None:
        db = _legacy_volume()
        migration.up(db)

        assert col.GARDEN_OBJECTS not in db.graph("").definitions[col.BELONGS_TO_TENANT]["from_vertex_collections"]

    def test_indexes_are_built_in_the_background_with_the_declared_uniqueness(self) -> None:
        db = _legacy_volume()
        migration.up(db)
        care_events = db.collection(col.CARE_EVENTS).added_indexes

        assert all(kw["in_background"] is True for c in db.collections.values() for kw in c.added_indexes)
        assert {(tuple(kw["fields"]), kw["unique"], kw["sparse"]) for kw in care_events} == {
            (("tenant_key", "location_key", "performed_at"), False, False),
            (("tenant_key", "performed_at"), False, False),
            (("task_key",), False, False),
            (("tenant_key", "source_ref.collection", "source_ref.key"), True, True),
        }

    def test_a_volume_without_the_graph_gets_collections_and_indexes_but_no_graph_change(self) -> None:
        db = _legacy_volume()
        db._graph = None

        report = migration.up(db)

        assert report.details["structure"]["graph_present"] is False
        assert len(db.created) == len(module._DOC_COLLECTIONS) + len(module._EDGE_COLLECTIONS)
        added = {(name, tuple(kw["fields"])) for name, c in db.collections.items() for kw in c.added_indexes}
        assert added == {(name, shape.fields) for name, shape in module._INDEXES}
        assert report.details["structure"]["graph_edges"] == []

    def test_a_bootstrapped_volume_changes_no_structure(self) -> None:
        db = _FakeDb(
            collections={
                **{name: _FakeCollection() for name in (*module._DOC_COLLECTIONS, *module._EDGE_COLLECTIONS)},
                col.LOCATIONS: _FakeCollection(indexes=_bootstrapped_indexes()),
                col.SLOTS: _FakeCollection(indexes=_bootstrapped_indexes()),
                col.GARDEN_OBJECTS: _FakeCollection(indexes=_bootstrapped_indexes()),
                col.CARE_EVENTS: _FakeCollection(indexes=_bootstrapped_indexes()),
            },
            graph=_bootstrapped_graph(),
        )

        report = migration.up(db)

        assert report.changed == 0
        assert db.created == []
        assert db.graph("").created == [] and db.graph("").replaced == []

    def test_the_selector_accepts_a_hash_typed_index_of_the_same_shape(self) -> None:
        """A pin for the #2034 selector, not a scenario: a pre-June volume cannot carry this index."""
        db = _legacy_volume()
        db.collection(col.LOCATIONS)._indexes.append({"type": "hash", "fields": ["site_key", "bed_status"]})

        migration.up(db)

        assert db.collection(col.LOCATIONS).added_indexes == []

    def test_a_non_unique_twin_does_not_stand_in_for_the_unique_constraint(self) -> None:
        db = _legacy_volume()
        db.collections[col.CARE_EVENTS] = _FakeCollection(
            indexes=[{"type": "persistent", "fields": ["tenant_key", "source_ref.collection", "source_ref.key"]}]
        )

        migration.up(db)

        assert [kw for kw in db.collection(col.CARE_EVENTS).added_indexes if kw["unique"]] == [
            {
                "fields": ["tenant_key", "source_ref.collection", "source_ref.key"],
                "unique": True,
                "sparse": True,
                "in_background": True,
            }
        ]


class TestData:
    def test_locations_with_dimensions_get_a_rect_at_the_origin_and_their_height(self) -> None:
        db = _legacy_volume()

        report = migration.up(db)

        docs = db.collection(col.LOCATIONS).docs
        assert docs["tent"]["geometry"] == {
            "kind": "rect",
            "origin": [0.0, 0.0],
            "width_m": 1.2,
            "length_m": 1.2,
            "rotation_deg": 0.0,
        }
        assert docs["tent"]["height_m"] == 2.0
        assert docs["tent"]["dimensions"] == [1.2, 1.2, 2.0]  # kept until WP 1.5
        assert (docs["bed"]["geometry"]["width_m"], docs["bed"]["geometry"]["length_m"]) == (1.2, 2.4)
        assert "height_m" not in docs["bed"]
        assert "geometry" not in docs["unset"]
        assert "geometry" not in docs["tall"] and docs["tall"]["height_m"] == 2.5
        assert "height_m" not in docs["sky"] and docs["sky"]["geometry"]["width_m"] == 1.0
        assert "geometry" not in docs["text"]
        assert docs["placed"]["geometry"]["kind"] == "circle"
        assert report.details[col.LOCATIONS] == {
            "scanned": 6,
            "updated": 4,
            "geometry_derived": 3,
            "geometry_already_present": 1,
            "height_derived": 2,
            "height_already_present": 1,
            "height_unset": 1,
            "refused": {
                "dimensions_invalid": {"count": 1, "keys": ["text"]},
                "geometry_not_derivable": {"count": 1, "keys": ["tall"]},
                "height_not_derivable": {"count": 1, "keys": ["sky"]},
            },
        }

    def test_slots_get_a_bed_frame_point_from_their_cell_and_the_location_pitch(self) -> None:
        db = _legacy_volume()

        report = migration.up(db)

        slots = db.collection(col.SLOTS).docs
        assert slots["t11"]["geometry"] == {"kind": "point", "origin": [0.3, 0.3]}  # GP-ACC-036
        assert slots["t22"]["geometry"]["origin"] == [0.6, 0.6]
        assert (slots["t11"]["row_index"], slots["t11"]["sequence"]) == (1, 5)
        assert slots["t11"]["geometry_source"] == "migrated_grid"
        assert slots["t11"]["position"] == [1, 1]  # kept until WP 1.5
        assert slots["b01"]["geometry"]["origin"] == [0.5, 0.25]  # pitch_m 0.25 of the bed
        # Ranked over all four bed slots — b00, b01, done, broken — so the two written here are 1 and 2.
        assert (slots["b00"]["sequence"], slots["b01"]["sequence"]) == (1, 2)
        assert "geometry" not in slots["broken"]
        assert {k: slots["done"][k] for k in _MIGRATED_SLOT_FIELDS} == _MIGRATED_SLOT_FIELDS
        assert "geometry" not in slots["orphan"]
        assert report.details[col.SLOTS] == {
            "scanned": 14,
            "updated": 11,
            "point_derived": 11,
            "geometry_already_present": 1,
            "pitch_default_assumed": 9,
            "locations_without_pitch": 1,
            "at_grid_origin": 2,
            "slots_sharing_a_cell": 0,
            "locations_with_collapsed_grid": 0,
            "refused": {
                "position_invalid": {"count": 1, "keys": ["broken"]},
                "location_missing": {"count": 1, "keys": ["orphan"]},
                "point_not_derivable": {"count": 0, "keys": []},
            },
        }

    def test_a_real_volume_stacks_its_slots_on_the_origin_in_slot_id_order_and_says_so(self) -> None:
        """No write path ever set a position: every slot is at (0, 0) and the id decides the order."""
        db = _real_volume()

        report = migration.up(db)

        slots = db.collection(col.SLOTS).docs
        assert all(slots[k]["geometry"] == {"kind": "point", "origin": [0.0, 0.0]} for k in ("9876", "9877", "10234"))
        # Natural order of the slot id (A2 before A10), not the lexicographic key ("10234" < "9876").
        assert [slots[k]["sequence"] for k in ("9876", "9877", "10234")] == [1, 2, 3]
        assert slots["10235"]["sequence"] == 1
        assert report.details[col.SLOTS]["at_grid_origin"] == 4
        assert report.details[col.SLOTS]["slots_sharing_a_cell"] == 3
        assert report.details[col.SLOTS]["locations_with_collapsed_grid"] == 1

    def test_updates_are_batched_per_collection(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(module, "_BATCH_SIZE", 4)
        db = _legacy_volume()

        migration.up(db)

        batches = [(name, len(updates)) for name, updates in db.aql.updates]
        assert batches == [(col.LOCATIONS, 4), (col.SLOTS, 4), (col.SLOTS, 4), (col.SLOTS, 3)]

    def test_the_report_counts_structure_and_documents(self) -> None:
        db = _legacy_volume()

        report = migration.up(db)

        structure = len(module._DOC_COLLECTIONS) + len(module._EDGE_COLLECTIONS) * 2 + len(module._INDEXES) + 3
        assert report.changed == structure + 4 + 11
        assert report.noop is False


class TestIdempotencyAndDryRun:
    def test_a_second_run_changes_nothing(self) -> None:
        db = _legacy_volume()
        migration.up(db)
        before = db.snapshot()
        db.created.clear()
        db.aql.updates.clear()

        report = migration.up(db)

        assert report.changed == 0
        assert report.noop is True
        assert db.created == [] and db.aql.updates == []
        assert db.snapshot() == before
        assert report.details[col.LOCATIONS]["updated"] == 0
        assert report.details[col.LOCATIONS]["refused"]["geometry_not_derivable"] == {"count": 1, "keys": ["tall"]}

    def test_a_run_interrupted_between_two_batches_is_completed_by_the_next_with_the_same_numbers(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The interrupted-run property, end to end: the second run numbers the rest as one run would."""
        monkeypatch.setattr(module, "_BATCH_SIZE", 4)
        undisturbed = _legacy_volume()
        migration.up(undisturbed)
        db = _legacy_volume()
        db.aql.fail_at_update = 3  # locations, the first slot chunk, then the connection drops

        with pytest.raises(_InterruptedError):
            migration.up(db)
        applied_first = {u["_key"] for name, updates in db.aql.updates if name == col.SLOTS for u in updates}
        assert len(applied_first) == 4
        db.aql.fail_at_update = None
        db.created.clear()

        report = migration.up(db)

        assert report.details[col.SLOTS]["updated"] == 7
        assert db.snapshot() == undisturbed.snapshot()
        assert db.created == []  # the structure was already there

    def test_a_dry_run_reports_the_same_plan_and_writes_nothing(self) -> None:
        db = _legacy_volume()
        before = db.snapshot()

        report = migration.up(db, dry_run=True)

        assert (report.changed, report.dry_run) == (0, True)
        assert db.created == [] and db.aql.updates == []
        assert db.graph("").created == [] and db.graph("").replaced == []
        assert db.snapshot() == before
        assert report.details["structure"]["document_collections"] == list(module._DOC_COLLECTIONS)
        assert report.details[col.LOCATIONS]["will_update"] == 4
        assert report.details[col.SLOTS]["will_update"] == 11
        assert report.details[col.SLOTS]["pitch_default_assumed"] == 9

    def test_a_dry_run_after_the_run_is_empty(self) -> None:
        db = _legacy_volume()
        migration.up(db)

        report = migration.up(db, dry_run=True)

        assert report.details[col.LOCATIONS]["will_update"] == 0
        assert report.details[col.SLOTS]["will_update"] == 0
        assert report.details["structure"]["indexes"] == []

    def test_a_stored_null_geometry_is_not_already_present(self) -> None:
        db = _legacy_volume()
        db.collection(col.LOCATIONS).docs["tent"]["geometry"] = None
        db.collection(col.SLOTS).docs["t00"]["geometry"] = None

        migration.up(db)

        assert db.collection(col.LOCATIONS).docs["tent"]["geometry"]["kind"] == "rect"
        assert db.collection(col.SLOTS).docs["t00"]["geometry"]["kind"] == "point"

    def test_a_volume_without_the_legacy_collections_derives_nothing(self) -> None:
        db = _FakeDb(graph=_bootstrapped_graph())

        report = migration.up(db)

        assert report.details[col.LOCATIONS]["updated"] == 0
        assert report.details[col.SLOTS]["updated"] == 0


class TestDeclarations:
    """The migration's constants are literals (M-7); the bootstrap must carry them, and may carry more.

    When a later work package widens an edge or adds an index, this test is where the
    bootstrap side moves — the applied v0093 never changes.
    """

    def test_the_frozen_structure_is_what_the_issue_names(self) -> None:
        assert module._DOC_COLLECTIONS == (
            "garden_objects",
            "care_events",
            "irrigation_zones",
            "garden_plan_audit",
            "bed_templates",
        )
        assert module._EDGE_COLLECTIONS == (
            "has_garden_object",
            "run_planned_at",
            "care_event_at",
            "task_logged_as",
            "has_irrigation_zone",
            "zone_covers",
            "zone_supplied_by",
            "zone_actuated_by",
        )
        assert module._WIDENED_EDGES == {
            "belongs_to_tenant": (("care_events", "irrigation_zones", "bed_templates"), ("tenants",)),
            "care_event_for": (("care_events",), ("plant_instances",)),
            "has_task": (("garden_objects",), ("tasks",)),
        }
        assert [(name, shape.fields, shape.unique, shape.sparse) for name, shape in module._INDEXES] == [
            ("locations", ("site_key", "bed_status"), False, False),
            ("garden_objects", ("site_key", "object_type"), False, False),
            ("slots", ("location_key", "slot_role"), False, False),
            ("care_events", ("tenant_key", "location_key", "performed_at"), False, False),
            ("care_events", ("tenant_key", "performed_at"), False, False),
            ("care_events", ("task_key",), False, False),
            ("care_events", ("tenant_key", "source_ref.collection", "source_ref.key"), True, True),
        ]

    def test_the_bootstrap_carries_everything_the_migration_creates(self) -> None:
        bootstrap = {d["edge_collection"]: d for d in col.GRAPH_EDGE_DEFINITIONS}

        assert set(module._DOC_COLLECTIONS) <= set(col.DOCUMENT_COLLECTIONS)
        assert set(module._EDGE_COLLECTIONS) <= set(col.EDGE_COLLECTIONS)
        for definition in module._NEW_EDGE_DEFINITIONS:
            declared = bootstrap[definition["edge_collection"]]
            assert set(definition["from_vertex_collections"]) <= set(declared["from_vertex_collections"])
            assert set(definition["to_vertex_collections"]) <= set(declared["to_vertex_collections"])
        for edge, (added, targets) in module._WIDENED_EDGES.items():
            assert set(added) <= set(bootstrap[edge]["from_vertex_collections"]), edge
            assert set(targets) <= set(bootstrap[edge]["to_vertex_collections"]), edge
        bootstrap_indexes = {
            (col.LOCATIONS, tuple(col.LOCATION_BED_STATUS_INDEX_FIELDS)),
            (col.GARDEN_OBJECTS, tuple(col.GARDEN_OBJECT_TYPE_INDEX_FIELDS)),
            (col.SLOTS, tuple(col.SLOT_ROLE_INDEX_FIELDS)),
            (col.CARE_EVENTS, tuple(col.CARE_EVENT_LOCATION_HISTORY_INDEX_FIELDS)),
            (col.CARE_EVENTS, tuple(col.CARE_EVENT_TENANT_HISTORY_INDEX_FIELDS)),
            (col.CARE_EVENTS, tuple(col.CARE_EVENT_TASK_INDEX_FIELDS)),
            (col.CARE_EVENTS, tuple(col.CARE_EVENT_SOURCE_REF_INDEX_FIELDS)),
        }
        assert {(name, shape.fields) for name, shape in module._INDEXES} <= bootstrap_indexes

    def test_no_tenant_key_index_on_the_site_anchored_collections(self) -> None:
        for name, shape in module._INDEXES:
            if name in (col.LOCATIONS, col.SLOTS, col.GARDEN_OBJECTS):
                assert "tenant_key" not in shape.fields, (name, shape)

    def test_the_migration_is_irreversible(self) -> None:
        assert migration.version == "0093"
        assert migration.reversible is False
        with pytest.raises(IrreversibleMigrationError):
            migration.down(_FakeDb())
