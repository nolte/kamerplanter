"""Unit tests for AreaDosingCalculator (REQ-004 W-013, AP-11)."""

import pytest

from app.common.enums import FertilizerType, NutrientReleaseSpeed
from app.domain.engines.area_dosing_engine import AreaDosingCalculator
from app.domain.models.fertilizer import Fertilizer


def _fert(name: str, **kwargs) -> Fertilizer:
    defaults = {
        "product_name": name,
        "fertilizer_type": FertilizerType.ORGANIC,
    }
    defaults.update(kwargs)
    return Fertilizer(**defaults)


class TestAreaDosing:
    def test_grams_per_m2_times_area(self):
        calc = AreaDosingCalculator()
        hornspaene = _fert(
            "Hornspäne",
            application_rate_g_per_m2=80.0,
            npk_ratio=(14.0, 0.0, 0.0),
            nutrient_release_speed=NutrientReleaseSpeed.MONTHS,
        )
        result = calc.calculate([hornspaene], area_m2=2.5)
        assert result.items[0].total_grams == pytest.approx(200.0)
        assert result.items[0].nutrient_release_speed == "months"

    def test_liters_per_m2_times_area(self):
        calc = AreaDosingCalculator()
        kompost = _fert("Kompost", application_rate_l_per_m2=3.0)
        result = calc.calculate([kompost], area_m2=4.0)
        assert result.items[0].total_liters == pytest.approx(12.0)

    def test_dilution_note_present(self):
        calc = AreaDosingCalculator()
        jauche = _fert("Brennnesseljauche", application_rate_l_per_m2=1.0, dilution_ratio="1:10")
        result = calc.calculate([jauche], area_m2=2.0)
        assert result.items[0].dilution_ratio == "1:10"
        assert result.items[0].note is not None
        assert "1:10" in result.items[0].note
        assert any("1:10" in ins for ins in result.instructions)

    def test_missing_rate_yields_warning_no_crash(self):
        calc = AreaDosingCalculator()
        empty = _fert("No Rate Product")
        result = calc.calculate([empty], area_m2=2.0)
        assert result.items[0].total_grams is None
        assert result.items[0].total_liters is None
        assert any("no area application rate" in w for w in result.warnings)

    def test_nitrogen_fixer_guard(self):
        calc = AreaDosingCalculator()
        n_fert = _fert("Blutmehl", application_rate_g_per_m2=50.0, npk_ratio=(12.0, 0.0, 0.0))
        result = calc.calculate([n_fert], area_m2=1.0, demand_level="nitrogen_fixer")
        assert any("nitrogen" in w.lower() for w in result.warnings)

    def test_zero_area_raises(self):
        calc = AreaDosingCalculator()
        with pytest.raises(ValueError, match="area_m2"):
            calc.calculate([_fert("X", application_rate_g_per_m2=10.0)], area_m2=0.0)
