from fastapi import APIRouter, Depends, Query

from app.api.v1.tanks.router import _fill_event_response, _tank_response
from app.api.v1.tanks.schemas import (
    ActiveNutrientPlanResponse,
    ActivePlanFertilizerInfo,
    AlertResponse,
    DueMaintenanceResponse,
    FeedsFromRequest,
    FillEventResultResponse,
    LiveStateResponse,
    MaintenanceLogCreate,
    MaintenanceLogResponse,
    MaintenanceScheduleCreate,
    MaintenanceScheduleResponse,
    MaintenanceScheduleUpdate,
    SensorCreate,
    SensorResponse,
    TankCreate,
    TankFillEventCreate,
    TankFillEventResponse,
    TankFillEventStatsResponse,
    TankResponse,
    TankStateCreate,
    TankStateResponse,
    TankUpdate,
)
from app.common.auth import get_current_tenant
from app.common.dependencies import get_sensor_service, get_tank_service
from app.domain.models.sensor import Sensor
from app.domain.models.tank import (
    FertilizerSnapshot,
    MaintenanceLog,
    MaintenanceSchedule,
    Tank,
    TankFillEvent,
    TankState,
)
from app.domain.models.tenant_context import TenantContext
from app.domain.services.sensor_service import SensorService
from app.domain.services.tank_service import TankService

router = APIRouter(prefix="/tanks", tags=["tanks"])


@router.get("/maintenance/due", response_model=list[DueMaintenanceResponse])
def get_all_due_maintenances(
    ctx: TenantContext = Depends(get_current_tenant),
    service: TankService = Depends(get_tank_service),
):
    dues = service.get_all_due_maintenances(tenant_key=ctx.tenant_key)
    return [DueMaintenanceResponse(**d) for d in dues]


@router.get("", response_model=list[TankResponse])
def list_tanks(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    tank_type: str | None = None,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TankService = Depends(get_tank_service),
):
    filters: dict[str, str] = {}
    if tank_type:
        filters["tank_type"] = tank_type
    items, _total = service.list_tanks(offset, limit, filters or None, tenant_key=ctx.tenant_key)
    return [_tank_response(t) for t in items]


@router.post("", response_model=TankResponse, status_code=201)
def create_tank(
    body: TankCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TankService = Depends(get_tank_service),
):
    tank = Tank(**body.model_dump(), tenant_key=ctx.tenant_key)
    created = service.create_tank(tank)
    return _tank_response(created)


@router.get("/{key}", response_model=TankResponse)
def get_tank(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TankService = Depends(get_tank_service),
):
    t = service.get_tank(key, tenant_key=ctx.tenant_key)
    return _tank_response(t)


@router.put("/{key}", response_model=TankResponse)
def update_tank(
    key: str,
    body: TankUpdate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TankService = Depends(get_tank_service),
):
    service.get_tank(key, tenant_key=ctx.tenant_key)
    data = body.model_dump(exclude_none=True)
    updated = service.update_tank(key, data)
    return _tank_response(updated)


@router.delete("/{key}", status_code=204)
def delete_tank(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TankService = Depends(get_tank_service),
):
    service.get_tank(key, tenant_key=ctx.tenant_key)
    service.delete_tank(key)


@router.post("/{key}/states", response_model=TankStateResponse, status_code=201)
def record_state(
    key: str,
    body: TankStateCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TankService = Depends(get_tank_service),
):
    service.get_tank(key, tenant_key=ctx.tenant_key)
    state = TankState(**body.model_dump())
    created = service.record_state(key, state)
    return TankStateResponse(key=created.key or "", **created.model_dump(exclude={"key"}))


@router.get("/{key}/states", response_model=list[TankStateResponse])
def get_states(
    key: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: TenantContext = Depends(get_current_tenant),
    service: TankService = Depends(get_tank_service),
):
    service.get_tank(key, tenant_key=ctx.tenant_key)
    states = service.get_states(key, offset, limit)
    return [TankStateResponse(key=s.key or "", **s.model_dump(exclude={"key"})) for s in states]


