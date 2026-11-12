"""REQ-053 GP-FR-074 (#2896) — succession batches reserve slots, end to end on a real ArangoDB.

The real succession, run and reservation services over the real repositories: ``generate`` writes one
``run_planned_at`` edge per batch slot with the batch's window, an overlap is the 409 of V-08 and leaves no run
behind, a schedule change drops the edges of the batches not yet due, the plan read model announces the first
reserved day of a slot (``planned_from``) and another tenant's reservation is neither counted nor announced.
"""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import pytest
from arango import ArangoClient

from app.common.exceptions import NotFoundError, PlanError
from app.data_access.arango import collections as col
from app.data_access.arango.care_event_repository import ArangoCareEventRepository
from app.data_access.arango.collections import ensure_collections
from app.data_access.arango.garden_plan_repository import ArangoGardenPlanRepository
from app.data_access.arango.plant_instance_repository import ArangoPlantInstanceRepository
from app.data_access.arango.planting_reservation_repository import ArangoPlantingReservationRepository
from app.data_access.arango.planting_run_repository import ArangoPlantingRunRepository
from app.data_access.arango.site_repository import ArangoSiteRepository
from app.data_access.arango.succession_plan_repository import ArangoSuccessionPlanRepository
from app.domain.engines.planting_run_engine import PlantingRunEngine
from app.domain.models.succession_plan import SuccessionPlan
from app.domain.services import succession_plan_service as succession_module
from app.domain.services.care_event_service import CareEventService
from app.domain.services.garden_plan_service import GardenPlanService
from app.domain.services.planting_reservation_service import PlantingReservationService
from app.domain.services.planting_run_service import PlantingRunService
from app.domain.services.succession_plan_service import SuccessionPlanService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name
from tests.support.care_event_fakes import FakeAttachmentRepo, FakeAttachmentService, FakeFertilizers, FakeMemberships

pytestmark = pytest.mark.usefixtures("arango_db")

TEST_DATABASE = run_database_name("succession_slot_reservation")
A, B = "ten_a", "ten_b"
D = date
#: Before the first batch; ``GET /plan`` reads its own UTC day, so the dates lie in a future year.
TODAY = D(2027, 1, 10)
_BED_GEOMETRY = {"kind": "rect", "origin": [0, 0], "width_m": 4, "length_m": 2, "rotation_deg": 0}


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
def world(database, monkeypatch):
    db = database
    for entry in db.collections():
        if not entry["system"]:
            db.collection(entry["name"]).truncate()
    monkeypatch.setattr(succession_module, "today_utc", lambda: TODAY)
    db.collection(col.SITES).insert({"_key": "site_a", "tenant_key": A, "name": "A", "type": "outdoor"})
    db.collection(col.SITES).insert({"_key": "site_b", "tenant_key": B, "name": "B", "type": "outdoor"})
    db.collection(col.LOCATIONS).insert(
        {"_key": "bed", "site_key": "site_a", "name": "Bed 3", "area_m2": 8.0, "geometry": _BED_GEOMETRY}
    )
    for n in range(1, 5):
        db.collection(col.SLOTS).insert(
            {"_key": f"s{n}", "slot_id": f"BED3_00{n}", "location_key": "bed", "sequence": n,
             "capacity_plants": 1, "currently_occupied": False,
             "geometry": {"kind": "point", "origin": [0.5 * n, 1.0]}}
        )  # fmt: skip
        db.collection(col.HAS_SLOT).insert({"_from": f"{col.LOCATIONS}/bed", "_to": f"{col.SLOTS}/s{n}"})
    db.collection(col.SPECIES).insert({"_key": "sp", "scientific_name": "Lactuca sativa", "tenant_key": ""})

    sites = ArangoSiteRepository(db)
    plan_repo = ArangoGardenPlanRepository(db)
    run_repo = ArangoPlantingRunRepository(db)
    reservation_repo = ArangoPlantingReservationRepository(db)
    care = CareEventService(
        ArangoCareEventRepository(db),
        sites,
        FakeMemberships(),
        FakeFertilizers(),
        FakeAttachmentRepo(),
        FakeAttachmentService(),
    )
    reservations = PlantingReservationService(reservation_repo, run_repo, sites, plan_repo, care)

    def resolver(key, *, tenant_key):
        if key != "sp":
            raise NotFoundError("Species", key)
        return SimpleNamespace(scientific_name="Lactuca sativa", green_manure_suitable=False)

    runs = PlantingRunService(
        run_repo,
        ArangoPlantInstanceRepository(db),
        PlantingRunEngine(),
        site_repo=sites,
        species_resolver=resolver,
        reservations=reservations,
        reservation_repo=reservation_repo,
    )
    succession = SuccessionPlanService(
        ArangoSuccessionPlanRepository(db),
        runs,
        site_repo=sites,
        species_resolver=resolver,
        reservations=reservations,
    )
    return SimpleNamespace(db=db, succession=succession, plan=GardenPlanService(sites, plan_repo))


