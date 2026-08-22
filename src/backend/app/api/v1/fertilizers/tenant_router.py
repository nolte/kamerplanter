from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.api.mapping import to_response
from app.api.v1.fertilizers.schemas import (
    FertilizerCreate,
    FertilizerResponse,
    FertilizerUpdate,
    IncompatibilityCreate,
    IncompatibilityResponse,
    NutrientPlanUsageResponse,
    StockCreate,
    StockResponse,
    StockUpdate,
)
from app.common.auth import get_current_tenant, require_permission
from app.common.dependencies import get_fertilizer_service
from app.common.enums import DataOrigin
from app.common.openapi_responses import NOT_FOUND_RESPONSE
from app.common.pagination import PaginationParams, get_pagination
from app.core.permissions import Action, ResourceType
from app.domain.models.fertilizer import Fertilizer, FertilizerStock
from app.domain.models.tenant_context import TenantContext
from app.domain.services.fertilizer_service import FertilizerService

router = APIRouter(prefix="/fertilizers", tags=["fertilizers"], responses=NOT_FOUND_RESPONSE)


def _fert_response(f: Fertilizer) -> FertilizerResponse:
    # Provenance is derived from tenant ownership: the shared catalog uses an
    # empty tenant_key (system), tenant-created products carry their tenant_key.
    origin = DataOrigin.TENANT if f.tenant_key else DataOrigin.SYSTEM
    return to_response(f, FertilizerResponse, origin=origin)


@router.get("", response_model=list[FertilizerResponse])
def list_fertilizers(
    pagination: PaginationParams = Depends(get_pagination),
    fertilizer_type: str | None = Query(None, description="Filter by fertilizer type."),
    brand: str | None = Query(None, description="Filter by brand."),
    is_organic: bool | None = Query(None, description="Filter by organic flag."),
    tank_safe: bool | None = Query(None, description="Filter by tank-safe flag."),
    ctx: TenantContext = Depends(get_current_tenant),
    service: FertilizerService = Depends(get_fertilizer_service),
):
    """List the tenant's fertilizers (shared catalog plus tenant products), filtered."""
    filters: dict = {}
    if fertilizer_type:
        filters["fertilizer_type"] = fertilizer_type
    if brand:
        filters["brand"] = brand
    if is_organic is not None:
        filters["is_organic"] = is_organic
    if tank_safe is not None:
        filters["tank_safe"] = tank_safe
    items, _total = service.list_fertilizers(
        pagination.offset, pagination.limit, filters or None, tenant_key=ctx.tenant_key
    )
    return [_fert_response(f) for f in items]


@router.post("", response_model=FertilizerResponse, status_code=201)
def create_fertilizer(
    body: FertilizerCreate,
    ctx: TenantContext = Depends(require_permission(ResourceType.FERTILIZER, Action.CREATE)),
    service: FertilizerService = Depends(get_fertilizer_service),
):
    """Create a tenant-owned fertilizer product."""
    fert = Fertilizer(**body.model_dump(), tenant_key=ctx.tenant_key)
    created = service.create_fertilizer(fert)
    return _fert_response(created)


