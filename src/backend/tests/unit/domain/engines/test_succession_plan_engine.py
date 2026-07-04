"""REQ-013 §2 — SuccessionPlanEngine pure-logic tests (Szenario 4 + edge cases)."""

from datetime import date, timedelta

from app.common.enums import PlantingRunStatus, PlantingRunType
from app.domain.engines.succession_plan_engine import SuccessionPlanEngine
from app.domain.models.succession_plan import SuccessionPlan

ENGINE = SuccessionPlanEngine()


def _scenario4_plan() -> SuccessionPlan:
    """The exact Szenario 4 plan: lettuce, weekly-ish over a whole season."""
    return SuccessionPlan(
        _key="sp_salat",
        tenant_key="tenant_lisa",
        name="Salat-Staffel Beet C 2026",
        species_key="species_lactuca_sativa",
        cultivar_key="cultivar_lollo_rosso",
        interval_days=21,
        start_date=date(2026, 4, 1),
        end_date=date(2026, 8, 31),
        plants_per_batch=12,
        location_key="loc_beet_c",
    )


class TestComputeTotalBatches:
    def test_scenario4_yields_eight_batches(self):
        assert ENGINE.compute_total_batches(date(2026, 4, 1), date(2026, 8, 31), 21) == 8

    def test_single_day_window_is_one_batch(self):
        assert ENGINE.compute_total_batches(date(2026, 4, 1), date(2026, 4, 1), 21) == 1

    def test_exact_multiple_of_interval(self):
        # 42 days / 21 = 2 → +1 = 3 batches (day 0, 21, 42).
        assert ENGINE.compute_total_batches(date(2026, 4, 1), date(2026, 5, 13), 21) == 3

    def test_window_shorter_than_interval_is_one_batch(self):
        assert ENGINE.compute_total_batches(date(2026, 4, 1), date(2026, 4, 10), 21) == 1

    def test_negative_window_yields_zero(self):
        assert ENGINE.compute_total_batches(date(2026, 8, 31), date(2026, 4, 1), 21) == 0


class TestGenerateBatchRuns:
    def test_scenario4_generates_exactly_eight_runs(self):
        runs = ENGINE.generate_batch_runs(_scenario4_plan())
        assert len(runs) == 8

    def test_planned_start_dates_follow_interval(self):
        plan = _scenario4_plan()
        runs = ENGINE.generate_batch_runs(plan)
        expected = [plan.start_date + timedelta(days=21 * i) for i in range(8)]
        assert [r.planned_start_date for r in runs] == expected
        # First three concrete dates from the spec: 01.04., 22.04., 13.05.
        assert runs[0].planned_start_date == date(2026, 4, 1)
        assert runs[1].planned_start_date == date(2026, 4, 22)
        assert runs[2].planned_start_date == date(2026, 5, 13)
        # Last batch = start + 7*21 = 26.08.2026.
        assert runs[7].planned_start_date == date(2026, 8, 26)

    def test_sequence_and_total_are_set(self):
        runs = ENGINE.generate_batch_runs(_scenario4_plan())
        assert [r.succession_sequence for r in runs] == list(range(1, 9))
        assert all(r.succession_total == 8 for r in runs)

    def test_run_metadata_matches_plan(self):
        plan = _scenario4_plan()
        runs = ENGINE.generate_batch_runs(plan)
        first = runs[0]
        assert first.name == "Salat-Staffel Beet C 2026 1/8"
        assert first.run_type == PlantingRunType.MONOCULTURE
        assert first.status == PlantingRunStatus.PLANNED
        assert first.planned_quantity == 12
        assert first.location_key == "loc_beet_c"
        assert first.tenant_key == "tenant_lisa"
        assert first.succession_plan_key == "sp_salat"

    def test_build_entry_carries_species_and_cultivar(self):
        plan = _scenario4_plan()
        entry = ENGINE.build_entry(plan)
        assert entry.species_key == "species_lactuca_sativa"
        assert entry.cultivar_key == "cultivar_lollo_rosso"
        assert entry.quantity == 12
        # id_prefix must satisfy the ^[A-Z]{2,5}$ constraint.
        assert entry.id_prefix == "LAC"


class TestNextBatchToGenerate:
    def test_none_generated_yields_first(self):
        plan = _scenario4_plan()
        plan.total_batches = 8
        assert ENGINE.next_batch_to_generate(plan) == 1

    def test_partial_progress_yields_next(self):
        plan = _scenario4_plan()
        plan.total_batches = 8
        plan.completed_batches = 3
        assert ENGINE.next_batch_to_generate(plan) == 4

    def test_all_generated_yields_none(self):
        plan = _scenario4_plan()
        plan.total_batches = 8
        plan.completed_batches = 8
        assert ENGINE.next_batch_to_generate(plan) is None

    def test_total_derived_when_not_stored(self):
        plan = _scenario4_plan()  # total_batches defaults to 0
        assert ENGINE.next_batch_to_generate(plan) == 1
