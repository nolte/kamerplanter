"""#1878 — ``update_slot`` keeps the ``has_slot`` edge on the slot's ``location_key``.

``SiteRepository.update_slot`` used to rewrite the slot document only. A slot
re-parented through ``PUT /t/{slug}/slots/{key}`` therefore carried the new
``location_key`` while ``has_slot`` (location -> slot) still hung off the old
location, and ``get_slots_by_location`` (which walks the edge) and
``resolve_owned_slot`` (which reads the field) answered differently for the same
slot. Only a real server shows both reads, so the repository runs against one.
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.site_repository import ArangoSiteRepository
from app.domain.models.site import Slot
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("slot_update_edge")
pytestmark = pytest.mark.usefixtures("arango_db")

_DOCS = [col.SITES, col.LOCATIONS, col.SLOTS]
_EDGES = [col.HAS_SLOT]


@pytest.fixture(scope="module")
def _database():
    client = ArangoClient(hosts=ARANGO_URL)
    try:
        system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
        if system.has_database(TEST_DATABASE):
            system.delete_database(TEST_DATABASE)
        system.create_database(TEST_DATABASE)
        database = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
        for name in _DOCS:
            database.create_collection(name)
        for name in _EDGES:
            database.create_collection(name, edge=True)
        yield database
        system.delete_database(TEST_DATABASE)
    finally:
        client.close()


@pytest.fixture
def db(_database):
    for name in (*_DOCS, *_EDGES):
        _database.collection(name).truncate()
    return _database


@pytest.fixture
def repo(db):
    return ArangoSiteRepository(db)


def _seed(db) -> None:
    db.collection(col.SITES).insert_many([{"_key": "site-1", "tenant_key": "A"}, {"_key": "site-2", "tenant_key": "B"}])
    for key in ("loc-1", "loc-2"):
        db.collection(col.LOCATIONS).insert({"_key": key, "name": key, "site_key": "site-1"})
    db.collection(col.LOCATIONS).insert({"_key": "loc-foreign", "name": "foreign", "site_key": "site-2"})
    db.collection(col.SLOTS).insert({"_key": "slot-1", "slot_id": "TENT_A1", "location_key": "loc-1"})
    db.collection(col.HAS_SLOT).insert({"_from": f"{col.LOCATIONS}/loc-1", "_to": f"{col.SLOTS}/slot-1"})


def _parents(db) -> list[str]:
    return sorted(e["_from"] for e in db.aql.execute("FOR e IN has_slot FILTER e._to == 'slots/slot-1' RETURN e"))


def test_changing_the_location_moves_the_edge_with_the_field(db, repo) -> None:
    _seed(db)

    updated = repo.update_slot("slot-1", Slot(slot_id="TENT_A1", location_key="loc-2"))

    assert updated.location_key == "loc-2"
    assert _parents(db) == [f"{col.LOCATIONS}/loc-2"]


def test_an_update_that_keeps_the_location_leaves_exactly_one_edge(db, repo) -> None:
    _seed(db)

    repo.update_slot("slot-1", Slot(slot_id="TENT_A1", location_key="loc-1"))

    assert _parents(db) == [f"{col.LOCATIONS}/loc-1"]


def test_the_edge_never_follows_the_field_into_another_tenant(db, repo) -> None:
    """An internal caller hands back the slot it read; on a pre-#1871 row that field is foreign."""
    _seed(db)

    repo.update_slot("slot-1", Slot(slot_id="TENT_A1", location_key="loc-foreign"))

    assert _parents(db) == [f"{col.LOCATIONS}/loc-1"]


def test_a_missing_site_leaves_the_edge_where_it_is(db, repo) -> None:
    _seed(db)
    db.collection(col.LOCATIONS).insert({"_key": "loc-nosite", "name": "x", "site_key": "gone"})

    repo.update_slot("slot-1", Slot(slot_id="TENT_A1", location_key="loc-nosite"))

    assert _parents(db) == [f"{col.LOCATIONS}/loc-1"]


def test_a_slot_without_an_edge_gets_one(db, repo) -> None:
    _seed(db)
    db.collection(col.HAS_SLOT).truncate()

    repo.update_slot("slot-1", Slot(slot_id="TENT_A1", location_key="loc-2"))

    assert _parents(db) == [f"{col.LOCATIONS}/loc-2"]


def test_duplicate_edges_collapse_onto_the_field(db, repo) -> None:
    _seed(db)
    db.collection(col.HAS_SLOT).insert({"_from": f"{col.LOCATIONS}/loc-2", "_to": f"{col.SLOTS}/slot-1"})

    repo.update_slot("slot-1", Slot(slot_id="TENT_A1", location_key="loc-2"))

    assert _parents(db) == [f"{col.LOCATIONS}/loc-2"]
