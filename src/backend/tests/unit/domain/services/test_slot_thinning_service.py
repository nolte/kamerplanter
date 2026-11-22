"""REQ-053 W-015 (Anhang A 60) — sowing a row or zone slot and thinning it into plants of its run.

The real :class:`SlotThinningService`, :class:`PlantingRunService` and :class:`CareEventService` over the in-memory
world of ``tests/support/planting_reservation_fakes.py``. What these tests prove is the service's decision: the count
from the slot's measure and the run's spacing (no default, E-10), ownership through the slot's bed, the role gate, and
the write set handed to the repository. The transaction itself is proven against ArangoDB in
``tests/integration/test_slot_thinning_flow.py``.
"""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.common.datetimes import today_utc
from app.common.enums import PlantingRunStatus, SlotRole, TenantRole
from app.common.exceptions import ForbiddenError, NotFoundError, PlanError, PlanValidationError
from app.domain.engines.slot_reservation_engine import ActivePlant
from app.domain.models.planting_reservation import (
    MAX_ZONE_STAND_QUANTITY,
    QUICK_PLANTING_MAX_QUANTITY,
    SlotThinningInput,
)
from app.domain.services.slot_thinning_service import THINNING_STAND_SUMMARY, THINNING_SUMMARY
from tests.support.garden_plan_fakes import OTHER_TENANT, TENANT
from tests.support.slot_thinning_world import sown_world

USER = "u_sabine"


def thin(world, *, role: TenantRole = TenantRole.GROWER, **request):
    return world.thinning.thin_slot(
        "row1", tenant_key=TENANT, user_key=USER, role=role, request=SlotThinningInput(**request)
    )


class TestPlan:
    def test_the_plan_names_the_runs_spacing_and_the_count_it_gives(self) -> None:
        plan = sown_world().thinning.plan_thinning("row1", tenant_key=TENANT)
        assert (plan.measure_kind, plan.measure_value) == ("length", 1.2)
        assert plan.thinning_to_cm == 5.0
        assert plan.suggested_count == 24
        assert plan.species_key == "sp_carrot"

    def test_without_a_spacing_on_the_run_the_plan_suggests_nothing(self) -> None:
        plan = sown_world(thinning_to_cm=None).thinning.plan_thinning("row1", tenant_key=TENANT)
        assert plan.thinning_to_cm is None
        assert plan.suggested_count is None

    def test_a_foreign_slot_is_not_found(self) -> None:
        with pytest.raises(NotFoundError):
            sown_world().thinning.plan_thinning("foreign_row", tenant_key=TENANT)


