"""Unit tests for the REQ-046 ``WeatherSourceResolver`` fallback chain."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
import pytest

from app.domain.interfaces.weather_adapter import WeatherAdapter
from app.domain.models.weather import (
    WeatherForecast,
    WeatherSourceConfig,
    WeatherSourceEntry,
    WeatherSourcePublicConfig,
)
from app.domain.services.weather_adapter_registry import WeatherAdapterRegistry
from app.domain.services.weather_source_resolver import WeatherSourceResolver


def _forecast(source: str) -> WeatherForecast:
    return WeatherForecast(
        site_key="",
        forecast_date=datetime.now(tz=UTC).date(),
        source=source,
        fetched_at=datetime.now(tz=UTC),
    )


def _site():
    return SimpleNamespace(gps_coordinates=(52.5, 13.4))


class _StubAdapter(WeatherAdapter):
    kind = "public"
    result: list[WeatherForecast] = []
    raise_exc: Exception | None = None

    async def fetch_daily(self, *, latitude, longitude, config=None):
        if self.raise_exc is not None:
            raise self.raise_exc
        return list(type(self).result)


@pytest.fixture
def registry_guard():
    original = WeatherAdapterRegistry._adapters.copy()
    WeatherAdapterRegistry.clear()
    yield
    WeatherAdapterRegistry._adapters = original


def _register(source_name: str, *, result=None, raise_exc=None, kind="public"):
    cls = type(
        f"Stub_{source_name}",
        (_StubAdapter,),
        {
            "source_name": source_name,
            "kind": kind,
            "result": result or [],
            "raise_exc": raise_exc,
        },
    )
    WeatherAdapterRegistry.register(cls)
    return cls


def _entry(source_name, kind="public", config=None):
    return WeatherSourceEntry(source_name=source_name, kind=kind, enabled=True, config=config)


class TestResolveDaily:
    @pytest.mark.asyncio
    async def test_first_source_wins(self, registry_guard):
        _register("open-meteo", result=[_forecast("open-meteo")])
        _register("dwd", result=[_forecast("dwd")])
        resolver = WeatherSourceResolver(MagicMock(), lambda: None)
        cfg = WeatherSourceConfig(site_key="s1", sources=[_entry("open-meteo"), _entry("dwd")])

        records = await resolver.resolve_daily(_site(), cfg)

        assert [r.source for r in records] == ["open-meteo"]

    @pytest.mark.asyncio
    async def test_timeout_falls_back_to_next(self, registry_guard):
        _register("open-meteo", raise_exc=httpx.TimeoutException("boom"))
        _register("dwd", result=[_forecast("dwd")])
        resolver = WeatherSourceResolver(MagicMock(), lambda: None)
        cfg = WeatherSourceConfig(site_key="s1", sources=[_entry("open-meteo"), _entry("dwd")])

        records = await resolver.resolve_daily(_site(), cfg)

        assert [r.source for r in records] == ["dwd"]

    @pytest.mark.asyncio
    async def test_all_empty_returns_empty(self, registry_guard):
        _register("open-meteo", result=[])
        _register("dwd", result=[])
        resolver = WeatherSourceResolver(MagicMock(), lambda: None)
        cfg = WeatherSourceConfig(site_key="s1", sources=[_entry("open-meteo"), _entry("dwd")])

        records = await resolver.resolve_daily(_site(), cfg)

        assert records == []

    @pytest.mark.asyncio
    async def test_no_config_uses_default_source(self, registry_guard, monkeypatch):
        _register("open-meteo", result=[_forecast("open-meteo")])
        from app.domain.services import weather_source_resolver as mod

        monkeypatch.setattr(mod.settings, "weather_default_public_source", "open-meteo", raising=False)
        resolver = WeatherSourceResolver(MagicMock(), lambda: None)

        records = await resolver.resolve_daily(_site(), None)

        assert [r.source for r in records] == ["open-meteo"]

    @pytest.mark.asyncio
    async def test_owm_key_decrypted_and_passed_to_adapter(self, registry_guard):
        captured = {}

        class OwmStub(_StubAdapter):
            source_name = "openweathermap"
            result = [_forecast("openweathermap")]

            def __init__(self, api_key=None, **kwargs):
                captured["api_key"] = api_key

        WeatherAdapterRegistry.register(OwmStub)
        encryption = MagicMock()
        encryption.decrypt.return_value = "plaintext-key"
        resolver = WeatherSourceResolver(encryption, lambda: None)
        cfg = WeatherSourceConfig(
            site_key="s1",
            sources=[
                _entry("openweathermap", config=WeatherSourcePublicConfig(api_key_ref="cipher")),
            ],
        )

        records = await resolver.resolve_daily(_site(), cfg)

        encryption.decrypt.assert_called_once_with("cipher")
        assert captured["api_key"] == "plaintext-key"
        assert [r.source for r in records] == ["openweathermap"]

    @pytest.mark.asyncio
    async def test_ha_source_skipped_when_no_client(self, registry_guard):
        class HaStub(_StubAdapter):
            source_name = "ha_weather"
            kind = "home_assistant"
            result = [_forecast("ha_weather")]

            def __init__(self, ha_client):
                self._ha = ha_client

        WeatherAdapterRegistry.register(HaStub)
        _register("open-meteo", result=[_forecast("open-meteo")])
        resolver = WeatherSourceResolver(MagicMock(), lambda: None)  # ha factory -> None
        cfg = WeatherSourceConfig(
            site_key="s1",
            sources=[_entry("ha_weather", kind="home_assistant"), _entry("open-meteo")],
        )

        records = await resolver.resolve_daily(_site(), cfg)

        # HA source unavailable -> fell through to open-meteo.
        assert [r.source for r in records] == ["open-meteo"]

    @pytest.mark.asyncio
    async def test_no_gps_returns_empty(self, registry_guard):
        _register("open-meteo", result=[_forecast("open-meteo")])
        resolver = WeatherSourceResolver(MagicMock(), lambda: None)
        cfg = WeatherSourceConfig(site_key="s1", sources=[_entry("open-meteo")])

        records = await resolver.resolve_daily(SimpleNamespace(gps_coordinates=None), cfg)

        assert records == []
