"""Unit tests for the REQ-041 ``NasaPowerWeatherAdapter``.

The two ``_map_*`` projections are tested directly against fixture payloads (no
HTTP); ``fetch_daily`` / ``fetch_climate_normals`` are each covered once with a
mocked ``httpx.AsyncClient`` to exercise the async path and the request shape.
"""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.data_access.external.nasa_power_weather_adapter import NasaPowerWeatherAdapter
from app.domain.services.weather_adapter_registry import WeatherAdapterRegistry

# Two daily records; the second row exercises the -999 sentinel on several fields.
NASA_DAILY_RESPONSE = {
    "properties": {
        "parameter": {
            "T2M_MIN": {"20260601": 8.5, "20260602": -999.0},
            "T2M_MAX": {"20260601": 21.0, "20260602": 22.4},
            "PRECTOTCORR": {"20260601": 2.3, "20260602": 0.0},
            "WS2M": {"20260601": 3.0, "20260602": -999.0},
            "RH2M": {"20260601": 70.0, "20260602": 65.0},
            "ALLSKY_SFC_SW_DWN": {"20260601": 18.4, "20260602": 20.1},
        }
    }
}

# Twelve monthly values per parameter + an annual (ANN) key.
NASA_CLIMATOLOGY_RESPONSE = {
    "header": {"start": 2001, "end": 2020},
    "properties": {
        "parameter": {
            "T2M": {
                m: 10.0 for m in ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")
            }
            | {"ANN": 10.5},
            "T2M_MIN": {
                "JAN": -3.0,
                "FEB": -1.0,
                "MAR": 2.0,
                "APR": 5.0,
                "MAY": 9.0,
                "JUN": 12.0,
                "JUL": 14.0,
                "AUG": 13.5,
                "SEP": 10.0,
                "OCT": 6.0,
                "NOV": 1.0,
                "DEC": -2.0,
            },
            "PRECTOTCORR": {
                m: 2.0 for m in ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")
            },
            "ALLSKY_SFC_SW_DWN": {
                m: 12.0 for m in ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")
            },
        }
    },
}


class TestMapDaily:
    def test_maps_daily_fields_as_reanalysis(self):
        adapter = NasaPowerWeatherAdapter()

        records = adapter._map_daily(NASA_DAILY_RESPONSE)

        assert len(records) == 2
        first = records[0]
        assert first.forecast_date == date(2026, 6, 1)
        assert first.temp_min_c == 8.5
        assert first.temp_max_c == 21.0
        assert first.precipitation_mm == 2.3
        # WS2M 3.0 m/s → 10.8 km/h (×3.6).
        assert first.wind_speed_kmh == 10.8
        assert first.humidity_percent == 70.0
        assert first.solar_radiation_mj_m2 == 18.4
        assert first.source == "nasa-power"
        assert first.data_kind == "reanalysis"
        assert first.is_current_conditions is False
        assert first.weather_code is None

    def test_sentinel_collapses_to_none(self):
        adapter = NasaPowerWeatherAdapter()

        second = adapter._map_daily(NASA_DAILY_RESPONSE)[1]

        assert second.temp_min_c is None  # -999 → None
        assert second.wind_speed_kmh is None  # -999 wind → None (no ×3.6 on sentinel)
        assert second.temp_max_c == 22.4

    def test_empty_payload_returns_empty(self):
        adapter = NasaPowerWeatherAdapter()

        assert adapter._map_daily({}) == []


