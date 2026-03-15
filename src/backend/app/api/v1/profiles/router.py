from fastapi import APIRouter, Depends

from app.api.v1.profiles.schemas import (
    NutrientProfileCreate,
    NutrientProfileResponse,
    RequirementProfileCreate,
    RequirementProfileResponse,
)
from app.common.dependencies import get_phase_service
from app.domain.models.phase import NutrientProfile, RequirementProfile
from app.domain.services.phase_service import PhaseService

router = APIRouter(prefix="/profiles", tags=["profiles"])

@router.get("/requirements/{phase_key}", response_model=RequirementProfileResponse)
def get_requirement_profile(phase_key: str, service: PhaseService = Depends(get_phase_service)):
    p = service.get_requirement_profile(phase_key)
    return RequirementProfileResponse(key=p.key or "", **p.model_dump(exclude={"key"}))

@router.post("/requirements", response_model=RequirementProfileResponse, status_code=201)
def create_requirement_profile(body: RequirementProfileCreate, service: PhaseService = Depends(get_phase_service)):
    profile = RequirementProfile(**body.model_dump())
    created = service.create_requirement_profile(profile)
    return RequirementProfileResponse(key=created.key or "", **created.model_dump(exclude={"key"}))

@router.get("/nutrients/{phase_key}", response_model=NutrientProfileResponse)
def get_nutrient_profile(phase_key: str, service: PhaseService = Depends(get_phase_service)):
    p = service.get_nutrient_profile(phase_key)
    return NutrientProfileResponse(key=p.key or "", **p.model_dump(exclude={"key"}))

@router.post("/nutrients", response_model=NutrientProfileResponse, status_code=201)
def create_nutrient_profile(body: NutrientProfileCreate, service: PhaseService = Depends(get_phase_service)):
    profile = NutrientProfile(**body.model_dump())
    created = service.create_nutrient_profile(profile)
    return NutrientProfileResponse(key=created.key or "", **created.model_dump(exclude={"key"}))

@router.put("/requirements/{key}", response_model=RequirementProfileResponse)
def update_requirement_profile(key: str, body: RequirementProfileCreate, service: PhaseService = Depends(get_phase_service)):
    profile = RequirementProfile(**body.model_dump())
    updated = service.update_requirement_profile(key, profile)
    return RequirementProfileResponse(key=updated.key or "", **updated.model_dump(exclude={"key"}))

@router.put("/nutrients/{key}", response_model=NutrientProfileResponse)
def update_nutrient_profile(key: str, body: NutrientProfileCreate, service: PhaseService = Depends(get_phase_service)):
    profile = NutrientProfile(**body.model_dump())
    updated = service.update_nutrient_profile(key, profile)
    return NutrientProfileResponse(key=updated.key or "", **updated.model_dump(exclude={"key"}))

@router.post("/generate-defaults/{phase_key}")
def generate_default_profiles(phase_key: str, service: PhaseService = Depends(get_phase_service)):
    req, nut = service.generate_default_profiles(phase_key)
    return {
        "requirement_profile": RequirementProfileResponse(key=req.key or "", **req.model_dump(exclude={"key"})),
        "nutrient_profile": NutrientProfileResponse(key=nut.key or "", **nut.model_dump(exclude={"key"})),
    }
