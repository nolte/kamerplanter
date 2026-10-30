"""#2499 — v0100 measured on a real ArangoDB (prod point P-2): the AQL scan and the batched UPDATE.

Plants written by ``create_plants`` before the WP 3.8 fix carry ``slot_key`` but no ``location_key`` /
``site_key``. The fixture inserts that stored shape directly (the production writer now stamps both).

Locally it needs a database::

    docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_v0100_backfill_plant_location_site.py -v
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.collections import ensure_collections
from app.migrations.versions.v0100_backfill_plant_location_site import migration
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the migration's scan and batched UPDATE are AQL over a real server"),
]

_DB_NAME = run_database_name("v0100_backfill_plant_location_site")


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


def _insert(collection, docs: list[dict]) -> None:  # type: ignore[no-untyped-def]
    """``insert_many`` reports a refused document in its result instead of raising: a seed must not vanish."""
    refused = [r for r in collection.insert_many(docs) if isinstance(r, Exception)]
    assert not refused, refused


def _seed(db) -> None:  # type: ignore[no-untyped-def]
    _insert(
        db.collection(col.LOCATIONS),
        [
            {"_key": "L1", "site_key": "S1"},
            {"_key": "L2", "site_key": "S2"},
            {"_key": "L4", "site_key": "S4"},
            {"_key": "L5"},  # names no site
            {"_key": "L6", "site_key": "S_gone"},  # names a site that does not exist
            {"_key": "L7", "site_key": "S7"},  # anchored by a legacy site
        ],
    )
    _insert(
        db.collection(col.SITES),
        [
            {"_key": "S1", "tenant_key": "t1"},
            {"_key": "S2", "tenant_key": "t2"},
            {"_key": "S4", "tenant_key": "t1"},
            {"_key": "S7"},  # legacy: no tenant_key
        ],
    )
    slots = db.collection(col.SLOTS)
    # (location_key, slot_id) is unique: every stored slot carries its own slot_id
    _insert(
        slots,
        [
            {**row, "slot_id": f"SLOT-{row['_key']}"}
            for row in [
                {"_key": "s1", "location_key": "L1"},
                {"_key": "s2", "location_key": "L2"},
                {"_key": "s3"},  # no location
                {"_key": "s5", "location_key": "L5"},
                {"_key": "s6", "location_key": "L6"},
                {"_key": "s7", "location_key": "L7"},
                {"_key": "s9", "location_key": "L1"},
            ]
        ],
    )
    slots.delete("s9")  # a plant still names it: slot_missing
    # (tenant_key, instance_id) is unique: every stored plant carries its own instance_id
    plant = {"tenant_key": "t1", "location_key": None, "site_key": None}
    _insert(
        db.collection(col.PLANT_INSTANCES),
        [
            {**row, "instance_id": f"PLANT-{row['_key']}"}
            for row in [
                {**plant, "_key": "ok", "slot_key": "s1"},
                {**plant, "_key": "keep", "slot_key": "s1", "location_key": "L4"},
                {**plant, "_key": "ghostloc", "slot_key": "s1", "location_key": "OTHER"},
                {**plant, "_key": "noslot", "slot_key": None},
                {**plant, "_key": "foreign", "slot_key": "s2"},
                {**plant, "_key": "done", "slot_key": "s1", "location_key": "L1", "site_key": "S1"},
                # #2524 item 3: the edge cases the first suite did not seed
                {"_key": "notenant", "slot_key": "s1", "location_key": None, "site_key": None},
                {**plant, "_key": "legacy", "slot_key": "s7"},
                {**plant, "_key": "ghost", "slot_key": "s9"},
                {**plant, "_key": "nolocslot", "slot_key": "s3"},
                {**plant, "_key": "nosite", "slot_key": "s5"},
                {**plant, "_key": "sitemissing", "slot_key": "s6"},
                # #2524 item 1: site already set, location missing
                {**plant, "_key": "halfsame", "slot_key": "s1", "site_key": "S1"},
                {**plant, "_key": "halfother", "slot_key": "s1", "site_key": "S_other"},
            ]
        ],
    )


#: Every seeded plant the migration must leave untouched, by reason.
_UNRESOLVED = {
    "no_slot": ["noslot"],
    "cross_tenant": ["foreign", "notenant"],
    "location_missing": ["ghostloc"],
    "slot_missing": ["ghost"],
    "slot_without_location": ["nolocslot"],
    "location_without_site_key": ["nosite"],
    "site_missing": ["sitemissing"],
    "site_without_tenant": ["legacy"],
    "site_mismatch": ["halfother"],
}


def _plant(db, key: str) -> dict:  # type: ignore[no-untyped-def]
    return db.collection(col.PLANT_INSTANCES).get(key)


def test_dry_run_reports_and_writes_nothing(db) -> None:  # type: ignore[no-untyped-def]
    _seed(db)
    revs = {d["_key"]: d["_rev"] for d in db.collection(col.PLANT_INSTANCES).all()}

    report = migration.up(db, dry_run=True)

    assert {d["_key"]: d["_rev"] for d in db.collection(col.PLANT_INSTANCES).all()} == revs
    assert report.details["will_update"] == 3  # ok, keep, halfsame
    assert {reason: sorted(b["listed"]) for reason, b in report.details["unresolved"].items()} == _UNRESOLVED
    assert report.details["unresolved_count"] == sum(len(keys) for keys in _UNRESOLVED.values())


def test_apply_derives_both_keys_and_never_overwrites(db) -> None:  # type: ignore[no-untyped-def]
    _seed(db)

    report = migration.up(db)

    assert report.changed == 3
    assert (_plant(db, "ok")["location_key"], _plant(db, "ok")["site_key"]) == ("L1", "S1")
    assert (_plant(db, "keep")["location_key"], _plant(db, "keep")["site_key"]) == (
        "L4",
        "S4",
    )  # site from its own location, not the slot's
    assert (_plant(db, "ghostloc")["location_key"], _plant(db, "ghostloc")["site_key"]) == ("OTHER", None)
    assert (_plant(db, "halfsame")["location_key"], _plant(db, "halfsame")["site_key"]) == ("L1", "S1")
    assert (_plant(db, "halfother")["location_key"], _plant(db, "halfother")["site_key"]) == (None, "S_other")
    for key in (k for keys in _UNRESOLVED.values() for k in keys if k not in ("ghostloc", "halfother")):
        assert (_plant(db, key)["location_key"], _plant(db, key)["site_key"]) == (None, None), key


def test_a_second_run_writes_nothing_more(db) -> None:  # type: ignore[no-untyped-def]
    _seed(db)
    migration.up(db)
    revs = {d["_key"]: d["_rev"] for d in db.collection(col.PLANT_INSTANCES).all()}

    migration.up(db)

    assert {d["_key"]: d["_rev"] for d in db.collection(col.PLANT_INSTANCES).all()} == revs


def test_a_volume_over_one_update_batch_is_repaired_whole_and_only_once(db) -> None:  # type: ignore[no-untyped-def]
    """#2524 item 3: more plants than one ``UPDATE`` batch (500) and more unresolved keys than are listed (25)."""
    db.collection(col.LOCATIONS).insert({"_key": "L1", "site_key": "S1"})
    db.collection(col.SITES).insert({"_key": "S1", "tenant_key": "t1"})
    db.collection(col.SLOTS).insert({"_key": "s1", "location_key": "L1"})
    repairable = [f"r{i:04d}" for i in range(1203)]
    unplaced = [f"u{i:02d}" for i in range(30)]
    _insert(
        db.collection(col.PLANT_INSTANCES),
        [
            {"_key": key, "instance_id": f"PLANT-{key}", "tenant_key": "t1", "slot_key": slot}
            | {"location_key": None, "site_key": None}
            for keys, slot in ((repairable, "s1"), (unplaced, None))
            for key in keys
        ],
    )

    dry = migration.up(db, dry_run=True)
    first = migration.up(db)
    revs = {d["_key"]: d["_rev"] for d in db.collection(col.PLANT_INSTANCES).all()}
    second = migration.up(db)

    assert dry.details["will_update"] == first.changed == 1203
    assert len(first.details["listed_keys"]) == 25
    assert first.details["unresolved"]["no_slot"]["count"] == 30
    assert len(first.details["unresolved"]["no_slot"]["listed"]) == 25
    stored = {d["_key"]: (d["location_key"], d["site_key"]) for d in db.collection(col.PLANT_INSTANCES).all()}
    assert all(stored[key] == ("L1", "S1") for key in repairable)
    assert all(stored[key] == (None, None) for key in unplaced)
    assert second.changed == 0 and second.scanned == 30
    assert {d["_key"]: d["_rev"] for d in db.collection(col.PLANT_INSTANCES).all()} == revs


def test_the_dry_run_report_is_the_real_run_report(db) -> None:  # type: ignore[no-untyped-def]
    """#2524 item 4: the streamed scan reports in a dry run exactly what the real run then writes."""
    _seed(db)

    dry = migration.up(db, dry_run=True)
    real = migration.up(db)

    assert dry.details.pop("will_update") == real.details.pop("updated") == real.changed == 3
    assert dry.details == real.details
    assert dry.scanned == real.scanned
