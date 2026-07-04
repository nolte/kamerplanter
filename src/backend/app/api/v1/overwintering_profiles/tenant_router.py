from fastapi import APIRouter, Depends

from app.api.mapping import to_response
from app.api.v1.overwintering_profiles.schemas import (
    OverwinteringProfileAutoGenerate,
    OverwinteringProfileCreate,
    OverwinteringProfileResponse,
    OverwinteringProfileUpdate,
    WinterHardinessOverviewResponse,
)
from app.common.auth import get_current_tenant
from app.common.dependencies import (
    get_overwintering_profile_service,
    get_plant_repo,
    get_site_repo,
    get_species_repo,
)
from app.common.pagination import PaginationParams, get_pagination
from app.data_access.arango.plant_instance_repository import ArangoPlantInstanceRepository
from app.data_access.arango.site_repository import ArangoSiteRepository
from app.data_access.arango.species_repository import ArangoSpeciesRepository
from app.domain.models.overwintering_profile import OverwinteringProfile
from app.domain.models.tenant_context import TenantContext
from app.domain.services.overwintering_profile_service import OverwinteringProfileService

router = APIRouter(prefix="/overwintering-profiles", tags=["overwintering-profiles"])


def _profile_response(profile: OverwinteringProfile) -> OverwinteringProfileResponse:
    return to_response(profile, OverwinteringProfileResponse)


@router.get("", response_model=list[OverwinteringProfileResponse])
def list_overwintering_profiles(
    pagination: PaginationParams = Depends(get_pagination),
    ctx: TenantContext = Depends(get_current_tenant),
    service: OverwinteringProfileService = Depends(get_overwintering_profile_service),
) -> list[OverwinteringProfileResponse]:
    items, _total = service.list_profiles(ctx.tenant_key, pagination.offset, pagination.limit)
    return [_profile_response(p) for p in items]


@router.get("/hardiness-overview", response_model=WinterHardinessOverviewResponse)
def get_hardiness_overview(
    ctx: TenantContext = Depends(get_current_tenant),
    service: OverwinteringProfileService = Depends(get_overwintering_profile_service),
) -> WinterHardinessOverviewResponse:
    overview = service.get_hardiness_overview(ctx.tenant_key)
    return WinterHardinessOverviewResponse(**overview.model_dump())


@router.post("", response_model=OverwinteringProfileResponse, status_code=201)
def create_overwintering_profile(
    body: OverwinteringProfileCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: OverwinteringProfileService = Depends(get_overwintering_profile_service),
) -> OverwinteringProfileResponse:
    profile = OverwinteringProfile(**body.model_dump(), tenant_key=ctx.tenant_key)
    created = service.create_profile(profile, ctx.tenant_key)
    return _profile_response(created)


@router.post("/auto-generate", response_model=OverwinteringProfileResponse, status_code=201)
def auto_generate_overwintering_profile(
    body: OverwinteringProfileAutoGenerate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: OverwinteringProfileService = Depends(get_overwintering_profile_service),
    species_repo: ArangoSpeciesRepository = Depends(get_species_repo),
    site_repo: ArangoSiteRepository = Depends(get_site_repo),
    plant_repo: ArangoPlantInstanceRepository = Depends(get_plant_repo),
) -> OverwinteringProfileResponse:
    frost_sensitivity = body.frost_sensitivity
    species_zone = body.species_zone
    site_zone = body.site_zone

    # Resolve species frost data from the plant/species when not supplied inline.
    species_key = body.species_key
    if species_key is None and body.plant_key:
        plant = plant_repo.get_by_key(body.plant_key)
        if plant is not None:
            species_key = plant.species_key
    if species_key and (frost_sensitivity is None or species_zone is None):
        species = species_repo.get_by_key(species_key)
        if species is not None:
            if frost_sensitivity is None:
                frost_sensitivity = species.frost_sensitivity
            if species_zone is None and species.hardiness_zones:
                species_zone = species.hardiness_zones[0]

    # Resolve the site climate zone (tenant-checked).
    if body.site_key and site_zone is None:
        site = site_repo.get_by_key(body.site_key)
        if site is not None and site.tenant_key == ctx.tenant_key and site.climate_zone:
            site_zone = site.climate_zone

    created = service.auto_generate_profile(
        ctx.tenant_key,
        plant_key=body.plant_key,
        planting_run_key=body.planting_run_key,
        frost_sensitivity=frost_sensitivity,
        species_zone=species_zone,
        site_zone=site_zone,
        winter_action_month=body.winter_action_month,
        spring_action_month=body.spring_action_month,
        winter_quarter_key=body.winter_quarter_key,
    )
    return _profile_response(created)


@router.get("/{key}", response_model=OverwinteringProfileResponse)
def get_overwintering_profile(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: OverwinteringProfileService = Depends(get_overwintering_profile_service),
) -> OverwinteringProfileResponse:
    profile = service.get_profile(key, ctx.tenant_key)
    return _profile_response(profile)


@router.put("/{key}", response_model=OverwinteringProfileResponse)
def update_overwintering_profile(
    key: str,
    body: OverwinteringProfileUpdate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: OverwinteringProfileService = Depends(get_overwintering_profile_service),
) -> OverwinteringProfileResponse:
    updates = body.model_dump(exclude_unset=True)
    updated = service.update_profile(key, ctx.tenant_key, updates)
    return _profile_response(updated)


@router.delete("/{key}", status_code=204)
def delete_overwintering_profile(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: OverwinteringProfileService = Depends(get_overwintering_profile_service),
) -> None:
    service.delete_profile(key, ctx.tenant_key)
