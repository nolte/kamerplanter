"""Tests for WaterMixCalculator.recommend_mix_ratio() — REQ-004 v3.3."""

import pytest

from app.domain.engines.water_mix_engine import (
    CA_MG_RATIO_MIN_RO_BUMP,
    CHLORAMINE_LIMIT_LIVING_PPM,
    CHLORAMINE_LIMIT_PPM,
    CHLORINE_LIMIT_LIVING_PPM,
    CHLORINE_LIMIT_PPM,
    DEFAULT_HEADROOM,
    FALLBACK_RO_PERCENT,
    FLUSH_MIN_RO_PERCENT,
    SUBSTRATE_ALKALINITY_LIMIT,
    SUBSTRATE_HEADROOM,
    WaterMixCalculator,
)
from app.domain.models.site import RoWaterProfile, TapWaterProfile


def _make_tap(**kwargs) -> TapWaterProfile:
    defaults = {
        "ec_ms": 0.4,
        "ph": 7.5,
        "alkalinity_ppm": 50,  # low enough to not trigger alkalinity constraint
        "gh_ppm": 200,
        "calcium_ppm": 60,
        "magnesium_ppm": 15,  # Ca:Mg = 4:1 (healthy ratio)
        "chlorine_ppm": 0.3,
        "chloramine_ppm": 0.1,
    }
    defaults.update(kwargs)
    return TapWaterProfile(**defaults)


def _make_ro(**kwargs) -> RoWaterProfile:
    defaults = {"ec_ms": 0.02, "ph": 6.5}
    defaults.update(kwargs)
    return RoWaterProfile(**defaults)


