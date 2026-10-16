"""#2323 (REQ-053 M1, GP-ACC-035/036 data side) — v0093 measured on a real ArangoDB.

* on a volume the bootstrap shaped, the structural half is a no-op and the data half
  derives the geometries; the AQL scans and the batched ``UPDATE`` are the real ones;
* on a pre-M1 volume (the collections and the graph as they were before this version)
  the migration creates and widens what the bootstrap would, and a subsequent
  ``ensure_collections`` adds nothing on top — the two paths converge on one shape;
* a second run changes no document (``_rev`` stays), a dry run writes nothing.

Locally it needs a database::

    docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_v0093_garden_plan_geometry.py -v
"""

from __future__ import annotations

from typing import Any

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.collections import ensure_collections
from app.migrations.support.legacy_indexes import indexes_on
from app.migrations.versions.v0093_garden_plan_geometry import migration
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the migration's scans and batched UPDATE are AQL over a real server"),
]

_DB_NAME = run_database_name("v0093_garden_plan_geometry")

_NEW_DOCUMENTS = {col.GARDEN_OBJECTS, col.CARE_EVENTS, col.IRRIGATION_ZONES, col.GARDEN_PLAN_AUDIT, col.BED_TEMPLATES}
_NEW_EDGES = set(col.GARDEN_PLAN_EDGE_COLLECTIONS)
_WIDENED = {
    col.BELONGS_TO_TENANT: {col.CARE_EVENTS, col.IRRIGATION_ZONES, col.BED_TEMPLATES},
    col.CARE_EVENT_FOR: {col.CARE_EVENTS},
    col.HAS_TASK: {col.GARDEN_OBJECTS},
}


