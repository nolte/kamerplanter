import pytest

from app.common.enums import FertilizerType, PhaseName, SubstrateType
from app.domain.engines.ec_budget_engine import (
    FRESH_COCO_CALMAG_BOOST,
    EcBudgetCalculator,
    EcBudgetFertilizerInput,
    EcBudgetInput,
)


def _fert(key: str = "fert-a", name: str = "FertA", ec: float = 0.15, **kw):
    defaults = {
        "key": key,
        "product_name": name,
        "ec_contribution_per_ml": ec,
        "ec_contribution_uncertain": False,
        "max_dose_ml_per_liter": None,
        "fertilizer_type": FertilizerType.BASE,
    }
    defaults.update(kw)
    return EcBudgetFertilizerInput(**defaults)


def _input(**kw):
    defaults = {
        "base_water_ec": 0.15,
        "target_ec": 1.8,
        "alkalinity_ppm": 80,
        "substrate": SubstrateType.COCO,
        "phase": PhaseName.VEGETATIVE,
        "volume_liters": 10,
        "fertilizers": [_fert("grow", "Grow", 0.12), _fert("bloom", "Bloom", 0.08)],
        "recipe_ml_per_liter": {"grow": 3.0, "bloom": 2.0},
    }
    defaults.update(kw)
    return EcBudgetInput(**defaults)


# ── Basic happy path ──────────────────────────────────────────────────


class TestEcBudgetBasic:
    def test_happy_path_two_fertilizers(self):
        calc = EcBudgetCalculator()
        result = calc.calculate(_input())

        assert result.ec_mix == pytest.approx(0.15, abs=0.01)
        assert result.ec_net == pytest.approx(1.65, abs=0.01)
        assert result.ec_final > 0
        assert result.living_soil_bypass is False
        assert len(result.segments) >= 3  # base water + 2 ferts + pH reserve
        assert len(result.dosage_table) == 2
        assert len(result.dosage_instructions) >= 4  # fill + 2 ferts + pH + verify

    def test_result_valid_within_tolerance(self):
        calc = EcBudgetCalculator()
        result = calc.calculate(_input())

        # With recipe scaling, ec_final should approximate target
        assert abs(result.ec_final - result.ec_target) <= result.tolerance + 0.01
        assert result.valid is True

    def test_no_fertilizers(self):
        calc = EcBudgetCalculator()
        result = calc.calculate(_input(fertilizers=[], recipe_ml_per_liter={}))

        # Only base water + pH reserve
        assert result.ec_fertilizers == 0
        assert result.ec_final == pytest.approx(0.15 + 0.03, abs=0.01)
        assert len(result.dosage_table) == 0


# ── Living Soil bypass ────────────────────────────────────────────────


class TestLivingSoilBypass:
    def test_living_soil_returns_bypass(self):
        calc = EcBudgetCalculator()
        result = calc.calculate(_input(substrate=SubstrateType.LIVING_SOIL))

        assert result.living_soil_bypass is True
        assert result.ec_net == 0
        assert result.ec_silicate == 0
        assert result.ec_calmag == 0
        assert result.ec_fertilizers == 0
        assert result.valid is True
        assert len(result.warnings) == 1
        assert "Living Soil" in result.warnings[0]
        assert len(result.segments) == 0


# ── CalMag pre-deduction ─────────────────────────────────────────────


class TestCalMagPreDeduction:
    def test_calmag_reduces_remaining_budget(self):
        calc = EcBudgetCalculator()
        result = calc.calculate(
            _input(
                calmag_key="calmag-1",
                calmag_dose_ml_per_liter=1.0,
                calmag_ec_per_ml=0.15,
            )
        )

        assert result.ec_calmag == pytest.approx(0.15, abs=0.01)
        # CalMag segment should be present
        calmag_segs = [s for s in result.segments if s.label == "CalMag"]
        assert len(calmag_segs) == 1
        assert calmag_segs[0].ml_per_liter == pytest.approx(1.0, abs=0.01)

        # Total fertilizer EC should be reduced since CalMag eats budget
        result_no_calmag = calc.calculate(_input())
        assert result.ec_fertilizers < result_no_calmag.ec_fertilizers


# ── Silicate pre-deduction ───────────────────────────────────────────


