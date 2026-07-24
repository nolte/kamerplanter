"""REQ-016 InvenTree integration tenant-scoped router.

Mounted under ``/t/{tenant_slug}/inventree``. Connection management requires the
tenant ADMIN role; references, browsing, sync and the transaction log require
GROWER (write) / membership (read). Every handler resolves the tenant via
:func:`get_current_tenant` and the service verifies ownership against
``tenant_key`` before touching any resource (SEC-B4).

The integration is optional: when the kill-switch is off or no active connection
exists, live-connection operations return 409 (``FeatureDisabledError``) — never
a 500.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.api.mapping import to_response
from app.api.v1.inventree.schemas import (
    HealthCheckResponse,
    InvenTreeConnectionCreate,
    InvenTreeConnectionResponse,
    InvenTreeConnectionUpdate,
    InvenTreeReferenceResponse,
    ReferenceLinkRequest,
    StockTransactionResponse,
)
from app.common.auth import get_current_tenant, require_tenant_role
from app.common.dependencies import get_inventree_service
from app.common.enums import TenantRole
from app.common.openapi_responses import CRUD_RESPONSES
from app.common.pagination import PaginationParams, get_pagination
from app.domain.models.inventree import InvenTreeConnection
from app.domain.models.tenant_context import TenantContext
from app.domain.services.inventree_service import InvenTreeService

router = APIRouter(prefix="/inventree", tags=["inventree"], responses=CRUD_RESPONSES)


def _connection_response(connection: InvenTreeConnection) -> InvenTreeConnectionResponse:
    return to_response(
        connection,
        InvenTreeConnectionResponse,
        api_token_set=bool(connection.api_token_encrypted),
    )


# ── Connections (ADMIN) ─────────────────────────────────────────────────


@router.get("/connections", response_model=list[InvenTreeConnectionResponse])
def list_connections(
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.ADMIN)),
    service: InvenTreeService = Depends(get_inventree_service),
):
    """List the tenant's InvenTree connections."""
    return [_connection_response(c) for c in service.list_connections(ctx.tenant_key)]


@router.post("/connections", response_model=InvenTreeConnectionResponse, status_code=201)
def create_connection(
    body: InvenTreeConnectionCreate,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.ADMIN)),
    service: InvenTreeService = Depends(get_inventree_service),
):
    """Create an InvenTree connection for the tenant."""
    created = service.create_connection(
        ctx.tenant_key,
        name=body.name,
        base_url=body.base_url,
        api_token=body.api_token,
        verify_ssl=body.verify_ssl,
        is_active=body.is_active,
        sync_interval_minutes=body.sync_interval_minutes,
        push_interval_minutes=body.push_interval_minutes,
    )
    return _connection_response(created)


@router.get("/connections/{connection_key}", response_model=InvenTreeConnectionResponse)
def get_connection(
    connection_key: Annotated[str, Path(description="Document key of the InvenTree connection.")],
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.ADMIN)),
    service: InvenTreeService = Depends(get_inventree_service),
):
    """Return a single InvenTree connection by key."""
    return _connection_response(service.get_connection(connection_key, ctx.tenant_key))


@router.put("/connections/{connection_key}", response_model=InvenTreeConnectionResponse)
def update_connection(
    connection_key: Annotated[str, Path(description="Document key of the InvenTree connection.")],
    body: InvenTreeConnectionUpdate,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.ADMIN)),
    service: InvenTreeService = Depends(get_inventree_service),
):
    """Update an InvenTree connection."""
    updated = service.update_connection(connection_key, ctx.tenant_key, body.model_dump(exclude_none=True))
    return _connection_response(updated)


@router.delete("/connections/{connection_key}", status_code=204)
def delete_connection(
    connection_key: Annotated[str, Path(description="Document key of the InvenTree connection.")],
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.ADMIN)),
    service: InvenTreeService = Depends(get_inventree_service),
):
    """Delete an InvenTree connection."""
    service.delete_connection(connection_key, ctx.tenant_key)


