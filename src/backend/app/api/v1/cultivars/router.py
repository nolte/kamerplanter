from typing import Annotated

from fastapi import APIRouter, Depends, Path

from app.api.mapping import to_response
from app.api.v1.cultivars.schemas import CultivarCreate, CultivarResponse
from app.common.auth import get_current_user
from app.common.dependencies import get_species_service
from app.common.enums import DataOrigin
from app.common.openapi_responses import CRUD_RESPONSES, UNAUTHORIZED_RESPONSE
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
):
    """Create a tenant-owned cultivar for a species."""
    # User-created cultivars are tenant-owned (editable); seeded ones stay 'system'.
    cultivar = Cultivar(
        species_key=species_key,
        origin=DataOrigin.TENANT,
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
