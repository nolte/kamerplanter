"""#2952 — v0112 measured on a real ArangoDB: the scan, the guarded insert and ``down``.

A plant moved before #2948 carries the new ``slot_key`` and only the edge to the slot it was created on. The fixture
writes that stored shape directly (the production writer now adds the edge). Asserted: the edge to the current slot
appears with the marker and the plant's creation time, the edge to the slot left stays, the crop-rotation history of
the new slot (``get_history_by_slot``) finds the plant, a slot of another tenant gets no edge, a second run inserts
nothing, the dry run writes nothing and ``down`` removes exactly the marked edges.

Locally it needs a database::

    docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_v0112_placed_in_backfill.py -v
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.collections import ensure_collections
from app.data_access.arango.plant_instance_repository import ArangoPlantInstanceRepository
from app.migrations.versions.v0112_placed_in_backfill import migration
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the migration's scan and guarded INSERT are AQL over a real server"),
]

_DB_NAME = run_database_name("v0112_placed_in_backfill")
CREATED = "2025-04-01T08:00:00+00:00"


@pytest.fixture
def db():  # type: ignore[no-untyped-def]
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)
    system.create_database(_DB_NAME)
    database = client.db(_DB_NAME, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    ensure_collections(database)
    _seed(database)
    yield database
    system.delete_database(_DB_NAME)


def _insert(collection, docs: list[dict]) -> None:  # type: ignore[no-untyped-def]
    refused = [r for r in collection.insert_many(docs) if isinstance(r, Exception)]
    assert not refused, refused


def _plant(key: str, slot: str | None, tenant: str = "t_a", **fields: object) -> dict:
    return {
        "_key": key,
        "tenant_key": tenant,
        "instance_id": f"ID-{key}",
        "species_key": "sp",
        "planted_on": "2025-04-01",
        "slot_key": slot,
        "created_at": CREATED,
        **fields,
    }


def _seed(db) -> None:  # type: ignore[no-untyped-def]
    _insert(
        db.collection(col.SITES), [{"_key": "site_a", "tenant_key": "t_a"}, {"_key": "site_b", "tenant_key": "t_b"}]
    )
    _insert(
        db.collection(col.LOCATIONS),
        [
            {"_key": "bed_a", "site_key": "site_a"},
            {"_key": "bed_a2", "site_key": "site_a"},
            {"_key": "bed_b", "site_key": "site_b"},
        ],
    )
    _insert(
        db.collection(col.SLOTS),
        [
            {"_key": "a1", "slot_id": "A1", "location_key": "bed_a"},
            {"_key": "a2", "slot_id": "A2", "location_key": "bed_a2"},
            {"_key": "b1", "slot_id": "B1", "location_key": "bed_b"},
        ],
    )
    _insert(
        db.collection(col.PLANT_INSTANCES),
        [
            _plant("legacy", "a2"),  # created on a1, moved to a2 before #2948
            _plant("placed", "a1"),  # never moved: has its edge
            _plant("foreign", "b1"),  # t_a plant naming a t_b slot: never linked
            _plant("loose", None),
            _plant("harvested", "a2", removed_on="2025-09-01"),
        ],
    )
    _insert(
        db.collection(col.PLACED_IN),
        [
            {"_from": "plant_instances/legacy", "_to": "slots/a1", "created_at": CREATED},
            {"_from": "plant_instances/placed", "_to": "slots/a1", "created_at": CREATED},
        ],
    )


def _targets(db, plant: str) -> list[str]:  # type: ignore[no-untyped-def]
    return sorted(e["_to"] for e in db.collection(col.PLACED_IN).find({"_from": f"plant_instances/{plant}"}))


def test_the_legacy_moved_plants_get_their_edge_and_keep_the_old_one(db) -> None:  # type: ignore[no-untyped-def]
    report = migration.up(db)

    assert report.changed == 2
    assert report.details["inserted"] == 2
    assert report.details["unresolved"] == {"cross_tenant": {"count": 1, "listed": ["foreign"]}}
    assert _targets(db, "legacy") == ["slots/a1", "slots/a2"]
    assert _targets(db, "harvested") == ["slots/a2"]
    assert _targets(db, "placed") == ["slots/a1"]
    assert _targets(db, "foreign") == []
    assert _targets(db, "loose") == []
    new = next(iter(db.collection(col.PLACED_IN).find({"_from": "plant_instances/legacy", "_to": "slots/a2"})))
    assert (new["backfilled_by"], new["created_at"]) == ("v0112", CREATED)


def test_the_new_slots_rotation_history_finds_the_plant(db) -> None:  # type: ignore[no-untyped-def]
    plants = ArangoPlantInstanceRepository(db)
    before = {p.key for p in plants.get_history_by_slot("a2", years=5, tenant_key="t_a")}

    migration.up(db)

    after = {p.key for p in plants.get_history_by_slot("a2", years=5, tenant_key="t_a")}
    assert before == set()
    assert after == {"legacy", "harvested"}
    # the slot left keeps its history
    assert {p.key for p in plants.get_history_by_slot("a1", years=5, tenant_key="t_a")} == {"legacy", "placed"}


def test_a_second_run_inserts_nothing(db) -> None:  # type: ignore[no-untyped-def]
    migration.up(db)
    edges = db.collection(col.PLACED_IN).count()

    second = migration.up(db)

    assert second.changed == 0
    assert second.scanned == 1  # the foreign plant, listed again
    assert db.collection(col.PLACED_IN).count() == edges


def test_the_dry_run_writes_nothing(db) -> None:  # type: ignore[no-untyped-def]
    report = migration.up(db, dry_run=True)

    assert (report.dry_run, report.changed, report.details["will_insert"]) == (True, 0, 2)
    assert db.collection(col.PLACED_IN).count() == 2


def test_down_removes_exactly_the_marked_edges(db) -> None:  # type: ignore[no-untyped-def]
    migration.up(db)
    assert db.collection(col.PLACED_IN).count() == 4

    dry = migration.down(db, dry_run=True)
    assert (dry.changed, dry.details["will_remove"], db.collection(col.PLACED_IN).count()) == (0, 2, 4)

    report = migration.down(db)

    assert report.changed == 2
    assert _targets(db, "legacy") == ["slots/a1"]
    assert _targets(db, "placed") == ["slots/a1"]
    assert _targets(db, "harvested") == []