class TestRecommendMixRatio:
    """Tests for the recommend_mix_ratio method."""

    def test_soft_water_needs_no_ro(self):
        """Very soft tap water (EC 0.1) should need 0% RO for a 1.2 target EC."""
        calc = WaterMixCalculator()
        tap = _make_tap(ec_ms=0.1, chlorine_ppm=0.0, chloramine_ppm=0.0)
        ro = _make_ro()

        result = calc.recommend_mix_ratio(
            tap=tap, ro=ro, target_ec_ms=1.2, substrate_type="coco",
        )

        assert result.recommended_ro_percent == 0
        assert result.available_ec_for_nutrients > 0
        assert result.ec_headroom > SUBSTRATE_HEADROOM["coco"]

    def test_hard_water_needs_high_ro(self):
        """Hard tap water (EC 0.8) with 1.2 target on hydro needs significant RO."""
        calc = WaterMixCalculator()
        tap = _make_tap(ec_ms=0.8, chlorine_ppm=0.2, chloramine_ppm=0.1)
        ro = _make_ro()

        result = calc.recommend_mix_ratio(
            tap=tap, ro=ro, target_ec_ms=1.2, substrate_type="hydro_solution",
        )

        # Hydro needs 95% headroom → almost pure RO needed
        assert result.recommended_ro_percent >= 40
        headroom = result.available_ec_for_nutrients / result.target_ec_ms
        assert headroom >= SUBSTRATE_HEADROOM["hydro_solution"]

    def test_very_hard_water_triggers_fallback(self):
        """Extremely hard water (EC 1.5) with low target (0.8) should trigger fallback."""
        calc = WaterMixCalculator()
        tap = _make_tap(ec_ms=1.5, chlorine_ppm=0.2, chloramine_ppm=0.1)
        ro = _make_ro(ec_ms=0.03)

        result = calc.recommend_mix_ratio(
            tap=tap, ro=ro, target_ec_ms=0.8, substrate_type="hydro_solution",
        )

        assert result.recommended_ro_percent >= 70

    def test_high_chlorine_forces_higher_ro(self):
        """High chlorine in tap water should push RO% higher even if EC is fine."""
        calc = WaterMixCalculator()
        tap = _make_tap(ec_ms=0.2, chlorine_ppm=1.5, chloramine_ppm=0.0)
        ro = _make_ro()

        result = calc.recommend_mix_ratio(
            tap=tap, ro=ro, target_ec_ms=1.5, substrate_type="soil",
        )

        # At 0% RO, chlorine = 1.5 > 0.5 limit
        # Need enough RO to bring chlorine below 0.5
        # chlorine at X% RO = 1.5 * (1 - X/100) < 0.5 → X > 66.7
        assert result.recommended_ro_percent >= 70

    def test_high_chloramine_forces_higher_ro(self):
        """High chloramine should push RO% higher."""
        calc = WaterMixCalculator()
        tap = _make_tap(ec_ms=0.2, chlorine_ppm=0.0, chloramine_ppm=0.8)
        ro = _make_ro()

        result = calc.recommend_mix_ratio(
            tap=tap, ro=ro, target_ec_ms=1.5, substrate_type="soil",
        )

        # At 0% RO, chloramine = 0.8 > 0.3 limit
        # chloramine at X% RO = 0.8 * (1 - X/100) < 0.3 → X > 62.5
        assert result.recommended_ro_percent >= 65

    def test_substrate_headroom_soil_vs_hydro(self):
        """Soil (85% headroom) should recommend lower RO% than hydro (95%)."""
        calc = WaterMixCalculator()
        tap = _make_tap(ec_ms=0.5, chlorine_ppm=0.1, chloramine_ppm=0.05)
        ro = _make_ro()

        soil_result = calc.recommend_mix_ratio(
            tap=tap, ro=ro, target_ec_ms=1.2, substrate_type="soil",
        )
        hydro_result = calc.recommend_mix_ratio(
            tap=tap, ro=ro, target_ec_ms=1.2, substrate_type="hydro_solution",
        )

        assert soil_result.recommended_ro_percent <= hydro_result.recommended_ro_percent

    def test_unknown_substrate_uses_default_headroom(self):
        """Unknown substrate type should use DEFAULT_HEADROOM."""
        calc = WaterMixCalculator()
        tap = _make_tap(ec_ms=0.4, chlorine_ppm=0.1, chloramine_ppm=0.05)
        ro = _make_ro()

        result = calc.recommend_mix_ratio(
            tap=tap, ro=ro, target_ec_ms=1.2, substrate_type="unknown_substrate",
        )

        assert result.min_headroom_ratio == DEFAULT_HEADROOM

    def test_calmag_correction_included(self):
        """When target Ca/Mg > 0, recommendation should include CalMag correction."""
        calc = WaterMixCalculator()
        tap = _make_tap()
        ro = _make_ro()

        result = calc.recommend_mix_ratio(
            tap=tap, ro=ro, target_ec_ms=1.2, substrate_type="coco",
            target_ca_ppm=60.0, target_mg_ppm=15.0,
        )

        assert result.calmag_correction is not None
        # At recommended RO%, Ca and Mg will be diluted, so correction is needed
        if result.recommended_ro_percent > 0:
            assert result.calmag_correction.needs_correction is True

    def test_no_calmag_when_targets_zero(self):
        """When no Ca/Mg targets are set, calmag_correction should be None."""
        calc = WaterMixCalculator()
        tap = _make_tap()
        ro = _make_ro()

        result = calc.recommend_mix_ratio(
            tap=tap, ro=ro, target_ec_ms=1.2, substrate_type="coco",
        )

        assert result.calmag_correction is None

    def test_alternatives_generated(self):
        """Recommendation should include alternative RO percentages."""
        calc = WaterMixCalculator()
        tap = _make_tap(ec_ms=0.5, chlorine_ppm=0.1, chloramine_ppm=0.05)
        ro = _make_ro()

        result = calc.recommend_mix_ratio(
            tap=tap, ro=ro, target_ec_ms=1.2, substrate_type="coco",
        )

        # Should have at least 1 alternative (could have up to 3)
        assert len(result.alternatives) >= 1
        for alt in result.alternatives:
            assert alt.ro_percent != result.recommended_ro_percent
            assert 0 <= alt.ro_percent <= 100
            assert len(alt.trade_off) > 0

    def test_reasoning_not_empty(self):
        """Reasoning string should always be populated."""
        calc = WaterMixCalculator()
        tap = _make_tap()
        ro = _make_ro()

        result = calc.recommend_mix_ratio(
            tap=tap, ro=ro, target_ec_ms=1.2, substrate_type="coco",
        )

        assert len(result.reasoning) > 0

    def test_effective_ec_matches_calculation(self):
        """The effective EC in the result should match recalculation."""
        calc = WaterMixCalculator()
        tap = _make_tap(ec_ms=0.6)
        ro = _make_ro()

        result = calc.recommend_mix_ratio(
            tap=tap, ro=ro, target_ec_ms=1.5, substrate_type="coco",
        )

        # Verify consistency
        effective = calc.calculate_effective_water(tap, ro, result.recommended_ro_percent)
        assert result.effective_ec_ms == pytest.approx(effective.ec_ms, abs=0.001)

    def test_all_substrate_headrooms_exist(self):
        """Ensure all specified substrate types have headroom values."""
        # Hydroponic / no CEC
        assert SUBSTRATE_HEADROOM["hydro_solution"] == 0.95
        assert SUBSTRATE_HEADROOM["deep_water_culture"] == 0.95
        assert SUBSTRATE_HEADROOM["aeroponics"] == 0.95
        assert SUBSTRATE_HEADROOM["rockwool_slab"] == 0.95
        assert SUBSTRATE_HEADROOM["rockwool_plug"] == 0.95
        assert SUBSTRATE_HEADROOM["clay_pebbles"] == 0.95
        assert SUBSTRATE_HEADROOM["perlite"] == 0.93
        assert SUBSTRATE_HEADROOM["none"] == 0.95
        # Moderate CEC
        assert SUBSTRATE_HEADROOM["coco"] == 0.90
        assert SUBSTRATE_HEADROOM["vermiculite"] == 0.90
        assert SUBSTRATE_HEADROOM["pon_mineral"] == 0.90
        assert SUBSTRATE_HEADROOM["orchid_bark"] == 0.92
        # High CEC
        assert SUBSTRATE_HEADROOM["soil"] == 0.85
        assert SUBSTRATE_HEADROOM["peat"] == 0.83
        # Special
        assert SUBSTRATE_HEADROOM["sphagnum"] == 0.99
        # living_soil intentionally absent — uses water-quality path
        assert "living_soil" not in SUBSTRATE_HEADROOM
        assert DEFAULT_HEADROOM == 0.85

    def test_all_alkalinity_limits_exist(self):
        """Ensure all substrate types have alkalinity limits."""
        assert SUBSTRATE_ALKALINITY_LIMIT["hydro_solution"] == 60.0
        assert SUBSTRATE_ALKALINITY_LIMIT["rockwool_slab"] == 60.0
        assert SUBSTRATE_ALKALINITY_LIMIT["coco"] == 80.0
        assert SUBSTRATE_ALKALINITY_LIMIT["soil"] == 120.0
        assert SUBSTRATE_ALKALINITY_LIMIT["living_soil"] == 80.0  # microbiome protection
        assert SUBSTRATE_ALKALINITY_LIMIT["sphagnum"] == 10.0

    def test_constants_values(self):
        """Verify safety limit constants."""
        assert CHLORINE_LIMIT_PPM == 0.5
        assert CHLORAMINE_LIMIT_PPM == 0.3
        assert CHLORINE_LIMIT_LIVING_PPM == 0.1
        assert CHLORAMINE_LIMIT_LIVING_PPM == 0.1
        assert FALLBACK_RO_PERCENT == 80

    def test_recommended_ro_in_5_percent_steps(self):
        """Result should be in 5% increments (or fallback of 80%)."""
        calc = WaterMixCalculator()
        tap = _make_tap(ec_ms=0.4)
        ro = _make_ro()

        result = calc.recommend_mix_ratio(
            tap=tap, ro=ro, target_ec_ms=1.2, substrate_type="coco",
        )

        assert result.recommended_ro_percent % 5 == 0

    def test_fallback_when_impossible(self):
        """When target EC is below tap water EC even at 100% RO, use fallback."""
        calc = WaterMixCalculator()
        # RO with unusually high EC
        tap = _make_tap(ec_ms=0.5, chlorine_ppm=0.6, chloramine_ppm=0.4)
        ro = _make_ro(ec_ms=0.4)

        result = calc.recommend_mix_ratio(
            tap=tap, ro=ro, target_ec_ms=0.5, substrate_type="hydro_solution",
        )

        # Nothing can meet all criteria, so fallback
        assert result.recommended_ro_percent == FALLBACK_RO_PERCENT


