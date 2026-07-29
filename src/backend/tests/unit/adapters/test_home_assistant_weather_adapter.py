"""Unit tests for the REQ-046 ``HomeAssistantWeatherAdapter`` (both modes)."""

from datetime import date
from unittest.mock import MagicMock

import pytest

from app.common.datetimes import today_utc
from app.data_access.external.home_assistant_weather_adapter import HomeAssistantWeatherAdapter
from app.domain.models.weather import HaSensorMapping, WeatherSourceHaConfig


class TestEntityIdGuard:
    @pytest.mark.asyncio
    async def test_malicious_weather_entity_id_is_rejected(self):
        # SEC-003: a crafted entity_id must not reach the HA REST path.
        ha = MagicMock()
        adapter = HomeAssistantWeatherAdapter(ha)
        config = WeatherSourceHaConfig(mode="weather_entity", weather_entity_id="weather.x/../../api/config")

        records = await adapter.fetch_daily(latitude=0.0, longitude=0.0, config=config)

        assert records == []
        ha.get_state_attributes.assert_not_called()

    @pytest.mark.asyncio
    async def test_malicious_sensor_entity_id_is_skipped(self):
        # SEC-003: mapped sensor ids are validated before the HA call, too.
        ha = MagicMock()
        adapter = HomeAssistantWeatherAdapter(ha)
        config = WeatherSourceHaConfig(
            mode="sensor_mapping",
            sensor_mapping=HaSensorMapping(temp_min_entity="sensor.ok/../secrets"),
        )

        records = await adapter.fetch_daily(latitude=0.0, longitude=0.0, config=config)

        # one observed record is still produced, but the bad id is not read
        assert len(records) == 1
        assert records[0].temp_min_c is None
        ha.get_state.assert_not_called()


class TestModeAWeatherEntity:
    @pytest.mark.asyncio
    async def test_forecast_entity_produces_daily_records(self):
        ha = MagicMock()
        ha.get_state_attributes.return_value = {
            "forecast": [
                {
                    "datetime": "2026-07-05T00:00:00+00:00",
                    "temperature": 24.0,
                    "templow": 12.0,
                    "precipitation": 0.5,
                    "wind_speed": 15.0,
                    "humidity": 60,
                    "condition": "rainy",
                },
                {
                    "datetime": "2026-07-06T00:00:00+00:00",
                    "temperature": 26.0,
                    "templow": 14.0,
                    "condition": "sunny",
                },
            ]
        }
        adapter = HomeAssistantWeatherAdapter(ha)
        config = WeatherSourceHaConfig(mode="weather_entity", weather_entity_id="weather.home")

        records = await adapter.fetch_daily(latitude=0.0, longitude=0.0, config=config)

        assert len(records) == 2
        first = records[0]
        assert first.forecast_date == date(2026, 7, 5)
        assert first.temp_max_c == 24.0
        assert first.temp_min_c == 12.0
        assert first.precipitation_mm == 0.5
        assert first.wind_speed_kmh == 15.0
        assert first.humidity_percent == 60.0
        assert first.weather_code == "61"  # rainy -> WMO 61
        assert first.source == "ha_weather"
        assert first.data_kind == "forecast"
        assert first.is_current_conditions is False
        assert records[1].weather_code == "0"  # sunny -> WMO 0

    @pytest.mark.asyncio
    async def test_missing_attributes_returns_empty(self):
        ha = MagicMock()
        ha.get_state_attributes.return_value = None
        adapter = HomeAssistantWeatherAdapter(ha)
        config = WeatherSourceHaConfig(mode="weather_entity", weather_entity_id="weather.home")

        records = await adapter.fetch_daily(latitude=0.0, longitude=0.0, config=config)

        assert records == []


class TestModeBSensorMapping:
    @pytest.mark.asyncio
    async def test_sensor_mapping_produces_single_observed_record(self):
        ha = MagicMock()
        states = {
            "sensor.temp_min": {"value": 11.0},
            "sensor.temp_max": {"value": 23.0},
            "sensor.humidity": {"value": 55.0},
            "sensor.rain": {"value": 2.0},
            "sensor.unavailable": {"value": None},
        }
        ha.get_state.side_effect = lambda eid: states.get(eid)
        adapter = HomeAssistantWeatherAdapter(ha)
        mapping = HaSensorMapping(
            temp_min_entity="sensor.temp_min",
            temp_max_entity="sensor.temp_max",
            humidity_entity="sensor.humidity",
            precipitation_entity="sensor.rain",
            wind_speed_entity="sensor.unavailable",  # -> None
        )
        config = WeatherSourceHaConfig(mode="sensor_mapping", sensor_mapping=mapping)

        records = await adapter.fetch_daily(latitude=0.0, longitude=0.0, config=config)

        assert len(records) == 1
        record = records[0]
        # UTC, not ``date.today()``: the adapter stamps ``today_utc()`` (§12a,
        # #858) because this record's consumers filter it against a UTC day.
        assert record.forecast_date == today_utc()
        assert record.temp_min_c == 11.0
        assert record.temp_max_c == 23.0
        assert record.humidity_percent == 55.0
        assert record.precipitation_mm == 2.0
        assert record.wind_speed_kmh is None  # unavailable state
        assert record.wind_gust_kmh is None  # unmapped
        assert record.data_kind == "observed"
        assert record.is_current_conditions is True
        assert record.source == "ha_weather"

    @pytest.mark.asyncio
    async def test_falls_back_to_current_when_no_max(self):
        ha = MagicMock()
        states = {"sensor.current": {"value": 19.0}}
        ha.get_state.side_effect = lambda eid: states.get(eid)
        adapter = HomeAssistantWeatherAdapter(ha)
        mapping = HaSensorMapping(temp_current_entity="sensor.current")
        config = WeatherSourceHaConfig(mode="sensor_mapping", sensor_mapping=mapping)

        record = (await adapter.fetch_daily(latitude=0.0, longitude=0.0, config=config))[0]

        assert record.temp_max_c == 19.0
