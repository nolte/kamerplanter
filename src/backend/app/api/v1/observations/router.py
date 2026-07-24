from fastapi import APIRouter, Depends

from app.api.v1.observations.schemas import TimeseriesStatusResponse
from app.common.auth import get_current_user
from app.common.dependencies import get_observation_service
from app.common.openapi_responses import UNAUTHORIZED_RESPONSE
from app.domain.services.observation_service import ObservationService

router = APIRouter(
    prefix="/observations",
    tags=["observations"],
    dependencies=[Depends(get_current_user)],
    responses=UNAUTHORIZED_RESPONSE,
)


@router.get("/status", response_model=TimeseriesStatusResponse)
def get_timeseries_status(
    service: ObservationService = Depends(get_observation_service),
) -> TimeseriesStatusResponse:
    """Report whether the time-series backend is available for sensor readings."""
    return TimeseriesStatusResponse(available=service.is_available())