class TestThinning:
    def test_a_sown_row_becomes_its_plants_and_loses_sown_at(self) -> None:
        world = sown_world()
        outcome = thin(world)
        assert len(outcome.plant_keys) == 24
        (write,) = world.repo.thinning_writes
        assert write.slot_key == "row1"
        assert write.tenant_key == TENANT
        assert len(write.plants) == 24
        assert {item.plant.slot_key for item in write.plants} == {"row1"}
        assert {item.plant.species_key for item in write.plants} == {"sp_carrot"}
        assert {item.plant.tenant_key for item in write.plants} == {TENANT}
        assert write.event.category == "thinning"
        assert write.event.trigger == "system"
        assert world.runs.runs[world.run_key].status is PlantingRunStatus.ACTIVE
        assert outcome.run_started is True
        slot = next(slot for slot in world.plan.slots if slot.key == "row1")
        assert slot.sown_at is None

    def test_a_zone_is_thinned_by_its_area(self) -> None:
        world = sown_world(role=SlotRole.ZONE, thinning_to_cm=10.0)
        assert len(thin(world).plant_keys) == 50  # 0.5 m² at 10 cm

    def test_an_active_run_is_not_started_again(self) -> None:
        world = sown_world(run_status=PlantingRunStatus.ACTIVE)
        assert thin(world).run_started is False

    def test_the_growers_spacing_replaces_the_runs(self) -> None:
        assert len(thin(sown_world(), thinning_to_cm=10.0).plant_keys) == 12

    def test_the_growers_count_wins(self) -> None:
        assert len(thin(sown_world(thinning_to_cm=None), count=7).plant_keys) == 7

    def test_without_any_spacing_the_request_is_refused_and_nothing_is_written(self) -> None:
        world = sown_world(thinning_to_cm=None)
        with pytest.raises(PlanValidationError) as caught:
            thin(world)
        assert caught.value.details[0]["code"] == "thinning.spacing_required"
        assert world.repo.thinning_writes == []

    def test_a_viewer_may_not_thin(self) -> None:
        world = sown_world()
        with pytest.raises(ForbiddenError):
            thin(world, role=TenantRole.VIEWER)
        assert world.repo.thinning_writes == []

    def test_a_foreign_slot_is_not_found(self) -> None:
        world = sown_world()
        with pytest.raises(NotFoundError):
            world.thinning.thin_slot(
                "foreign_row", tenant_key=TENANT, user_key=USER, role=TenantRole.GROWER, request=SlotThinningInput()
            )
        with pytest.raises(NotFoundError):
            world.thinning.thin_slot(
                "row1", tenant_key=OTHER_TENANT, user_key=USER, role=TenantRole.GROWER, request=SlotThinningInput()
            )

    def test_a_legacy_entry_naming_another_tenants_species_stamps_no_plant(self) -> None:
        world = sown_world()
        world.species.add("sp_carrot", "Daucus carota", tenant_key=OTHER_TENANT)
        with pytest.raises(NotFoundError):
            thin(world)
        assert world.repo.thinning_writes == []

    def test_a_slot_that_is_not_sown_is_refused(self) -> None:
        world = sown_world()
        world.plan.slots[0] = world.plan.slots[0].model_copy(update={"sown_at": None})
        with pytest.raises(PlanError) as caught:
            thin(world)
        assert caught.value.error_code == "slot.not_sown"

    def test_a_slot_with_plants_standing_is_a_conflict(self) -> None:
        world = sown_world()
        world.repo.plants.append(ActivePlant(slot_key="row1", plant_key="p1", run_key=world.run_key, expected_end=None))
        with pytest.raises(PlanError) as caught:
            thin(world)
        assert caught.value.status_code == 409

    def test_a_sown_slot_no_run_reserves_is_refused(self) -> None:
        with pytest.raises(PlanError) as caught:
            thin(sown_world(reserved=False))
        assert caught.value.error_code == "thinning.no_run"

    def test_a_row_with_more_plants_than_one_write_takes_is_refused(self) -> None:
        world = sown_world(thinning_to_cm=0.2)  # 1.2 m of row at 0.2 cm = 600
        with pytest.raises(PlanError) as caught:
            thin(world)
        assert caught.value.error_code == "plan.quota_exceeded"
        assert caught.value.details[0]["limit"] == QUICK_PLANTING_MAX_QUANTITY
        assert world.repo.thinning_writes == []

    def test_a_planting_day_before_the_sowing_is_refused(self) -> None:
        with pytest.raises(PlanValidationError):
            thin(sown_world(), planted_on=today_utc() - timedelta(days=60))


