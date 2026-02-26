from fastapi import APIRouter, Depends, Query

from app.api.v1.nutrient_plans.schemas import (
    CloneRequest,
    FertilizerAssignRequest,
    NutrientPlanCreate,
    NutrientPlanResponse,
    NutrientPlanUpdate,
    PhaseEntryCreate,
    PhaseEntryResponse,
    PhaseEntryUpdate,
)
from app.common.dependencies import get_nutrient_plan_service
from app.domain.models.nutrient_plan import NutrientPlan, NutrientPlanPhaseEntry
from app.domain.services.nutrient_plan_service import NutrientPlanService

router = APIRouter(prefix="/nutrient-plans", tags=["nutrient-plans"])


def _plan_response(p: NutrientPlan) -> NutrientPlanResponse:
    return NutrientPlanResponse(key=p.key or "", **p.model_dump(exclude={"key"}))


def _entry_response(e: NutrientPlanPhaseEntry) -> PhaseEntryResponse:
    return PhaseEntryResponse(key=e.key or "", **e.model_dump(exclude={"key"}))


# ── Plan CRUD ────────────────────────────────────────────────────────

@router.get("", response_model=list[NutrientPlanResponse])
def list_plans(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    recommended_substrate_type: str | None = None,
    is_template: bool | None = None,
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    filters: dict = {}
    if recommended_substrate_type:
        filters["recommended_substrate_type"] = recommended_substrate_type
    if is_template is not None:
        filters["is_template"] = is_template
    items, _total = service.list_plans(offset, limit, filters or None)
    return [_plan_response(p) for p in items]


@router.post("", response_model=NutrientPlanResponse, status_code=201)
def create_plan(
    body: NutrientPlanCreate,
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    plan = NutrientPlan(**body.model_dump())
    created = service.create_plan(plan)
    return _plan_response(created)


@router.get("/{key}", response_model=NutrientPlanResponse)
def get_plan(key: str, service: NutrientPlanService = Depends(get_nutrient_plan_service)):
    p = service.get_plan(key)
    return _plan_response(p)


@router.put("/{key}", response_model=NutrientPlanResponse)
def update_plan(
    key: str,
    body: NutrientPlanUpdate,
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    data = body.model_dump(exclude_none=True)
    updated = service.update_plan(key, data)
    return _plan_response(updated)


@router.delete("/{key}", status_code=204)
def delete_plan(key: str, service: NutrientPlanService = Depends(get_nutrient_plan_service)):
    service.delete_plan(key)


# ── Clone + Validate ─────────────────────────────────────────────────

@router.post("/{key}/clone", response_model=NutrientPlanResponse, status_code=201)
def clone_plan(
    key: str,
    body: CloneRequest,
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    cloned = service.clone_plan(key, body.new_name, body.author)
    return _plan_response(cloned)


@router.get("/{key}/validate")
def validate_plan(key: str, service: NutrientPlanService = Depends(get_nutrient_plan_service)):
    return service.validate_plan(key)


# ── Phase entries ────────────────────────────────────────────────────

@router.get("/{key}/entries", response_model=list[PhaseEntryResponse])
def list_entries(key: str, service: NutrientPlanService = Depends(get_nutrient_plan_service)):
    entries = service.get_phase_entries(key)
    return [_entry_response(e) for e in entries]


@router.post("/{key}/entries", response_model=PhaseEntryResponse, status_code=201)
def create_entry(
    key: str,
    body: PhaseEntryCreate,
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    entry = NutrientPlanPhaseEntry(plan_key=key, **body.model_dump())
    created = service.create_phase_entry(key, entry)
    return _entry_response(created)


@router.put("/{key}/entries/{ek}", response_model=PhaseEntryResponse)
def update_entry(
    key: str,
    ek: str,
    body: PhaseEntryUpdate,
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    data = body.model_dump(exclude_none=True)
    updated = service.update_phase_entry(ek, data)
    return _entry_response(updated)


@router.delete("/{key}/entries/{ek}", status_code=204)
def delete_entry(
    key: str,
    ek: str,
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    service.delete_phase_entry(ek)


# ── Fertilizer assignment on entries ─────────────────────────────────

@router.post("/entries/{ek}/fertilizers", status_code=201)
def assign_fertilizer(
    ek: str,
    body: FertilizerAssignRequest,
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    service.add_fertilizer_to_entry(ek, body.fertilizer_key, body.ml_per_liter, body.optional)
    return {"status": "assigned"}


@router.delete("/entries/{ek}/fertilizers/{fk}", status_code=204)
def remove_fertilizer(
    ek: str,
    fk: str,
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    service.remove_fertilizer_from_entry(ek, fk)
