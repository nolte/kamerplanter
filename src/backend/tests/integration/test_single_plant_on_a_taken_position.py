"""REQ-053 V-25 (#2913): a single plant on a taken planting position, against a real ArangoDB.

What the doubles cannot decide, measured here through the production reads: a plant ``create_plant`` stores is found
again by the ``placed_in`` traversal (``get_active_by_slot``) so the next one on the same position is refused; a
removed plant frees it; a foreign tenant's plant on a slot is not read as standing there; a live run's
``run_planned_at`` edge (``reservations_for``) blocks a position, a completed run's does not; a row keeps taking
plants. Every refusal is paired with the positive control through the same path.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any
from unittest.mock import MagicMock

import pytest
from arango import ArangoClient

from app.common.datetimes import today_utc
from app.common.exceptions import PlanError
from app.data_access.arango import collections as col
from app.data_access.arango.plant_instance_repository import ArangoPlantInstanceRepository
from app.data_access.arango.planting_reservation_repository import ArangoPlantingReservationRepository
from app.data_access.arango.site_repository import ArangoSiteRepository
from app.domain.models.plant_instance import PlantInstance
from app.domain.services.plant_instance_service import PlantInstanceService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = pytest.mark.usefixtures("arango_db")

TEST_DATABASE = run_database_name("single_plant_taken_position")
A, B = "ten_a", "ten_b"


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    # The production schema and graph: ``get_active_by_slot`` traverses ``kamerplanter_graph``.
    col.ensure_collections(db)
    yield db
    system.delete_database(TEST_DATABASE)


def _slot(key: str, role: str = "position", capacity: int = 1) -> dict[str, Any]:
    return {
        "_key": key,
        "slot_id": f"BED_{key.upper()}",
        "location_key": "bed",
        "capacity_plants": capacity,
        "currently_occupied": False,
        "slot_role": role,
        "archived_at": None,
    }


@pytest.fixture
def db(database):
    for entry in database.collections():
        if not entry["system"]:
            database.collection(entry["name"]).truncate()
    database.collection(col.SITES).insert(
        {"_key": "site_a", "tenant_key": A, "name": "A", "type": "outdoor", "total_area_m2": 0.0, "timezone": "UTC"}
    )
    database.collection(col.LOCATIONS).insert(
        {"_key": "bed", "site_key": "site_a", "name": "Bed 1", "location_type_key": "bed", "area_m2": 2.0}
    )
    for slot in (_slot("s1"), _slot("s2"), _slot("s3"), _slot("row", "row", 20)):
        database.collection(col.SLOTS).insert(slot)
        database.collection(col.HAS_SLOT).insert({"_from": "locations/bed", "_to": f"slots/{slot['_key']}"})
    return database


def _service(db) -> PlantInstanceService:
    rotation = MagicMock()
    rotation.validate_or_raise.return_value = None
    companion = MagicMock()
    companion.check_or_raise.return_value = []
    return PlantInstanceService(
        ArangoPlantInstanceRepository(db),
        ArangoSiteRepository(db),
        rotation,
        companion,
        reservation_repo=ArangoPlantingReservationRepository(db),
    )


def _plant(slot_key: str, instance_id: str) -> PlantInstance:
    return PlantInstance(
        instance_id=instance_id,
        species_key="sp_lettuce",
        planted_on=date(2026, 11, 13),
        site_key="site_a",
        location_key="bed",
        slot_key=slot_key,
    )


def _reserve(db, run: str, slot: str, status: str) -> None:
    db.collection(col.PLANTING_RUNS).insert(
        {"_key": run, "tenant_key": A, "name": run, "run_type": "monoculture", "status": status, "location_key": "bed"}
    )
    start = today_utc() + timedelta(days=5)
    db.collection(col.RUN_PLANNED_AT).insert(
        {
            "_from": f"planting_runs/{run}",
            "_to": f"slots/{slot}",
            "entry_key": "e1",
            "planned_species_key": "sp_carrot",
            "sequence": 1,
            "planned_from": start.isoformat(),
            "planned_until": (start + timedelta(days=60)).isoformat(),
        }
    )


def test_the_second_plant_on_a_position_is_refused_and_a_removal_frees_it(db) -> None:
    service = _service(db)
    first = service.create_plant(_plant("s1", "LAC-1"), tenant_key=A)
    with pytest.raises(PlanError) as refused:
        service.create_plant(_plant("s1", "LAC-2"), tenant_key=A)
    assert refused.value.status_code == 409
    assert refused.value.error_code == "slot.occupied"
    assert db.collection(col.PLANT_INSTANCES).count() == 1

    db.collection(col.PLANT_INSTANCES).update({"_key": first.key, "removed_on": "2026-11-14"})
    again = service.create_plant(_plant("s1", "LAC-3"), tenant_key=A)
    assert again.key


def test_a_foreign_tenants_plant_on_the_slot_does_not_count(db) -> None:
    db.collection(col.PLANT_INSTANCES).insert(
        {
            "_key": "p_foreign",
            "tenant_key": B,
            "instance_id": "X",
            "species_key": "sp",
            "planted_on": "2026-01-01",
            "slot_key": "s2",
            "removed_on": None,
        }
    )
    db.collection(col.PLACED_IN).insert({"_from": "plant_instances/p_foreign", "_to": "slots/s2"})
    created = _service(db).create_plant(_plant("s2", "LAC-1"), tenant_key=A)
    assert created.slot_key == "s2"


def test_a_live_runs_reservation_blocks_a_position_a_completed_runs_does_not(db) -> None:
    _reserve(db, "run_live", "s2", "planned")
    _reserve(db, "run_done", "s3", "completed")
    service = _service(db)
    with pytest.raises(PlanError) as refused:
        service.create_plant(_plant("s2", "LAC-1"), tenant_key=A)
    assert refused.value.error_code == "slot.already_planned"
    assert refused.value.details[0]["conflicting_run_key"] == "run_live"
    assert service.create_plant(_plant("s3", "LAC-2"), tenant_key=A).slot_key == "s3"


def test_a_row_keeps_taking_plants(db) -> None:
    service = _service(db)
    service.create_plant(_plant("row", "CAR-1"), tenant_key=A)
    service.create_plant(_plant("row", "CAR-2"), tenant_key=A)
    assert db.collection(col.PLANT_INSTANCES).count() == 2
