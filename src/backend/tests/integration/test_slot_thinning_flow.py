"""REQ-053 W-015 (Anhang A 60, #2830) — sown → thinned → n plants, end to end on a real ArangoDB.

The real services and repositories, no double between the service call and the database: a row slot of the bed is
reserved by a planned run, recorded as sown (``PUT /slots/{key}/sowing``'s service), reported by the plant-state read
as lifecycle ``sown``, and thinned into the plants the row holds at the run's ``thinning_to_cm`` — afterwards
``sown_at`` is empty, the plants stand in the slot as plants of the run, the run is ``active`` and a ``thinning`` care
event names them. Another tenant reaches neither the slot nor the sown state (404).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from arango import ArangoClient

from app.common.datetimes import today_utc
from app.common.enums import PlantingRunStatus, PlantingRunType, TenantRole
from app.common.exceptions import NotFoundError, PlanError
from app.data_access.arango import collections as col
from app.data_access.arango.care_event_repository import ArangoCareEventRepository
from app.data_access.arango.collections import ensure_collections
from app.data_access.arango.garden_plan_repository import ArangoGardenPlanRepository
from app.data_access.arango.plant_instance_repository import ArangoPlantInstanceRepository
from app.data_access.arango.plant_state_repository import ArangoPlantStateRepository
from app.data_access.arango.planting_reservation_repository import ArangoPlantingReservationRepository
from app.data_access.arango.planting_run_repository import ArangoPlantingRunRepository
from app.data_access.arango.site_repository import ArangoSiteRepository
from app.data_access.arango.species_repository import ArangoSpeciesRepository
from app.domain.engines.planting_run_engine import PlantingRunEngine
from app.domain.models.planting_reservation import SlotThinningInput
from app.domain.models.planting_run import PlantingRun, PlantingRunEntry
from app.domain.services.care_event_service import CareEventService
from app.domain.services.plant_state_service import PlantStateService
from app.domain.services.planting_reservation_service import PlantingReservationService
from app.domain.services.planting_run_service import PlantingRunService
from app.domain.services.slot_thinning_service import SlotThinningService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name
from tests.support.care_event_fakes import FakeAttachmentRepo, FakeAttachmentService, FakeFertilizers, FakeMemberships

pytestmark = pytest.mark.usefixtures("arango_db")

TEST_DATABASE = run_database_name("slot_thinning_flow")
A, B = "ten_a", "ten_b"
USER = "u_sabine"
#: 1.20 m of row along the bed.
ROW = {"kind": "polyline", "points": [[0.2, 0.5], [1.4, 0.5]], "width_m": 0.05}


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    ensure_collections(db)
    yield db
    system.delete_database(TEST_DATABASE)
    client.close()


@pytest.fixture
def world(database):
    db = database
    for entry in db.collections():
        if not entry["system"]:
            db.collection(entry["name"]).truncate()
    db.collection(col.SITES).insert({"_key": "site_a", "tenant_key": A, "name": "A", "type": "outdoor"})
    db.collection(col.SITES).insert({"_key": "site_b", "tenant_key": B, "name": "B", "type": "outdoor"})
    db.collection(col.LOCATIONS).insert(
        {"_key": "bed", "site_key": "site_a", "name": "Bed 3", "area_m2": 8.0,
         "geometry": {"kind": "rect", "origin": [0, 0], "width_m": 4, "length_m": 2, "rotation_deg": 0}}
    )  # fmt: skip
    db.collection(col.SPECIES).insert({"_key": "sp_carrot", "scientific_name": "Daucus carota", "tenant_key": ""})
    db.collection(col.SLOTS).insert(
        {"_key": "row1", "slot_id": "BED3_R01", "location_key": "bed", "slot_role": "row", "geometry": ROW,
         "capacity_plants": 1, "currently_occupied": False, "geometry_source": "editor"}
    )  # fmt: skip
    db.collection(col.HAS_SLOT).insert({"_from": "locations/bed", "_to": "slots/row1"})

    sites = ArangoSiteRepository(db)
    run_repo = ArangoPlantingRunRepository(db)
    reservation_repo = ArangoPlantingReservationRepository(db)
    run = run_repo.create(
        PlantingRun(tenant_key=A, name="Carrots", run_type=PlantingRunType.MONOCULTURE, location_key="bed")
    )
    entry = run_repo.create_entry(
        PlantingRunEntry(
            run_key=run.key or "",
            tenant_key=A,
            species_key="sp_carrot",
            quantity=1,
            id_prefix="DAU",
            sowing_spacing_cm=1.0,
            thinning_to_cm=5.0,
        )
    )
    planned_from = today_utc() - timedelta(days=30)
    db.collection(col.RUN_PLANNED_AT).insert(
        {"_from": f"planting_runs/{run.key}", "_to": "slots/row1", "entry_key": entry.key,
         "planned_species_key": "sp_carrot", "sequence": 1, "planned_from": planned_from.isoformat()}
    )  # fmt: skip

    care = CareEventService(
        ArangoCareEventRepository(db),
        sites,
        FakeMemberships(),
        FakeFertilizers(),
        FakeAttachmentRepo(),
        FakeAttachmentService(),
    )
    plan = ArangoGardenPlanRepository(db)
    reservations = PlantingReservationService(reservation_repo, run_repo, sites, plan, care)
    runs = PlantingRunService(
        run_repo,
        ArangoPlantInstanceRepository(db),
        PlantingRunEngine(),
        site_repo=sites,
        reservations=reservations,
        reservation_repo=reservation_repo,
    )
    return SimpleNamespace(
        db=db,
        run_key=run.key,
        thinning=SlotThinningService(sites, reservation_repo, run_repo, runs, care, ArangoSpeciesRepository(db)),
        states=PlantStateService(sites, ArangoPlantStateRepository(db)),
        reservations=reservations,
    )


def sow(world, *, tenant_key: str = A):
    return world.thinning.mark_sown(
        "row1", tenant_key=tenant_key, role=TenantRole.GROWER, sown_at=today_utc() - timedelta(days=14)
    )


def test_sown_then_thinned_gives_the_plants_of_the_row_and_clears_sown_at(world) -> None:
    sow(world)
    assert world.db.collection(col.SLOTS).get("row1")["sown_at"] == (today_utc() - timedelta(days=14)).isoformat()

    states = world.states.list_plant_states("bed", tenant_key=A, now=datetime.now(UTC))
    assert [(entry.state.lifecycle, entry.source.slot_key) for entry in states] == [("sown", "row1")]
    planned = world.reservations.list_plantings("bed", tenant_key=A, state="planned", year=None, offset=0, limit=50)
    assert [(row.slot_role, row.sown_at) for row in planned] == [("row", today_utc() - timedelta(days=14))]

    plan = world.thinning.plan_thinning("row1", tenant_key=A)
    assert (plan.thinning_to_cm, plan.suggested_count) == (5.0, 24)

    outcome = world.thinning.thin_slot(
        "row1", tenant_key=A, user_key=USER, role=TenantRole.GROWER, request=SlotThinningInput()
    )

    assert len(outcome.plant_keys) == 24
    slot = world.db.collection(col.SLOTS).get("row1")
    assert slot["sown_at"] is None
    assert slot["currently_occupied"] is True
    placed = [e for e in world.db.collection(col.PLACED_IN).all() if e["_to"] == "slots/row1"]
    assert sorted(e["_from"].split("/")[1] for e in placed) == sorted(outcome.plant_keys)
    contained = {e["_to"].split("/")[1] for e in world.db.collection(col.RUN_CONTAINS).all()}
    assert contained == set(outcome.plant_keys)
    plants = [world.db.collection(col.PLANT_INSTANCES).get(key) for key in outcome.plant_keys]
    assert {p["tenant_key"] for p in plants} == {A}
    assert {p["species_key"] for p in plants} == {"sp_carrot"}
    assert {p["slot_key"] for p in plants} == {"row1"}
    run = world.db.collection(col.PLANTING_RUNS).get(world.run_key)
    assert run["status"] == PlantingRunStatus.ACTIVE.value
    assert run["actual_quantity"] == 24
    (event,) = [e for e in world.db.collection(col.CARE_EVENTS).all() if e["category"] == "thinning"]
    assert event["trigger"] == "system"
    assert sorted(event["plant_keys"]) == sorted(outcome.plant_keys)

    # the sown entry is gone; the plants are reported instead
    states = world.states.list_plant_states("bed", tenant_key=A, now=datetime.now(UTC), limit=50)
    assert {entry.state.lifecycle for entry in states} == {"active"}
    assert len(states) == 24


def test_a_second_thinning_of_the_same_slot_is_refused(world) -> None:
    sow(world)
    world.thinning.thin_slot("row1", tenant_key=A, user_key=USER, role=TenantRole.GROWER, request=SlotThinningInput())
    with pytest.raises(PlanError):
        world.thinning.thin_slot(
            "row1", tenant_key=A, user_key=USER, role=TenantRole.GROWER, request=SlotThinningInput()
        )
    assert len(list(world.db.collection(col.PLANT_INSTANCES).all())) == 24


def test_another_tenant_reaches_neither_the_slot_nor_its_sown_state(world) -> None:
    sow(world)
    with pytest.raises(NotFoundError):
        world.thinning.thin_slot(
            "row1", tenant_key=B, user_key=USER, role=TenantRole.GROWER, request=SlotThinningInput(count=3)
        )
    with pytest.raises(NotFoundError):
        sow(world, tenant_key=B)
    with pytest.raises(NotFoundError):
        world.states.list_plant_states("bed", tenant_key=B, now=datetime.now(UTC))
    # the read below the service filters on the reserving run's tenant as well
    assert ArangoPlantStateRepository(world.db).list_sown_slots("bed", tenant_key=B) == []
    assert list(world.db.collection(col.PLANT_INSTANCES).all()) == []
