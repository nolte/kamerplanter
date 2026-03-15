from fastapi import APIRouter, Depends, Query

from app.api.v1.tanks.schemas import (
    ActiveNutrientPlanResponse,
    ActivePlanFertilizerInfo,
    AlertResponse,
    DueMaintenanceResponse,
    FeedsFromRequest,
    FillEventResultResponse,
    HAEntitySuggestion,
    LiveStateResponse,
    LocationTankValidationResponse,
    MaintenanceLogCreate,
    MaintenanceLogResponse,
    MaintenanceScheduleCreate,
    MaintenanceScheduleResponse,
    MaintenanceScheduleUpdate,
    SensorCreate,
    SensorResponse,
    SensorUpdate,
    TankCreate,
    TankFillEventCreate,
    TankFillEventResponse,
    TankFillEventStatsResponse,
    TankResponse,
    TankStateCreate,
    TankStateResponse,
    TankUpdate,
)
from app.common.dependencies import get_ha_client, get_sensor_service, get_site_service, get_tank_service
from app.common.enums import IrrigationSystem
from app.data_access.external.ha_client import HomeAssistantClient
from app.domain.models.sensor import Sensor
from app.domain.models.tank import (
    FertilizerSnapshot,
    MaintenanceLog,
    MaintenanceSchedule,
    Tank,
    TankFillEvent,
    TankState,
)
from app.domain.services.sensor_service import SensorService
from app.domain.services.site_service import SiteService
from app.domain.services.tank_service import TankService

router = APIRouter(prefix="/tanks", tags=["tanks"])


def _tank_response(t: Tank) -> TankResponse:
    return TankResponse(key=t.key or "", **t.model_dump(exclude={"key"}))


# ── Global maintenance overview (before /{key} to avoid route conflict) ──

@router.get("/maintenance/due", response_model=list[DueMaintenanceResponse])
def get_all_due_maintenances(
    service: TankService = Depends(get_tank_service),
):
    dues = service.get_all_due_maintenances()
    return [DueMaintenanceResponse(**d) for d in dues]


# ── Location validation ──────────────────────────────────────────────

@router.get(
    "/validate-location/{location_key}",
    response_model=LocationTankValidationResponse,
)
def validate_location_tank(
    location_key: str,
    site_service: SiteService = Depends(get_site_service),
    tank_service: TankService = Depends(get_tank_service),
):
    """Check if a location with non-manual irrigation has a tank assigned."""
    site = site_service.get_site(location_key)
    warnings: list[str] = []

    if site.irrigation_system != IrrigationSystem.MANUAL:
        tanks, _total = tank_service.list_tanks(
            offset=0, limit=1, filters={"location_key": location_key},
        )
        if not tanks:
            warnings.append(
                f"Location '{site.name}' uses {site.irrigation_system.value} irrigation "
                "but has no tank assigned"
            )

    return LocationTankValidationResponse(valid=len(warnings) == 0, warnings=warnings)


# ── Sensor CRUD (before /{key} to avoid route conflict) ─────────────

@router.put("/sensors/{sensor_key}", response_model=SensorResponse)
def update_sensor(
    sensor_key: str,
    body: SensorUpdate,
    sensor_service: SensorService = Depends(get_sensor_service),
):
    from app.common.exceptions import NotFoundError
    existing = sensor_service.get_sensor(sensor_key)
    if existing is None:
        raise NotFoundError("Sensor", sensor_key)
    data = body.model_dump(exclude_none=True)
    for field, value in data.items():
        setattr(existing, field, value)
    updated = sensor_service.update_sensor(sensor_key, existing)
    return SensorResponse(key=updated.key or "", **updated.model_dump(exclude={"key"}))


@router.delete("/sensors/{sensor_key}", status_code=204)
def delete_sensor(
    sensor_key: str,
    sensor_service: SensorService = Depends(get_sensor_service),
):
    sensor_service.delete_sensor(sensor_key)


# ── HA Entity Discovery ───────────────────────────────────────────────

# Map HA device_class / unit_of_measurement to kamerplanter metric types
_DEVICE_CLASS_MAP: dict[str, str] = {
    "ph": "ph",
    "conductivity": "ec_ms",
    "temperature": "water_temp_celsius",
    "volume": "fill_level_liters",
    "distance": "fill_level_percent",
}

