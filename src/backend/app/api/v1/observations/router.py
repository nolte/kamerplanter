from fastapi import APIRouter, Depends

from app.api.v1.observations.schemas import TimeseriesStatusResponse
from app.common.dependencies import get_observation_service
from app.domain.services.observation_service import ObservationService

router = APIRouter(prefix="/observations", tags=["observations"])


@router.get("/status", response_model=TimeseriesStatusResponse)
def get_timeseries_status(
    service: ObservationService = Depends(get_observation_service),
) -> TimeseriesStatusResponse:
    return TimeseriesStatusResponse(available=service.is_available())
