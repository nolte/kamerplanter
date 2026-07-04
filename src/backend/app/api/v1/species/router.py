from fastapi import APIRouter, Depends, Query

from app.api.mapping import to_response
from app.api.v1.species.schemas import (
    ReferenceImageEntry,
    SpeciesCreate,
    SpeciesListResponse,
    SpeciesReferenceImagesResponse,
    SpeciesResponse,
)
from app.common.auth import get_current_user
from app.common.dependencies import get_family_repo, get_species_service
from app.config.settings import settings
from app.data_access.arango.botanical_family_repository import ArangoBotanicalFamilyRepository
from app.data_access.external.inference_service_client import InferenceServiceClient
from app.domain.models.species import Species
from app.domain.services.species_service import SpeciesService

router = APIRouter(prefix="/species", tags=["species"], dependencies=[Depends(get_current_user)])


def _species_response(s: Species, family_repo: ArangoBotanicalFamilyRepository) -> SpeciesResponse:
    family_name = None
    if s.family_key:
        fam = family_repo.get_by_key(s.family_key)
        if fam:
            family_name = fam.name
    return to_response(s, SpeciesResponse, family_name=family_name)


@router.get("", response_model=SpeciesListResponse)
def list_species(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    service: SpeciesService = Depends(get_species_service),
    family_repo: ArangoBotanicalFamilyRepository = Depends(get_family_repo),
):
    items, total = service.list_species(offset, limit)
    # Build family name cache to avoid N+1 queries
    family_keys = {s.family_key for s in items if s.family_key}
    family_map: dict[str, str] = {}
    for fk in family_keys:
        fam = family_repo.get_by_key(fk)
        if fam:
            family_map[fk] = fam.name
    return SpeciesListResponse(
        items=[to_response(s, SpeciesResponse, family_name=family_map.get(s.family_key or "")) for s in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/{key}", response_model=SpeciesResponse)
def get_species(
    key: str,
    service: SpeciesService = Depends(get_species_service),
    family_repo: ArangoBotanicalFamilyRepository = Depends(get_family_repo),
):
    s = service.get_species(key)
    return _species_response(s, family_repo)


@router.get("/{key}/reference-images", response_model=SpeciesReferenceImagesResponse)
def get_species_reference_images(
    key: str,
    service: SpeciesService = Depends(get_species_service),
):
    """Reference-image gallery for a species (REQ-029-A §4).

    Proxies the inference-service; returns an empty gallery when the service is
    disabled/unreachable or the index has no images for this species yet.
    """
    service.get_species(key)  # 404 if the species does not exist
    client = InferenceServiceClient(settings.inference_service_url)
    # Public gallery: never show images an admin has deselected.
    rows = client.list_references(key, active_only=True)
    images = [
        ReferenceImageEntry(
            source_url=r.get("source_url", ""),
            license=r.get("license"),
            attribution=r.get("attribution"),
            organ=r.get("organ"),
            source=r.get("source"),
        )
        for r in rows
        if r.get("source_url")
    ]
    return SpeciesReferenceImagesResponse(species_key=key, count=len(images), images=images)


@router.post("", response_model=SpeciesResponse, status_code=201)
def create_species(
    body: SpeciesCreate,
    service: SpeciesService = Depends(get_species_service),
    family_repo: ArangoBotanicalFamilyRepository = Depends(get_family_repo),
):
    species = Species(**body.model_dump())
    created = service.create_species(species)
    return _species_response(created, family_repo)


@router.put("/{key}", response_model=SpeciesResponse)
def update_species(
    key: str,
    body: SpeciesCreate,
    service: SpeciesService = Depends(get_species_service),
    family_repo: ArangoBotanicalFamilyRepository = Depends(get_family_repo),
):
    species = Species(**body.model_dump())
    updated = service.update_species(key, species)
    return _species_response(updated, family_repo)


@router.delete("/{key}", status_code=204)
def delete_species(key: str, service: SpeciesService = Depends(get_species_service)):
    service.delete_species(key)
