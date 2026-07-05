"""REQ-046 §4.3 — tenant-scoped weather-source endpoints.

Mounted under ``/t/{tenant_slug}`` by the tenant-scoped parent router, so the
paths declared here are already tenant-scoped (no ``/t`` prefix). Reads use
``get_current_tenant``; writes require at least the ``grower`` role
(``require_tenant_role``). The router stays thin — all logic lives in
:class:`WeatherSourceService`.
"""

from fastapi import APIRouter, Depends

from app.api.v1.tenant_scoped.weather.schemas import (
    AvailableSourceItem,
    AvailableSourcesResponse,
    HaEntityItem,
    HaSensorMappingResponse,
    WeatherSourceConfigRequest,
    WeatherSourceConfigResponse,
    WeatherSourceEntryRequest,
    WeatherSourceEntryResponse,
    WeatherSourceHaConfigResponse,
    WeatherSourcePublicConfigResponse,
    WeatherTestPreviewItem,
    WeatherTestResponse,
)
from app.common.auth import get_current_tenant, require_tenant_role
from app.common.dependencies import get_weather_source_service
from app.common.enums import TenantRole
from app.domain.models.tenant_context import TenantContext
from app.domain.models.weather import (
    WeatherForecast,
    WeatherSourceConfig,
    WeatherSourceEntry,
    WeatherSourceHaConfig,
    WeatherSourcePublicConfig,
)
from app.domain.services.weather_source_service import (
    AvailableWeatherSources,
    WeatherSourceService,
    WeatherTestResult,
)

router = APIRouter(tags=["weather"])


# ── Response mapping (masking happens here — no secret ever leaves) ────────


def _entry_response(entry: WeatherSourceEntry) -> WeatherSourceEntryResponse:
    public_config = None
    ha_config = None
    if isinstance(entry.config, WeatherSourcePublicConfig):
        public_config = WeatherSourcePublicConfigResponse(
            api_key_set=bool(entry.config.api_key_ref),
            units_hint=entry.config.units_hint,
        )
    elif isinstance(entry.config, WeatherSourceHaConfig):
        mapping = None
        if entry.config.sensor_mapping is not None:
            mapping = HaSensorMappingResponse(**entry.config.sensor_mapping.model_dump())
        ha_config = WeatherSourceHaConfigResponse(
            mode=entry.config.mode,
            weather_entity_id=entry.config.weather_entity_id,
            sensor_mapping=mapping,
        )
    return WeatherSourceEntryResponse(
        source_name=entry.source_name,
        kind=entry.kind,
        enabled=entry.enabled,
        public_config=public_config,
        ha_config=ha_config,
    )


def _config_response(site_key: str, config: WeatherSourceConfig | None) -> WeatherSourceConfigResponse:
    if config is None:
        return WeatherSourceConfigResponse(site_key=site_key, enabled=True, sources=[])
    return WeatherSourceConfigResponse(
        site_key=config.site_key,
        enabled=config.enabled,
        sources=[_entry_response(entry) for entry in config.sources],
        updated_at=config.updated_at,
        updated_by=config.updated_by,
    )


def _available_response(result: AvailableWeatherSources) -> AvailableSourcesResponse:
    return AvailableSourcesResponse(
        sources=[
            AvailableSourceItem(source_name=s.source_name, kind=s.kind, requires_api_key=s.requires_api_key)
            for s in result.sources
        ],
        ha_token_set=result.ha_token_set,
    )


def _preview_item(record: WeatherForecast) -> WeatherTestPreviewItem:
    return WeatherTestPreviewItem(
        forecast_date=record.forecast_date,
        temp_min_c=record.temp_min_c,
        temp_max_c=record.temp_max_c,
        precipitation_mm=record.precipitation_mm,
        wind_speed_kmh=record.wind_speed_kmh,
        humidity_percent=record.humidity_percent,
        source=record.source,
        data_kind=record.data_kind,
        is_current_conditions=record.is_current_conditions,
    )


def _test_response(result: WeatherTestResult) -> WeatherTestResponse:
    return WeatherTestResponse(
        reachable=result.reachable,
        preview=[_preview_item(record) for record in result.preview],
        error=result.error,
    )


# ── Endpoints ──────────────────────────────────────────────────────────────


@router.get("/sites/{site_key}/weather-source", response_model=WeatherSourceConfigResponse)
def get_weather_source(
    site_key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: WeatherSourceService = Depends(get_weather_source_service),
):
    """Read the site's weather-source configuration (masked, AC-8)."""
    config = service.get_config(site_key, ctx.tenant_key)
    return _config_response(site_key, config)


@router.put("/sites/{site_key}/weather-source", response_model=WeatherSourceConfigResponse)
def put_weather_source(
    site_key: str,
    body: WeatherSourceConfigRequest,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: WeatherSourceService = Depends(get_weather_source_service),
):
    """Store the site's weather-source configuration (encrypts new OWM keys)."""
    saved = service.save_config(site_key, ctx.tenant_key, ctx.user_key, body)
    return _config_response(site_key, saved)


@router.get("/weather-sources/available", response_model=AvailableSourcesResponse)
def list_available_sources(
    ctx: TenantContext = Depends(get_current_tenant),
    service: WeatherSourceService = Depends(get_weather_source_service),
):
    """List selectable public sources plus the HA option and token status."""
    return _available_response(service.available_sources(ctx.tenant_key))


@router.post("/sites/{site_key}/weather-sources/test", response_model=WeatherTestResponse)
async def test_weather_source(
    site_key: str,
    body: WeatherSourceEntryRequest,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: WeatherSourceService = Depends(get_weather_source_service),
):
    """Test an unsaved source configuration (reachability + preview, AC-7)."""
    result = await service.test_source(site_key, ctx.tenant_key, body)
    return _test_response(result)


@router.get("/ha/weather-entities", response_model=list[HaEntityItem])
def list_ha_weather_entities(
    ctx: TenantContext = Depends(get_current_tenant),
    service: WeatherSourceService = Depends(get_weather_source_service),
):
    """List HA ``weather.*`` entities for mode A (empty when HA is unavailable)."""
    return [HaEntityItem(**item) for item in service.list_ha_weather_entities()]


@router.get("/ha/sensor-entities", response_model=list[HaEntityItem])
def list_ha_sensor_entities(
    ctx: TenantContext = Depends(get_current_tenant),
    service: WeatherSourceService = Depends(get_weather_source_service),
):
    """List HA ``sensor.*`` entities for mode B (empty when HA is unavailable)."""
    return [HaEntityItem(**item) for item in service.list_ha_sensor_entities()]
