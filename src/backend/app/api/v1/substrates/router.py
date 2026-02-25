from fastapi import APIRouter, Depends, Query

from app.api.v1.substrates.schemas import (
    BatchCreate,
    BatchResponse,
    ReusabilityResponse,
    SubstrateCreate,
    SubstrateResponse,
)
from app.common.dependencies import get_substrate_service
from app.domain.models.substrate import Substrate, SubstrateBatch
from app.domain.services.substrate_service import SubstrateService

router = APIRouter(prefix="/substrates", tags=["substrates"])

@router.get("", response_model=list[SubstrateResponse])
def list_substrates(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: SubstrateService = Depends(get_substrate_service),
):
    items, total = service.list_substrates(offset, limit)
    return [SubstrateResponse(key=s.key or "", **s.model_dump(exclude={"key"})) for s in items]

@router.post("", response_model=SubstrateResponse, status_code=201)
def create_substrate(body: SubstrateCreate, service: SubstrateService = Depends(get_substrate_service)):
    substrate = Substrate(**body.model_dump())
    created = service.create_substrate(substrate)
    return SubstrateResponse(key=created.key or "", **created.model_dump(exclude={"key"}))

@router.get("/{key}", response_model=SubstrateResponse)
def get_substrate(key: str, service: SubstrateService = Depends(get_substrate_service)):
    s = service.get_substrate(key)
    return SubstrateResponse(key=s.key or "", **s.model_dump(exclude={"key"}))

@router.post("/batches", response_model=BatchResponse, status_code=201)
def create_batch(body: BatchCreate, service: SubstrateService = Depends(get_substrate_service)):
    batch = SubstrateBatch(**body.model_dump())
    created = service.create_batch(batch)
    return BatchResponse(key=created.key or "", **created.model_dump(exclude={"key"}))

@router.get("/batches/{key}", response_model=BatchResponse)
def get_batch(key: str, service: SubstrateService = Depends(get_substrate_service)):
    b = service.get_batch(key)
    return BatchResponse(key=b.key or "", **b.model_dump(exclude={"key"}))

@router.post("/batches/{key}/check-reusability", response_model=ReusabilityResponse)
def check_reusability(key: str, service: SubstrateService = Depends(get_substrate_service)):
    can_reuse, treatments = service.check_reusability(key)
    return ReusabilityResponse(can_reuse=can_reuse, treatments=treatments)
