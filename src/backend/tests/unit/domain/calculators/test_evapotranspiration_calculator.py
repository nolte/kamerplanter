"""REQ-037 — unit tests for the evapotranspiration & water-balance calculator.

The FAO-56 Penman-Monteith path is pinned against the canonical worked example
from Allen et al. (1998), *Crop evapotranspiration*, FAO Irrigation & Drainage
Paper 56, **Example 18** (6 July, Uccle/Brussels, lat 50.80°N, 100 m), whose
published result is ET₀ ≈ 3.9 mm/day.
"""

from app.domain.calculators.evapotranspiration_calculator import EvapotranspirationCalculator

# FAO-56 Example 18 driving inputs (see module docstring).
_EX18 = dict(
    latitude_deg=50.80,
    day_of_year=187,  # 6 July
    temp_min_c=12.3,
    temp_max_c=21.5,
    humidity_percent=73.5,  # (RHmax 84 + RHmin 63) / 2
    wind_speed_kmh=2.078 * 3.6,  # u2 = 2.078 m/s
    elevation_m=100.0,
    wind_measurement_height_m=2.0,
)


class TestPenmanMonteithReference:
    def test_fao56_example18_reference_vector(self):
        """Full PM path with measured solar radiation reproduces FAO-56 Example 18."""
        calc = EvapotranspirationCalculator()
        result = calc.calculate_et0(**_EX18, solar_radiation_mj_m2=22.07)

        assert result.method == "fao56_penman_monteith"
        assert result.quality == "high"
        # Published reference ET₀ ≈ 3.9 mm/day; the RHmean-derived vapour pressure
        # yields 3.787 — within 3 % of the paper. Pinned as a regression vector.
        assert result.et0_mm == 3.787
        assert 3.6 < result.et0_mm < 4.1

    def test_estimated_solar_downgrades_quality(self):
        """Without measured radiation the PM path estimates Rs and drops to medium."""
        calc = EvapotranspirationCalculator()
        result = calc.calculate_et0(**_EX18)

        assert result.method == "fao56_penman_monteith"
        assert result.quality == "medium"
        assert result.et0_mm > 0
        assert "estimated" in result.method_reason


class TestHargreavesFallback:
    def test_temperature_only_uses_hargreaves(self):
        """Only Tmin/Tmax → Hargreaves, medium quality, no exception."""
        calc = EvapotranspirationCalculator()
        result = calc.calculate_et0(latitude_deg=50.80, day_of_year=187, temp_min_c=12.3, temp_max_c=21.5)

        assert result.method == "hargreaves"
        assert result.quality == "medium"
        assert result.et0_mm > 0

    def test_wind_without_humidity_falls_back(self):
        calc = EvapotranspirationCalculator()
        result = calc.calculate_et0(
            latitude_deg=50.80, day_of_year=187, temp_min_c=12.3, temp_max_c=21.5, wind_speed_kmh=7.5
        )
        assert result.method == "hargreaves"

    def test_swapped_temperature_extremes_are_normalised(self):
        """A physically impossible Tmax < Tmin must not raise (swap-and-continue)."""
        calc = EvapotranspirationCalculator()
        result = calc.calculate_et0(latitude_deg=50.0, day_of_year=100, temp_min_c=25.0, temp_max_c=10.0)
        assert result.et0_mm >= 0


class TestWaterBalance:
    def test_rain_covers_demand_suppresses_irrigation(self):
        """ETc 3.5 mm + 12 mm rain → negative net demand, capped to 0."""
        calc = EvapotranspirationCalculator()
        balance = calc.calculate_water_balance(et0_mm=3.5, crop_coefficient_kc=1.0, precipitation_mm=12.0)

        assert balance.etc_mm == 3.5
        assert balance.effective_precipitation_mm == 9.6  # 12 * 0.8
        assert balance.net_demand_mm < 0
        assert balance.net_demand_mm_capped == 0.0
        assert balance.recommended_volume_liters == 0.0

    def test_water_holding_capacity_caps_demand(self):
        """net demand 9 mm with WHC 6 mm → capped to 6 mm."""
        calc = EvapotranspirationCalculator()
        balance = calc.calculate_water_balance(et0_mm=9.0, crop_coefficient_kc=1.0, water_holding_capacity_mm=6.0)
        assert balance.net_demand_mm == 9.0
        assert balance.net_demand_mm_capped == 6.0

    def test_volume_is_area_times_millimetres(self):
        """4 mm net demand × 5 m² → 20 L (1 mm = 1 L/m²)."""
        calc = EvapotranspirationCalculator()
        balance = calc.calculate_water_balance(et0_mm=4.0, crop_coefficient_kc=1.0, area_m2=5.0)
        assert balance.net_demand_mm_capped == 4.0
        assert balance.recommended_volume_liters == 20.0

    def test_kc_scales_etc(self):
        calc = EvapotranspirationCalculator()
        balance = calc.calculate_water_balance(et0_mm=4.0, crop_coefficient_kc=1.1)
        assert balance.kc_used == 1.1
        assert balance.etc_mm == 4.4

    def test_light_rain_below_threshold_counts_fully(self):
        calc = EvapotranspirationCalculator()
        balance = calc.calculate_water_balance(et0_mm=5.0, crop_coefficient_kc=1.0, precipitation_mm=3.0)
        assert balance.effective_precipitation_mm == 3.0
        assert balance.net_demand_mm == 2.0
