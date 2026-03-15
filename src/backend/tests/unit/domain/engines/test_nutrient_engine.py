import pytest

from app.common.enums import (
    ApplicationMethod,
    FertilizerType,
    PhEffect,
    SubstrateType,
)
from app.domain.engines.nutrient_engine import (
    FlushingProtocol,
    MixingSafetyValidator,
    NutrientSolutionCalculator,
    RunoffAnalyzer,
)
from app.domain.models.fertilizer import Fertilizer


def _make_fert(**kwargs) -> Fertilizer:
    defaults = {
        "product_name": "Test Fert",
        "fertilizer_type": FertilizerType.BASE,
        "npk_ratio": (5.0, 5.0, 5.0),
        "ec_contribution_per_ml": 0.1,
        "mixing_priority": 50,
    }
    defaults.update(kwargs)
    return Fertilizer(**defaults)


# ── NutrientSolutionCalculator ───────────────────────────────────────


class TestNutrientSolutionCalculator:
    @pytest.fixture
    def calculator(self):
        return NutrientSolutionCalculator()

    def test_basic_calculation(self, calculator):
        fert = _make_fert(ec_contribution_per_ml=0.1, npk_ratio=(10.0, 5.0, 5.0))
        result = calculator.calculate(
            target_volume_liters=10.0,
            target_ec_ms=1.5,
            target_ph=6.0,
            base_water_ec=0.3,
            base_water_ph=7.0,
            fertilizers=[fert],
        )
        assert result["calculated_ec"] > 0
        assert len(result["dosages"]) == 1
        assert result["dosages"][0]["ml_per_liter"] > 0

    def test_no_ec_budget(self, calculator):
        fert = _make_fert()
        result = calculator.calculate(
            target_volume_liters=10.0,
            target_ec_ms=0.3,
            target_ph=6.0,
            base_water_ec=0.5,
            base_water_ph=7.0,
            fertilizers=[fert],
        )
        assert "No EC budget" in result["warnings"][0]

    def test_empty_fertilizers(self, calculator):
        result = calculator.calculate(
            target_volume_liters=10.0,
            target_ec_ms=1.5,
            target_ph=6.0,
            base_water_ec=0.3,
            base_water_ph=7.0,
            fertilizers=[],
        )
        assert result["dosages"] == []
        assert result["calculated_ec"] == 0.3

    def test_multiple_fertilizers_equal_share(self, calculator):
        """Without recipe, equal EC share: each gets 50% of available EC."""
        ferts = [
            _make_fert(
                key="a",
                product_name="A",
                npk_ratio=(10.0, 0.0, 0.0),
                ec_contribution_per_ml=0.1,
                mixing_priority=10,
            ),
            _make_fert(
                key="b",
                product_name="B",
                npk_ratio=(0.0, 10.0, 0.0),
                ec_contribution_per_ml=0.1,
                mixing_priority=20,
            ),
        ]
        result = calculator.calculate(
            target_volume_liters=10.0,
            target_ec_ms=2.0,
            target_ph=6.0,
            base_water_ec=0.3,
            base_water_ph=7.0,
            fertilizers=ferts,
        )
        assert len(result["dosages"]) == 2
        assert result["dosages"][0]["product_name"] == "A"
        # Equal share: each contributes 0.85 mS → 8.5 ml/L
        assert result["dosages"][0]["ml_per_liter"] == pytest.approx(
            result["dosages"][1]["ml_per_liter"],
            abs=0.01,
        )

    def test_recipe_scaling(self, calculator):
        """With recipe_ml_per_liter, scaling preserves manufacturer ratios."""
        ferts = [
            _make_fert(key="a", product_name="A", ec_contribution_per_ml=0.2, mixing_priority=10),
            _make_fert(key="b", product_name="B", ec_contribution_per_ml=0.1, mixing_priority=20),
        ]
        # Manufacturer recipe: A=2ml/L, B=4ml/L → EC_recipe = 2*0.2 + 4*0.1 = 0.8
        # Available EC = 1.6, k = 1.6/0.8 = 2.0 → A=4ml/L, B=8ml/L
        result = calculator.calculate(
            target_volume_liters=10.0,
            target_ec_ms=2.0,
            target_ph=6.0,
            base_water_ec=0.4,
            base_water_ph=7.0,
            fertilizers=ferts,
            recipe_ml_per_liter={"a": 2.0, "b": 4.0},
        )
        assert result["dosages"][0]["ml_per_liter"] == pytest.approx(4.0, abs=0.01)
        assert result["dosages"][1]["ml_per_liter"] == pytest.approx(8.0, abs=0.01)
        assert result["calculated_ec"] == pytest.approx(2.0, abs=0.01)

    def test_ph_adjustment_down(self, calculator):
        result = calculator.calculate(
            target_volume_liters=10.0,
            target_ec_ms=1.5,
            target_ph=5.8,
            base_water_ec=0.3,
            base_water_ph=7.2,
            fertilizers=[_make_fert()],
        )
        assert result["ph_adjustment"]["needed"] is True
        assert result["ph_adjustment"]["direction"] == "down"

    def test_ph_no_adjustment_needed(self, calculator):
        result = calculator.calculate(
            target_volume_liters=10.0,
            target_ec_ms=1.5,
            target_ph=6.0,
            base_water_ec=0.3,
            base_water_ph=6.1,
            fertilizers=[_make_fert()],
        )
        assert result["ph_adjustment"]["needed"] is False

    def test_instructions_generated(self, calculator):
        result = calculator.calculate(
            target_volume_liters=10.0,
            target_ec_ms=1.5,
            target_ph=6.0,
            base_water_ec=0.3,
            base_water_ph=7.0,
            fertilizers=[_make_fert()],
        )
        assert len(result["instructions"]) >= 3
        assert "Fill container" in result["instructions"][0]

    def test_zero_ec_contribution_handled(self, calculator):
        fert = _make_fert(ec_contribution_per_ml=0.0)
        result = calculator.calculate(
            target_volume_liters=10.0,
            target_ec_ms=1.5,
            target_ph=6.0,
            base_water_ec=0.3,
            base_water_ph=7.0,
            fertilizers=[fert],
        )
        assert result["dosages"][0]["ml_per_liter"] == 0


