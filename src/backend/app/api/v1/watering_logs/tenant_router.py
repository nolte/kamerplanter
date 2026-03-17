from fastapi import APIRouter, Depends, Query

from app.api.v1.watering_logs.router import _log_response
from app.api.v1.watering_logs.schemas import (
    WateringConfirmRequest,
    WateringConfirmResponse,
    WateringLogCreate,
    WateringLogResponse,
    WateringLogUpdate,
    WateringLogWithWarnings,
    WateringQuickConfirmRequest,
    WateringStatsResponse,
)
from app.common.auth import get_current_tenant
from app.common.dependencies import get_watering_log_service
from app.domain.models.tenant_context import TenantContext
from app.domain.models.watering_log import WateringLog
from app.domain.services.watering_log_service import WateringLogService

router = APIRouter(tags=["watering-logs"])


@router.post("/watering-logs", response_model=WateringLogWithWarnings, status_code=201)
def create_log(
    body: WateringLogCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: WateringLogService = Depends(get_watering_log_service),
):
    log = WateringLog(**body.model_dump(), tenant_key=ctx.tenant_key)
    result = service.create_log(log)
    created = result["log"]
    fert_keys = list({fu.fertilizer_key for fu in created.fertilizers_used})
    fert_map = service.resolve_fertilizer_names(fert_keys) if fert_keys else {}
    plant_map = service.resolve_plant_names(created.plant_keys) if created.plant_keys else {}
    return WateringLogWithWarnings(log=_log_response(created, plant_map, fert_map), warnings=result["warnings"])


@router.get("/watering-logs", response_model=list[WateringLogResponse])
def list_logs(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: TenantContext = Depends(get_current_tenant),
    service: WateringLogService = Depends(get_watering_log_service),
):
    items, _total = service.list_logs(offset, limit, tenant_key=ctx.tenant_key)
    all_plant_keys = list({pk for log in items for pk in log.plant_keys})
    name_map = service.resolve_plant_names(all_plant_keys) if all_plant_keys else {}
    all_fert_keys = list({fu.fertilizer_key for log in items for fu in log.fertilizers_used})
    fert_map = service.resolve_fertilizer_names(all_fert_keys) if all_fert_keys else {}
    return [_log_response(log, name_map, fert_map) for log in items]


@router.get("/watering-logs/{key}", response_model=WateringLogResponse)
def get_log(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: WateringLogService = Depends(get_watering_log_service),
):
    log = service.get_log(key, tenant_key=ctx.tenant_key)
    name_map = service.resolve_plant_names(log.plant_keys) if log.plant_keys else {}
    fert_keys = list({fu.fertilizer_key for fu in log.fertilizers_used})
    fert_map = service.resolve_fertilizer_names(fert_keys) if fert_keys else {}
    return _log_response(log, name_map, fert_map)


@router.put("/watering-logs/{key}", response_model=WateringLogResponse)
def update_log(
    key: str,
    body: WateringLogUpdate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: WateringLogService = Depends(get_watering_log_service),
):
    service.get_log(key, tenant_key=ctx.tenant_key)
    updated = service.update_log(key, body.model_dump(exclude_unset=True))
    name_map = service.resolve_plant_names(updated.plant_keys) if updated.plant_keys else {}
    fert_keys = list({fu.fertilizer_key for fu in updated.fertilizers_used})
    fert_map = service.resolve_fertilizer_names(fert_keys) if fert_keys else {}
    return _log_response(updated, name_map, fert_map)


@router.delete("/watering-logs/{key}", status_code=204)
def delete_log(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: WateringLogService = Depends(get_watering_log_service),
):
    service.get_log(key, tenant_key=ctx.tenant_key)
    service.delete_log(key)


@router.get("/watering-logs/{key}/runoff")
def get_runoff_analysis(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: WateringLogService = Depends(get_watering_log_service),
):
    service.get_log(key, tenant_key=ctx.tenant_key)
    return service.analyze_runoff(key)


@router.get("/watering-logs/plant/{plant_key}", response_model=list[WateringLogResponse])
def get_plant_logs(
    plant_key: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: TenantContext = Depends(get_current_tenant),
    service: WateringLogService = Depends(get_watering_log_service),
):
    logs = service.get_by_plant(plant_key, offset, limit)
    all_pks = list({pk for log in logs for pk in log.plant_keys})
    name_map = service.resolve_plant_names(all_pks) if all_pks else {}
    all_fks = list({fu.fertilizer_key for log in logs for fu in log.fertilizers_used})
    fert_map = service.resolve_fertilizer_names(all_fks) if all_fks else {}
    return [_log_response(log, name_map, fert_map) for log in logs]


@router.get("/slots/{slot_key}/watering-logs", response_model=list[WateringLogResponse])
def get_slot_logs(
    slot_key: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: TenantContext = Depends(get_current_tenant),
    service: WateringLogService = Depends(get_watering_log_service),
):
    logs = service.get_by_slot(slot_key, offset, limit)
    all_pks = list({pk for log in logs for pk in log.plant_keys})
    name_map = service.resolve_plant_names(all_pks) if all_pks else {}
    all_fks = list({fu.fertilizer_key for log in logs for fu in log.fertilizers_used})
    fert_map = service.resolve_fertilizer_names(all_fks) if all_fks else {}
    return [_log_response(log, name_map, fert_map) for log in logs]


@router.get("/locations/{location_key}/watering-logs", response_model=list[WateringLogResponse])
def get_location_logs(
    location_key: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: TenantContext = Depends(get_current_tenant),
    service: WateringLogService = Depends(get_watering_log_service),
):
    logs = service.get_by_location(location_key, offset, limit)
    all_pks = list({pk for log in logs for pk in log.plant_keys})
    name_map = service.resolve_plant_names(all_pks) if all_pks else {}
    all_fks = list({fu.fertilizer_key for log in logs for fu in log.fertilizers_used})
    fert_map = service.resolve_fertilizer_names(all_fks) if all_fks else {}
    return [_log_response(log, name_map, fert_map) for log in logs]


@router.get("/locations/{location_key}/watering-stats", response_model=WateringStatsResponse)
def get_location_watering_stats(
    location_key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: WateringLogService = Depends(get_watering_log_service),
):
    stats = service.get_stats(location_key)
    return WateringStatsResponse(**stats)


@router.post("/watering-logs/confirm", response_model=WateringConfirmResponse, status_code=201)
def confirm_watering(
    body: WateringConfirmRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: WateringLogService = Depends(get_watering_log_service),
):
    result = service.confirm_watering(
        run_key=body.run_key,
        task_key=body.task_key,
        measured_ec=body.measured_ec,
        measured_ph=body.measured_ph,
        volume_liters=body.volume_liters,
        overrides=body.overrides,
    )
    return WateringConfirmResponse(**result)


@router.post("/watering-logs/quick-confirm", response_model=WateringConfirmResponse, status_code=201)
def quick_confirm_watering(
    body: WateringQuickConfirmRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: WateringLogService = Depends(get_watering_log_service),
):
    result = service.quick_confirm_watering(body.run_key, body.task_key)
    return WateringConfirmResponse(**result)
