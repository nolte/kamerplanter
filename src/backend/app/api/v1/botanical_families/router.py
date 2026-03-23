from fastapi import APIRouter, Depends, Query

from app.api.v1.botanical_families.schemas import FamilyCreate, FamilyResponse
from app.api.v1.species.schemas import SpeciesResponse
from app.common.auth import get_current_user
from app.common.dependencies import get_family_repo
from app.data_access.arango.botanical_family_repository import ArangoBotanicalFamilyRepository
from app.domain.models.botanical_family import BotanicalFamily

router = APIRouter(prefix="/botanical-families", tags=["botanical-families"], dependencies=[Depends(get_current_user)])


def _family_response(f: BotanicalFamily, repo: ArangoBotanicalFamilyRepository) -> FamilyResponse:
    count = repo.get_species_count_by_family(f.key or "")
    return FamilyResponse(key=f.key or "", species_count=count, **f.model_dump(exclude={"key"}))


@router.get("", response_model=list[FamilyResponse])
def list_families(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    repo: ArangoBotanicalFamilyRepository = Depends(get_family_repo),
):
    families, total = repo.get_all_families(offset, limit)
    return [_family_response(f, repo) for f in families]


@router.get("/{key}", response_model=FamilyResponse)
def get_family(key: str, repo: ArangoBotanicalFamilyRepository = Depends(get_family_repo)):
    f = repo.get_by_key(key)
    if f is None:
        from app.common.exceptions import NotFoundError

        raise NotFoundError("BotanicalFamily", key)
    return _family_response(f, repo)


@router.get("/{key}/species", response_model=list[SpeciesResponse])
def get_family_species(key: str, repo: ArangoBotanicalFamilyRepository = Depends(get_family_repo)):
    f = repo.get_by_key(key)
    if f is None:
        from app.common.exceptions import NotFoundError

        raise NotFoundError("BotanicalFamily", key)
    species_list = repo.get_species_by_family(key)
    return [SpeciesResponse(key=s.key or "", **s.model_dump(exclude={"key"})) for s in species_list]


@router.post("", response_model=FamilyResponse, status_code=201)
def create_family(body: FamilyCreate, repo: ArangoBotanicalFamilyRepository = Depends(get_family_repo)):
    family = BotanicalFamily(**body.model_dump())
    created = repo.create_family(family)
    return _family_response(created, repo)


@router.put("/{key}", response_model=FamilyResponse)
def update_family(key: str, body: FamilyCreate, repo: ArangoBotanicalFamilyRepository = Depends(get_family_repo)):
    family = BotanicalFamily(**body.model_dump())
    updated = repo.update_family(key, family)
    return _family_response(updated, repo)


@router.delete("/{key}", status_code=204)
def delete_family(key: str, repo: ArangoBotanicalFamilyRepository = Depends(get_family_repo)):
    repo.delete_family(key)
