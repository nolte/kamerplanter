"""REQ-013 §2 — SuccessionPlan model validation."""

from datetime import date

import pytest
from pydantic import ValidationError

from app.common.enums import SuccessionPlanStatus
from app.domain.models.succession_plan import SuccessionPlan


def _plan(**overrides) -> SuccessionPlan:
    data = {
        "name": "Salat-Staffel Beet C 2026",
        "species_key": "species_lactuca_sativa",
        "interval_days": 21,
        "start_date": date(2026, 4, 1),
        "end_date": date(2026, 8, 31),
        "plants_per_batch": 12,
    }
    data.update(overrides)
    return SuccessionPlan(**data)


class TestSuccessionPlan:
    def test_valid_plan_defaults(self):
        plan = _plan()
        assert plan.status == SuccessionPlanStatus.PLANNED
        assert plan.completed_batches == 0
        assert plan.total_batches == 0
        assert plan.reminder_days_before == 3

    def test_key_alias(self):
        plan = _plan(**{"_key": "sp1"})
        assert plan.key == "sp1"

    def test_end_before_start_raises(self):
        with pytest.raises(ValidationError, match="end_date"):
            _plan(start_date=date(2026, 8, 31), end_date=date(2026, 4, 1))

    def test_equal_start_end_allowed(self):
        plan = _plan(start_date=date(2026, 4, 1), end_date=date(2026, 4, 1))
        assert plan.start_date == plan.end_date

    def test_interval_days_must_be_positive(self):
        with pytest.raises(ValidationError):
            _plan(interval_days=0)

    def test_plants_per_batch_must_be_positive(self):
        with pytest.raises(ValidationError):
            _plan(plants_per_batch=0)

    def test_name_too_short(self):
        with pytest.raises(ValidationError):
            _plan(name="")
