"""REQ-053 W-015 (Anhang A 60) — sowing a row or zone slot and thinning it into plants of its run.

The real :class:`SlotThinningService`, :class:`PlantingRunService` and :class:`CareEventService` over the in-memory
world of ``tests/support/planting_reservation_fakes.py``. What these tests prove is the service's decision: the count
from the slot's measure and the run's spacing (no default, E-10), ownership through the slot's bed, the role gate, and
the write set handed to the repository. The transaction itself is proven against ArangoDB in
``tests/integration/test_slot_thinning_flow.py``.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from app.common.datetimes import today_utc
from app.common.enums import PlantingRunStatus, SlotRole, TenantRole
from app.common.exceptions import ForbiddenError, NotFoundError, PlanError, PlanValidationError
from app.domain.engines.slot_reservation_engine import ActivePlant
from app.domain.models.planting_reservation import SlotThinningInput
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
        assert write.activate_run is True
        slot = next(slot for slot in world.plan.slots if slot.key == "row1")
        assert slot.sown_at is None

    def test_a_zone_is_thinned_by_its_area(self) -> None:
        world = sown_world(role=SlotRole.ZONE, thinning_to_cm=10.0)
        assert len(thin(world).plant_keys) == 50  # 0.5 m² at 10 cm

    def test_an_active_run_is_not_started_again(self) -> None:
        world = sown_world(run_status=PlantingRunStatus.ACTIVE)
        thin(world)
        assert world.repo.thinning_writes[0].activate_run is False

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

    def test_more_plants_than_one_write_takes_are_refused(self) -> None:
        with pytest.raises(PlanError) as caught:
            thin(sown_world(role=SlotRole.ZONE, thinning_to_cm=2.0))  # 0.5 m² at 2 cm = 1250
        assert caught.value.error_code == "plan.quota_exceeded"

    def test_a_planting_day_before_the_sowing_is_refused(self) -> None:
        with pytest.raises(PlanValidationError):
            thin(sown_world(), planted_on=today_utc() - timedelta(days=60))


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
