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

from app.config.settings import settings
from app.domain.interfaces.weather_adapter import WeatherAdapter
from app.domain.models.weather import (
    WeatherForecast,
    WeatherSourceConfig,
    WeatherSourceEntry,
    WeatherSourcePublicConfig,
)
from app.domain.services.weather_adapter_registry import WeatherAdapterRegistry

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
    ) -> None:
        self._encryption = encryption
        self._ha_client_factory = ha_client_factory

    def _build(self, entry: WeatherSourceEntry) -> WeatherAdapter | None:
        adapter_cls = WeatherAdapterRegistry.get(entry.source_name)
        if adapter_cls is None:
            logger.warning("weather_source_unknown", source=entry.source_name)
            return None

        if entry.source_name in _KEYLESS_PUBLIC:
            return adapter_cls()

        if entry.source_name == "openweathermap":
            api_key: str | None = None
            if isinstance(entry.config, WeatherSourcePublicConfig) and entry.config.api_key_ref:
                api_key = self._encryption.decrypt(entry.config.api_key_ref)
            return adapter_cls(api_key=api_key)

        if entry.source_name == "ha_weather":
            ha_client = self._ha_client_factory()
            if ha_client is None:
                logger.info("weather_source_ha_unavailable", detail="no HA client — skipping ha_weather")
                return None
            return adapter_cls(ha_client)

        # Any other registered public adapter (e.g. REQ-041 nasa-power) with a
        # zero-argument constructor.
        return adapter_cls()

    def _default_entries(self) -> list[WeatherSourceEntry]:
        source_name = settings.weather_default_public_source
        return [WeatherSourceEntry(source_name=source_name, kind="public", enabled=True, config=None)]

    async def resolve_daily(self, site: Site, cfg: WeatherSourceConfig | None) -> list[WeatherForecast]:
        if site.gps_coordinates is None:
            return []
        latitude, longitude = site.gps_coordinates

        entries = [entry for entry in cfg.sources if entry.enabled] if cfg is not None else []
        if not entries:
            entries = self._default_entries()

        for entry in entries:
            adapter = self._build(entry)
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
