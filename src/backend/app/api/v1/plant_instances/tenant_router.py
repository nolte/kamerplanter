from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.api.mapping import to_response
from app.api.v1.plant_instances.schemas import (
    ActiveChannelResponse,
    AssignNutrientPlanRequest,
    AssignNutrientPlanStatusResponse,
    CultivarSummary,
    PlantCreate,
    PlantInstanceInPhaseResponse,
    PlantInstancesInPhaseResponse,
    PlantResponse,
    PlantRunSummaryResponse,
    RemovePlantRequest,
    SpeciesSummary,
    SurvivalStatsResponse,
    ValidatePlantingRequest,
    ValidatePlantingResponse,
)
from app.common.auth import get_current_tenant
from app.common.dependencies import get_nutrient_plan_service, get_plant_instance_service, get_planting_run_service
from app.common.openapi_responses import NOT_FOUND_RESPONSE
from app.common.pagination import PaginationParams, get_pagination
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.tenant_context import TenantContext
from app.domain.services.nutrient_plan_service import NutrientPlanService
from app.domain.services.plant_instance_service import PlantInstanceService
from app.domain.services.planting_run_service import PlantingRunService

router = APIRouter(prefix="/plant-instances", tags=["plant-instances"], responses=NOT_FOUND_RESPONSE)


def _to_response(p: PlantInstance, service: PlantInstanceService) -> PlantResponse:
    """Convert PlantInstance to PlantResponse, resolving phase name and
    denormalized species/cultivar labels from their keys."""
    phase_name = service.resolve_phase_name(p.current_phase_key) if p.current_phase_key else ""
    species = service.resolve_species(p.species_key)
    cultivar = service.resolve_cultivar(p.cultivar_key)
    return to_response(
        p,
        PlantResponse,
        current_phase=phase_name,
        species=(
            SpeciesSummary(scientific_name=species.scientific_name, common_names=species.common_names)
            if species
            else None
        ),
        cultivar=CultivarSummary(name=cultivar.name) if cultivar else None,
    )


@router.get("", response_model=list[PlantResponse])
def list_plants(
    pagination: PaginationParams = Depends(get_pagination),
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantInstanceService = Depends(get_plant_instance_service),
):
    """List the tenant's plant instances (paginated)."""
    items, _total = service.list_plants(pagination.offset, pagination.limit, tenant_key=ctx.tenant_key)
    return [_to_response(p, service) for p in items]


@router.get("/survival-stats", response_model=SurvivalStatsResponse)
def get_survival_stats(
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantInstanceService = Depends(get_plant_instance_service),
):
    """Survival-rate / failure-cause analytics for the tenant's plants (REQ-003 G1).

    Declared before ``/{key}`` so the literal path is not captured by the
    plant-key path parameter.
    """
    stats = service.get_survival_stats(ctx.tenant_key)
    return SurvivalStatsResponse(**stats.model_dump())