_UNIT_MAP: dict[str, str] = {
    "pH": "ph",
    "µS/cm": "ec_ms",
    "mS/cm": "ec_ms",
    "°C": "water_temp_celsius",
    "°F": "water_temp_celsius",
    "ppm": "tds_ppm",
    "mg/L": "dissolved_oxygen_mgl",
    "mV": "orp_mv",
    "%": "fill_level_percent",
    "L": "fill_level_liters",
}

_ENTITY_ID_HINTS: dict[str, str] = {
    "ph": "ph",
    "ec": "ec_ms",
    "conductivity": "ec_ms",
    "tds": "tds_ppm",
    "temperature": "water_temp_celsius",
    "temp": "water_temp_celsius",
    "oxygen": "dissolved_oxygen_mgl",
    "do": "dissolved_oxygen_mgl",
    "orp": "orp_mv",
    "redox": "orp_mv",
    "level": "fill_level_percent",
    "fill": "fill_level_percent",
    "volume": "fill_level_liters",
}


def _suggest_metric_type(entity: dict) -> str | None:
    """Infer kamerplanter metric_type from HA entity metadata."""
    dc = (entity.get("device_class") or "").lower()
    if dc in _DEVICE_CLASS_MAP:
        return _DEVICE_CLASS_MAP[dc]

    unit = entity.get("unit_of_measurement") or ""
    if unit in _UNIT_MAP:
        return _UNIT_MAP[unit]

    eid = (entity.get("entity_id") or "").lower()
    for hint, metric in _ENTITY_ID_HINTS.items():
        if hint in eid:
            return metric

    return None


@router.get("/ha-entities", response_model=list[HAEntitySuggestion])
def list_ha_entities(
    ha_client: HomeAssistantClient | None = Depends(get_ha_client),
):
    """Discover sensor entities from Home Assistant with metric type suggestions."""
    if ha_client is None:
        return []
    entities = ha_client.list_sensor_entities()
    results = []
    for e in entities:
        metric = _suggest_metric_type(e)
        results.append(HAEntitySuggestion(
            entity_id=e["entity_id"],
            friendly_name=e["friendly_name"],
            unit_of_measurement=e.get("unit_of_measurement"),
            device_class=e.get("device_class"),
            state=e.get("state"),
            suggested_metric_type=metric,
            suggested_name=e["friendly_name"],
        ))
    return results


# ── Tank CRUD ──────────────────────────────────────────────────────────

@router.get("", response_model=list[TankResponse])
def list_tanks(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    tank_type: str | None = None,
    service: TankService = Depends(get_tank_service),
):
    filters: dict[str, str] = {}
    if tank_type:
        filters["tank_type"] = tank_type
    items, _total = service.list_tanks(offset, limit, filters or None)
    return [_tank_response(t) for t in items]


@router.post("", response_model=TankResponse, status_code=201)
def create_tank(
    body: TankCreate,
    service: TankService = Depends(get_tank_service),
):
    tank = Tank(**body.model_dump())
    created = service.create_tank(tank)
    return _tank_response(created)


@router.get("/{key}", response_model=TankResponse)
def get_tank(key: str, service: TankService = Depends(get_tank_service)):
    t = service.get_tank(key)
    return _tank_response(t)


@router.put("/{key}", response_model=TankResponse)
def update_tank(
    key: str,
    body: TankUpdate,
    service: TankService = Depends(get_tank_service),
):
    data = body.model_dump(exclude_none=True)
    updated = service.update_tank(key, data)
    return _tank_response(updated)


@router.delete("/{key}", status_code=204)
def delete_tank(key: str, service: TankService = Depends(get_tank_service)):
    service.delete_tank(key)


# ── States ─────────────────────────────────────────────────────────────

@router.post("/{key}/states", response_model=TankStateResponse, status_code=201)
def record_state(
    key: str,
    body: TankStateCreate,
    service: TankService = Depends(get_tank_service),
):
    state = TankState(**body.model_dump())
    created = service.record_state(key, state)
    return TankStateResponse(key=created.key or "", **created.model_dump(exclude={"key"}))


