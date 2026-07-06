"""Unit tests for the REQ-046 ``WeatherSettingsService`` (central provider admin).

Covers effective resolution (DB override wins over env, env fallback without a
DB doc), global OWM key encryption + preservation-on-unchanged, and the
connection test using the effective config.
"""

from unittest.mock import MagicMock

import httpx
import pytest
from cryptography.fernet import Fernet

from app.domain.engines.encryption_engine import EncryptionEngine
from app.domain.interfaces.weather_adapter import WeatherAdapter
from app.domain.models.system_settings import SystemSettings, WeatherProviderSettings
from app.domain.services.weather_adapter_registry import WeatherAdapterRegistry
from app.domain.services.weather_settings_service import (
    _MASKED_SECRET,
    WeatherSettingsService,
)


def _engine() -> EncryptionEngine:
    return EncryptionEngine(Fernet.generate_key().decode())


def _service(stored: SystemSettings | None = None, *, engine: EncryptionEngine | None = None):
    repo = MagicMock()
    repo.get.return_value = stored
    repo.upsert.side_effect = lambda s: s
    return WeatherSettingsService(repo, engine or _engine()), repo


@pytest.fixture
def registry_guard():
    original = WeatherAdapterRegistry._adapters.copy()
    WeatherAdapterRegistry.clear()
    yield
    WeatherAdapterRegistry._adapters = original


def _set_env(env: MagicMock) -> None:
    env.open_meteo_enabled = True
    env.open_meteo_base_url = "https://env.open-meteo/v1"
    env.dwd_enabled = True
    env.dwd_base_url = "https://env.dwd"
    env.openweathermap_enabled = True
    env.openweathermap_base_url = "https://env.owm"
    env.weather_fetch_timeout_s = 20
    env.weather_default_public_source = "open-meteo"


class TestEffectiveSettings:
    def test_env_fallback_without_db_doc(self):
        service, _ = _service(stored=None)
        with _patch_env() as env:
            _set_env(env)
            effective = service.get_effective_weather_settings()
        assert effective.providers["open-meteo"].base_url == "https://env.open-meteo/v1"
        assert effective.providers["dwd"].enabled is True
        assert effective.fetch_timeout_s == 20
        assert effective.default_public_source == "open-meteo"
        assert effective.openweathermap_global_api_key is None

    def test_db_override_wins_over_env(self):
        stored = SystemSettings(
            weather_providers=WeatherProviderSettings(
                dwd_enabled=False,
                open_meteo_base_url="https://db.open-meteo/v1",
                fetch_timeout_s=45,
                default_public_source="dwd",
            )
        )
        service, _ = _service(stored=stored)
        with _patch_env() as env:
            _set_env(env)
            effective = service.get_effective_weather_settings()
        assert effective.providers["dwd"].enabled is False  # DB override
        assert effective.providers["open-meteo"].base_url == "https://db.open-meteo/v1"
        assert effective.providers["openweathermap"].base_url == "https://env.owm"  # env fallback
        assert effective.fetch_timeout_s == 45
        assert effective.default_public_source == "dwd"

    def test_global_key_decrypted(self):
        engine = _engine()
        stored = SystemSettings(
            weather_providers=WeatherProviderSettings(
                openweathermap_global_api_key_encrypted=engine.encrypt("global-secret"),
            )
        )
        service, _ = _service(stored=stored, engine=engine)
        with _patch_env() as env:
            _set_env(env)
            effective = service.get_effective_weather_settings()
        assert effective.openweathermap_global_api_key == "global-secret"


