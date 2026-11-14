"""REQ-053 W-015 (Anhang A 60, #2830) — sown → thinned → n plants, end to end on a real ArangoDB.

The real services and repositories, no double between the service call and the database: a row slot of the bed is
reserved by a planned run, recorded as sown (``PUT /slots/{key}/sowing``'s service), reported by the plant-state read
as lifecycle ``sown``, and thinned into the plants the row holds at the run's ``thinning_to_cm`` — afterwards
``sown_at`` is empty, the plants stand in the slot as plants of the run, the run is ``active`` and a ``thinning`` care
event names them. Another tenant reaches neither the slot nor the sown state (404).
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

import pytest
from arango import ArangoClient

from app.common.datetimes import today_utc
from app.common.enums import PlantingRunStatus, PlantingRunType, TenantRole, TerminationType
from app.common.exceptions import NotFoundError, PlanError, WriteConflictError
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
from app.domain.models.care_event import CareEvent
from app.domain.models.planting_reservation import ClearBedWrite, SlotThinningInput, SlotThinningWrite
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
        reservation_repo=reservation_repo,
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


def _thin(world):
    return world.thinning.thin_slot(
        "row1", tenant_key=A, user_key=USER, role=TenantRole.GROWER, request=SlotThinningInput()
    )


def _before_the_write(world, monkeypatch, step) -> None:
    """Run ``step`` after the service decided and before the transaction: what a concurrent writer does."""
    original = world.reservation_repo.thin_sown_slot

    def racing(write):
        step()
        return original(write)

    monkeypatch.setattr(world.reservation_repo, "thin_sown_slot", racing)


def test_a_reservation_released_between_read_and_write_is_a_conflict(world, monkeypatch) -> None:
    """SEC-001: the transaction re-reads the run's reservation of the slot after the bed lock."""
    sow(world)
    _before_the_write(world, monkeypatch, lambda: world.db.collection(col.RUN_PLANNED_AT).truncate())

    with pytest.raises(PlanError) as caught:
        _thin(world)

    assert caught.value.status_code == 409
    assert list(world.db.collection(col.PLANT_INSTANCES).all()) == []
    assert world.db.collection(col.SLOTS).get("row1")["sown_at"] is not None


def test_a_run_started_meanwhile_is_not_started_again(world, monkeypatch) -> None:
    """SEC-002: the activation is decided on the run the transaction sees, and only then a run phase row is written."""
    sow(world)

    def start_run() -> None:
        world.db.collection(col.PLANTING_RUNS).update({"_key": world.run_key, "status": "active"})

    _before_the_write(world, monkeypatch, start_run)

    outcome = _thin(world)

    assert outcome.run_started is False
    run = world.db.collection(col.PLANTING_RUNS).get(world.run_key)
    assert run.get("started_at") is None  # the started run is not re-stamped
    owners = {row["plant_instance_key"] for row in world.db.collection(col.PHASE_HISTORIES).all()}
    assert world.run_key not in owners


def test_a_planned_run_is_started_once(world) -> None:
    sow(world)
    outcome = _thin(world)
    assert outcome.run_started is True
    run = world.db.collection(col.PLANTING_RUNS).get(world.run_key)
    assert run["status"] == "active"


def test_an_instance_id_taken_meanwhile_is_a_conflict_not_a_500(world, monkeypatch) -> None:
    """SEC-003: the per-tenant unique instance id, taken after the ids were chosen, answers 409 and writes nothing."""
    sow(world)

    def take_the_first_id() -> None:
        world.db.collection(col.PLANT_INSTANCES).insert(
            {"_key": "squatter", "tenant_key": A, "instance_id": "bed_DAU_01", "species_key": "sp_carrot"}
        )

    _before_the_write(world, monkeypatch, take_the_first_id)

    with pytest.raises(PlanError) as caught:
        _thin(world)

    assert caught.value.status_code == 409
    assert [p["_key"] for p in world.db.collection(col.PLANT_INSTANCES).all()] == ["squatter"]
    assert world.db.collection(col.SLOTS).get("row1")["sown_at"] is not None


def test_a_foreign_private_species_lends_the_sown_slot_no_name(world) -> None:
    """SEC-005: the sown entry names only a species the tenant may read (global or its own)."""
    world.db.collection(col.SPECIES).insert(
        {"_key": "sp_secret", "scientific_name": "Secretus privatus", "common_names": ["Secret"], "tenant_key": B}
    )
    world.db.aql.execute(
        "FOR e IN @@edges UPDATE e WITH {planned_species_key: 'sp_secret'} IN @@edges",
        bind_vars={"@edges": col.RUN_PLANNED_AT},
    )
    sow(world)

    (sown,) = ArangoPlantStateRepository(world.db).list_sown_slots("bed", tenant_key=A)

    assert sown.species_key == "sp_secret"
    assert (sown.species_name, sown.scientific_name, sown.cultivar_name) == (None, None, None)