class TestLivingSoilPath:
    """Tests for the living-soil water-quality-only path."""

    def test_living_soil_uses_water_quality_path(self):
        """Living soil should not use EC headroom logic."""
        calc = WaterMixCalculator()
        tap = _make_tap(ec_ms=0.5, chlorine_ppm=0.0, chloramine_ppm=0.0, alkalinity_ppm=30)
        ro = _make_ro()

        result = calc.recommend_mix_ratio(
            tap=tap, ro=ro, target_ec_ms=1.5, substrate_type="living_soil",
        )

        # EC headroom fields should be 0 (not applicable)
        assert result.target_ec_ms == 0.0
        assert result.min_headroom_ratio == 0.0
        assert result.available_ec_for_nutrients == 0.0
        assert "living soil" in result.reasoning.lower() or "microbiome" in result.reasoning.lower()

    def test_living_soil_clean_water_no_ro(self):
        """Clean tap water (no chlorine, low alkalinity) needs no RO for living soil."""
        calc = WaterMixCalculator()
        tap = _make_tap(ec_ms=0.3, chlorine_ppm=0.0, chloramine_ppm=0.0, alkalinity_ppm=50)
        ro = _make_ro()

        result = calc.recommend_mix_ratio(
            tap=tap, ro=ro, target_ec_ms=1.5, substrate_type="living_soil",
        )

        assert result.recommended_ro_percent == 0

    def test_living_soil_chlorine_forces_ro(self):
        """Even low chlorine (0.2 ppm) should force RO for living soil (limit 0.1)."""
        calc = WaterMixCalculator()
        tap = _make_tap(ec_ms=0.3, chlorine_ppm=0.2, chloramine_ppm=0.0, alkalinity_ppm=30)
        ro = _make_ro()

        result = calc.recommend_mix_ratio(
            tap=tap, ro=ro, target_ec_ms=1.5, substrate_type="living_soil",
        )

        # 0.2 * (1 - X/100) < 0.1 → X > 50
        assert result.recommended_ro_percent >= 50

    def test_living_soil_high_alkalinity_forces_ro(self):
        """High alkalinity should force RO for living soil (limit 80 ppm)."""
        calc = WaterMixCalculator()
        tap = _make_tap(ec_ms=0.2, chlorine_ppm=0.0, chloramine_ppm=0.0, alkalinity_ppm=200)
        ro = _make_ro()

        result = calc.recommend_mix_ratio(
            tap=tap, ro=ro, target_ec_ms=1.5, substrate_type="living_soil",
        )

        # 200 * (1 - X/100) <= 80 → X >= 60
        assert result.recommended_ro_percent >= 60

    def test_living_soil_flush_overrides_quality_path(self):
        """Flush phase on living soil should use standard flush logic."""
        calc = WaterMixCalculator()
        tap = _make_tap(ec_ms=0.3, chlorine_ppm=0.0, chloramine_ppm=0.0, alkalinity_ppm=30)
        ro = _make_ro()

        result = calc.recommend_mix_ratio(
            tap=tap, ro=ro, target_ec_ms=1.0, substrate_type="living_soil",
            phase_name="flushing",
        )

        assert result.recommended_ro_percent >= FLUSH_MIN_RO_PERCENT

    def test_living_soil_chloramine_warning(self):
        """Chloramine in tap water should produce a removal hint."""
        calc = WaterMixCalculator()
        tap = _make_tap(ec_ms=0.3, chlorine_ppm=0.0, chloramine_ppm=0.2, alkalinity_ppm=30)
        ro = _make_ro()

        result = calc.recommend_mix_ratio(
            tap=tap, ro=ro, target_ec_ms=1.5, substrate_type="living_soil",
        )

        assert "chloramine" in result.reasoning.lower()

    def test_sphagnum_uses_water_quality_path(self):
        """Sphagnum should also use water-quality-only path."""
        calc = WaterMixCalculator()
        tap = _make_tap(ec_ms=0.3, chlorine_ppm=0.0, chloramine_ppm=0.0, alkalinity_ppm=30)
        ro = _make_ro()

        result = calc.recommend_mix_ratio(
            tap=tap, ro=ro, target_ec_ms=1.0, substrate_type="sphagnum",
        )

        # Sphagnum has alk limit 10 ppm → 30 * (1-X/100) <= 10 → X >= 67
        assert result.recommended_ro_percent >= 65
        assert "sphagnum" in result.reasoning.lower() or "carnivorous" in result.reasoning.lower()


