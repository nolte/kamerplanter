"""REQ-053 GP-FR-074 — a succession plan's batches reserve their slots (``run_planned_at``, GP-FR-065, V-08).

The real :class:`SuccessionPlanService`, :class:`PlantingRunService` and :class:`PlantingReservationService` over
the in-memory doubles of ``tests/support/planting_reservation_fakes.py``: the reservation a batch gets is the one
``plan-slots`` would write, read back from the reservation double, not a value the test hands in.

Every refusal asserts that **nothing was written** (no run, no reservation): a refusal that still wrote is the
defect, not the status code.
"""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import pytest

from app.common.enums import PlantingRunStatus, PlantingRunType
from app.common.exceptions import NotFoundError, PlanError
from app.domain.engines.slot_reservation_engine import Reservation
from app.domain.models.planting_run import PlantingRun
from app.domain.models.site import Slot
from app.domain.models.succession_plan import SuccessionPlan
from app.domain.services import succession_plan_service as succession_module
from app.domain.services.succession_plan_service import SuccessionPlanService
from tests.support.garden_plan_fakes import OTHER_TENANT, TENANT
from tests.support.planting_reservation_fakes import build_world
from tests.unit.domain.services.test_succession_plan_service import _FakeSuccessionRepo

D = date
#: Before the first batch: every batch of the plan is still to come.
BEFORE_SEASON = D(2027, 1, 10)


@pytest.fixture
def world(monkeypatch) -> SimpleNamespace:
    world = build_world()
    world.plan.slots = [Slot(_key=f"s{n}", slot_id=f"BED3_00{n}", location_key="bed", sequence=n) for n in range(1, 7)]
    world.today = BEFORE_SEASON
    monkeypatch.setattr(succession_module, "today_utc", lambda: world.today)
    world.plans = _FakeSuccessionRepo()
    world.succession = SuccessionPlanService(
        world.plans,
        world.service,
        site_repo=world.sites,
        species_resolver=lambda key, *, tenant_key: world.species[key],
        reservations=world.reservations,
    )
    return world


def make_plan(world, **overrides) -> SuccessionPlan:
    """Three batches of two lettuces in bed 3: 1 April, 22 April, 13 May 2027."""
    data = {
        "name": "Lettuce bed 3",
        "species_key": "sp_tomato",
        "interval_days": 21,
        "start_date": D(2027, 4, 1),
        "end_date": D(2027, 5, 13),
        "plants_per_batch": 2,
        "location_key": "bed",
        **overrides,
    }
    return world.succession.create_plan(SuccessionPlan(**data), tenant_key=TENANT)


def reserved(world) -> dict[str, list[tuple[str, date | None, date | None]]]:
    """Per run, its reserved slots with the window stamped on each edge, in ``sequence`` order."""
    by_run: dict[str, list[tuple[str, date | None, date | None]]] = {}
    for r in sorted(world.repo.reservations, key=lambda r: (r.run_key, r.sequence)):
        by_run.setdefault(r.run_key, []).append((r.slot_key, r.planned_from, r.planned_until))
    return by_run


def foreign_hold(world, slot_keys: list[str], start: date, end: date | None) -> None:
    """Another run of the tenant reserves ``slot_keys`` for ``[start, end]``."""
    for sequence, slot_key in enumerate(slot_keys, start=1):
        world.repo.reservations.append(Reservation(slot_key, "run_tomato", "e_t", "sp", sequence, start, end))