@router.get(
    "/by-phase-definition/{phase_definition_key}",
    response_model=PlantInstancesInPhaseResponse,
)
def list_plants_in_phase_definition(
    phase_definition_key: Annotated[str, Path(description="Document key of the phase definition.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantInstanceService = Depends(get_plant_instance_service),
):
    """List the tenant's *active* plant instances currently in a phase definition (FIX-01 R1/R8).

    Read-only and tenant-scoped: only the caller's tenant's instances are returned
    (SEC-001), and only active ones (``removed_on == null``). An empty list is a
    valid result (R4). Declared before ``/{key}`` so the two-segment literal path is
    matched here and not captured by the plant-key path parameter.
    """
    rows = service.list_active_in_phase_definition(ctx.tenant_key, phase_definition_key)
    items = [PlantInstanceInPhaseResponse(**row) for row in rows]
    return PlantInstancesInPhaseResponse(total=len(items), items=items)


@router.get("/{key}", response_model=PlantResponse)
def get_plant(
    key: Annotated[str, Path(description="Document key of the plant instance.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantInstanceService = Depends(get_plant_instance_service),
):
    """Return a single plant instance by key."""
    p = service.get_plant(key, tenant_key=ctx.tenant_key)
    return _to_response(p, service)


@router.post("", response_model=PlantResponse, status_code=201)
def create_plant(
    body: PlantCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantInstanceService = Depends(get_plant_instance_service),
):
    """Create a plant instance for the tenant."""
    plant = PlantInstance(**body.model_dump(), tenant_key=ctx.tenant_key)
    created = service.create_plant(plant)
    return _to_response(created, service)


@router.put("/{key}", response_model=PlantResponse)
def update_plant(
    key: Annotated[str, Path(description="Document key of the plant instance.")],
    body: PlantCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantInstanceService = Depends(get_plant_instance_service),
):
    """Update the user-editable fields of a plant instance."""
    existing = service.get_plant(key, tenant_key=ctx.tenant_key)
    # Merge: keep server-managed fields from existing, apply user-editable fields from body
    update_data = body.model_dump()
    existing.instance_id = update_data["instance_id"]
    existing.species_key = update_data["species_key"]
    existing.cultivar_key = update_data.get("cultivar_key")
    existing.site_key = update_data.get("site_key")
    existing.location_key = update_data.get("location_key")
    existing.slot_key = update_data.get("slot_key")
    existing.substrate_batch_key = update_data.get("substrate_batch_key")
    existing.substrate_key = update_data.get("substrate_key")
    existing.plant_name = update_data.get("plant_name")
    existing.planted_on = update_data["planted_on"]
    existing.container_volume_liters = update_data.get("container_volume_liters")
    existing.substrate_type_override = update_data.get("substrate_type_override")
    # ADR-006 E1 — per-instance cultivation cycle override (None = same as the species).
    existing.cultivation_cycle_type = update_data.get("cultivation_cycle_type")
    updated = service.update_plant(key, existing)
    return _to_response(updated, service)


@router.post("/{key}/remove", response_model=PlantResponse)
def remove_plant(
    key: Annotated[str, Path(description="Document key of the plant instance.")],
    body: RemovePlantRequest | None = None,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantInstanceService = Depends(get_plant_instance_service),
):
    """Mark a plant instance as removed, recording the termination reason."""
    removed = service.remove_plant(
        key,
        termination_type=body.termination_type if body else None,
        termination_cause=body.termination_cause if body else None,
        tenant_key=ctx.tenant_key,
    )
    return _to_response(removed, service)


@router.post("/slots/{slot_key}/validate-planting", response_model=ValidatePlantingResponse)
def validate_planting(
    slot_key: Annotated[str, Path(description="Document key of the slot to plant into.")],
    body: ValidatePlantingRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantInstanceService = Depends(get_plant_instance_service),
):
    """Validate whether a species may be planted into a slot.

    A ``slot_key`` belonging to another tenant produces no findings — the slot
    history and neighbourhood reads behind this are tenant-scoped (#927).
    """
    result = service.validate_planting(slot_key, body.species_key, tenant_key=ctx.tenant_key)
    return ValidatePlantingResponse(**result)


@router.post("/{key}/nutrient-plan", response_model=AssignNutrientPlanStatusResponse, status_code=201)
def assign_nutrient_plan(
    key: Annotated[str, Path(description="Document key of the plant instance.")],
    body: AssignNutrientPlanRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    plant_service: PlantInstanceService = Depends(get_plant_instance_service),
    plan_service: NutrientPlanService = Depends(get_nutrient_plan_service),
) -> AssignNutrientPlanStatusResponse:
    """Assign a nutrient plan to a plant instance."""
    plant_service.get_plant(key, tenant_key=ctx.tenant_key)
    plan_service.assign_to_plant(key, body.plan_key, body.assigned_by, tenant_key=ctx.tenant_key)
    return AssignNutrientPlanStatusResponse(status="assigned")


@router.get("/{key}/nutrient-plan")
def get_nutrient_plan(
    key: Annotated[str, Path(description="Document key of the plant instance.")],
    ctx: TenantContext = Depends(get_current_tenant),
    plant_service: PlantInstanceService = Depends(get_plant_instance_service),
    plan_service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    """Return the nutrient plan assigned to a plant instance, or ``null``."""
    plant_service.get_plant(key, tenant_key=ctx.tenant_key)
    plan = plan_service.get_plant_plan(key, tenant_key=ctx.tenant_key)
    if plan is None:
        return None
    return plan.model_dump(by_alias=False)


@router.delete("/{key}/nutrient-plan", status_code=204)
def remove_nutrient_plan(
    key: Annotated[str, Path(description="Document key of the plant instance.")],
    ctx: TenantContext = Depends(get_current_tenant),
    plant_service: PlantInstanceService = Depends(get_plant_instance_service),
    plan_service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    """Remove the nutrient plan assigned to a plant instance."""
    plant_service.get_plant(key, tenant_key=ctx.tenant_key)
    plan_service.remove_plant_plan(key)


@router.get("/{key}/current-dosages")
def get_current_dosages(
    key: Annotated[str, Path(description="Document key of the plant instance.")],
    current_week: int = Query(ge=1, description="1-based week within the current phase to compute dosages for."),
    ctx: TenantContext = Depends(get_current_tenant),
    plant_service: PlantInstanceService = Depends(get_plant_instance_service),
    plan_service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    """Return the current per-channel dosages for a plant instance's active plan."""
    plant = plant_service.get_plant(key, tenant_key=ctx.tenant_key)
    phase_name = plant_service.resolve_phase_name(plant.current_phase_key or "")
    result = plan_service.get_current_dosages(key, phase_name, current_week, tenant_key=ctx.tenant_key)
    if result is None:
        return {"message": "No plan or matching entry found"}
    return result


@router.get("/{key}/active-channels", response_model=list[ActiveChannelResponse])
def get_active_channels(
    key: Annotated[str, Path(description="Document key of the plant instance.")],
    current_week: int = Query(ge=1, description="1-based week within the current phase to evaluate."),
    ctx: TenantContext = Depends(get_current_tenant),
    plant_service: PlantInstanceService = Depends(get_plant_instance_service),
    plan_service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    """List the active nutrient channels for a plant instance in the given week."""
    plant = plant_service.get_plant(key, tenant_key=ctx.tenant_key)
    plan = plan_service.get_plant_plan(key, tenant_key=ctx.tenant_key)
    if plan is None or plan.key is None:
        return []
    phase_name = plant_service.resolve_phase_name(plant.current_phase_key or "")
    channels = plan_service.get_active_channels_for_plan(plan.key, phase_name, current_week, tenant_key=ctx.tenant_key)
    return channels


@router.get("/{key}/planting-runs", response_model=list[PlantRunSummaryResponse])
def get_plant_runs(
    key: Annotated[str, Path(description="Document key of the plant instance.")],
    ctx: TenantContext = Depends(get_current_tenant),
    plant_service: PlantInstanceService = Depends(get_plant_instance_service),
    run_service: PlantingRunService = Depends(get_planting_run_service),
) -> list[PlantRunSummaryResponse]:
    """List the planting runs a plant instance belongs to."""
    plant_service.get_plant(key, tenant_key=ctx.tenant_key)
    runs = run_service.get_runs_for_plant(key)
    return [
        PlantRunSummaryResponse(
            key=r.key or "",
            name=r.name,
            status=r.status.value if hasattr(r.status, "value") else r.status,
        )
        for r in runs
    ]
