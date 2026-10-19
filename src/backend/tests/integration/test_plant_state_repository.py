"""REQ-053 WP 3.7 (#2397) — the plant-states read of a bed against a real store (GP-API-054, GP-ACC-050).

The five statements of ``ArangoPlantStateRepository`` are only proven by a server: a double that returns what the
service expects certifies nothing about the AQL. Every join is exercised with a twin of the *other* tenant that
names the same bed or plant key, and a leak shows up as a wrong count rather than a wrong shape.
Needs a real ArangoDB (see ``tests/integration/conftest.py``).
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.plant_state_repository import ArangoPlantStateRepository
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("plant_state_repository")
pytestmark = pytest.mark.usefixtures("arango_db")

A, B = "ten_a", "ten_b"
NOW = datetime(2026, 6, 10, 12, 0, tzinfo=UTC)
_DOCUMENTS = [
    col.SPECIES,
    col.CULTIVARS,
    col.SLOTS,
    col.GROWTH_PHASES,
    col.PLANT_INSTANCES,
    col.PLANTING_RUNS,
    col.TASKS,
    col.CARE_EVENTS,
    col.PEST_DETECTIONS,
    col.HARVEST_BATCHES,
]


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
        database.create_collection(col.RUN_CONTAINS, edge=True)
        yield database
        system.delete_database(TEST_DATABASE)
    finally:
        client.close()


@pytest.fixture
def db(_database):
    for name in (*_DOCUMENTS, col.RUN_CONTAINS):
        _database.collection(name).truncate()
    return _database


def _insert(db, name: str, *docs: dict) -> None:
    db.collection(name).insert_many(list(docs))


def _plant(key: str, tenant: str = A, **fields) -> dict:
    return {
        "_key": key,
        "tenant_key": tenant,
        "instance_id": f"I-{key}",
        "species_key": "sp",
        "location_key": "bed",
        "planted_on": "2026-04-01",
        "removed_on": None,
        **fields,
    }


def _read(db, *, tenant: str = A, offset: int = 0, limit: int = 50, location: str = "bed"):
    return ArangoPlantStateRepository(db).list_bed_plants(
        location, tenant_key=tenant, now=NOW, offset=offset, limit=limit
    )


@pytest.fixture
def world(db):
    _insert(
        db,
        col.SPECIES,
        {"_key": "sp", "scientific_name": "Solanum lycopersicum", "common_names": ["Tomato", "Love apple"]},
    )
    _insert(db, col.CULTIVARS, {"_key": "cv", "name": "Roma"})
    _insert(
        db,
        col.SLOTS,
        {"_key": "s1", "slot_id": "BED_001", "location_key": "bed"},
        {"_key": "sx", "slot_id": "FOREIGN_001", "location_key": "other_bed"},
    )
    _insert(
        db,
        col.GROWTH_PHASES,
        {
            "_key": "ph",
            "name": "flowering",
            "display_name": "Flowering",
            "typical_duration_days": 60,
            "allows_harvest": False,
        },
    )
    _insert(db, col.PLANTING_RUNS, {"_key": "run1", "tenant_key": A})
    return db


class TestFacts:
    def test_one_plant_with_everything_joined_in(self, world) -> None:
        db = world
        _insert(
            db,
            col.PLANT_INSTANCES,
            _plant(
                "p1",
                cultivar_key="cv",
                slot_key="s1",
                current_phase_key="ph",
                current_phase_started_at="2026-05-20T08:00:00+00:00",
                photo_refs=["att1", "att2"],
            ),
        )
        db.collection(col.RUN_CONTAINS).insert(
            {"_from": f"{col.PLANTING_RUNS}/run1", "_to": f"{col.PLANT_INSTANCES}/p1"}
        )
        _insert(
            db,
            col.TASKS,
            {
                "_key": "t1",
                "tenant_key": A,
                "status": "pending",
                "entity_type": "plant_instance",
                "entity_key": "p1",
                "name": "Prune",
                "category": "pruning",
                "due_date": "2026-06-08T00:00:00+00:00",
            },
            {
                "_key": "t2",
                "tenant_key": A,
                "status": "pending",
                "entity_type": "planting_run",
                "entity_key": "run1",
                "name": "Water",
                "category": "watering",
                "due_date": "2026-06-10T00:00:00+00:00",
            },
            {
                "_key": "t3",
                "tenant_key": A,
                "status": "completed",
                "entity_type": "plant_instance",
                "entity_key": "p1",
                "name": "Done",
                "category": "pruning",
                "due_date": "2026-06-01T00:00:00+00:00",
            },
            {
                "_key": "t4",
                "tenant_key": A,
                "status": "pending",
                "suggested": True,
                "entity_type": "plant_instance",
                "entity_key": "p1",
                "name": "Proposal",
                "category": "pruning",
                "due_date": "2026-06-01T00:00:00+00:00",
            },
        )
        _insert(
            db,
            col.CARE_EVENTS,
            {
                "_key": "e1",
                "tenant_key": A,
                "location_key": "bed",
                "category": "watering",
                "plant_keys": ["p1"],
                "performed_at": "2026-06-05T07:00:00+00:00",
                "voided_at": None,
            },
            {
                "_key": "e2",
                "tenant_key": A,
                "location_key": "bed",
                "category": "watering",
                "plant_keys": [],
                "performed_at": "2026-06-09T07:00:00+00:00",
                "voided_at": None,
            },
            {
                "_key": "e3",
                "tenant_key": A,
                "location_key": "bed",
                "category": "feeding",
                "plant_keys": ["p1"],
                "performed_at": "2026-06-01T07:00:00+00:00",
                "voided_at": None,
            },
            {
                "_key": "e4",
                "tenant_key": A,
                "location_key": "bed",
                "category": "feeding",
                "plant_keys": ["p1"],
                "performed_at": "2026-06-09T09:00:00+00:00",
                "voided_at": "2026-06-09T10:00:00+00:00",
            },
        )
        _insert(
            db,
            col.PEST_DETECTIONS,
            {
                "_key": "d1",
                "tenant_key": A,
                "plant_instance_key": "p1",
                "created_at": "2026-06-08T10:00:00+00:00",
                "findings": [{"label": "aphid", "common_name": "Aphids", "category": "pest"}],
                "feedback": [],
            },
            {
                "_key": "d2",
                "tenant_key": A,
                "plant_instance_key": "p1",
                "created_at": "2026-06-09T10:00:00+00:00",
                "findings": [{"label": "ladybird", "common_name": "Ladybird", "category": "beneficial"}],
                "feedback": [],
            },
            {
                "_key": "d3",
                "tenant_key": A,
                "plant_instance_key": "p1",
                "created_at": "2026-06-09T11:00:00+00:00",
                "findings": [{"label": "mildew", "common_name": "Mildew", "category": "symptom"}],
                "feedback": [{"finding_label": "mildew", "confirmed": False}],
            },
            {
                "_key": "d4",
                "tenant_key": A,
                "plant_instance_key": "p1",
                "created_at": "2026-03-01T10:00:00+00:00",
                "findings": [{"label": "old", "common_name": "Old", "category": "pest"}],
                "feedback": [],
            },
        )
        _insert(
            db,
            col.HARVEST_BATCHES,
            {"_key": "h1", "tenant_key": A, "plant_key": "p1", "harvest_type": "partial", "wet_weight_g": 120.5},
            {"_key": "h2", "tenant_key": A, "plant_key": "p1", "harvest_type": "continuous", "wet_weight_g": 30.0},
        )

        [source] = _read(db)

        assert (source.plant_key, source.instance_id, source.slot_key, source.slot_id) == (
            "p1",
            "I-p1",
            "s1",
            "BED_001",
        )
        assert (source.species_name, source.scientific_name, source.cultivar_name) == (
            "Tomato",
            "Solanum lycopersicum",
            "Roma",
        )
        assert (source.phase_key, source.phase_name, source.phase_typical_days) == ("ph", "Flowering", 60)
        assert source.phase_started_on == date(2026, 5, 20)
        assert source.planted_on == date(2026, 4, 1)
        assert sorted((task.category, task.due) for task in source.open_tasks) == [
            ("pruning", date(2026, 6, 8)),
            ("watering", date(2026, 6, 10)),
        ]
        assert source.next_task is not None
        assert (source.next_task.name, source.next_task.due) == ("Prune", date(2026, 6, 8))
        # the bed-wide watering of 06-09 is newer than the plant's own of 06-05; the voided feeding does not count
        assert source.last_watering_at == datetime(2026, 6, 9, 7, 0, tzinfo=UTC)
        assert source.last_feeding_at == datetime(2026, 6, 1, 7, 0, tzinfo=UTC)
        # aphids stand; the beneficial, the rejected finding and the stale detection do not
        assert (source.open_finding_count, source.finding_label) == (1, "Aphids")
        assert (source.harvest_batch_count, source.harvested_total_g) == (2, 150.5)
        assert source.cover_photo_ref == "att1"

    def test_a_plant_without_any_extras_has_empty_facts(self, world) -> None:
        _insert(world, col.PLANT_INSTANCES, _plant("p1"))
        [source] = _read(world)
        assert source.open_tasks == ()
        assert source.next_task is None
        assert source.last_watering_at is None
        assert source.open_finding_count == 0
        assert (source.harvest_batch_count, source.harvested_total_g) == (0, None)
        assert source.cover_photo_ref is None
        assert source.phase_key is None

    def test_the_slot_of_another_bed_is_not_reported(self, world) -> None:
        _insert(world, col.PLANT_INSTANCES, _plant("p1", slot_key="sx"))
        [source] = _read(world)
        assert (source.slot_key, source.slot_id) == (None, None)

    def test_removed_plants_are_not_listed(self, world) -> None:
        _insert(world, col.PLANT_INSTANCES, _plant("p1"), _plant("p2", removed_on="2026-05-01"))
        assert [source.plant_key for source in _read(world)] == ["p1"]


class TestWindow:
    def test_plants_are_ordered_by_key_and_paged(self, world) -> None:
        _insert(world, col.PLANT_INSTANCES, *[_plant(f"p{n}") for n in (3, 1, 2, 5, 4)])
        assert [s.plant_key for s in _read(world, offset=0, limit=2)] == ["p1", "p2"]
        assert [s.plant_key for s in _read(world, offset=2, limit=2)] == ["p3", "p4"]
        assert [s.plant_key for s in _read(world, offset=4, limit=2)] == ["p5"]
        assert _read(world, offset=5, limit=2) == []


class TestTenantScope:
    def test_another_tenants_plant_in_the_same_bed_is_not_listed(self, world) -> None:
        _insert(world, col.PLANT_INSTANCES, _plant("p1"), _plant("p2", tenant=B))
        assert [s.plant_key for s in _read(world)] == ["p1"]
        assert [s.plant_key for s in _read(world, tenant=B)] == ["p2"]

    def test_foreign_tasks_events_findings_and_harvests_on_a_shared_key_do_not_count(self, world) -> None:
        db = world
        _insert(db, col.PLANT_INSTANCES, _plant("p1"))
        _insert(
            db,
            col.TASKS,
            {
                "_key": "t1",
                "tenant_key": B,
                "status": "pending",
                "entity_type": "plant_instance",
                "entity_key": "p1",
                "name": "Foreign",
                "category": "pruning",
                "due_date": "2026-06-01T00:00:00+00:00",
            },
        )
        _insert(
            db,
            col.CARE_EVENTS,
            {
                "_key": "e1",
                "tenant_key": B,
                "location_key": "bed",
                "category": "watering",
                "plant_keys": ["p1"],
                "performed_at": "2026-06-09T07:00:00+00:00",
                "voided_at": None,
            },
        )
        _insert(
            db,
            col.PEST_DETECTIONS,
            {
                "_key": "d1",
                "tenant_key": B,
                "plant_instance_key": "p1",
                "created_at": "2026-06-09T10:00:00+00:00",
                "findings": [{"label": "x", "common_name": "X", "category": "pest"}],
                "feedback": [],
            },
        )
        _insert(
            db,
            col.HARVEST_BATCHES,
            {"_key": "h1", "tenant_key": B, "plant_key": "p1", "harvest_type": "partial", "wet_weight_g": 99.0},
        )

        [source] = _read(db)

        assert source.open_tasks == ()
        assert source.next_task is None
        assert source.last_watering_at is None
        assert source.open_finding_count == 0
        assert source.harvest_batch_count == 0

    def test_an_empty_tenant_is_refused(self, world) -> None:
        with pytest.raises(ValueError, match="tenant_key"):
            _read(world, tenant="")
