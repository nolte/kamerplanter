"""Unit tests for the REQ-046 ``WeatherSourceService`` (PR-4, Welle 2).

Covers the substantive logic: OWM key encryption + preservation-on-unchanged
(AC-8), the denormalized ``Site.weather_source_priority`` view, the site
ownership guard (AC-11), the available-sources provider filter, and the unsaved
connection test (AC-7).
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import httpx
import pytest
from cryptography.fernet import Fernet

from app.api.v1.tenant_scoped.weather.schemas import (
    HaSensorMappingRequest,
    WeatherSourceConfigRequest,
    WeatherSourceEntryRequest,
    WeatherSourceHaConfigRequest,
    WeatherSourcePublicConfigRequest,
)
from app.common.exceptions import ForbiddenError, NotFoundError
from app.domain.engines.encryption_engine import EncryptionEngine
from app.domain.interfaces.weather_adapter import WeatherAdapter
from app.domain.models.site import Site
from app.domain.models.weather import (
    WeatherForecast,
    WeatherSourceConfig,
    WeatherSourceEntry,
    WeatherSourceHaConfig,
    WeatherSourcePublicConfig,
)
from app.domain.services.weather_adapter_registry import WeatherAdapterRegistry
from app.domain.services.weather_source_service import _MASKED_SECRET, WeatherSourceService

TENANT_KEY = "t-1"
SITE_KEY = "site-1"


def _site(tenant_key: str = TENANT_KEY) -> Site:
    return Site(_key=SITE_KEY, tenant_key=tenant_key, name="Garden", gps_coordinates=(52.5, 13.4))


def _forecast(source: str) -> WeatherForecast:
    return WeatherForecast(
        site_key="",
        forecast_date=datetime.now(tz=UTC).date(),
        source=source,
        fetched_at=datetime.now(tz=UTC),
        temp_min_c=5.0,
        temp_max_c=12.0,
    )


@pytest.fixture
def registry_guard():
    original = WeatherAdapterRegistry._adapters.copy()
    WeatherAdapterRegistry.clear()
    yield
    WeatherAdapterRegistry._adapters = original


def _build_service(*, site=None, existing=None, ha_client=None, encryption=None):
    site_repo = MagicMock()
    site_repo.get_site_by_key.return_value = site if site is not None else _site()
    config_repo = MagicMock()
    config_repo.get_by_site.return_value = existing
    config_repo.upsert.side_effect = lambda cfg: cfg
    engine = encryption if encryption is not None else EncryptionEngine(Fernet.generate_key().decode())
    service = WeatherSourceService(
        weather_source_config_repo=config_repo,
        site_repo=site_repo,
        encryption_engine=engine,
        resolver=MagicMock(),
        ha_client_factory=lambda: ha_client,
    )
    return service, config_repo, site_repo, engine


def _public_entry_request(api_key=None, units_hint=None):
    return WeatherSourceEntryRequest(
        source_name="openweathermap",
        kind="public",
        enabled=True,
        public_config=WeatherSourcePublicConfigRequest(api_key=api_key, units_hint=units_hint),
    )


class TestSaveConfig:
    def test_new_owm_key_is_encrypted(self):
        service, config_repo, _, engine = _build_service()
        request = WeatherSourceConfigRequest(sources=[_public_entry_request(api_key="plain-secret")])

        saved = service.save_config(SITE_KEY, TENANT_KEY, "user-1", request)

        stored = saved.sources[0].config
        assert isinstance(stored, WeatherSourcePublicConfig)
        assert stored.api_key_ref is not None
        assert stored.api_key_ref != "plain-secret"  # ciphertext, not plaintext
        assert engine.decrypt(stored.api_key_ref) == "plain-secret"
        config_repo.upsert.assert_called_once()

    def test_masked_key_preserves_existing_ciphertext(self):
        existing = WeatherSourceConfig(
            site_key=SITE_KEY,
            tenant_key=TENANT_KEY,
            sources=[
                WeatherSourceEntry(
                    source_name="openweathermap",
                    kind="public",
                    config=WeatherSourcePublicConfig(api_key_ref="stored-cipher"),
                )
            ],
        )
        service, _, _, _ = _build_service(existing=existing)
        request = WeatherSourceConfigRequest(sources=[_public_entry_request(api_key=_MASKED_SECRET)])

        saved = service.save_config(SITE_KEY, TENANT_KEY, "user-1", request)

        assert saved.sources[0].config.api_key_ref == "stored-cipher"

    def test_empty_key_preserves_existing_ciphertext(self):
        existing = WeatherSourceConfig(
            site_key=SITE_KEY,
            tenant_key=TENANT_KEY,
            sources=[
                WeatherSourceEntry(
                    source_name="openweathermap",
                    kind="public",
                    config=WeatherSourcePublicConfig(api_key_ref="stored-cipher"),
                )
            ],
        )
        service, _, _, _ = _build_service(existing=existing)
        request = WeatherSourceConfigRequest(sources=[_public_entry_request(api_key=None)])

        saved = service.save_config(SITE_KEY, TENANT_KEY, "user-1", request)

        assert saved.sources[0].config.api_key_ref == "stored-cipher"

    def test_denormalized_priority_updated_on_site(self):
        service, _, site_repo, _ = _build_service()
        request = WeatherSourceConfigRequest(
            sources=[
                WeatherSourceEntryRequest(source_name="open-meteo", kind="public", enabled=True),
                WeatherSourceEntryRequest(source_name="dwd", kind="public", enabled=False),
            ]
        )

        service.save_config(SITE_KEY, TENANT_KEY, "user-1", request)

        site_repo.update_site.assert_called_once()
        saved_site = site_repo.update_site.call_args.args[1]
        assert saved_site.weather_source_priority == ["open-meteo"]  # only the enabled one

    def test_ha_config_is_stored(self):
        service, _, _, _ = _build_service()
        request = WeatherSourceConfigRequest(
            sources=[
                WeatherSourceEntryRequest(
                    source_name="ha_weather",
                    kind="home_assistant",
                    ha_config=WeatherSourceHaConfigRequest(
                        mode="sensor_mapping",
                        sensor_mapping=HaSensorMappingRequest(temp_max_entity="sensor.outside_temp"),
                    ),
                )
            ]
        )

        saved = service.save_config(SITE_KEY, TENANT_KEY, "user-1", request)

        stored = saved.sources[0].config
        assert isinstance(stored, WeatherSourceHaConfig)
        assert stored.mode == "sensor_mapping"
        assert stored.sensor_mapping.temp_max_entity == "sensor.outside_temp"


class TestOwnershipGuard:
    def test_get_config_foreign_tenant_forbidden(self):
        service, _, _, _ = _build_service(site=_site(tenant_key="other-tenant"))
        with pytest.raises(ForbiddenError):
            service.get_config(SITE_KEY, TENANT_KEY)

    def test_get_config_missing_site_not_found(self):
        service, _, site_repo, _ = _build_service()
        site_repo.get_site_by_key.return_value = None
        with pytest.raises(NotFoundError):
            service.get_config(SITE_KEY, TENANT_KEY)

    def test_save_foreign_tenant_forbidden_and_no_write(self):
        service, config_repo, _, _ = _build_service(site=_site(tenant_key="other-tenant"))
        request = WeatherSourceConfigRequest(sources=[])
        with pytest.raises(ForbiddenError):
            service.save_config(SITE_KEY, TENANT_KEY, "user-1", request)
        config_repo.upsert.assert_not_called()


class TestAvailableSources:
    def test_lists_enabled_public_plus_ha(self, registry_guard, monkeypatch):
        _register_public("open-meteo", requires_api_key=False)
        _register_public("dwd", requires_api_key=False)
        _register_public("openweathermap", requires_api_key=True)
        _register_ha()
        import app.domain.services.weather_source_service as mod

        monkeypatch.setattr(mod.settings, "dwd_enabled", False, raising=False)
        service, _, _, _ = _build_service(ha_client=object())

        result = service.available_sources(TENANT_KEY)

        names = {s.source_name for s in result.sources}
        assert "open-meteo" in names
        assert "openweathermap" in names
        assert "dwd" not in names  # disabled provider filtered out
        assert "ha_weather" in names
        assert result.ha_token_set is True

    def test_ha_token_absent(self, registry_guard):
        _register_public("open-meteo", requires_api_key=False)
        _register_ha()
        service, _, _, _ = _build_service(ha_client=None)

        result = service.available_sources(TENANT_KEY)

        assert result.ha_token_set is False


class TestTestSource:
    @pytest.mark.asyncio
    async def test_reachable_with_preview(self, registry_guard):
        _register_public("open-meteo", records=[_forecast("open-meteo")] * 5)
        service, config_repo, _, _ = _build_service()
        entry = WeatherSourceEntryRequest(source_name="open-meteo", kind="public")

        result = await service.test_source(SITE_KEY, TENANT_KEY, entry)

        assert result.reachable is True
        assert 1 <= len(result.preview) <= 3
        config_repo.upsert.assert_not_called()  # test saves nothing

    @pytest.mark.asyncio
    async def test_http_error_returns_reachable_false(self, registry_guard):
        _register_public("open-meteo", raise_exc=httpx.ConnectError("refused"))
        service, config_repo, _, _ = _build_service()
        entry = WeatherSourceEntryRequest(source_name="open-meteo", kind="public")

        result = await service.test_source(SITE_KEY, TENANT_KEY, entry)

        assert result.reachable is False
        assert result.error
        config_repo.upsert.assert_not_called()

    @pytest.mark.asyncio
    async def test_owm_uses_body_key_not_store(self, registry_guard):
        captured = {}

        @WeatherAdapterRegistry.register
        class _OwmStub(WeatherAdapter):
            source_name = "openweathermap"
            kind = "public"
            requires_api_key = True

            def __init__(self, api_key=None, **kwargs):
                captured["api_key"] = api_key

            async def fetch_daily(self, *, latitude, longitude, config=None):
                return [_forecast("openweathermap")]

            async def health_check(self, *, config=None):
                return True

        service, _, _, _ = _build_service()
        entry = WeatherSourceEntryRequest(
            source_name="openweathermap",
            kind="public",
            public_config=WeatherSourcePublicConfigRequest(api_key="body-key"),
        )

        result = await service.test_source(SITE_KEY, TENANT_KEY, entry)

        assert captured["api_key"] == "body-key"  # straight from the request body
        assert result.reachable is True

    @pytest.mark.asyncio
    async def test_ha_without_token_is_not_reachable(self, registry_guard):
        _register_ha()
        service, _, _, _ = _build_service(ha_client=None)
        entry = WeatherSourceEntryRequest(
            source_name="ha_weather",
            kind="home_assistant",
            ha_config=WeatherSourceHaConfigRequest(mode="weather_entity", weather_entity_id="weather.home"),
        )

        result = await service.test_source(SITE_KEY, TENANT_KEY, entry)

        assert result.reachable is False
        assert result.error


class TestHaEntities:
    def test_weather_entities_with_token(self):
        ha_client = MagicMock()
        ha_client.list_weather_entities.return_value = [{"entity_id": "weather.home", "friendly_name": "Home"}]
        service, _, _, _ = _build_service(ha_client=ha_client)

        assert service.list_ha_weather_entities() == [{"entity_id": "weather.home", "friendly_name": "Home"}]

    def test_sensor_entities_without_token_returns_empty(self):
        service, _, _, _ = _build_service(ha_client=None)
        assert service.list_ha_sensor_entities() == []


# ── Stub adapter registration helpers ──────────────────────────────────────


def _register_public(source_name, *, records=None, raise_exc=None, requires_api_key=False):
    resolved_records = records if records is not None else [_forecast(source_name)]

    class _Stub(WeatherAdapter):
        async def fetch_daily(self, *, latitude, longitude, config=None):
            if raise_exc is not None:
                raise raise_exc
            return list(resolved_records)

        async def health_check(self, *, config=None):
            if raise_exc is not None:
                raise raise_exc
            return bool(resolved_records)

    _Stub.source_name = source_name
    _Stub.kind = "public"
    _Stub.requires_api_key = requires_api_key
    WeatherAdapterRegistry.register(_Stub)
    return _Stub


def _register_ha():
    class _HaStub(WeatherAdapter):
        source_name = "ha_weather"
        kind = "home_assistant"
        requires_api_key = False

        def __init__(self, ha_client):
            self._ha = ha_client

        async def fetch_daily(self, *, latitude, longitude, config=None):
            return [_forecast("ha_weather")]

        async def health_check(self, *, config=None):
            return True

    WeatherAdapterRegistry.register(_HaStub)
    return _HaStub