@router.get("/{key}/states", response_model=list[TankStateResponse])
def get_states(
    key: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: TankService = Depends(get_tank_service),
):
    states = service.get_states(key, offset, limit)
    return [
        TankStateResponse(key=s.key or "", **s.model_dump(exclude={"key"}))
        for s in states
    ]


@router.get("/{key}/states/latest", response_model=TankStateResponse | None)
def get_latest_state(
    key: str,
    service: TankService = Depends(get_tank_service),
):
    state = service.get_latest_state(key)
    if state is None:
        return None
    return TankStateResponse(key=state.key or "", **state.model_dump(exclude={"key"}))


# ── Alerts ─────────────────────────────────────────────────────────────

@router.get("/{key}/alerts", response_model=list[AlertResponse])
def get_alerts(key: str, service: TankService = Depends(get_tank_service)):
    alerts = service.get_alerts(key)
    return [AlertResponse(**a) for a in alerts]


# ── Maintenance logs ───────────────────────────────────────────────────

@router.post("/{key}/maintenance", response_model=MaintenanceLogResponse, status_code=201)
def log_maintenance(
    key: str,
    body: MaintenanceLogCreate,
    service: TankService = Depends(get_tank_service),
):
    log = MaintenanceLog(**body.model_dump())
    created = service.log_maintenance(key, log)
    return MaintenanceLogResponse(key=created.key or "", **created.model_dump(exclude={"key"}))


@router.get("/{key}/maintenance", response_model=list[MaintenanceLogResponse])
def get_maintenance_history(
    key: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: TankService = Depends(get_tank_service),
):
    logs = service.get_maintenance_history(key, offset, limit)
    return [
        MaintenanceLogResponse(key=log.key or "", **log.model_dump(exclude={"key"}))
        for log in logs
    ]


@router.get("/{key}/maintenance/due", response_model=list[DueMaintenanceResponse])
def get_due_maintenances(
    key: str,
    service: TankService = Depends(get_tank_service),
):
    dues = service.get_due_maintenances(key)
    return [DueMaintenanceResponse(**d) for d in dues]


# ── Schedules ──────────────────────────────────────────────────────────

@router.post("/{key}/schedules", response_model=MaintenanceScheduleResponse, status_code=201)
def create_schedule(
    key: str,
    body: MaintenanceScheduleCreate,
    service: TankService = Depends(get_tank_service),
):
    schedule = MaintenanceSchedule(**body.model_dump())
    created = service.create_schedule(key, schedule)
    return MaintenanceScheduleResponse(
        key=created.key or "", **created.model_dump(exclude={"key"}),
    )


@router.get("/{key}/schedules", response_model=list[MaintenanceScheduleResponse])
def get_schedules(
    key: str,
    service: TankService = Depends(get_tank_service),
):
    schedules = service.get_schedules(key)
    return [
        MaintenanceScheduleResponse(key=s.key or "", **s.model_dump(exclude={"key"}))
        for s in schedules
    ]


@router.put("/{key}/schedules/{skey}", response_model=MaintenanceScheduleResponse)
def update_schedule(
    key: str,
    skey: str,
    body: MaintenanceScheduleUpdate,
    service: TankService = Depends(get_tank_service),
):
    data = body.model_dump(exclude_none=True)
    updated = service.update_schedule(skey, data)
    return MaintenanceScheduleResponse(
        key=updated.key or "", **updated.model_dump(exclude={"key"}),
    )


@router.delete("/{key}/schedules/{skey}", status_code=204)
def delete_schedule(
    key: str,
    skey: str,
    service: TankService = Depends(get_tank_service),
):
    service.delete_schedule(skey)


# ── Fill Events ────────────────────────────────────────────────────────

def _fill_event_response(e: TankFillEvent) -> TankFillEventResponse:
    return TankFillEventResponse(key=e.key or "", **e.model_dump(exclude={"key"}))


