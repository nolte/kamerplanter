import pytest
from pydantic import ValidationError

from app.domain.models.phase import NutrientProfile, RequirementProfile


class TestRequirementProfile:
    def test_valid_profile(self):
        p = RequirementProfile(temperature_day_c=25.0, temperature_night_c=20.0)
        assert p.vpd_target_kpa == 1.0

    def test_night_must_be_lower_than_day(self):
        with pytest.raises(ValidationError, match="Night temperature"):
            RequirementProfile(temperature_day_c=20.0, temperature_night_c=25.0)

    def test_equal_temps_fail(self):
        with pytest.raises(ValidationError, match="Night temperature"):
            RequirementProfile(temperature_day_c=20.0, temperature_night_c=20.0)

    def test_photoperiod_range(self):
        p = RequirementProfile(
            temperature_day_c=25.0,
            temperature_night_c=20.0,
            photoperiod_hours=12.0,
        )
        assert p.photoperiod_hours == 12.0

    def test_photoperiod_too_high(self):
        with pytest.raises(ValidationError):
            RequirementProfile(
                temperature_day_c=25.0,
                temperature_night_c=20.0,
                photoperiod_hours=25.0,
            )


class TestRequirementProfileEnvironmentalPhysiology:
    """REQ-003 v2.6 — VPD threshold, T_opt, far-red fraction."""

    def test_defaults_are_none(self):
        p = RequirementProfile(temperature_day_c=25.0, temperature_night_c=20.0)
        assert p.vpd_threshold_kpa is None
        assert p.vpd_sensitivity is None
        assert p.photosynthesis_temp_opt_c is None
        assert p.far_red_fraction is None

    def test_vpd_threshold_valid(self):
        p = RequirementProfile(temperature_day_c=25.0, temperature_night_c=20.0, vpd_threshold_kpa=1.6)
        assert p.vpd_threshold_kpa == 1.6

    def test_vpd_threshold_negative_rejected(self):
        with pytest.raises(ValidationError):
            RequirementProfile(temperature_day_c=25.0, temperature_night_c=20.0, vpd_threshold_kpa=-0.1)

    def test_vpd_sensitivity_valid(self):
        p = RequirementProfile(temperature_day_c=25.0, temperature_night_c=20.0, vpd_sensitivity="high")
        assert p.vpd_sensitivity == "high"

    def test_vpd_sensitivity_invalid_rejected(self):
        with pytest.raises(ValidationError):
            RequirementProfile(temperature_day_c=25.0, temperature_night_c=20.0, vpd_sensitivity="extreme")

    def test_photosynthesis_temp_opt_set(self):
        p = RequirementProfile(temperature_day_c=25.0, temperature_night_c=20.0, photosynthesis_temp_opt_c=28.0)
        assert p.photosynthesis_temp_opt_c == 28.0

    def test_far_red_fraction_valid(self):
        p = RequirementProfile(temperature_day_c=25.0, temperature_night_c=20.0, far_red_fraction=0.5)
        assert p.far_red_fraction == 0.5

    def test_far_red_fraction_above_one_rejected(self):
        with pytest.raises(ValidationError):
            RequirementProfile(temperature_day_c=25.0, temperature_night_c=20.0, far_red_fraction=1.5)

    def test_far_red_fraction_negative_rejected(self):
        with pytest.raises(ValidationError):
            RequirementProfile(temperature_day_c=25.0, temperature_night_c=20.0, far_red_fraction=-0.1)

    def test_model_validate_from_seed_dict(self):
        raw = {
            "phase_key": "ph1",
            "temperature_day_c": 26.0,
            "temperature_night_c": 21.0,
            "vpd_threshold_kpa": 1.4,
            "vpd_sensitivity": "medium",
            "photosynthesis_temp_opt_c": 27.5,
            "far_red_fraction": 0.45,
        }
        p = RequirementProfile.model_validate(raw)
        assert p.vpd_threshold_kpa == 1.4
        assert p.vpd_sensitivity == "medium"
        assert p.photosynthesis_temp_opt_c == 27.5
        assert p.far_red_fraction == 0.45


class TestNutrientProfile:
    def test_valid_profile(self):
        p = NutrientProfile(npk_ratio=(3, 1, 2), target_ec_ms=1.5)
        assert p.npk_ratio == (3, 1, 2)

    def test_flushing_zero_npk(self):
        p = NutrientProfile(npk_ratio=(0, 0, 0), target_ec_ms=0.0)
        assert sum(p.npk_ratio) == 0

    def test_ph_range(self):
        p = NutrientProfile(target_ph=6.5)
        assert p.target_ph == 6.5

    def test_ph_too_high(self):
        with pytest.raises(ValidationError):
            NutrientProfile(target_ph=15.0)


class TestNutrientProfileMicronutrients:
    """REQ-004 v3.5 — explicit Mn/Zn/Cu/Mo micronutrient fields."""

    def test_defaults_are_none(self):
        p = NutrientProfile()
        assert p.manganese_ppm is None
        assert p.zinc_ppm is None
        assert p.copper_ppm is None
        assert p.molybdenum_ppm is None
        assert p.micro_nutrients == {}

    def test_micronutrients_valid(self):
        p = NutrientProfile(manganese_ppm=2, zinc_ppm=1, copper_ppm=1, molybdenum_ppm=1)
        assert p.manganese_ppm == 2
        assert p.zinc_ppm == 1
        assert p.copper_ppm == 1
        assert p.molybdenum_ppm == 1

    def test_micronutrient_negative_rejected(self):
        with pytest.raises(ValidationError):
            NutrientProfile(manganese_ppm=-1)

    def test_free_form_micro_nutrients_still_supported(self):
        p = NutrientProfile(micro_nutrients={"silicon": 5})
        assert p.micro_nutrients["silicon"] == 5

    def test_model_validate_from_seed_dict(self):
        raw = {
            "phase_key": "ph1",
            "npk_ratio": (3, 1, 2),
            "manganese_ppm": 2,
            "zinc_ppm": 1,
            "copper_ppm": 1,
            "molybdenum_ppm": 1,
        }
        p = NutrientProfile.model_validate(raw)
        assert p.manganese_ppm == 2
        assert p.zinc_ppm == 1
        assert p.copper_ppm == 1
        assert p.molybdenum_ppm == 1
