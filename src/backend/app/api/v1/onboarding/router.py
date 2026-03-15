from fastapi import APIRouter, Depends

from app.api.v1.onboarding.schemas import (
    OnboardingCompleteRequest,
    OnboardingProgressUpdate,
    OnboardingStateResponse,
)
from app.common.dependencies import get_onboarding_service
from app.domain.services.onboarding_service import OnboardingService

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

# Note: In a full implementation, user_key comes from the auth token.
# For now, we accept it as a query param for development.


@router.get("/state", response_model=OnboardingStateResponse)
def get_onboarding_state(
    user_key: str = "demo",
    service: OnboardingService = Depends(get_onboarding_service),
):
    state = service.get_state(user_key)
    return OnboardingStateResponse(key=state.key or "", **state.model_dump(exclude={"key"}))


@router.post("/complete")
def complete_onboarding(
    body: OnboardingCompleteRequest,
    user_key: str = "demo",
    service: OnboardingService = Depends(get_onboarding_service),
):
    result = service.complete_wizard(
        user_key=user_key,
        kit_id=body.kit_id,
        experience_level=body.experience_level.value if body.experience_level else None,
        site_name=body.site_name,
        plant_count=body.plant_count,
        has_ro_system=body.has_ro_system,
        tap_water_ec_ms=body.tap_water_ec_ms,
        tap_water_ph=body.tap_water_ph,
    )
    return result


@router.post("/skip", response_model=OnboardingStateResponse)
def skip_onboarding(
    user_key: str = "demo",
    service: OnboardingService = Depends(get_onboarding_service),
):
    state = service.skip_wizard(user_key)
    return OnboardingStateResponse(key=state.key or "", **state.model_dump(exclude={"key"}))


@router.patch("/state", response_model=OnboardingStateResponse)
def update_onboarding_progress(
    body: OnboardingProgressUpdate,
    user_key: str = "demo",
    service: OnboardingService = Depends(get_onboarding_service),
):
    kwargs = {}
    if body.selected_kit_id is not None:
        kwargs["selected_kit_id"] = body.selected_kit_id
    if body.selected_experience_level is not None:
        kwargs["selected_experience_level"] = body.selected_experience_level.value
    state = service.save_progress(user_key, body.wizard_step, **kwargs)
    return OnboardingStateResponse(key=state.key or "", **state.model_dump(exclude={"key"}))
