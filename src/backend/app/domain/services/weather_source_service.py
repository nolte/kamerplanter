"""REQ-046 §4.3 — ``WeatherSourceService`` (weather-source configuration logic).

Keeps the tenant-scoped router thin. Owns:

* **Site ownership** — every site-bound operation loads the site through the
  site repository and rejects a site that is missing (``404``) or belongs to a
  different tenant (``403``), so a caller can never touch a foreign site's
  weather config (AC-11).
* **Secret handling (D1, AC-8)** — a *new* plaintext OpenWeatherMap key is
  Fernet-encrypted via :class:`EncryptionEngine` and stored as ciphertext in
  ``WeatherSourcePublicConfig.api_key_ref``. An empty / masked key means
  "unchanged": the previously stored ciphertext is preserved, never wiped. The
  plaintext key is never persisted and never returned (the response schema only
  reports ``api_key_set``).
* **Denormalized view (§2.1)** — ``Site.weather_source_priority`` is rewritten
  from the enabled sources on every save.
* **Connection test (AC-7)** — builds an adapter directly from the *unsaved*
  request entry (OpenWeatherMap uses the plaintext key from the body, never the
  store) and reports reachability plus a small preview, mapping any adapter /
  HTTP error to ``reachable=False`` with a human-readable message instead of a
  ``500``. Nothing is persisted.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import httpx
import structlog
from pydantic import BaseModel, Field

from app.common.exceptions import ForbiddenError, NotFoundError
from app.config.settings import settings
from app.domain.models.weather import (
    HaSensorMapping,
    WeatherForecast,
    WeatherSourceConfig,
    WeatherSourceEntry,
    WeatherSourceHaConfig,
    WeatherSourcePublicConfig,
)
from app.domain.services.weather_adapter_registry import WeatherAdapterRegistry

if TYPE_CHECKING:
    from collections.abc import Callable

    from app.api.v1.tenant_scoped.weather.schemas import (
        WeatherSourceConfigRequest,
        WeatherSourceEntryRequest,
        WeatherSourceHaConfigRequest,
    )
    from app.data_access.arango.site_repository import ArangoSiteRepository
    from app.data_access.arango.weather_source_config_repository import ArangoWeatherSourceConfigRepository
    from app.data_access.external.ha_client import HomeAssistantClient
    from app.domain.engines.encryption_engine import EncryptionEngine
    from app.domain.models.site import Site
    from app.domain.services.weather_settings_service import EffectiveWeatherSettings
    from app.domain.services.weather_source_resolver import WeatherSourceResolver

logger = structlog.get_logger(__name__)

#: Placeholder the frontend renders / echoes for an already-stored secret; the
#: service treats it (and empty input) as "key unchanged".
_MASKED_SECRET = "••••"

#: Per-provider kill switches (§5). Sources not listed default to enabled (e.g. a
#: REQ-041 nasa-power adapter registering later).
_PROVIDER_ENABLED: dict[str, Callable[[], bool]] = {
    "open-meteo": lambda: settings.open_meteo_enabled,
    "dwd": lambda: settings.dwd_enabled,
    "openweathermap": lambda: settings.openweathermap_enabled,
}


class AvailableWeatherSource(BaseModel):
    """One selectable source for the "add source" UI."""

    source_name: str
    kind: str
    requires_api_key: bool = False


class AvailableWeatherSources(BaseModel):
    """Result of :meth:`WeatherSourceService.available_sources`."""

    sources: list[AvailableWeatherSource] = Field(default_factory=list)
    ha_token_set: bool = False


class WeatherTestResult(BaseModel):
    """Result of :meth:`WeatherSourceService.test_source` (AC-7)."""

    reachable: bool
    preview: list[WeatherForecast] = Field(default_factory=list)
    error: str | None = None


class WeatherSourceService:
    """Business logic for per-site weather-source configuration (REQ-046)."""

    def __init__(
        self,
        weather_source_config_repo: ArangoWeatherSourceConfigRepository,
        site_repo: ArangoSiteRepository,
        encryption_engine: EncryptionEngine,
        resolver: WeatherSourceResolver,
        ha_client_factory: Callable[[], HomeAssistantClient | None],
        weather_settings_provider: Callable[[], EffectiveWeatherSettings] | None = None,
    ) -> None:
        self._config_repo = weather_source_config_repo
        self._site_repo = site_repo
        self._encryption = encryption_engine
        # The resolver is injected for parity with the fetch pipeline; the test
        # endpoint deliberately builds adapters from the unsaved body instead of
        # decrypting stored config, so it is not used here yet.
        self._resolver = resolver
        self._ha_client_factory = ha_client_factory
        # DB-backed effective provider config; when absent, the enable flags fall
        # back to the raw env kill-switches (``settings.<p>_enabled``).
        self._weather_settings_provider = weather_settings_provider

    # ── Site ownership ────────────────────────────────────────────────

    def _load_owned_site(self, site_key: str, tenant_key: str) -> Site:
        site = self._site_repo.get_site_by_key(site_key)
        if site is None:
            raise NotFoundError("Site", site_key)
        if site.tenant_key != tenant_key:
            raise ForbiddenError("This site belongs to a different tenant.")
        return site

    def verify_site_owned(self, site_key: str, tenant_key: str) -> None:
        """Public ownership guard for read endpoints needing defense-in-depth.

        Raises :class:`NotFoundError` (unknown site) / :class:`ForbiddenError`
        (foreign site) exactly like the write-path check, so read routes can
        enforce site ownership at the API layer consistently with the sibling
        weather-source endpoints instead of relying solely on a service filter.
        """
        self._load_owned_site(site_key, tenant_key)

    # ── Read ──────────────────────────────────────────────────────────

    def get_config(self, site_key: str, tenant_key: str) -> WeatherSourceConfig | None:
        """Load the site's config (or ``None``). The returned model still holds
        the ciphertext in ``api_key_ref``; the router masks it in the response."""
        self._load_owned_site(site_key, tenant_key)
        return self._config_repo.get_by_site(site_key, tenant_key)

    # ── Write ─────────────────────────────────────────────────────────

    def save_config(
        self,
        site_key: str,
        tenant_key: str,
        user_key: str,
        request: WeatherSourceConfigRequest,
    ) -> WeatherSourceConfig:
        site = self._load_owned_site(site_key, tenant_key)
        existing = self._config_repo.get_by_site(site_key, tenant_key)
        existing_key_refs = self._existing_key_refs(existing)

        entries = [
            WeatherSourceEntry(
                source_name=req_entry.source_name,
                kind=req_entry.kind,
                enabled=req_entry.enabled,
                config=self._build_stored_config(req_entry, existing_key_refs),
            )
            for req_entry in request.sources
        ]

        config = WeatherSourceConfig(
            key=existing.key if existing else None,
            weather_source_config_id=(existing.weather_source_config_id if existing else ""),
            site_key=site_key,
            tenant_key=tenant_key,
            enabled=request.enabled,
            sources=entries,
            updated_at=datetime.now(tz=UTC),
            updated_by=user_key,
        )
        saved = self._config_repo.upsert(config)

        # Denormalized view for legacy consumers (§2.1).
        site.weather_source_priority = [entry.source_name for entry in entries if entry.enabled]
        if site.key:
            self._site_repo.update_site(site.key, site)
        return saved

    @staticmethod
    def _existing_key_refs(existing: WeatherSourceConfig | None) -> dict[str, str]:
        if existing is None:
            return {}
        refs: dict[str, str] = {}
        for entry in existing.sources:
            if isinstance(entry.config, WeatherSourcePublicConfig) and entry.config.api_key_ref:
                refs[entry.source_name] = entry.config.api_key_ref
        return refs

    def _build_stored_config(
        self,
        req_entry: WeatherSourceEntryRequest,
        existing_key_refs: dict[str, str],
    ) -> WeatherSourcePublicConfig | WeatherSourceHaConfig | None:
        if req_entry.kind == "home_assistant":
            return self._to_stored_ha_config(req_entry.ha_config)

        public = req_entry.public_config
        api_key_ref = self._resolve_api_key_ref(
            req_entry.source_name,
            public.api_key if public else None,
            existing_key_refs,
        )
        units_hint = public.units_hint if public else None
        if api_key_ref is None and units_hint is None:
            return None
        return WeatherSourcePublicConfig(api_key_ref=api_key_ref, units_hint=units_hint)

    def _resolve_api_key_ref(
        self,
        source_name: str,
        new_plaintext: str | None,
        existing_key_refs: dict[str, str],
    ) -> str | None:
        """Encrypt a newly typed key, else preserve the stored ciphertext."""
        if new_plaintext and new_plaintext != _MASKED_SECRET:
            return self._encryption.encrypt(new_plaintext)
        return existing_key_refs.get(source_name)

    @staticmethod
    def _to_stored_ha_config(
        ha_request: WeatherSourceHaConfigRequest | None,
    ) -> WeatherSourceHaConfig | None:
        if ha_request is None:
            return None
        mapping = None
        if ha_request.sensor_mapping is not None:
            mapping = HaSensorMapping(**ha_request.sensor_mapping.model_dump())
        return WeatherSourceHaConfig(
            mode=ha_request.mode,
            weather_entity_id=ha_request.weather_entity_id,
            sensor_mapping=mapping,
        )

    # ── Available sources ─────────────────────────────────────────────

    def available_sources(self, tenant_key: str) -> AvailableWeatherSources:
        effective = self._weather_settings_provider() if self._weather_settings_provider is not None else None
        sources: list[AvailableWeatherSource] = []
        for source_name in WeatherAdapterRegistry.public_sources():
            if not self._provider_enabled(source_name, effective):
                continue
            adapter_cls = WeatherAdapterRegistry.get(source_name)
            sources.append(
                AvailableWeatherSource(
                    source_name=source_name,
                    kind="public",
                    requires_api_key=bool(adapter_cls and adapter_cls.requires_api_key),
                )
            )

        ha_token_set = self._ha_client_factory() is not None
        if WeatherAdapterRegistry.get("ha_weather") is not None:
            sources.append(
                AvailableWeatherSource(source_name="ha_weather", kind="home_assistant", requires_api_key=False)
            )
        return AvailableWeatherSources(sources=sources, ha_token_set=ha_token_set)

    @staticmethod
    def _provider_enabled(source_name: str, effective: EffectiveWeatherSettings | None = None) -> bool:
        if effective is not None:
            provider = effective.provider(source_name)
            # Unknown providers (e.g. a future nasa-power) default to enabled.
            return provider.enabled if provider is not None else True
        check = _PROVIDER_ENABLED.get(source_name)
        return check() if check is not None else True

    # ── Connection test (unsaved) ─────────────────────────────────────

    async def test_source(
        self,
        site_key: str,
        tenant_key: str,
        entry: WeatherSourceEntryRequest,
    ) -> WeatherTestResult:
        site = self._load_owned_site(site_key, tenant_key)

        adapter_cls = WeatherAdapterRegistry.get(entry.source_name)
        if adapter_cls is None:
            return WeatherTestResult(reachable=False, error=f"Unknown weather source '{entry.source_name}'.")

        config: object | None = None
        if entry.kind == "home_assistant":
            ha_client = self._ha_client_factory()
            if ha_client is None:
                return WeatherTestResult(
                    reachable=False,
                    error="Home Assistant is not connected. Set an HA token before testing this source.",
                )
            adapter = adapter_cls(ha_client)
            config = self._to_stored_ha_config(entry.ha_config)
        elif entry.source_name == "openweathermap":
            # Plaintext key straight from the (unsaved) request body — never the store.
            plaintext_key = entry.public_config.api_key if entry.public_config else None
            adapter = adapter_cls(api_key=plaintext_key)
        else:
            adapter = adapter_cls()

        try:
            reachable = await adapter.health_check(config=config)
        except (httpx.HTTPError, httpx.TimeoutException) as exc:
            return WeatherTestResult(reachable=False, error=str(exc))
        except Exception as exc:  # noqa: BLE001 — the test endpoint must never surface a 500
            logger.warning("weather_source_test_failed", source=entry.source_name, error=str(exc))
            return WeatherTestResult(reachable=False, error=str(exc))

        if not reachable:
            return WeatherTestResult(reachable=False, error="Source did not return any data.")

        preview: list[WeatherForecast] = []
        if site.gps_coordinates is not None:
            latitude, longitude = site.gps_coordinates
            try:
                records = await adapter.fetch_daily(latitude=latitude, longitude=longitude, config=config)
                preview = records[:3]
            except (httpx.HTTPError, httpx.TimeoutException) as exc:
                return WeatherTestResult(reachable=False, error=str(exc))
            except Exception as exc:  # noqa: BLE001 — preview failure must never surface a 500
                logger.warning("weather_source_preview_failed", source=entry.source_name, error=str(exc))
                return WeatherTestResult(reachable=False, error=str(exc))
        return WeatherTestResult(reachable=True, preview=preview)

    # ── HA entity pickers ─────────────────────────────────────────────

    def list_ha_weather_entities(self) -> list[dict]:
        """HA ``weather.*`` entities (mode A). Empty list when HA is unavailable."""
        return self._ha_entities(lambda client: client.list_weather_entities())

    def list_ha_sensor_entities(self) -> list[dict]:
        """HA ``sensor.*`` entities (mode B). Empty list when HA is unavailable."""
        return self._ha_entities(lambda client: client.list_sensor_entities())

    def _ha_entities(self, reader: Callable[[HomeAssistantClient], list[dict]]) -> list[dict]:
        ha_client = self._ha_client_factory()
        if ha_client is None:
            return []
        try:
            return reader(ha_client)
        except (httpx.HTTPError, httpx.TimeoutException) as exc:
            logger.warning("ha_weather_entities_failed", error=str(exc))
            return []