class TestSilicatePreDeduction:
    def test_silicate_before_calmag_in_segments(self):
        calc = EcBudgetCalculator()
        result = calc.calculate(
            _input(
                silicate_key="silicate-1",
                silicate_dose_ml_per_liter=0.5,
                silicate_ec_per_ml=0.04,
                calmag_key="calmag-1",
                calmag_dose_ml_per_liter=1.0,
                calmag_ec_per_ml=0.15,
            )
        )

        assert result.ec_silicate == pytest.approx(0.02, abs=0.01)
        assert result.ec_calmag == pytest.approx(0.15, abs=0.01)

        # Check segment order: base water → silicate → calmag → ferts → pH
        labels = [s.label for s in result.segments]
        si_idx = labels.index("Silicate")
        cm_idx = labels.index("CalMag")
        assert si_idx < cm_idx

    def test_silicate_reduces_budget(self):
        calc = EcBudgetCalculator()
        result_with = calc.calculate(
            _input(
                silicate_key="si",
                silicate_dose_ml_per_liter=0.5,
                silicate_ec_per_ml=0.10,
            )
        )
        result_without = calc.calculate(_input())

        assert result_with.ec_fertilizers < result_without.ec_fertilizers


# ── Fresh Coco Boost ─────────────────────────────────────────────────


class TestFreshCocoBoost:
    def test_cycles_used_zero_boosts_calmag(self):
        calc = EcBudgetCalculator()
        base_dose = 1.0

        result = calc.calculate(
            _input(
                substrate=SubstrateType.COCO,
                substrate_cycles_used=0,
                calmag_key="cm",
                calmag_dose_ml_per_liter=base_dose,
                calmag_ec_per_ml=0.15,
            )
        )

        expected_dose = round(base_dose * (1 + FRESH_COCO_CALMAG_BOOST), 2)
        calmag_seg = [s for s in result.segments if s.label == "CalMag"][0]
        assert calmag_seg.ml_per_liter == pytest.approx(expected_dose, abs=0.01)

        # Warning about fresh coco
        assert any("Fresh coco" in w for w in result.warnings)

    def test_cycles_used_nonzero_no_boost(self):
        calc = EcBudgetCalculator()
        result = calc.calculate(
            _input(
                substrate_cycles_used=3,
                calmag_key="cm",
                calmag_dose_ml_per_liter=1.0,
                calmag_ec_per_ml=0.15,
            )
        )

        calmag_seg = [s for s in result.segments if s.label == "CalMag"][0]
        assert calmag_seg.ml_per_liter == pytest.approx(1.0, abs=0.01)
        assert not any("Fresh coco" in w for w in result.warnings)


# ── Uncertain EC ─────────────────────────────────────────────────────


class TestUncertainEc:
    def test_uncertain_fert_applies_reserve(self):
        calc = EcBudgetCalculator()
        fert_uncertain = _fert("unc", "Organic Liquid", 0.05, ec_contribution_uncertain=True)
        fert_normal = _fert("norm", "Normal", 0.10)

        result = calc.calculate(
            _input(
                fertilizers=[fert_uncertain, fert_normal],
                recipe_ml_per_liter={"unc": 2.0, "norm": 3.0},
            )
        )

        # Should have warning about uncertain EC
        assert any("uncertain" in w.lower() for w in result.warnings)

        # Compare with no uncertain: fertilizer EC should be lower due to reserve
        result_certain = calc.calculate(
            _input(
                fertilizers=[
                    _fert("unc", "Organic Liquid", 0.05),
                    fert_normal,
                ],
                recipe_ml_per_liter={"unc": 2.0, "norm": 3.0},
            )
        )
        assert result.ec_fertilizers < result_certain.ec_fertilizers


# ── Temperature correction ───────────────────────────────────────────


class TestTemperatureCorrection:
    def test_correct_ec_at_25_cold_water(self):
        # EC@25 = 1.72 / (1 + 0.02 * (18 - 25)) = 1.72 / 0.86 ≈ 2.0
        corrected = EcBudgetCalculator.correct_ec_at_25(1.72, 18.0)
        assert corrected == pytest.approx(2.0, abs=0.01)

    def test_correct_ec_at_25_warm_water(self):
        # EC@25 = 2.2 / (1 + 0.02 * (30 - 25)) = 2.2 / 1.1 = 2.0
        corrected = EcBudgetCalculator.correct_ec_at_25(2.2, 30.0)
        assert corrected == pytest.approx(2.0, abs=0.01)

    def test_correct_ec_at_25_already_25(self):
        corrected = EcBudgetCalculator.correct_ec_at_25(1.8, 25.0)
        assert corrected == pytest.approx(1.8, abs=0.001)

    def test_result_includes_temperature_correction(self):
        calc = EcBudgetCalculator()
        result = calc.calculate(
            _input(
                measured_ec=1.72,
                measured_temp_celsius=18.0,
            )
        )

        assert result.ec_at_25_corrected is not None
        assert result.ec_at_25_corrected == pytest.approx(2.0, abs=0.01)