class TestUpdate:
    def test_new_global_key_is_encrypted(self):
        engine = _engine()
        service, repo = _service(stored=None, engine=engine)
        service.update_weather_settings(openweathermap_global_api_key="fresh-key")
        upserted = repo.upsert.call_args[0][0]
        cipher = upserted.weather_providers.openweathermap_global_api_key_encrypted
        assert cipher is not None
        assert cipher != "fresh-key"
        assert engine.decrypt(cipher) == "fresh-key"

    def test_masked_key_preserves_existing_ciphertext(self):
        stored = SystemSettings(
            weather_providers=WeatherProviderSettings(
                openweathermap_global_api_key_encrypted="stored-cipher",
            )
        )
        service, repo = _service(stored=stored)
        service.update_weather_settings(openweathermap_global_api_key=_MASKED_SECRET)
        upserted = repo.upsert.call_args[0][0]
        assert upserted.weather_providers.openweathermap_global_api_key_encrypted == "stored-cipher"

    def test_empty_key_preserves_existing_ciphertext(self):
        stored = SystemSettings(
            weather_providers=WeatherProviderSettings(
                openweathermap_global_api_key_encrypted="stored-cipher",
            )
        )
        service, repo = _service(stored=stored)
        service.update_weather_settings(openweathermap_global_api_key="", dwd_enabled=False)
        upserted = repo.upsert.call_args[0][0]
        assert upserted.weather_providers.openweathermap_global_api_key_encrypted == "stored-cipher"
        assert upserted.weather_providers.dwd_enabled is False

    def test_unknown_default_source_raises(self):
        service, repo = _service(stored=None)
        with pytest.raises(ValueError, match="Unknown weather source"):
            service.update_weather_settings(default_public_source="nope")
        repo.upsert.assert_not_called()

    def test_has_global_key_flag(self):
        service_set, _ = _service(
            stored=SystemSettings(
                weather_providers=WeatherProviderSettings(openweathermap_global_api_key_encrypted="c"),
            )
        )
        service_unset, _ = _service(stored=None)
        assert service_set.has_global_openweathermap_key() is True
        assert service_unset.has_global_openweathermap_key() is False


class TestProviderTest:
    @pytest.mark.asyncio
    async def test_reachable_with_preview(self, registry_guard):
        class _Stub(WeatherAdapter):
            source_name = "open-meteo"
            kind = "public"

            def __init__(self, **kwargs):
                self._kwargs = kwargs

            async def fetch_daily(self, *, latitude, longitude, config=None):
                from datetime import UTC, datetime

                from app.domain.models.weather import WeatherForecast

                return [
                    WeatherForecast(
                        site_key="",
                        forecast_date=datetime.now(tz=UTC).date(),
                        source="open-meteo",
                        fetched_at=datetime.now(tz=UTC),
                    )
                ] * 5

            async def health_check(self, *, config=None):
                return True

        WeatherAdapterRegistry.register(_Stub)
        service, _ = _service(stored=None)
        with _patch_env() as env:
            _set_env(env)
            result = await service.test_provider("open-meteo")
        assert result.reachable is True
        assert 1 <= len(result.preview) <= 3

    @pytest.mark.asyncio
    async def test_broken_provider_no_500(self, registry_guard):
        class _Stub(WeatherAdapter):
            source_name = "dwd"
            kind = "public"

            def __init__(self, **kwargs):
                pass

            async def fetch_daily(self, *, latitude, longitude, config=None):
                raise httpx.ConnectError("refused")

            async def health_check(self, *, config=None):
                raise httpx.ConnectError("refused")

        WeatherAdapterRegistry.register(_Stub)
        service, _ = _service(stored=None)
        with _patch_env() as env:
            _set_env(env)
            result = await service.test_provider("dwd")
        assert result.reachable is False
        assert result.error

    @pytest.mark.asyncio
    async def test_disabled_provider_reports_disabled(self, registry_guard):
        service, _ = _service(
            stored=SystemSettings(weather_providers=WeatherProviderSettings(dwd_enabled=False)),
        )
        with _patch_env() as env:
            _set_env(env)
            result = await service.test_provider("dwd")
        assert result.reachable is False
        assert "disabled" in (result.error or "")

    @pytest.mark.asyncio
    async def test_unknown_source(self):
        service, _ = _service(stored=None)
        result = await service.test_provider("bogus")
        assert result.reachable is False


def _patch_env():
    from unittest.mock import patch

    return patch("app.domain.services.weather_settings_service.env_settings")
