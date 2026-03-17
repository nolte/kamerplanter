from fastapi import APIRouter, Depends, Query

from app.api.v1.fertilizers.router import _fert_response
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
from app.common.auth import get_current_tenant
from app.common.dependencies import get_fertilizer_service
from app.domain.models.fertilizer import Fertilizer, FertilizerStock
from app.domain.models.tenant_context import TenantContext
from app.domain.services.fertilizer_service import FertilizerService

router = APIRouter(prefix="/fertilizers", tags=["fertilizers"])


@router.get("", response_model=list[FertilizerResponse])
def list_fertilizers(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    fertilizer_type: str | None = None,
    brand: str | None = None,
    is_organic: bool | None = None,
    tank_safe: bool | None = None,
    ctx: TenantContext = Depends(get_current_tenant),
    service: FertilizerService = Depends(get_fertilizer_service),
):
    filters: dict = {}
    if fertilizer_type:
        filters["fertilizer_type"] = fertilizer_type
    if brand:
        filters["brand"] = brand
    if is_organic is not None:
        filters["is_organic"] = is_organic
    if tank_safe is not None:
        filters["tank_safe"] = tank_safe
    items, _total = service.list_fertilizers(offset, limit, filters or None, tenant_key=ctx.tenant_key)
    return [_fert_response(f) for f in items]


@router.post("", response_model=FertilizerResponse, status_code=201)
def create_fertilizer(
    body: FertilizerCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: FertilizerService = Depends(get_fertilizer_service),
):
    fert = Fertilizer(**body.model_dump(), tenant_key=ctx.tenant_key)
    created = service.create_fertilizer(fert)
    return _fert_response(created)


@router.get("/{key}", response_model=FertilizerResponse)
def get_fertilizer(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: FertilizerService = Depends(get_fertilizer_service),
):
    f = service.get_fertilizer(key, tenant_key=ctx.tenant_key)
    return _fert_response(f)


@router.put("/{key}", response_model=FertilizerResponse)
def update_fertilizer(
    key: str,
    body: FertilizerUpdate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: FertilizerService = Depends(get_fertilizer_service),
):
    service.get_fertilizer(key, tenant_key=ctx.tenant_key)
    data = body.model_dump(exclude_none=True)
    updated = service.update_fertilizer(key, data)
    return _fert_response(updated)


@router.delete("/{key}", status_code=204)
def delete_fertilizer(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: FertilizerService = Depends(get_fertilizer_service),
):
    service.get_fertilizer(key, tenant_key=ctx.tenant_key)
    service.delete_fertilizer(key)


@router.get("/{key}/stocks", response_model=list[StockResponse])
def list_stocks(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: FertilizerService = Depends(get_fertilizer_service),
):
    service.get_fertilizer(key, tenant_key=ctx.tenant_key)
    stocks = service.get_stocks(key)
    return [StockResponse(key=s.key or "", **s.model_dump(exclude={"key"})) for s in stocks]


@router.post("/{key}/stocks", response_model=StockResponse, status_code=201)
def create_stock(
    key: str,
    body: StockCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: FertilizerService = Depends(get_fertilizer_service),
):
    service.get_fertilizer(key, tenant_key=ctx.tenant_key)
    stock = FertilizerStock(fertilizer_key=key, **body.model_dump())
    created = service.create_stock(key, stock)
    return StockResponse(key=created.key or "", **created.model_dump(exclude={"key"}))


@router.put("/{key}/stocks/{sk}", response_model=StockResponse)
def update_stock(
    key: str,
    sk: str,
    body: StockUpdate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: FertilizerService = Depends(get_fertilizer_service),
):
    service.get_fertilizer(key, tenant_key=ctx.tenant_key)
    data = body.model_dump(exclude_none=True)
    updated = service.update_stock(sk, data)
    return StockResponse(key=updated.key or "", **updated.model_dump(exclude={"key"}))


@router.delete("/{key}/stocks/{sk}", status_code=204)
def delete_stock(
    key: str,
    sk: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: FertilizerService = Depends(get_fertilizer_service),
):
    service.get_fertilizer(key, tenant_key=ctx.tenant_key)
    service.delete_stock(sk)


@router.get("/{key}/incompatibilities", response_model=list[IncompatibilityResponse])
def list_incompatibilities(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: FertilizerService = Depends(get_fertilizer_service),
):
    service.get_fertilizer(key, tenant_key=ctx.tenant_key)
    return service.get_incompatibilities(key)


@router.post("/{key}/incompatibilities", response_model=IncompatibilityResponse, status_code=201)
def add_incompatibility(
    key: str,
    body: IncompatibilityCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: FertilizerService = Depends(get_fertilizer_service),
):
    service.get_fertilizer(key, tenant_key=ctx.tenant_key)
    service.add_incompatibility(key, body.other_key, body.reason, body.severity)
    return IncompatibilityResponse(
        fertilizer_key=body.other_key, product_name=None, reason=body.reason, severity=body.severity
    )


@router.delete("/{key}/incompatibilities/{other_key}", status_code=204)
def remove_incompatibility(
    key: str,
    other_key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: FertilizerService = Depends(get_fertilizer_service),
):
    service.get_fertilizer(key, tenant_key=ctx.tenant_key)
    service.remove_incompatibility(key, other_key)


@router.get("/{key}/nutrient-plans", response_model=list[NutrientPlanUsageResponse])
def list_nutrient_plan_usage(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: FertilizerService = Depends(get_fertilizer_service),
):
    service.get_fertilizer(key, tenant_key=ctx.tenant_key)
    return service.get_nutrient_plan_usage(key)
