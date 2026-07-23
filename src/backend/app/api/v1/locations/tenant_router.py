from fastapi import APIRouter, Depends, Query

from app.api.mapping import to_response
from app.api.v1.locations.schemas import FrostWarningResponse, LocationCreate, LocationResponse
from app.api.v1.tanks.schemas import LiveStateResponse, SensorCreate, SensorResponse
from app.common.auth import get_current_tenant
from app.common.dependencies import get_sensor_service, get_site_service
from app.domain.models.sensor import Sensor
from app.domain.models.site import Location
from app.domain.models.tenant_context import TenantContext
from app.domain.services.sensor_service import SensorService
from app.domain.services.site_service import SiteService

router = APIRouter(prefix="/locations", tags=["locations"])


def _verify_location_tenant(key: str, ctx: TenantContext, service: SiteService) -> Location:
    """Get a location and verify it belongs to a site owned by the tenant."""
    loc = service.get_location(key)
    service.get_site(loc.site_key, tenant_key=ctx.tenant_key)
    return loc


@router.get("", response_model=list[LocationResponse])
def list_locations(
    site_key: str = Query(...),
    parent_location_key: str | None = Query(None),
    ctx: TenantContext = Depends(get_current_tenant),
    service: SiteService = Depends(get_site_service),
):
    service.get_site(site_key, tenant_key=ctx.tenant_key)
    if parent_location_key:
        items = service.list_location_children(parent_location_key)
    else:
        items = service.list_locations(site_key)
    return [to_response(loc, LocationResponse) for loc in items]


@router.get("/{key}", response_model=LocationResponse)
def get_location(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: SiteService = Depends(get_site_service),
):
    loc = _verify_location_tenant(key, ctx, service)
    return to_response(loc, LocationResponse)


@router.get("/{key}/children", response_model=list[LocationResponse])
def list_location_children(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: SiteService = Depends(get_site_service),
):
    _verify_location_tenant(key, ctx, service)
    items = service.list_location_children(key)
    return [to_response(loc, LocationResponse) for loc in items]


@router.post("", response_model=LocationResponse, status_code=201)
def create_location(
    body: LocationCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: SiteService = Depends(get_site_service),
):
    service.get_site(body.site_key, tenant_key=ctx.tenant_key)
    location = Location(**body.model_dump())
    created = service.create_location(location)
    return to_response(created, LocationResponse)


@router.put("/{key}", response_model=LocationResponse)
def update_location(
    key: str,
    body: LocationCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: SiteService = Depends(get_site_service),
):
    _verify_location_tenant(key, ctx, service)
    location = Location(**body.model_dump())
    service.get_site(location.site_key, tenant_key=ctx.tenant_key)
    updated = service.update_location(key, location)
    return to_response(updated, LocationResponse)


@router.delete("/{key}", status_code=204)
def delete_location(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: SiteService = Depends(get_site_service),
):
    _verify_location_tenant(key, ctx, service)
    service.delete_location(key)


# ── Sensors ──────────────────────────────────────────────────────────


@router.get("/{key}/sensors", response_model=list[SensorResponse])
def get_location_sensors(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: SiteService = Depends(get_site_service),
    sensor_service: SensorService = Depends(get_sensor_service),
):
    _verify_location_tenant(key, ctx, service)
    sensors = sensor_service.get_sensors_for_location(key)
    return [to_response(s, SensorResponse) for s in sensors]


@router.post("/{key}/sensors", response_model=SensorResponse, status_code=201)
def create_location_sensor(
    key: str,
    body: SensorCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: SiteService = Depends(get_site_service),
    sensor_service: SensorService = Depends(get_sensor_service),
):
    _verify_location_tenant(key, ctx, service)
    sensor = Sensor(
        name=body.name,
        metric_type=body.metric_type,
        ha_entity_id=body.ha_entity_id,
        mqtt_topic=body.mqtt_topic,
        location_key=key,
    )
    created = sensor_service.create_sensor(sensor)
    return to_response(created, SensorResponse)


@router.get("/{key}/sensors/live", response_model=LiveStateResponse)
def get_location_sensors_live(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: SiteService = Depends(get_site_service),
    sensor_service: SensorService = Depends(get_sensor_service),
):
    _verify_location_tenant(key, ctx, service)
    sensors = sensor_service.get_sensors_for_location(key)
    result = sensor_service.get_live_state_for_sensors(sensors)
    return LiveStateResponse(**result)


@router.get("/{key}/frost-warning", response_model=FrostWarningResponse)
def get_location_frost_warning(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: SiteService = Depends(get_site_service),
    sensor_service: SensorService = Depends(get_sensor_service),
):
    """Reactive frost-warning state for a location (Home Assistant read path).

    Backs ``binary_sensor.kp_{location}_frost_warning``: the HA coordinator
    learns which locations to surface from ``/ha-publish/enabled-keys/location``
    (opt-in) and polls this route per location. The reactive ``frost_warning`` is
    derived from the location's latest ambient temperature; it is ``null`` when no
    temperature reading is available.

    The proactive forecast early-warning is served once per site — not per
    location — via ``GET /sites/{site_key}/weather-forecast`` (Issue #409, F1), so
    a site with N locations no longer triggers N identical forecast reads on this
    hot path.
    """
    _verify_location_tenant(key, ctx, service)
    result = sensor_service.get_location_frost_warning(key)
    return FrostWarningResponse(**result)
