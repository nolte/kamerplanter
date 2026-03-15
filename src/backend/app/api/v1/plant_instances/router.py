from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Query

from app.api.v1.plant_instances.schemas import (
    ActiveChannelResponse,
    AssignNutrientPlanRequest,
    PlantCreate,
    PlantResponse,
    ValidatePlantingRequest,
    ValidatePlantingResponse,
)
from app.common.dependencies import get_nutrient_plan_service, get_plant_instance_service, get_planting_run_service
from app.domain.models.plant_instance import PlantInstance

if TYPE_CHECKING:
    from app.domain.services.nutrient_plan_service import NutrientPlanService
    from app.domain.services.plant_instance_service import PlantInstanceService
    from app.domain.services.planting_run_service import PlantingRunService

router = APIRouter(prefix="/plant-instances", tags=["plant-instances"])


def _to_response(p: PlantInstance, service: PlantInstanceService) -> PlantResponse:
    """Convert PlantInstance to PlantResponse, resolving phase name from key."""
    phase_name = service.resolve_phase_name(p.current_phase_key) if p.current_phase_key else ""
    return PlantResponse(
        key=p.key or "",
        current_phase=phase_name,
        **p.model_dump(exclude={"key"}),
    )


@router.get("", response_model=list[PlantResponse])
def list_plants(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: PlantInstanceService = Depends(get_plant_instance_service),
):
    items, total = service.list_plants(offset, limit)
    return [_to_response(p, service) for p in items]

@router.get("/{key}", response_model=PlantResponse)
def get_plant(key: str, service: PlantInstanceService = Depends(get_plant_instance_service)):
    p = service.get_plant(key)
    return _to_response(p, service)

@router.post("", response_model=PlantResponse, status_code=201)
def create_plant(body: PlantCreate, service: PlantInstanceService = Depends(get_plant_instance_service)):
    plant = PlantInstance(**body.model_dump())
    created = service.create_plant(plant)
    return _to_response(created, service)

@router.put("/{key}", response_model=PlantResponse)
def update_plant(key: str, body: PlantCreate, service: PlantInstanceService = Depends(get_plant_instance_service)):
    plant = PlantInstance(**body.model_dump())
    updated = service.update_plant(key, plant)
    return _to_response(updated, service)

@router.post("/{key}/remove", response_model=PlantResponse)
def remove_plant(key: str, service: PlantInstanceService = Depends(get_plant_instance_service)):
    removed = service.remove_plant(key)
    return _to_response(removed, service)

@router.post("/slots/{slot_key}/validate-planting", response_model=ValidatePlantingResponse)
def validate_planting(
    slot_key: str, body: ValidatePlantingRequest, service: PlantInstanceService = Depends(get_plant_instance_service),
):
    result = service.validate_planting(slot_key, body.species_key)
    return ValidatePlantingResponse(**result)


# ── Nutrient Plan assignment ─────────────────────────────────────────

@router.post("/{key}/nutrient-plan", status_code=201)
def assign_nutrient_plan(
    key: str,
    body: AssignNutrientPlanRequest,
    plant_service: PlantInstanceService = Depends(get_plant_instance_service),
    plan_service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    plant_service.get_plant(key)  # ensure exists
    plan_service.assign_to_plant(key, body.plan_key, body.assigned_by)
    return {"status": "assigned"}


@router.get("/{key}/nutrient-plan")
def get_nutrient_plan(
    key: str,
    plant_service: PlantInstanceService = Depends(get_plant_instance_service),
    plan_service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    plant_service.get_plant(key)
    plan = plan_service.get_plant_plan(key)
    if plan is None:
        return None
    return plan.model_dump(by_alias=False)


@router.delete("/{key}/nutrient-plan", status_code=204)
def remove_nutrient_plan(
    key: str,
    plant_service: PlantInstanceService = Depends(get_plant_instance_service),
    plan_service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    plant_service.get_plant(key)
    plan_service.remove_plant_plan(key)


@router.get("/{key}/current-dosages")
def get_current_dosages(
    key: str,
    current_week: int = Query(ge=1),
    plant_service: PlantInstanceService = Depends(get_plant_instance_service),
    plan_service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    plant = plant_service.get_plant(key)
    phase_name = plant_service.resolve_phase_name(plant.current_phase_key or "")
    result = plan_service.get_current_dosages(key, phase_name, current_week)
    if result is None:
        return {"message": "No plan or matching entry found"}
    return result


@router.get("/{key}/active-channels", response_model=list[ActiveChannelResponse])
def get_active_channels(
    key: str,
    current_week: int = Query(ge=1),
    plant_service: PlantInstanceService = Depends(get_plant_instance_service),
    plan_service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    """Return active delivery channels for a plant instance's current phase."""
    plant = plant_service.get_plant(key)
    plan = plan_service.get_plant_plan(key)
    if plan is None or plan.key is None:
        return []
    phase_name = plant_service.resolve_phase_name(plant.current_phase_key or "")
    channels = plan_service.get_active_channels_for_plan(
        plan.key, phase_name, current_week,
    )
    return channels


# ── Planting Run lookup ──────────────────────────────────────────────

@router.get("/{key}/planting-runs")
def get_plant_runs(
    key: str,
    plant_service: PlantInstanceService = Depends(get_plant_instance_service),
    run_service: PlantingRunService = Depends(get_planting_run_service),
):
    plant_service.get_plant(key)  # ensure plant exists
    runs = run_service.get_runs_for_plant(key)
    return [
        {
            "key": r.key,
            "name": r.name,
            "status": r.status.value if hasattr(r.status, "value") else r.status,
        }
        for r in runs
    ]
