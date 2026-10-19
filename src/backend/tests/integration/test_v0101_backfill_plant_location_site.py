"""#2499 — v0101 measured on a real ArangoDB (prod point P-2): the AQL scan and the batched UPDATE.

Plants written by ``create_plants`` before the WP 3.8 fix carry ``slot_key`` but no ``location_key`` /
``site_key``. The fixture inserts that stored shape directly (the production writer now stamps both).

Locally it needs a database::

    docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_v0101_backfill_plant_location_site.py -v
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.collections import ensure_collections
from app.migrations.versions.v0101_backfill_plant_location_site import migration
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the migration's scan and batched UPDATE are AQL over a real server"),
]

_DB_NAME = run_database_name("v0101_backfill_plant_location_site")


@pytest.fixture
def db():  # type: ignore[no-untyped-def]
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)
    system.create_database(_DB_NAME)
    database = client.db(_DB_NAME, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    ensure_collections(database)
    yield database
    system.delete_database(_DB_NAME)


def _seed(db) -> None:  # type: ignore[no-untyped-def]
    db.collection(col.LOCATIONS).insert_many(
        [
            {"_key": "L1", "tenant_key": "t1", "site_key": "S1"},
            {"_key": "L2", "tenant_key": "t2", "site_key": "S2"},
        ]
    )
    db.collection(col.SLOTS).insert_many([{"_key": "s1", "location_key": "L1"}, {"_key": "s2", "location_key": "L2"}])
    plant = {"tenant_key": "t1", "location_key": None, "site_key": None}
    db.collection(col.PLANT_INSTANCES).insert_many(
        [
            {**plant, "_key": "ok", "slot_key": "s1"},
            {**plant, "_key": "keep", "slot_key": "s1", "location_key": "OTHER"},
            {**plant, "_key": "noslot", "slot_key": None},
            {**plant, "_key": "foreign", "slot_key": "s2"},
            {**plant, "_key": "done", "slot_key": "s1", "location_key": "L1", "site_key": "S1"},
        ]
    )


def _plant(db, key: str) -> dict:  # type: ignore[no-untyped-def]
    return db.collection(col.PLANT_INSTANCES).get(key)


def test_dry_run_reports_and_writes_nothing(db) -> None:  # type: ignore[no-untyped-def]
    _seed(db)
    revs = {d["_key"]: d["_rev"] for d in db.collection(col.PLANT_INSTANCES).all()}

    report = migration.up(db, dry_run=True)

    assert {d["_key"]: d["_rev"] for d in db.collection(col.PLANT_INSTANCES).all()} == revs
    assert report.details["will_update"] == 2
    assert report.details["unresolved"]["no_slot"]["listed"] == ["noslot"]
    assert report.details["unresolved"]["cross_tenant"]["listed"] == ["foreign"]


def test_apply_derives_both_keys_and_never_overwrites(db) -> None:  # type: ignore[no-untyped-def]
    _seed(db)

    report = migration.up(db)

    assert report.changed == 2
    assert (_plant(db, "ok")["location_key"], _plant(db, "ok")["site_key"]) == ("L1", "S1")
    assert (_plant(db, "keep")["location_key"], _plant(db, "keep")["site_key"]) == ("OTHER", "S1")
    assert _plant(db, "noslot")["location_key"] is None
    assert _plant(db, "foreign")["site_key"] is None


def test_a_second_run_writes_nothing_more(db) -> None:  # type: ignore[no-untyped-def]
    _seed(db)
    migration.up(db)
    revs = {d["_key"]: d["_rev"] for d in db.collection(col.PLANT_INSTANCES).all()}

    migration.up(db)

    assert {d["_key"]: d["_rev"] for d in db.collection(col.PLANT_INSTANCES).all()} == revs
