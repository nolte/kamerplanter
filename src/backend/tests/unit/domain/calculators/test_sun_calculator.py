from datetime import date
from zoneinfo import ZoneInfo

import pytest

from app.domain.calculators.sun_calculator import (
    calculate_sun_directions,
    calculate_sun_times,
    calculate_sun_times_range,
)

# Berlin: 52.52°N, 13.405°E
BERLIN_LAT = 52.52
BERLIN_LON = 13.405
BERLIN_TZ = "Europe/Berlin"

# Quito (equator): -0.18°S, -78.47°W
QUITO_LAT = -0.18
QUITO_LON = -78.47
QUITO_TZ = "America/Guayaquil"

# Cape Town (southern hemisphere): -33.92°S, 18.42°E
CAPE_TOWN_LAT = -33.92
CAPE_TOWN_LON = 18.42
CAPE_TOWN_TZ = "Africa/Johannesburg"


class TestSunTimesBasic:
    def test_returns_all_fields(self):
        result = calculate_sun_times(BERLIN_LAT, BERLIN_LON, date(2025, 6, 21), BERLIN_TZ)
        assert "sunrise" in result
        assert "sunset" in result
        assert "dawn" in result
        assert "dusk" in result
        assert "day_length_hours" in result
        assert "date" in result

    def test_time_format_hhmm(self):
        result = calculate_sun_times(BERLIN_LAT, BERLIN_LON, date(2025, 6, 21), BERLIN_TZ)
        for key in ("sunrise", "sunset", "dawn", "dusk"):
            parts = result[key].split(":")
            assert len(parts) == 2
            assert len(parts[0]) == 2
            assert len(parts[1]) == 2


class TestSummerVsWinter:
    def test_berlin_summer_long_day(self):
        result = calculate_sun_times(BERLIN_LAT, BERLIN_LON, date(2025, 6, 21), BERLIN_TZ)
        assert result["day_length_hours"] > 16.0

    def test_berlin_winter_short_day(self):
        result = calculate_sun_times(BERLIN_LAT, BERLIN_LON, date(2025, 12, 21), BERLIN_TZ)
        assert result["day_length_hours"] < 9.0


class TestEquator:
    def test_quito_stable_day_length_june(self):
        result = calculate_sun_times(QUITO_LAT, QUITO_LON, date(2025, 6, 21), QUITO_TZ)
        assert 11.5 < result["day_length_hours"] < 12.5

    def test_quito_stable_day_length_december(self):
        result = calculate_sun_times(QUITO_LAT, QUITO_LON, date(2025, 12, 21), QUITO_TZ)
        assert 11.5 < result["day_length_hours"] < 12.5


class TestSouthernHemisphere:
    def test_cape_town_inverted_seasons(self):
        june = calculate_sun_times(CAPE_TOWN_LAT, CAPE_TOWN_LON, date(2025, 6, 21), CAPE_TOWN_TZ)
        december = calculate_sun_times(CAPE_TOWN_LAT, CAPE_TOWN_LON, date(2025, 12, 21), CAPE_TOWN_TZ)
        # June is winter in southern hemisphere (shorter days)
        assert june["day_length_hours"] < december["day_length_hours"]


class TestSunTimesRange:
    def test_range_returns_correct_count(self):
        results = calculate_sun_times_range(BERLIN_LAT, BERLIN_LON, date(2025, 6, 1), date(2025, 6, 7), BERLIN_TZ)
        assert len(results) == 7

    def test_range_single_day(self):
        results = calculate_sun_times_range(BERLIN_LAT, BERLIN_LON, date(2025, 6, 1), date(2025, 6, 1), BERLIN_TZ)
        assert len(results) == 1

    def test_range_dates_are_sequential(self):
        results = calculate_sun_times_range(BERLIN_LAT, BERLIN_LON, date(2025, 1, 1), date(2025, 1, 5), BERLIN_TZ)
        dates = [r["date"] for r in results]
        assert dates == ["2025-01-01", "2025-01-02", "2025-01-03", "2025-01-04", "2025-01-05"]


class TestSunDirections:
    """REQ-053 GP-FR-016: the compass's sunrise and sunset azimuths."""

    BERLIN = ZoneInfo(BERLIN_TZ)

    def test_midsummer_in_berlin_rises_in_the_northeast_and_sets_in_the_northwest(self):
        directions = calculate_sun_directions(BERLIN_LAT, BERLIN_LON, date(2026, 6, 21), self.BERLIN)

        assert directions is not None
        assert directions.day == date(2026, 6, 21)
        # At 52.5 N the solstice sun rises and sets about 42 degrees north of east and west (upper limb, refraction).
        assert 46.5 <= directions.sunrise.azimuth_deg <= 49.0
        assert 311.0 <= directions.sunset.azimuth_deg <= 313.5
        assert directions.sunrise.time == "04:43"
        assert directions.sunset.time == "21:32"

    def test_the_equinox_rises_near_east_and_sets_near_west(self):
        directions = calculate_sun_directions(BERLIN_LAT, BERLIN_LON, date(2026, 3, 20), self.BERLIN)

        assert directions is not None
        assert abs(directions.sunrise.azimuth_deg - 90.0) < 3.0
        assert abs(directions.sunset.azimuth_deg - 270.0) < 3.0

    def test_midwinter_rises_in_the_southeast(self):
        directions = calculate_sun_directions(BERLIN_LAT, BERLIN_LON, date(2026, 12, 21), self.BERLIN)

        assert directions is not None
        assert 125.0 <= directions.sunrise.azimuth_deg <= 135.0
        assert 225.0 <= directions.sunset.azimuth_deg <= 235.0

    def test_the_southern_hemisphere_in_its_winter_rises_in_the_northeast(self):
        directions = calculate_sun_directions(CAPE_TOWN_LAT, CAPE_TOWN_LON, date(2026, 6, 21), ZoneInfo(CAPE_TOWN_TZ))

        assert directions is not None
        assert 55.0 <= directions.sunrise.azimuth_deg <= 70.0

    def test_the_azimuths_are_rounded_to_a_tenth(self):
        directions = calculate_sun_directions(BERLIN_LAT, BERLIN_LON, date(2026, 5, 3), self.BERLIN)

        assert directions is not None
        for value in (directions.sunrise.azimuth_deg, directions.sunset.azimuth_deg):
            assert round(value, 1) == value
            assert 0.0 <= value < 360.0

    @pytest.mark.parametrize("on", [date(2026, 6, 21), date(2026, 12, 21)])
    def test_polar_day_and_polar_night_have_no_direction(self, on: date):
        assert calculate_sun_directions(78.2, 15.6, on, ZoneInfo("Arctic/Longyearbyen")) is None