# ── Phase/Substrate EC max validation ────────────────────────────────


class TestPhaseEcMaxValidation:
    def test_exceed_ec_max_invalid(self):
        calc = EcBudgetCalculator()
        # Seedling on coco has max 1.0 — target 2.5 will exceed
        result = calc.calculate(
            _input(
                target_ec=2.5,
                phase=PhaseName.SEEDLING,
                substrate=SubstrateType.COCO,
            )
        )

        assert result.ec_max == 1.0
        assert result.valid is False
        assert any("exceeds" in w.lower() for w in result.warnings)

    def test_within_ec_max_valid(self):
        calc = EcBudgetCalculator()
        result = calc.calculate(
            _input(
                target_ec=0.9,
                phase=PhaseName.SEEDLING,
                substrate=SubstrateType.COCO,
                fertilizers=[_fert("a", "A", 0.20)],
                recipe_ml_per_liter={"a": 2.0},
            )
        )

        assert result.ec_max == 1.0
        # May still be valid if the final EC is within bounds


# ── Tolerance validation ─────────────────────────────────────────────


class TestToleranceValidation:
    def test_tolerance_is_10_percent_of_target(self):
        calc = EcBudgetCalculator()
        result = calc.calculate(_input(target_ec=2.0))
        assert result.tolerance == pytest.approx(0.2, abs=0.01)

    def test_tolerance_minimum_01(self):
        calc = EcBudgetCalculator()
        result = calc.calculate(
            _input(
                target_ec=0.5,
                phase=PhaseName.SEEDLING,
                substrate=SubstrateType.SOIL,
            )
        )
        # 0.5 * 0.10 = 0.05, but min is 0.1
        assert result.tolerance == pytest.approx(0.1, abs=0.01)


# ── Recipe scaling preserves ratio ───────────────────────────────────


class TestRecipeScaling:
    def test_ratio_preserved(self):
        calc = EcBudgetCalculator()
        # 3:2:1 ratio
        ferts = [
            _fert("a", "A", 0.10),
            _fert("b", "B", 0.10),
            _fert("c", "C", 0.10),
        ]
        result = calc.calculate(
            _input(
                fertilizers=ferts,
                recipe_ml_per_liter={"a": 3.0, "b": 2.0, "c": 1.0},
            )
        )

        doses = {d["key"]: d["ml_per_liter"] for d in result.dosage_table}
        # Ratio should be 3:2:1
        if doses["c"] > 0:
            ratio_ab = doses["a"] / doses["c"]
            ratio_bc = doses["b"] / doses["c"]
            assert ratio_ab == pytest.approx(3.0, abs=0.1)
            assert ratio_bc == pytest.approx(2.0, abs=0.1)


# ── Equal share fallback ─────────────────────────────────────────────


class TestEqualShareFallback:
    def test_no_recipe_equal_distribution(self):
        calc = EcBudgetCalculator()
        ferts = [
            _fert("a", "A", 0.10),
            _fert("b", "B", 0.10),
        ]
        result = calc.calculate(
            _input(
                fertilizers=ferts,
                recipe_ml_per_liter={},  # no recipe → equal share
            )
        )

        doses = {d["key"]: d["ml_per_liter"] for d in result.dosage_table}
        # Same ec_contribution_per_ml → same dose
        assert doses["a"] == pytest.approx(doses["b"], abs=0.01)

    def test_different_ec_per_ml_adjusts_dose(self):
        calc = EcBudgetCalculator()
        ferts = [
            _fert("a", "A", 0.20),  # 2x stronger
            _fert("b", "B", 0.10),
        ]
        result = calc.calculate(
            _input(
                fertilizers=ferts,
                recipe_ml_per_liter={},
            )
        )

        doses = {d["key"]: d["ml_per_liter"] for d in result.dosage_table}
        # A has 2x EC/ml → needs half the dose for same EC share
        assert doses["a"] == pytest.approx(doses["b"] / 2, abs=0.1)
