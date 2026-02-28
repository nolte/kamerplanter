from fastapi import APIRouter, Depends, Query

from app.api.v1.fertilizers.schemas import (
    FertilizerCreate,
    FertilizerResponse,
    FertilizerUpdate,
    IncompatibilityCreate,
    IncompatibilityResponse,
    StockCreate,
    StockResponse,
    StockUpdate,
)
from app.common.dependencies import get_fertilizer_service
from app.domain.models.fertilizer import Fertilizer, FertilizerStock
from app.domain.services.fertilizer_service import FertilizerService

router = APIRouter(prefix="/fertilizers", tags=["fertilizers"])


def _fert_response(f: Fertilizer) -> FertilizerResponse:
    return FertilizerResponse(key=f.key or "", **f.model_dump(exclude={"key"}))


# ── Fertilizer CRUD ──────────────────────────────────────────────────

@router.get("", response_model=list[FertilizerResponse])
def list_fertilizers(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    fertilizer_type: str | None = None,
    brand: str | None = None,
    is_organic: bool | None = None,
    tank_safe: bool | None = None,
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
    items, _total = service.list_fertilizers(offset, limit, filters or None)
    return [_fert_response(f) for f in items]


@router.post("", response_model=FertilizerResponse, status_code=201)
def create_fertilizer(
    body: FertilizerCreate,
    service: FertilizerService = Depends(get_fertilizer_service),
):
    fert = Fertilizer(**body.model_dump())
    created = service.create_fertilizer(fert)
    return _fert_response(created)


@router.get("/{key}", response_model=FertilizerResponse)
def get_fertilizer(key: str, service: FertilizerService = Depends(get_fertilizer_service)):
    f = service.get_fertilizer(key)
    return _fert_response(f)


@router.put("/{key}", response_model=FertilizerResponse)
def update_fertilizer(
    key: str,
    body: FertilizerUpdate,
    service: FertilizerService = Depends(get_fertilizer_service),
):
    data = body.model_dump(exclude_none=True)
    updated = service.update_fertilizer(key, data)
    return _fert_response(updated)


@router.delete("/{key}", status_code=204)
def delete_fertilizer(key: str, service: FertilizerService = Depends(get_fertilizer_service)):
    service.delete_fertilizer(key)


# ── Stock CRUD ───────────────────────────────────────────────────────

@router.get("/{key}/stocks", response_model=list[StockResponse])
def list_stocks(key: str, service: FertilizerService = Depends(get_fertilizer_service)):
    stocks = service.get_stocks(key)
    return [StockResponse(key=s.key or "", **s.model_dump(exclude={"key"})) for s in stocks]


@router.post("/{key}/stocks", response_model=StockResponse, status_code=201)
def create_stock(
    key: str,
    body: StockCreate,
    service: FertilizerService = Depends(get_fertilizer_service),
):
    stock = FertilizerStock(fertilizer_key=key, **body.model_dump())
    created = service.create_stock(key, stock)
    return StockResponse(key=created.key or "", **created.model_dump(exclude={"key"}))


@router.put("/{key}/stocks/{sk}", response_model=StockResponse)
def update_stock(
    key: str,
    sk: str,
    body: StockUpdate,
    service: FertilizerService = Depends(get_fertilizer_service),
):
    data = body.model_dump(exclude_none=True)
    updated = service.update_stock(sk, data)
    return StockResponse(key=updated.key or "", **updated.model_dump(exclude={"key"}))


@router.delete("/{key}/stocks/{sk}", status_code=204)
def delete_stock(
    key: str,
    sk: str,
    service: FertilizerService = Depends(get_fertilizer_service),
):
    service.delete_stock(sk)


# ── Incompatibilities ────────────────────────────────────────────────

@router.get("/{key}/incompatibilities", response_model=list[IncompatibilityResponse])
def list_incompatibilities(
    key: str,
    service: FertilizerService = Depends(get_fertilizer_service),
):
    return service.get_incompatibilities(key)


@router.post("/{key}/incompatibilities", response_model=IncompatibilityResponse, status_code=201)
def add_incompatibility(
    key: str,
    body: IncompatibilityCreate,
    service: FertilizerService = Depends(get_fertilizer_service),
):
    service.add_incompatibility(key, body.other_key, body.reason, body.severity)
    return IncompatibilityResponse(
        fertilizer_key=body.other_key,
        product_name=None,
        reason=body.reason,
        severity=body.severity,
    )


@router.delete("/{key}/incompatibilities/{other_key}", status_code=204)
def remove_incompatibility(
    key: str,
    other_key: str,
    service: FertilizerService = Depends(get_fertilizer_service),
):
    service.remove_incompatibility(key, other_key)
