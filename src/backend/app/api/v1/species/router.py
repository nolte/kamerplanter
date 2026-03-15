from fastapi import APIRouter, Depends, Query

from app.api.v1.species.schemas import SpeciesCreate, SpeciesListResponse, SpeciesResponse
from app.common.dependencies import get_family_repo, get_species_service
from app.data_access.arango.botanical_family_repository import ArangoBotanicalFamilyRepository
from app.domain.models.species import Species
from app.domain.services.species_service import SpeciesService

router = APIRouter(prefix="/species", tags=["species"])


def _species_response(s: Species, family_repo: ArangoBotanicalFamilyRepository) -> SpeciesResponse:
    family_name = None
    if s.family_key:
        fam = family_repo.get_by_key(s.family_key)
        if fam:
            family_name = fam.name
    return SpeciesResponse(key=s.key or "", family_name=family_name, **s.model_dump(exclude={"key"}))


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
        items=[
            SpeciesResponse(
                key=s.key or "",
                family_name=family_map.get(s.family_key or ""),
                **s.model_dump(exclude={"key"}),
            )
            for s in items
        ],
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
