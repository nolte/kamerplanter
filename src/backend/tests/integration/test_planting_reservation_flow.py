"""REQ-053 WP 3.2 (#2392) — the acceptance criteria of the reservation, end to end on a real ArangoDB.

The real services and repositories, no double between the router's service call and the database: GP-ACC-019
(a run on a bed with geometry places its slots and reservations), GP-ACC-020 (``create-plants`` stands the plants on
exactly the planned slots in ``sequence`` order), GP-ACC-021 / GP-ACC-039 (V-08 with a time window — a follow-up
crop after the window, the 409 inside it) and GP-ACC-040 (clearing a bed ends its runs and plants, archives the
slots, logs ``clearing`` and does not block the next layout).
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from types import SimpleNamespace

import pytest
from arango import ArangoClient

from app.common.enums import LayoutStrategy, PlantingRunStatus, PlantingRunType, TenantRole, TerminationType
from app.common.exceptions import NotFoundError, PlanError
from app.data_access.arango import collections as col
from app.data_access.arango.care_event_repository import ArangoCareEventRepository
from app.data_access.arango.collections import ensure_collections
from app.data_access.arango.garden_plan_repository import ArangoGardenPlanRepository
from app.data_access.arango.plant_instance_repository import ArangoPlantInstanceRepository
from app.data_access.arango.planting_reservation_repository import ArangoPlantingReservationRepository
from app.data_access.arango.planting_run_repository import ArangoPlantingRunRepository
from app.data_access.arango.site_repository import ArangoSiteRepository
from app.domain.engines.planting_run_engine import PlantingRunEngine
from app.domain.models.planting_reservation import QuickPlantingInput
from app.domain.models.planting_run import PlantingRun, PlantingRunEntry
from app.domain.services.care_event_service import CareEventService
from app.domain.services.planting_reservation_service import PlantingReservationService
from app.domain.services.planting_run_service import PlantingRunService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name
from tests.support.care_event_fakes import FakeAttachmentRepo, FakeAttachmentService, FakeFertilizers, FakeMemberships

pytestmark = pytest.mark.usefixtures("arango_db")

TEST_DATABASE = run_database_name("planting_reservation_flow")
A, B = "ten_a", "ten_b"
USER = "u_sabine"
D = date


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
        {
            "_key": "bed",
            "site_key": "site_a",
            "name": "Bed 3",
            "area_m2": 8.0,
            "geometry": {"kind": "rect", "origin": [0, 0], "width_m": 4, "length_m": 2, "rotation_deg": 0},
        }
    )
    db.collection(col.LOCATIONS).insert(
        {"_key": "bed_b", "site_key": "site_b", "name": "Bed B", "area_m2": 8.0,
         "geometry": {"kind": "rect", "origin": [0, 0], "width_m": 4, "length_m": 2, "rotation_deg": 0}}
    )  # fmt: skip
    sites = ArangoSiteRepository(db)
    plan = ArangoGardenPlanRepository(db)
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
    reservations = PlantingReservationService(reservation_repo, run_repo, sites, plan, care)
    species = {"sp": SimpleNamespace(scientific_name="Solanum lycopersicum", green_manure_suitable=False)}

    def resolver(key, *, tenant_key):
        if key not in species:
            raise NotFoundError("Species", key)
        return species[key]

    # the species must exist as a document for the entry_for_species edge's reads; the edge itself needs no vertex
    db.collection(col.SPECIES).insert({"_key": "sp", "scientific_name": "Solanum lycopersicum", "tenant_key": ""})
    service = PlantingRunService(
        run_repo,
        ArangoPlantInstanceRepository(db),
        PlantingRunEngine(),
        site_repo=sites,
        species_resolver=resolver,
        reservations=reservations,
        reservation_repo=reservation_repo,
    )
    return SimpleNamespace(db=db, service=service, reservations=reservations, plants=ArangoPlantInstanceRepository(db))


def run_of(**overrides) -> PlantingRun:
    data = {
        "name": "Tomatoes 2026",
        "run_type": PlantingRunType.MONOCULTURE,
        "location_key": "bed",
        "planned_start_date": D(2026, 5, 15),
        "planned_until": D(2026, 9, 30),
        **overrides,
    }
    return PlantingRun(**data)


def entry_of(**overrides) -> PlantingRunEntry:
    data = {
        "species_key": "sp",
        "quantity": 6,
        "id_prefix": "TOM",
        "spacing_cm": 60,
        "row_spacing_cm": 80,
        "layout_strategy": LayoutStrategy.ROWS,
        **overrides,
    }
    return PlantingRunEntry(**data)


def plantings(world, state: str | None = None, year: int | None = None):
    return world.reservations.list_plantings("bed", tenant_key=A, state=state, year=year, offset=0, limit=500)


def edges(world, collection: str) -> list[dict]:
    return list(world.db.collection(collection).all())


def test_gp_acc_019_a_run_on_a_bed_with_geometry_places_its_slots_and_reservations(world) -> None:
    run = world.service.create_run(run_of(), [entry_of()], tenant_key=A)

    planned = edges(world, col.RUN_PLANNED_AT)
    assert sorted(e["sequence"] for e in planned) == [1, 2, 3, 4, 5, 6]
    assert {e["_from"] for e in planned} == {f"planting_runs/{run.key}"}
    slots = edges(world, col.SLOTS)
    assert len(slots) == 6 and {s["slot_role"] for s in slots} == {"position"}
    assert {s["geometry_source"] for s in slots} == {"layout"}
    assert len(edges(world, col.HAS_SLOT)) == 6
    rows = plantings(world, "planned")
    assert len(rows) == 6 and {r.run_key for r in rows} == {run.key}
    assert sorted(r.sequence for r in rows if r.sequence) == [1, 2, 3, 4, 5, 6]
    assert {(r.planned_from, r.planned_until) for r in rows} == {(D(2026, 5, 15), D(2026, 9, 30))}
    assert plantings(world, "active") == []


def test_gp_acc_020_the_plants_stand_on_the_planned_slots_in_sequence_order(world) -> None:
    run = world.service.create_run(run_of(), [entry_of()], tenant_key=A)
    by_sequence = [
        e["_to"].split("/")[1] for e in sorted(edges(world, col.RUN_PLANNED_AT), key=lambda e: e["sequence"])
    ]

    result = world.service.create_plants(run.key, tenant_key=A)

    assert result["assigned_slots"] == by_sequence
    placed = {e["_from"].split("/")[1]: e["_to"].split("/")[1] for e in edges(world, col.PLACED_IN)}
    assert [placed[key] for key in result["plant_keys"]] == by_sequence
    assert plantings(world, "planned") == []
    assert len(plantings(world, "active")) == 6
    assert world.db.collection(col.PLANTING_RUNS).get(run.key)["status"] == "active"
    assert len(edges(world, col.RUN_PLANNED_AT)) == 6  # consumed reservations stay until the run ends


def test_gp_acc_021_and_039_the_time_window_decides(world) -> None:
    first = world.service.create_run(run_of(), [entry_of(quantity=2)], tenant_key=A)
    slot_keys = [e["_to"].split("/")[1] for e in edges(world, col.RUN_PLANNED_AT)]

    def second_run(start: date, until: date | None = None) -> tuple[PlantingRun, str]:
        run = world.service.create_run(
            run_of(name="Follow-up", planned_start_date=start, planned_until=until),
            [entry_of(layout_strategy=None, quantity=2)],
            tenant_key=A,
        )
        return run, world.service._repo.get_entries(run.key)[0].key  # noqa: SLF001

    # a follow-up crop after the first window is allowed (Nachkultur)
    after, after_entry = second_run(D(2026, 10, 5))
    planned = world.reservations.plan_slots(
        after.key, tenant_key=A, role=TenantRole.GROWER, entry_key=after_entry, slot_keys=slot_keys
    )
    assert [s for s, _ in planned.slots] == slot_keys

    # a run that starts inside the first window is not
    inside, inside_entry = second_run(D(2026, 8, 1))
    with pytest.raises(PlanError) as caught:
        world.reservations.plan_slots(
            inside.key, tenant_key=A, role=TenantRole.GROWER, entry_key=inside_entry, slot_keys=slot_keys
        )
    detail = caught.value.details[0]
    assert (caught.value.status_code, detail["code"], detail["conflicting_run_key"]) == (
        409,
        "slot.already_planned",
        first.key,
    )
    assert (detail["overlap_from"], detail["overlap_until"]) == ("2026-08-01", "2026-09-30")
    # nothing of the refused request was written
    assert not [e for e in edges(world, col.RUN_PLANNED_AT) if e["_from"] == f"planting_runs/{inside.key}"]

    # releasing every other reservation of the slots frees them for the run that was refused
    for run_key in (first.key, after.key):
        for slot_key in slot_keys:
            world.reservations.release_slot(run_key, slot_key, tenant_key=A, role=TenantRole.GROWER)
    world.reservations.plan_slots(
        inside.key, tenant_key=A, role=TenantRole.GROWER, entry_key=inside_entry, slot_keys=slot_keys
    )


def test_an_active_plant_blocks_a_reservation_that_starts_before_its_runs_end(world) -> None:
    first = world.service.create_run(run_of(), [entry_of(quantity=2)], tenant_key=A)
    world.service.create_plants(first.key, tenant_key=A)
    slot_keys = [e["_to"].split("/")[1] for e in edges(world, col.RUN_PLANNED_AT)]
    second = world.service.create_run(
        run_of(name="Next", planned_start_date=D(2026, 9, 1)), [entry_of(layout_strategy=None)], tenant_key=A
    )
    entry_key = world.service._repo.get_entries(second.key)[0].key  # noqa: SLF001

    with pytest.raises(PlanError) as caught:
        world.reservations.plan_slots(
            second.key, tenant_key=A, role=TenantRole.GROWER, entry_key=entry_key, slot_keys=slot_keys
        )

    assert caught.value.details[0]["conflicting_run_key"] == first.key
    assert caught.value.details[0]["overlap_until"] == "2026-09-30"


def test_gp_acc_040_clearing_a_bed_ends_its_runs_and_does_not_block_the_next_layout(world) -> None:
    for name in ("Run one", "Run two"):
        run = world.service.create_run(run_of(name=name), [entry_of()], tenant_key=A)
        world.service.create_plants(run.key, tenant_key=A)
    assert len(plantings(world, "active")) == 12

    outcome = world.reservations.clear_bed(
        "bed",
        tenant_key=A,
        user_key=USER,
        role=TenantRole.GROWER,
        termination_type=TerminationType.SENESCED,
        reason="end of season",
    )

    assert (outcome.plants_removed, outcome.runs_completed, outcome.slots_archived) == (12, 2, 12)
    assert plantings(world, "active") == []
    historical = plantings(world, "historical")
    assert len(historical) == 12 and {r.removed_on for r in historical} == {datetime.now(UTC).date()}
    assert {r["status"] for r in edges(world, col.PLANTING_RUNS)} == {PlantingRunStatus.COMPLETED.value}
    assert len([s for s in edges(world, col.SLOTS) if s.get("archived_at")]) == 12
    (event,) = edges(world, col.CARE_EVENTS)
    assert (event["category"], event["trigger"], event["location_key"], event["reason"]) == (
        "clearing",
        "system",
        "bed",
        "end of season",
    )
    assert len(edges(world, col.CARE_EVENT_FOR)) == 12
    assert edges(world, col.RUN_PLANNED_AT) == []

    # the next run in the bed, laid out as a zone over the whole bed, is not refused by the archived positions
    zone = entry_of(layout_strategy=LayoutStrategy.ZONE, spacing_cm=20, row_spacing_cm=20, quantity=100)
    next_run = world.service.create_run(
        run_of(name="Next season", planned_start_date=D(2026, 11, 1), planned_until=None), [zone], tenant_key=A
    )
    assert next_run.key
    new_zone = [s for s in edges(world, col.SLOTS) if s["slot_role"] == "zone"]
    assert len(new_zone) == 1 and new_zone[0]["capacity_plants"] == 100 and not new_zone[0].get("archived_at")


def test_a_foreign_tenant_cannot_see_or_clear_the_bed(world) -> None:
    run = world.service.create_run(run_of(), [entry_of()], tenant_key=A)
    world.service.create_plants(run.key, tenant_key=A)

    with pytest.raises(NotFoundError):
        world.reservations.list_plantings("bed", tenant_key=B, state=None, year=None, offset=0, limit=10)
    with pytest.raises(NotFoundError):
        world.reservations.clear_bed(
            "bed",
            tenant_key=B,
            user_key=USER,
            role=TenantRole.LEAD,
            termination_type=TerminationType.DIED,
            reason=None,
        )

    assert len(plantings(world, "active")) == 6  # the positive control: the owner still sees all of it
    assert edges(world, col.CARE_EVENTS) == []


def test_quick_planting_is_one_transaction_with_a_field_mode_run(world) -> None:
    result = world.service.quick_plant(
        "bed",
        tenant_key=A,
        role=TenantRole.GROWER,
        request=QuickPlantingInput(
            species_key="sp", quantity=8, layout_strategy=LayoutStrategy.GRID, spacing_cm=50, planted_on=D(2026, 5, 20)
        ),
    )

    run = world.db.collection(col.PLANTING_RUNS).get(result.run_key)
    assert (run["status"], run["source"], run["actual_quantity"], run["tenant_key"]) == ("active", "field_mode", 8, A)
    active = plantings(world, "active")
    assert len(active) == 8 and {r.run_key for r in active} == {result.run_key}
    assert len(result.created_slot_keys) == 8 and result.warnings == []
    assert {r.planted_on for r in active} == {D(2026, 5, 20)}


def test_a_foreign_tenant_cannot_reserve_release_or_plant_a_run(world) -> None:
    """GP-NFR-050 for the planting-run routes: 404, the owner's positive control, and the database unchanged."""
    import json

    run = world.service.create_run(run_of(), [entry_of(quantity=2)], tenant_key=A)
    entry_key = world.service._repo.get_entries(run.key)[0].key  # noqa: SLF001
    slot_keys = [e["_to"].split("/")[1] for e in edges(world, col.RUN_PLANNED_AT)]

    def snapshot() -> str:
        names = (col.SLOTS, col.RUN_PLANNED_AT, col.PLANTING_RUNS, col.PLANT_INSTANCES, col.PLACED_IN, col.RUN_CONTAINS)
        return json.dumps({n: sorted(map(str, world.db.collection(n).all())) for n in names}, sort_keys=True)

    before = snapshot()
    with pytest.raises(NotFoundError):
        world.reservations.plan_slots(
            run.key, tenant_key=B, role=TenantRole.LEAD, entry_key=entry_key, slot_keys=slot_keys
        )
    with pytest.raises(NotFoundError):
        world.reservations.release_slot(run.key, slot_keys[0], tenant_key=B, role=TenantRole.LEAD)
    with pytest.raises(NotFoundError):
        world.service.create_plants(run.key, tenant_key=B)
    assert snapshot() == before

    # the positive control: the owner reaches the same run through the same calls
    world.reservations.plan_slots(
        run.key, tenant_key=A, role=TenantRole.GROWER, entry_key=entry_key, slot_keys=slot_keys[:1]
    )
    assert len(world.service.create_plants(run.key, tenant_key=A)["plant_keys"]) == 2


def test_a_slot_of_another_bed_or_another_tenant_is_reference_not_found(world) -> None:
    from app.common.exceptions import PlanValidationError

    world.db.collection(col.SLOTS).insert({"_key": "slot_foreign", "slot_id": "FOREIGN_001", "location_key": "bed_b"})
    run = world.service.create_run(run_of(), [entry_of(layout_strategy=None)], tenant_key=A)
    entry_key = world.service._repo.get_entries(run.key)[0].key  # noqa: SLF001

    bodies = []
    for key in ("slot_foreign", "slot_gone"):
        with pytest.raises(PlanValidationError) as caught:
            world.reservations.plan_slots(
                run.key, tenant_key=A, role=TenantRole.GROWER, entry_key=entry_key, slot_keys=[key]
            )
        assert caught.value.codes == ["reference.not_found"]
        bodies.append(str(caught.value.details).replace(key, "<key>"))
    assert bodies[0] == bodies[1]  # foreign and absent read alike
    assert edges(world, col.RUN_PLANNED_AT) == []
