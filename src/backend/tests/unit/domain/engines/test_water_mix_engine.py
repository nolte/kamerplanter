from datetime import date

import pytest

import math

from app.domain.engines.water_mix_engine import (
    WaterMixCalculator,
    WaterSourceValidator,
)
from app.domain.models.site import RoWaterProfile, TapWaterProfile


def _make_tap(**kwargs) -> TapWaterProfile:
    defaults = {
        "ec_ms": 0.4,
        "ph": 7.5,
        "alkalinity_ppm": 120,
        "gh_ppm": 200,
        "calcium_ppm": 60,
        "magnesium_ppm": 15,
        "chlorine_ppm": 0.3,
        "chloramine_ppm": 0.1,
    }
    defaults.update(kwargs)
    return TapWaterProfile(**defaults)


def _make_ro(**kwargs) -> RoWaterProfile:
    defaults = {"ec_ms": 0.02, "ph": 6.5}
    defaults.update(kwargs)
    return RoWaterProfile(**defaults)


# ── WaterMixCalculator ────────────────────────────────────────────────


class TestCalculateEffectiveWater:
    def test_50_50_mix(self):
        calc = WaterMixCalculator()
        tap = _make_tap()
        ro = _make_ro()
        result = calc.calculate_effective_water(tap, ro, ro_percent=50)

        # EC and minerals: linear weighted average
        assert result.ec_ms == pytest.approx(0.21, abs=0.01)
        assert result.calcium_ppm == pytest.approx(30.0, abs=0.01)
        assert result.magnesium_ppm == pytest.approx(7.5, abs=0.01)
        assert result.alkalinity_ppm == pytest.approx(60.0, abs=0.01)
        assert result.chlorine_ppm == pytest.approx(0.15, abs=0.01)
        assert result.chloramine_ppm == pytest.approx(0.05, abs=0.01)

        # pH: logarithmic mixing (H⁺ space) — NOT linear!
        # -log10(10^(-6.5)*0.5 + 10^(-7.5)*0.5) ≈ 6.76
        expected_ph = -math.log10(10**(-6.5) * 0.5 + 10**(-7.5) * 0.5)
        assert result.ph == pytest.approx(expected_ph, abs=0.01)

    def test_100_percent_ro(self):
        calc = WaterMixCalculator()
        tap = _make_tap()
        ro = _make_ro()
        result = calc.calculate_effective_water(tap, ro, ro_percent=100)

        assert result.ec_ms == pytest.approx(0.02, abs=0.001)
        assert result.ph == pytest.approx(6.5, abs=0.01)
        assert result.calcium_ppm == pytest.approx(0.0, abs=0.001)
        assert result.magnesium_ppm == pytest.approx(0.0, abs=0.001)
        assert result.alkalinity_ppm == pytest.approx(0.0, abs=0.001)

    def test_0_percent_ro(self):
        calc = WaterMixCalculator()
        tap = _make_tap()
        ro = _make_ro()
        result = calc.calculate_effective_water(tap, ro, ro_percent=0)

        assert result.ec_ms == pytest.approx(0.4, abs=0.001)
        assert result.ph == pytest.approx(7.5, abs=0.01)
        assert result.calcium_ppm == pytest.approx(60.0, abs=0.001)
        assert result.magnesium_ppm == pytest.approx(15.0, abs=0.001)


class TestCalculateRoPercentForTarget:
    def test_target_between_ro_and_tap(self):
        calc = WaterMixCalculator()
        tap = _make_tap(ec_ms=0.4)
        ro = _make_ro(ec_ms=0.02)
        # Target 0.15 → r = (0.4-0.15)/(0.4-0.02) = 0.6579 → 66%
        result = calc.calculate_ro_percent_for_target(tap, ro, target_ec_ms=0.15)
        assert result == 66

    def test_target_equals_tap(self):
        calc = WaterMixCalculator()
        tap = _make_tap(ec_ms=0.4)
        ro = _make_ro(ec_ms=0.02)
        result = calc.calculate_ro_percent_for_target(tap, ro, target_ec_ms=0.4)
        assert result == 0

    def test_target_below_ro(self):
        calc = WaterMixCalculator()
        tap = _make_tap(ec_ms=0.4)
        ro = _make_ro(ec_ms=0.02)
        result = calc.calculate_ro_percent_for_target(tap, ro, target_ec_ms=0.01)
        assert result == 100

    def test_roundtrip_consistency(self):
        calc = WaterMixCalculator()
        tap = _make_tap(ec_ms=0.5)
        ro = _make_ro(ec_ms=0.03)
        # Calculate RO% for target 0.2
        ro_pct = calc.calculate_ro_percent_for_target(tap, ro, target_ec_ms=0.2)
        # Apply that percent and check EC is close to target
        result = calc.calculate_effective_water(tap, ro, ro_percent=ro_pct)
        assert result.ec_ms == pytest.approx(0.2, abs=0.02)


