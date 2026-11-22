"""REQ-046 follow-up — central admin for the public weather providers.

Platform-admin-gated CRUD over the instance-wide public weather-service config
(Open-Meteo, DWD, OpenWeatherMap), backed by the ``SYSTEM_SETTINGS`` singleton
via :class:`WeatherSettingsService`. Mirrors the storage / HA admin endpoints:

* ``GET`` returns the effective config **masked** — per-provider ``enabled`` +
  ``base_url`` plus attribution, and only the *presence* flag of the global
  OpenWeatherMap fallback key (never the value / ciphertext).
* ``PUT`` persists the overrides; a new global key is Fernet-encrypted, an empty
  / masked value keeps the stored ciphertext.
* ``POST /{source_name}/test`` probes a provider with its *effective* config
  (base URL, timeout, and the global key for OpenWeatherMap) and maps any error
  to ``reachable=False`` instead of a 500.
* ``POST /fetch`` queues a manual weather fetch over all sites (202); refused with
  409 while weather is switched off or a fetch runs, 429 + ``Retry-After`` within 10
  minutes after the previous manual fetch, 503 when lock or broker are unreachable
  (REQ-046 §3.6a, #2934).
* ``GET /fetch-status`` reports the newest run, the newest successful run and the
  next scheduled run.

Gating: ``require_platform_admin`` is light-mode-aware — in light mode (REQ-027)
there is no platform tenant and the sole anonymous system user is treated as the
operator/admin, so the same dependency works in BOTH modes and the router is
registered once for both.
"""

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, Path

from app.api.v1.admin.weather_providers.schemas import (
    WeatherFetchStatusResponse,
    WeatherFetchTriggerResponse,
    WeatherProviderInfo,
    WeatherProvidersResponse,
    WeatherProvidersUpdate,
    WeatherProviderTestResponse,
)
from app.common.auth import require_platform_admin
from app.common.dependencies import get_weather_fetch_service, get_weather_settings_service
from app.common.enums import WeatherFetchTrigger
from app.common.exceptions import ValidationError, WeatherFetchUnavailableError
from app.common.log_privacy import loggable_error
from app.common.openapi_responses import AUTH_RESPONSES
from app.common.url_safety import validate_server_side_url
from app.data_access.external.weather_attributions import WEATHER_ATTRIBUTIONS
from app.domain.models.user import User
from app.domain.services.weather_fetch_service import WeatherFetchService
from app.domain.services.weather_settings_service import (
    WEATHER_PROVIDER_NAMES,
    WeatherSettingsService,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/admin/weather-providers", tags=["admin-weather"], responses=AUTH_RESPONSES)


def _build_response(service: WeatherSettingsService) -> WeatherProvidersResponse:
    effective = service.get_effective_weather_settings()
    providers = [
        WeatherProviderInfo(
            source_name=source_name,
            enabled=effective.providers[source_name].enabled,
            base_url=effective.providers[source_name].base_url,
            attribution=WEATHER_ATTRIBUTIONS.get(source_name, ""),
        )
        for source_name in WEATHER_PROVIDER_NAMES
    ]
    return WeatherProvidersResponse(
        providers=providers,
        openweathermap_global_api_key_set=service.has_global_openweathermap_key(),
        fetch_timeout_s=effective.fetch_timeout_s,
        fetch_interval_hours=effective.fetch_interval_hours,
        default_public_source=effective.default_public_source,
    )


@router.get("", response_model=WeatherProvidersResponse)
def get_weather_providers(
    _user: User = Depends(require_platform_admin),
    service: WeatherSettingsService = Depends(get_weather_settings_service),
):
    """Return the masked effective weather-provider config (no key/ciphertext)."""
    return _build_response(service)


@router.put("", response_model=WeatherProvidersResponse)
def update_weather_providers(
    body: WeatherProvidersUpdate,
    _user: User = Depends(require_platform_admin),
    service: WeatherSettingsService = Depends(get_weather_settings_service),
):
    """Persist the central weather-provider overrides (DB override, env fallback)."""
    # SEC-W1: an operator-set base_url is fetched server-side (fetch + test path),
    # so validate it against SSRF (scheme allowlist + private/loopback/metadata
    # rejection) before persisting. An empty string clears the override → env
    # default, so only non-empty overrides are checked. Mirrors the HA/storage
    # admin URL guards (admin/settings/router.py).
    for field_name, url in (
        ("open_meteo_base_url", body.open_meteo_base_url),
        ("dwd_base_url", body.dwd_base_url),
        ("openweathermap_base_url", body.openweathermap_base_url),
    ):
        if url:
            validate_server_side_url(url, field=field_name)
    try:
        service.update_weather_settings(
            open_meteo_enabled=body.open_meteo_enabled,
            open_meteo_base_url=body.open_meteo_base_url,
            dwd_enabled=body.dwd_enabled,
            dwd_base_url=body.dwd_base_url,
            openweathermap_enabled=body.openweathermap_enabled,
            openweathermap_base_url=body.openweathermap_base_url,
            openweathermap_global_api_key=body.openweathermap_global_api_key,
            fetch_timeout_s=body.fetch_timeout_s,
            fetch_interval_hours=body.fetch_interval_hours,
            default_public_source=body.default_public_source,
        )
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    return _build_response(service)


@router.post(
    "/fetch",
    response_model=WeatherFetchTriggerResponse,
    status_code=202,
    responses={
        409: {"description": "A weather fetch is running, or weather is switched off (WEATHER_FETCH_DISABLED)."},
        429: {"description": "Cooldown after the previous manual fetch; see the Retry-After header."},
        503: {"description": "The fetch lock cannot be checked or the task broker is unreachable."},
    },
)
def trigger_weather_fetch(
    _user: User = Depends(require_platform_admin),
    service: WeatherFetchService = Depends(get_weather_fetch_service),
) -> WeatherFetchTriggerResponse:
    """Queue a manual weather fetch over all sites; the result appears in ``/fetch-status``."""
    from app.tasks.weather_tasks import fetch_weather_forecasts

    service.reserve_manual_fetch()
    try:
        task = fetch_weather_forecasts.delay(trigger=WeatherFetchTrigger.MANUAL.value)
    except Exception as exc:  # noqa: BLE001 — any broker failure means "not queued"
        # Not queued: the cooldown must not block the admin's next attempt, and an
        # unreachable broker is a 503, not the generic 500 (security review N1).
        service.cancel_manual_fetch()
        logger.warning("weather_fetch_dispatch_failed", error=loggable_error(exc))
        raise WeatherFetchUnavailableError from exc
    return WeatherFetchTriggerResponse(task_id=getattr(task, "id", None))


@router.get("/fetch-status", response_model=WeatherFetchStatusResponse)
def get_weather_fetch_status(
    _user: User = Depends(require_platform_admin),
    service: WeatherFetchService = Depends(get_weather_fetch_service),
) -> WeatherFetchStatusResponse:
    """Newest run, newest successful run and the next scheduled fetch."""
    overview = service.get_overview()
    return WeatherFetchStatusResponse(**overview.model_dump())


@router.post("/{source_name}/test", response_model=WeatherProviderTestResponse)
async def test_weather_provider(
    source_name: Annotated[str, Path(description="Weather provider identifier (open_meteo, dwd or openweathermap).")],
    _user: User = Depends(require_platform_admin),
    service: WeatherSettingsService = Depends(get_weather_settings_service),
):
    """Probe a provider with its effective config; errors → ``reachable=False``."""
    result = await service.test_provider(source_name)
    return WeatherProviderTestResponse(
        reachable=result.reachable,
        preview=result.preview,
        error=result.error,
    )
