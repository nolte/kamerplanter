from fastapi import APIRouter, Depends, Query

from app.api.v1.starter_kits.schemas import ApplyKitRequest, StarterKitResponse
from app.common.dependencies import get_onboarding_service, get_starter_kit_service
from app.domain.services.onboarding_service import OnboardingService
from app.domain.services.starter_kit_service import StarterKitService

router = APIRouter(prefix="/starter-kits", tags=["starter-kits"])


@router.get("", response_model=list[StarterKitResponse])
def list_starter_kits(
    difficulty: str | None = Query(None),
    service: StarterKitService = Depends(get_starter_kit_service),
):
    kits = service.list_kits(difficulty)
    return [StarterKitResponse(key=k.key or "", **k.model_dump(exclude={"key"})) for k in kits]


@router.get("/{kit_id}", response_model=StarterKitResponse)
def get_starter_kit(
    kit_id: str,
    service: StarterKitService = Depends(get_starter_kit_service),
):
    kit = service.get_kit_by_id(kit_id)
    return StarterKitResponse(key=kit.key or "", **kit.model_dump(exclude={"key"}))


@router.post("/{kit_id}/apply")
def apply_starter_kit(
    kit_id: str,
    body: ApplyKitRequest,
    user_key: str = "demo",
    onboarding: OnboardingService = Depends(get_onboarding_service),
):
    result = onboarding.complete_wizard(
        user_key=user_key,
        kit_id=kit_id,
        site_name=body.site_name,
        plant_count=body.plant_count,
    )
    return result