class TestEachBatchReservesItsSlots:
    def test_open_windows_give_every_batch_its_own_slots(self, world) -> None:
        plan = make_plan(world)

        _, runs = world.succession.generate_runs(plan.key, tenant_key=TENANT)

        assert [run.planned_from for run in runs] == [D(2027, 4, 1), D(2027, 4, 22), D(2027, 5, 13)]
        assert reserved(world) == {
            runs[0].key: [("s1", D(2027, 4, 1), None), ("s2", D(2027, 4, 1), None)],
            runs[1].key: [("s3", D(2027, 4, 22), None), ("s4", D(2027, 4, 22), None)],
            runs[2].key: [("s5", D(2027, 5, 13), None), ("s6", D(2027, 5, 13), None)],
        }
        # Written through the plan-slots path: one reservation write per batch, for the batch's own entry.
        assert [write.run_key for write in world.repo.reservation_writes] == [run.key for run in runs]
        assert {run.source for run in runs} == {"succession"}

    def test_a_batch_duration_closes_the_window_so_disjoint_batches_share_the_slots(self, world) -> None:
        plan = make_plan(world, batch_duration_days=21)

        _, runs = world.succession.generate_runs(plan.key, tenant_key=TENANT)

        assert reserved(world) == {
            runs[0].key: [("s1", D(2027, 4, 1), D(2027, 4, 21)), ("s2", D(2027, 4, 1), D(2027, 4, 21))],
            runs[1].key: [("s1", D(2027, 4, 22), D(2027, 5, 12)), ("s2", D(2027, 4, 22), D(2027, 5, 12))],
            runs[2].key: [("s1", D(2027, 5, 13), D(2027, 6, 2)), ("s2", D(2027, 5, 13), D(2027, 6, 2))],
        }

    def test_overlapping_batches_rotate_through_the_bed(self, world) -> None:
        # 42 days of culture at a 21-day interval: two batches stand at once, the third takes the first's slots.
        plan = make_plan(world, batch_duration_days=42)

        _, runs = world.succession.generate_runs(plan.key, tenant_key=TENANT)

        assert [[slot for slot, _, _ in reserved(world)[run.key]] for run in runs] == [
            ["s1", "s2"],
            ["s3", "s4"],
            ["s1", "s2"],
        ]

    def test_a_slot_of_another_run_is_skipped(self, world) -> None:
        foreign_hold(world, ["s1"], D(2027, 3, 1), D(2027, 6, 30))
        plan = make_plan(world, batch_duration_days=21)

        _, runs = world.succession.generate_runs(plan.key, tenant_key=TENANT)

        assert [slot for slot, _, _ in reserved(world)[runs[0].key]] == ["s2", "s3"]

    def test_generate_next_reserves_only_the_next_batch(self, world) -> None:
        plan = make_plan(world, batch_duration_days=21)

        _, run = world.succession.generate_next_run(plan.key, tenant_key=TENANT)

        assert run is not None
        assert reserved(world) == {
            run.key: [("s1", D(2027, 4, 1), D(2027, 4, 21)), ("s2", D(2027, 4, 1), D(2027, 4, 21))]
        }

    def test_a_batch_whose_sowing_day_passed_reserves_nothing(self, world) -> None:
        world.today = D(2027, 4, 22)  # batch 1 is overdue; batch 2 is sown today
        plan = make_plan(world)

        _, runs = world.succession.generate_runs(plan.key, tenant_key=TENANT)

        assert runs[0].key not in reserved(world)
        assert [slot for slot, _, _ in reserved(world)[runs[1].key]] == ["s1", "s2"]

    def test_a_bed_without_slots_reserves_nothing_and_still_generates(self, world) -> None:
        world.plan.slots = []
        plan = make_plan(world)

        _, runs = world.succession.generate_runs(plan.key, tenant_key=TENANT)

        assert len(runs) == 3
        assert world.repo.reservations == []

    def test_a_plan_without_a_bed_reserves_nothing(self, world) -> None:
        plan = make_plan(world, location_key=None)

        _, runs = world.succession.generate_runs(plan.key, tenant_key=TENANT)

        assert len(runs) == 3
        assert world.repo.reservations == []


class TestRefusals:
    def test_an_overlap_with_another_run_is_409_and_writes_nothing(self, world) -> None:
        foreign_hold(world, ["s1", "s2", "s3", "s4", "s5"], D(2027, 5, 1), None)
        plan = make_plan(world, batch_duration_days=21)

        with pytest.raises(PlanError) as refused:
            world.succession.generate_runs(plan.key, tenant_key=TENANT)

        assert refused.value.status_code == 409
        assert refused.value.error_code == "slot.already_planned"
        detail = refused.value.details[0]
        assert detail["conflicting_run_key"] == "run_tomato"
        # Batch 2 (22 April - 12 May) meets the hold from 1 May on; batch 1 ended before it.
        assert detail["overlap_from"] == "2027-05-01"
        # Batch 2 failed, so batch 1 was never written either.
        assert world.runs.runs == {}
        assert world.repo.reservation_writes == []
        assert world.plans.get_or_raise(plan.key).completed_batches == 0

    def test_open_batches_that_fill_the_bed_are_409(self, world) -> None:
        world.plan.slots = world.plan.slots[:4]
        plan = make_plan(world)  # open windows: batch 3 finds s1-s4 held by batches 1 and 2

        with pytest.raises(PlanError) as refused:
            world.succession.generate_runs(plan.key, tenant_key=TENANT)

        assert refused.value.status_code == 409
        # The holder is a batch of the same request, not yet stored: no key to name.
        assert refused.value.details[0]["conflicting_run_key"] is None
        assert world.runs.runs == {}

    def test_a_bed_smaller_than_one_batch_is_422(self, world) -> None:
        plan = make_plan(world, plants_per_batch=7)

        with pytest.raises(PlanError) as refused:
            world.succession.generate_runs(plan.key, tenant_key=TENANT)

        assert refused.value.status_code == 422
        assert refused.value.error_code == "succession.not_enough_slots"
        assert refused.value.details[0]["available"] == 6
        assert world.runs.runs == {}

    def test_a_reservation_placed_between_choice_and_write_takes_the_batch_back(self, world) -> None:
        plan = make_plan(world, batch_duration_days=21)
        original = world.repo.set_reservation
        calls: list[str] = []

        def racing(write, verify) -> None:
            calls.append(write.run_key)
            if len(calls) == 2:  # someone reserved s1 for batch 2's window in the meantime
                foreign_hold(world, ["s1"], D(2027, 4, 22), D(2027, 4, 30))
            original(write, verify)

        world.repo.set_reservation = racing

        with pytest.raises(PlanError):
            world.succession.generate_runs(plan.key, tenant_key=TENANT)

        # Batch 2's run is gone again, batch 1 stays and counts: a second call does not create it twice.
        assert list(world.runs.runs) == [calls[0]]
        assert world.runs.deleted == [calls[1]]
        assert world.plans.get_or_raise(plan.key).completed_batches == 1


