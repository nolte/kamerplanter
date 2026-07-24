from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path

from app.api.mapping import to_response
from app.api.v1.phases.schemas import (
    CurrentPhaseResponse,
    PhaseHistoryDateUpdate,
    PhaseHistoryResponse,
    TransitionRequest,
)
from app.api.v1.plant_instances.schemas import PlantResponse
from app.common.auth import get_current_user
from app.common.dependencies import get_phase_service, get_plant_instance_service
from app.common.openapi_responses import NOT_FOUND_RESPONSE, UNAUTHORIZED_RESPONSE
from app.domain.services.phase_service import PhaseService
from app.domain.services.plant_instance_service import PlantInstanceService

router = APIRouter(
    prefix="/plant-instances/{plant_key}/phases",
    tags=["phases"],
    dependencies=[Depends(get_current_user)],
    responses={**UNAUTHORIZED_RESPONSE, **NOT_FOUND_RESPONSE},
)


@router.get("/current", response_model=CurrentPhaseResponse)
def get_current_phase(
    plant_key: Annotated[str, Path(description="Document key of the plant instance.")],
    service: PhaseService = Depends(get_phase_service),
):
    """Return the plant instance's current phase snapshot."""
    result = service.get_current_phase(plant_key)
    return CurrentPhaseResponse(**result)


@router.post("/transition", response_model=PlantResponse)
def transition_phase(
    plant_key: Annotated[str, Path(description="Document key of the plant instance.")],
    body: TransitionRequest,
    service: PhaseService = Depends(get_phase_service),
    plant_service: PlantInstanceService = Depends(get_plant_instance_service),
):
    """Transition a plant instance to a target phase."""
    plant = service.transition_phase(plant_key, body.target_phase_key, body.reason, force=body.force)
    phase_name = plant_service.resolve_phase_name(plant.current_phase_key or "")
    return to_response(plant, PlantResponse, current_phase=phase_name)


@router.get("/history", response_model=list[PhaseHistoryResponse])
def get_phase_history(
    plant_key: Annotated[str, Path(description="Document key of the plant instance.")],
    service: PhaseService = Depends(get_phase_service),
):
    """List the plant instance's phase-transition history."""
    history = service.get_phase_history(plant_key)
    return [to_response(h, PhaseHistoryResponse) for h in history]


@router.patch("/history/{history_key}", response_model=PhaseHistoryResponse)
def update_phase_history_dates(
    plant_key: Annotated[str, Path(description="Document key of the plant instance.")],
    history_key: Annotated[str, Path(description="Document key of the phase-history entry.")],
    body: PhaseHistoryDateUpdate,
    service: PhaseService = Depends(get_phase_service),
):
    """Adjust the entered/exited dates of a phase-history entry."""
    if body.entered_at is None and body.exited_at is None:
        raise HTTPException(status_code=422, detail="At least one of entered_at or exited_at must be provided")
    try:
        h = service.update_phase_history_dates(plant_key, history_key, body.entered_at, body.exited_at)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return to_response(h, PhaseHistoryResponse)


@router.delete("/history/{history_key}", status_code=204)
def delete_phase_history(
    plant_key: Annotated[str, Path(description="Document key of the plant instance.")],
    history_key: Annotated[str, Path(description="Document key of the phase-history entry.")],
    service: PhaseService = Depends(get_phase_service),
):
    """Delete a phase-history entry of a plant instance."""
    try:
        service.delete_phase_history(plant_key, history_key)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
