from fastapi import APIRouter, Depends, Query

from app.api.v1.locations.schemas import LocationTreeNode
from app.api.v1.sites.router import _build_tree, _site_response
from app.api.v1.sites.schemas import SiteCreate, SiteResponse
from app.api.v1.tanks.schemas import LiveStateResponse, SensorCreate, SensorResponse
from app.common.auth import get_current_tenant
from app.common.dependencies import get_sensor_service, get_site_service
from app.domain.models.sensor import Sensor
from app.domain.models.site import Site
from app.domain.models.tenant_context import TenantContext
from app.domain.services.sensor_service import SensorService
from app.domain.services.site_service import SiteService

router = APIRouter(prefix="/sites", tags=["sites"])


@router.get("", response_model=list[SiteResponse])
def list_sites(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: TenantContext = Depends(get_current_tenant),
    service: SiteService = Depends(get_site_service),
):
    items, _total = service.list_sites(offset, limit, tenant_key=ctx.tenant_key)
    return [_site_response(s, service) for s in items]


@router.get("/{key}", response_model=SiteResponse)
def get_site(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: SiteService = Depends(get_site_service),
):
    s = service.get_site(key, tenant_key=ctx.tenant_key)
    return _site_response(s, service)


@router.post("", response_model=SiteResponse, status_code=201)
def create_site(
    body: SiteCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: SiteService = Depends(get_site_service),
):
    site = Site(**body.model_dump(), tenant_key=ctx.tenant_key)
    created = service.create_site(site)
    return _site_response(created, service)


@router.put("/{key}", response_model=SiteResponse)
def update_site(
    key: str,
    body: SiteCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: SiteService = Depends(get_site_service),
):
    service.get_site(key, tenant_key=ctx.tenant_key)
    site = Site(**body.model_dump(), tenant_key=ctx.tenant_key)
    updated = service.update_site(key, site)
    return _site_response(updated, service)


@router.delete("/{key}", status_code=204)
def delete_site(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: SiteService = Depends(get_site_service),
):
    service.get_site(key, tenant_key=ctx.tenant_key)
    service.delete_site(key)


@router.get("/{key}/location-tree", response_model=list[LocationTreeNode])
def get_location_tree(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: SiteService = Depends(get_site_service),
):
    service.get_site(key, tenant_key=ctx.tenant_key)
    all_locations = service.get_location_tree(key)
    slots_by_location: dict[str, int] = {}
    for loc in all_locations:
        loc_key = loc.key or ""
        slots = service.list_slots(loc_key)
        slots_by_location[loc_key] = len(slots)
    return _build_tree(all_locations, slots_by_location)


@router.get("/{key}/sensors", response_model=list[SensorResponse])
def get_site_sensors(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    site_service: SiteService = Depends(get_site_service),
    sensor_service: SensorService = Depends(get_sensor_service),
):
    site_service.get_site(key, tenant_key=ctx.tenant_key)
    sensors = sensor_service.get_sensors_for_site(key)
    return [SensorResponse(key=s.key or "", **s.model_dump(exclude={"key"})) for s in sensors]


@router.post("/{key}/sensors", response_model=SensorResponse, status_code=201)
def create_site_sensor(
    key: str,
    body: SensorCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    site_service: SiteService = Depends(get_site_service),
    sensor_service: SensorService = Depends(get_sensor_service),
):
    site_service.get_site(key, tenant_key=ctx.tenant_key)
    sensor = Sensor(
        name=body.name,
        metric_type=body.metric_type,
        ha_entity_id=body.ha_entity_id,
        mqtt_topic=body.mqtt_topic,
        site_key=key,
    )
    created = sensor_service.create_sensor(sensor)
    return SensorResponse(key=created.key or "", **created.model_dump(exclude={"key"}))


@router.get("/{key}/sensors/live", response_model=LiveStateResponse)
def get_site_sensors_live(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    site_service: SiteService = Depends(get_site_service),
    sensor_service: SensorService = Depends(get_sensor_service),
):
    site_service.get_site(key, tenant_key=ctx.tenant_key)
    sensors = sensor_service.get_sensors_for_site(key)
    result = sensor_service.get_live_state_for_sensors(sensors)
    return LiveStateResponse(**result)