class TestMapClimateNormals:
    def test_maps_twelve_months_and_coldest(self):
        adapter = NasaPowerWeatherAdapter()

        normal = adapter._map_climate_normals(NASA_CLIMATOLOGY_RESPONSE)

        assert normal is not None
        assert normal.source == "nasa-power"
        assert len(normal.monthly_temp_min_c) == 12
        assert len(normal.monthly_temp_avg_c) == 12
        assert len(normal.monthly_precip_mm) == 12
        assert len(normal.monthly_solar_mj_m2) == 12
        # coldest_month_min_c == min(monthly_temp_min_c) (AC).
        assert normal.coldest_month_min_c == -3.0
        assert normal.coldest_month_min_c == min(normal.monthly_temp_min_c)
        assert normal.period_start_year == 2001
        assert normal.period_end_year == 2020
        assert normal.annual_temp_avg_c == 10.5

    def test_precip_mm_per_day_converted_to_monthly_total(self):
        adapter = NasaPowerWeatherAdapter()

        normal = adapter._map_climate_normals(NASA_CLIMATOLOGY_RESPONSE)

        # January: 2.0 mm/day × 31 days = 62.0 mm.
        assert normal.monthly_precip_mm[0] == 62.0
        # February (non-leap reference): 2.0 × 28 = 56.0 mm.
        assert normal.monthly_precip_mm[1] == 56.0

    def test_missing_parameter_returns_none(self):
        adapter = NasaPowerWeatherAdapter()

        assert adapter._map_climate_normals({"properties": {"parameter": {}}}) is None

    def test_partial_month_series_yields_empty_list(self):
        adapter = NasaPowerWeatherAdapter()
        payload = {
            "properties": {
                "parameter": {
                    "T2M_MIN": {"JAN": -3.0, "FEB": -1.0},  # only two months
                }
            }
        }

        normal = adapter._map_climate_normals(payload)

        assert normal is not None
        # A partial series is dropped rather than mis-aligned.
        assert normal.monthly_temp_min_c == []
        assert normal.coldest_month_min_c is None


class TestAsyncPaths:
    @pytest.mark.asyncio
    async def test_fetch_daily_calls_daily_point_endpoint(self):
        adapter = NasaPowerWeatherAdapter(base_url="https://power.test/api/temporal")
        mock_resp = MagicMock()
        mock_resp.json.return_value = NASA_DAILY_RESPONSE
        mock_resp.raise_for_status = MagicMock()

        with patch("app.data_access.external.nasa_power_weather_adapter.httpx.AsyncClient") as mock_cls:
            mock_ac = AsyncMock()
            mock_ac.get.return_value = mock_resp
            mock_ac.__aenter__ = AsyncMock(return_value=mock_ac)
            mock_ac.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_ac

            records = await adapter.fetch_daily(latitude=52.5, longitude=13.4)

        assert len(records) == 2
        called_url = mock_ac.get.call_args.args[0]
        assert called_url == "https://power.test/api/temporal/daily/point"
        params = mock_ac.get.call_args.kwargs["params"]
        assert params["community"] == "AG"
        assert "ALLSKY_SFC_SW_DWN" in params["parameters"]

    @pytest.mark.asyncio
    async def test_fetch_climate_normals_calls_climatology_endpoint(self):
        adapter = NasaPowerWeatherAdapter(base_url="https://power.test/api/temporal")
        mock_resp = MagicMock()
        mock_resp.json.return_value = NASA_CLIMATOLOGY_RESPONSE
        mock_resp.raise_for_status = MagicMock()

        with patch("app.data_access.external.nasa_power_weather_adapter.httpx.AsyncClient") as mock_cls:
            mock_ac = AsyncMock()
            mock_ac.get.return_value = mock_resp
            mock_ac.__aenter__ = AsyncMock(return_value=mock_ac)
            mock_ac.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_ac

            normal = await adapter.fetch_climate_normals(latitude=52.5, longitude=13.4)

        assert normal is not None
        called_url = mock_ac.get.call_args.args[0]
        assert called_url == "https://power.test/api/temporal/climatology/point"


class TestRegistrationContract:
    def test_adapter_is_keyless_public(self):
        assert NasaPowerWeatherAdapter.requires_api_key is False
        assert NasaPowerWeatherAdapter.kind == "public"

    def test_registered_in_registry(self):
        # Importing the module ran the @register decorator side effect.
        assert WeatherAdapterRegistry.get("nasa-power") is NasaPowerWeatherAdapter
        assert "nasa-power" in WeatherAdapterRegistry.public_sources()
