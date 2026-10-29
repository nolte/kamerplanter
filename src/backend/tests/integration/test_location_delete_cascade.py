"""#2513 WP-4 — the legacy ``delete_location`` removes the bed's subtree and every edge on it, against ArangoDB.

What no double can decide, measured here:

* the location, every location the ``contains`` tree reaches below it and their slots go;
* no edge of any collection the graph lets end at a location or a slot survives on a removed one — ``care_event_at``,
  ``has_task``, ``run_at_location``, ``zone_covers``, ``placed_in`` included; the edge set is derived here from the
  graph definitions, independently of the repository's own write set;
* the care events stay (history, REQ-053 GP-FR-101), and so does the irrigation zone that covered the bed;
* a sibling bed of the same shape is untouched — rows and edges byte-identical (positive control);
* a failure after the first write leaves the database as it was (one stream transaction);
* a location that does not exist returns ``False`` and writes nothing.
"""

from __future__ import annotations

from typing import Any

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.graph_edges import edges_touching
from app.data_access.arango.site_repository import ArangoSiteRepository
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = pytest.mark.usefixtures("arango_db")

TEST_DATABASE = run_database_name("location_delete_cascade")
SITE = "site_a"

_EDGE_COLLECTIONS = tuple(
    dict.fromkeys(edge for name in (col.LOCATIONS, col.SLOTS) for edge, _ in edges_touching(name))
)
_DOCUMENT_COLLECTIONS = (col.SITES, col.LOCATIONS, col.SLOTS, col.CARE_EVENTS, col.IRRIGATION_ZONES)


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    col.ensure_collections(db)
    yield db
    system.delete_database(TEST_DATABASE)


def _edge(db, edge: str, from_id: str, to_id: str) -> None:
    db.collection(edge).insert({"_from": from_id, "_to": to_id})


def _seed_bed(db, bed: str) -> dict[str, list[str]]:
    """A bed with a child bed, a slot and one edge of every shape WP-4 names; returns the ids that go and stay."""
    bed_id, child = f"{col.LOCATIONS}/{bed}", f"child_{bed}"
    child_id, slot_id = f"{col.LOCATIONS}/{child}", f"{col.SLOTS}/slot_{bed}"
    db.collection(col.LOCATIONS).insert({"_key": bed, "site_key": SITE, "name": bed})
    # Nested under the bed and carrying no ``site_key``: reachable only through the ``contains`` tree.
    db.collection(col.LOCATIONS).insert({"_key": child, "parent_location_key": bed, "name": child})
    _edge(db, col.CONTAINS, f"{col.SITES}/{SITE}", bed_id)
    _edge(db, col.CONTAINS, bed_id, child_id)

    db.collection(col.SLOTS).insert({"_key": f"slot_{bed}", "slot_id": "A1", "location_key": bed})
    _edge(db, col.HAS_SLOT, bed_id, slot_id)
    _edge(db, col.PLACED_IN, f"{col.PLANT_INSTANCES}/plant_{bed}", slot_id)

    care = f"care_{bed}"
    db.collection(col.CARE_EVENTS).insert({"_key": care, "site_key": SITE, "location_key": bed, "category": "water"})
    _edge(db, col.CARE_EVENT_AT, f"{col.CARE_EVENTS}/{care}", bed_id)
    _edge(db, col.HAS_TASK, bed_id, f"{col.TASKS}/task_{bed}")
    _edge(db, col.RUN_AT_LOCATION, f"{col.PLANTING_RUNS}/run_{bed}", bed_id)
    _edge(db, col.RUN_AT_LOCATION, f"{col.PLANTING_RUNS}/run_child_{bed}", child_id)

    zone = f"zone_{bed}"
    db.collection(col.IRRIGATION_ZONES).insert({"_key": zone, "tenant_key": "ten_a", "site_key": SITE, "name": zone})
    _edge(db, col.ZONE_COVERS, f"{col.IRRIGATION_ZONES}/{zone}", bed_id)
    return {
        "gone": [bed_id, child_id, slot_id],
        "kept": [f"{col.CARE_EVENTS}/{care}", f"{col.IRRIGATION_ZONES}/{zone}"],
    }


