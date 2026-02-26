from fastapi import APIRouter, Depends, Query

from app.api.v1.plant_instances.schemas import (
    AssignNutrientPlanRequest,
    PlantCreate,
    PlantResponse,
    ValidatePlantingRequest,
    ValidatePlantingResponse,
)
from app.common.dependencies import get_nutrient_plan_service, get_plant_instance_service
from app.domain.models.plant_instance import PlantInstance
from app.domain.services.nutrient_plan_service import NutrientPlanService
from app.domain.services.plant_instance_service import PlantInstanceService

router = APIRouter(prefix="/plant-instances", tags=["plant-instances"])

@router.get("", response_model=list[PlantResponse])
def list_plants(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: PlantInstanceService = Depends(get_plant_instance_service),
):
    items, total = service.list_plants(offset, limit)
    return [PlantResponse(key=p.key or "", **p.model_dump(exclude={"key"})) for p in items]

@router.get("/{key}", response_model=PlantResponse)
def get_plant(key: str, service: PlantInstanceService = Depends(get_plant_instance_service)):
    p = service.get_plant(key)
    return PlantResponse(key=p.key or "", **p.model_dump(exclude={"key"}))

@router.post("", response_model=PlantResponse, status_code=201)
def create_plant(body: PlantCreate, service: PlantInstanceService = Depends(get_plant_instance_service)):
    plant = PlantInstance(**body.model_dump())
    created = service.create_plant(plant)
    return PlantResponse(key=created.key or "", **created.model_dump(exclude={"key"}))

@router.put("/{key}", response_model=PlantResponse)
def update_plant(key: str, body: PlantCreate, service: PlantInstanceService = Depends(get_plant_instance_service)):
    plant = PlantInstance(**body.model_dump())
    updated = service.update_plant(key, plant)
    return PlantResponse(key=updated.key or "", **updated.model_dump(exclude={"key"}))

@router.post("/{key}/remove", response_model=PlantResponse)
def remove_plant(key: str, service: PlantInstanceService = Depends(get_plant_instance_service)):
    removed = service.remove_plant(key)
    return PlantResponse(key=removed.key or "", **removed.model_dump(exclude={"key"}))

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
    return {"key": plan.key, "name": plan.name}


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
    result = plan_service.get_current_dosages(key, plant.current_phase, current_week)
    if result is None:
        return {"message": "No plan or matching entry found"}
    return result
