"""Unit tests for the REQ-046 ``WeatherAdapterRegistry``.

The registry stores the adapter **class** (not an instance), because weather
adapters need constructor dependencies (an ``httpx.AsyncClient`` or the HA
client) that are only available at build time.
"""

from app.domain.interfaces.weather_adapter import WeatherAdapter
from app.domain.models.weather import WeatherForecast
from app.domain.services.weather_adapter_registry import WeatherAdapterRegistry


class DummyPublicAdapter(WeatherAdapter):
    source_name = "dummy-public"
    kind = "public"
    requires_api_key = False

    async def fetch_daily(self, *, latitude, longitude, config=None) -> list[WeatherForecast]:
        return []


class DummyHaAdapter(WeatherAdapter):
    source_name = "dummy-ha"
    kind = "home_assistant"
    requires_api_key = False

    async def fetch_daily(self, *, latitude, longitude, config=None) -> list[WeatherForecast]:
        return []


class TestWeatherAdapterRegistry:
    def setup_method(self):
        self._original = WeatherAdapterRegistry._adapters.copy()
        WeatherAdapterRegistry.clear()

    def teardown_method(self):
        WeatherAdapterRegistry._adapters = self._original

    def test_register_returns_class_and_stores_class(self):
        returned = WeatherAdapterRegistry.register(DummyPublicAdapter)

        assert returned is DummyPublicAdapter
        # The registry stores the class itself, never an instance.
        assert WeatherAdapterRegistry.get("dummy-public") is DummyPublicAdapter

    def test_get_unknown_returns_none(self):
        assert WeatherAdapterRegistry.get("nope") is None

    def test_all_returns_copy(self):
        WeatherAdapterRegistry.register(DummyPublicAdapter)

        snapshot = WeatherAdapterRegistry.all()
        assert snapshot == {"dummy-public": DummyPublicAdapter}
        snapshot["mutated"] = DummyHaAdapter
        assert "mutated" not in WeatherAdapterRegistry.all()

    def test_public_sources_only_lists_public_kind(self):
        WeatherAdapterRegistry.register(DummyPublicAdapter)
        WeatherAdapterRegistry.register(DummyHaAdapter)

        assert WeatherAdapterRegistry.public_sources() == ["dummy-public"]

    def test_clear_empties_registry(self):
        WeatherAdapterRegistry.register(DummyPublicAdapter)
        WeatherAdapterRegistry.clear()

        assert WeatherAdapterRegistry.all() == {}
        assert WeatherAdapterRegistry.public_sources() == []
