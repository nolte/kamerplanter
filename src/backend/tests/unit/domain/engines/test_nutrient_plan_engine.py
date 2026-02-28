import pytest

from app.common.enums import PhaseName
from app.domain.engines.nutrient_plan_engine import NutrientPlanValidator
from app.domain.models.nutrient_plan import NutrientPlanPhaseEntry


@pytest.fixture
def validator():
    return NutrientPlanValidator()


def _make_entry(**kwargs) -> NutrientPlanPhaseEntry:
    defaults = {
        "plan_key": "p1",
        "phase_name": PhaseName.VEGETATIVE,
        "sequence_order": 1,
        "week_start": 1,
        "week_end": 4,
    }
    defaults.update(kwargs)
    return NutrientPlanPhaseEntry(**defaults)


class TestValidateCompleteness:
    def test_all_phases_covered(self, validator):
        entries = [
            _make_entry(phase_name=PhaseName.GERMINATION, sequence_order=1, week_start=1, week_end=2),
            _make_entry(phase_name=PhaseName.SEEDLING, sequence_order=2, week_start=3, week_end=4),
            _make_entry(phase_name=PhaseName.VEGETATIVE, sequence_order=3, week_start=5, week_end=8),
            _make_entry(phase_name=PhaseName.FLOWERING, sequence_order=4, week_start=9, week_end=12),
            _make_entry(phase_name=PhaseName.HARVEST, sequence_order=5, week_start=13, week_end=14),
        ]
        result = validator.validate_completeness(entries)
        assert result["complete"] is True
        assert len(result["issues"]) == 0

    def test_missing_phase(self, validator):
        entries = [
            _make_entry(phase_name=PhaseName.VEGETATIVE, sequence_order=1, week_start=1, week_end=4),
            _make_entry(phase_name=PhaseName.FLOWERING, sequence_order=2, week_start=5, week_end=8),
        ]
        result = validator.validate_completeness(entries)
        assert result["complete"] is False
        assert any("germination" in i.lower() for i in result["issues"])

    def test_week_gap(self, validator):
        entries = [
            _make_entry(phase_name=PhaseName.VEGETATIVE, sequence_order=1, week_start=1, week_end=4),
            _make_entry(phase_name=PhaseName.VEGETATIVE, sequence_order=2, week_start=7, week_end=10),
        ]
        result = validator.validate_completeness(entries)
        assert result["complete"] is False
        assert any("gap" in i.lower() for i in result["issues"])

    def test_empty_entries(self, validator):
        result = validator.validate_completeness([])
        assert result["complete"] is False
        assert len(result["issues"]) == 5  # all phases missing


