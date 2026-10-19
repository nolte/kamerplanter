"""REQ-053 WP 3.2 — what ``PlantingRunService`` does with slots: the layout at create (GP-API-020), the planned
slots at ``create-plants`` (GP-API-023, GP-FR-066), the ending of a run's reservations, and quick planting
(GP-API-017, GP-UX-027).

Pinned: GP-ACC-019 (six slots, ``sequence 1..6``), GP-ACC-020 (plants on exactly the planned slots in
``sequence`` order), the surplus reservations that stay, a free-slot fallback that keeps off other runs'
reservations, the compensation of a failed layout, ``quantity <= 500`` and ``source = field_mode``.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.common.enums import (
    LayoutStrategy,
    PlanRole,
    PlantingRunStatus,
    PlantingRunType,
    SlotRole,
    TenantRole,
)
from app.common.exceptions import ForbiddenError, NotFoundError, PlanError, PlanValidationError
from app.domain.engines.slot_reservation_engine import ActivePlant, Reservation
from app.domain.models.planting_reservation import QuickPlantingInput
from app.domain.models.planting_run import PlantingRun, PlantingRunEntry
from app.domain.models.site import Slot
from tests.support.garden_plan_fakes import (
    OTHER_TENANT,
    TENANT,
    make_location,
    make_site,
    rect,
)
from tests.support.planting_reservation_fakes import build_world

D = date
GROWER = TenantRole.GROWER


@pytest.fixture
def world():
    return build_world()


def tomato_entry(**overrides) -> PlantingRunEntry:
    data = {
        "species_key": "sp_tomato",
        "quantity": 6,
        "id_prefix": "TOM",
        "spacing_cm": 60,
        "row_spacing_cm": 80,
        "layout_strategy": LayoutStrategy.ROWS,
        **overrides,
    }
    return PlantingRunEntry(**data)


def new_run(**overrides) -> PlantingRun:
    data = {
        "name": "Tomatoes 2026",
        "run_type": PlantingRunType.MONOCULTURE,
        "location_key": "bed",
        "planned_start_date": D(2026, 5, 15),
        "planned_until": D(2026, 9, 30),
        **overrides,
    }
    return PlantingRun(**data)


class TestCreateRunLayout:
    def test_a_bed_with_geometry_gets_slots_and_reservations(self, world) -> None:
        """GP-ACC-019: six positions with ``run_planned_at`` edges ``sequence 1..6`` and the run's window."""
        run = world.service.create_run(new_run(), [tomato_entry()], tenant_key=TENANT)

        (write,) = world.repo.layout_writes
        assert write.run_key == run.key
        assert (write.planned_from, write.planned_until) == (D(2026, 5, 15), D(2026, 9, 30))
        assert [s.sequence for s in write.slots] == [1, 2, 3, 4, 5, 6]
        assert {s.slot.slot_role for s in write.slots} == {SlotRole.POSITION}
        stored_entry = next(iter(world.runs.entries.values()))
        assert {s.entry_key for s in write.slots} == {stored_entry.key}
        assert run.planned_from == D(2026, 5, 15)  # the window starts with the run

    def test_the_window_can_be_set_apart_from_the_start_date(self, world) -> None:
        world.service.create_run(
            new_run(planned_from=D(2026, 5, 1), planned_until=None), [tomato_entry()], tenant_key=TENANT
        )

        (write,) = world.repo.layout_writes
        assert (write.planned_from, write.planned_until) == (D(2026, 5, 1), None)

    @pytest.mark.parametrize(
        "run_overrides",
        [{"location_key": "bed_nogeo"}, {"location_key": None}],
        ids=["bed without geometry", "no location"],
    )
    def test_without_a_bed_with_geometry_the_run_is_stored_as_before(self, world, run_overrides) -> None:
        run = world.service.create_run(new_run(**run_overrides), [tomato_entry()], tenant_key=TENANT)

        assert run.key in world.runs.runs
        assert world.repo.layout_writes == []

    @pytest.mark.parametrize("strategy", [None, LayoutStrategy.FREE])
    def test_an_entry_without_a_layout_or_with_free_places_nothing(self, world, strategy) -> None:
        world.service.create_run(new_run(), [tomato_entry(layout_strategy=strategy)], tenant_key=TENANT)

        assert world.repo.layout_writes == []

    def test_a_refused_layout_stores_no_run(self, world) -> None:
        with pytest.raises(PlanError) as caught:
            world.service.create_run(new_run(), [tomato_entry(spacing_cm=None)], tenant_key=TENANT)

        assert caught.value.error_code == "layout.spacing_required"
        assert world.runs.runs == {}

    def test_a_failed_slot_write_takes_the_run_back(self, world) -> None:
        def explode(write):
            raise RuntimeError("write conflict")

        world.repo.place_run_layout = explode

        with pytest.raises(RuntimeError):
            world.service.create_run(new_run(), [tomato_entry()], tenant_key=TENANT)

        assert world.runs.deleted == ["run_1"]
        assert world.runs.runs == {}

    def test_another_tenants_bed_is_404_and_nothing_is_stored(self, world) -> None:
        with pytest.raises(NotFoundError):
            world.service.create_run(new_run(location_key="loc_foreign"), [tomato_entry()], tenant_key=TENANT)

        assert world.runs.runs == {} and world.repo.layout_writes == []

    def test_green_manure_needs_a_species_suited_as_green_manure(self, world) -> None:
        with pytest.raises(PlanError) as caught:
            world.service.create_run(new_run(plan_role=PlanRole.GREEN_MANURE), [tomato_entry()], tenant_key=TENANT)
        assert caught.value.error_code == "run.species_not_green_manure"

        green = tomato_entry(species_key="sp_phacelia", layout_strategy=None)
        assert world.service.create_run(new_run(plan_role=PlanRole.GREEN_MANURE), [green], tenant_key=TENANT)


