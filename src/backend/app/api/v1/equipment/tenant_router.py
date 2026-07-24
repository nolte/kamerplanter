"""REQ-016 Equipment tenant-scoped router.

Mounted under ``/t/{tenant_slug}/equipment``. Reads require membership, writes
require GROWER, delete requires ADMIN (REQ-016 §4). Every handler resolves the
tenant via :func:`get_current_tenant`; the service verifies ownership against
``tenant_key`` before touching an equipment item (SEC-B4).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.api.mapping import to_response
from app.api.v1.inventree.schemas import EquipmentCreate, EquipmentResponse, EquipmentUpdate
from app.common.auth import get_current_tenant, require_tenant_role
from app.common.dependencies import get_inventree_service
from app.common.enums import TenantRole
from app.common.openapi_responses import NOT_FOUND_RESPONSE
from app.domain.models.inventree import Equipment
from app.domain.models.tenant_context import TenantContext
from app.domain.services.inventree_service import InvenTreeService

router = APIRouter(prefix="/equipment", tags=["equipment"], responses=NOT_FOUND_RESPONSE)


@router.get("", response_model=list[EquipmentResponse])
def list_equipment(
    equipment_type: str | None = Query(None, description="Filter by equipment type."),
    status: str | None = Query(None, description="Filter by equipment status."),
    location_key: str | None = Query(None, description="Restrict to equipment attached to this location."),
    ctx: TenantContext = Depends(get_current_tenant),
    service: InvenTreeService = Depends(get_inventree_service),
):
    """List the tenant's equipment, optionally filtered by type, status or location."""
    if location_key:
        items = service.find_equipment_by_location(ctx.tenant_key, location_key)
    else:
        items = service.list_equipment(ctx.tenant_key, equipment_type=equipment_type, status=status)
    return [to_response(item, EquipmentResponse) for item in items]


@router.post("", response_model=EquipmentResponse, status_code=201)
def create_equipment(
    body: EquipmentCreate,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: InvenTreeService = Depends(get_inventree_service),
):
    """Create a new equipment item for the tenant."""
    equipment = Equipment(**body.model_dump())
    created = service.create_equipment(ctx.tenant_key, equipment)
    return to_response(created, EquipmentResponse)


@router.get("/by-location/{location_key}", response_model=list[EquipmentResponse])
def equipment_by_location(
    location_key: Annotated[str, Path(description="Document key of the location.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: InvenTreeService = Depends(get_inventree_service),
):
    """List the equipment attached to a location."""
    items = service.find_equipment_by_location(ctx.tenant_key, location_key)
    return [to_response(item, EquipmentResponse) for item in items]


@router.get("/{equipment_key}", response_model=EquipmentResponse)
def get_equipment(
    equipment_key: Annotated[str, Path(description="Document key of the equipment item.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: InvenTreeService = Depends(get_inventree_service),
):
    """Return a single equipment item by key."""
    return to_response(service.get_equipment(equipment_key, ctx.tenant_key), EquipmentResponse)


@router.put("/{equipment_key}", response_model=EquipmentResponse)
def update_equipment(
    equipment_key: Annotated[str, Path(description="Document key of the equipment item.")],
    body: EquipmentUpdate,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: InvenTreeService = Depends(get_inventree_service),
):
    """Update an equipment item's configuration."""
    updated = service.update_equipment(equipment_key, ctx.tenant_key, body.model_dump(exclude_unset=True))
    return to_response(updated, EquipmentResponse)


@router.delete("/{equipment_key}", status_code=204)
def delete_equipment(
    equipment_key: Annotated[str, Path(description="Document key of the equipment item.")],
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.ADMIN)),
    service: InvenTreeService = Depends(get_inventree_service),
):
    """Delete an equipment item."""
    service.delete_equipment(equipment_key, ctx.tenant_key)
