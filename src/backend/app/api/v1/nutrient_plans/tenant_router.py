from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.api.mapping import to_response
from app.api.v1.nutrient_plans.schemas import (
    CalculateDosagesRequest,
    CalculateDosagesResponse,
    ChannelFertilizerAssignedResponse,
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
from app.common.enums import DataOrigin
from app.common.openapi_responses import NOT_FOUND_RESPONSE
from app.common.pagination import PaginationParams, get_pagination
from app.domain.models.nutrient_plan import NutrientPlan, NutrientPlanPhaseEntry
from app.domain.models.tenant_context import TenantContext
from app.domain.services.nutrient_plan_service import NutrientPlanService

router = APIRouter(prefix="/nutrient-plans", tags=["nutrient-plans"], responses=NOT_FOUND_RESPONSE)


def _plan_response(p: NutrientPlan) -> NutrientPlanResponse:
    # Provenance is derived from tenant ownership: the shared catalog uses an
    # empty tenant_key (system), tenant-created plans carry their tenant_key.
    origin = DataOrigin.TENANT if p.tenant_key else DataOrigin.SYSTEM
    return to_response(p, NutrientPlanResponse, origin=origin)


def _entry_response(e: NutrientPlanPhaseEntry) -> PhaseEntryResponse:
    return to_response(e, PhaseEntryResponse)


@router.get("", response_model=list[NutrientPlanResponse])
def list_plans(
    pagination: PaginationParams = Depends(get_pagination),
    recommended_substrate_type: str | None = Query(default=None, description="Filter by recommended substrate type."),
    is_template: bool | None = Query(default=None, description="Filter by template flag."),
    ctx: TenantContext = Depends(get_current_tenant),
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    """List the tenant's nutrient plans (paginated, optionally filtered)."""
    filters: dict = {}
    if recommended_substrate_type:
        filters["recommended_substrate_type"] = recommended_substrate_type
    if is_template is not None:
        filters["is_template"] = is_template
    items, _total = service.list_plans(pagination.offset, pagination.limit, filters or None, tenant_key=ctx.tenant_key)
    return [_plan_response(p) for p in items]


@router.post("", response_model=NutrientPlanResponse, status_code=201)
def create_plan(
    body: NutrientPlanCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    """Create a nutrient plan for the tenant."""
    plan = NutrientPlan(**body.model_dump(), tenant_key=ctx.tenant_key)
    created = service.create_plan(plan)
    return _plan_response(created)


@router.get("/{key}", response_model=NutrientPlanResponse)
def get_plan(
    key: Annotated[str, Path(description="Document key of the nutrient plan.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    """Return a single nutrient plan by key."""
    p = service.get_plan(key, tenant_key=ctx.tenant_key)
    return _plan_response(p)


@router.put("/{key}", response_model=NutrientPlanResponse)
def update_plan(
    key: Annotated[str, Path(description="Document key of the nutrient plan.")],
    body: NutrientPlanUpdate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    """Update a nutrient plan."""
    service.get_plan(key, tenant_key=ctx.tenant_key, for_write=True)
    data = body.model_dump(exclude_none=True)
    updated = service.update_plan(key, data)
    return _plan_response(updated)


@router.delete("/{key}", status_code=204)
def delete_plan(
    key: Annotated[str, Path(description="Document key of the nutrient plan.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    """Delete a nutrient plan."""
    service.get_plan(key, tenant_key=ctx.tenant_key, for_write=True)
    service.delete_plan(key)


@router.post("/{key}/clone", response_model=NutrientPlanResponse, status_code=201)
def clone_plan(
    key: Annotated[str, Path(description="Document key of the nutrient plan to clone.")],
    body: CloneRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    """Clone a nutrient plan into a new tenant-owned plan."""
    service.get_plan(key, tenant_key=ctx.tenant_key)
    cloned = service.clone_plan(key, body.new_name, body.author, tenant_key=ctx.tenant_key)
    return _plan_response(cloned)


@router.get("/{key}/validate")
def validate_plan(
    key: Annotated[str, Path(description="Document key of the nutrient plan.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    """Validate a nutrient plan and return any issues found."""
    service.get_plan(key, tenant_key=ctx.tenant_key)
    return service.validate_plan(key)


@router.get("/{key}/entries", response_model=list[PhaseEntryResponse])
def list_entries(
    key: Annotated[str, Path(description="Document key of the nutrient plan.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    """List a nutrient plan's phase entries."""
    service.get_plan(key, tenant_key=ctx.tenant_key)
    entries = service.get_phase_entries(key)
    return [_entry_response(e) for e in entries]


@router.post("/{key}/entries", response_model=PhaseEntryResponse, status_code=201)
def create_entry(
    key: Annotated[str, Path(description="Document key of the nutrient plan.")],
    body: PhaseEntryCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    """Add a phase entry to a nutrient plan."""
    service.get_plan(key, tenant_key=ctx.tenant_key, for_write=True)
    entry = NutrientPlanPhaseEntry(plan_key=key, **body.model_dump())
    created = service.create_phase_entry(key, entry)
    return _entry_response(created)


@router.put("/{key}/entries/{ek}", response_model=PhaseEntryResponse)
def update_entry(
    key: Annotated[str, Path(description="Document key of the nutrient plan.")],
    ek: Annotated[str, Path(description="Document key of the phase entry.")],
    body: PhaseEntryUpdate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    """Update a nutrient plan's phase entry."""
    service.get_plan(key, tenant_key=ctx.tenant_key, for_write=True)
    data = body.model_dump(exclude_none=True)
    updated = service.update_phase_entry(ek, data)
    return _entry_response(updated)


@router.delete("/{key}/entries/{ek}", status_code=204)
def delete_entry(
    key: Annotated[str, Path(description="Document key of the nutrient plan.")],
    ek: Annotated[str, Path(description="Document key of the phase entry.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    """Delete a nutrient plan's phase entry."""
    service.get_plan(key, tenant_key=ctx.tenant_key, for_write=True)
    service.delete_phase_entry(ek)


@router.get(
    "/{key}/water-mix-recommendations",
    response_model=WaterMixBatchRecommendationResponse,
)
def get_water_mix_recommendations_batch(
    key: Annotated[str, Path(description="Document key of the nutrient plan.")],
    site_key: str = Query(..., description="Site key with water source configuration"),
    substrate_type: str | None = Query(None, description="Override substrate type"),
    ctx: TenantContext = Depends(get_current_tenant),
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    """Return water-mix recommendations for every phase of a nutrient plan."""
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
    key: Annotated[str, Path(description="Document key of the nutrient plan.")],
    sequence_order: Annotated[int, Path(description="Sequence order of the phase entry within the plan.")],
    site_key: str = Query(..., description="Site key with water source configuration"),
    substrate_type: str | None = Query(None, description="Override substrate type"),
    ctx: TenantContext = Depends(get_current_tenant),
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    """Return the water-mix recommendation for a single plan phase."""
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
    key: Annotated[str, Path(description="Document key of the nutrient plan.")],
    body: CalculateDosagesRequest,
    location_key: str | None = Query(default=None, description="Location key used to scale per-area dosing."),
    plant_count: int | None = Query(default=None, description="Plant count used to scale per-plant dosing."),
    ctx: TenantContext = Depends(get_current_tenant),
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    """Calculate concrete fertilizer dosages for a plan phase."""
    result = service.calculate_dosages(
        tenant_key=ctx.tenant_key,
        plan_key=key,
        sequence_order=body.phase_sequence_order,
        site_key=body.site_key,
        volume_liters=body.volume_liters,
        channel_id=body.channel_id,
        ro_percent_override=body.ro_percent_override,
        location_key=location_key,
        plant_count=plant_count,
    )
    return result.model_dump()


@router.post(
    "/entries/{ek}/channels/{cid}/fertilizers",
    status_code=201,
    response_model=ChannelFertilizerAssignedResponse,
)
def assign_channel_fertilizer(
    ek: Annotated[str, Path(description="Document key of the phase entry.")],
    cid: Annotated[str, Path(description="Identifier of the delivery channel.")],
    body: ChannelFertilizerAssignRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    """Assign a fertilizer to a phase entry's delivery channel."""
    service.add_fertilizer_to_channel(ek, cid, body.fertilizer_key, body.ml_per_liter, body.optional)
    return {"status": "assigned"}


@router.delete("/entries/{ek}/channels/{cid}/fertilizers/{fk}", status_code=204)
def remove_channel_fertilizer(
    ek: Annotated[str, Path(description="Document key of the phase entry.")],
    cid: Annotated[str, Path(description="Identifier of the delivery channel.")],
    fk: Annotated[str, Path(description="Document key of the fertilizer to remove.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    """Remove a fertilizer from a phase entry's delivery channel."""
    service.remove_fertilizer_from_channel(ek, cid, fk)
