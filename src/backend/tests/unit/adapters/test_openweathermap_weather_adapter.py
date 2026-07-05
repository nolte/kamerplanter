"""Unit tests for the REQ-046 ``OpenWeatherMapWeatherAdapter``.

Covers the 3-hourly -> daily aggregation, m/s -> km/h wind conversion, the OWM
condition-id -> WMO mapping, and the "no key -> empty result" degradation.
"""

from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.data_access.external.openweathermap_weather_adapter import OpenWeatherMapWeatherAdapter


def _ts(year: int, month: int, day: int, hour: int) -> int:
    return int(datetime(year, month, day, hour, tzinfo=UTC).timestamp())


OWM_RESPONSE = {
    "list": [
        {
            "dt": _ts(2026, 7, 5, 9),
            "main": {"temp_min": 14.0, "temp_max": 20.0, "humidity": 70},
            "weather": [{"id": 500}],
            "wind": {"speed": 5.0, "gust": 8.0},
            "rain": {"3h": 1.0},
        },
        {
            "dt": _ts(2026, 7, 5, 15),
            "main": {"temp_min": 18.0, "temp_max": 26.0, "humidity": 50},
            "weather": [{"id": 800}],
            "wind": {"speed": 3.0, "gust": 6.0},
            "rain": {"3h": 0.5},
        },
        {
            "dt": _ts(2026, 7, 6, 12),
            "main": {"temp_min": 15.0, "temp_max": 22.0, "humidity": 60},
            "weather": [{"id": 803}],
            "wind": {"speed": 4.0},
        },
    ]
}


class TestMap:
    def test_aggregates_and_converts_wind(self):
        adapter = OpenWeatherMapWeatherAdapter(api_key="k")

        records = adapter._map(OWM_RESPONSE)

        assert len(records) == 2
        day1 = records[0]
        assert day1.forecast_date == date(2026, 7, 5)
        assert day1.temp_min_c == 14.0
        assert day1.temp_max_c == 26.0
        assert day1.precipitation_mm == 1.5
        # max wind 5.0 m/s -> 18.0 km/h
        assert day1.wind_speed_kmh == 18.0
        assert day1.wind_gust_kmh == 28.8
        assert day1.humidity_percent == 60.0  # mean of 70 and 50
        assert day1.weather_code == "61"  # first slice id 500 -> rain
        assert day1.source == "openweathermap"
        assert day1.data_kind == "forecast"

    def test_owm_id_maps_clouds(self):
        adapter = OpenWeatherMapWeatherAdapter(api_key="k")

        records = adapter._map(OWM_RESPONSE)

        assert records[1].weather_code == "3"  # id 803 -> clouds

    def test_empty_payload_returns_empty(self):
        adapter = OpenWeatherMapWeatherAdapter(api_key="k")

        assert adapter._map({}) == []


class TestFetchDaily:
    @pytest.mark.asyncio
    async def test_no_api_key_returns_empty(self):
        adapter = OpenWeatherMapWeatherAdapter(api_key=None)

        records = await adapter.fetch_daily(latitude=52.5, longitude=13.4)

        assert records == []

    @pytest.mark.asyncio
    async def test_health_check_false_without_key(self):
        adapter = OpenWeatherMapWeatherAdapter(api_key=None)

        assert await adapter.health_check() is False

    @pytest.mark.asyncio
    async def test_http_error_never_leaks_api_key(self):
        # SEC-001: httpx error strings echo the request URL incl. ``appid``. The
        # adapter must re-raise a redacted ``httpx.HTTPError`` (base type so the
        # resolver still falls back) that no longer contains the plaintext key.
        key = "SUPER-SECRET-KEY-123"
        adapter = OpenWeatherMapWeatherAdapter(api_key=key)
        req = httpx.Request("GET", f"https://api.openweathermap.org/data/2.5/forecast?appid={key}")
        leaking = httpx.HTTPStatusError(
            f"Client error '401 Unauthorized' for url '{req.url}'",
            request=req,
            response=httpx.Response(401, request=req),
        )
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock(side_effect=leaking)
        with patch("app.data_access.external.openweathermap_weather_adapter.httpx.AsyncClient") as mock_cls:
            mock_ac = AsyncMock()
            mock_ac.get.return_value = mock_resp
            mock_ac.__aenter__ = AsyncMock(return_value=mock_ac)
            mock_ac.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_ac
            with pytest.raises(httpx.HTTPError) as excinfo:
                await adapter.fetch_daily(latitude=52.5, longitude=13.4)

        assert key not in str(excinfo.value)
        assert "***" in str(excinfo.value)
