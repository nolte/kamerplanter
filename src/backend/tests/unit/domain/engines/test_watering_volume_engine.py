"""Tests for WateringVolumeEngine — phase/species/substrate/container volume suggestions."""

from datetime import date

import pytest

from app.common.enums import IrrigationStrategy, SubstrateType, WaterRetention
from app.domain.engines.watering_volume_engine import WateringVolumeEngine


@pytest.fixture
def engine():
    return WateringVolumeEngine()


class TestFallbackDefault:
    def test_no_inputs_returns_default(self, engine: WateringVolumeEngine):
        result = engine.suggest_volume()
        assert result.volume_ml == 250
        assert result.source == "fallback_default"

    def test_default_range_is_25_percent(self, engine: WateringVolumeEngine):
        result = engine.suggest_volume()
        assert result.volume_ml_min == 188  # 250 * 0.75
        assert result.volume_ml_max == 312  # 250 * 1.25


class TestPhaseRequirementProfile:
    def test_phase_override_takes_priority(self, engine: WateringVolumeEngine):
        result = engine.suggest_volume(
            phase_irrigation_volume_ml=500,
            species_volume_ml_min=100,
            species_volume_ml_max=200,
            container_volume_liters=10.0,
        )
        assert result.source == "phase_requirement_profile"
        assert result.volume_ml == 500

    def test_zero_phase_volume_falls_through(self, engine: WateringVolumeEngine):
        result = engine.suggest_volume(
            phase_irrigation_volume_ml=0,
            species_volume_ml_min=100,
            species_volume_ml_max=300,
        )
        assert result.source == "species_watering_guide"


class TestSpeciesWateringGuide:
    def test_species_guide_midpoint(self, engine: WateringVolumeEngine):
        result = engine.suggest_volume(
            species_volume_ml_min=100,
            species_volume_ml_max=300,
        )
        assert result.source == "species_watering_guide"
        assert result.volume_ml == 200
        assert result.volume_ml_min == 100
        assert result.volume_ml_max == 300

    def test_seasonal_adjustment_applied(self, engine: WateringVolumeEngine):
        seasonal = [
            {"months": [1, 2, 12], "volume_ml_min": 50, "volume_ml_max": 100, "label": "winter"},
        ]
        result = engine.suggest_volume(
            species_volume_ml_min=200,
            species_volume_ml_max=400,
            species_seasonal_adjustments=seasonal,
            reference_date=date(2026, 1, 15),
        )
        assert result.volume_ml == 75  # midpoint of 50-100
        assert "seasonal_adjustment=winter" in result.adjustments

    def test_no_seasonal_match_uses_base(self, engine: WateringVolumeEngine):
        seasonal = [
            {"months": [7, 8], "volume_ml_min": 500, "volume_ml_max": 800, "label": "summer"},
        ]
        result = engine.suggest_volume(
            species_volume_ml_min=100,
            species_volume_ml_max=200,
            species_seasonal_adjustments=seasonal,
            reference_date=date(2026, 1, 15),
        )
        assert result.volume_ml == 150


class TestContainerSubstrateCalculation:
    def test_coco_10l_container(self, engine: WateringVolumeEngine):
        result = engine.suggest_volume(
            container_volume_liters=10.0,
            substrate_type=SubstrateType.COCO,
        )
        assert result.source == "container_substrate_calculation"
        # 10L * 0.20 * 1000 = 2000ml
        assert result.volume_ml == 2000

    def test_soil_5l_container(self, engine: WateringVolumeEngine):
        result = engine.suggest_volume(
            container_volume_liters=5.0,
            substrate_type=SubstrateType.SOIL,
        )
        # 5L * 0.15 * 1000 = 750ml
        assert result.volume_ml == 750

    def test_unknown_substrate_uses_default_ratio(self, engine: WateringVolumeEngine):
        result = engine.suggest_volume(
            container_volume_liters=10.0,
            substrate_type="some_unknown",
        )
        # 10L * 0.15 (default) * 1000 = 1500ml
        assert result.volume_ml == 1500


class TestRetentionModifier:
    def test_low_retention_increases_volume(self, engine: WateringVolumeEngine):
        base = engine.suggest_volume(container_volume_liters=10.0, substrate_type=SubstrateType.SOIL)
        with_low = engine.suggest_volume(
            container_volume_liters=10.0,
            substrate_type=SubstrateType.SOIL,
            water_retention=WaterRetention.LOW,
        )
        assert with_low.volume_ml > base.volume_ml

    def test_high_retention_decreases_volume(self, engine: WateringVolumeEngine):
        base = engine.suggest_volume(container_volume_liters=10.0, substrate_type=SubstrateType.SOIL)
        with_high = engine.suggest_volume(
            container_volume_liters=10.0,
            substrate_type=SubstrateType.SOIL,
            water_retention=WaterRetention.HIGH,
        )
        assert with_high.volume_ml < base.volume_ml

    def test_whc_percent_overrides_retention_enum(self, engine: WateringVolumeEngine):
        """water_holding_capacity_percent takes precedence over water_retention enum."""
        result = engine.suggest_volume(
            container_volume_liters=10.0,
            substrate_type=SubstrateType.SOIL,
            water_retention=WaterRetention.LOW,  # would increase
            water_holding_capacity_percent=80.0,  # high WHC → decrease
        )
        # WHC 80% → modifier = 1.0 + (50 - 80)/100 = 0.70
        # 1500 * 0.70 = 1050
        assert result.volume_ml < 1500
        assert any("whc=80.0%" in a for a in result.adjustments)


