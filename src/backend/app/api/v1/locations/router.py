from fastapi import APIRouter, Depends, Query

from app.api.v1.locations.schemas import LocationCreate, LocationResponse
from app.api.v1.tanks.schemas import LiveStateResponse, SensorCreate, SensorResponse
from app.common.dependencies import get_sensor_service, get_site_service
from app.domain.models.sensor import Sensor
from app.domain.models.site import Location
from app.domain.services.sensor_service import SensorService
from app.domain.services.site_service import SiteService

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("", response_model=list[LocationResponse])
def list_locations(
    site_key: str = Query(...),
    parent_location_key: str | None = Query(None),
    service: SiteService = Depends(get_site_service),
):
    if parent_location_key:
        items = service.list_location_children(parent_location_key)
    else:
        items = service.list_locations(site_key)
    return [LocationResponse(key=loc.key or "", **loc.model_dump(exclude={"key"})) for loc in items]


@router.get("/{key}", response_model=LocationResponse)
def get_location(key: str, service: SiteService = Depends(get_site_service)):
    loc = service.get_location(key)
    return LocationResponse(key=loc.key or "", **loc.model_dump(exclude={"key"}))


@router.get("/{key}/children", response_model=list[LocationResponse])
def list_location_children(key: str, service: SiteService = Depends(get_site_service)):
    items = service.list_location_children(key)
    return [LocationResponse(key=loc.key or "", **loc.model_dump(exclude={"key"})) for loc in items]


@router.post("", response_model=LocationResponse, status_code=201)
def create_location(body: LocationCreate, service: SiteService = Depends(get_site_service)):
    location = Location(**body.model_dump())
    created = service.create_location(location)
    return LocationResponse(key=created.key or "", **created.model_dump(exclude={"key"}))


@router.put("/{key}", response_model=LocationResponse)
def update_location(key: str, body: LocationCreate, service: SiteService = Depends(get_site_service)):
    location = Location(**body.model_dump())
    updated = service.update_location(key, location)
    return LocationResponse(key=updated.key or "", **updated.model_dump(exclude={"key"}))


@router.delete("/{key}", status_code=204)
def delete_location(key: str, service: SiteService = Depends(get_site_service)):
    service.delete_location(key)


# ── Sensors ──────────────────────────────────────────────────────────


@router.get("/{key}/sensors", response_model=list[SensorResponse])
def get_location_sensors(
    key: str,
    sensor_service: SensorService = Depends(get_sensor_service),
):
    sensors = sensor_service.get_sensors_for_location(key)
    return [SensorResponse(key=s.key or "", **s.model_dump(exclude={"key"})) for s in sensors]


@router.post("/{key}/sensors", response_model=SensorResponse, status_code=201)
def create_location_sensor(
    key: str,
    body: SensorCreate,
    sensor_service: SensorService = Depends(get_sensor_service),
):
    sensor = Sensor(
        name=body.name,
        metric_type=body.metric_type,
        ha_entity_id=body.ha_entity_id,
        mqtt_topic=body.mqtt_topic,
        location_key=key,
    )
    created = sensor_service.create_sensor(sensor)
    return SensorResponse(key=created.key or "", **created.model_dump(exclude={"key"}))


@router.get("/{key}/sensors/live", response_model=LiveStateResponse)
def get_location_sensors_live(
    key: str,
    sensor_service: SensorService = Depends(get_sensor_service),
):
    sensors = sensor_service.get_sensors_for_location(key)
    result = sensor_service.get_live_state_for_sensors(sensors)
    return LiveStateResponse(**result)
