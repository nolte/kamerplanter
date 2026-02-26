from datetime import date

from app.domain.calculators.sun_calculator import calculate_sun_times, calculate_sun_times_range

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
        results = calculate_sun_times_range(
            BERLIN_LAT, BERLIN_LON, date(2025, 6, 1), date(2025, 6, 7), BERLIN_TZ
        )
        assert len(results) == 7

    def test_range_single_day(self):
        results = calculate_sun_times_range(
            BERLIN_LAT, BERLIN_LON, date(2025, 6, 1), date(2025, 6, 1), BERLIN_TZ
        )
        assert len(results) == 1

    def test_range_dates_are_sequential(self):
        results = calculate_sun_times_range(
            BERLIN_LAT, BERLIN_LON, date(2025, 1, 1), date(2025, 1, 5), BERLIN_TZ
        )
        dates = [r["date"] for r in results]
        assert dates == ["2025-01-01", "2025-01-02", "2025-01-03", "2025-01-04", "2025-01-05"]
