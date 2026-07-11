"""REQ-026 — unit tests for the aquaponics domain engines."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest

from app.common.enums import (
    AquaponicSystemType,
    CyclingStatus,
    FishFeedCategory,
    FishFeedingResponse,
    TemperatureZone,
)
from app.domain.engines.aquaponics_engine import (
    AquaponicsSafetyValidator,
    BiofilterManager,
    FeedingRateCalculator,
    FishHealthMonitor,
    NitrogenCycleEngine,
    NutrientDeficiencyAnalyzer,
    StockingDensityCalculator,
)
from app.domain.models.aquaponik import (
    AquaponicSystem,
    FishFeedingEvent,
    FishSpecies,
    FishStock,
    WaterTest,
)


def _tilapia() -> FishSpecies:
    return FishSpecies(
        _key="tilapia_nile",
        scientific_name="Oreochromis niloticus",
        common_name_de="Nil-Tilapia",
        common_name_en="Nile Tilapia",
        temperature_zone=TemperatureZone.WARMWATER,
        temperature_min_c=18,
        temperature_max_c=34,
        temperature_optimal_min_c=26,
        temperature_optimal_max_c=30,
        temperature_lethal_low_c=12,
        temperature_lethal_high_c=38,
        ph_min=6.5,
        ph_max=8.5,
        do_minimum_mgl=2.0,
        do_optimal_mgl=5.0,
        do_stress_mgl=3.0,
        max_tan_mgl=2.0,
        max_nitrite_mgl=1.0,
        max_nitrate_mgl=200,
        fcr_hobby=1.8,
        fcr_professional=1.3,
        feed_type=FishFeedCategory.OMNIVORE,
        max_stocking_density_kg_per_1000l=25,
        growth_rate_g_per_day=3.0,
        market_weight_g=500,
        time_to_market_days=180,
    )


def _trout() -> FishSpecies:
    return FishSpecies(
        _key="trout_rainbow",
        scientific_name="Oncorhynchus mykiss",
        common_name_de="Regenbogenforelle",
        common_name_en="Rainbow Trout",
        temperature_zone=TemperatureZone.COLDWATER,
        temperature_min_c=8,
        temperature_max_c=18,
        temperature_optimal_min_c=12,
        temperature_optimal_max_c=16,
        temperature_lethal_low_c=-0.5,
        temperature_lethal_high_c=22,
        ph_min=6.5,
        ph_max=8.0,
        do_minimum_mgl=5.0,
        do_optimal_mgl=8.0,
        do_stress_mgl=6.0,
        max_tan_mgl=0.5,
        max_nitrite_mgl=0.1,
        max_nitrate_mgl=80,
        feed_type=FishFeedCategory.CARNIVORE,
        max_stocking_density_kg_per_1000l=30,
    )


def _system() -> AquaponicSystem:
    return AquaponicSystem(
        name="Tilapia-Salat DWC",
        system_type=AquaponicSystemType.DWC,
        total_volume_liters=640,
        grow_area_m2=4.0,
        daily_feed_target_g=67.5,
        biofilter_type="mbbr",
        biofilter_volume_liters=40,
    )


def _wt(tan, no2, no3, ph=7.2, temp=26.0, tested_at=None, **extra) -> WaterTest:
    return WaterTest(
        system_key="sys1",
        tested_at=tested_at or datetime.now(UTC),
        ph=ph,
        ammonia_tan_mgl=tan,
        nitrite_mgl=no2,
        nitrate_mgl=no3,
        temperature_c=temp,
        **extra,
    )


class TestNitrogenCycleEngine:
    def test_free_ammonia_emerson_vector(self):
        engine = NitrogenCycleEngine()
        # Spec test vector: pH 7.0, 25 C, TAN 1.0 -> ~0.0057 mg/L (+/-5%).
        value = engine.calculate_free_ammonia(1.0, 7.0, 25.0)
        assert value == pytest.approx(0.0057, abs=0.0004)

    def test_do_saturation_curve(self):
        engine = NitrogenCycleEngine()
        assert engine.calculate_do_saturation(15) == pytest.approx(10.1, abs=0.3)
        assert engine.calculate_do_saturation(25) == pytest.approx(8.2, abs=0.4)

    def test_ammonia_spike_is_critical(self):
        engine = NitrogenCycleEngine()
        wt = _wt(3.0, 0.2, 30, ph=7.5, temp=28)
        wt.free_ammonia_mgl = engine.calculate_free_ammonia(3.0, 7.5, 28)
        evals = engine.evaluate_water_quality(wt, _tilapia())
        free = [e for e in evals if e.parameter == "free_ammonia"]
        assert free and free[0].severity == "critical"
        # TAN 3.0 exceeds tilapia max 2.0.
        tan = [e for e in evals if e.parameter == "ammonia_tan"]
        assert tan and tan[0].severity == "critical"

    def test_trout_stricter_than_tilapia_on_nitrite(self):
        engine = NitrogenCycleEngine()
        wt = _wt(0.2, 0.3, 30)
        trout_alerts = engine.evaluate_water_quality(wt, _trout())
        tilapia_alerts = engine.evaluate_water_quality(wt, _tilapia())
        assert any(e.parameter == "nitrite" for e in trout_alerts)
        assert not any(e.parameter == "nitrite" for e in tilapia_alerts)

    def test_temperature_lethal_and_do_saturation(self):
        engine = NitrogenCycleEngine()
        wt = _wt(0.1, 0.05, 20, temp=40, dissolved_oxygen_mgl=1.0)
        alerts = engine.evaluate_water_quality(wt, _tilapia())
        temp = [e for e in alerts if e.parameter == "temperature"]
        assert temp and temp[0].severity == "critical"
        assert any(e.parameter == "dissolved_oxygen" for e in alerts)

    def test_no_species_only_grades_free_ammonia(self):
        engine = NitrogenCycleEngine()
        wt = _wt(3.0, 0.2, 30, ph=7.5, temp=28)
        wt.free_ammonia_mgl = engine.calculate_free_ammonia(3.0, 7.5, 28)
        alerts = engine.evaluate_water_quality(wt, None)
        assert all(e.parameter == "free_ammonia" for e in alerts)

    def test_kh_crash_and_gh_bounds(self):
        engine = NitrogenCycleEngine()
        wt = _wt(0.1, 0.05, 20, kh_dh=3.0, gh_dh=22.0)
        alerts = engine.evaluate_water_quality(wt, _tilapia())
        assert any(e.parameter == "kh" for e in alerts)
        assert any(e.parameter == "gh" for e in alerts)

    def test_cycling_detection_stable_becomes_cycled(self):
        engine = NitrogenCycleEngine()
        base = datetime.now(UTC) - timedelta(days=10)
        tests = [_wt(0.1, 0.05, 40, tested_at=base + timedelta(days=i)) for i in range(8)]
        progress = engine.detect_cycling_phase(tests)
        assert progress.status == CyclingStatus.CYCLED
        assert progress.progress_percent == 100.0

    def test_cycling_detection_in_progress(self):
        engine = NitrogenCycleEngine()
        base = datetime.now(UTC) - timedelta(days=5)
        tests = [
            _wt(4.0, 0.1, 5, tested_at=base),
            _wt(2.0, 3.0, 10, tested_at=base + timedelta(days=2)),
            _wt(0.1, 0.05, 20, tested_at=base + timedelta(days=4)),
        ]
        progress = engine.detect_cycling_phase(tests)
        assert progress.status == CyclingStatus.CYCLING
        assert progress.estimated_completion is not None

    def test_cycling_empty_history_is_new(self):
        engine = NitrogenCycleEngine()
        progress = engine.detect_cycling_phase([])
        assert progress.status == CyclingStatus.NEW
        assert progress.progress_percent == 0.0

    def test_alkalinity_crash_risk(self):
        engine = NitrogenCycleEngine()
        assert engine.check_alkalinity_crash_risk(3.0, 50.0) is not None
        assert engine.check_alkalinity_crash_risk(6.0, 50.0) is None
        assert engine.check_alkalinity_crash_risk(3.0, 0.0) is None


class TestFeedingRateCalculator:
    def test_optimal_temperature_full_feed(self):
        calc = FeedingRateCalculator()
        rec = calc.calculate_daily_feed(2.5, 28, _tilapia(), CyclingStatus.CYCLED)
        assert rec.temperature_factor == 1.0
        assert rec.cycling_factor == 1.0
        assert rec.recommended_g == pytest.approx(2.5 * 1000 * 0.03, abs=0.1)

    def test_below_optimum_reduces_feed(self):
        calc = FeedingRateCalculator()
        rec = calc.calculate_daily_feed(2.5, 22, _tilapia(), CyclingStatus.CYCLED)
        assert 0 < rec.temperature_factor < 1
        assert any("Optimum" in n for n in rec.notes)

    def test_above_max_temperature_stops_feed(self):
        calc = FeedingRateCalculator()
        rec = calc.calculate_daily_feed(2.5, 35, _tilapia(), CyclingStatus.CYCLED)
        assert rec.temperature_factor == 0.0
        assert rec.recommended_g == 0.0

    def test_refused_feeding_zero(self):
        calc = FeedingRateCalculator()
        rec = calc.calculate_daily_feed(2.5, 28, _tilapia(), CyclingStatus.CYCLED, FishFeedingResponse.REFUSED)
        assert rec.recommended_g == 0.0

    def test_cycling_reduces_feed(self):
        calc = FeedingRateCalculator()
        rec = calc.calculate_daily_feed(2.5, 28, _tilapia(), CyclingStatus.CYCLING)
        assert rec.cycling_factor == 0.25

    def test_tan_production_by_protein(self):
        calc = FeedingRateCalculator()
        omni = calc.calculate_tan_production(100, 32.0)
        carni = calc.calculate_tan_production(100, 45.0)
        assert carni > omni

    def test_ramp_up_schedule_temperature_dependent(self):
        calc = FeedingRateCalculator()
        warm = calc.calculate_ramp_up_schedule(100, "post_cycling", 25)
        cool = calc.calculate_ramp_up_schedule(100, "post_cycling", 17)
        cold = calc.calculate_ramp_up_schedule(100, "post_cycling", 10)
        assert len(warm.weeks) < len(cool.weeks)
        assert cold.weeks == []


class TestStockingDensityCalculator:
    def test_validate_stocking_ok(self):
        calc = StockingDensityCalculator()
        stock = FishStock(
            system_key="s",
            name="Tilapia",
            species_key="tilapia_nile",
            count=15,
            initial_count=15,
            avg_weight_g=150,
            stocking_date=date(2026, 3, 1),
        )
        result = calc.validate_stocking(stock, 500, _tilapia(), _system())
        assert result.status == "ok"
        assert result.current_density_kg_per_1000l == pytest.approx(4.5, abs=0.1)

    def test_overstocked(self):
        calc = StockingDensityCalculator()
        stock = FishStock(
            system_key="s",
            name="Tilapia",
            species_key="tilapia_nile",
            count=300,
            initial_count=300,
            avg_weight_g=150,
            stocking_date=date(2026, 3, 1),
        )
        result = calc.validate_stocking(stock, 500, _tilapia(), _system())
        assert result.status == "overstocked"

    def test_max_fish(self):
        calc = StockingDensityCalculator()
        assert calc.calculate_max_fish(1000, _tilapia()) > 0


class TestNutrientDeficiencyAnalyzer:
    def test_iron_deficiency_detected(self):
        analyzer = NutrientDeficiencyAnalyzer()
        wt = _wt(0.1, 0.05, 40, iron_ppm=0.5, potassium_ppm=200, calcium_ppm=80, magnesium_ppm=30)
        report = analyzer.analyze(wt, _system())
        iron = next(f for f in report.findings if f.nutrient == "iron")
        assert iron.status == "deficient"
        assert report.grow_bed_ec_status in ("ok", "out_of_range")

    def test_phosphate_accumulation(self):
        analyzer = NutrientDeficiencyAnalyzer()
        wt = _wt(0.1, 0.05, 40, phosphate_ppm=90)
        report = analyzer.analyze(wt, _system())
        po4 = next(f for f in report.findings if f.nutrient == "phosphate")
        assert po4.status == "excess"

    def test_unknown_when_missing(self):
        analyzer = NutrientDeficiencyAnalyzer()
        report = analyzer.analyze(_wt(0.1, 0.05, 40), _system())
        assert any(f.status == "unknown" for f in report.findings)


class TestAquaponicsSafetyValidator:
    def test_blocks_synthetic_fertilizer(self):
        v = AquaponicsSafetyValidator()
        violation = v.validate_fertilizer_safe(aquaponic_safe=False, system_ph=7.0)
        assert violation and violation.severity == "block"

    def test_fe_edta_warns_above_ph(self):
        v = AquaponicsSafetyValidator()
        violation = v.validate_fertilizer_safe(aquaponic_safe=True, system_ph=7.0, is_fe_edta=True)
        assert violation and violation.violation_type == "fe_edta_ph"

    def test_chloramine_blocks(self):
        v = AquaponicsSafetyValidator()
        assert v.validate_no_chlorine(None, 0.01).severity == "block"
        assert v.validate_no_chlorine(0.01, None).severity == "warning"
        assert v.validate_no_chlorine(0.0, 0.0) is None

    def test_copper_pesticide_blocks(self):
        v = AquaponicsSafetyValidator()
        assert v.validate_no_copper_pesticide(True) is not None
        assert v.validate_no_copper_pesticide(False) is None

    def test_water_change_rate(self):
        v = AquaponicsSafetyValidator()
        assert v.validate_water_change_rate(200, 640) is not None
        assert v.validate_water_change_rate(50, 640) is None

    def test_temperature_incompatibility(self):
        v = AquaponicsSafetyValidator()
        assert v.validate_temperature_compatibility(_tilapia(), "coldwater") is not None
        assert v.validate_temperature_compatibility(_tilapia(), "warmwater") is None


class TestBiofilterManager:
    def test_turnover_rate(self):
        mgr = BiofilterManager()
        assert mgr.calculate_turnover_rate(1280, 640) == 2.0
        assert mgr.calculate_turnover_rate(1280, 0) == 0.0

    def test_dimensioning_sufficient(self):
        mgr = BiofilterManager()
        result = mgr.estimate_required_surface_area(67.5, 26, "mbbr", 40)
        assert result.status in ("sufficient", "marginal", "insufficient")
        assert result.daily_tan_production_g > 0

    def test_nitrification_stops_below_5c(self):
        mgr = BiofilterManager()
        result = mgr.estimate_required_surface_area(67.5, 3, "mbbr", 40)
        assert result.status == "unknown"

    def test_seasonal_reactivation(self):
        mgr = BiofilterManager()
        plan = mgr.seasonal_reactivation_plan(CyclingStatus.DORMANT, 18, 100)
        assert plan is not None
        assert mgr.seasonal_reactivation_plan(CyclingStatus.CYCLED, 18, 100) is None


class TestFishHealthMonitor:
    def _stock(self, count=100, mortality=0) -> FishStock:
        return FishStock(
            system_key="s",
            name="Cohort",
            species_key="tilapia_nile",
            count=count - mortality,
            initial_count=count,
            avg_weight_g=150,
            mortality_count=mortality,
            stocking_date=date(2026, 3, 1),
        )

    def test_mortality_rate_warning(self):
        mon = FishHealthMonitor()
        alerts = mon.evaluate_fish_health(self._stock(mortality=3), [], [], _tilapia())
        assert any(a.alert_type == "mortality_rate" and a.severity == "warning" for a in alerts)

    def test_mortality_rate_critical(self):
        mon = FishHealthMonitor()
        alerts = mon.evaluate_fish_health(self._stock(mortality=6), [], [], _tilapia())
        assert any(a.alert_type == "mortality_rate" and a.severity == "critical" for a in alerts)

    def test_feeding_refusal_alert(self):
        mon = FishHealthMonitor()
        now = datetime.now(UTC)
        feedings = [
            FishFeedingEvent(
                system_key="s",
                stock_key="k",
                fed_at=now - timedelta(hours=i),
                amount_g=10,
                water_temp_c=26,
                fish_response=FishFeedingResponse.REFUSED,
            )
            for i in range(2)
        ]
        alerts = mon.evaluate_fish_health(self._stock(), feedings, [], _tilapia())
        assert any(a.alert_type == "feeding_refusal" for a in alerts)

    def test_calculate_mortality_rate_zero_initial(self):
        mon = FishHealthMonitor()
        stock = self._stock(count=0)
        assert mon.calculate_mortality_rate(stock) == 0.0