@pytest.fixture
def db(database):
    for name in (*_DOCUMENT_COLLECTIONS, *_EDGE_COLLECTIONS):
        database.collection(name).truncate()
    return database


@pytest.fixture
def seeded(db) -> dict[str, dict[str, list[str]]]:
    db.collection(col.SITES).insert({"_key": SITE, "tenant_key": "ten_a", "name": "Garden", "type": "outdoor"})
    return {"bed": _seed_bed(db, "bed"), "sibling": _seed_bed(db, "sibling")}


def _documents(db) -> dict[str, dict[str, Any]]:
    return {doc["_id"]: doc for name in _DOCUMENT_COLLECTIONS for doc in db.collection(name).all()}


def _edges(db) -> dict[str, dict[str, Any]]:
    return {doc["_id"]: doc for name in _EDGE_COLLECTIONS for doc in db.collection(name).all()}


class TestDeletingALocationCutsTheDerivedEdgeSet:
    def test_the_subtree_and_every_edge_on_it_go_and_nothing_else_changes(self, db, seeded) -> None:
        documents, edges = _documents(db), _edges(db)
        gone = set(seeded["bed"]["gone"])
        touching = [e for e in edges.values() if e["_from"] in gone or e["_to"] in gone]
        # The seed holds what the assertion claims is cut: contains ×2, has_slot, placed_in, care_event_at,
        # has_task, run_at_location ×2, zone_covers.
        assert len(touching) == 9

        assert ArangoSiteRepository(db).delete_location("bed") is True

        assert _documents(db) == {doc_id: doc for doc_id, doc in documents.items() if doc_id not in gone}
        assert _edges(db) == {
            edge_id: edge for edge_id, edge in edges.items() if edge["_from"] not in gone and edge["_to"] not in gone
        }

    def test_the_care_event_and_the_zone_stay(self, db, seeded) -> None:
        ArangoSiteRepository(db).delete_location("bed")

        for doc_id in seeded["bed"]["kept"]:
            assert db.document(doc_id) is not None, doc_id

    def test_the_sibling_bed_is_untouched(self, db, seeded) -> None:
        def owned_by_sibling() -> tuple[dict[str, Any], dict[str, Any]]:
            ids = set(seeded["sibling"]["gone"]) | set(seeded["sibling"]["kept"])
            docs = {doc_id: doc for doc_id, doc in _documents(db).items() if doc_id in ids}
            edges = {e_id: e for e_id, e in _edges(db).items() if e["_from"] in ids or e["_to"] in ids}
            return docs, edges

        before = owned_by_sibling()
        assert len(before[0]) == 5
        assert len(before[1]) == 9

        ArangoSiteRepository(db).delete_location("bed")

        assert owned_by_sibling() == before

    def test_deleting_the_child_leaves_its_parent(self, db, seeded) -> None:
        ArangoSiteRepository(db).delete_location("child_bed")

        assert db.document(f"{col.LOCATIONS}/bed") is not None
        assert db.document(f"{col.LOCATIONS}/child_bed") is None
        assert db.document(f"{col.SLOTS}/slot_bed") is not None
        assert [e["_to"] for e in db.collection(col.CONTAINS).all() if e["_from"] == f"{col.LOCATIONS}/bed"] == []

    def test_a_failure_after_the_first_write_leaves_everything_in_place(self, db, seeded, monkeypatch) -> None:
        documents, edges = _documents(db), _edges(db)
        original = ArangoSiteRepository._remove_rows

        def fail_on_locations(txn: Any, collection: str, ids: Any) -> None:
            original(txn, collection, ids)
            if collection == col.LOCATIONS:
                raise RuntimeError("injected after the removals")

        monkeypatch.setattr(ArangoSiteRepository, "_remove_rows", staticmethod(fail_on_locations))

        with pytest.raises(RuntimeError, match="injected"):
            ArangoSiteRepository(db).delete_location("bed")

        assert _documents(db) == documents
        assert _edges(db) == edges

    def test_a_missing_location_returns_false_and_writes_nothing(self, db, seeded) -> None:
        documents, edges = _documents(db), _edges(db)

        assert ArangoSiteRepository(db).delete_location("bed_missing") is False

        assert _documents(db) == documents
        assert _edges(db) == edges
