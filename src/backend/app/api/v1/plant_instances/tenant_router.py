from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.api.mapping import to_response
from app.api.v1.plant_instances.row_labels import PlantRowLabels
from app.api.v1.plant_instances.schemas import (
    ActiveChannelResponse,
    AssignNutrientPlanRequest,
    AssignNutrientPlanStatusResponse,
    FailureCauseRuleResponse,
    PlantCreate,
    PlantInstanceInPhaseResponse,
    PlantInstancesInPhaseResponse,
    PlantPatch,
    PlantResponse,
    PlantRunSummaryResponse,
    RemovePlantRequest,
    SurvivalStatsResponse,
    TerminationOptionsResponse,
    ValidatePlantingRequest,
    ValidatePlantingResponse,
)
from app.common.auth import get_current_tenant, require_permission
from app.common.dependencies import get_nutrient_plan_service, get_plant_instance_service, get_planting_run_service
from app.common.openapi_responses import NOT_FOUND_RESPONSE
from app.common.pagination import CursorPaginationParams, get_cursor_pagination
from app.core.permissions import Action, ResourceType
from app.domain.models.failure_cause import TerminationOptions
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.tenant_context import TenantContext
from app.domain.services.nutrient_plan_service import NutrientPlanService
from app.domain.services.plant_instance_service import PlantInstanceService
from app.domain.services.planting_run_service import PlantingRunService

router = APIRouter(prefix="/plant-instances", tags=["plant-instances"], responses=NOT_FOUND_RESPONSE)


def _row_labels(service: PlantInstanceService, tenant_key: str) -> PlantRowLabels:
    """Per-request label memo resolving through the service under ``tenant_key`` (#3032)."""
    return PlantRowLabels(
        resolve_species=lambda species_key: service.resolve_species(species_key, tenant_key=tenant_key),
        resolve_cultivar=service.resolve_cultivar,
        resolve_phase_name=service.resolve_phase_name,
    )


def _to_response(
    p: PlantInstance,
    service: PlantInstanceService,
    tenant_key: str,
    labels: PlantRowLabels | None = None,
    planting_runs: list[PlantRunSummaryResponse] | None = None,
) -> PlantResponse:
    """Convert PlantInstance to PlantResponse, resolving phase name and
    denormalized species/cultivar labels from their keys.

    A list route passes one shared ``labels`` memo for all its rows (#3032); a
    single-plant route gets a fresh one. ``planting_runs`` is resolved by the list
    route only (#3015); every other route leaves it ``None``.
    """
    if labels is None:
        labels = _row_labels(service, tenant_key)
    return to_response(
        p,
        PlantResponse,
        current_phase=labels.phase_name(p.current_phase_key),
        species=labels.species(p.species_key),
        cultivar=labels.cultivar(p.cultivar_key),
        planting_runs=planting_runs,
    )


def termination_options_response(options: TerminationOptions) -> TerminationOptionsResponse:
    """Map the dialog options of one plant onto the response (shared with the frontend-fixture contract test)."""
    return TerminationOptionsResponse(
        suggested_cause=options.suggested_cause,
        wilt_prone_family=options.wilt_prone_family,
        rules=[
            FailureCauseRuleResponse(
                termination_cause=rule.termination_cause,
                prefill=rule.prefill,
                choices=list(rule.choices),
                asks_wilt_follow_up=rule.asks_wilt_follow_up,
            )
            for rule in options.rules
        ],
        wilt_follow_up_class=options.wilt_follow_up_class,
        pathogen_classes=list(options.pathogen_classes),
        pathogens=list(options.pathogens),
        confirmation_sources=list(options.confirmation_sources),
    )


@router.get("", response_model=list[PlantResponse])
def list_plants(
    pagination: CursorPaginationParams = Depends(get_cursor_pagination),
    location_key: str | None = Query(
        default=None,
        min_length=1,
        max_length=254,
        description="Only the plants placed at this location (#3015). A location of another tenant lists nothing.",
    ),
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantInstanceService = Depends(get_plant_instance_service),
):
    """List the tenant's plant instances (paginated; ``?after=<key>`` pages by keyset, MT-035).

    Every row carries ``planting_runs``, the runs it is attached to (#3015), resolved for the whole page in one read:
    the list view used to read the plants of every run of the tenant to label its rows.
    """
    items = service.list_plants_window(
        tenant_key=ctx.tenant_key,
        offset=pagination.offset,
        limit=pagination.limit,
        after=pagination.after,
        location_key=location_key,
    )
    labels = _row_labels(service, ctx.tenant_key)
    run_refs = service.run_refs_for_plants([p.key for p in items if p.key], tenant_key=ctx.tenant_key)
    return [
        _to_response(
            p,
            service,
            ctx.tenant_key,
            labels,
            planting_runs=[PlantRunSummaryResponse(**ref) for ref in run_refs.get(p.key or "", [])],
        )
        for p in items
    ]


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
    return _to_response(p, service, ctx.tenant_key)


