"""#2107 — v0087 removes the never-written ``tenant_key`` from locations and slots, against a real ArangoDB.

The rows carry the shapes a volume holds: ``tenant_key: ""`` (the model default
every write stored), a v0004 stamp (the site's tenant), and a row already without
the attribute. Only the attribute goes; everything else, and the sites, stay.
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.migrations.versions.v0087_drop_location_slot_tenant_key import migration
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("v0087_location_slot_tenant_key")

pytestmark = pytest.mark.usefixtures("arango_db")


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    db.create_collection(col.SITES).insert({"_key": "s1", "tenant_key": "t1", "name": "Site"})
    locations = db.create_collection(col.LOCATIONS)
    locations.insert({"_key": "default", "tenant_key": "", "name": "Tent", "site_key": "s1"})
    locations.insert({"_key": "stamped", "tenant_key": "t1", "name": "Bed", "site_key": "s1"})
    locations.insert({"_key": "clean", "name": "Shelf", "site_key": "s1"})
    db.create_collection(col.SLOTS).insert(
        {"_key": "a1", "tenant_key": "", "slot_id": "TENT_A1", "location_key": "default"}
    )
    yield db
    system.delete_database(TEST_DATABASE)


def test_v0087_drops_only_the_attribute_and_is_idempotent(database) -> None:
    locations, slots = database.collection(col.LOCATIONS), database.collection(col.SLOTS)
    clean_before = locations.get("clean")

    dry = migration.up(database, dry_run=True)
    assert (dry.scanned, dry.changed) == (3, 0)
    assert locations.get("stamped")["tenant_key"] == "t1"

    first = migration.up(database)
    second = migration.up(database)

    assert (first.scanned, first.changed) == (3, 3)
    assert (second.scanned, second.changed) == (0, 0)
    for key in ("default", "stamped", "clean"):
        assert "tenant_key" not in locations.get(key)
    assert locations.get("stamped")["name"] == "Bed" and locations.get("stamped")["site_key"] == "s1"
    assert locations.get("clean") == clean_before
    assert "tenant_key" not in slots.get("a1") and slots.get("a1")["location_key"] == "default"
    assert database.collection(col.SITES).get("s1")["tenant_key"] == "t1"
