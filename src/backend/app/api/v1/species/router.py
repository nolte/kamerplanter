from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.api.mapping import to_response
from app.api.v1.species.schemas import (
    ReferenceImageEntry,
    SpeciesCreate,
    SpeciesListResponse,
    SpeciesReferenceImagesResponse,
    SpeciesResponse,
)
from app.common.auth import get_active_tenant_key, get_creating_tenant_key, get_current_user
from app.common.dependencies import get_family_repo, get_species_service
from app.common.enums import DataOrigin
from app.common.openapi_responses import CRUD_RESPONSES, UNAUTHORIZED_RESPONSE
from app.config.settings import settings
from app.data_access.arango.botanical_family_repository import ArangoBotanicalFamilyRepository
from app.data_access.external.inference_service_client import InferenceServiceClient
from app.domain.models.species import Species
from app.domain.services.species_service import SpeciesService

router = APIRouter(
    prefix="/species",
    tags=["species"],
    dependencies=[Depends(get_current_user)],
    responses={**UNAUTHORIZED_RESPONSE, **CRUD_RESPONSES},
)


def _species_response(s: Species, family_repo: ArangoBotanicalFamilyRepository) -> SpeciesResponse:
    family_name = None
    if s.family_key:
        fam = family_repo.get_by_key(s.family_key)
        if fam:
            family_name = fam.name
    return to_response(s, SpeciesResponse, family_name=family_name)


@router.get("", response_model=SpeciesListResponse)
def list_species(
    offset: int = Query(0, ge=0, description="Number of species to skip (pagination offset)."),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of species to return."),
    service: SpeciesService = Depends(get_species_service),
    family_repo: ArangoBotanicalFamilyRepository = Depends(get_family_repo),
    tenant_key: str = Depends(get_active_tenant_key),
):
    """List the species catalogue (paginated).

    Tenant-aware on this global route (F-5, #808): returns the global seed
    catalogue (``tenant_key == ""``) plus the caller's own-tenant species, and
    never a foreign tenant's. The active tenant is resolved by
    :func:`~app.common.auth.get_active_tenant_key`; an anonymous/light-mode caller
    resolves to ``""`` and sees only the global catalogue.
    """
    items, total = service.list_species(offset, limit, tenant_key=tenant_key)
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
    key: Annotated[str, Path(description="Document key of the species.")],
    service: SpeciesService = Depends(get_species_service),
    family_repo: ArangoBotanicalFamilyRepository = Depends(get_family_repo),
):
    """Return a single species by key."""
    s = service.get_species(key)
    return _species_response(s, family_repo)


@router.get("/{key}/reference-images", response_model=SpeciesReferenceImagesResponse)
def get_species_reference_images(
    key: Annotated[str, Path(description="Document key of the species.")],
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
    tenant_key: str = Depends(get_creating_tenant_key),
):
    """Create a tenant-owned species master record."""
    # User-created master data is tenant-owned (editable); seeded species default
    # to 'system' (read-only). Provenance is server-set, never from the form body.
    #
    # tenant_key is resolved from the authenticated caller (their personal tenant),
    # never from the request body (#1000, F-3/#808) — ``SpeciesCreate`` carries no
    # tenant field, so ``body.model_dump()`` cannot smuggle one in. This binds a
    # newly created species to its owner so F-5's read predicate can keep it out of
    # foreign tenants while the global seed catalogue (tenant_key == "") stays
    # visible to all.
    species = Species(**body.model_dump(), origin=DataOrigin.TENANT, tenant_key=tenant_key)
    created = service.create_species(species)
    return _species_response(created, family_repo)


@router.put("/{key}", response_model=SpeciesResponse)
def update_species(
    key: Annotated[str, Path(description="Document key of the species.")],
    body: SpeciesCreate,
    service: SpeciesService = Depends(get_species_service),
    family_repo: ArangoBotanicalFamilyRepository = Depends(get_family_repo),
):
    """Update an existing species master record."""
    species = Species(**body.model_dump())
    updated = service.update_species(key, species)
    return _species_response(updated, family_repo)


@router.delete("/{key}", status_code=204)
def delete_species(
    key: Annotated[str, Path(description="Document key of the species.")],
    service: SpeciesService = Depends(get_species_service),
):
    """Delete a species master record."""
    service.delete_species(key)
