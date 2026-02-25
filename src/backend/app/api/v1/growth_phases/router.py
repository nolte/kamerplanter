from fastapi import APIRouter, Depends, Query

from app.api.v1.growth_phases.schemas import PhaseCreate, PhaseResponse
from app.common.dependencies import get_phase_service
from app.domain.models.lifecycle import GrowthPhase
from app.domain.services.phase_service import PhaseService

router = APIRouter(prefix="/growth-phases", tags=["growth-phases"])

@router.get("", response_model=list[PhaseResponse])
def list_phases(lifecycle_key: str = Query(...), service: PhaseService = Depends(get_phase_service)):
    phases = service.get_phases(lifecycle_key)
    return [PhaseResponse(key=p.key or "", **p.model_dump(exclude={"key"})) for p in phases]

@router.get("/{key}", response_model=PhaseResponse)
def get_phase(key: str, service: PhaseService = Depends(get_phase_service)):
    p = service.get_phase(key)
    return PhaseResponse(key=p.key or "", **p.model_dump(exclude={"key"}))

@router.post("", response_model=PhaseResponse, status_code=201)
def create_phase(body: PhaseCreate, service: PhaseService = Depends(get_phase_service)):
    phase = GrowthPhase(**body.model_dump())
    created = service.create_phase(phase)
    return PhaseResponse(key=created.key or "", **created.model_dump(exclude={"key"}))

@router.put("/{key}", response_model=PhaseResponse)
def update_phase(key: str, body: PhaseCreate, service: PhaseService = Depends(get_phase_service)):
    phase = GrowthPhase(**body.model_dump())
    updated = service.update_phase(key, phase)
    return PhaseResponse(key=updated.key or "", **updated.model_dump(exclude={"key"}))

@router.delete("/{key}", status_code=204)
def delete_phase(key: str, service: PhaseService = Depends(get_phase_service)):
    service.delete_phase(key)
