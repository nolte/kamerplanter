"""The garden plan of a site (REQ-053 §21.1): read model, boundary, transactional batch, change log.

Every route resolves its site **in the service** through the tenant anchor (§22.3 T-04); the
gate here only decides the caller's rank. The batch checks the caller's role once more per
operation (SR-001) — the route-level gate (``location:update``, ab Gärtner) is the entry, not
the whole rule.
"""

import json
import re
from time import perf_counter
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Path, Query, Request

from app.api.mapping import to_response
from app.api.v1.auth.router import limiter, user_rate_limit_key
from app.api.v1.garden_objects.schemas import garden_object_to_response
from app.api.v1.garden_plan.schemas import (
    SCHEMA_VERSION,
    DerivedGeometrySchema,
    GardenPlanResponse,
    PlanAuditEntryResponse,
    PlanBatchRequest,
    PlanBatchResponse,
    PlanBoundaryRequest,
    PlanBoundaryResponse,
    PlanGardenObjectResponse,
    PlanLocationResponse,
    PlanPlantResponse,
    PlanSettingsResponse,
    PlanSlotGeometry,
    PlanSlotResponse,
)
from app.common.auth import get_current_tenant, require_permission
from app.common.dependencies import get_garden_plan_service
from app.common.enums import SlotRole
from app.common.exceptions import PlanRevisionConflictError, ValidationError
from app.common.openapi_responses import (
    CONFLICT_RESPONSE,
    FORBIDDEN_RESPONSE,
    NOT_FOUND_RESPONSE,
    VALIDATION_RESPONSE,
)
from app.common.pagination import PaginationParams, get_pagination
from app.config.settings import settings
from app.core.permissions import Action, ResourceType
from app.domain.calculators.geometry_calculator import area_m2
from app.domain.models.garden_plan import GardenPlanView, PlanBatchResult, PlanSlotView, PlantShortInfo, SetBoundaryOp
from app.domain.models.tenant_context import TenantContext
from app.domain.services.garden_plan_service import INCLUDE_PARTS, GardenPlanService
from app.observability.garden_plan_metrics import observe_batch_duration, observe_plan_size, record_conflict

router = APIRouter(prefix="/sites", tags=["garden-plan"], responses=NOT_FOUND_RESPONSE)

_SITE_KEY = Annotated[str, Path(description="Document key of the site.")]


def _operations_bytes(operations: list[dict[str, Any]]) -> int:
    """Size of the parsed operations as compact JSON, for the 2 MB ceiling (GP-NFR-013).

    Measured on the parsed list rather than by reading the request body again: the edge already bounds the raw
    body (``app/common/body_limit.py``), and a route that reads one itself needs a bound of its own.
    """
    return len(json.dumps(operations, separators=(",", ":")).encode())


def _plan_response(view: GardenPlanView) -> GardenPlanResponse:
    plan = view.plan
    return GardenPlanResponse(
        schema_version=SCHEMA_VERSION,
        site_key=view.site_key,
        site_name=view.site_name,
        plan_revision=view.plan_revision,
        plan=(
            PlanSettingsResponse(
                boundary=plan.boundary,
                north_angle_deg=plan.north_angle_deg,
                default_grid_m=plan.default_grid_m,
                adjacency_factor=plan.adjacency_factor,
                plan_revision=plan.plan_revision,
                plan_updated_at=plan.plan_updated_at,
                plan_updated_by_name=view.plan_updated_by_name,
            )
            if plan is not None
            else None
        ),
        locations=[
            to_response(
                location,
                PlanLocationResponse,
                season_state=view.season_states.get(location.key or ""),
                open_task_count=view.task_counters.get(location.key or "", _NO_TASKS).open_task_count,
                overdue_task_count=view.task_counters.get(location.key or "", _NO_TASKS).overdue_task_count,
            )
            for location in view.locations
        ],
        garden_objects=[
            PlanGardenObjectResponse(
                **garden_object_to_response(obj).model_dump(),
                open_task_count=view.object_task_counters.get(obj.key or "", _NO_TASKS).open_task_count,
                overdue_task_count=view.object_task_counters.get(obj.key or "", _NO_TASKS).overdue_task_count,
            )
            for obj in view.garden_objects
        ],
        slots=[_slot_response(slot) for slot in view.slots],
        plants=[_plant_response(plant) for plant in view.plants],
        zones=view.zones,
    )