class TestCreatePlantsOnPlannedSlots:
    def planned_run(self, world, *, slot_order=("s3", "s1", "s2"), quantity=2) -> str:
        """A planned run with three reserved slots, reserved in a deliberate non-alphabetical ``sequence``."""
        world.plan.slots = [
            Slot(_key=key, slot_id=f"BED3_{n:03d}", location_key="bed") for n, key in enumerate(("s1", "s2", "s3"), 1)
        ]
        run = world.service.create_run(
            new_run(), [tomato_entry(layout_strategy=None, quantity=quantity)], tenant_key=TENANT
        )
        entry = next(iter(world.runs.entries.values()))
        world.repo.reservations = [
            Reservation(slot, run.key, entry.key, "sp_tomato", sequence, D(2026, 5, 15), D(2026, 9, 30))
            for sequence, slot in enumerate(slot_order, 1)
        ]
        return run.key

    def test_the_plants_stand_on_the_reserved_slots_in_sequence_order(self, world) -> None:
        """GP-ACC-020 / GP-FR-066."""
        run_key = self.planned_run(world)

        result = world.service.create_plants(run_key, tenant_key=TENANT)

        assert [p.slot_key for p in world.plants.created] == ["s3", "s1"]  # sequence 1, 2 — not slot_id order
        assert result["assigned_slots"] == ["s3", "s1"]
        assert result["slots_assigned"] == 2
        assert world.runs.runs[run_key].status is PlantingRunStatus.ACTIVE

    @pytest.mark.parametrize("assign", [True, False])
    def test_the_plants_carry_the_beds_location_and_garden(self, world, assign) -> None:
        """Every bed read finds a bed's plants by ``location_key`` (plant states, the ``position_corrected`` plant
        check), so a plant created here names its bed and garden as a quick-planted one does - with or without a
        slot. Found by the wave-3 E2E (#2398): the plants stood on their slots but were invisible to the bed."""
        run_key = self.planned_run(world)

        world.service.create_plants(run_key, tenant_key=TENANT, assign_to_slots=assign)

        assert {(p.location_key, p.site_key) for p in world.plants.created} == {
            ("bed", world.plan.locations["bed"].site_key)
        }

    def test_moving_an_active_run_moves_its_plants_to_the_new_bed(self, world) -> None:
        """A run moved to another location (``PATCH`` ``location_key``) takes its plants along: slot, bed and
        garden. Before, only ``slot_key`` followed, so the moved plants still named the old bed."""
        # A second garden of the same tenant: the move has to carry the site along, not only the bed.
        world.sites.sites["site_2"] = make_site().model_copy(update={"key": "site_2"})
        world.plan.locations["bed2"] = make_location("bed2", name="Bed 4", geometry=rect(0, 0, 2, 1)).model_copy(
            update={"site_key": "site_2"}
        )
        world.plan.slots = [Slot(_key="n1", slot_id="BED4_001", location_key="bed2")]
        run = world.service.create_run(
            new_run(planned_until=None), [tomato_entry(layout_strategy=None, quantity=2)], tenant_key=TENANT
        )
        world.service.create_plants(run.key, tenant_key=TENANT, assign_to_slots=False)

        world.service.update_run(run.key, {"location_key": "bed2"}, tenant_key=TENANT)

        assert [(p.location_key, p.site_key, p.slot_key) for p in world.plants.created] == [
            ("bed2", "site_2", "n1"),  # onto the new bed's free slot
            ("bed2", "site_2", None),  # more plants than slots: in the bed, without a position
        ]

    def test_the_surplus_reservation_stays(self, world) -> None:
        run_key = self.planned_run(world)

        world.service.create_plants(run_key, tenant_key=TENANT)

        assert [(r.run_key, r.slot_key) for r in world.repo.reservations] == [
            (run_key, "s3"),
            (run_key, "s1"),
            (run_key, "s2"),
        ]  # s2 stays reserved until the run ends or the grower releases it

    def test_without_assign_to_slots_the_plants_get_no_slot(self, world) -> None:
        run_key = self.planned_run(world)

        result = world.service.create_plants(run_key, tenant_key=TENANT, assign_to_slots=False)

        assert [p.slot_key for p in world.plants.created] == [None, None]
        assert result["assigned_slots"] == [] and result["slots_assigned"] == 0

    def test_the_planting_date_is_the_callers(self, world) -> None:
        run_key = self.planned_run(world)

        world.service.create_plants(run_key, tenant_key=TENANT, planted_on=D(2026, 5, 20))

        assert {p.planted_on for p in world.plants.created} == {D(2026, 5, 20)}

    def test_plants_beyond_the_reservation_fall_back_to_free_slots_but_not_to_reserved_ones(self, world) -> None:
        run_key = self.planned_run(world, slot_order=("s1",), quantity=3)
        world.repo.reservations.append(Reservation("s3", "run_other", "e_x", "sp", 1, D(2027, 1, 1), None))

        world.service.create_plants(run_key, tenant_key=TENANT)

        # s1 is the run's own; s2 is free; s3 is another live run's and is never taken as a "free" slot
        assert [p.slot_key for p in world.plants.created] == ["s1", "s2", None]

    def test_the_fallback_keeps_off_the_slots_the_run_reserved_for_another_entry(self, world) -> None:
        world.plan.slots = [
            Slot(_key=key, slot_id=f"BED3_{n:03d}", location_key="bed")
            for n, key in enumerate(("s1", "s2", "s3", "s4"), 1)
        ]
        # a run with two entries is stored directly: the monoculture rule of create_run would refuse it
        run = world.runs.create(new_run().model_copy(update={"tenant_key": TENANT}))
        for quantity in (3, 1):
            world.runs.create_entry(
                tomato_entry(layout_strategy=None, quantity=quantity).model_copy(
                    update={"run_key": run.key, "tenant_key": TENANT}
                )
            )
        world.service._engine.validate_run_type_constraints = lambda *args, **kwargs: None  # noqa: SLF001
        first, second = sorted(world.runs.entries.values(), key=lambda e: e.key)
        world.repo.reservations = [
            Reservation("s2", run.key, first.key, "sp_tomato", 1, D(2026, 5, 15), None),
            Reservation("s1", run.key, second.key, "sp_tomato", 1, D(2026, 5, 15), None),
        ]

        world.service.create_plants(run.key, tenant_key=TENANT)

        # entry one: its reserved s2, then a *free* slot (s3, s4) — never entry two's reserved s1
        assert [p.slot_key for p in world.plants.created][:3] == ["s2", "s3", "s4"]
        assert world.plants.created[3].slot_key == "s1"

    def test_a_position_slot_still_holding_an_earlier_runs_plant_is_skipped(self, world) -> None:
        run_key = self.planned_run(world, slot_order=("s1", "s2"))
        world.repo.plants.append(ActivePlant("s1", "pi_old", "run_old", D(2026, 5, 10)))

        world.service.create_plants(run_key, tenant_key=TENANT)

        assert world.plants.created[0].slot_key != "s1"

    def test_an_archived_slot_is_never_a_place_to_plant_again(self, world) -> None:
        from datetime import UTC, datetime

        world.plan.slots = [
            Slot(_key="old", slot_id="BED3_001", location_key="bed", archived_at=datetime(2026, 1, 1, tzinfo=UTC)),
            Slot(_key="new", slot_id="BED3_002", location_key="bed"),
        ]
        run = world.service.create_run(new_run(), [tomato_entry(layout_strategy=None, quantity=1)], tenant_key=TENANT)

        world.service.create_plants(run.key, tenant_key=TENANT)

        assert [p.slot_key for p in world.plants.created] == ["new"]

    def test_a_zone_slot_takes_up_to_its_capacity(self, world) -> None:
        world.plan.slots = [
            Slot(_key="z", slot_id="BED3_Z", location_key="bed", slot_role=SlotRole.ZONE, capacity_plants=3)
        ]
        run = world.service.create_run(new_run(), [tomato_entry(layout_strategy=None, quantity=4)], tenant_key=TENANT)
        entry = next(iter(world.runs.entries.values()))
        world.repo.reservations = [Reservation("z", run.key, entry.key, "sp_tomato", 1, D(2026, 5, 15), None)]

        world.service.create_plants(run.key, tenant_key=TENANT)

        assert [p.slot_key for p in world.plants.created] == ["z", "z", "z", None]
        assert world.slot_updates == [("z", True)]  # the slot is marked once, not per plant


