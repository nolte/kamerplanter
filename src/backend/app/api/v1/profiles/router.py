from typing import Annotated

from fastapi import APIRouter, Depends, Path

from app.api.mapping import to_response
from app.api.v1.profiles.schemas import (
    GenerateDefaultProfilesResponse,
    NutrientProfileCreate,
    NutrientProfileResponse,
    RequirementProfileCreate,
    RequirementProfileResponse,
)
from app.common.auth import get_current_user
from app.common.dependencies import get_phase_service
from app.common.openapi_responses import NOT_FOUND_RESPONSE, UNAUTHORIZED_RESPONSE
from app.domain.engines.phase_resource_resolver import nutrient_profile_guidance
from app.domain.models.phase import NutrientProfile, RequirementProfile
from app.domain.services.phase_service import PhaseService

router = APIRouter(
    prefix="/profiles",
    tags=["profiles"],
    dependencies=[Depends(get_current_user)],
    responses={**UNAUTHORIZED_RESPONSE, **NOT_FOUND_RESPONSE},
)


def _nutrient_response_with_guidance(profile: NutrientProfile) -> NutrientProfileResponse:
    """Map a stored nutrient profile to its response, enriched with E8 guidance.

    The feed/pH-gating rules live in the domain (:func:`nutrient_profile_guidance`);
    this presentation-layer helper only maps their result onto the response so the
    plant-detail view can surface flush/rest (0:0:0) and pH warnings.
    """
    response = to_response(profile, NutrientProfileResponse)
    feed, micros_available, ph_note = nutrient_profile_guidance(
        profile.npk_ratio, profile.target_ec_ms, profile.target_ph
    )
    return response.model_copy(update={"feed": feed, "micros_available": micros_available, "ph_note": ph_note})


@router.get("/requirements/{phase_key}", response_model=RequirementProfileResponse)
def get_requirement_profile(
    phase_key: Annotated[str, Path(description="Document key of the phase.")],
    service: PhaseService = Depends(get_phase_service),
):
    """Return the environmental requirement profile for a phase."""
    p = service.get_requirement_profile(phase_key)
    return to_response(p, RequirementProfileResponse)


@router.post("/requirements", response_model=RequirementProfileResponse, status_code=201)
def create_requirement_profile(body: RequirementProfileCreate, service: PhaseService = Depends(get_phase_service)):
    """Create an environmental requirement profile."""
    profile = RequirementProfile(**body.model_dump())
    created = service.create_requirement_profile(profile)
    return to_response(created, RequirementProfileResponse)


@router.get("/nutrients/{phase_key}", response_model=NutrientProfileResponse)
def get_nutrient_profile(
    phase_key: Annotated[str, Path(description="Document key of the phase.")],
    service: PhaseService = Depends(get_phase_service),
):
    """Return the nutrient profile for a phase, enriched with E8 guidance."""
    p = service.get_nutrient_profile(phase_key)
    return _nutrient_response_with_guidance(p)


@router.post("/nutrients", response_model=NutrientProfileResponse, status_code=201)
def create_nutrient_profile(body: NutrientProfileCreate, service: PhaseService = Depends(get_phase_service)):
    """Create a nutrient profile."""
    profile = NutrientProfile(**body.model_dump())
    created = service.create_nutrient_profile(profile)
    return _nutrient_response_with_guidance(created)


@router.put("/requirements/{key}", response_model=RequirementProfileResponse)
def update_requirement_profile(
    key: Annotated[str, Path(description="Document key of the requirement profile.")],
    body: RequirementProfileCreate,
    service: PhaseService = Depends(get_phase_service),
):
    """Update an environmental requirement profile."""
    profile = RequirementProfile(**body.model_dump())
    updated = service.update_requirement_profile(key, profile)
    return to_response(updated, RequirementProfileResponse)


@router.put("/nutrients/{key}", response_model=NutrientProfileResponse)
def update_nutrient_profile(
    key: Annotated[str, Path(description="Document key of the nutrient profile.")],
    body: NutrientProfileCreate,
    service: PhaseService = Depends(get_phase_service),
):
    """Update a nutrient profile."""
    profile = NutrientProfile(**body.model_dump())
    updated = service.update_nutrient_profile(key, profile)
    return _nutrient_response_with_guidance(updated)


@router.post("/generate-defaults/{phase_key}", response_model=GenerateDefaultProfilesResponse)
def generate_default_profiles(
    phase_key: Annotated[str, Path(description="Document key of the phase.")],
    service: PhaseService = Depends(get_phase_service),
) -> GenerateDefaultProfilesResponse:
    """Generate and return the default requirement and nutrient profiles for a phase."""
    req, nut = service.generate_default_profiles(phase_key)
    return GenerateDefaultProfilesResponse(
        requirement_profile=to_response(req, RequirementProfileResponse),
        nutrient_profile=_nutrient_response_with_guidance(nut),
    )
