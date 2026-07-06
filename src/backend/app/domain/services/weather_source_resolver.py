"""REQ-046 §3.5 — ``WeatherSourceResolver`` (public-vs-HA fallback chain).

Walks a site's prioritised :class:`WeatherSourceConfig.sources` and returns the
first source that yields data, degrading to the next source on unavailability
(HA off, API 5xx/timeout, empty response). When a site has no configuration it
falls back to the default public source (``settings.weather_default_public_source``,
D5).

Adapter construction is centralised here (not in the registry, which only holds
classes) because different sources need different constructor dependencies:

* keyless public sources (open-meteo / dwd) -> ``AdapterCls()``
* openweathermap -> the Fernet **ciphertext** in ``config.api_key_ref`` is
  decrypted here (the resolver owns the :class:`EncryptionEngine`) and the
  **plaintext** key is passed to ``AdapterCls(api_key=...)``
* ha_weather -> built from the ``ha_client_factory``; when it returns ``None``
  (no HA token) the source is treated as unavailable and skipped.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import httpx
import structlog

from app.domain.interfaces.weather_adapter import WeatherAdapter
from app.domain.models.weather import (
    WeatherForecast,
    WeatherSourceConfig,
    WeatherSourceEntry,
    WeatherSourcePublicConfig,
)
from app.domain.services.weather_adapter_registry import WeatherAdapterRegistry
from app.domain.services.weather_settings_service import (
    EffectiveWeatherSettings,
    env_effective_weather_settings,
)

if TYPE_CHECKING:
    from app.data_access.external.ha_client import HomeAssistantClient
    from app.domain.engines.encryption_engine import EncryptionEngine
    from app.domain.models.site import Site

logger = structlog.get_logger(__name__)

_KEYLESS_PUBLIC = {"open-meteo", "dwd"}


class WeatherSourceResolver:
    """Resolves the effective daily weather for a site along its source priority."""

    def __init__(
        self,
        encryption: EncryptionEngine,
        ha_client_factory: Callable[[], HomeAssistantClient | None],
        weather_settings_provider: Callable[[], EffectiveWeatherSettings] | None = None,
    ) -> None:
        self._encryption = encryption
        self._ha_client_factory = ha_client_factory
        # DB-backed effective provider config (base URL, timeout, enable flags,
        # global OWM fallback key). When absent, falls back to the env defaults so
        # the resolver stays usable in isolation.
        self._weather_settings_provider = weather_settings_provider

    def _effective(self) -> EffectiveWeatherSettings:
        if self._weather_settings_provider is not None:
            return self._weather_settings_provider()
        return env_effective_weather_settings()

    def _build(self, entry: WeatherSourceEntry, effective: EffectiveWeatherSettings) -> WeatherAdapter | None:
        adapter_cls = WeatherAdapterRegistry.get(entry.source_name)
        if adapter_cls is None:
            logger.warning("weather_source_unknown", source=entry.source_name)
            return None

        provider = effective.provider(entry.source_name)
        # A centrally disabled public provider is skipped entirely.
        if provider is not None and not provider.enabled:
            logger.info("weather_source_provider_disabled", source=entry.source_name)
            return None

        if entry.source_name in _KEYLESS_PUBLIC:
            return self._build_public(adapter_cls, provider, effective)

        if entry.source_name == "openweathermap":
            api_key: str | None = None
            if isinstance(entry.config, WeatherSourcePublicConfig) and entry.config.api_key_ref:
                api_key = self._encryption.decrypt(entry.config.api_key_ref)
            # No per-site key -> fall back to the instance-wide global key.
            if not api_key:
                api_key = effective.openweathermap_global_api_key
            return self._build_public(adapter_cls, provider, effective, api_key=api_key)

        if entry.source_name == "ha_weather":
            ha_client = self._ha_client_factory()
            if ha_client is None:
                logger.info("weather_source_ha_unavailable", detail="no HA client — skipping ha_weather")
                return None
            return adapter_cls(ha_client)

        # Any other registered public adapter (e.g. REQ-041 nasa-power) with a
        # zero-argument constructor.
        return adapter_cls()

    @staticmethod
    def _build_public(
        adapter_cls: type[WeatherAdapter],
        provider: object | None,
        effective: EffectiveWeatherSettings,
        *,
        api_key: str | None = None,
    ) -> WeatherAdapter:
        """Build a public adapter with the effective base URL + timeout."""
        kwargs: dict[str, object] = {"timeout_s": float(effective.fetch_timeout_s)}
        if provider is not None:
            kwargs["base_url"] = provider.base_url  # type: ignore[attr-defined]
        if api_key is not None:
            kwargs["api_key"] = api_key
        return adapter_cls(**kwargs)  # type: ignore[arg-type]

    def _default_entries(self, effective: EffectiveWeatherSettings) -> list[WeatherSourceEntry]:
        source_name = effective.default_public_source
        return [WeatherSourceEntry(source_name=source_name, kind="public", enabled=True, config=None)]

    async def resolve_daily(self, site: Site, cfg: WeatherSourceConfig | None) -> list[WeatherForecast]:
        if site.gps_coordinates is None:
            return []
        latitude, longitude = site.gps_coordinates

        effective = self._effective()
        entries = [entry for entry in cfg.sources if entry.enabled] if cfg is not None else []
        if not entries:
            entries = self._default_entries(effective)

        for entry in entries:
            adapter = self._build(entry, effective)
            if adapter is None:
                continue
            try:
                forecasts = await adapter.fetch_daily(latitude=latitude, longitude=longitude, config=entry.config)
            except (httpx.HTTPError, httpx.TimeoutException) as exc:
                logger.warning("weather_source_fetch_failed", source=entry.source_name, error=str(exc))
                continue
            if forecasts:
                return forecasts
        return []