class TestEndingARun:
    def test_deleting_a_planned_run_drops_its_reservations_and_layout_slots(self, world) -> None:
        run = world.service.create_run(new_run(), [tomato_entry()], tenant_key=TENANT)

        world.service.delete_run(run.key, tenant_key=TENANT)

        assert world.repo.dropped == [(run.key, True)]
        assert world.runs.deleted == [run.key]

    def test_a_run_of_another_tenant_is_not_touched(self, world) -> None:
        run = world.service.create_run(new_run(), [tomato_entry()], tenant_key=TENANT)

        with pytest.raises(NotFoundError):
            world.service.delete_run(run.key, tenant_key=OTHER_TENANT)

        assert world.repo.dropped == []

    def test_a_reserved_run_keeps_its_bed(self, world) -> None:
        run = world.service.create_run(new_run(), [tomato_entry()], tenant_key=TENANT)

        with pytest.raises(PlanError) as caught:
            world.service.update_run(run.key, {"location_key": "bed_nogeo"}, tenant_key=TENANT)

        assert caught.value.error_code == "run.reserved_bed_fixed"

    def test_an_unreserved_run_moves_its_window_with_its_start_date(self, world) -> None:
        run = world.service.create_run(
            new_run(planned_until=None), [tomato_entry(layout_strategy=None)], tenant_key=TENANT
        )
        assert run.planned_from == D(2026, 5, 15)

        moved = world.service.update_run(run.key, {"planned_start_date": D(2026, 6, 1)}, tenant_key=TENANT)

        assert (moved.planned_start_date, moved.planned_from) == (D(2026, 6, 1), D(2026, 6, 1))

    def test_a_window_that_was_set_apart_stays_where_it_is(self, world) -> None:
        run = world.service.create_run(
            new_run(planned_from=D(2026, 5, 1), planned_until=None),
            [tomato_entry(layout_strategy=None)],
            tenant_key=TENANT,
        )

        moved = world.service.update_run(run.key, {"planned_start_date": D(2026, 6, 1)}, tenant_key=TENANT)

        assert moved.planned_from == D(2026, 5, 1)

    def test_a_start_after_the_end_of_the_window_is_422(self, world) -> None:
        run = world.service.create_run(new_run(), [tomato_entry(layout_strategy=None)], tenant_key=TENANT)

        with pytest.raises(PlanError) as caught:
            world.service.update_run(run.key, {"planned_start_date": D(2026, 12, 1)}, tenant_key=TENANT)

        assert caught.value.error_code == "run.window_reversed"

    def test_a_reserved_run_keeps_its_start_date(self, world) -> None:
        run = world.service.create_run(new_run(), [tomato_entry()], tenant_key=TENANT)

        with pytest.raises(PlanError) as caught:
            world.service.update_run(run.key, {"planned_start_date": D(2026, 6, 1)}, tenant_key=TENANT)
        assert caught.value.error_code == "run.reserved_window_fixed"

        # the same date, or any other field, is no move of the window
        world.service.update_run(run.key, {"planned_start_date": D(2026, 5, 15), "name": "Renamed"}, tenant_key=TENANT)