class TestRowSpacing:
    """#2862 — a zone counts row spacing x in-row spacing when a row spacing is known (run, profile or grower).

    The zone of the world is 0.5 m²; carrot thinned to 4 cm in rows 25 cm apart gives 50 plants, the square grid of
    4 cm gives 312. The values are test data, not constants of the code (E-10).
    """

    def _zone(self, **kwargs) -> SimpleNamespace:
        return sown_world(role=SlotRole.ZONE, thinning_to_cm=4.0, **kwargs)

    def test_the_runs_row_spacing_counts_rows(self) -> None:
        plan = self._zone(row_spacing_cm=25.0).thinning.plan_thinning("row1", tenant_key=TENANT)
        assert (plan.row_spacing_cm, plan.row_spacing_source, plan.count_formula) == (25.0, "run", "rows")
        assert plan.suggested_count == 50

    def test_the_species_profile_prefills_its_lower_value(self) -> None:
        plan = self._zone(species_row_spacing_cm="25-30").thinning.plan_thinning("row1", tenant_key=TENANT)
        assert (plan.row_spacing_cm, plan.row_spacing_source) == (25.0, "species")
        assert plan.species_row_spacing_cm == "25-30"
        assert plan.suggested_count == 50

    def test_the_run_wins_over_the_species_profile(self) -> None:
        world = self._zone(row_spacing_cm=50.0, species_row_spacing_cm="25-30")
        plan = world.thinning.plan_thinning("row1", tenant_key=TENANT)
        assert (plan.row_spacing_cm, plan.row_spacing_source, plan.suggested_count) == (50.0, "run", 25)

    @pytest.mark.parametrize("profile", [None, "unknown", "2"])
    def test_without_a_usable_row_spacing_the_zone_stays_the_square_grid_estimate(self, profile) -> None:
        plan = self._zone(species_row_spacing_cm=profile).thinning.plan_thinning("row1", tenant_key=TENANT)
        assert (plan.row_spacing_cm, plan.row_spacing_source, plan.count_formula) == (None, None, "square_grid")
        assert plan.suggested_count == 312

    def test_a_row_slot_ignores_the_row_spacing(self) -> None:
        plan = sown_world(row_spacing_cm=25.0).thinning.plan_thinning("row1", tenant_key=TENANT)
        assert (plan.count_formula, plan.suggested_count) == ("along_row", 24)

    def test_thinning_stores_the_rows_count(self) -> None:
        assert len(thin(self._zone(species_row_spacing_cm="25-30")).plant_keys) == 50

    def test_the_growers_row_spacing_replaces_run_and_profile(self) -> None:
        world = self._zone(row_spacing_cm=50.0, species_row_spacing_cm="40")
        assert len(thin(world, row_spacing_cm=25.0).plant_keys) == 50

    def test_an_explicit_null_asks_for_the_square_grid(self) -> None:
        # Broadcast sowing: the grower clears the prefilled row spacing.
        world = self._zone(species_row_spacing_cm="25-30")
        assert len(thin(world, row_spacing_cm=None).plant_keys) == 312

    def test_a_row_spacing_below_the_layout_bound_is_invalid(self) -> None:
        with pytest.raises(ValidationError):
            SlotThinningInput(row_spacing_cm=4.0)
        with pytest.raises(ValidationError):
            SlotThinningInput(row_spacing_cm=1_501.0)

    def test_the_500_plant_cap_is_unchanged(self) -> None:
        assert QUICK_PLANTING_MAX_QUANTITY == 500
        # Rows of a zone that yield more than one write takes become a target stand (#2862): 0.5 m² at 1 x 5 cm.
        world = sown_world(role=SlotRole.ZONE, thinning_to_cm=1.0, row_spacing_cm=5.0)
        assert world.thinning.plan_thinning("row1", tenant_key=TENANT).max_count == 500
        outcome = thin(world)
        assert (outcome.plant_keys, outcome.stand_quantity) == ([], 1_000)
        # The same 2 cm in rows 25 cm apart is 100 plants and is written.
        assert len(thin(sown_world(role=SlotRole.ZONE, thinning_to_cm=2.0, row_spacing_cm=25.0)).plant_keys) == 100


