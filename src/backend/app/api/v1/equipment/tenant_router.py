"""REQ-016 Equipment tenant-scoped router.

Mounted under ``/t/{tenant_slug}/equipment``. Reads require membership, writes
require GROWER, delete requires ADMIN (REQ-016 §4). Every handler resolves the
tenant via :func:`get_current_tenant`; the service verifies ownership against
``tenant_key`` before touching an equipment item (SEC-B4).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.mapping import to_response
from app.api.v1.inventree.schemas import EquipmentCreate, EquipmentResponse, EquipmentUpdate
from app.common.auth import get_current_tenant, require_tenant_role
from app.common.dependencies import get_inventree_service
from app.common.enums import TenantRole
from app.domain.models.inventree import Equipment
from app.domain.models.tenant_context import TenantContext
from app.domain.services.inventree_service import InvenTreeService

router = APIRouter(prefix="/equipment", tags=["equipment"])


@router.get("", response_model=list[EquipmentResponse])
def list_equipment(
    equipment_type: str | None = Query(None),
    status: str | None = Query(None),
    location_key: str | None = Query(None),
    ctx: TenantContext = Depends(get_current_tenant),
    service: InvenTreeService = Depends(get_inventree_service),
):
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
    equipment = Equipment(**body.model_dump())
    created = service.create_equipment(ctx.tenant_key, equipment)
    return to_response(created, EquipmentResponse)


@router.get("/by-location/{location_key}", response_model=list[EquipmentResponse])
def equipment_by_location(
    location_key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: InvenTreeService = Depends(get_inventree_service),
):
    items = service.find_equipment_by_location(ctx.tenant_key, location_key)
    return [to_response(item, EquipmentResponse) for item in items]


@router.get("/{equipment_key}", response_model=EquipmentResponse)
def get_equipment(
    equipment_key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: InvenTreeService = Depends(get_inventree_service),
):
    return to_response(service.get_equipment(equipment_key, ctx.tenant_key), EquipmentResponse)


@router.put("/{equipment_key}", response_model=EquipmentResponse)
def update_equipment(
    equipment_key: str,
    body: EquipmentUpdate,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: InvenTreeService = Depends(get_inventree_service),
):
    updated = service.update_equipment(equipment_key, ctx.tenant_key, body.model_dump(exclude_unset=True))
    return to_response(updated, EquipmentResponse)


@router.delete("/{equipment_key}", status_code=204)
def delete_equipment(
    equipment_key: str,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.ADMIN)),
    service: InvenTreeService = Depends(get_inventree_service),
):
    service.delete_equipment(equipment_key, ctx.tenant_key)