@pytest.fixture
def fresh_db():  # type: ignore[no-untyped-def]
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)
    system.create_database(_DB_NAME)
    yield client.db(_DB_NAME, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    system.delete_database(_DB_NAME)


@pytest.fixture
def db(fresh_db):  # type: ignore[no-untyped-def]
    ensure_collections(fresh_db)
    return fresh_db


def _pre_m1_shape(database) -> None:  # type: ignore[no-untyped-def]
    """The collections and the graph as every volume had them before v0093."""
    for name in col.DOCUMENT_COLLECTIONS:
        if name not in _NEW_DOCUMENTS:
            database.create_collection(name)
    for name in col.EDGE_COLLECTIONS:
        if name not in _NEW_EDGES:
            database.create_collection(name, edge=True)
    definitions = []
    for definition in col.GRAPH_EDGE_DEFINITIONS:
        edge = definition["edge_collection"]
        if edge in _NEW_EDGES:
            continue
        narrowed = dict(definition)
        narrowed["from_vertex_collections"] = [
            name for name in definition["from_vertex_collections"] if name not in _WIDENED.get(edge, set())
        ]
        definitions.append(narrowed)
    database.create_graph(col.GRAPH_NAME, edge_definitions=definitions)


def _seed_legacy_rows(database) -> None:  # type: ignore[no-untyped-def]
    database.collection(col.LOCATIONS).insert_many(
        [
            {"_key": "tent", "site_key": "s", "area_m2": 1.44, "dimensions": [1.2, 1.2, 2.0]},
            {"_key": "bed", "site_key": "s", "area_m2": 2.88, "dimensions": [2.4, 1.2, 0.0], "pitch_m": 0.25},
            {"_key": "unset", "site_key": "s", "area_m2": 0.0, "dimensions": [0.0, 0.0, 0.0]},
        ]
    )
    database.collection(col.SLOTS).insert_many(
        [
            {
                "_key": f"t{row}{column}",
                "slot_id": f"T_{row}{column}",
                "location_key": "tent",
                "position": [row, column],
            }
            for row in range(3)
            for column in range(3)
        ]
        + [
            {"_key": "b12", "slot_id": "BED_12", "location_key": "bed", "position": [1, 2]},
            # The real-volume shape: no position ever written, every slot of the bed on (0, 0).
            {"_key": "b_a10", "slot_id": "BED_A10", "location_key": "bed", "position": [0, 0]},
            {"_key": "b_a2", "slot_id": "BED_A2", "location_key": "bed", "position": [0, 0]},
        ]
    )


def _definitions(database) -> dict[str, dict[str, Any]]:  # type: ignore[no-untyped-def]
    return {d["edge_collection"]: d for d in database.graph(col.GRAPH_NAME).edge_definitions()}


def _index_count(database) -> dict[str, int]:  # type: ignore[no-untyped-def]
    return {name: len(database.collection(name).indexes()) for name in (col.LOCATIONS, col.SLOTS, *_NEW_DOCUMENTS)}


_M1_INDEXES = (
    (col.LOCATIONS, col.LOCATION_BED_STATUS_INDEX_FIELDS),
    (col.GARDEN_OBJECTS, col.GARDEN_OBJECT_TYPE_INDEX_FIELDS),
    (col.SLOTS, col.SLOT_ROLE_INDEX_FIELDS),
    (col.CARE_EVENTS, col.CARE_EVENT_LOCATION_HISTORY_INDEX_FIELDS),
    (col.CARE_EVENTS, col.CARE_EVENT_TENANT_HISTORY_INDEX_FIELDS),
    (col.CARE_EVENTS, col.CARE_EVENT_TASK_INDEX_FIELDS),
    (col.CARE_EVENTS, col.CARE_EVENT_SOURCE_REF_INDEX_FIELDS),
)


def _m1_index_counts(database) -> dict[tuple[str, tuple[str, ...]], int]:  # type: ignore[no-untyped-def]
    """How many persistent-family indexes each M1 declaration has on the volume (1 = converged)."""
    return {(name, tuple(fields)): len(indexes_on(database.collection(name), fields)) for name, fields in _M1_INDEXES}


def test_a_bootstrapped_volume_keeps_its_structure_and_gets_the_geometries(db) -> None:  # type: ignore[no-untyped-def]
    _seed_legacy_rows(db)
    indexes_before = _index_count(db)

    report = migration.up(db)

    structure = report.details["structure"]
    assert (structure["document_collections"], structure["edge_collections"], structure["indexes"]) == ([], [], [])
    assert (structure["graph_edges"], structure["graph_edges_widened"]) == ([], {})
    assert _index_count(db) == indexes_before

    tent = db.collection(col.LOCATIONS).get("tent")
    assert tent["geometry"] == {"kind": "rect", "origin": [0, 0], "width_m": 1.2, "length_m": 1.2, "rotation_deg": 0}
    assert tent["height_m"] == 2.0
    assert tent["dimensions"] == [1.2, 1.2, 2.0]
    bed = db.collection(col.LOCATIONS).get("bed")
    assert (bed["geometry"]["width_m"], bed["geometry"]["length_m"]) == (1.2, 2.4)
    assert "height_m" not in bed
    assert "geometry" not in db.collection(col.LOCATIONS).get("unset")  # GP-ACC-035: stays, geometry = null

    middle = db.collection(col.SLOTS).get("t11")  # GP-ACC-036: the slot the criterion drags by 10 cm
    assert middle["geometry"] == {"kind": "point", "origin": [0.3, 0.3]}
    assert (middle["row_index"], middle["sequence"], middle["geometry_source"]) == (1, 5, "migrated_grid")
    assert middle["position"] == [1, 1]
    assert db.collection(col.SLOTS).get("b12")["geometry"]["origin"] == [0.5, 0.25]
    # Stacked on the origin, numbered by the slot id in natural order (A2 before A10), b12 after both.
    assert db.collection(col.SLOTS).get("b_a2")["geometry"] == {"kind": "point", "origin": [0, 0]}
    assert [db.collection(col.SLOTS).get(k)["sequence"] for k in ("b_a2", "b_a10", "b12")] == [1, 2, 3]
    assert report.details[col.LOCATIONS]["updated"] == 2
    assert report.details[col.SLOTS] == {
        "scanned": 12,
        "updated": 12,
        "point_derived": 12,
        "geometry_already_present": 0,
        "pitch_default_assumed": 9,
        "locations_without_pitch": 1,
        "at_grid_origin": 3,
        "slots_sharing_a_cell": 2,
        "locations_with_collapsed_grid": 1,
        "refused": {
            "position_invalid": {"count": 0, "keys": []},
            "location_missing": {"count": 0, "keys": []},
            "point_not_derivable": {"count": 0, "keys": []},
        },
    }
    assert report.changed == 14


def test_a_pre_m1_volume_converges_on_the_bootstrap_shape(fresh_db) -> None:  # type: ignore[no-untyped-def]
    _pre_m1_shape(fresh_db)
    assert not fresh_db.has_collection(col.CARE_EVENTS)
    assert col.CARE_EVENTS not in _definitions(fresh_db)[col.BELONGS_TO_TENANT]["from_vertex_collections"]

    report = migration.up(fresh_db)

    assert all(fresh_db.has_collection(name) for name in _NEW_DOCUMENTS | _NEW_EDGES)
    definitions = _definitions(fresh_db)
    bootstrap = {d["edge_collection"]: d for d in col.GRAPH_EDGE_DEFINITIONS}
    for edge in _NEW_EDGES | set(_WIDENED):
        assert set(definitions[edge]["from_vertex_collections"]) == set(bootstrap[edge]["from_vertex_collections"])
        assert set(definitions[edge]["to_vertex_collections"]) == set(bootstrap[edge]["to_vertex_collections"])
    assert col.GARDEN_OBJECTS not in definitions[col.BELONGS_TO_TENANT]["from_vertex_collections"]
    source_ref = indexes_on(fresh_db.collection(col.CARE_EVENTS), col.CARE_EVENT_SOURCE_REF_INDEX_FIELDS)
    assert [(idx["unique"], idx["sparse"]) for idx in source_ref] == [(True, True)]
    assert indexes_on(fresh_db.collection(col.LOCATIONS), col.LOCATION_BED_STATUS_INDEX_FIELDS)
    assert indexes_on(fresh_db.collection(col.SLOTS), col.SLOT_ROLE_INDEX_FIELDS)
    assert report.details["structure"]["graph_edges"] == list(col.GARDEN_PLAN_EDGE_COLLECTIONS)
    assert set(report.details["structure"]["graph_edges_widened"]) == set(_WIDENED)

    # The bootstrap finds nothing left to do on M1's own shapes: exactly one index per
    # declaration (a differently-flagged twin would be a second one), the same
    # definitions. The pre-M1 fixture carries no other bootstrap index, so the whole
    # count is not compared — ensure_collections legitimately adds those.
    definitions_before = _definitions(fresh_db)
    ensure_collections(fresh_db)
    assert _definitions(fresh_db) == definitions_before
    assert _m1_index_counts(fresh_db) == {shape: 1 for shape in _m1_index_counts(fresh_db)}
    assert len(_m1_index_counts(fresh_db)) == 7
    assert migration.up(fresh_db).changed == 0


def test_a_second_run_changes_no_document_and_a_dry_run_writes_nothing(db) -> None:  # type: ignore[no-untyped-def]
    _seed_legacy_rows(db)
    untouched = {doc["_key"]: doc["_rev"] for doc in db.collection(col.SLOTS).all()}

    dry = migration.up(db, dry_run=True)

    assert (dry.changed, dry.dry_run) == (0, True)
    assert dry.details[col.SLOTS]["will_update"] == 12
    assert {doc["_key"]: doc["_rev"] for doc in db.collection(col.SLOTS).all()} == untouched
    assert "geometry" not in db.collection(col.LOCATIONS).get("tent")

    migration.up(db)
    revisions = {doc["_key"]: doc["_rev"] for doc in db.collection(col.SLOTS).all()}
    location_revisions = {doc["_key"]: doc["_rev"] for doc in db.collection(col.LOCATIONS).all()}

    again = migration.up(db)

    assert again.changed == 0 and again.noop is True
    assert {doc["_key"]: doc["_rev"] for doc in db.collection(col.SLOTS).all()} == revisions
    assert {doc["_key"]: doc["_rev"] for doc in db.collection(col.LOCATIONS).all()} == location_revisions
    assert again.details[col.SLOTS]["geometry_already_present"] == 12
