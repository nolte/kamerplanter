from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.api.mapping import to_response
from app.api.v1.slots.schemas import ManualAdjacencyRequest, SlotCreate, SlotPatch, SlotResponse
from app.common.auth import get_current_tenant, require_permission
from app.common.dependencies import (
    get_adjacency_dispatch,
    get_adjacency_service,
    get_garden_resource_service,
    get_planting_reservation_service,
    get_site_service,
)
from app.common.openapi_responses import FORBIDDEN_RESPONSE, NOT_FOUND_RESPONSE, VALIDATION_RESPONSE
from app.core.permissions import Action, ResourceType
from app.domain.models.site import Slot
from app.domain.models.tenant_context import TenantContext
from app.domain.services.adjacency_service import AdjacencyDispatch, AdjacencyService, request_adjacency_recompute
from app.domain.services.garden_resource_service import GardenResourceService
from app.domain.services.planting_reservation_service import PlantingReservationService
from app.domain.services.site_service import SiteService

router = APIRouter(prefix="/slots", tags=["slots"], responses=NOT_FOUND_RESPONSE)


def _verify_slot_tenant(key: str, ctx: TenantContext, service: SiteService) -> Slot:
    """The slot ``key`` if its location's site is the tenant's, else 404 as ``Slot`` (#1871 B13).

    One step through the anchor, so a foreign and an unknown slot give the same
    answer and no other tenant's site key is echoed.
    """
    return service.get_slot(key, tenant_key=ctx.tenant_key)


@router.get("", response_model=list[SlotResponse])
def list_slots(
    location_key: str = Query(..., description="Document key of the location to list slots for."),
    ctx: TenantContext = Depends(get_current_tenant),
    service: SiteService = Depends(get_site_service),
):
    """List the slots of a location."""
    items = service.list_slots(location_key, tenant_key=ctx.tenant_key)
    return [to_response(s, SlotResponse) for s in items]


@router.get("/{key}", response_model=SlotResponse)
def get_slot(
    key: Annotated[str, Path(description="Document key of the slot.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: SiteService = Depends(get_site_service),
):
    """Return a single slot by key."""
    slot = _verify_slot_tenant(key, ctx, service)
    return to_response(slot, SlotResponse)


@router.post("", response_model=SlotResponse, status_code=201)
def create_slot(
    body: SlotCreate,
    ctx: TenantContext = Depends(require_permission(ResourceType.LOCATION, Action.CREATE)),
    service: SiteService = Depends(get_site_service),
    dispatch: AdjacencyDispatch = Depends(get_adjacency_dispatch),
):
    """Create a slot within a location."""
    slot = Slot(**body.model_dump())
    created = service.create_slot(slot, tenant_key=ctx.tenant_key)
    request_adjacency_recompute(dispatch, created.location_key)
    return to_response(created, SlotResponse)


@router.put("/{key}", response_model=SlotResponse)
def update_slot(
    key: Annotated[str, Path(description="Document key of the slot.")],
    body: SlotCreate,
    ctx: TenantContext = Depends(require_permission(ResourceType.LOCATION, Action.UPDATE)),
    service: SiteService = Depends(get_site_service),
    dispatch: AdjacencyDispatch = Depends(get_adjacency_dispatch),
):
    """Update a slot."""
    # The slot and the body's location are both resolved under the tenant in the
    # service (#1871 B1, #2107): storing the location as given re-parented the slot
    # into another tenant's location.
    previous = _verify_slot_tenant(key, ctx, service)
    slot = Slot(**body.model_dump())
    updated = service.update_slot(key, slot, tenant_key=ctx.tenant_key)
    for location_key in dict.fromkeys((previous.location_key, updated.location_key)):  # re-parenting: both beds
        request_adjacency_recompute(dispatch, location_key)
    return to_response(updated, SlotResponse)


@router.patch("/{key}", response_model=SlotResponse, responses={**FORBIDDEN_RESPONSE, **VALIDATION_RESPONSE})
def patch_slot(
    key: Annotated[str, Path(description="Document key of the slot.")],
    body: SlotPatch,
    ctx: TenantContext = Depends(require_permission(ResourceType.LOCATION, Action.UPDATE)),
    service: GardenResourceService = Depends(get_garden_resource_service),
    reservations: PlantingReservationService = Depends(get_planting_reservation_service),
) -> SlotResponse:
    """Correct a slot's geometry (bed frame), role or capacity (GP-API-014).

    Outside the plan revision (GP-NFR-007). 422 ``slot.outside_bed`` (V-04) or ``slot.overlap`` (V-06)
    when the new geometry breaks a rule. Triggers the adjacency recompute (GP-NFR-016). A new geometry
    under a standing plant is "Correct position" (GP-FR-068): it logs ``care_event(position_corrected)``
    with the plant.
    """
    slot = service.patch_slot(key, tenant_key=ctx.tenant_key, role=ctx.role, patch=body)
    if "geometry" in body.model_fields_set:
        reservations.record_position_correction(key, tenant_key=ctx.tenant_key, user_key=ctx.user_key, role=ctx.role)
    return to_response(slot, SlotResponse)


@router.delete("/{key}", status_code=204)
def delete_slot(
    key: Annotated[str, Path(description="Document key of the slot.")],
    ctx: TenantContext = Depends(require_permission(ResourceType.LOCATION, Action.DELETE)),
    service: SiteService = Depends(get_site_service),
):
    """Delete a slot."""
    service.delete_slot(key, tenant_key=ctx.tenant_key)


@router.put(
    "/{key}/adjacent/{other_key}",
    status_code=204,
    responses={**FORBIDDEN_RESPONSE, **VALIDATION_RESPONSE},
)
def set_manual_adjacency(
    key: Annotated[str, Path(description="Document key of the first slot.")],
    other_key: Annotated[str, Path(description="Document key of the second slot.")],
    body: ManualAdjacencyRequest | None = None,
    ctx: TenantContext = Depends(require_permission(ResourceType.LOCATION, Action.UPDATE)),
    service: AdjacencyService = Depends(get_adjacency_service),
) -> None:
    """Mark two slots as neighbours by hand (``source = manual``, both directions); the geometry never removes it.

    Both slots must belong to the caller's tenant and to the same site: a slot of a foreign tenant is 404, one
    of another site of the same tenant is 422 ``adjacency.different_site`` (SR-021).
    """
    service.set_manual_edge(
        key,
        other_key,
        tenant_key=ctx.tenant_key,
        role=ctx.role,
        distance_cm=None if body is None else body.distance_cm,
    )


@router.delete("/{key}/adjacent/{other_key}", status_code=204, responses=FORBIDDEN_RESPONSE)
def remove_manual_adjacency(
    key: Annotated[str, Path(description="Document key of the first slot.")],
    other_key: Annotated[str, Path(description="Document key of the second slot.")],
    ctx: TenantContext = Depends(require_permission(ResourceType.LOCATION, Action.UPDATE)),
    service: AdjacencyService = Depends(get_adjacency_service),
) -> None:
    """Remove a manual neighbourhood. A neighbourhood the geometry derives stays (and is re-derived if gone)."""
    service.remove_manual_edge(key, other_key, tenant_key=ctx.tenant_key, role=ctx.role)