@router.post("", response_model=PlantResponse, status_code=201)
def create_plant(
    body: PlantCreate,
    ctx: TenantContext = Depends(require_permission(ResourceType.PLANT, Action.CREATE)),
    service: PlantInstanceService = Depends(get_plant_instance_service),
):
    """Create a plant instance for the tenant."""
    plant = PlantInstance(**body.model_dump())
    created = service.create_plant(plant, tenant_key=ctx.tenant_key)
    return _to_response(created, service, ctx.tenant_key)


@router.put("/{key}", response_model=PlantResponse)
def update_plant(
    key: Annotated[str, Path(description="Document key of the plant instance.")],
    body: PlantCreate,
    ctx: TenantContext = Depends(require_permission(ResourceType.PLANT, Action.UPDATE)),
    service: PlantInstanceService = Depends(get_plant_instance_service),
):
    """Replace the user-editable fields of a plant instance — **full replacement**.

    Every optional field absent from the body is written back as ``None`` and
    removed from the stored document. Measured: a body carrying only the three
    required fields plus one change erases ``location_key``, ``slot_key``,
    ``cultivar_key``, ``plant_name``, ``container_volume_liters`` and
    ``substrate_batch_key``.

    That is deliberate — the repository sets ``_update_is_full_replace`` so a
    ``PUT`` can *clear* a nullable field, which the edit form needs — and it is a
    trap for any caller composing a request from the schema alone, which is how
    #1098 was filed. **Use ``PATCH`` to change a subset.**

    ``current_phase_key`` is *not* in the assignment list below: it is
    server-managed and moves only through the phase-transition path, which
    enforces the state machine. A ``PUT`` therefore never loses a plant's phase —
    contrary to what #1098 assumed, and worth stating here so the next reader does
    not have to re-derive it from the absence of a line.
    """
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
    updated = service.update_plant(key, existing, tenant_key=ctx.tenant_key)
    return _to_response(updated, service, ctx.tenant_key)


@router.patch("/{key}", response_model=PlantResponse)
def patch_plant(
    key: Annotated[str, Path(description="Document key of the plant instance.")],
    body: PlantPatch,
    ctx: TenantContext = Depends(require_permission(ResourceType.PLANT, Action.UPDATE)),
    service: PlantInstanceService = Depends(get_plant_instance_service),
):
    """Change a subset of a plant's fields, leaving the rest untouched (#1098).

    The safe sibling of ``PUT``. **Omitted means untouched**; an explicit ``null``
    clears the field. The two are told apart by which keys the request actually
    carried (``model_fields_set``), not by the resulting value — comparing values
    would make one of the two intents unreachable.

    This exists because the only way to change one field was the full-replacement
    ``PUT``, and getting that wrong is silent: the response is a ``200`` carrying
    the row it just emptied. An agent asked to set a substrate would, following
    the schema name, also erase the plant's location and its batch reference.
    """
    existing = service.get_plant(key, tenant_key=ctx.tenant_key)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(existing, field, value)
    updated = service.update_plant(key, existing, tenant_key=ctx.tenant_key)
    return _to_response(updated, service, ctx.tenant_key)


@router.post("/{key}/remove", response_model=PlantResponse)
def remove_plant(
    key: Annotated[str, Path(description="Document key of the plant instance.")],
    body: RemovePlantRequest | None = None,
    ctx: TenantContext = Depends(require_permission(ResourceType.PLANT, Action.UPDATE)),
    service: PlantInstanceService = Depends(get_plant_instance_service),
):
    """Mark a plant instance as removed, recording the termination reason."""
    removed = service.remove_plant(
        key,
        termination_type=body.termination_type if body else None,
        termination_cause=body.termination_cause if body else None,
        failure_cause_class=body.failure_cause_class if body else None,
        failure_pathogen=body.failure_pathogen if body else None,
        failure_pathogen_confirmed=body.failure_pathogen_confirmed if body else None,
        failure_pathogen_source=body.failure_pathogen_source if body else None,
        tenant_key=ctx.tenant_key,
    )
    return _to_response(removed, service, ctx.tenant_key)


@router.get("/{key}/termination-options", response_model=TerminationOptionsResponse)
def get_termination_options(
    key: Annotated[str, Path(description="Document key of the plant instance.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantInstanceService = Depends(get_plant_instance_service),
) -> TerminationOptionsResponse:
    """What the termination dialog offers for this plant (REQ-003 E5/E6, REQ-053 §11.3a, #2888).

    The cause-class pre-fill table resolved for the plant: the suggested cause (``bolting`` after a premature
    bolt) and, per cause, the pre-filled class, the allowed classes and whether the wilt follow-up is asked.
    A plant of another tenant answers 404.
    """
    return termination_options_response(service.get_termination_options(key, tenant_key=ctx.tenant_key))


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
    ctx: TenantContext = Depends(require_permission(ResourceType.PLANT, Action.UPDATE)),
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
    ctx: TenantContext = Depends(require_permission(ResourceType.PLANT, Action.UPDATE)),
    plan_service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    """Remove the nutrient plan assigned to a plant instance."""
    plan_service.remove_plant_plan(key, tenant_key=ctx.tenant_key)


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
