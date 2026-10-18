"""REQ-053 WP 3.3 (#2393) — the reconcile of derived ``adjacent_to`` edges and the species hints, against a real store.

The AQL of ``sync_derived_adjacency`` / ``remove_manual_adjacency`` / ``load_slot_species_hints`` is only
proven by a server: a double that returns what the service expects certifies nothing about the statement.
Needs a real ArangoDB (see ``tests/integration/conftest.py``).
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.garden_plan_repository import ArangoGardenPlanRepository
from app.data_access.arango.graph_repository import ArangoGraphRepository
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("adjacency_edges")
pytestmark = pytest.mark.usefixtures("arango_db")

_DOCUMENTS = [col.SITES, col.LOCATIONS, col.SLOTS, col.SPECIES, col.PLANT_INSTANCES, col.PLANTING_RUNS]
_EDGES = [col.ADJACENT_TO, col.RUN_PLANNED_AT]


@pytest.fixture(scope="module")
def _database():
    client = ArangoClient(hosts=ARANGO_URL)
    try:
        system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
        if system.has_database(TEST_DATABASE):
            system.delete_database(TEST_DATABASE)
        system.create_database(TEST_DATABASE)
        database = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
        for name in _DOCUMENTS:
            database.create_collection(name)
        for name in _EDGES:
            database.create_collection(name, edge=True)
        yield database
        system.delete_database(TEST_DATABASE)
    finally:
        client.close()


@pytest.fixture
def db(_database):
    for name in (*_DOCUMENTS, *_EDGES):
        _database.collection(name).truncate()
    return _database


@pytest.fixture
def graph(db):
    return ArangoGraphRepository(db)


def _slot(key: str) -> str:
    return f"{col.SLOTS}/{key}"


def _edges(db) -> dict[tuple[str, str], dict]:
    return {(e["_from"], e["_to"]): e for e in db.collection(col.ADJACENT_TO).all()}


def test_sync_creates_both_directions_with_distance_and_source(db, graph) -> None:
    result = graph.sync_derived_adjacency(["a", "b", "c"], [("a", "b", 30.0)])

    edges = _edges(db)
    assert set(edges) == {(_slot("a"), _slot("b")), (_slot("b"), _slot("a"))}
    assert all(e["distance_cm"] == 30.0 and e["source"] == "derived" for e in edges.values())
    assert (result.created, result.updated, result.removed, result.kept) == (2, 0, 0, 0)


def test_sync_is_idempotent(db, graph) -> None:
    graph.sync_derived_adjacency(["a", "b"], [("a", "b", 30.0)])
    before = {key: edge["_rev"] for key, edge in _edges(db).items()}

    result = graph.sync_derived_adjacency(["a", "b"], [("a", "b", 30.0)])

    assert (result.created, result.updated, result.removed, result.kept) == (0, 0, 0, 2)
    assert {key: edge["_rev"] for key, edge in _edges(db).items()} == before


def test_sync_removes_pairs_that_left_and_updates_a_changed_distance(db, graph) -> None:
    graph.sync_derived_adjacency(["a", "b", "c"], [("a", "b", 30.0), ("b", "c", 30.0)])

    result = graph.sync_derived_adjacency(["a", "b", "c"], [("a", "b", 36.5)])

    edges = _edges(db)
    assert set(edges) == {(_slot("a"), _slot("b")), (_slot("b"), _slot("a"))}
    assert {e["distance_cm"] for e in edges.values()} == {36.5}
    assert (result.removed, result.updated) == (2, 2)


def test_a_manual_edge_survives_every_sync_and_blocks_a_derived_twin(db, graph) -> None:
    graph.set_adjacent_slots("a", "b", distance_cm=99.0, source="manual")

    graph.sync_derived_adjacency(["a", "b", "c"], [("a", "b", 30.0), ("b", "c", 30.0)])
    graph.sync_derived_adjacency(["a", "b", "c"], [])

    edges = _edges(db)
    manual = {key for key, edge in edges.items() if edge["source"] == "manual"}
    assert manual == {(_slot("a"), _slot("b")), (_slot("b"), _slot("a"))}
    assert {edges[key]["distance_cm"] for key in manual} == {99.0}
    assert set(edges) == manual


def test_a_legacy_edge_without_a_source_is_not_managed(db, graph) -> None:
    for a, b in (("a", "b"), ("b", "a")):
        db.collection(col.ADJACENT_TO).insert({"_from": _slot(a), "_to": _slot(b)})

    graph.sync_derived_adjacency(["a", "b"], [("a", "b", 30.0)])
    graph.sync_derived_adjacency(["a", "b"], [])

    edges = _edges(db)
    assert set(edges) == {(_slot("a"), _slot("b")), (_slot("b"), _slot("a"))}
    assert all("source" not in e for e in edges.values())


def test_sync_leaves_edges_of_slots_outside_the_bed_alone(db, graph) -> None:
    graph.set_adjacent_slots("a", "z", distance_cm=40.0)

    graph.sync_derived_adjacency(["a", "b"], [])

    assert {(_slot("a"), _slot("z")), (_slot("z"), _slot("a"))} <= set(_edges(db))


def test_sync_collapses_a_duplicated_direction(db, graph) -> None:
    for _ in range(2):
        db.collection(col.ADJACENT_TO).insert(
            {"_from": _slot("a"), "_to": _slot("b"), "source": "derived", "distance_cm": 30.0}
        )
    db.collection(col.ADJACENT_TO).insert(
        {"_from": _slot("b"), "_to": _slot("a"), "source": "derived", "distance_cm": 30.0}
    )

    graph.sync_derived_adjacency(["a", "b"], [("a", "b", 30.0)])

    assert len(_edges(db)) == 2
    assert db.collection(col.ADJACENT_TO).count() == 2


def test_remove_manual_adjacency_deletes_only_the_manual_pair(db, graph) -> None:
    graph.set_adjacent_slots("a", "b", source="manual")
    graph.set_adjacent_slots("b", "c", distance_cm=30.0)

    assert graph.remove_manual_adjacency("b", "a") == 2
    assert graph.remove_manual_adjacency("b", "c") == 0

    assert set(_edges(db)) == {(_slot("b"), _slot("c")), (_slot("c"), _slot("b"))}


def test_an_empty_slot_list_touches_nothing(db, graph) -> None:
    graph.set_adjacent_slots("a", "b")

    graph.sync_derived_adjacency([], [])

    assert len(_edges(db)) == 2


def test_species_hints_come_from_plants_and_live_reservations_of_the_tenants_bed(db) -> None:
    db.collection(col.SITES).insert({"_key": "s1", "tenant_key": "t1"})
    db.collection(col.SITES).insert({"_key": "s2", "tenant_key": "t2"})
    db.collection(col.LOCATIONS).insert({"_key": "bed", "site_key": "s1"})
    db.collection(col.SLOTS).insert({"_key": "p1", "location_key": "bed"})
    db.collection(col.SLOTS).insert({"_key": "p2", "location_key": "bed"})
    db.collection(col.SLOTS).insert({"_key": "gone", "location_key": "bed", "archived_at": "2026-01-01T00:00:00+00:00"})
    db.collection(col.SPECIES).insert(
        {
            "_key": "tomato",
            "spacing_cm": "50--60",
            "row_spacing_cm": "80",
            "mature_width_cm": "60",
            "growth_habit": "herb",
        }
    )
    db.collection(col.SPECIES).insert({"_key": "apple", "mature_width_cm": "400", "growth_habit": "tree"})
    db.collection(col.PLANT_INSTANCES).insert(
        {"_key": "pl1", "tenant_key": "t1", "slot_key": "p1", "species_key": "tomato", "removed_on": None}
    )
    db.collection(col.PLANT_INSTANCES).insert(
        {"_key": "pl2", "tenant_key": "t1", "slot_key": "p1", "species_key": "apple", "removed_on": "2026-05-01"}
    )
    db.collection(col.PLANTING_RUNS).insert({"_key": "live", "status": "planned"})
    db.collection(col.PLANTING_RUNS).insert({"_key": "done", "status": "completed"})
    db.collection(col.RUN_PLANNED_AT).insert(
        {"_from": f"{col.PLANTING_RUNS}/live", "_to": _slot("p2"), "planned_species_key": "apple"}
    )
    db.collection(col.RUN_PLANNED_AT).insert(
        {"_from": f"{col.PLANTING_RUNS}/done", "_to": _slot("p2"), "planned_species_key": "tomato"}
    )
    db.collection(col.RUN_PLANNED_AT).insert(
        {"_from": f"{col.PLANTING_RUNS}/live", "_to": _slot("gone"), "planned_species_key": "apple"}
    )
    repo = ArangoGardenPlanRepository(db)

    hints = repo.load_slot_species_hints("bed", tenant_key="t1")

    assert sorted((h.slot_key, h.species_key) for h in hints) == [("p1", "tomato"), ("p2", "apple")]
    tomato = next(h for h in hints if h.species_key == "tomato")
    assert (tomato.spacing_cm, tomato.row_spacing_cm, tomato.mature_width_cm) == ("50--60", "80", "60")
    assert repo.load_slot_species_hints("bed", tenant_key="t2") == []
    assert repo.load_slot_species_hints("missing", tenant_key="t1") == []
