"""REQ-026 Fish species global catalog router.

Fish species are global seed reference data (not tenant-scoped), consumed by the
aquaponics fish/plant compatibility graph. All endpoints are read-only and
require an authenticated member.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.api.mapping import to_response
from app.api.v1.aquaponik.schemas import CompatiblePlantsResponse, FishSpeciesResponse
from app.common.auth import get_current_user
from app.common.dependencies import get_aquaponik_service
from app.common.openapi_responses import NOT_FOUND_RESPONSE, UNAUTHORIZED_RESPONSE
from app.domain.services.aquaponik_service import AquaponikService

router = APIRouter(
    prefix="/fish-species",
    tags=["fish-species"],
    dependencies=[Depends(get_current_user)],
    responses={**UNAUTHORIZED_RESPONSE, **NOT_FOUND_RESPONSE},
)


@router.get("", response_model=list[FishSpeciesResponse])
def list_fish_species(
    temperature_zone: str | None = Query(None, description="Filter by temperature zone."),
    feed_type: str | None = Query(None, description="Filter by feed type."),
    service: AquaponikService = Depends(get_aquaponik_service),
):
    """List the global fish-species catalog, optionally filtered."""
    species = service.list_species(temperature_zone, feed_type)
    return [to_response(s, FishSpeciesResponse) for s in species]


@router.get("/by-temperature-zone/{zone}", response_model=list[FishSpeciesResponse])
def list_by_temperature_zone(
    zone: Annotated[str, Path(description="Temperature zone to filter by.")],
    service: AquaponikService = Depends(get_aquaponik_service),
):
    """List the fish species belonging to a temperature zone."""
    species = service.list_species_by_zone(zone)
    return [to_response(s, FishSpeciesResponse) for s in species]


@router.get("/{species_key}", response_model=FishSpeciesResponse)
def get_fish_species(
    species_key: Annotated[str, Path(description="Document key of the fish species.")],
    service: AquaponikService = Depends(get_aquaponik_service),
):
    """Return a single fish species by key."""
    species = service.get_species(species_key)
    return to_response(species, FishSpeciesResponse)


@router.get("/{species_key}/compatible-plants", response_model=CompatiblePlantsResponse)
def get_compatible_plants(
    species_key: Annotated[str, Path(description="Document key of the fish species.")],
    service: AquaponikService = Depends(get_aquaponik_service),
):
    """Return the plants compatible with a fish species in an aquaponic system."""
    result = service.get_compatible_plants(species_key)
    return CompatiblePlantsResponse(**result)
