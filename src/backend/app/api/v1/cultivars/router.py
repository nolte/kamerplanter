from typing import Annotated

from fastapi import APIRouter, Depends, Path

from app.api.mapping import to_response
from app.api.v1.cultivars.schemas import CultivarCreate, CultivarResponse
from app.common.auth import get_creating_tenant_key, get_current_user
from app.common.dependencies import get_species_service
from app.common.enums import DataOrigin
from app.common.exceptions import ValidationError
from app.common.openapi_responses import CRUD_RESPONSES, UNAUTHORIZED_RESPONSE
from app.config.settings import settings
from app.domain.models.species import Cultivar
from app.domain.services.species_service import SpeciesService

router = APIRouter(
    prefix="/species/{species_key}/cultivars",
    tags=["cultivars"],
    dependencies=[Depends(get_current_user)],
    responses={**UNAUTHORIZED_RESPONSE, **CRUD_RESPONSES},
)


@router.get("", response_model=list[CultivarResponse])
def list_cultivars(
    species_key: Annotated[str, Path(description="Document key of the species.")],
    service: SpeciesService = Depends(get_species_service),
):
    """List the cultivars registered for a species."""
    cultivars = service.list_cultivars(species_key)
    return [to_response(c, CultivarResponse) for c in cultivars]


@router.post("", response_model=CultivarResponse, status_code=201)
def create_cultivar(
    species_key: Annotated[str, Path(description="Document key of the species.")],
    body: CultivarCreate,
    service: SpeciesService = Depends(get_species_service),
    tenant_key: str = Depends(get_creating_tenant_key),
):
    """Create a tenant-owned cultivar for a species."""
    # SEC-004 pendant (#1090): in full mode a tenant-owned create with no resolvable
    # active tenant must NOT be stamped global. Without this guard an authenticated
    # caller who has no personal tenant would resolve ``tenant_key == ""`` and inject
    # an ``origin=TENANT`` cultivar straight into the shared seed catalogue every
    # tenant sees. Reject it as 422 instead. Light mode (REQ-027) is single-tenant, so
    # the empty key there is the legitimate global operator context — never blocked.
    if settings.kamerplanter_mode == "full" and not tenant_key:
        raise ValidationError("Cannot create a tenant-owned cultivar without an active tenant.")
    # User-created cultivars are tenant-owned (editable); seeded ones stay 'system'.
    #
    # tenant_key is resolved from the authenticated caller (their personal tenant),
    # never from the request body (#1000, #1090) — ``CultivarCreate`` carries no
    # tenant field, so ``body.model_dump()`` cannot smuggle one in. This binds a
    # newly created cultivar to its owner so the tenant-aware read predicate can keep
    # it out of foreign tenants while the global seed catalogue (tenant_key == "")
    # stays visible to all. Mirrors the species create path.
    cultivar = Cultivar(
        species_key=species_key,
        origin=DataOrigin.TENANT,
        tenant_key=tenant_key,
        **body.model_dump(exclude={"species_key"}),
    )
    created = service.create_cultivar(cultivar)
    return to_response(created, CultivarResponse)


@router.get("/{cultivar_key}", response_model=CultivarResponse)
def get_cultivar(
    species_key: Annotated[str, Path(description="Document key of the species.")],
    cultivar_key: Annotated[str, Path(description="Document key of the cultivar.")],
    service: SpeciesService = Depends(get_species_service),
):
    """Return a single cultivar of a species by key."""
    c = service.get_cultivar(cultivar_key)
    return to_response(c, CultivarResponse)


@router.put("/{cultivar_key}", response_model=CultivarResponse)
def update_cultivar(
    species_key: Annotated[str, Path(description="Document key of the species.")],
    cultivar_key: Annotated[str, Path(description="Document key of the cultivar.")],
    body: CultivarCreate,
    service: SpeciesService = Depends(get_species_service),
):
    """Update an existing cultivar of a species."""
    # The model built here carries the *default* ``tenant_key == ""`` — the edit form
    # never submits ownership (#1090). The service restores the stored owner before
    # writing, so this full-replace update cannot move a tenant-owned cultivar into
    # the shared global catalogue.
    cultivar = Cultivar(species_key=species_key, **body.model_dump(exclude={"species_key"}))
    updated = service.update_cultivar(cultivar_key, cultivar)
    return to_response(updated, CultivarResponse)


@router.delete("/{cultivar_key}", status_code=204)
def delete_cultivar(
    species_key: Annotated[str, Path(description="Document key of the species.")],
    cultivar_key: Annotated[str, Path(description="Document key of the cultivar.")],
    service: SpeciesService = Depends(get_species_service),
):
    """Delete a cultivar of a species."""
    service.delete_cultivar(cultivar_key)