def _slot_response(slot: PlanSlotView) -> PlanSlotResponse:
    """A slot with the fields at their common value left out (``None`` is not sent): GP-NFR-031.

    Left out are ``slot_role`` = position, ``capacity_plants`` = 1, ``currently_occupied`` = false and the
    ``kind`` of a point geometry. Only these, and only here: a blanket "omit defaults" would also drop the
    ``kind`` discriminator of every geometry, and a geometry without its kind cannot be read.
    """
    geometry = slot.plan_geometry
    plan_geometry = None
    if geometry is not None:
        kind = geometry["kind"]
        plan_geometry = PlanSlotGeometry(**{**geometry, "kind": None if kind == "point" else kind})
    return PlanSlotResponse(
        key=slot.key,
        slot_id=slot.slot_id,
        location_key=slot.location_key,
        slot_role=None if slot.slot_role == SlotRole.POSITION else slot.slot_role,
        capacity_plants=None if slot.capacity_plants == 1 else slot.capacity_plants,
        currently_occupied=True if slot.currently_occupied else None,
        row_index=slot.row_index,
        sequence=slot.sequence,
        plan_geometry=plan_geometry,
    )


def _plant_response(plant: PlantShortInfo) -> PlanPlantResponse:
    """The short info of §21.1; ``location_key`` only for a plant without a slot (the slot already names it)."""
    return to_response(plant, PlanPlantResponse, location_key=None if plant.slot_key else plant.location_key)


def _batch_response(result: PlanBatchResult) -> PlanBatchResponse:
    return PlanBatchResponse(
        plan_revision=result.plan_revision,
        key_map=result.key_map,
        updated=result.updated,
        deleted=result.deleted,
        derived={
            key: DerivedGeometrySchema(area_m2=value.area_m2, bbox=value.bbox) for key, value in result.derived.items()
        },
    )


def _include(raw: str) -> frozenset[str]:
    parts = {part for part in re.split(r"\s*,\s*", raw.strip()) if part}
    unknown = parts - INCLUDE_PARTS
    if unknown:
        raise ValidationError(
            "include accepts plants, tasks and zones.",
            details=[{"field": "include", "reason": "Unknown value.", "code": "validation.invalid"}],
        )
    return frozenset(parts)


class _NoTasks:
    open_task_count = 0
    overdue_task_count = 0


_NO_TASKS = _NoTasks()


@router.get(
    "/{key}/plan",
    response_model=GardenPlanResponse,
    response_model_exclude_none=True,
    summary="Read the whole garden plan of a site",
)
def get_plan(
    key: _SITE_KEY,
    include: Annotated[
        str,
        Query(description="Comma-separated parts to include: plants, tasks, zones. Default: all (GP-API-001)."),
    ] = "plants,tasks,zones",
    ctx: TenantContext = Depends(get_current_tenant),
    service: GardenPlanService = Depends(get_garden_plan_service),
) -> GardenPlanResponse:
    """The site plan, locations with geometry, garden objects, slots in plan coordinates, plant short
    info and task counters in one request (GP-API-001, GP-NFR-002)."""
    view = service.get_plan(key, tenant_key=ctx.tenant_key, include=_include(include))
    observe_plan_size(len(view.locations) + len(view.garden_objects))
    return _plan_response(view)