def test_a_position_slot_is_never_marked_sown_by_the_repository(world) -> None:
    """SEC-006: the write itself is limited to rows and zones, not only the service's check."""
    world.db.collection(col.SLOTS).update({"_key": "row1", "slot_role": "position"})

    assert not world.reservation_repo.mark_slot_sown("bed", "row1", sown_at=today_utc(), tenant_key=A)
    assert world.db.collection(col.SLOTS).get("row1").get("sown_at") is None


# ── #2862: a zone above the quota becomes a target stand (REQ-053 §11.1 step 7, §11.3 "Zonen-Bestand") ──

#: 0.5 m² of zone; thinned to 2 cm on the square grid it holds 1 250 seedlings - more than one write takes (500).
ZONE = {"kind": "polygon", "points": [[0.2, 0.2], [1.2, 0.2], [1.2, 0.7], [0.2, 0.7]]}


def _sown_zone(world) -> None:
    # merge=False replaces the row's geometry object: a merge would keep the polyline's ``width_m`` on the polygon,
    # a geometry the Slot model refuses to load.
    world.db.collection(col.SLOTS).update({"_key": "row1", "slot_role": "zone", "geometry": ZONE}, merge=False)
    sow(world)


def _thin_zone(world, **request):
    return world.thinning.thin_slot(
        "row1",
        tenant_key=A,
        user_key=USER,
        role=TenantRole.GROWER,
        request=SlotThinningInput(thinning_to_cm=2.0, row_spacing_cm=None, **request),
    )


def test_a_zone_above_the_quota_records_the_target_stand_and_no_plant(world) -> None:
    _sown_zone(world)
    sown_at = (today_utc() - timedelta(days=14)).isoformat()

    outcome = _thin_zone(world)

    assert (outcome.plant_keys, outcome.stand_quantity) == ([], 1_250)
    assert list(world.db.collection(col.PLANT_INSTANCES).all()) == []
    assert list(world.db.collection(col.PLACED_IN).all()) == []
    slot = world.db.collection(col.SLOTS).get("row1")
    assert (slot["sown_at"], slot["thinned_at"], slot["currently_occupied"]) == (
        sown_at,
        today_utc().isoformat(),
        True,
    )
    run = world.db.collection(col.PLANTING_RUNS).get(world.run_key)
    assert (run["status"], run["actual_quantity"]) == ("active", 1_250)
    entry = world.db.collection(col.PLANTING_RUN_ENTRIES).all().next()
    assert entry["quantity"] == 1  # the planned amount stays
    (event,) = [e for e in world.db.collection(col.CARE_EVENTS).all() if e["category"] == "thinning"]
    assert event["plant_keys"] == []  # the whole bed (GP-FR-100)

    # The plan shows the zone stand, standing, in the place of the sown entry; the planting list names the day.
    (state,) = world.states.list_plant_states("bed", tenant_key=A, now=datetime.now(UTC))
    assert (state.state.lifecycle, state.source.slot_key, state.source.thinned_at) == ("active", "row1", today_utc())
    (planned,) = world.reservations.list_plantings("bed", tenant_key=A, state="planned", year=None, offset=0, limit=50)
    assert planned.thinned_at == today_utc()


def test_a_zone_stand_keeps_the_slot_taken(world) -> None:
    _sown_zone(world)
    _thin_zone(world)

    (stand,) = world.reservation_repo.active_plants_in(["row1"], tenant_key=A)
    assert (stand.stand, stand.plant_key, stand.run_key, stand.expected_end) == (True, "", None, None)
    # The stand is anchored on the bed's site: another tenant sees nothing of it.
    assert world.reservation_repo.active_plants_in(["row1"], tenant_key=B) == []
    # Neither a second thinning nor a new sowing takes the slot; the repository refuses as well as the service.
    with pytest.raises(PlanError) as caught:
        _thin_zone(world)
    assert caught.value.status_code == 409
    with pytest.raises(PlanError):
        sow(world)
    assert not world.reservation_repo.mark_slot_sown("bed", "row1", sown_at=today_utc(), tenant_key=A)
    run = world.db.collection(col.PLANTING_RUNS).get(world.run_key)
    assert run["actual_quantity"] == 1_250


def test_up_to_the_quota_a_zone_still_gets_its_plants(world) -> None:
    _sown_zone(world)

    outcome = _thin_zone(world, count=500)

    assert (len(outcome.plant_keys), outcome.stand_quantity) == (500, None)
    slot = world.db.collection(col.SLOTS).get("row1")
    assert slot["sown_at"] is None
    assert slot.get("thinned_at") is None


def test_clearing_the_bed_ends_the_zone_stand(world) -> None:
    _sown_zone(world)
    _thin_zone(world)

    world.reservations.clear_bed(
        "bed",
        tenant_key=A,
        user_key=USER,
        role=TenantRole.GROWER,
        termination_type=TerminationType.HARVESTED,
        reason=None,
    )

    slot = world.db.collection(col.SLOTS).get("row1")
    assert slot.get("thinned_at") is None or slot.get("archived_at") is not None
    assert world.reservation_repo.active_plants_in(["row1"], tenant_key=A) == []


