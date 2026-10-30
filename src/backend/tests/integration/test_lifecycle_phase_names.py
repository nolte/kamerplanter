"""#2489 W-1 — ``ArangoLifecycleRepository.get_phase_names`` measured on the server.

The print reads the names of every distinct phase of a site in one statement instead of one growth-phase read per
key. ``DOCUMENT`` must answer the growth phases among the keys and drop the rest: an absent key, a phase-sequence
entry key, a key that is no valid document key, a phase without a name.
Needs a real ArangoDB (see ``tests/integration/conftest.py``).
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.lifecycle_repository import ArangoLifecycleRepository
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("lifecycle_phase_names")
pytestmark = pytest.mark.usefixtures("arango_db")


@pytest.fixture(scope="module")
def db():
    client = ArangoClient(hosts=ARANGO_URL)
    try:
        system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
        if system.has_database(TEST_DATABASE):
            system.delete_database(TEST_DATABASE)
        system.create_database(TEST_DATABASE)
        database = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
        for name in (col.LIFECYCLE_CONFIGS, col.GROWTH_PHASES, col.PHASE_SEQUENCE_ENTRIES):
            database.create_collection(name)
        database.collection(col.GROWTH_PHASES).insert_many(
            [
                {"_key": "ph-flower", "name": "flowering", "display_name": "Flowering"},
                {"_key": "ph-veg", "name": "vegetative"},
                {"_key": "ph-nameless", "name": ""},
            ]
        )
        database.collection(col.PHASE_SEQUENCE_ENTRIES).insert({"_key": "entry-1", "phase_definition_key": "d"})
        yield database
        system.delete_database(TEST_DATABASE)
    finally:
        client.close()


def test_the_growth_phases_among_the_keys_and_nothing_else(db) -> None:
    names = ArangoLifecycleRepository(db).get_phase_names(
        ["ph-flower", "ph-veg", "ph-nameless", "entry-1", "absent", "not a/valid key", "ph-veg"]
    )

    assert names == {"ph-flower": "flowering", "ph-veg": "vegetative"}


def test_four_hundred_keys_in_one_read(db) -> None:
    keys = [f"ph-{index:04d}" for index in range(400)]

    names = ArangoLifecycleRepository(db).get_phase_names([*keys, "ph-flower"])

    assert names == {"ph-flower": "flowering"}
