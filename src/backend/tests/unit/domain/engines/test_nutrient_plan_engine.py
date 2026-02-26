import pytest

from app.common.enums import FertilizerType, PhaseName
from app.domain.engines.nutrient_plan_engine import NutrientPlanValidator
from app.domain.models.fertilizer import Fertilizer
from app.domain.models.nutrient_plan import FertilizerDosage, NutrientPlanPhaseEntry


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
        "target_ec_ms": 1.5,
    }
    defaults.update(kwargs)
    return NutrientPlanPhaseEntry(**defaults)


def _make_fert(**kwargs) -> Fertilizer:
    defaults = {
        "product_name": "Test Fert",
        "fertilizer_type": FertilizerType.BASE,
        "ec_contribution_per_ml": 0.5,
    }
    defaults.update(kwargs)
    return Fertilizer(**defaults)


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


class TestValidateEcBudget:
    def test_ec_within_tolerance(self, validator):
        fert = _make_fert(ec_contribution_per_ml=0.5)
        entry = _make_entry(
            target_ec_ms=1.5,
            fertilizer_dosages=[
                FertilizerDosage(fertilizer_key="f1", ml_per_liter=3.0),
            ],
        )
        result = validator.validate_ec_budget(entry, {"f1": fert})
        assert result["valid"] is True
        assert result["calculated_ec"] == 1.5

    def test_ec_exceeds_tolerance(self, validator):
        fert = _make_fert(ec_contribution_per_ml=0.5)
        entry = _make_entry(
            target_ec_ms=1.0,
            fertilizer_dosages=[
                FertilizerDosage(fertilizer_key="f1", ml_per_liter=5.0),
            ],
        )
        result = validator.validate_ec_budget(entry, {"f1": fert})
        assert result["valid"] is False
        assert "mismatch" in result["message"].lower()

    def test_missing_fertilizer(self, validator):
        entry = _make_entry(
            target_ec_ms=1.5,
            fertilizer_dosages=[
                FertilizerDosage(fertilizer_key="f_missing", ml_per_liter=3.0),
            ],
        )
        result = validator.validate_ec_budget(entry, {})
        assert result["valid"] is False
        assert "missing" in result["message"].lower()

    def test_no_dosages(self, validator):
        entry = _make_entry(target_ec_ms=1.5, fertilizer_dosages=[])
        result = validator.validate_ec_budget(entry, {})
        assert result["valid"] is True
        assert result["calculated_ec"] == 0.0

    def test_multiple_fertilizers(self, validator):
        fert_a = _make_fert(ec_contribution_per_ml=0.3)
        fert_b = _make_fert(ec_contribution_per_ml=0.2)
        entry = _make_entry(
            target_ec_ms=1.1,
            fertilizer_dosages=[
                FertilizerDosage(fertilizer_key="fa", ml_per_liter=2.0),
                FertilizerDosage(fertilizer_key="fb", ml_per_liter=2.5),
            ],
        )
        # 2.0*0.3 + 2.5*0.2 = 0.6 + 0.5 = 1.1
        result = validator.validate_ec_budget(entry, {"fa": fert_a, "fb": fert_b})
        assert result["valid"] is True
        assert result["calculated_ec"] == 1.1

    def test_ec_tolerance_boundary(self, validator):
        fert = _make_fert(ec_contribution_per_ml=0.5)
        entry = _make_entry(
            target_ec_ms=1.5,
            fertilizer_dosages=[
                FertilizerDosage(fertilizer_key="f1", ml_per_liter=2.4),
            ],
        )
        # 2.4 * 0.5 = 1.2, delta = 0.3 (exactly at tolerance)
        result = validator.validate_ec_budget(entry, {"f1": fert})
        assert result["valid"] is True