class TestQuickPlanting:
    def request(self, **overrides) -> QuickPlantingInput:
        data = {"species_key": "sp_tomato", "quantity": 4, **overrides}
        return QuickPlantingInput(**data)

    def plant(self, world, location="bed", **overrides):
        return world.service.quick_plant(location, tenant_key=TENANT, role=GROWER, request=self.request(**overrides))

    def test_run_slots_and_plants_are_one_write(self, world) -> None:
        result = self.plant(world, layout_strategy=LayoutStrategy.GRID, spacing_cm=50)

        (write,) = world.repo.quick_writes
        run = write.run
        assert (run.status, run.source, run.plan_role) == (PlantingRunStatus.ACTIVE, "field_mode", PlanRole.MAIN_CROP)
        assert (run.planned_quantity, run.actual_quantity, run.location_key) == (4, 4, "bed")
        assert len(write.plants) == 4 and len(write.slots) == 4
        assert [p.slot_index for p in write.plants] == [0, 1, 2, 3]
        assert all(s.currently_occupied for s in write.slots)
        assert len(result.plant_keys) == 4 and len(result.created_slot_keys) == 4
        assert result.warnings == []

    def test_the_plants_name_the_bed_so_that_an_unplaced_one_is_still_the_beds(self, world) -> None:
        self.plant(world)

        (write,) = world.repo.quick_writes
        assert {p.plant.location_key for p in write.plants} == {"bed"}
        assert {p.plant.site_key for p in write.plants} == {"site_1"}
        assert {p.plant.tenant_key for p in write.plants} == {TENANT}

    def test_without_a_layout_the_plants_are_recorded_without_positions(self, world) -> None:
        result = self.plant(world)

        (write,) = world.repo.quick_writes
        assert write.slots == [] and {p.slot_index for p in write.plants} == {None}
        assert result.created_slot_keys == []

    def test_a_layout_on_a_bed_without_geometry_warns(self, world) -> None:
        result = self.plant(world, "bed_nogeo", layout_strategy=LayoutStrategy.GRID, spacing_cm=50)

        assert result.warnings == ["layout.bed_without_geometry"]
        assert world.repo.quick_writes[0].slots == []

    def test_plants_beyond_what_the_bed_holds_are_recorded_without_a_position(self, world) -> None:
        result = self.plant(world, quantity=40, layout_strategy=LayoutStrategy.GRID, spacing_cm=100)

        (write,) = world.repo.quick_writes
        placed = [p for p in write.plants if p.slot_index is not None]
        assert 0 < len(placed) < 40
        assert len(write.plants) == 40
        assert "layout.capacity_exceeded" in result.warnings

    def test_the_instance_ids_follow_the_species(self, world) -> None:
        result = self.plant(world)
        assert result.instance_ids[0] == "bed_SOL_01"

    def test_more_than_500_plants_are_422_at_the_model(self) -> None:
        with pytest.raises(ValueError):
            self.request(quantity=501)

    @pytest.mark.parametrize("strategy", [LayoutStrategy.ZONE, LayoutStrategy.FREE])
    def test_zone_and_free_are_no_quick_layouts(self, strategy) -> None:
        with pytest.raises(ValueError):
            self.request(layout_strategy=strategy, spacing_cm=40)

    def test_a_viewer_may_not_plant(self, world) -> None:
        with pytest.raises(ForbiddenError):
            world.service.quick_plant("bed", tenant_key=TENANT, role=TenantRole.VIEWER, request=self.request())

        assert world.repo.quick_writes == []

    def test_another_tenants_bed_is_404_and_nothing_is_written(self, world) -> None:
        with pytest.raises(NotFoundError):
            world.service.quick_plant("loc_foreign", tenant_key=TENANT, role=GROWER, request=self.request())
        with pytest.raises(NotFoundError):
            world.service.quick_plant("bed", tenant_key=OTHER_TENANT, role=GROWER, request=self.request())

        assert world.repo.quick_writes == []

    def test_a_species_the_tenant_may_not_read_is_422_reference_not_found(self, world) -> None:
        with pytest.raises(PlanValidationError) as caught:
            self.plant(world, species_key="sp_unknown")

        assert (caught.value.codes, caught.value.details[0]["field"]) == (["reference.not_found"], "species_key")
        assert world.repo.quick_writes == []

    def test_a_fallow_run_does_not_exist(self) -> None:
        with pytest.raises(ValueError):
            self.request(plan_role=PlanRole.FALLOW)

    def test_a_green_manure_run_needs_a_green_manure_species(self, world) -> None:
        with pytest.raises(PlanError):
            self.plant(world, plan_role=PlanRole.GREEN_MANURE)
        assert world.repo.quick_writes == []
        self.plant(world, species_key="sp_phacelia", plan_role=PlanRole.GREEN_MANURE)
        assert world.repo.quick_writes[0].run.plan_role is PlanRole.GREEN_MANURE