@router.post("/{key}/fills", response_model=FillEventResultResponse, status_code=201)
def record_fill_event(
    key: str,
    body: TankFillEventCreate,
    service: TankService = Depends(get_tank_service),
):
    ferts = [
        FertilizerSnapshot(**f.model_dump())
        for f in body.fertilizers_used
    ]
    event = TankFillEvent(
        **body.model_dump(exclude={"fertilizers_used"}),
        fertilizers_used=ferts,
    )
    result = service.record_fill_event(key, event)
    return FillEventResultResponse(
        fill_event=_fill_event_response(result["fill_event"]),
        tank_state=(
            TankStateResponse(key=result["tank_state"].key or "", **result["tank_state"].model_dump(exclude={"key"}))
            if result["tank_state"] else None
        ),
        warnings=result["warnings"],
        water_defaults_source=result["water_defaults_source"],
    )


@router.get("/{key}/fills", response_model=list[TankFillEventResponse])
def get_fill_events(
    key: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: TankService = Depends(get_tank_service),
):
    events = service.get_fill_history(key, offset, limit)
    return [_fill_event_response(e) for e in events]


@router.get("/{key}/fills/latest", response_model=TankFillEventResponse | None)
def get_latest_fill(
    key: str,
    service: TankService = Depends(get_tank_service),
):
    event = service.get_latest_fill(key)
    if event is None:
        return None
    return _fill_event_response(event)


@router.get("/{key}/fills/stats", response_model=TankFillEventStatsResponse)
def get_fill_stats(
    key: str,
    start_date: str | None = None,
    end_date: str | None = None,
    service: TankService = Depends(get_tank_service),
):
    stats = service.get_fill_stats(key, start_date, end_date)
    return TankFillEventStatsResponse(**stats)


# ── Active Nutrient Plans ─────────────────────────────────────────────

@router.get("/{key}/active-nutrient-plans", response_model=list[ActiveNutrientPlanResponse])
def get_active_nutrient_plans(
    key: str,
    service: TankService = Depends(get_tank_service),
):
    """Resolve nutrient plans for active planting runs at this tank's location."""
    results = service.get_active_nutrient_plans(key)
    return [
        ActiveNutrientPlanResponse(
            run_key=r["run_key"],
            run_name=r["run_name"],
            run_status=r["run_status"],
            plan_key=r["plan_key"],
            plan_name=r["plan_name"],
            current_phase=r.get("current_phase"),
            plant_count=r.get("plant_count", 0),
            current_phase_entry=r.get("current_phase_entry"),
            all_phase_entries=r.get("all_phase_entries", []),
            fertilizers=[
                ActivePlanFertilizerInfo(**f) for f in r.get("fertilizers", [])
            ],
            watering_schedule=r.get("watering_schedule"),
            water_mix_ratio_ro_percent=r.get("water_mix_ratio_ro_percent"),
        )
        for r in results
    ]


# ── Relationships ──────────────────────────────────────────────────────

@router.post("/{key}/feeds-from", status_code=201)
def link_feeds_from(
    key: str,
    body: FeedsFromRequest,
    service: TankService = Depends(get_tank_service),
):
    service.link_feeds_from(key, body.source_tank_key)
    return {"status": "linked"}


# ── Sensors & Live Query ──────────────────────────────────────────────

@router.get("/{key}/states/live", response_model=LiveStateResponse)
def get_live_state(
    key: str,
    sensor_service: SensorService = Depends(get_sensor_service),
):
    """Read-through live query from Home Assistant — no persistence."""
    result = sensor_service.get_live_state(key)
    return LiveStateResponse(**result)


@router.get("/{key}/sensors", response_model=list[SensorResponse])
def get_sensors(
    key: str,
    sensor_service: SensorService = Depends(get_sensor_service),
):
    sensors = sensor_service.get_sensors_for_tank(key)
    return [
        SensorResponse(key=s.key or "", **s.model_dump(exclude={"key"}))
        for s in sensors
    ]


@router.post("/{key}/sensors", response_model=SensorResponse, status_code=201)
def create_sensor(
    key: str,
    body: SensorCreate,
    sensor_service: SensorService = Depends(get_sensor_service),
):
    sensor = Sensor(**body.model_dump(exclude={"tank_key"}), tank_key=key)
    created = sensor_service.create_sensor(sensor)
    return SensorResponse(key=created.key or "", **created.model_dump(exclude={"key"}))