@router.post("/connections/{connection_key}/health-check", response_model=HealthCheckResponse)
async def health_check(
    connection_key: Annotated[str, Path(description="Document key of the InvenTree connection.")],
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.ADMIN)),
    service: InvenTreeService = Depends(get_inventree_service),
):
    """Probe an InvenTree connection's live health."""
    result = await service.health_check(connection_key, ctx.tenant_key)
    return HealthCheckResponse(**result)


# ── References (GROWER write / member read) ─────────────────────────────


@router.post("/references/link", response_model=InvenTreeReferenceResponse, status_code=201)
async def link_entity(
    body: ReferenceLinkRequest,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: InvenTreeService = Depends(get_inventree_service),
):
    """Link a domain entity to an InvenTree part."""
    reference = await service.link_entity(
        ctx.tenant_key,
        body.entity_collection,
        body.entity_key,
        body.inventree_part_id,
        auto_deduct=body.auto_deduct,
        deduct_unit=body.deduct_unit,
    )
    return to_response(reference, InvenTreeReferenceResponse)


@router.get("/references", response_model=list[InvenTreeReferenceResponse])
def list_references(
    entity_collection: str | None = Query(None, description="Filter references by linked entity collection."),
    ctx: TenantContext = Depends(get_current_tenant),
    service: InvenTreeService = Depends(get_inventree_service),
):
    """List the tenant's InvenTree entity references."""
    references = service.list_references(ctx.tenant_key, entity_collection)
    return [to_response(r, InvenTreeReferenceResponse) for r in references]


@router.delete("/references/{reference_key}", status_code=204)
def unlink_entity(
    reference_key: Annotated[str, Path(description="Document key of the InvenTree reference.")],
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: InvenTreeService = Depends(get_inventree_service),
):
    """Remove an InvenTree entity reference."""
    service.unlink_entity(reference_key, ctx.tenant_key)


@router.post("/references/{reference_key}/sync")
async def sync_reference(
    reference_key: Annotated[str, Path(description="Document key of the InvenTree reference.")],
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: InvenTreeService = Depends(get_inventree_service),
):
    """Sync a single InvenTree reference's stock level."""
    return await service.sync_reference(reference_key, ctx.tenant_key)


# ── Browse (member) ─────────────────────────────────────────────────────


@router.get("/browse/parts")
async def browse_parts(
    query: str = Query(..., min_length=2, description="Search term to match InvenTree parts against."),
    category_id: int | None = Query(None, description="Restrict the search to this InvenTree category."),
    limit: int = Query(25, ge=1, le=100, description="Maximum number of parts to return."),
    ctx: TenantContext = Depends(get_current_tenant),
    service: InvenTreeService = Depends(get_inventree_service),
):
    """Search parts in the connected InvenTree instance."""
    return await service.browse_parts(ctx.tenant_key, query, category_id=category_id, limit=limit)


@router.get("/browse/categories")
async def browse_categories(
    parent_id: int | None = Query(None, description="List the child categories of this InvenTree category."),
    ctx: TenantContext = Depends(get_current_tenant),
    service: InvenTreeService = Depends(get_inventree_service),
):
    """List categories in the connected InvenTree instance."""
    return await service.browse_categories(ctx.tenant_key, parent_id=parent_id)


# ── Sync + transactions ─────────────────────────────────────────────────


@router.post("/sync/trigger")
async def trigger_sync(
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: InvenTreeService = Depends(get_inventree_service),
):
    """Trigger a full stock sync and push pending stock transactions."""
    stock = await service.sync_stock_levels(ctx.tenant_key)
    push = await service.push_pending_transactions(ctx.tenant_key)
    return {"stock_sync": stock, "push": push}


@router.get("/transactions", response_model=list[StockTransactionResponse])
def list_transactions(
    status: str | None = Query(None, description="Filter transactions by processing status."),
    pagination: PaginationParams = Depends(get_pagination),
    ctx: TenantContext = Depends(get_current_tenant),
    service: InvenTreeService = Depends(get_inventree_service),
):
    """List the tenant's InvenTree stock transactions (paginated)."""
    transactions = service.list_transactions(
        ctx.tenant_key, status=status, offset=pagination.offset, limit=pagination.limit
    )
    return [to_response(t, StockTransactionResponse) for t in transactions]
