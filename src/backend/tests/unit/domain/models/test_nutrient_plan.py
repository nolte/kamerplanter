import pytest
from pydantic import ValidationError

from app.common.enums import PhaseName, SubstrateType
from app.domain.models.nutrient_plan import FertilizerDosage, NutrientPlan, NutrientPlanPhaseEntry


class TestFertilizerDosage:
    def test_valid_dosage(self):
        d = FertilizerDosage(fertilizer_key="f1", ml_per_liter=2.5)
        assert d.ml_per_liter == 2.5
        assert d.optional is False

    def test_ml_per_liter_zero_raises(self):
        with pytest.raises(ValidationError):
            FertilizerDosage(fertilizer_key="f1", ml_per_liter=0)

    def test_ml_per_liter_exceeds_max(self):
        with pytest.raises(ValidationError):
            FertilizerDosage(fertilizer_key="f1", ml_per_liter=51)

    def test_ml_per_liter_at_max(self):
        d = FertilizerDosage(fertilizer_key="f1", ml_per_liter=50)
        assert d.ml_per_liter == 50


class TestNutrientPlanPhaseEntry:
    def test_valid_entry(self):
        entry = NutrientPlanPhaseEntry(
            plan_key="p1",
            phase_name=PhaseName.VEGETATIVE,
            sequence_order=1,
            week_start=1,
            week_end=4,
        )
        assert entry.phase_name == PhaseName.VEGETATIVE

    def test_week_end_before_start_raises(self):
        with pytest.raises(ValidationError, match="week_end"):
            NutrientPlanPhaseEntry(
                plan_key="p1",
                phase_name=PhaseName.VEGETATIVE,
                sequence_order=1,
                week_start=5,
                week_end=3,
            )

    def test_week_end_equals_start_is_valid(self):
        """A single-week entry (start == end) is valid."""
        entry = NutrientPlanPhaseEntry(
            plan_key="p1",
            phase_name=PhaseName.VEGETATIVE,
            sequence_order=1,
            week_start=3,
            week_end=3,
        )
        assert entry.week_start == entry.week_end

    def test_npk_negative_raises(self):
        with pytest.raises(ValidationError, match="non-negative"):
            NutrientPlanPhaseEntry(
                plan_key="p1",
                phase_name=PhaseName.VEGETATIVE,
                sequence_order=1,
                week_start=1,
                week_end=4,
                npk_ratio=(-1.0, 0.0, 0.0),
            )

    def test_all_phase_names(self):
        for phase in PhaseName:
            entry = NutrientPlanPhaseEntry(
                plan_key="p1",
                phase_name=phase,
                sequence_order=1,
                week_start=1,
                week_end=2,
            )
            assert entry.phase_name == phase

    def test_key_alias(self):
        entry = NutrientPlanPhaseEntry(
            plan_key="p1",
            phase_name=PhaseName.VEGETATIVE,
            sequence_order=1,
            week_start=1,
            week_end=2,
            **{"_key": "e1"},
        )
        assert entry.key == "e1"


class TestNutrientPlan:
    def test_valid_plan(self):
        plan = NutrientPlan(name="Veg Plan A", author="Admin")
        assert plan.name == "Veg Plan A"
        assert plan.is_template is False
        assert plan.version == "1.0"

    def test_name_too_short(self):
        with pytest.raises(ValidationError):
            NutrientPlan(name="")

    def test_tags_normalized(self):
        plan = NutrientPlan(name="Test", tags=["ORGANIC", "  Indoor ", "coco"])
        assert plan.tags == ["organic", "indoor", "coco"]

    def test_substrate_type(self):
        plan = NutrientPlan(
            name="Test",
            recommended_substrate_type=SubstrateType.COCO,
        )
        assert plan.recommended_substrate_type == SubstrateType.COCO

    def test_key_alias(self):
        plan = NutrientPlan(name="Test", **{"_key": "p1"})
        assert plan.key == "p1"

    def test_cloned_from_key(self):
        plan = NutrientPlan(name="Clone", cloned_from_key="orig")
        assert plan.cloned_from_key == "orig"