# ── FlushingProtocol ─────────────────────────────────────────────────


class TestFlushingProtocol:
    @pytest.fixture
    def protocol(self):
        return FlushingProtocol()

    def test_coco_flush(self, protocol):
        result = protocol.generate(
            current_ec_ms=2.0,
            days_until_harvest=21,
            substrate_type=SubstrateType.COCO,
        )
        assert result["substrate_type"] == "coco"
        assert 10 <= result["recommended_flush_days"] <= 21
        assert len(result["schedule"]) > 0

    def test_hydro_flush_shorter(self, protocol):
        result = protocol.generate(
            current_ec_ms=2.0,
            days_until_harvest=14,
            substrate_type=SubstrateType.HYDRO_SOLUTION,
        )
        assert result["recommended_flush_days"] <= 14

    def test_soil_flush_longer(self, protocol):
        result = protocol.generate(
            current_ec_ms=2.0,
            days_until_harvest=30,
            substrate_type=SubstrateType.SOIL,
        )
        assert result["recommended_flush_days"] >= 14

    def test_schedule_progression(self, protocol):
        result = protocol.generate(
            current_ec_ms=2.0,
            days_until_harvest=21,
            substrate_type=SubstrateType.COCO,
        )
        schedule = result["schedule"]
        # Last entry should be plain water (dosage 0%)
        assert schedule[-1]["dosage_percent"] == 0
        # First entry should have higher dosage
        assert schedule[0]["dosage_percent"] > schedule[-1]["dosage_percent"]

    def test_short_harvest_window(self, protocol):
        result = protocol.generate(
            current_ec_ms=1.5,
            days_until_harvest=5,
            substrate_type=SubstrateType.HYDRO_SOLUTION,
        )
        assert result["recommended_flush_days"] >= 5


# ── RunoffAnalyzer ───────────────────────────────────────────────────


class TestRunoffAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return RunoffAnalyzer()

    def test_salt_buildup(self, analyzer):
        result = analyzer.analyze(
            input_ec_ms=1.5,
            runoff_ec_ms=2.5,
            input_ph=6.0,
            runoff_ph=6.2,
            input_volume_liters=2.0,
            runoff_volume_liters=0.4,
        )
        assert result["ec_status"] == "SALT_BUILDUP"
        assert result["overall_health"] == "POOR"

    def test_ec_warning(self, analyzer):
        result = analyzer.analyze(
            input_ec_ms=1.5,
            runoff_ec_ms=1.9,
            input_ph=6.0,
            runoff_ph=6.1,
            input_volume_liters=2.0,
            runoff_volume_liters=0.4,
        )
        assert result["ec_status"] == "WARNING"

    def test_ec_ok(self, analyzer):
        result = analyzer.analyze(
            input_ec_ms=1.5,
            runoff_ec_ms=1.6,
            input_ph=6.0,
            runoff_ph=6.1,
            input_volume_liters=2.0,
            runoff_volume_liters=0.4,
        )
        assert result["ec_status"] == "OK"

    def test_underfed(self, analyzer):
        result = analyzer.analyze(
            input_ec_ms=1.5,
            runoff_ec_ms=1.0,
            input_ph=6.0,
            runoff_ph=6.1,
            input_volume_liters=2.0,
            runoff_volume_liters=0.4,
        )
        assert result["ec_status"] == "UNDERFED"

    def test_ph_drift(self, analyzer):
        result = analyzer.analyze(
            input_ec_ms=1.5,
            runoff_ec_ms=1.6,
            input_ph=6.0,
            runoff_ph=7.0,
            input_volume_liters=2.0,
            runoff_volume_liters=0.4,
        )
        assert result["ph_status"] == "DRIFT"

    def test_low_runoff_volume(self, analyzer):
        result = analyzer.analyze(
            input_ec_ms=1.5,
            runoff_ec_ms=1.6,
            input_ph=6.0,
            runoff_ph=6.1,
            input_volume_liters=2.0,
            runoff_volume_liters=0.1,
        )
        assert result["volume_status"] == "LOW"

    def test_high_runoff_volume(self, analyzer):
        result = analyzer.analyze(
            input_ec_ms=1.5,
            runoff_ec_ms=1.6,
            input_ph=6.0,
            runoff_ph=6.1,
            input_volume_liters=2.0,
            runoff_volume_liters=1.0,
        )
        assert result["volume_status"] == "HIGH"

    def test_ideal_runoff(self, analyzer):
        result = analyzer.analyze(
            input_ec_ms=1.5,
            runoff_ec_ms=1.6,
            input_ph=6.0,
            runoff_ph=6.1,
            input_volume_liters=2.0,
            runoff_volume_liters=0.4,
        )
        assert result["volume_status"] == "OK"
        assert result["overall_health"] == "GOOD"

    def test_runoff_percent_calculation(self, analyzer):
        result = analyzer.analyze(
            input_ec_ms=1.5,
            runoff_ec_ms=1.6,
            input_ph=6.0,
            runoff_ph=6.1,
            input_volume_liters=10.0,
            runoff_volume_liters=2.0,
        )
        assert result["runoff_percent"] == 20.0


# ── MixingSafetyValidator ────────────────────────────────────────────


class TestMixingSafetyValidator:
    @pytest.fixture
    def validator(self):
        return MixingSafetyValidator()

    def test_safe_combination(self, validator):
        ferts = [
            _make_fert(product_name="Base A"),
            _make_fert(product_name="Base B"),
        ]
        result = validator.validate_combination(ferts)
        assert result["safe"] is True
        assert len(result["warnings"]) == 0

    def test_calmag_sulfate_wrong_order(self, validator):
        ferts = [
            _make_fert(product_name="CalMag", mixing_priority=60),
            _make_fert(product_name="Epsom Salt", mixing_priority=10),
        ]
        result = validator.validate_combination(ferts)
        assert result["safe"] is False
        assert any("CRITICAL" in w for w in result["warnings"])

    def test_calmag_sulfate_correct_order(self, validator):
        ferts = [
            _make_fert(product_name="CalMag", mixing_priority=10),
            _make_fert(product_name="Epsom Salt", mixing_priority=60),
        ]
        result = validator.validate_combination(ferts)
        assert not any("CalMag" in w and "CRITICAL" in w for w in result["warnings"])

    def test_ph_conflict_warning(self, validator):
        ferts = [
            _make_fert(product_name="Acid Product", ph_effect=PhEffect.ACIDIC),
            _make_fert(product_name="Alkaline Product", ph_effect=PhEffect.ALKALINE),
        ]
        result = validator.validate_combination(ferts)
        assert result["safe"] is False
        assert any("pH" in w for w in result["warnings"])

    def test_foliar_fertigation_mix_warning(self, validator):
        ferts = [
            _make_fert(product_name="Foliar Only", recommended_application=ApplicationMethod.FOLIAR),
            _make_fert(product_name="Drip Feed", recommended_application=ApplicationMethod.FERTIGATION),
        ]
        result = validator.validate_combination(ferts)
        assert any("foliar" in w.lower() for w in result["warnings"])

    def test_temperature_biological_too_hot(self, validator):
        result = validator.validate_temperature(40.0, FertilizerType.BIOLOGICAL)
        assert result["ok"] is False

    def test_temperature_too_cold(self, validator):
        result = validator.validate_temperature(3.0, FertilizerType.BASE)
        assert result["ok"] is False

    def test_temperature_optimal(self, validator):
        result = validator.validate_temperature(20.0, FertilizerType.BASE)
        assert result["ok"] is True

    def test_temperature_warm_warning(self, validator):
        result = validator.validate_temperature(32.0, FertilizerType.BASE)
        assert result["ok"] is True
        assert "high" in result["message"].lower()
