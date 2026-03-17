from fastapi import APIRouter, Depends, Query

from app.api.v1.plant_instances.router import _to_response
from app.api.v1.plant_instances.schemas import (
    ActiveChannelResponse,
    AssignNutrientPlanRequest,
    PlantCreate,
    PlantResponse,
    ValidatePlantingRequest,
    ValidatePlantingResponse,
)
from app.common.auth import get_current_tenant
from app.common.dependencies import get_nutrient_plan_service, get_plant_instance_service, get_planting_run_service
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.tenant_context import TenantContext
from app.domain.services.nutrient_plan_service import NutrientPlanService
from app.domain.services.plant_instance_service import PlantInstanceService
from app.domain.services.planting_run_service import PlantingRunService

router = APIRouter(prefix="/plant-instances", tags=["plant-instances"])


@router.get("", response_model=list[PlantResponse])
def list_plants(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantInstanceService = Depends(get_plant_instance_service),
):
    items, _total = service.list_plants(offset, limit, tenant_key=ctx.tenant_key)
    return [_to_response(p, service) for p in items]


@router.get("/{key}", response_model=PlantResponse)
def get_plant(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantInstanceService = Depends(get_plant_instance_service),
):
    p = service.get_plant(key, tenant_key=ctx.tenant_key)
    return _to_response(p, service)


@router.post("", response_model=PlantResponse, status_code=201)
def create_plant(
    body: PlantCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantInstanceService = Depends(get_plant_instance_service),
):
    plant = PlantInstance(**body.model_dump(), tenant_key=ctx.tenant_key)
    created = service.create_plant(plant)
    return _to_response(created, service)


@router.put("/{key}", response_model=PlantResponse)
def update_plant(
    key: str,
    body: PlantCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantInstanceService = Depends(get_plant_instance_service),
):
    service.get_plant(key, tenant_key=ctx.tenant_key)
    plant = PlantInstance(**body.model_dump(), tenant_key=ctx.tenant_key)
    updated = service.update_plant(key, plant)
    return _to_response(updated, service)


@router.post("/{key}/remove", response_model=PlantResponse)
def remove_plant(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantInstanceService = Depends(get_plant_instance_service),
):
    service.get_plant(key, tenant_key=ctx.tenant_key)
    removed = service.remove_plant(key)
    return _to_response(removed, service)


@router.post("/slots/{slot_key}/validate-planting", response_model=ValidatePlantingResponse)
def validate_planting(
    slot_key: str,
    body: ValidatePlantingRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantInstanceService = Depends(get_plant_instance_service),
):
    result = service.validate_planting(slot_key, body.species_key)
    return ValidatePlantingResponse(**result)


@router.post("/{key}/nutrient-plan", status_code=201)
def assign_nutrient_plan(
    key: str,
    body: AssignNutrientPlanRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    plant_service: PlantInstanceService = Depends(get_plant_instance_service),
    plan_service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    plant_service.get_plant(key, tenant_key=ctx.tenant_key)
    plan_service.assign_to_plant(key, body.plan_key, body.assigned_by)
    return {"status": "assigned"}


@router.get("/{key}/nutrient-plan")
def get_nutrient_plan(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    plant_service: PlantInstanceService = Depends(get_plant_instance_service),
    plan_service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    plant_service.get_plant(key, tenant_key=ctx.tenant_key)
    plan = plan_service.get_plant_plan(key)
    if plan is None:
        return None
    return plan.model_dump(by_alias=False)


@router.delete("/{key}/nutrient-plan", status_code=204)
def remove_nutrient_plan(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    plant_service: PlantInstanceService = Depends(get_plant_instance_service),
    plan_service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    plant_service.get_plant(key, tenant_key=ctx.tenant_key)
    plan_service.remove_plant_plan(key)


@router.get("/{key}/current-dosages")
def get_current_dosages(
    key: str,
    current_week: int = Query(ge=1),
    ctx: TenantContext = Depends(get_current_tenant),
    plant_service: PlantInstanceService = Depends(get_plant_instance_service),
    plan_service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    plant = plant_service.get_plant(key, tenant_key=ctx.tenant_key)
    phase_name = plant_service.resolve_phase_name(plant.current_phase_key or "")
    result = plan_service.get_current_dosages(key, phase_name, current_week)
    if result is None:
        return {"message": "No plan or matching entry found"}
    return result


@router.get("/{key}/active-channels", response_model=list[ActiveChannelResponse])
def get_active_channels(
    key: str,
    current_week: int = Query(ge=1),
    ctx: TenantContext = Depends(get_current_tenant),
    plant_service: PlantInstanceService = Depends(get_plant_instance_service),
    plan_service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    plant = plant_service.get_plant(key, tenant_key=ctx.tenant_key)
    plan = plan_service.get_plant_plan(key)
    if plan is None or plan.key is None:
        return []
    phase_name = plant_service.resolve_phase_name(plant.current_phase_key or "")
    channels = plan_service.get_active_channels_for_plan(plan.key, phase_name, current_week)
    return channels


@router.get("/{key}/planting-runs")
def get_plant_runs(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    plant_service: PlantInstanceService = Depends(get_plant_instance_service),
    run_service: PlantingRunService = Depends(get_planting_run_service),
):
    plant_service.get_plant(key, tenant_key=ctx.tenant_key)
    runs = run_service.get_runs_for_plant(key)
    return [
        {
            "key": r.key,
            "name": r.name,
            "status": r.status.value if hasattr(r.status, "value") else r.status,
        }
        for r in runs
    ]
