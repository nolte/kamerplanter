from typing import Annotated

from fastapi import APIRouter, Depends, Path

from app.api.mapping import to_response
from app.api.v1.botanical_families.schemas import FamilyCreate, FamilyResponse
from app.api.v1.species.schemas import SpeciesResponse
from app.common.auth import get_current_user
from app.common.dependencies import get_family_repo
from app.common.openapi_responses import AUTH_CRUD_RESPONSES
from app.common.pagination import PaginationParams, get_pagination
from app.data_access.arango.botanical_family_repository import ArangoBotanicalFamilyRepository
from app.domain.models.botanical_family import BotanicalFamily

router = APIRouter(
    prefix="/botanical-families",
    tags=["botanical-families"],
    dependencies=[Depends(get_current_user)],
    responses=AUTH_CRUD_RESPONSES,
)


def _family_response(f: BotanicalFamily, repo: ArangoBotanicalFamilyRepository) -> FamilyResponse:
    count = repo.get_species_count_by_family(f.key or "")
    return to_response(f, FamilyResponse, species_count=count)


@router.get("", response_model=list[FamilyResponse])
def list_families(
    pagination: PaginationParams = Depends(get_pagination),
    repo: ArangoBotanicalFamilyRepository = Depends(get_family_repo),
):
    """List botanical families with their species counts."""
    families, total = repo.get_all_families(pagination.offset, pagination.limit)
    return [_family_response(f, repo) for f in families]


@router.get("/{key}", response_model=FamilyResponse)
def get_family(
    key: Annotated[str, Path(description="Document key of the botanical family.")],
    repo: ArangoBotanicalFamilyRepository = Depends(get_family_repo),
):
    """Return a single botanical family by key."""
    f = repo.get_by_key(key)
    if f is None:
        from app.common.exceptions import NotFoundError

        raise NotFoundError("BotanicalFamily", key)
    return _family_response(f, repo)


@router.get("/{key}/species", response_model=list[SpeciesResponse])
def get_family_species(
    key: Annotated[str, Path(description="Document key of the botanical family.")],
    repo: ArangoBotanicalFamilyRepository = Depends(get_family_repo),
):
    """List all species belonging to a botanical family."""
    f = repo.get_by_key(key)
    if f is None:
        from app.common.exceptions import NotFoundError

        raise NotFoundError("BotanicalFamily", key)
    species_list = repo.get_species_by_family(key)
    return [to_response(s, SpeciesResponse) for s in species_list]


@router.post("", response_model=FamilyResponse, status_code=201)
def create_family(body: FamilyCreate, repo: ArangoBotanicalFamilyRepository = Depends(get_family_repo)):
    """Create a new botanical family."""
    family = BotanicalFamily(**body.model_dump())
    created = repo.create_family(family)
    return _family_response(created, repo)


@router.put("/{key}", response_model=FamilyResponse)
def update_family(
    key: Annotated[str, Path(description="Document key of the botanical family.")],
    body: FamilyCreate,
    repo: ArangoBotanicalFamilyRepository = Depends(get_family_repo),
):
    """Update an existing botanical family."""
    family = BotanicalFamily(**body.model_dump())
    updated = repo.update_family(key, family)
    return _family_response(updated, repo)


@router.delete("/{key}", status_code=204)
def delete_family(
    key: Annotated[str, Path(description="Document key of the botanical family.")],
    repo: ArangoBotanicalFamilyRepository = Depends(get_family_repo),
):
    """Delete a botanical family."""
    repo.delete_family(key)
