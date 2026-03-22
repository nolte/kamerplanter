from fastapi import APIRouter, Depends, Query

from app.api.v1.nutrient_plans.schemas import (
    CalculateDosagesRequest,
    CalculateDosagesResponse,
    ChannelFertilizerAssignRequest,
    CloneRequest,
    NutrientPlanCreate,
    NutrientPlanResponse,
    NutrientPlanUpdate,
    PhaseEntryCreate,
    PhaseEntryResponse,
    PhaseEntryUpdate,
    WaterMixBatchRecommendationResponse,
    WaterMixRecommendationResponse,
)
from app.common.auth import get_current_tenant
from app.common.dependencies import get_nutrient_plan_service
from app.domain.models.nutrient_plan import NutrientPlan, NutrientPlanPhaseEntry
from app.domain.models.tenant_context import TenantContext
from app.domain.services.nutrient_plan_service import NutrientPlanService

router = APIRouter(prefix="/nutrient-plans", tags=["nutrient-plans"])


def _plan_response(p: NutrientPlan) -> NutrientPlanResponse:
    return NutrientPlanResponse(key=p.key or "", **p.model_dump(exclude={"key"}))


def _entry_response(e: NutrientPlanPhaseEntry) -> PhaseEntryResponse:
    return PhaseEntryResponse(key=e.key or "", **e.model_dump(exclude={"key"}))


@router.get("", response_model=list[NutrientPlanResponse])
def list_plans(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    recommended_substrate_type: str | None = None,
    is_template: bool | None = None,
    ctx: TenantContext = Depends(get_current_tenant),
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    filters: dict = {}
    if recommended_substrate_type:
        filters["recommended_substrate_type"] = recommended_substrate_type
    if is_template is not None:
        filters["is_template"] = is_template
    items, _total = service.list_plans(offset, limit, filters or None, tenant_key=ctx.tenant_key)
    return [_plan_response(p) for p in items]


@router.post("", response_model=NutrientPlanResponse, status_code=201)
def create_plan(
    body: NutrientPlanCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    plan = NutrientPlan(**body.model_dump(), tenant_key=ctx.tenant_key)
    created = service.create_plan(plan)
    return _plan_response(created)


@router.get("/{key}", response_model=NutrientPlanResponse)
def get_plan(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    p = service.get_plan(key, tenant_key=ctx.tenant_key)
    return _plan_response(p)


@router.put("/{key}", response_model=NutrientPlanResponse)
def update_plan(
    key: str,
    body: NutrientPlanUpdate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    service.get_plan(key, tenant_key=ctx.tenant_key)
    data = body.model_dump(exclude_none=True)
    updated = service.update_plan(key, data)
    return _plan_response(updated)


@router.delete("/{key}", status_code=204)
def delete_plan(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    service.get_plan(key, tenant_key=ctx.tenant_key)
    service.delete_plan(key)


@router.post("/{key}/clone", response_model=NutrientPlanResponse, status_code=201)
def clone_plan(
    key: str,
    body: CloneRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    service.get_plan(key, tenant_key=ctx.tenant_key)
    cloned = service.clone_plan(key, body.new_name, body.author)
    return _plan_response(cloned)


@router.get("/{key}/validate")
def validate_plan(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    service.get_plan(key, tenant_key=ctx.tenant_key)
    return service.validate_plan(key)


@router.get("/{key}/entries", response_model=list[PhaseEntryResponse])
def list_entries(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    service.get_plan(key, tenant_key=ctx.tenant_key)
    entries = service.get_phase_entries(key)
    return [_entry_response(e) for e in entries]


@router.post("/{key}/entries", response_model=PhaseEntryResponse, status_code=201)
def create_entry(
    key: str,
    body: PhaseEntryCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    service.get_plan(key, tenant_key=ctx.tenant_key)
    entry = NutrientPlanPhaseEntry(plan_key=key, **body.model_dump())
    created = service.create_phase_entry(key, entry)
    return _entry_response(created)


@router.put("/{key}/entries/{ek}", response_model=PhaseEntryResponse)
def update_entry(
    key: str,
    ek: str,
    body: PhaseEntryUpdate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    service.get_plan(key, tenant_key=ctx.tenant_key)
    data = body.model_dump(exclude_none=True)
    updated = service.update_phase_entry(ek, data)
    return _entry_response(updated)


@router.delete("/{key}/entries/{ek}", status_code=204)
def delete_entry(
    key: str,
    ek: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    service.get_plan(key, tenant_key=ctx.tenant_key)
    service.delete_phase_entry(ek)


@router.get(
    "/{key}/water-mix-recommendations",
    response_model=WaterMixBatchRecommendationResponse,
)
def get_water_mix_recommendations_batch(
    key: str,
    site_key: str = Query(..., description="Site key with water source configuration"),
    substrate_type: str | None = Query(None, description="Override substrate type"),
    ctx: TenantContext = Depends(get_current_tenant),
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    return service.get_water_mix_recommendations_batch(
        tenant_key=ctx.tenant_key,
        plan_key=key,
        site_key=site_key,
        substrate_type_override=substrate_type,
    )


@router.get(
    "/{key}/entries/{sequence_order}/water-mix-recommendation",
    response_model=WaterMixRecommendationResponse,
)
def get_water_mix_recommendation(
    key: str,
    sequence_order: int,
    site_key: str = Query(..., description="Site key with water source configuration"),
    substrate_type: str | None = Query(None, description="Override substrate type"),
    ctx: TenantContext = Depends(get_current_tenant),
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    return service.get_water_mix_recommendation(
        tenant_key=ctx.tenant_key,
        plan_key=key,
        sequence_order=sequence_order,
        site_key=site_key,
        substrate_type_override=substrate_type,
    )


@router.post(
    "/{key}/calculate-dosages",
    response_model=CalculateDosagesResponse,
)
def calculate_dosages(
    key: str,
    body: CalculateDosagesRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    result = service.calculate_dosages(
        tenant_key=ctx.tenant_key,
        plan_key=key,
        sequence_order=body.phase_sequence_order,
        site_key=body.site_key,
        volume_liters=body.volume_liters,
        channel_id=body.channel_id,
        ro_percent_override=body.ro_percent_override,
    )
    return result.model_dump()


@router.post("/entries/{ek}/channels/{cid}/fertilizers", status_code=201)
def assign_channel_fertilizer(
    ek: str,
    cid: str,
    body: ChannelFertilizerAssignRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    service.add_fertilizer_to_channel(ek, cid, body.fertilizer_key, body.ml_per_liter, body.optional)
    return {"status": "assigned"}


@router.delete("/entries/{ek}/channels/{cid}/fertilizers/{fk}", status_code=204)
def remove_channel_fertilizer(
    ek: str,
    cid: str,
    fk: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    service.remove_fertilizer_from_channel(ek, cid, fk)
