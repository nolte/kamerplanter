"""REQ-026 Fish species global catalog router.

Fish species are global seed reference data (not tenant-scoped), consumed by the
aquaponics fish/plant compatibility graph. All endpoints are read-only and
require an authenticated member.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.mapping import to_response
from app.api.v1.aquaponik.schemas import CompatiblePlantsResponse, FishSpeciesResponse
from app.common.auth import get_current_user
from app.common.dependencies import get_aquaponik_service
from app.domain.services.aquaponik_service import AquaponikService

router = APIRouter(
    prefix="/fish-species",
    tags=["fish-species"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=list[FishSpeciesResponse])
def list_fish_species(
    temperature_zone: str | None = None,
    feed_type: str | None = None,
    service: AquaponikService = Depends(get_aquaponik_service),
):
    species = service.list_species(temperature_zone, feed_type)
    return [to_response(s, FishSpeciesResponse) for s in species]


@router.get("/by-temperature-zone/{zone}", response_model=list[FishSpeciesResponse])
def list_by_temperature_zone(
    zone: str,
    service: AquaponikService = Depends(get_aquaponik_service),
):
    species = service.list_species_by_zone(zone)
    return [to_response(s, FishSpeciesResponse) for s in species]


@router.get("/{species_key}", response_model=FishSpeciesResponse)
def get_fish_species(
    species_key: str,
    service: AquaponikService = Depends(get_aquaponik_service),
):
    species = service.get_species(species_key)
    return to_response(species, FishSpeciesResponse)


@router.get("/{species_key}/compatible-plants", response_model=CompatiblePlantsResponse)
def get_compatible_plants(
    species_key: str,
    service: AquaponikService = Depends(get_aquaponik_service),
):
    result = service.get_compatible_plants(species_key)
    return CompatiblePlantsResponse(**result)
