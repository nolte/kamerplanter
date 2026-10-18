"""REQ-053 WP 3.2 — the run fields of the reservation (REQ-013 §2) and the capacity of area slots (GP-FR-064)."""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from app.common.enums import PlanRole, PlantingRunType, SlotRole
from app.domain.models.planting_run import RUN_SOURCES, PlantingRun
from app.domain.models.site import MAX_AREA_CAPACITY, MAX_POSITION_CAPACITY, Slot


def run(**overrides) -> PlantingRun:
    return PlantingRun(name="Tomatoes", run_type=PlantingRunType.MONOCULTURE, **overrides)


class TestRunFields:
    def test_a_run_without_the_new_fields_reads_as_before(self) -> None:
        stored = run()
        assert (stored.plan_role, stored.source, stored.planned_from, stored.reserved_area_m2) == (
            PlanRole.MAIN_CROP,
            None,
            None,
            None,
        )

    def test_a_fallow_period_has_no_run(self) -> None:
        with pytest.raises(ValidationError):
            run(plan_role=PlanRole.FALLOW)

    @pytest.mark.parametrize("source", sorted(RUN_SOURCES))
    def test_every_listed_source_is_accepted(self, source) -> None:
        assert run(source=source).source == source

    def test_a_source_outside_the_allowlist_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            run(source="telepathy")

    def test_the_window_may_not_end_before_it_starts(self) -> None:
        with pytest.raises(ValidationError):
            run(planned_from=date(2026, 6, 1), planned_until=date(2026, 5, 1))
        assert run(planned_from=date(2026, 6, 1), planned_until=date(2026, 6, 1))
        assert run(planned_from=date(2026, 6, 1), planned_until=None)  # open end

    def test_the_area_reservation_is_positive(self) -> None:
        with pytest.raises(ValidationError):
            run(reserved_area_m2=0)
        assert run(reserved_area_m2=3.8).reserved_area_m2 == 3.8

    def test_the_override_reason_is_bounded(self) -> None:
        with pytest.raises(ValidationError):
            run(rotation_override_reason="x" * 501)


class TestSlotCapacity:
    def slot(self, role: SlotRole, capacity: int) -> Slot:
        return Slot(slot_id="BED_001", slot_role=role, capacity_plants=capacity)

    def test_a_position_holds_at_most_twenty(self) -> None:
        assert self.slot(SlotRole.POSITION, MAX_POSITION_CAPACITY)
        with pytest.raises(ValidationError):
            self.slot(SlotRole.POSITION, MAX_POSITION_CAPACITY + 1)

    @pytest.mark.parametrize("role", [SlotRole.ROW, SlotRole.ZONE])
    def test_an_area_slot_holds_what_the_layout_fits(self, role) -> None:
        assert self.slot(role, 500).capacity_plants == 500
        assert self.slot(role, MAX_AREA_CAPACITY)
        with pytest.raises(ValidationError):
            self.slot(role, MAX_AREA_CAPACITY + 1)
