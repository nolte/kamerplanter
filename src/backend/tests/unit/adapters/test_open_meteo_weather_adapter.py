"""Unit tests for the REQ-046 ``OpenMeteoWeatherAdapter``.

``_map`` is tested directly against a fixture payload (no HTTP); ``fetch_daily``
is covered once with a mocked ``httpx.AsyncClient`` to exercise the async path.
"""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.data_access.external.open_meteo_weather_adapter import OpenMeteoWeatherAdapter

OPEN_METEO_RESPONSE = {
    "daily": {
        "time": ["2026-07-05", "2026-07-06"],
        "temperature_2m_min": [12.3, None],
        "temperature_2m_max": [24.1, 25.0],
        "precipitation_sum": [0.0, 3.4],
        "wind_speed_10m_max": [18.0, 22.5],
        "wind_gusts_10m_max": [35.0, 40.0],
        "relative_humidity_2m_mean": [65.0, 70.0],
        "weather_code": [3, 61],
    }
}


class TestMap:
    def test_maps_all_daily_fields(self):
        adapter = OpenMeteoWeatherAdapter()

        records = adapter._map(OPEN_METEO_RESPONSE)

        assert len(records) == 2
        first = records[0]
        assert first.forecast_date == date(2026, 7, 5)
        assert first.temp_min_c == 12.3
        assert first.temp_max_c == 24.1
        assert first.precipitation_mm == 0.0
        assert first.wind_speed_kmh == 18.0
        assert first.wind_gust_kmh == 35.0
        assert first.humidity_percent == 65.0
        assert first.weather_code == "3"
        assert first.source == "open-meteo"
        assert first.data_kind == "forecast"
        assert first.is_current_conditions is False

    def test_null_and_sentinel_collapse_to_none(self):
        adapter = OpenMeteoWeatherAdapter()
        payload = {
            "daily": {
                "time": ["2026-07-05"],
                "temperature_2m_min": [-999.0],
                "temperature_2m_max": [None],
                "precipitation_sum": [None],
                "wind_speed_10m_max": [None],
                "wind_gusts_10m_max": [None],
                "relative_humidity_2m_mean": [None],
                "weather_code": [None],
            }
        }

        record = adapter._map(payload)[0]

        assert record.temp_min_c is None
        assert record.temp_max_c is None
        assert record.weather_code is None

    def test_empty_payload_returns_empty(self):
        adapter = OpenMeteoWeatherAdapter()

        assert adapter._map({}) == []


class TestFetchDaily:
    @pytest.mark.asyncio
    async def test_fetch_daily_calls_provider_and_maps(self):
        adapter = OpenMeteoWeatherAdapter(base_url="https://weather.test/v1/forecast")

        mock_resp = MagicMock()
        mock_resp.json.return_value = OPEN_METEO_RESPONSE
        mock_resp.raise_for_status = MagicMock()

        with patch("app.data_access.external.open_meteo_weather_adapter.httpx.AsyncClient") as mock_cls:
            mock_ac = AsyncMock()
            mock_ac.get.return_value = mock_resp
            mock_ac.__aenter__ = AsyncMock(return_value=mock_ac)
            mock_ac.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_ac

            records = await adapter.fetch_daily(latitude=52.5, longitude=13.4)

        assert len(records) == 2
        called_url = mock_ac.get.call_args.args[0]
        assert called_url == "https://weather.test/v1/forecast"
        params = mock_ac.get.call_args.kwargs["params"]
        assert params["wind_speed_unit"] == "kmh"
        assert params["timezone"] == "auto"
        assert params["forecast_days"] == 7
