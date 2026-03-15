from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends

from app.common.dependencies import get_species_service

if TYPE_CHECKING:
    from app.api.v1.companion_planting.schemas import CompatibilitySet, IncompatibilitySet
    from app.domain.services.species_service import SpeciesService

router = APIRouter(prefix="/companion-planting", tags=["companion-planting"])


@router.get("/species/{species_key}/compatible")
def get_compatible(species_key: str, service: SpeciesService = Depends(get_species_service)):
    return service.get_compatible_species(species_key)


@router.get("/species/{species_key}/incompatible")
def get_incompatible(species_key: str, service: SpeciesService = Depends(get_species_service)):
    return service.get_incompatible_species(species_key)


@router.post("/compatible", status_code=201)
def set_compatible(body: CompatibilitySet, service: SpeciesService = Depends(get_species_service)):
    from app.common.dependencies import get_graph_repo

    graph = get_graph_repo()
    graph.set_compatibility(body.from_species_key, body.to_species_key, body.score)
    return {"status": "created"}


@router.post("/incompatible", status_code=201)
def set_incompatible(body: IncompatibilitySet, service: SpeciesService = Depends(get_species_service)):
    from app.common.dependencies import get_graph_repo

    graph = get_graph_repo()
    graph.set_incompatibility(body.from_species_key, body.to_species_key, body.reason)
    return {"status": "created"}


@router.get("/species/{species_key}/recommendations")
def get_companion_recommendations(species_key: str, service: SpeciesService = Depends(get_species_service)):
    return service.get_companion_recommendations(species_key)
