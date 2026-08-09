from typing import Annotated

from fastapi import APIRouter, Depends, Path

from app.api.mapping import to_response
from app.api.v1.botanical_families.schemas import FamilyCreate, FamilyResponse
from app.api.v1.species.schemas import SpeciesResponse
from app.common.auth import get_active_tenant_key, get_current_user
from app.common.dependencies import get_family_repo
from app.common.exceptions import NotFoundError
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


def _family_response_with_count(f: BotanicalFamily, species_count: int) -> FamilyResponse:
    """Map one family onto its response using an already-resolved species count.

    Split out so the list endpoint can feed counts from a single bulk lookup
    while the single-row endpoints keep resolving their own count.
    """
    return to_response(f, FamilyResponse, species_count=species_count)


def _family_response(f: BotanicalFamily, repo: ArangoBotanicalFamilyRepository, tenant_key: str) -> FamilyResponse:
    """Map one family, resolving its species count with a per-family count query.

    For single-row endpoints only (get/create/update), where exactly one count is
    needed. The list endpoint must NOT use this: one count query per row is the
    N+1 that :meth:`ArangoBotanicalFamilyRepository.get_species_counts_by_family`
    exists to remove. ``tenant_key`` scopes the count to the caller's visible
    species (F-5, #808) so it matches the tenant-scoped species listing.
    """
    return _family_response_with_count(f, repo.get_species_count_by_family(f.key or "", tenant_key=tenant_key))


@router.get("", response_model=list[FamilyResponse])
def list_families(
    pagination: PaginationParams = Depends(get_pagination),
    repo: ArangoBotanicalFamilyRepository = Depends(get_family_repo),
    tenant_key: str = Depends(get_active_tenant_key),
):
    """List botanical families with their species counts.

    Species counts are tenant-scoped on this global route (F-5, #808): they count
    the global seed catalogue plus the caller's own species, never a foreign
    tenant's, so the number matches the tenant-scoped species listing.
    """
    families, total = repo.get_all_families(pagination.offset, pagination.limit)
    # One aggregate lookup for the whole page instead of a count query per row.
    # Families without species are absent from the map by design, hence the 0
    # default rather than a missing-key error.
    counts = repo.get_species_counts_by_family(tenant_key=tenant_key)
    return [_family_response_with_count(f, counts.get(f.key or "", 0)) for f in families]


@router.get("/{key}", response_model=FamilyResponse)
def get_family(
    key: Annotated[str, Path(description="Document key of the botanical family.")],
    repo: ArangoBotanicalFamilyRepository = Depends(get_family_repo),
    tenant_key: str = Depends(get_active_tenant_key),
):
    """Return a single botanical family by key."""
    f = repo.get_by_key(key)
    if f is None:
        raise NotFoundError("BotanicalFamily", key)
    return _family_response(f, repo, tenant_key)


@router.get("/{key}/species", response_model=list[SpeciesResponse])
def get_family_species(
    key: Annotated[str, Path(description="Document key of the botanical family.")],
    repo: ArangoBotanicalFamilyRepository = Depends(get_family_repo),
    tenant_key: str = Depends(get_active_tenant_key),
):
    """List all species belonging to a botanical family.

    Tenant-scoped on this global route (F-5, #808): global seeds plus the
    caller's own species, never a foreign tenant's.
    """
    f = repo.get_by_key(key)
    if f is None:
        raise NotFoundError("BotanicalFamily", key)
    species_list = repo.get_species_by_family(key, tenant_key=tenant_key)
    return [to_response(s, SpeciesResponse) for s in species_list]


@router.post("", response_model=FamilyResponse, status_code=201)
def create_family(
    body: FamilyCreate,
    repo: ArangoBotanicalFamilyRepository = Depends(get_family_repo),
    tenant_key: str = Depends(get_active_tenant_key),
):
    """Create a new botanical family."""
    family = BotanicalFamily(**body.model_dump())
    created = repo.create_family(family)
    return _family_response(created, repo, tenant_key)


@router.put("/{key}", response_model=FamilyResponse)
def update_family(
    key: Annotated[str, Path(description="Document key of the botanical family.")],
    body: FamilyCreate,
    repo: ArangoBotanicalFamilyRepository = Depends(get_family_repo),
    tenant_key: str = Depends(get_active_tenant_key),
):
    """Update an existing botanical family."""
    family = BotanicalFamily(**body.model_dump())
    updated = repo.update_family(key, family)
    return _family_response(updated, repo, tenant_key)


@router.delete("/{key}", status_code=204)
def delete_family(
    key: Annotated[str, Path(description="Document key of the botanical family.")],
    repo: ArangoBotanicalFamilyRepository = Depends(get_family_repo),
):
    """Delete a botanical family."""
    repo.delete_family(key)
