from fastapi import APIRouter, Depends

from app.api.mapping import to_response
from app.api.v1.profiles.schemas import (
    NutrientProfileCreate,
    NutrientProfileResponse,
    RequirementProfileCreate,
    RequirementProfileResponse,
)
from app.common.auth import get_current_user
from app.common.dependencies import get_phase_service
from app.domain.engines.phase_resource_resolver import ph_micronutrient_availability
from app.domain.models.phase import NutrientProfile, RequirementProfile
from app.domain.services.phase_service import PhaseService

router = APIRouter(prefix="/profiles", tags=["profiles"], dependencies=[Depends(get_current_user)])


def _nutrient_response_with_guidance(profile: NutrientProfile) -> NutrientProfileResponse:
    """Map a stored nutrient profile to its response, enriched with E8 guidance.

    The pH-gated micronutrient availability (REQ-003 E8) is derived from the phase
    target pH via the phase resource resolver, and ``feed`` is derived from the stored
    NPK/EC so the plant-detail view can surface flush/rest (0:0:0) and pH warnings
    instead of the raw values alone.
    """
    response = to_response(profile, NutrientProfileResponse)
    micros_available, ph_note = ph_micronutrient_availability(profile.target_ph)
    feed = tuple(profile.npk_ratio) != (0, 0, 0) or profile.target_ec_ms > 0
    return response.model_copy(update={"feed": feed, "micros_available": micros_available, "ph_note": ph_note})


@router.get("/requirements/{phase_key}", response_model=RequirementProfileResponse)
def get_requirement_profile(phase_key: str, service: PhaseService = Depends(get_phase_service)):
    p = service.get_requirement_profile(phase_key)
    return to_response(p, RequirementProfileResponse)


@router.post("/requirements", response_model=RequirementProfileResponse, status_code=201)
def create_requirement_profile(body: RequirementProfileCreate, service: PhaseService = Depends(get_phase_service)):
    profile = RequirementProfile(**body.model_dump())
    created = service.create_requirement_profile(profile)
    return to_response(created, RequirementProfileResponse)


@router.get("/nutrients/{phase_key}", response_model=NutrientProfileResponse)
def get_nutrient_profile(phase_key: str, service: PhaseService = Depends(get_phase_service)):
    p = service.get_nutrient_profile(phase_key)
    return _nutrient_response_with_guidance(p)


@router.post("/nutrients", response_model=NutrientProfileResponse, status_code=201)
def create_nutrient_profile(body: NutrientProfileCreate, service: PhaseService = Depends(get_phase_service)):
    profile = NutrientProfile(**body.model_dump())
    created = service.create_nutrient_profile(profile)
    return _nutrient_response_with_guidance(created)


@router.put("/requirements/{key}", response_model=RequirementProfileResponse)
def update_requirement_profile(
    key: str,
    body: RequirementProfileCreate,
    service: PhaseService = Depends(get_phase_service),
):
    profile = RequirementProfile(**body.model_dump())
    updated = service.update_requirement_profile(key, profile)
    return to_response(updated, RequirementProfileResponse)


@router.put("/nutrients/{key}", response_model=NutrientProfileResponse)
def update_nutrient_profile(key: str, body: NutrientProfileCreate, service: PhaseService = Depends(get_phase_service)):
    profile = NutrientProfile(**body.model_dump())
    updated = service.update_nutrient_profile(key, profile)
    return _nutrient_response_with_guidance(updated)


@router.post("/generate-defaults/{phase_key}")
def generate_default_profiles(phase_key: str, service: PhaseService = Depends(get_phase_service)):
    req, nut = service.generate_default_profiles(phase_key)
    return {
        "requirement_profile": to_response(req, RequirementProfileResponse),
        "nutrient_profile": _nutrient_response_with_guidance(nut),
    }
