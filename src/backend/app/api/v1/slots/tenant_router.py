from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.api.mapping import to_response
from app.api.v1.slots.schemas import SlotCreate, SlotResponse
from app.common.auth import get_current_tenant, require_permission
from app.common.dependencies import get_site_service
from app.common.openapi_responses import NOT_FOUND_RESPONSE
from app.core.permissions import Action, ResourceType
from app.domain.models.site import Slot
from app.domain.models.tenant_context import TenantContext
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
    service.get_location(location_key, tenant_key=ctx.tenant_key)
    items = service.list_slots(location_key)
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
):
    """Create a slot within a location."""
    service.get_location(body.location_key, tenant_key=ctx.tenant_key)
    slot = Slot(**body.model_dump())
    created = service.create_slot(slot)
    return to_response(created, SlotResponse)


@router.put("/{key}", response_model=SlotResponse)
def update_slot(
    key: Annotated[str, Path(description="Document key of the slot.")],
    body: SlotCreate,
    ctx: TenantContext = Depends(require_permission(ResourceType.LOCATION, Action.UPDATE)),
    service: SiteService = Depends(get_site_service),
):
    """Update a slot."""
    _verify_slot_tenant(key, ctx, service)
    # The body's location is resolved under the tenant too (#1871 B1): storing
    # it as given re-parented the slot into another tenant's location.
    service.get_location(body.location_key, tenant_key=ctx.tenant_key)
    slot = Slot(**body.model_dump())
    updated = service.update_slot(key, slot)
    return to_response(updated, SlotResponse)


@router.delete("/{key}", status_code=204)
def delete_slot(
    key: Annotated[str, Path(description="Document key of the slot.")],
    ctx: TenantContext = Depends(require_permission(ResourceType.LOCATION, Action.DELETE)),
    service: SiteService = Depends(get_site_service),
):
    """Delete a slot."""
    _verify_slot_tenant(key, ctx, service)
    service.delete_slot(key)