class TestAlkalinityConstraint:
    """Tests for the alkalinity-based RO% constraint."""

    def test_high_alkalinity_forces_ro(self):
        """High alkalinity (162 ppm) on coco (limit 80) should force RO dilution."""
        calc = WaterMixCalculator()
        tap = _make_tap(ec_ms=0.3, alkalinity_ppm=162, chlorine_ppm=0.0, chloramine_ppm=0.0)
        ro = _make_ro()

        result = calc.recommend_mix_ratio(
            tap=tap, ro=ro, target_ec_ms=2.0, substrate_type="coco",
        )

        # EC headroom is fine at 0%, but alkalinity 162 > 80 coco limit
        # Need ~50% RO to bring alk below 80 → 162 * 0.5 = 81
        assert result.recommended_ro_percent >= 50
        assert "lkalinity" in result.reasoning

    def test_low_alkalinity_no_penalty(self):
        """Low alkalinity (40 ppm) should not increase RO beyond EC needs."""
        calc = WaterMixCalculator()
        tap = _make_tap(ec_ms=0.1, alkalinity_ppm=40, chlorine_ppm=0.0, chloramine_ppm=0.0)
        ro = _make_ro()

        result = calc.recommend_mix_ratio(
            tap=tap, ro=ro, target_ec_ms=1.5, substrate_type="coco",
        )

        assert result.recommended_ro_percent == 0

    def test_soil_tolerates_higher_alkalinity(self):
        """Soil (limit 120) should tolerate alkalinity that forces RO on coco (limit 80)."""
        calc = WaterMixCalculator()
        tap = _make_tap(ec_ms=0.3, alkalinity_ppm=100, chlorine_ppm=0.0, chloramine_ppm=0.0)
        ro = _make_ro()

        coco = calc.recommend_mix_ratio(
            tap=tap, ro=ro, target_ec_ms=1.5, substrate_type="coco",
        )
        soil = calc.recommend_mix_ratio(
            tap=tap, ro=ro, target_ec_ms=1.5, substrate_type="soil",
        )

        # Coco should need more RO than soil for same alkalinity
        assert coco.recommended_ro_percent > soil.recommended_ro_percent