class TestPlanChangesReleaseFutureBatches:
    def _generated(self, world, **overrides):
        plan = make_plan(world, batch_duration_days=21, **overrides)
        _, runs = world.succession.generate_runs(plan.key, tenant_key=TENANT)
        return plan, runs

    def test_a_schedule_change_releases_only_the_batches_not_yet_due(self, world) -> None:
        plan, runs = self._generated(world)
        world.today = D(2027, 4, 25)  # batch 1 and 2 are due; batch 3 (13 May) is not

        world.succession.update_plan(plan.key, {"interval_days": 28}, tenant_key=TENANT)

        assert set(reserved(world)) == {runs[0].key, runs[1].key}
        assert world.repo.dropped == [(runs[2].key, False)]
        # The run stays; only its slots are free again.
        assert runs[2].key in world.runs.runs

    def test_a_started_batch_keeps_its_slots_even_before_its_date(self, world) -> None:
        plan, runs = self._generated(world)
        started = runs[2].model_copy(update={"status": PlantingRunStatus.ACTIVE})
        world.runs.runs[started.key] = started

        world.succession.update_plan(plan.key, {"plants_per_batch": 1}, tenant_key=TENANT)

        assert set(reserved(world)) == {runs[2].key}
        assert [run_key for run_key, _ in world.repo.dropped] == [runs[0].key, runs[1].key]

    def test_a_change_of_the_name_keeps_every_reservation(self, world) -> None:
        plan, runs = self._generated(world)

        world.succession.update_plan(plan.key, {"name": "Lettuce, early"}, tenant_key=TENANT)

        assert set(reserved(world)) == {run.key for run in runs}
        assert world.repo.dropped == []

    def test_cancelling_the_plan_releases_its_future_batches(self, world) -> None:
        plan, runs = self._generated(world)

        world.succession.update_plan(plan.key, {"status": "cancelled"}, tenant_key=TENANT)

        assert reserved(world) == {}
        assert [run_key for run_key, _ in world.repo.dropped] == [run.key for run in runs]

    def test_deleting_the_plan_releases_its_future_batches(self, world) -> None:
        plan, runs = self._generated(world)
        world.today = D(2027, 4, 1)  # batch 1 is due today and keeps its slots

        assert world.succession.delete_plan(plan.key, tenant_key=TENANT)

        assert set(reserved(world)) == {runs[0].key}


class TestTenantIsolation:
    def test_another_tenant_can_neither_generate_nor_release(self, world) -> None:
        plan, runs = TestPlanChangesReleaseFutureBatches()._generated(world)

        with pytest.raises(NotFoundError):
            world.succession.generate_runs(plan.key, tenant_key=OTHER_TENANT)
        with pytest.raises(NotFoundError):
            world.succession.update_plan(plan.key, {"interval_days": 7}, tenant_key=OTHER_TENANT)
        with pytest.raises(NotFoundError):
            world.succession.delete_plan(plan.key, tenant_key=OTHER_TENANT)

        assert set(reserved(world)) == {run.key for run in runs}
        assert world.repo.dropped == []

    def test_a_run_of_another_tenant_naming_the_plan_is_never_released(self, world) -> None:
        plan, runs = TestPlanChangesReleaseFutureBatches()._generated(world)
        foreign = PlantingRun(
            _key="run_foreign",
            tenant_key=OTHER_TENANT,
            name="Foreign",
            run_type=PlantingRunType.MONOCULTURE,
            planned_start_date=D(2027, 6, 1),
            succession_plan_key=plan.key,
        )
        world.runs.runs[foreign.key] = foreign
        world.repo.reservations.append(Reservation("s5", "run_foreign", "e_f", "sp", 1, D(2027, 6, 1), None))

        world.succession.delete_plan(plan.key, tenant_key=TENANT)

        assert "run_foreign" not in [run_key for run_key, _ in world.repo.dropped]
        assert len(world.repo.dropped) == len(runs)
        assert set(reserved(world)) == {"run_foreign"}