@router.get("/{key}/states/latest", response_model=TankStateResponse | None)
def get_latest_state(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TankService = Depends(get_tank_service),
):
    service.get_tank(key, tenant_key=ctx.tenant_key)
    state = service.get_latest_state(key)
    if state is None:
        return None
    return TankStateResponse(key=state.key or "", **state.model_dump(exclude={"key"}))


@router.get("/{key}/alerts", response_model=list[AlertResponse])
def get_alerts(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TankService = Depends(get_tank_service),
):
    service.get_tank(key, tenant_key=ctx.tenant_key)
    alerts = service.get_alerts(key)
    return [AlertResponse(**a) for a in alerts]


@router.post("/{key}/maintenance", response_model=MaintenanceLogResponse, status_code=201)
def log_maintenance(
    key: str,
    body: MaintenanceLogCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TankService = Depends(get_tank_service),
):
    service.get_tank(key, tenant_key=ctx.tenant_key)
    log = MaintenanceLog(**body.model_dump())
    created = service.log_maintenance(key, log)
    return MaintenanceLogResponse(key=created.key or "", **created.model_dump(exclude={"key"}))


@router.get("/{key}/maintenance", response_model=list[MaintenanceLogResponse])
def get_maintenance_history(
    key: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: TenantContext = Depends(get_current_tenant),
    service: TankService = Depends(get_tank_service),
):
    service.get_tank(key, tenant_key=ctx.tenant_key)
    logs = service.get_maintenance_history(key, offset, limit)
    return [MaintenanceLogResponse(key=log.key or "", **log.model_dump(exclude={"key"})) for log in logs]


@router.get("/{key}/maintenance/due", response_model=list[DueMaintenanceResponse])
def get_due_maintenances(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TankService = Depends(get_tank_service),
):
    service.get_tank(key, tenant_key=ctx.tenant_key)
    dues = service.get_due_maintenances(key)
    return [DueMaintenanceResponse(**d) for d in dues]


@router.post("/{key}/schedules", response_model=MaintenanceScheduleResponse, status_code=201)
def create_schedule(
    key: str,
    body: MaintenanceScheduleCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TankService = Depends(get_tank_service),
):
    service.get_tank(key, tenant_key=ctx.tenant_key)
    schedule = MaintenanceSchedule(**body.model_dump())
    created = service.create_schedule(key, schedule)
    return MaintenanceScheduleResponse(key=created.key or "", **created.model_dump(exclude={"key"}))


@router.get("/{key}/schedules", response_model=list[MaintenanceScheduleResponse])
def get_schedules(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TankService = Depends(get_tank_service),
):
    service.get_tank(key, tenant_key=ctx.tenant_key)
    schedules = service.get_schedules(key)
    return [MaintenanceScheduleResponse(key=s.key or "", **s.model_dump(exclude={"key"})) for s in schedules]


@router.put("/{key}/schedules/{skey}", response_model=MaintenanceScheduleResponse)
def update_schedule(
    key: str,
    skey: str,
    body: MaintenanceScheduleUpdate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TankService = Depends(get_tank_service),
):
    service.get_tank(key, tenant_key=ctx.tenant_key)
    data = body.model_dump(exclude_none=True)
    updated = service.update_schedule(skey, data)
    return MaintenanceScheduleResponse(key=updated.key or "", **updated.model_dump(exclude={"key"}))


@router.delete("/{key}/schedules/{skey}", status_code=204)
def delete_schedule(
    key: str,
    skey: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TankService = Depends(get_tank_service),
):
    service.get_tank(key, tenant_key=ctx.tenant_key)
    service.delete_schedule(skey)