class TestIrrigationStrategyModifier:
    def test_frequent_strategy_reduces_volume(self, engine: WateringVolumeEngine):
        base = engine.suggest_volume(container_volume_liters=10.0, substrate_type=SubstrateType.COCO)
        frequent = engine.suggest_volume(
            container_volume_liters=10.0,
            substrate_type=SubstrateType.COCO,
            irrigation_strategy=IrrigationStrategy.FREQUENT,
        )
        assert frequent.volume_ml < base.volume_ml

    def test_infrequent_strategy_increases_volume(self, engine: WateringVolumeEngine):
        base = engine.suggest_volume(container_volume_liters=10.0, substrate_type=SubstrateType.COCO)
        infrequent = engine.suggest_volume(
            container_volume_liters=10.0,
            substrate_type=SubstrateType.COCO,
            irrigation_strategy=IrrigationStrategy.INFREQUENT,
        )
        assert infrequent.volume_ml > base.volume_ml


class TestPhaseFactor:
    def test_flowering_increases_species_volume(self, engine: WateringVolumeEngine):
        veg = engine.suggest_volume(
            species_volume_ml_min=200,
            species_volume_ml_max=400,
            phase_name="vegetative",
        )
        flower = engine.suggest_volume(
            species_volume_ml_min=200,
            species_volume_ml_max=400,
            phase_name="flowering",
        )
        assert flower.volume_ml > veg.volume_ml

    def test_seedling_reduces_volume(self, engine: WateringVolumeEngine):
        veg = engine.suggest_volume(
            species_volume_ml_min=200,
            species_volume_ml_max=400,
            phase_name="vegetative",
        )
        seedling = engine.suggest_volume(
            species_volume_ml_min=200,
            species_volume_ml_max=400,
            phase_name="seedling",
        )
        assert seedling.volume_ml < veg.volume_ml

    def test_dormancy_drastically_reduces(self, engine: WateringVolumeEngine):
        result = engine.suggest_volume(
            species_volume_ml_min=200,
            species_volume_ml_max=400,
            phase_name="dormancy",
        )
        # dormancy factor = 0.25 → 300 * 0.25 = 75
        assert result.volume_ml == 75

    def test_phase_factor_not_applied_when_phase_override_set(self, engine: WateringVolumeEngine):
        """When phase_irrigation_volume_ml is set, phase_factor is NOT additionally applied."""
        result = engine.suggest_volume(
            phase_irrigation_volume_ml=500,
            phase_name="seedling",  # would be 0.5x, but should be ignored
        )
        assert result.volume_ml == 500


class TestContainerScaling:
    def test_large_container_scales_species_guide(self, engine: WateringVolumeEngine):
        """A 20L container should scale up species guide (damped by sqrt)."""
        small = engine.suggest_volume(
            species_volume_ml_min=200,
            species_volume_ml_max=400,
            container_volume_liters=5.0,  # reference = 1.0x
        )
        large = engine.suggest_volume(
            species_volume_ml_min=200,
            species_volume_ml_max=400,
            container_volume_liters=20.0,  # sqrt(4) = 2.0x
        )
        assert large.volume_ml > small.volume_ml
        assert any("container_scale" in a for a in large.adjustments)

    def test_small_container_scales_down(self, engine: WateringVolumeEngine):
        result = engine.suggest_volume(
            species_volume_ml_min=200,
            species_volume_ml_max=400,
            container_volume_liters=2.0,  # 2/5 = 0.4x
        )
        assert result.volume_ml < 300  # less than midpoint

    def test_reference_container_no_scaling(self, engine: WateringVolumeEngine):
        """5L container = reference, no scaling applied."""
        result = engine.suggest_volume(
            species_volume_ml_min=200,
            species_volume_ml_max=400,
            container_volume_liters=5.0,
        )
        assert not any("container_scale" in a for a in result.adjustments)


class TestMinimumVolume:
    def test_minimum_10ml(self, engine: WateringVolumeEngine):
        result = engine.suggest_volume(
            species_volume_ml_min=1,
            species_volume_ml_max=5,
            phase_name="dormancy",
        )
        assert result.volume_ml >= 10
        assert result.volume_ml_min >= 10


class TestCombinedScenarios:
    def test_cannabis_flowering_coco_11l(self, engine: WateringVolumeEngine):
        """Realistic cannabis scenario: flowering in 11L coco."""
        result = engine.suggest_volume(
            container_volume_liters=11.0,
            substrate_type=SubstrateType.COCO,
            water_retention=WaterRetention.MEDIUM,
            irrigation_strategy=IrrigationStrategy.FREQUENT,
            phase_name="flowering",
        )
        # 11L * 0.20 * 1000 = 2200ml base
        # * 0.70 (frequent) = 1540
        # * 1.20 (flowering) = 1848
        assert result.source == "container_substrate_calculation"
        assert 1500 < result.volume_ml < 2200

    def test_houseplant_soil_1l_dormancy(self, engine: WateringVolumeEngine):
        """Small houseplant in dormancy."""
        result = engine.suggest_volume(
            container_volume_liters=1.0,
            substrate_type=SubstrateType.SOIL,
            water_retention=WaterRetention.HIGH,
            phase_name="dormancy",
        )
        # 1L * 0.15 * 1000 = 150ml base
        # * 0.80 (high retention) = 120
        # * 0.25 (dormancy) = 30
        assert result.volume_ml < 50

    def test_tomato_outdoor_with_species_guide(self, engine: WateringVolumeEngine):
        """Tomato with species guide and 15L container."""
        result = engine.suggest_volume(
            species_volume_ml_min=500,
            species_volume_ml_max=1000,
            container_volume_liters=15.0,
            phase_name="flowering",
        )
        # midpoint = 750, * 1.20 (flowering) = 900
        # container scale = sqrt(15/5) = sqrt(3) ≈ 1.73 → 900 * 1.73 ≈ 1558
        assert result.source == "species_watering_guide"
        assert result.volume_ml > 1000
