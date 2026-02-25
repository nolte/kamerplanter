from fastapi import APIRouter, Depends

from app.api.v1.cultivars.schemas import CultivarCreate, CultivarResponse
from app.common.dependencies import get_species_service
from app.domain.models.species import Cultivar
from app.domain.services.species_service import SpeciesService

router = APIRouter(prefix="/species/{species_key}/cultivars", tags=["cultivars"])

@router.get("", response_model=list[CultivarResponse])
def list_cultivars(species_key: str, service: SpeciesService = Depends(get_species_service)):
    cultivars = service.list_cultivars(species_key)
    return [CultivarResponse(key=c.key or "", **c.model_dump(exclude={"key"})) for c in cultivars]

@router.post("", response_model=CultivarResponse, status_code=201)
def create_cultivar(species_key: str, body: CultivarCreate, service: SpeciesService = Depends(get_species_service)):
    cultivar = Cultivar(species_key=species_key, **body.model_dump(exclude={"species_key"}))
    created = service.create_cultivar(cultivar)
    return CultivarResponse(key=created.key or "", **created.model_dump(exclude={"key"}))

@router.delete("/{cultivar_key}", status_code=204)
def delete_cultivar(species_key: str, cultivar_key: str, service: SpeciesService = Depends(get_species_service)):
    service.delete_cultivar(cultivar_key)