@router.get("/{key}", response_model=FertilizerResponse)
def get_fertilizer(
    key: Annotated[str, Path(description="Document key of the fertilizer.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: FertilizerService = Depends(get_fertilizer_service),
):
    """Return a single fertilizer by key."""
    f = service.get_fertilizer(key, tenant_key=ctx.tenant_key)
    return _fert_response(f)


@router.put("/{key}", response_model=FertilizerResponse)
def update_fertilizer(
    key: Annotated[str, Path(description="Document key of the fertilizer.")],
    body: FertilizerUpdate,
    ctx: TenantContext = Depends(require_permission(ResourceType.FERTILIZER, Action.UPDATE)),
    service: FertilizerService = Depends(get_fertilizer_service),
):
    """Update a tenant-owned fertilizer product."""
    service.get_fertilizer(key, tenant_key=ctx.tenant_key)
    data = body.model_dump(exclude_none=True)
    updated = service.update_fertilizer(key, data)
    return _fert_response(updated)


@router.delete("/{key}", status_code=204)
def delete_fertilizer(
    key: Annotated[str, Path(description="Document key of the fertilizer.")],
    ctx: TenantContext = Depends(require_permission(ResourceType.FERTILIZER, Action.DELETE)),
    service: FertilizerService = Depends(get_fertilizer_service),
):
    """Delete a tenant-owned fertilizer product."""
    service.get_fertilizer(key, tenant_key=ctx.tenant_key)
    service.delete_fertilizer(key)


@router.get("/{key}/stocks", response_model=list[StockResponse])
def list_stocks(
    key: Annotated[str, Path(description="Document key of the fertilizer.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: FertilizerService = Depends(get_fertilizer_service),
):
    """List a fertilizer's stock entries."""
    service.get_fertilizer(key, tenant_key=ctx.tenant_key)
    stocks = service.get_stocks(key)
    return [to_response(s, StockResponse) for s in stocks]


@router.post("/{key}/stocks", response_model=StockResponse, status_code=201)
def create_stock(
    key: Annotated[str, Path(description="Document key of the fertilizer.")],
    body: StockCreate,
    ctx: TenantContext = Depends(require_permission(ResourceType.FERTILIZER, Action.CREATE)),
    service: FertilizerService = Depends(get_fertilizer_service),
):
    """Add a stock entry to a fertilizer."""
    service.get_fertilizer(key, tenant_key=ctx.tenant_key)
    stock = FertilizerStock(fertilizer_key=key, **body.model_dump())
    created = service.create_stock(key, stock)
    return to_response(created, StockResponse)


@router.put("/{key}/stocks/{sk}", response_model=StockResponse)
def update_stock(
    key: Annotated[str, Path(description="Document key of the fertilizer.")],
    sk: Annotated[str, Path(description="Document key of the stock entry.")],
    body: StockUpdate,
    ctx: TenantContext = Depends(require_permission(ResourceType.FERTILIZER, Action.UPDATE)),
    service: FertilizerService = Depends(get_fertilizer_service),
):
    """Update a fertilizer stock entry.

    The product/stock pairing and the visibility check live in the service
    (#1265). They used to live here as `get_fertilizer(key, ...)`, which
    verified the product named in the URL and then patched whatever stock key
    followed it.
    """
    data = body.model_dump(exclude_none=True)
    updated = service.update_stock(sk, data, fertilizer_key=key, tenant_key=ctx.tenant_key)
    return to_response(updated, StockResponse)


@router.delete("/{key}/stocks/{sk}", status_code=204)
def delete_stock(
    key: Annotated[str, Path(description="Document key of the fertilizer.")],
    sk: Annotated[str, Path(description="Document key of the stock entry.")],
    ctx: TenantContext = Depends(require_permission(ResourceType.FERTILIZER, Action.DELETE)),
    service: FertilizerService = Depends(get_fertilizer_service),
):
    """Delete a fertilizer stock entry.

    Pairing-checked in the service, for the reason given on `update_stock`.
    """
    service.delete_stock(sk, fertilizer_key=key, tenant_key=ctx.tenant_key)


@router.get("/{key}/incompatibilities", response_model=list[IncompatibilityResponse])
def list_incompatibilities(
    key: Annotated[str, Path(description="Document key of the fertilizer.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: FertilizerService = Depends(get_fertilizer_service),
):
    """List a fertilizer's declared incompatibilities."""
    service.get_fertilizer(key, tenant_key=ctx.tenant_key)
    return service.get_incompatibilities(key)


@router.post("/{key}/incompatibilities", response_model=IncompatibilityResponse, status_code=201)
def add_incompatibility(
    key: Annotated[str, Path(description="Document key of the fertilizer.")],
    body: IncompatibilityCreate,
    ctx: TenantContext = Depends(require_permission(ResourceType.FERTILIZER, Action.UPDATE)),
    service: FertilizerService = Depends(get_fertilizer_service),
):
    """Declare an incompatibility between this fertilizer and another."""
    service.get_fertilizer(key, tenant_key=ctx.tenant_key)
    service.add_incompatibility(key, body.other_key, body.reason, body.severity)
    return IncompatibilityResponse(
        fertilizer_key=body.other_key, product_name=None, reason=body.reason, severity=body.severity
    )


@router.delete("/{key}/incompatibilities/{other_key}", status_code=204)
def remove_incompatibility(
    key: Annotated[str, Path(description="Document key of the fertilizer.")],
    other_key: Annotated[str, Path(description="Document key of the incompatible fertilizer.")],
    ctx: TenantContext = Depends(require_permission(ResourceType.FERTILIZER, Action.UPDATE)),
    service: FertilizerService = Depends(get_fertilizer_service),
):
    """Remove a declared incompatibility between two fertilizers."""
    service.get_fertilizer(key, tenant_key=ctx.tenant_key)
    service.remove_incompatibility(key, other_key)


@router.get("/{key}/nutrient-plans", response_model=list[NutrientPlanUsageResponse])
def list_nutrient_plan_usage(
    key: Annotated[str, Path(description="Document key of the fertilizer.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: FertilizerService = Depends(get_fertilizer_service),
):
    """List the nutrient plans that use this fertilizer."""
    service.get_fertilizer(key, tenant_key=ctx.tenant_key)
    return service.get_nutrient_plan_usage(key)
