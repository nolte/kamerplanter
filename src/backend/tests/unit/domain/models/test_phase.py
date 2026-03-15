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
