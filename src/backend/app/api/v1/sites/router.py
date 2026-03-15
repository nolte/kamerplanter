from fastapi import APIRouter, Depends, Query

from app.api.v1.locations.schemas import LocationTreeNode
from app.api.v1.sites.schemas import SiteCreate, SiteResponse, WaterSourceWarningSchema
from app.api.v1.tanks.schemas import LiveStateResponse, SensorCreate, SensorResponse
from app.common.dependencies import get_sensor_service, get_site_service
from app.domain.models.sensor import Sensor
from app.domain.models.site import Location, Site
from app.domain.services.sensor_service import SensorService
from app.domain.services.site_service import SiteService

router = APIRouter(prefix="/sites", tags=["sites"])


def _site_response(site: Site, service: SiteService) -> SiteResponse:
    warnings = service.get_water_warnings(site)
    return SiteResponse(
        key=site.key or "",
        **site.model_dump(exclude={"key"}),
        water_config_warnings=[
            WaterSourceWarningSchema(code=w.code, message=w.message, severity=w.severity)
            for w in warnings
        ],
    )


@router.get("", response_model=list[SiteResponse])
def list_sites(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: SiteService = Depends(get_site_service),
):
    items, total = service.list_sites(offset, limit)
    return [_site_response(s, service) for s in items]

@router.get("/{key}", response_model=SiteResponse)
def get_site(key: str, service: SiteService = Depends(get_site_service)):
    s = service.get_site(key)
    return _site_response(s, service)

@router.post("", response_model=SiteResponse, status_code=201)
def create_site(body: SiteCreate, service: SiteService = Depends(get_site_service)):
    site = Site(**body.model_dump())
    created = service.create_site(site)
    return _site_response(created, service)

@router.put("/{key}", response_model=SiteResponse)
def update_site(key: str, body: SiteCreate, service: SiteService = Depends(get_site_service)):
    site = Site(**body.model_dump())
    updated = service.update_site(key, site)
    return _site_response(updated, service)

@router.get("/{key}/location-tree", response_model=list[LocationTreeNode])
def get_location_tree(key: str, service: SiteService = Depends(get_site_service)):
    all_locations = service.get_location_tree(key)
    slots_by_location: dict[str, int] = {}
    for loc in all_locations:
        loc_key = loc.key or ""
        slots = service.list_slots(loc_key)
        slots_by_location[loc_key] = len(slots)
    return _build_tree(all_locations, slots_by_location)


def _build_tree(
    locations: list[Location],
    slots_by_location: dict[str, int],
) -> list[LocationTreeNode]:
    nodes: dict[str, LocationTreeNode] = {}
    for loc in locations:
        loc_key = loc.key or ""
        nodes[loc_key] = LocationTreeNode(
            key=loc_key,
            name=loc.name,
            location_type_key=loc.location_type_key,
            depth=loc.depth,
            parent_location_key=loc.parent_location_key,
            slot_count=slots_by_location.get(loc_key, 0),
        )
    roots: list[LocationTreeNode] = []
    for loc in locations:
        loc_key = loc.key or ""
        node = nodes[loc_key]
        if loc.parent_location_key and loc.parent_location_key in nodes:
            nodes[loc.parent_location_key].children.append(node)
        else:
            roots.append(node)
    return roots


@router.delete("/{key}", status_code=204)
def delete_site(key: str, service: SiteService = Depends(get_site_service)):
    service.delete_site(key)


# ── Sensors ──────────────────────────────────────────────────────────


@router.get("/{key}/sensors", response_model=list[SensorResponse])
def get_site_sensors(
    key: str,
    sensor_service: SensorService = Depends(get_sensor_service),
):
    sensors = sensor_service.get_sensors_for_site(key)
    return [
        SensorResponse(key=s.key or "", **s.model_dump(exclude={"key"}))
        for s in sensors
    ]


@router.post("/{key}/sensors", response_model=SensorResponse, status_code=201)
def create_site_sensor(
    key: str,
    body: SensorCreate,
    sensor_service: SensorService = Depends(get_sensor_service),
):
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
    sensor_service: SensorService = Depends(get_sensor_service),
):
    sensors = sensor_service.get_sensors_for_site(key)
    result = sensor_service.get_live_state_for_sensors(sensors)
    return LiveStateResponse(**result)
