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

    def test_calmag_hyphenated_name_wrong_order(self, validator):
        """'Cal-Mag Plus' must be recognised via the normalized name fallback."""
        ferts = [
            _make_fert(product_name="Cal-Mag Plus", fertilizer_type=FertilizerType.SUPPLEMENT, mixing_priority=20),
            _make_fert(product_name="Epsom Salt", mixing_priority=10),
        ]
        result = validator.validate_combination(ferts)
        assert result["safe"] is False
        assert any("CRITICAL" in w for w in result["warnings"])

    def test_calmag_by_type_wrong_order(self, validator):
        """'CaliMagic' typed CALMAG is recognised purely by its structured type."""
        ferts = [
            _make_fert(product_name="CaliMagic", fertilizer_type=FertilizerType.CALMAG, mixing_priority=20),
            _make_fert(product_name="Epsom Salt", mixing_priority=10),
        ]
        result = validator.validate_combination(ferts)
        assert result["safe"] is False
        assert any("CRITICAL" in w for w in result["warnings"])

    def test_bittersalz_recognised_as_sulfate(self, validator):
        """'Bittersalz' (German Epsom) triggers the CalMag-before-sulfate rule."""
        ferts = [
            _make_fert(product_name="Cal-Mag", fertilizer_type=FertilizerType.CALMAG, mixing_priority=30),
            _make_fert(product_name="Bittersalz", mixing_priority=10),
        ]
        result = validator.validate_combination(ferts)
        assert any("CRITICAL" in w for w in result["warnings"])

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
