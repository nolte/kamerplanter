"""REQ-046 / REQ-041 — the concrete weather adapters register on import."""

# Importing the modules triggers the ``@WeatherAdapterRegistry.register`` decorators.
import app.data_access.external.dwd_weather_adapter  # noqa: F401
import app.data_access.external.home_assistant_weather_adapter  # noqa: F401
import app.data_access.external.nasa_power_weather_adapter  # noqa: F401  REQ-041
import app.data_access.external.open_meteo_weather_adapter  # noqa: F401
import app.data_access.external.openweathermap_weather_adapter  # noqa: F401
from app.data_access.external.weather_attributions import WEATHER_ATTRIBUTIONS
from app.domain.services.weather_adapter_registry import WeatherAdapterRegistry


class TestWeatherAdapterRegistration:
    def test_all_adapters_registered(self):
        registered = WeatherAdapterRegistry.all()

        assert "open-meteo" in registered
        assert "dwd" in registered
        assert "openweathermap" in registered
        assert "ha_weather" in registered
        # REQ-041 — NASA POWER reanalysis / climate-normal adapter.
        assert "nasa-power" in registered

    def test_public_sources_exclude_ha_weather(self):
        public = WeatherAdapterRegistry.public_sources()

        assert "open-meteo" in public
        assert "dwd" in public
        assert "openweathermap" in public
        assert "nasa-power" in public
        assert "ha_weather" not in public

    def test_attributions_present_for_public_sources(self):
        assert set(WEATHER_ATTRIBUTIONS) == {"open-meteo", "dwd", "openweathermap", "nasa-power"}
        # REQ-041 licence gate — NASA POWER attribution is non-empty and cites POWER.
        assert "NASA POWER" in WEATHER_ATTRIBUTIONS["nasa-power"]
