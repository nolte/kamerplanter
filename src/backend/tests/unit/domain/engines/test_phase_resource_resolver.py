"""Tests for the E7/E8 phase resource resolver (REQ-003)."""

from app.common.enums import NutrientDemandLevel
from app.domain.engines.phase_resource_resolver import (
    ph_micronutrient_availability,
    resolve_irrigation,
    resolve_nutrient,
)


class TestIrrigation:
    def test_rest_phase_is_minimal(self) -> None:
        reg = resolve_irrigation("winter_rest", base_frequency_days=3, base_volume_ml=300)
        assert reg.water_only is True
        assert reg.frequency_days > 3  # much less frequent
        assert reg.volume_ml_per_plant < 300

    def test_dry_storage_is_dry(self) -> None:
        reg = resolve_irrigation("dry_storage")
        assert reg.volume_ml_per_plant == 0.0

    def test_flushing_is_water_only(self) -> None:
        reg = resolve_irrigation("flushing")
        assert reg.water_only is True

    def test_seedling_is_frequent_low_volume(self) -> None:
        reg = resolve_irrigation("seedling", base_frequency_days=4, base_volume_ml=300)
        assert reg.frequency_days <= 2
        assert reg.volume_ml_per_plant < 300

    def test_waterlogging_sensitive_caps_volume(self) -> None:
        reg = resolve_irrigation("vegetative", base_volume_ml=300, waterlogging_tolerance="sensitive")
        assert reg.volume_ml_per_plant <= 300 * 0.7


class TestNutrient:
    def test_rest_phase_no_feed(self) -> None:
        reg = resolve_nutrient("winter_rest")
        assert reg.feed is False
        assert reg.npk_ratio == (0, 0, 0)
        assert reg.target_ec_ms == 0.0

    def test_flushing_zero_npk(self) -> None:
        reg = resolve_nutrient("flushing", base_ec_ms=1.5)
        assert reg.feed is False
        assert reg.npk_ratio == (0, 0, 0)

    def test_heavy_feeder_scales_ec_up(self) -> None:
        heavy = resolve_nutrient("vegetative", base_ec_ms=1.5, nutrient_demand_level=NutrientDemandLevel.HEAVY_FEEDER)
        light = resolve_nutrient("vegetative", base_ec_ms=1.5, nutrient_demand_level=NutrientDemandLevel.LIGHT_FEEDER)
        assert heavy.target_ec_ms > light.target_ec_ms
        assert heavy.feed is True

    def test_extended_rest_phase_maps_to_no_feed(self) -> None:
        # summer_rest / cool_rest map to dormancy (D8) -> no feed
        assert resolve_nutrient("cool_rest").feed is False


class TestPhGating:
    """E8: per-phase target pH is surfaced and gates micronutrient availability."""

    def test_target_ph_passthrough(self) -> None:
        reg = resolve_nutrient("vegetative", base_ph=6.2)
        assert reg.target_ph == 6.2

    def test_optimal_ph_keeps_micros_available(self) -> None:
        reg = resolve_nutrient("vegetative", base_ph=6.3)
        assert reg.micros_available is True
        assert "optimal" in reg.ph_note

    def test_high_ph_locks_out_micros(self) -> None:
        reg = resolve_nutrient("flowering", base_ph=7.2)
        assert reg.micros_available is False
        assert "lock out" in reg.ph_note

    def test_low_ph_flags_molybdenum_drop(self) -> None:
        reg = resolve_nutrient("vegetative", base_ph=5.2)
        assert reg.micros_available is False
        assert "molybdenum" in reg.ph_note

    def test_ph_passed_through_on_rest_and_flush(self) -> None:
        # rest / flush are no-feed, but the target pH + gating are still surfaced.
        rest = resolve_nutrient("winter_rest", base_ph=7.5)
        assert rest.feed is False
        assert rest.target_ph == 7.5
        assert rest.micros_available is False
        flush = resolve_nutrient("flushing", base_ph=6.2)
        assert flush.feed is False
        assert flush.target_ph == 6.2
        assert flush.micros_available is True

    def test_availability_helper_boundaries(self) -> None:
        assert ph_micronutrient_availability(6.0)[0] is True
        assert ph_micronutrient_availability(6.5)[0] is True
        assert ph_micronutrient_availability(6.6)[0] is False
        assert ph_micronutrient_availability(5.9)[0] is False
