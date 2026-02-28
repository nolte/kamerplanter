from fastapi import APIRouter, Depends, Query

from app.api.v1.substrates.schemas import (
    BatchCreate,
    BatchResponse,
    PreparationResponse,
    PreparationStep,
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

@router.put("/{key}", response_model=SubstrateResponse)
def update_substrate(key: str, body: SubstrateCreate, service: SubstrateService = Depends(get_substrate_service)):
    substrate = Substrate(**body.model_dump())
    updated = service.update_substrate(key, substrate)
    return SubstrateResponse(key=updated.key or "", **updated.model_dump(exclude={"key"}))

@router.delete("/{key}", status_code=204)
def delete_substrate(key: str, service: SubstrateService = Depends(get_substrate_service)):
    service.delete_substrate(key)

@router.get("/{substrate_key}/batches", response_model=list[BatchResponse])
def list_batches(substrate_key: str, service: SubstrateService = Depends(get_substrate_service)):
    batches = service.list_batches(substrate_key)
    return [BatchResponse(key=b.key or "", **b.model_dump(exclude={"key"})) for b in batches]

@router.post("/batches", response_model=BatchResponse, status_code=201)
def create_batch(body: BatchCreate, service: SubstrateService = Depends(get_substrate_service)):
    batch = SubstrateBatch(**body.model_dump())
    created = service.create_batch(batch)
    return BatchResponse(key=created.key or "", **created.model_dump(exclude={"key"}))

@router.get("/batches/{key}", response_model=BatchResponse)
def get_batch(key: str, service: SubstrateService = Depends(get_substrate_service)):
    b = service.get_batch(key)
    return BatchResponse(key=b.key or "", **b.model_dump(exclude={"key"}))

@router.put("/batches/{key}", response_model=BatchResponse)
def update_batch(key: str, body: BatchCreate, service: SubstrateService = Depends(get_substrate_service)):
    batch = SubstrateBatch(**body.model_dump())
    updated = service.update_batch(key, batch)
    return BatchResponse(key=updated.key or "", **updated.model_dump(exclude={"key"}))

@router.delete("/batches/{key}", status_code=204)
def delete_batch(key: str, service: SubstrateService = Depends(get_substrate_service)):
    service.delete_batch(key)

@router.post("/batches/{key}/check-reusability", response_model=ReusabilityResponse)
def check_reusability(key: str, service: SubstrateService = Depends(get_substrate_service)):
    can_reuse, issues, prep_steps, prep_time, ready_date = service.check_reusability(key)
    return ReusabilityResponse(
        can_reuse=can_reuse,
        treatments=issues,
        preparation_steps=[PreparationStep(**s) for s in prep_steps],
        estimated_prep_time_hours=prep_time,
        ready_date=ready_date,
    )

@router.post("/batches/{key}/prepare-reuse", response_model=PreparationResponse)
def prepare_reuse(key: str, service: SubstrateService = Depends(get_substrate_service)):
    result = service.prepare_reuse(key)
    return PreparationResponse(
        can_reuse=result["can_reuse"],
        issues=result["issues"],
        preparation_steps=[PreparationStep(**s) for s in result["preparation_steps"]],
        estimated_prep_time_hours=result["estimated_prep_time_hours"],
        ready_date=result["ready_date"],
    )

@router.post("/batches/{batch_key}/assign-slot/{slot_key}", status_code=201)
def assign_batch_to_slot(
    batch_key: str,
    slot_key: str,
    service: SubstrateService = Depends(get_substrate_service),
):
    service.assign_batch_to_slot(batch_key, slot_key)
    return {"status": "assigned", "batch_key": batch_key, "slot_key": slot_key}