class TestZoneStand:
    """#2862, REQ-053 §11.1 step 7 / §32.8 Pkt. 1 — a zone above the quota becomes a target stand, not 1 000 plants.

    The zone of the world is 0.5 m²; thinned to 2 cm on the square grid it holds 1 250 plants. Test data, not
    constants of the code (E-10).
    """

    def test_a_zone_above_the_quota_records_the_target_stand_instead_of_plants(self) -> None:
        world = sown_world(role=SlotRole.ZONE, thinning_to_cm=2.0)
        outcome = thin(world)
        assert (outcome.plant_keys, outcome.instance_ids, outcome.stand_quantity) == ([], [], 1_250)
        (write,) = world.repo.thinning_writes
        assert write.plants == []
        assert write.stand_quantity == 1_250
        assert write.tenant_key == TENANT
        # The event is the whole bed's (GP-FR-100): no plant keys, the stand in the summary.
        assert write.event.category == "thinning"
        assert write.event.plant_keys == []
        assert write.event.summary == THINNING_STAND_SUMMARY.format(slot_id="BED3_R01", count=1_250)
        # The run starts as with plants.
        assert outcome.run_started is True
        assert world.runs.runs[world.run_key].status is PlantingRunStatus.ACTIVE

    def test_the_slot_keeps_sown_at_and_is_marked_as_a_stand_on_the_thinning_day(self) -> None:
        world = sown_world(role=SlotRole.ZONE, thinning_to_cm=2.0)
        sown_at = world.plan.slots[0].sown_at
        day = today_utc() - timedelta(days=2)
        thin(world, planted_on=day)
        slot = next(slot for slot in world.plan.slots if slot.key == "row1")
        assert (slot.sown_at, slot.thinned_at, slot.currently_occupied) == (sown_at, day, True)

    def test_up_to_the_quota_a_zone_still_gets_single_plants(self) -> None:
        world = sown_world(role=SlotRole.ZONE, thinning_to_cm=2.0)
        outcome = thin(world, count=QUICK_PLANTING_MAX_QUANTITY)
        assert len(outcome.plant_keys) == QUICK_PLANTING_MAX_QUANTITY
        assert outcome.stand_quantity is None
        (write,) = world.repo.thinning_writes
        assert write.stand_quantity is None
        assert write.event.summary == THINNING_SUMMARY.format(slot_id="BED3_R01", count=QUICK_PLANTING_MAX_QUANTITY)

    def test_one_above_the_quota_is_a_stand(self) -> None:
        outcome = thin(sown_world(role=SlotRole.ZONE, thinning_to_cm=2.0), count=QUICK_PLANTING_MAX_QUANTITY + 1)
        assert (outcome.plant_keys, outcome.stand_quantity) == ([], QUICK_PLANTING_MAX_QUANTITY + 1)

    def test_a_growers_count_above_the_quota_on_a_row_is_refused(self) -> None:
        world = sown_world()
        with pytest.raises(PlanError) as caught:
            thin(world, count=QUICK_PLANTING_MAX_QUANTITY + 1)
        assert caught.value.error_code == "plan.quota_exceeded"
        assert world.repo.thinning_writes == []

    def test_a_stand_larger_than_a_zone_holds_is_refused(self) -> None:
        world = sown_world(role=SlotRole.ZONE, thinning_to_cm=0.2)  # 0.5 m² at 0.2 cm = 125 000
        with pytest.raises(PlanError) as caught:
            thin(world)
        assert caught.value.error_code == "plan.quota_exceeded"
        assert caught.value.details[0]["limit"] == MAX_ZONE_STAND_QUANTITY
        assert world.repo.thinning_writes == []

    def test_a_count_above_the_stand_bound_is_invalid(self) -> None:
        with pytest.raises(ValidationError):
            SlotThinningInput(count=MAX_ZONE_STAND_QUANTITY + 1)

    def test_the_plan_names_the_stand_bound_for_a_zone_only(self) -> None:
        zone = sown_world(role=SlotRole.ZONE).thinning.plan_thinning("row1", tenant_key=TENANT)
        row = sown_world().thinning.plan_thinning("row1", tenant_key=TENANT)
        assert (zone.max_count, zone.max_stand_count) == (QUICK_PLANTING_MAX_QUANTITY, MAX_ZONE_STAND_QUANTITY)
        assert (row.max_count, row.max_stand_count) == (QUICK_PLANTING_MAX_QUANTITY, None)

    def test_a_zone_stand_is_not_thinned_again(self) -> None:
        world = sown_world(role=SlotRole.ZONE, thinning_to_cm=2.0)
        thin(world)
        with pytest.raises(PlanError) as caught:
            thin(world)
        assert (caught.value.error_code, caught.value.status_code) == ("slot.occupied", 409)
        assert len(world.repo.thinning_writes) == 1

    def test_a_zone_stand_is_not_sown_again(self) -> None:
        world = sown_world(role=SlotRole.ZONE, thinning_to_cm=2.0)
        thin(world)
        with pytest.raises(PlanError) as caught:
            world.thinning.mark_sown("row1", tenant_key=TENANT, role=TenantRole.GROWER, sown_at=today_utc())
        assert (caught.value.error_code, caught.value.status_code) == ("slot.occupied", 409)
        assert world.repo.sowings == []