@router.post("/{key}/fills", response_model=FillEventResultResponse, status_code=201)
def record_fill_event(
    key: str,
    body: TankFillEventCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TankService = Depends(get_tank_service),
):
    service.get_tank(key, tenant_key=ctx.tenant_key)
    ferts = [FertilizerSnapshot(**f.model_dump()) for f in body.fertilizers_used]
    event = TankFillEvent(**body.model_dump(exclude={"fertilizers_used"}), fertilizers_used=ferts)
    result = service.record_fill_event(key, event)
    return FillEventResultResponse(
        fill_event=_fill_event_response(result["fill_event"]),
        tank_state=(
            TankStateResponse(key=result["tank_state"].key or "", **result["tank_state"].model_dump(exclude={"key"}))
            if result["tank_state"]
            else None
        ),
        warnings=result["warnings"],
        water_defaults_source=result["water_defaults_source"],
    )


@router.get("/{key}/fills", response_model=list[TankFillEventResponse])
def get_fill_events(
    key: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: TenantContext = Depends(get_current_tenant),
    service: TankService = Depends(get_tank_service),
):
    service.get_tank(key, tenant_key=ctx.tenant_key)
    events = service.get_fill_history(key, offset, limit)
    return [_fill_event_response(e) for e in events]


@router.get("/{key}/fills/latest", response_model=TankFillEventResponse | None)
def get_latest_fill(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TankService = Depends(get_tank_service),
):
    service.get_tank(key, tenant_key=ctx.tenant_key)
    event = service.get_latest_fill(key)
    if event is None:
        return None
    return _fill_event_response(event)


@router.get("/{key}/fills/stats", response_model=TankFillEventStatsResponse)
def get_fill_stats(
    key: str,
    start_date: str | None = None,
    end_date: str | None = None,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TankService = Depends(get_tank_service),
):
    service.get_tank(key, tenant_key=ctx.tenant_key)
    stats = service.get_fill_stats(key, start_date, end_date)
    return TankFillEventStatsResponse(**stats)


@router.get("/{key}/active-nutrient-plans", response_model=list[ActiveNutrientPlanResponse])
def get_active_nutrient_plans(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TankService = Depends(get_tank_service),
):
    service.get_tank(key, tenant_key=ctx.tenant_key)
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
            fertilizers=[ActivePlanFertilizerInfo(**f) for f in r.get("fertilizers", [])],
            watering_schedule=r.get("watering_schedule"),
            water_mix_ratio_ro_percent=r.get("water_mix_ratio_ro_percent"),
        )
        for r in results
    ]


@router.post("/{key}/feeds-from", status_code=201)
def link_feeds_from(
    key: str,
    body: FeedsFromRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TankService = Depends(get_tank_service),
):
    service.get_tank(key, tenant_key=ctx.tenant_key)
    service.link_feeds_from(key, body.source_tank_key)
    return {"status": "linked"}


@router.get("/{key}/states/live", response_model=LiveStateResponse)
def get_live_state(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    tank_service: TankService = Depends(get_tank_service),
    sensor_service: SensorService = Depends(get_sensor_service),
):
    tank_service.get_tank(key, tenant_key=ctx.tenant_key)
    result = sensor_service.get_live_state(key)
    return LiveStateResponse(**result)


@router.get("/{key}/sensors", response_model=list[SensorResponse])
def get_sensors(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    tank_service: TankService = Depends(get_tank_service),
    sensor_service: SensorService = Depends(get_sensor_service),
):
    tank_service.get_tank(key, tenant_key=ctx.tenant_key)
    sensors = sensor_service.get_sensors_for_tank(key)
    return [SensorResponse(key=s.key or "", **s.model_dump(exclude={"key"})) for s in sensors]


@router.post("/{key}/sensors", response_model=SensorResponse, status_code=201)
def create_sensor(
    key: str,
    body: SensorCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    tank_service: TankService = Depends(get_tank_service),
    sensor_service: SensorService = Depends(get_sensor_service),
):
    tank_service.get_tank(key, tenant_key=ctx.tenant_key)
    sensor = Sensor(**body.model_dump(exclude={"tank_key"}), tank_key=key)
    created = sensor_service.create_sensor(sensor)
    return SensorResponse(key=created.key or "", **created.model_dump(exclude={"key"}))
