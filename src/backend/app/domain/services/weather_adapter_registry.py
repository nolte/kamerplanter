"""REQ-046 §3.2 — ``WeatherAdapterRegistry`` (SSOT for weather adapters).

Registry of all weather adapters. Pattern analogous to ``AdapterRegistry``
(REQ-011), but it stores the adapter **class** (not an instance) because weather
adapters require constructor dependencies (an ``httpx.AsyncClient`` or the HA
client) that are only available at build time. REQ-041
(``NasaPowerWeatherAdapter``) and REQ-039 (climate-normal adapters) register
here — they do NOT define their own registry.
"""

from app.domain.interfaces.weather_adapter import WeatherAdapter


class WeatherAdapterRegistry:
    """Registry of weather-adapter classes keyed by ``source_name``."""

    _adapters: dict[str, type[WeatherAdapter]] = {}

    @classmethod
    def register(cls, adapter_cls: type[WeatherAdapter]) -> type[WeatherAdapter]:
        """Class decorator that registers the adapter **class** under its
        ``source_name`` and returns it unchanged."""
        cls._adapters[adapter_cls.source_name] = adapter_cls
        return adapter_cls

    @classmethod
    def get(cls, source_name: str) -> type[WeatherAdapter] | None:
        return cls._adapters.get(source_name)

    @classmethod
    def all(cls) -> dict[str, type[WeatherAdapter]]:
        return dict(cls._adapters)

    @classmethod
    def public_sources(cls) -> list[str]:
        return [name for name, adapter in cls._adapters.items() if adapter.kind == "public"]

    @classmethod
    def clear(cls) -> None:
        """Clear all registered adapters (for testing)."""
        cls._adapters = {}