class TestPhaseAndDays:
    """Agrobiology review of WP 10.9: the seedling phase from the thinning day; days and spacing within bounds."""

    def _with_phases(self, world, *names: str) -> None:
        phases = [SimpleNamespace(key=f"gp_{name}", name=name, sequence_order=i) for i, name in enumerate(names)]
        world.service._phase_repo = SimpleNamespace(
            get_lifecycle_by_species=lambda species_key: SimpleNamespace(key="lc"),
            get_phases_by_lifecycle=lambda key: list(reversed(phases)),
        )

    def test_thinned_plants_start_as_seedlings_on_the_thinning_day(self) -> None:
        world = sown_world()
        self._with_phases(world, "germination", "seedling", "vegetative")
        day = today_utc() - timedelta(days=2)
        thin(world, planted_on=day)
        (write,) = world.repo.thinning_writes
        assert {item.plant.current_phase_key for item in write.plants} == {"gp_seedling"}
        started = datetime.combine(day, time.min, tzinfo=UTC)
        assert {item.plant.current_phase_started_at for item in write.plants} == {started}
        assert {item.history.entered_at for item in write.plants if item.history} == {started}
        assert write.run_phase_key == "gp_seedling"

    def test_without_a_seedling_phase_the_first_after_germination(self) -> None:
        world = sown_world()
        self._with_phases(world, "germination", "vegetative")
        thin(world)
        assert {item.plant.current_phase_key for item in world.repo.thinning_writes[0].plants} == {"gp_vegetative"}

    def test_a_thinning_day_in_the_future_is_refused(self) -> None:
        world = sown_world()
        with pytest.raises(PlanValidationError) as caught:
            thin(world, planted_on=today_utc() + timedelta(days=1))
        assert caught.value.details[0]["code"] == "thinning.planted_in_future"
        assert world.repo.thinning_writes == []

    def test_a_run_spacing_wider_than_thinning_takes_is_refused(self) -> None:
        world = sown_world(thinning_to_cm=300.0)
        with pytest.raises(PlanValidationError) as caught:
            thin(world)
        assert caught.value.details[0]["code"] == "thinning.spacing_out_of_range"

    def test_a_request_spacing_above_200_cm_is_invalid(self) -> None:
        with pytest.raises(ValidationError):
            SlotThinningInput(thinning_to_cm=250.0)

    def test_a_sowing_two_years_back_is_taken_older_is_not(self) -> None:
        world = sown_world()
        world.plan.slots[0] = world.plan.slots[0].model_copy(update={"sown_at": None})
        world.thinning.mark_sown(
            "row1", tenant_key=TENANT, role=TenantRole.GROWER, sown_at=today_utc() - timedelta(days=730)
        )
        world.plan.slots[0] = world.plan.slots[0].model_copy(update={"sown_at": None})
        with pytest.raises(PlanValidationError):
            world.thinning.mark_sown(
                "row1", tenant_key=TENANT, role=TenantRole.GROWER, sown_at=today_utc() - timedelta(days=731)
            )

    def test_a_reservation_released_meanwhile_is_a_conflict(self) -> None:
        world = sown_world()
        original = world.repo.thin_sown_slot

        def released_first(write):
            world.repo.reservations.clear()
            return original(write)

        world.repo.thin_sown_slot = released_first
        with pytest.raises(PlanError) as caught:
            thin(world)
        assert caught.value.status_code == 409


class TestSowing:
    def test_a_reserved_row_is_marked_sown(self) -> None:
        world = sown_world()
        world.plan.slots[0] = world.plan.slots[0].model_copy(update={"sown_at": None})
        day = today_utc() - timedelta(days=1)
        slot = world.thinning.mark_sown("row1", tenant_key=TENANT, role=TenantRole.GROWER, sown_at=day)
        assert slot.sown_at == day
        assert world.repo.sowings == [("row1", day.isoformat())]

    def test_a_position_slot_cannot_be_sown(self) -> None:
        world = sown_world(role=SlotRole.POSITION, geometry={"kind": "point", "origin": [0.5, 0.5]})
        with pytest.raises(PlanError) as caught:
            world.thinning.mark_sown("row1", tenant_key=TENANT, role=TenantRole.GROWER, sown_at=today_utc())
        assert caught.value.error_code == "slot.not_sowable"

    def test_a_sowing_in_the_future_is_refused(self) -> None:
        world = sown_world()
        with pytest.raises(PlanValidationError):
            world.thinning.mark_sown(
                "row1", tenant_key=TENANT, role=TenantRole.GROWER, sown_at=today_utc() + timedelta(days=1)
            )

    def test_a_viewer_may_not_sow(self) -> None:
        with pytest.raises(ForbiddenError):
            sown_world().thinning.mark_sown("row1", tenant_key=TENANT, role=TenantRole.VIEWER, sown_at=today_utc())