# ── #2862 SEC-001/SEC-002: the repository writes anchor the tenant themselves ──
# Each test calls the repository directly with a foreign tenant - the service's ``resolve_owned_slot`` is bypassed on
# purpose. The bed belongs to tenant A (site_a); tenant B owns site_b only.


def _foreign_run_reserving_row1(world) -> str:
    """A live run of tenant B with a reservation of A's slot - the state a bypassed service check would act on."""
    world.db.collection(col.PLANTING_RUNS).insert(
        {"_key": "run_b", "tenant_key": B, "name": "B", "run_type": "monoculture", "status": "planned"}
    )
    world.db.collection(col.RUN_PLANNED_AT).insert(
        {"_from": "planting_runs/run_b", "_to": "slots/row1", "entry_key": "e_b", "planned_species_key": "sp_carrot",
         "sequence": 1, "planned_from": (today_utc() - timedelta(days=30)).isoformat()}
    )  # fmt: skip
    return "run_b"


def _thinning_write(world, *, tenant_key: str, run_key: str, entry_key: str, stand: int | None = None):
    sown_at = date.fromisoformat(world.db.collection(col.SLOTS).get("row1")["sown_at"])
    event = CareEvent(
        tenant_key=tenant_key,
        site_key="site_b",
        location_key="bed",
        category="thinning",
        performed_at=datetime.now(UTC),
        trigger="system",
    )
    return SlotThinningWrite(
        location_key="bed",
        slot_key="row1",
        sown_at=sown_at,
        run_key=run_key,
        entry_key=entry_key,
        tenant_key=tenant_key,
        plants=[],
        event=event,
        phase_started_at=datetime.now(UTC),
        stand_quantity=stand,
        thinned_on=today_utc() if stand is not None else None,
    )


def test_the_repository_does_not_sow_a_foreign_tenants_slot(world) -> None:
    assert not world.reservation_repo.mark_slot_sown("bed", "row1", sown_at=today_utc(), tenant_key=B)
    assert world.db.collection(col.SLOTS).get("row1").get("sown_at") is None


@pytest.mark.parametrize("stand", [None, 1_250])
def test_the_repository_does_not_thin_a_foreign_tenants_slot(world, stand) -> None:
    _sown_zone(world)
    run_key = _foreign_run_reserving_row1(world)

    with pytest.raises(WriteConflictError):
        world.reservation_repo.thin_sown_slot(
            _thinning_write(world, tenant_key=B, run_key=run_key, entry_key="e_b", stand=stand)
        )

    slot = world.db.collection(col.SLOTS).get("row1")
    assert slot["sown_at"] is not None
    assert slot.get("thinned_at") is None
    assert world.db.collection(col.PLANTING_RUNS).get(run_key).get("actual_quantity") in (None, 0)
    assert [e for e in world.db.collection(col.CARE_EVENTS).all() if e["category"] == "thinning"] == []


def test_a_foreign_or_ended_run_thins_nothing(world) -> None:
    """Fail closed for a run of another tenant or one that ended: nothing is written.

    The outcome alone cannot tell *which* check refused: the run count (``_COUNT_THINNED_PLANTS``) filters tenant and
    status too, and an aborted transaction leaves no trace of how far it got. That ``_RESERVATION_STILL_HELD`` checks
    the run before the first write is pinned on the query text in
    ``tests/unit/data_access/arango/test_slot_write_queries_anchor_the_tenant.py``.
    """
    _sown_zone(world)
    entry_key = world.db.collection(col.RUN_PLANNED_AT).all().next()["entry_key"]

    # A's own run, named under B: refused before the first write.
    with pytest.raises(WriteConflictError):
        world.reservation_repo.thin_sown_slot(
            _thinning_write(world, tenant_key=B, run_key=world.run_key, entry_key=entry_key, stand=1_250)
        )
    # A's run, ended meanwhile: refused as well.
    world.db.collection(col.PLANTING_RUNS).update({"_key": world.run_key, "status": "completed"})
    with pytest.raises(WriteConflictError):
        world.reservation_repo.thin_sown_slot(
            _thinning_write(world, tenant_key=A, run_key=world.run_key, entry_key=entry_key, stand=1_250)
        )
    assert world.db.collection(col.SLOTS).get("row1").get("thinned_at") is None


def test_clearing_under_a_foreign_tenant_leaves_the_zone_stand(world) -> None:
    _sown_zone(world)
    _thin_zone(world)

    world.reservation_repo.clear_bed(
        ClearBedWrite(
            location_key="bed",
            tenant_key=B,
            termination_type="harvested",
            removed_on=today_utc(),
            event=CareEvent(
                tenant_key=B,
                site_key="site_b",
                location_key="bed",
                category="clearing",
                performed_at=datetime.now(UTC),
                trigger="system",
            ),
        )
    )

    slot = world.db.collection(col.SLOTS).get("row1")
    assert slot["thinned_at"] == today_utc().isoformat()
    assert slot.get("archived_at") is None
    assert [s.stand for s in world.reservation_repo.active_plants_in(["row1"], tenant_key=A)] == [True]