class TestSuggestCalmagCorrection:
    def test_deficit_detected(self):
        calc = WaterMixCalculator()
        tap = _make_tap()
        ro = _make_ro()
        effective = calc.calculate_effective_water(tap, ro, ro_percent=80)

        correction = calc.suggest_calmag_correction(effective, target_ca_ppm=60, target_mg_ppm=15)

        assert correction.needs_correction is True
        assert correction.calcium_deficit_ppm > 0
        assert correction.magnesium_deficit_ppm > 0

    def test_no_deficit(self):
        calc = WaterMixCalculator()
        tap = _make_tap(calcium_ppm=100, magnesium_ppm=40)
        ro = _make_ro()
        effective = calc.calculate_effective_water(tap, ro, ro_percent=0)

        correction = calc.suggest_calmag_correction(effective, target_ca_ppm=50, target_mg_ppm=20)

        assert correction.needs_correction is False
        assert correction.calcium_deficit_ppm == 0
        assert correction.magnesium_deficit_ppm == 0

    def test_ca_mg_ratio_ideal(self):
        calc = WaterMixCalculator()
        tap = _make_tap()
        ro = _make_ro()
        effective = calc.calculate_effective_water(tap, ro, ro_percent=0)
        # 3.5:1 ratio → ideal range
        correction = calc.suggest_calmag_correction(effective, target_ca_ppm=70, target_mg_ppm=20)
        assert correction.ca_mg_ratio == pytest.approx(3.5, abs=0.01)
        assert correction.ca_mg_ratio_warning is None

    def test_ca_mg_ratio_too_low(self):
        calc = WaterMixCalculator()
        tap = _make_tap()
        ro = _make_ro()
        effective = calc.calculate_effective_water(tap, ro, ro_percent=0)
        # 1.5:1 ratio → too low
        correction = calc.suggest_calmag_correction(effective, target_ca_ppm=30, target_mg_ppm=20)
        assert correction.ca_mg_ratio == pytest.approx(1.5, abs=0.01)
        assert correction.ca_mg_ratio_warning is not None
        assert "low" in correction.ca_mg_ratio_warning.lower()

    def test_ca_mg_ratio_too_high(self):
        calc = WaterMixCalculator()
        tap = _make_tap()
        ro = _make_ro()
        effective = calc.calculate_effective_water(tap, ro, ro_percent=0)
        # 6:1 ratio → too high
        correction = calc.suggest_calmag_correction(effective, target_ca_ppm=120, target_mg_ppm=20)
        assert correction.ca_mg_ratio == pytest.approx(6.0, abs=0.01)
        assert correction.ca_mg_ratio_warning is not None
        assert "high" in correction.ca_mg_ratio_warning.lower()


# ── WaterSourceValidator ──────────────────────────────────────────────


class TestGhPlausibility:
    def test_warning_on_deviation(self):
        validator = WaterSourceValidator()
        # GH of 500 but Ca=10, Mg=5 → expected ≈ 45.5 → huge deviation
        tap = _make_tap(gh_ppm=500, calcium_ppm=10, magnesium_ppm=5)
        warnings = validator.validate_gh_plausibility(tap)

        assert len(warnings) == 1
        assert warnings[0].code == "gh_plausibility"
        assert warnings[0].severity == "warning"

    def test_no_warning_when_plausible(self):
        validator = WaterSourceValidator()
        # Ca=60, Mg=15 → expected GH ≈ 60*2.497 + 15*4.116 ≈ 211.6
        tap = _make_tap(gh_ppm=210, calcium_ppm=60, magnesium_ppm=15)
        warnings = validator.validate_gh_plausibility(tap)

        assert len(warnings) == 0

    def test_no_warning_when_all_zero(self):
        validator = WaterSourceValidator()
        tap = _make_tap(gh_ppm=0, calcium_ppm=0, magnesium_ppm=0)
        warnings = validator.validate_gh_plausibility(tap)

        assert len(warnings) == 0


class TestMeasurementAge:
    def test_warning_when_old(self):
        validator = WaterSourceValidator()
        tap = _make_tap(measurement_date=date(2024, 1, 1))
        warnings = validator.validate_measurement_age(tap, today=date(2026, 2, 28))

        assert len(warnings) == 1
        assert warnings[0].code == "measurement_age"
        assert warnings[0].severity == "info"

    def test_no_warning_when_recent(self):
        validator = WaterSourceValidator()
        tap = _make_tap(measurement_date=date(2026, 1, 1))
        warnings = validator.validate_measurement_age(tap, today=date(2026, 2, 28))

        assert len(warnings) == 0

    def test_no_warning_when_no_date(self):
        validator = WaterSourceValidator()
        tap = _make_tap()
        warnings = validator.validate_measurement_age(tap)

        assert len(warnings) == 0


class TestRoMembrane:
    def test_warning_when_ec_high(self):
        validator = WaterSourceValidator()
        ro = _make_ro(ec_ms=0.12)
        warnings = validator.validate_ro_membrane(ro)

        assert len(warnings) == 1
        assert warnings[0].code == "ro_membrane"
        assert warnings[0].severity == "warning"

    def test_no_warning_when_ec_normal(self):
        validator = WaterSourceValidator()
        ro = _make_ro(ec_ms=0.02)
        warnings = validator.validate_ro_membrane(ro)

        assert len(warnings) == 0


class TestValidateAll:
    def test_no_warnings_for_valid_profile(self):
        validator = WaterSourceValidator()
        # All values plausible and consistent
        tap = _make_tap(
            gh_ppm=210,
            calcium_ppm=60,
            magnesium_ppm=15,
            measurement_date=date(2026, 1, 15),
        )
        ro = _make_ro(ec_ms=0.02)
        warnings = validator.validate_all(tap, ro, today=date(2026, 2, 28))

        assert len(warnings) == 0

    def test_multiple_warnings(self):
        validator = WaterSourceValidator()
        tap = _make_tap(
            gh_ppm=500,
            calcium_ppm=10,
            magnesium_ppm=5,
            measurement_date=date(2024, 1, 1),
        )
        ro = _make_ro(ec_ms=0.15)
        warnings = validator.validate_all(tap, ro, today=date(2026, 2, 28))

        codes = {w.code for w in warnings}
        assert "gh_plausibility" in codes
        assert "measurement_age" in codes
        assert "ro_membrane" in codes
