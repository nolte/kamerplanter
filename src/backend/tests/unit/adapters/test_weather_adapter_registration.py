"""REQ-046 — the four concrete weather adapters register on import."""

# Importing the modules triggers the ``@WeatherAdapterRegistry.register`` decorators.
import app.data_access.external.dwd_weather_adapter  # noqa: F401
import app.data_access.external.home_assistant_weather_adapter  # noqa: F401
import app.data_access.external.open_meteo_weather_adapter  # noqa: F401
import app.data_access.external.openweathermap_weather_adapter  # noqa: F401
from app.data_access.external.weather_attributions import WEATHER_ATTRIBUTIONS
from app.domain.services.weather_adapter_registry import WeatherAdapterRegistry


class TestWeatherAdapterRegistration:
    def test_all_four_adapters_registered(self):
        registered = WeatherAdapterRegistry.all()

        assert "open-meteo" in registered
        assert "dwd" in registered
        assert "openweathermap" in registered
        assert "ha_weather" in registered

    def test_public_sources_exclude_ha_weather(self):
        public = WeatherAdapterRegistry.public_sources()

        assert "open-meteo" in public
        assert "dwd" in public
        assert "openweathermap" in public
        assert "ha_weather" not in public

    def test_attributions_present_for_public_sources(self):
        assert set(WEATHER_ATTRIBUTIONS) == {"open-meteo", "dwd", "openweathermap"}