def make_plan(world, **overrides) -> SuccessionPlan:
    """Three batches of two lettuces: 1 April, 22 April, 13 May 2027, 21 days each."""
    data = {
        "name": "Lettuce bed 3",
        "species_key": "sp",
        "interval_days": 21,
        "start_date": D(2027, 4, 1),
        "end_date": D(2027, 5, 13),
        "plants_per_batch": 2,
        "batch_duration_days": 21,
        "location_key": "bed",
        **overrides,
    }
    return world.succession.create_plan(SuccessionPlan(**data), tenant_key=A)


def planned_edges(world) -> list[tuple[str, str, str, str | None]]:
    return sorted(
        (e["_from"].split("/")[1], e["_to"].split("/")[1], e["planned_from"], e["planned_until"])
        for e in world.db.collection(col.RUN_PLANNED_AT).all()
    )


def test_every_batch_reserves_its_slots_for_its_window(world) -> None:
    plan = make_plan(world)

    stored, runs = world.succession.generate_runs(plan.key, tenant_key=A)

    assert stored.completed_batches == 3
    first, second, third = (run.key for run in runs)
    assert planned_edges(world) == sorted(
        [
            (first, "s1", "2027-04-01", "2027-04-21"),
            (first, "s2", "2027-04-01", "2027-04-21"),
            (second, "s1", "2027-04-22", "2027-05-12"),
            (second, "s2", "2027-04-22", "2027-05-12"),
            (third, "s1", "2027-05-13", "2027-06-02"),
            (third, "s2", "2027-05-13", "2027-06-02"),
        ]
    )
    run_doc = world.db.collection(col.PLANTING_RUNS).get(first)
    assert (run_doc["planned_from"], run_doc["planned_until"], run_doc["source"]) == (
        "2027-04-01",
        "2027-04-21",
        "succession",
    )


def test_an_overlap_is_409_and_stores_no_run(world) -> None:
    occupied = make_plan(world, name="Earlier", batch_duration_days=None, end_date=D(2027, 4, 1), plants_per_batch=3)
    world.succession.generate_runs(occupied.key, tenant_key=A)  # s1-s3 from 1 April, open end
    runs_before = world.db.collection(col.PLANTING_RUNS).count()

    plan = make_plan(world)
    with pytest.raises(PlanError) as refused:
        world.succession.generate_runs(plan.key, tenant_key=A)

    assert (refused.value.status_code, refused.value.error_code) == (409, "slot.already_planned")
    assert world.db.collection(col.PLANTING_RUNS).count() == runs_before


def test_a_schedule_change_drops_the_edges_of_the_future_batches(world) -> None:
    plan = make_plan(world)
    world.succession.generate_runs(plan.key, tenant_key=A)

    world.succession.update_plan(plan.key, {"interval_days": 28}, tenant_key=A)

    assert planned_edges(world) == []
    assert world.db.collection(col.PLANTING_RUNS).count() == 3


def test_the_plan_announces_the_first_reserved_day_of_a_slot(world) -> None:
    plan = make_plan(world)
    world.succession.generate_runs(plan.key, tenant_key=A)

    view = world.plan.get_plan("site_a", tenant_key=A)

    by_key = {slot.key: slot.planned_from for slot in view.slots}
    # s1/s2 are reserved by three batches; the plan shows the first of them. s3/s4 are free.
    assert by_key == {"s1": D(2027, 4, 1), "s2": D(2027, 4, 1), "s3": None, "s4": None}


def test_another_tenants_reservation_is_neither_counted_nor_announced(world) -> None:
    # A run of tenant B on A's bed holding s1 (a legacy row across tenants): both reads take the tenant's own runs.
    world.db.collection(col.PLANTING_RUNS).insert(
        {"_key": "run_b", "tenant_key": B, "name": "B", "run_type": "monoculture", "status": "planned",
         "location_key": "bed"}
    )  # fmt: skip
    world.db.collection(col.RUN_PLANNED_AT).insert(
        {"_from": f"{col.PLANTING_RUNS}/run_b", "_to": f"{col.SLOTS}/s1", "entry_key": "e", "sequence": 1,
         "planned_from": "2027-03-01", "planned_until": None}
    )  # fmt: skip

    assert world.plan.get_plan("site_a", tenant_key=A).slots[0].planned_from is None
    plan = make_plan(world)
    _, runs = world.succession.generate_runs(plan.key, tenant_key=A)
    assert {(run_key, slot) for run_key, slot, _, _ in planned_edges(world) if run_key == runs[0].key} == {
        (runs[0].key, "s1"),
        (runs[0].key, "s2"),
    }
