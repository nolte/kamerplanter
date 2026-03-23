from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.phases.schemas import (
    CurrentPhaseResponse,
    PhaseHistoryDateUpdate,
    PhaseHistoryResponse,
    TransitionRequest,
)
from app.api.v1.plant_instances.schemas import PlantResponse
from app.common.auth import get_current_user
from app.common.dependencies import get_phase_service, get_plant_instance_service
from app.domain.services.phase_service import PhaseService
from app.domain.services.plant_instance_service import PlantInstanceService

router = APIRouter(
    prefix="/plant-instances/{plant_key}/phases",
    tags=["phases"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/current", response_model=CurrentPhaseResponse)
def get_current_phase(plant_key: str, service: PhaseService = Depends(get_phase_service)):
    result = service.get_current_phase(plant_key)
    return CurrentPhaseResponse(**result)


@router.post("/transition", response_model=PlantResponse)
def transition_phase(
    plant_key: str,
    body: TransitionRequest,
    service: PhaseService = Depends(get_phase_service),
    plant_service: PlantInstanceService = Depends(get_plant_instance_service),
):
    plant = service.transition_phase(plant_key, body.target_phase_key, body.reason, force=body.force)
    phase_name = plant_service.resolve_phase_name(plant.current_phase_key or "")
    return PlantResponse(key=plant.key or "", current_phase=phase_name, **plant.model_dump(exclude={"key"}))


@router.get("/history", response_model=list[PhaseHistoryResponse])
def get_phase_history(plant_key: str, service: PhaseService = Depends(get_phase_service)):
    history = service.get_phase_history(plant_key)
    return [PhaseHistoryResponse(key=h.key or "", **h.model_dump(exclude={"key"})) for h in history]


@router.patch("/history/{history_key}", response_model=PhaseHistoryResponse)
def update_phase_history_dates(
    plant_key: str,
    history_key: str,
    body: PhaseHistoryDateUpdate,
    service: PhaseService = Depends(get_phase_service),
):
    if body.entered_at is None and body.exited_at is None:
        raise HTTPException(status_code=422, detail="At least one of entered_at or exited_at must be provided")
    try:
        h = service.update_phase_history_dates(plant_key, history_key, body.entered_at, body.exited_at)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return PhaseHistoryResponse(key=h.key or "", **h.model_dump(exclude={"key"}))


@router.delete("/history/{history_key}", status_code=204)
def delete_phase_history(
    plant_key: str,
    history_key: str,
    service: PhaseService = Depends(get_phase_service),
):
    try:
        service.delete_phase_history(plant_key, history_key)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