class TestCaMgRatioConstraint:
    """Tests for Ca:Mg ratio-based minimum RO%."""

    def test_high_ca_mg_ratio_bumps_ro(self):
        """Ca:Mg > 5:1 should bump RO% by at least CA_MG_RATIO_MIN_RO_BUMP."""
        calc = WaterMixCalculator()
        # Ca:Mg = 72:7 ≈ 10.3:1
        tap = _make_tap(ec_ms=0.2, calcium_ppm=72, magnesium_ppm=7,
                        alkalinity_ppm=30, chlorine_ppm=0.0, chloramine_ppm=0.0)
        ro = _make_ro()

        result = calc.recommend_mix_ratio(
            tap=tap, ro=ro, target_ec_ms=2.0, substrate_type="coco",
        )

        # Even though EC and alkalinity are fine, Ca:Mg forces min RO
        assert result.recommended_ro_percent >= CA_MG_RATIO_MIN_RO_BUMP
        assert "Ca:Mg" in result.reasoning

    def test_healthy_ca_mg_ratio_no_bump(self):
        """Ca:Mg = 4:1 should not add extra RO%."""
        calc = WaterMixCalculator()
        tap = _make_tap(ec_ms=0.2, calcium_ppm=60, magnesium_ppm=15,
                        alkalinity_ppm=30, chlorine_ppm=0.0, chloramine_ppm=0.0)
        ro = _make_ro()

        result = calc.recommend_mix_ratio(
            tap=tap, ro=ro, target_ec_ms=2.0, substrate_type="coco",
        )

        assert result.recommended_ro_percent == 0
        assert "Ca:Mg" not in result.reasoning

    def test_calmag_warning_high_ratio(self):
        """CalMag correction should warn when final Ca:Mg > 5:1."""
        calc = WaterMixCalculator()
        tap = _make_tap()
        ro = _make_ro()

        result = calc.recommend_mix_ratio(
            tap=tap, ro=ro, target_ec_ms=1.5, substrate_type="coco",
            target_ca_ppm=200, target_mg_ppm=30,  # 6.7:1
        )

        assert result.calmag_correction is not None
        assert result.calmag_correction.ca_mg_ratio is not None
        assert result.calmag_correction.ca_mg_ratio > 5.0
        assert "magnesium lockout" in result.calmag_correction.ca_mg_ratio_warning.lower()

    def test_calmag_warning_low_ratio(self):
        """CalMag correction should warn when final Ca:Mg < 2:1."""
        calc = WaterMixCalculator()
        tap = _make_tap()
        ro = _make_ro()

        result = calc.recommend_mix_ratio(
            tap=tap, ro=ro, target_ec_ms=1.5, substrate_type="coco",
            target_ca_ppm=30, target_mg_ppm=30,  # 1:1
        )

        assert result.calmag_correction is not None
        assert result.calmag_correction.ca_mg_ratio is not None
        assert result.calmag_correction.ca_mg_ratio < 2.0
        assert "calcium deficiency" in result.calmag_correction.ca_mg_ratio_warning.lower()


class TestFlushPhaseConstraint:
    """Tests for flush phase RO% override."""

    def test_flush_forces_high_ro(self):
        """Flush phase should force >= 85% RO regardless of EC headroom."""
        calc = WaterMixCalculator()
        tap = _make_tap(ec_ms=0.3, alkalinity_ppm=30, chlorine_ppm=0.0, chloramine_ppm=0.0)
        ro = _make_ro()

        result = calc.recommend_mix_ratio(
            tap=tap, ro=ro, target_ec_ms=2.0, substrate_type="coco",
            phase_name="flushing",
        )

        assert result.recommended_ro_percent >= FLUSH_MIN_RO_PERCENT
        assert "lush" in result.reasoning

    def test_non_flush_not_affected(self):
        """Non-flush phases should not be affected by flush constraint."""
        calc = WaterMixCalculator()
        tap = _make_tap(ec_ms=0.2, alkalinity_ppm=30, chlorine_ppm=0.0, chloramine_ppm=0.0)
        ro = _make_ro()

        result = calc.recommend_mix_ratio(
            tap=tap, ro=ro, target_ec_ms=2.0, substrate_type="coco",
            phase_name="flowering",
        )

        # Without any constraint triggers, should be 0%
        assert result.recommended_ro_percent == 0
