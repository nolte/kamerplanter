"""Unit tests for the REQ-046 weather domain models."""

from datetime import date, datetime

from app.domain.models.weather import (
    HaSensorMapping,
    WeatherForecast,
    WeatherSourceConfig,
    WeatherSourceEntry,
    WeatherSourceHaConfig,
    WeatherSourcePublicConfig,
)


class TestWeatherForecast:
    def test_additive_defaults(self):
        fc = WeatherForecast(
            site_key="site1",
            forecast_date=date(2026, 7, 5),
            source="open-meteo",
            fetched_at=datetime(2026, 7, 5, 6, 0, 0),
        )

        assert fc.data_kind == "forecast"
        assert fc.is_current_conditions is False
        # Numeric fields are optional (HA sensor mapping may leave them None).
        assert fc.temp_min_c is None
        assert fc.wind_gust_kmh is None
        assert fc.solar_radiation_mj_m2 is None

    def test_observed_current_conditions(self):
        fc = WeatherForecast(
            site_key="site1",
            forecast_date=date(2026, 7, 5),
            source="ha_weather",
            fetched_at=datetime(2026, 7, 5, 6, 0, 0),
            data_kind="observed",
            is_current_conditions=True,
            temp_max_c=21.4,
        )

        assert fc.data_kind == "observed"
        assert fc.is_current_conditions is True

    def test_key_alias_round_trip(self):
        fc = WeatherForecast(
            _key="wf1",
            site_key="site1",
            forecast_date=date(2026, 7, 5),
            source="dwd",
            fetched_at=datetime(2026, 7, 5, 6, 0, 0),
        )

        assert fc.key == "wf1"
        dumped = fc.model_dump(by_alias=True)
        assert dumped["_key"] == "wf1"
        # populate_by_name allows constructing from the field name too.
        assert WeatherForecast(key="wf2", **{k: v for k, v in fc.model_dump().items() if k != "key"}).key == "wf2"


class TestWeatherSourceConfig:
    def test_mixed_public_and_ha_sources(self):
        cfg = WeatherSourceConfig(
            site_key="site1",
            tenant_key="tenantA",
            sources=[
                WeatherSourceEntry(
                    source_name="ha-weather",
                    kind="home_assistant",
                    config=WeatherSourceHaConfig(
                        mode="sensor_mapping",
                        sensor_mapping=HaSensorMapping(
                            temp_max_entity="sensor.outdoor_temp",
                            humidity_entity="sensor.outdoor_humidity",
                        ),
                    ),
                ),
                WeatherSourceEntry(
                    source_name="open-meteo",
                    kind="public",
                    config=None,
                ),
                WeatherSourceEntry(
                    source_name="openweathermap",
                    kind="public",
                    config=WeatherSourcePublicConfig(api_key_ref="secret-ref-123"),
                ),
            ],
        )

        assert cfg.enabled is True
        assert len(cfg.sources) == 3
        # Smart-union resolution keeps the correct config subtype per entry.
        assert isinstance(cfg.sources[0].config, WeatherSourceHaConfig)
        assert cfg.sources[0].config.mode == "sensor_mapping"
        assert cfg.sources[0].config.sensor_mapping.temp_max_entity == "sensor.outdoor_temp"
        assert cfg.sources[1].config is None
        assert isinstance(cfg.sources[2].config, WeatherSourcePublicConfig)
        assert cfg.sources[2].config.api_key_ref == "secret-ref-123"

    def test_ha_weather_entity_mode(self):
        entry = WeatherSourceEntry(
            source_name="ha-weather",
            kind="home_assistant",
            config=WeatherSourceHaConfig(mode="weather_entity", weather_entity_id="weather.home"),
        )

        assert isinstance(entry.config, WeatherSourceHaConfig)
        assert entry.config.weather_entity_id == "weather.home"
        assert entry.config.sensor_mapping is None

    def test_key_alias_round_trip(self):
        cfg = WeatherSourceConfig(_key="cfg1", site_key="site1", tenant_key="tenantA")

        assert cfg.key == "cfg1"
        assert cfg.model_dump(by_alias=True)["_key"] == "cfg1"