@router.put(
    "/{key}/plan/boundary",
    response_model=PlanBoundaryResponse,
    summary="Set the garden boundary (creates the plan)",
    responses={**FORBIDDEN_RESPONSE, **CONFLICT_RESPONSE, **VALIDATION_RESPONSE},
)
@limiter.limit(settings.rate_limit_plan_batch, key_func=user_rate_limit_key)
def put_boundary(
    request: Request,
    key: _SITE_KEY,
    body: PlanBoundaryRequest,
    ctx: TenantContext = Depends(require_permission(ResourceType.LOCATION, Action.UPDATE)),
    service: GardenPlanService = Depends(get_garden_plan_service),
) -> PlanBoundaryResponse:
    """Set the boundary, north angle and grid; creates the plan on the first call (GP-API-002).

    422 ``boundary.shrinks_below_objects`` when the new boundary would leave a top-level object
    outside (V-19).
    """
    operation = SetBoundaryOp(
        op="set_boundary",
        boundary=body.boundary,
        north_angle_deg=body.north_angle_deg,
        default_grid_m=body.default_grid_m,
        adjacency_factor=body.adjacency_factor,
    )
    try:
        result = service.set_boundary(
            key,
            tenant_key=ctx.tenant_key,
            user_key=ctx.user_key,
            role=ctx.role,
            operation=operation,
            expected_revision=body.expected_revision,
        )
    except PlanRevisionConflictError:
        record_conflict()
        raise
    return PlanBoundaryResponse(
        plan_revision=result.plan_revision, total_area_m2=area_m2(body.boundary), boundary=body.boundary
    )


@router.post(
    "/{key}/plan/batch",
    response_model=PlanBatchResponse,
    summary="Apply a list of plan operations atomically",
    responses={**FORBIDDEN_RESPONSE, **CONFLICT_RESPONSE, **VALIDATION_RESPONSE},
)
@limiter.limit(settings.rate_limit_plan_batch, key_func=user_rate_limit_key)
def apply_batch(
    request: Request,
    key: _SITE_KEY,
    body: PlanBatchRequest,
    ctx: TenantContext = Depends(require_permission(ResourceType.LOCATION, Action.UPDATE)),
    service: GardenPlanService = Depends(get_garden_plan_service),
) -> PlanBatchResponse:
    """All-or-nothing: one transaction with a revision check inside (GP-API-003, GP-NFR-013).

    Each operation is checked against the caller's role first: ``delete`` needs the lead role,
    and a batch holding one the caller may not run is refused whole with 403
    ``batch.operation_forbidden {op_index}``. Then, in order: references (422
    ``reference.not_found``), Pydantic, domain rules (422 ``geometry.outside_parent``,
    ``bed.overlap`` …), and last the revision (409 ``plan.revision_conflict``).
    """
    started = perf_counter()
    try:
        result = service.apply_batch(
            key,
            tenant_key=ctx.tenant_key,
            user_key=ctx.user_key,
            role=ctx.role,
            expected_revision=body.expected_revision,
            operations=body.operations,
            body_bytes=_operations_bytes(body.operations),
        )
    except PlanRevisionConflictError:
        record_conflict()
        raise
    observe_batch_duration(perf_counter() - started)
    return _batch_response(result)


@router.get(
    "/{key}/plan/audit",
    response_model=list[PlanAuditEntryResponse],
    summary="The plan's change log (deletions and boundary changes)",
)
def list_plan_audit(
    key: _SITE_KEY,
    pagination: PaginationParams = Depends(get_pagination),
    ctx: TenantContext = Depends(get_current_tenant),
    service: GardenPlanService = Depends(get_garden_plan_service),
) -> list[PlanAuditEntryResponse]:
    """Newest first; the editor is named by display name (GP-API-008, SR-011)."""
    entries = service.list_audit(key, tenant_key=ctx.tenant_key, offset=pagination.offset, limit=pagination.limit)
    return [to_response(entry, PlanAuditEntryResponse) for entry in entries]
