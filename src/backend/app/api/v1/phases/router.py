from fastapi import APIRouter, Depends

from app.api.v1.phases.schemas import CurrentPhaseResponse, PhaseHistoryResponse, TransitionRequest
from app.api.v1.plant_instances.schemas import PlantResponse
from app.common.dependencies import get_phase_service
from app.domain.services.phase_service import PhaseService

router = APIRouter(prefix="/plant-instances/{plant_key}/phases", tags=["phases"])

@router.get("/current", response_model=CurrentPhaseResponse)
def get_current_phase(plant_key: str, service: PhaseService = Depends(get_phase_service)):
    result = service.get_current_phase(plant_key)
    return CurrentPhaseResponse(**result)

@router.post("/transition", response_model=PlantResponse)
def transition_phase(plant_key: str, body: TransitionRequest, service: PhaseService = Depends(get_phase_service)):
    plant = service.transition_phase(plant_key, body.target_phase_key, body.reason)
    return PlantResponse(key=plant.key or "", **plant.model_dump(exclude={"key"}))

@router.get("/history", response_model=list[PhaseHistoryResponse])
def get_phase_history(plant_key: str, service: PhaseService = Depends(get_phase_service)):
    history = service.get_phase_history(plant_key)
    return [PhaseHistoryResponse(key=h.key or "", **h.model_dump(exclude={"key"})) for h in history]
