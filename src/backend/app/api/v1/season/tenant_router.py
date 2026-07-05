"""REQ-047 §4.4 — tenant-scoped season & overwintering-automation endpoints."""

from fastapi import APIRouter, Depends

from app.api.mapping import to_response
from app.api.v1.overwintering_profiles.schemas import (
    OverwinteringOverrideRequest,
    OverwinteringProfileResponse,
)
from app.api.v1.season.schemas import SeasonOverviewResponse, SeasonStateResponse
from app.common.auth import get_current_tenant
from app.common.dependencies import (
    get_overwintering_profile_service,
    get_plant_repo,
    get_season_state_service,
    get_site_repo,
    get_species_repo,
)
from app.common.enums import GrowthHabit, RootType
from app.common.exceptions import NotFoundError
from app.data_access.arango.plant_instance_repository import ArangoPlantInstanceRepository
from app.data_access.arango.site_repository import ArangoSiteRepository
from app.data_access.arango.species_repository import ArangoSpeciesRepository
from app.domain.models.overwintering_profile import OverwinteringProfile
from app.domain.models.season_state import SeasonState
from app.domain.models.tenant_context import TenantContext
from app.domain.services.overwintering_profile_service import OverwinteringProfileService
from app.domain.services.season_state_service import SeasonStateService

router = APIRouter(tags=["season"])

_GEOPHYTE_ROOT_TYPES = frozenset({RootType.TUBEROUS, RootType.BULBOUS, RootType.CORM})


def _season_response(state: SeasonState) -> SeasonStateResponse:
    return to_response(state, SeasonStateResponse)


def _profile_response(profile: OverwinteringProfile) -> OverwinteringProfileResponse:
    return to_response(profile, OverwinteringProfileResponse)


@router.get("/sites/{site_key}/season-state", response_model=SeasonStateResponse)
def get_site_season_state(
    site_key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: SeasonStateService = Depends(get_season_state_service),
) -> SeasonStateResponse:
    """Read the current season state (and trigger source) of a site.

    404 unknown site, 409 for a pure indoor site (no season).
    """
    state = service.get_state_for_site(site_key, ctx.tenant_key)
    return _season_response(state)


@router.get("/season/overview", response_model=SeasonOverviewResponse)
def get_season_overview(
    ctx: TenantContext = Depends(get_current_tenant),
    service: SeasonStateService = Depends(get_season_state_service),
) -> SeasonOverviewResponse:
    """Aggregated season states over all outdoor/greenhouse sites of the tenant."""
    states = service.get_overview(ctx.tenant_key)
    return SeasonOverviewResponse(states=[_season_response(s) for s in states])


@router.get("/plants/{plant_key}/overwintering", response_model=OverwinteringProfileResponse)
def get_plant_overwintering(
    plant_key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: OverwinteringProfileService = Depends(get_overwintering_profile_service),
) -> OverwinteringProfileResponse:
    """Read the auto-materialised overwintering profile of a plant instance."""
    profile = service.get_plant_profile(plant_key, ctx.tenant_key)
    return _profile_response(profile)


@router.patch("/plants/{plant_key}/overwintering", response_model=OverwinteringProfileResponse)
def override_plant_overwintering(
    plant_key: str,
    body: OverwinteringOverrideRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: OverwinteringProfileService = Depends(get_overwintering_profile_service),
) -> OverwinteringProfileResponse:
    """Override individual fields (sets ``user_overridden=True``). 422 on D5 conflict."""
    updates = body.model_dump(exclude_unset=True)
    updated = service.override_plant_profile(plant_key, ctx.tenant_key, updates)
    return _profile_response(updated)


@router.post("/plants/{plant_key}/overwintering/reset", response_model=OverwinteringProfileResponse)
def reset_plant_overwintering(
    plant_key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: OverwinteringProfileService = Depends(get_overwintering_profile_service),
    plant_repo: ArangoPlantInstanceRepository = Depends(get_plant_repo),
    species_repo: ArangoSpeciesRepository = Depends(get_species_repo),
    site_repo: ArangoSiteRepository = Depends(get_site_repo),
) -> OverwinteringProfileResponse:
    """Reset to the automatic derivation (``user_overridden=False``) and re-materialise."""
    # Ensure the profile exists and belongs to the tenant (404 otherwise).
    service.get_plant_profile(plant_key, ctx.tenant_key)

    plant = plant_repo.get_by_key(plant_key)
    if plant is None or plant.tenant_key != ctx.tenant_key:
        raise NotFoundError("PlantInstance", plant_key)

    frost_sensitivity = None
    species_zone = None
    is_geophyte = False
    if plant.species_key:
        species = species_repo.get_by_key(plant.species_key)
        if species is not None:
            frost_sensitivity = species.frost_sensitivity
            if species.hardiness_zones:
                species_zone = species.hardiness_zones[0]
            is_geophyte = species.root_type in _GEOPHYTE_ROOT_TYPES or species.growth_habit == GrowthHabit.BULB_GEOPHYTE

    site_zone = None
    if plant.site_key:
        site = site_repo.get_by_key(plant.site_key)
        if site is not None and site.tenant_key == ctx.tenant_key and site.climate_zone:
            site_zone = site.climate_zone

    updated = service.rematerialize_plant_profile(
        plant_key,
        ctx.tenant_key,
        frost_sensitivity=frost_sensitivity,
        species_zone=species_zone,
        site_zone=site_zone,
        is_geophyte=is_geophyte,
        species_key=plant.species_key,
    )
    return _profile_response(updated)
