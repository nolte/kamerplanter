from fastapi import APIRouter, Depends, Query

from app.api.v1.tanks.schemas import (
    AlertResponse,
    DueMaintenanceResponse,
    FeedsFromRequest,
    MaintenanceLogCreate,
    MaintenanceLogResponse,
    MaintenanceScheduleCreate,
    MaintenanceScheduleResponse,
    MaintenanceScheduleUpdate,
    TankCreate,
    TankResponse,
    TankStateCreate,
    TankStateResponse,
    TankUpdate,
)
from app.common.dependencies import get_tank_service
from app.domain.models.tank import MaintenanceLog, MaintenanceSchedule, Tank, TankState
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


# ── Relationships ──────────────────────────────────────────────────────

@router.post("/{key}/feeds-from", status_code=201)
def link_feeds_from(
    key: str,
    body: FeedsFromRequest,
    service: TankService = Depends(get_tank_service),
):
    service.link_feeds_from(key, body.source_tank_key)
    return {"status": "linked"}
