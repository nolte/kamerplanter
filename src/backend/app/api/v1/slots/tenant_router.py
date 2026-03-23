from fastapi import APIRouter, Depends, Query

from app.api.v1.slots.schemas import SlotCreate, SlotResponse
from app.common.auth import get_current_tenant
from app.common.dependencies import get_site_service
from app.domain.models.site import Slot
from app.domain.models.tenant_context import TenantContext
from app.domain.services.site_service import SiteService

router = APIRouter(prefix="/slots", tags=["slots"])


def _verify_slot_tenant(key: str, ctx: TenantContext, service: SiteService) -> Slot:
    """Get a slot and verify it belongs to a location whose site is owned by the tenant."""
    slot = service.get_slot(key)
    loc = service.get_location(slot.location_key)
    service.get_site(loc.site_key, tenant_key=ctx.tenant_key)
    return slot


@router.get("", response_model=list[SlotResponse])
def list_slots(
    location_key: str = Query(...),
    ctx: TenantContext = Depends(get_current_tenant),
    service: SiteService = Depends(get_site_service),
):
    loc = service.get_location(location_key)
    service.get_site(loc.site_key, tenant_key=ctx.tenant_key)
    items = service.list_slots(location_key)
    return [SlotResponse(key=s.key or "", **s.model_dump(exclude={"key"})) for s in items]


@router.get("/{key}", response_model=SlotResponse)
def get_slot(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: SiteService = Depends(get_site_service),
):
    slot = _verify_slot_tenant(key, ctx, service)
    return SlotResponse(key=slot.key or "", **slot.model_dump(exclude={"key"}))


@router.post("", response_model=SlotResponse, status_code=201)
def create_slot(
    body: SlotCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: SiteService = Depends(get_site_service),
):
    loc = service.get_location(body.location_key)
    service.get_site(loc.site_key, tenant_key=ctx.tenant_key)
    slot = Slot(**body.model_dump())
    created = service.create_slot(slot)
    return SlotResponse(key=created.key or "", **created.model_dump(exclude={"key"}))


@router.put("/{key}", response_model=SlotResponse)
def update_slot(
    key: str,
    body: SlotCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: SiteService = Depends(get_site_service),
):
    _verify_slot_tenant(key, ctx, service)
    slot = Slot(**body.model_dump())
    updated = service.update_slot(key, slot)
    return SlotResponse(key=updated.key or "", **updated.model_dump(exclude={"key"}))


@router.delete("/{key}", status_code=204)
def delete_slot(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: SiteService = Depends(get_site_service),
):
    _verify_slot_tenant(key, ctx, service)
    service.delete_slot(key)
