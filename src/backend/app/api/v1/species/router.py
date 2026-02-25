from fastapi import APIRouter, Depends, Query

from app.api.v1.species.schemas import SpeciesCreate, SpeciesListResponse, SpeciesResponse
from app.common.dependencies import get_species_service
from app.domain.models.species import Species
from app.domain.services.species_service import SpeciesService

router = APIRouter(prefix="/species", tags=["species"])

@router.get("", response_model=SpeciesListResponse)
def list_species(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: SpeciesService = Depends(get_species_service),
):
    items, total = service.list_species(offset, limit)
    return SpeciesListResponse(
        items=[SpeciesResponse(key=s.key or "", **s.model_dump(exclude={"key"})) for s in items],
        total=total, offset=offset, limit=limit,
    )

@router.get("/{key}", response_model=SpeciesResponse)
def get_species(key: str, service: SpeciesService = Depends(get_species_service)):
    s = service.get_species(key)
    return SpeciesResponse(key=s.key or "", **s.model_dump(exclude={"key"}))

@router.post("", response_model=SpeciesResponse, status_code=201)
def create_species(body: SpeciesCreate, service: SpeciesService = Depends(get_species_service)):
    species = Species(**body.model_dump())
    created = service.create_species(species)
    return SpeciesResponse(key=created.key or "", **created.model_dump(exclude={"key"}))

@router.put("/{key}", response_model=SpeciesResponse)
def update_species(key: str, body: SpeciesCreate, service: SpeciesService = Depends(get_species_service)):
    species = Species(**body.model_dump())
    updated = service.update_species(key, species)
    return SpeciesResponse(key=updated.key or "", **updated.model_dump(exclude={"key"}))

@router.delete("/{key}", status_code=204)
def delete_species(key: str, service: SpeciesService = Depends(get_species_service)):
    service.delete_species(key)
