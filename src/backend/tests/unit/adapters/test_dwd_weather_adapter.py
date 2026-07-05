"""Unit tests for the REQ-046 ``DwdWeatherAdapter`` (Brightsky facade).

Verifies the hourly -> daily aggregation and the icon/condition -> WMO mapping.
"""

from datetime import date

from app.data_access.external.dwd_weather_adapter import DwdWeatherAdapter

BRIGHTSKY_RESPONSE = {
    "weather": [
        {
            "timestamp": "2026-07-05T06:00:00+00:00",
            "temperature": 12.0,
            "precipitation": 0.0,
            "wind_speed": 10.0,
            "wind_gust_speed": 20.0,
            "relative_humidity": 80.0,
            "icon": "cloudy",
            "condition": "dry",
        },
        {
            "timestamp": "2026-07-05T12:00:00+00:00",
            "temperature": 22.0,
            "precipitation": 1.5,
            "wind_speed": 18.0,
            "wind_gust_speed": 30.0,
            "relative_humidity": 60.0,
            "icon": "rain",
            "condition": "rain",
        },
        {
            "timestamp": "2026-07-06T12:00:00+00:00",
            "temperature": 25.0,
            "precipitation": 0.0,
            "wind_speed": 5.0,
            "wind_gust_speed": 12.0,
            "relative_humidity": 55.0,
            "icon": "clear-day",
            "condition": "dry",
        },
    ]
}


class TestMap:
    def test_aggregates_hourly_into_days(self):
        adapter = DwdWeatherAdapter()

        records = adapter._map(BRIGHTSKY_RESPONSE)

        assert len(records) == 2
        day1 = records[0]
        assert day1.forecast_date == date(2026, 7, 5)
        assert day1.temp_min_c == 12.0
        assert day1.temp_max_c == 22.0
        assert day1.precipitation_mm == 1.5
        assert day1.wind_speed_kmh == 18.0  # max of the day
        assert day1.wind_gust_kmh == 30.0
        assert day1.humidity_percent == 70.0  # mean of 80 and 60
        assert day1.source == "dwd"
        assert day1.data_kind == "forecast"
        # First non-empty icon of the day wins -> "cloudy" -> WMO "3".
        assert day1.weather_code == "3"

    def test_clear_day_maps_to_wmo_zero(self):
        adapter = DwdWeatherAdapter()

        records = adapter._map(BRIGHTSKY_RESPONSE)

        assert records[1].weather_code == "0"

    def test_condition_fallback_when_icon_unknown(self):
        adapter = DwdWeatherAdapter()
        payload = {
            "weather": [
                {
                    "timestamp": "2026-07-05T12:00:00+00:00",
                    "temperature": 20.0,
                    "icon": "some-unknown-icon",
                    "condition": "thunderstorm",
                }
            ]
        }

        record = adapter._map(payload)[0]

        assert record.weather_code == "95"

    def test_empty_payload_returns_empty(self):
        adapter = DwdWeatherAdapter()

        assert adapter._map({}) == []
