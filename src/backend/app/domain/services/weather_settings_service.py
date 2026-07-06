"""REQ-046 follow-up — instance-wide public weather-provider settings.

Central admin management of the public weather services (Open-Meteo, DWD,
OpenWeatherMap), backed by the ``SYSTEM_SETTINGS`` singleton and mirroring the
Home-Assistant DB-override + env-fallback pattern
(:class:`SystemSettingsService.get_effective_ha_settings`).

Owns three concerns:

* **Effective resolution** — per provider ``enabled`` + ``base_url`` and the
  global ``fetch_timeout_s`` / ``default_public_source``, layering the DB
  override (``SystemSettings.weather_providers``) on top of the env defaults.
* **Secret handling** — the global OpenWeatherMap fallback key is Fernet-
  encrypted (via :class:`EncryptionEngine`) and stored as ciphertext. A new
  plaintext key is encrypted; an empty / masked value means "unchanged" so the
  stored ciphertext is preserved, never wiped. The decrypted plaintext is
  returned only through :meth:`get_effective_weather_settings` (internal use by
  the resolver / connection test) and never through the admin response.
* **Connection test** — builds an adapter from the *effective* config (base URL,
  timeout, and the global key for OpenWeatherMap) and reports reachability plus
  a small preview, mapping any adapter / HTTP error to ``reachable=False`` with a
  human-readable message instead of a ``500`` (the OWM adapter already redacts
  the key from its error strings — SEC-001).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
import structlog
from pydantic import BaseModel, Field

from app.config.settings import settings as env_settings
from app.domain.models.system_settings import SystemSettings, WeatherProviderSettings
from app.domain.models.weather import WeatherForecast
from app.domain.services.weather_adapter_registry import WeatherAdapterRegistry

if TYPE_CHECKING:
    from app.data_access.arango.system_settings_repository import ArangoSystemSettingsRepository
    from app.domain.engines.encryption_engine import EncryptionEngine

logger = structlog.get_logger(__name__)

#: The three public providers this service manages centrally. Other adapters
#: (e.g. a future REQ-041 nasa-power) are unaffected and stay env-driven.
WEATHER_PROVIDER_NAMES: tuple[str, ...] = ("open-meteo", "dwd", "openweathermap")

#: Placeholder the frontend echoes for an already-stored secret; treated (like an
#: empty value) as "global key unchanged".
_MASKED_SECRET = "••••"

#: Reference point (Berlin) for the connection-test preview.
_TEST_LAT = 52.52
_TEST_LON = 13.40


class EffectiveWeatherProvider(BaseModel):
    """Effective config of a single provider (DB override on top of env)."""

    enabled: bool
    base_url: str


class EffectiveWeatherSettings(BaseModel):
    """Resolved weather-provider settings for the resolver / fetch pipeline.

    ``openweathermap_global_api_key`` carries the **decrypted plaintext** global
    fallback key and is for internal use only — it is never serialised into an
    admin API response.
    """

    providers: dict[str, EffectiveWeatherProvider] = Field(default_factory=dict)
    openweathermap_global_api_key: str | None = None
    fetch_timeout_s: int = 20
    default_public_source: str = "open-meteo"

    def provider(self, source_name: str) -> EffectiveWeatherProvider | None:
        return self.providers.get(source_name)


class WeatherProviderTestResult(BaseModel):
    """Result of :meth:`WeatherSettingsService.test_provider`."""

    reachable: bool
    preview: list[WeatherForecast] = Field(default_factory=list)
    error: str | None = None


def env_effective_weather_settings() -> EffectiveWeatherSettings:
    """Effective settings from the environment alone (no DB override).

    Used as the fallback when no DB-backed provider is wired into the resolver
    (keeps the resolver usable in isolation / unit tests)."""
    return EffectiveWeatherSettings(
        providers={
            "open-meteo": EffectiveWeatherProvider(
                enabled=env_settings.open_meteo_enabled,
                base_url=env_settings.open_meteo_base_url,
            ),
            "dwd": EffectiveWeatherProvider(
                enabled=env_settings.dwd_enabled,
                base_url=env_settings.dwd_base_url,
            ),
            "openweathermap": EffectiveWeatherProvider(
                enabled=env_settings.openweathermap_enabled,
                base_url=env_settings.openweathermap_base_url,
            ),
        },
        openweathermap_global_api_key=None,
        fetch_timeout_s=env_settings.weather_fetch_timeout_s,
        default_public_source=env_settings.weather_default_public_source,
    )


class WeatherSettingsService:
    """Instance-wide public weather-provider configuration (REQ-046 follow-up)."""

    def __init__(
        self,
        repo: ArangoSystemSettingsRepository,
        encryption: EncryptionEngine,
    ) -> None:
        self._repo = repo
        self._encryption = encryption

    # ── Read ──────────────────────────────────────────────────────────

    def _stored(self) -> WeatherProviderSettings:
        settings = self._repo.get()
        return settings.weather_providers if settings else WeatherProviderSettings()

    def get_effective_weather_settings(self) -> EffectiveWeatherSettings:
        """Return effective provider settings: DB override on top of env.

        Decrypts the global OpenWeatherMap key (internal use only). A malformed
        ciphertext degrades to ``None`` (logged) rather than crashing the fetch.
        """
        wp = self._stored()

        def _enabled(db_val: bool | None, env_val: bool) -> bool:
            return db_val if db_val is not None else env_val

        def _url(db_val: str | None, env_val: str) -> str:
            return db_val if db_val else env_val

        providers = {
            "open-meteo": EffectiveWeatherProvider(
                enabled=_enabled(wp.open_meteo_enabled, env_settings.open_meteo_enabled),
                base_url=_url(wp.open_meteo_base_url, env_settings.open_meteo_base_url),
            ),
            "dwd": EffectiveWeatherProvider(
                enabled=_enabled(wp.dwd_enabled, env_settings.dwd_enabled),
                base_url=_url(wp.dwd_base_url, env_settings.dwd_base_url),
            ),
            "openweathermap": EffectiveWeatherProvider(
                enabled=_enabled(wp.openweathermap_enabled, env_settings.openweathermap_enabled),
                base_url=_url(wp.openweathermap_base_url, env_settings.openweathermap_base_url),
            ),
        }

        global_key: str | None = None
        if wp.openweathermap_global_api_key_encrypted:
            try:
                global_key = self._encryption.decrypt(wp.openweathermap_global_api_key_encrypted)
            except Exception as exc:  # noqa: BLE001 — a bad ciphertext must not abort a fetch
                logger.warning("weather_global_key_decrypt_failed", error=str(exc))
                global_key = None

        return EffectiveWeatherSettings(
            providers=providers,
            openweathermap_global_api_key=global_key,
            fetch_timeout_s=(
                wp.fetch_timeout_s if wp.fetch_timeout_s is not None else env_settings.weather_fetch_timeout_s
            ),
            default_public_source=(wp.default_public_source or env_settings.weather_default_public_source),
        )

    def has_global_openweathermap_key(self) -> bool:
        """Whether a global OWM fallback key is stored (never the value)."""
        return bool(self._stored().openweathermap_global_api_key_encrypted)

    # ── Write ─────────────────────────────────────────────────────────

    def update_weather_settings(
        self,
        *,
        open_meteo_enabled: bool | None = None,
        open_meteo_base_url: str | None = None,
        dwd_enabled: bool | None = None,
        dwd_base_url: str | None = None,
        openweathermap_enabled: bool | None = None,
        openweathermap_base_url: str | None = None,
        openweathermap_global_api_key: str | None = None,
        fetch_timeout_s: int | None = None,
        default_public_source: str | None = None,
    ) -> SystemSettings:
        """Persist the provider overrides (DB override, env fallback preserved).

        Raises ``ValueError`` for an unknown ``default_public_source`` so the API
        layer can map it to a 422 rather than persist an unusable default.
        """
        if default_public_source is not None and default_public_source not in WEATHER_PROVIDER_NAMES:
            raise ValueError(
                f"Unknown weather source '{default_public_source}'. Allowed: {', '.join(WEATHER_PROVIDER_NAMES)}.",
            )

        stored = self._repo.get() or SystemSettings()
        wp = stored.weather_providers

        if open_meteo_enabled is not None:
            wp.open_meteo_enabled = open_meteo_enabled
        if open_meteo_base_url is not None:
            wp.open_meteo_base_url = open_meteo_base_url
        if dwd_enabled is not None:
            wp.dwd_enabled = dwd_enabled
        if dwd_base_url is not None:
            wp.dwd_base_url = dwd_base_url
        if openweathermap_enabled is not None:
            wp.openweathermap_enabled = openweathermap_enabled
        if openweathermap_base_url is not None:
            wp.openweathermap_base_url = openweathermap_base_url
        if fetch_timeout_s is not None:
            wp.fetch_timeout_s = fetch_timeout_s
        if default_public_source is not None:
            wp.default_public_source = default_public_source

        # A new plaintext key is encrypted; empty / masked means "unchanged".
        if openweathermap_global_api_key and openweathermap_global_api_key != _MASKED_SECRET:
            wp.openweathermap_global_api_key_encrypted = self._encryption.encrypt(openweathermap_global_api_key)

        stored.weather_providers = wp
        return self._repo.upsert(stored)

    def delete_global_openweathermap_key(self) -> bool:
        """Clear the stored global OWM key so no instance-wide fallback applies."""
        stored = self._repo.get()
        if stored is None:
            return False
        stored.weather_providers.openweathermap_global_api_key_encrypted = None
        self._repo.upsert(stored)
        return True

    # ── Connection test (effective config) ────────────────────────────

    async def test_provider(self, source_name: str) -> WeatherProviderTestResult:
        """Probe a provider with its *effective* config (never a 500, no leak)."""
        if source_name not in WEATHER_PROVIDER_NAMES:
            return WeatherProviderTestResult(reachable=False, error=f"Unknown weather source '{source_name}'.")

        effective = self.get_effective_weather_settings()
        provider = effective.provider(source_name)
        if provider is None or not provider.enabled:
            return WeatherProviderTestResult(reachable=False, error=f"Provider '{source_name}' is disabled.")

        adapter_cls = WeatherAdapterRegistry.get(source_name)
        if adapter_cls is None:
            return WeatherProviderTestResult(reachable=False, error=f"Unknown weather source '{source_name}'.")

        timeout_s = float(effective.fetch_timeout_s)
        if source_name == "openweathermap":
            adapter = adapter_cls(
                api_key=effective.openweathermap_global_api_key,
                base_url=provider.base_url,
                timeout_s=timeout_s,
            )
        else:
            adapter = adapter_cls(base_url=provider.base_url, timeout_s=timeout_s)

        try:
            reachable = await adapter.health_check()
        except (httpx.HTTPError, httpx.TimeoutException) as exc:
            return WeatherProviderTestResult(reachable=False, error=str(exc))
        except Exception as exc:  # noqa: BLE001 — the test endpoint must never surface a 500
            logger.warning("weather_provider_test_failed", source=source_name, error=str(exc))
            return WeatherProviderTestResult(reachable=False, error=str(exc))

        if not reachable:
            return WeatherProviderTestResult(reachable=False, error="Source did not return any data.")

        try:
            records = await adapter.fetch_daily(latitude=_TEST_LAT, longitude=_TEST_LON)
            preview = records[:3]
        except (httpx.HTTPError, httpx.TimeoutException) as exc:
            return WeatherProviderTestResult(reachable=False, error=str(exc))
        except Exception as exc:  # noqa: BLE001 — preview failure must never surface a 500
            logger.warning("weather_provider_preview_failed", source=source_name, error=str(exc))
            return WeatherProviderTestResult(reachable=False, error=str(exc))

        return WeatherProviderTestResult(reachable=True, preview=preview)
