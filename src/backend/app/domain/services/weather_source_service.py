"""REQ-046 §4.3 — ``WeatherSourceService`` (weather-source configuration logic).

Keeps the tenant-scoped router thin. Owns:

* **Site ownership** — every site-bound operation resolves the site through
  :func:`require_owned_site` and refuses a site that is missing *or* belongs to
  a different tenant with the same ``404`` (AC-11, #1871 B8), so a caller can
  never touch a foreign site's weather config and cannot tell a foreign site
  from an absent one.
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

from app.common.log_privacy import loggable_error
from app.config.settings import settings
from app.domain.models.weather import (
    HaSensorMapping,
    WeatherForecast,
    WeatherSourceConfig,
    WeatherSourceEntry,
    WeatherSourceHaConfig,
    WeatherSourcePublicConfig,
)
from app.domain.services.ha_entity_grant_service import (
    DenyAllHaEntityGate,
    HaEntityGate,
    only_granted,
    require_granted,
)
from app.domain.services.location_ownership import require_owned_site
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
    from app.domain.interfaces.climate_normal_repository import IClimateNormalRepository
    from app.domain.models.site import Site
    from app.domain.models.weather import ClimateNormal
    from app.domain.services.weather_settings_service import EffectiveWeatherSettings

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
        ha_client_factory: Callable[[], HomeAssistantClient | None],
        weather_settings_provider: Callable[[], EffectiveWeatherSettings] | None = None,
        climate_normal_repo: IClimateNormalRepository | None = None,
        ha_entity_grants: HaEntityGate | None = None,
    ) -> None:
        self._config_repo = weather_source_config_repo
        # MT-015 (#2112): the Home Assistant entities a weather source names must
        # be granted to the site's tenant. Absent, nothing is granted (fail-closed).
        self._ha_entity_gate: HaEntityGate = ha_entity_grants or DenyAllHaEntityGate()
        self._site_repo = site_repo
        self._encryption = encryption_engine
        self._ha_client_factory = ha_client_factory
        # DB-backed effective provider config; when absent, the enable flags fall
        # back to the raw env kill-switches (``settings.<p>_enabled``).
        self._weather_settings_provider = weather_settings_provider
        # REQ-041 — optional so existing constructions (tests) stay valid; the
        # climate-normal read endpoint wires it in via the dependency factory.
        self._climate_normal_repo = climate_normal_repo

    # ── Site ownership ────────────────────────────────────────────────

    def _load_owned_site(self, site_key: str, tenant_key: str) -> Site:
        """The tenant's site behind ``site_key``, or ``NotFoundError``.

        An unknown site and a site of another tenant raise the **same** error —
        status, code, message and details — after the same single read (REQ-046
        AC-11, operator decision #1871 B8 of 2026-10-03). The 403 this answered
        for a foreign site until then was an existence oracle for other tenants'
        site keys.
        """
        return require_owned_site(self._site_repo, site_key, tenant_key, "Site", site_key)

    def verify_site_owned(self, site_key: str, tenant_key: str) -> None:
        """Public ownership guard for read endpoints needing defense-in-depth.

        Raises :class:`NotFoundError` for an unknown and for a foreign site alike,
        exactly like the write-path check, so read routes can enforce site
        ownership at the API layer consistently with the sibling weather-source
        endpoints instead of relying solely on a service filter.
        """
        self._load_owned_site(site_key, tenant_key)

    # ── Read ──────────────────────────────────────────────────────────

    def get_config(self, site_key: str, tenant_key: str) -> WeatherSourceConfig | None:
        """Load the site's config (or ``None``). The returned model still holds
        the ciphertext in ``api_key_ref``; the router masks it in the response."""
        self._load_owned_site(site_key, tenant_key)
        return self._config_repo.get_by_site(site_key, tenant_key)

    def get_climate_normals(self, site_key: str, tenant_key: str) -> list[ClimateNormal]:
        """REQ-041 — the site's long-term climate normals (one per source).

        Enforces site ownership first (``404`` for unknown and foreign alike) so a
        caller can never read a foreign site's normals, then returns the
        tenant-scoped records. Returns ``[]`` when the collection has not been
        populated yet (fetch beat has not run for this site) — never a ``500``.
        """
        self._load_owned_site(site_key, tenant_key)
        if self._climate_normal_repo is None:
            return []
        return self._climate_normal_repo.get_by_site(site_key, tenant_key)

    # ── Write ─────────────────────────────────────────────────────────

    def save_config(
        self,
        site_key: str,
        tenant_key: str,
        user_key: str,
        request: WeatherSourceConfigRequest,
    ) -> WeatherSourceConfig:
        site = self._load_owned_site(site_key, tenant_key)
        for req_entry in request.sources:
            if req_entry.kind == "home_assistant":
                self._require_granted_ha_entities(tenant_key, req_entry.ha_config)
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

    def _require_granted_ha_entities(self, tenant_key: str, ha_request: WeatherSourceHaConfigRequest | None) -> None:
        """Refuse a Home Assistant weather configuration naming an ungranted entity (422)."""
        if ha_request is None:
            return
        references: dict[str, str | None] = {"weather_entity_id": ha_request.weather_entity_id}
        if ha_request.sensor_mapping is not None:
            for field, entity_id in ha_request.sensor_mapping.model_dump().items():
                references[f"sensor_mapping.{field}"] = entity_id
        require_granted(self._ha_entity_gate, tenant_key, references)

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
        # The constructor below is chosen by ``entry.kind``, the class by
        # ``entry.source_name``; nothing upstream ties the two together. A
        # mismatch (``dwd`` sent as ``home_assistant``) built an adapter with the
        # wrong arguments and raised TypeError outside the try below — a 500.
        # Found by the mypy ratchet's call-arg class (#2169).
        if adapter_cls.kind != entry.kind:
            return WeatherTestResult(
                reachable=False,
                error=f"Weather source '{entry.source_name}' is not a {entry.kind} source.",
            )

        config: object | None = None
        if entry.kind == "home_assistant":
            # An unsaved configuration reads Home Assistant just like a saved one,
            # so it is held to the same allowlist (MT-015, #2112).
            self._require_granted_ha_entities(tenant_key, entry.ha_config)
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
            logger.warning("weather_source_test_failed", source=entry.source_name, error=loggable_error(exc))
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
                logger.warning("weather_source_preview_failed", source=entry.source_name, error=loggable_error(exc))
                return WeatherTestResult(reachable=False, error=str(exc))
        return WeatherTestResult(reachable=True, preview=preview)

    # ── HA entity pickers ─────────────────────────────────────────────

    def list_ha_weather_entities(self, *, tenant_key: str) -> list[dict]:
        """The tenant's granted HA ``weather.*`` entities (mode A). Empty when HA is unavailable."""
        return only_granted(
            self._ha_entity_gate, tenant_key, self._ha_entities(lambda client: client.list_weather_entities())
        )

    def list_ha_sensor_entities(self, *, tenant_key: str) -> list[dict]:
        """The tenant's granted HA ``sensor.*`` entities (mode B). Empty when HA is unavailable."""
        return only_granted(
            self._ha_entity_gate, tenant_key, self._ha_entities(lambda client: client.list_sensor_entities())
        )

    def _ha_entities(self, reader: Callable[[HomeAssistantClient], list[dict]]) -> list[dict]:
        ha_client = self._ha_client_factory()
        if ha_client is None:
            return []
        try:
            return reader(ha_client)
        except (httpx.HTTPError, httpx.TimeoutException) as exc:
            logger.warning("ha_weather_entities_failed", error=loggable_error(exc))
            return []
