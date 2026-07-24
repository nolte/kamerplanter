from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.api.mapping import to_response
from app.api.v1.overwintering_profiles.schemas import (
    LinkSharedTemplateRequest,
    OverwinteringProfileAutoGenerate,
    OverwinteringProfileCreate,
    OverwinteringProfileResponse,
    OverwinteringProfileUpdate,
    OverwinteringTemplateResponse,
    WinterHardinessOverviewResponse,
)
from app.common.auth import get_current_tenant
from app.common.dependencies import (
    get_overwintering_profile_service,
    get_plant_repo,
    get_site_repo,
    get_species_repo,
)
from app.common.enums import GrowthHabit, RootType
from app.common.exceptions import NotFoundError
from app.common.openapi_responses import CRUD_RESPONSES
from app.common.pagination import PaginationParams, get_pagination
from app.data_access.arango.plant_instance_repository import ArangoPlantInstanceRepository
from app.data_access.arango.site_repository import ArangoSiteRepository
from app.data_access.arango.species_repository import ArangoSpeciesRepository
from app.domain.models.overwintering_profile import OverwinteringProfile
from app.domain.models.overwintering_profile_template import OverwinteringProfileTemplate
from app.domain.models.species import Species
from app.domain.models.tenant_context import TenantContext
from app.domain.services.overwintering_profile_service import OverwinteringProfileService

router = APIRouter(prefix="/overwintering-profiles", tags=["overwintering-profiles"], responses=CRUD_RESPONSES)

#: Root types / growth habits that identify a tuber/bulb/corm geophyte, which is
#: dug up and stored over winter rather than moved indoors (REQ-022 §Knollen-/
#: Zwiebel-Zyklus, B3).
_GEOPHYTE_ROOT_TYPES = frozenset({RootType.TUBEROUS, RootType.BULBOUS, RootType.CORM})


def _is_geophyte(species: Species) -> bool:
    return species.root_type in _GEOPHYTE_ROOT_TYPES or species.growth_habit == GrowthHabit.BULB_GEOPHYTE


def _profile_response(profile: OverwinteringProfile) -> OverwinteringProfileResponse:
    return to_response(profile, OverwinteringProfileResponse)


@router.get("", response_model=list[OverwinteringProfileResponse])
def list_overwintering_profiles(
    pagination: PaginationParams = Depends(get_pagination),
    ctx: TenantContext = Depends(get_current_tenant),
    service: OverwinteringProfileService = Depends(get_overwintering_profile_service),
) -> list[OverwinteringProfileResponse]:
    """List the tenant's overwintering profiles (paginated)."""
    items, _total = service.list_profiles(ctx.tenant_key, pagination.offset, pagination.limit)
    return [_profile_response(p) for p in items]


@router.get("/hardiness-overview", response_model=WinterHardinessOverviewResponse)
def get_hardiness_overview(
    ctx: TenantContext = Depends(get_current_tenant),
    service: OverwinteringProfileService = Depends(get_overwintering_profile_service),
) -> WinterHardinessOverviewResponse:
    """Return the tenant's winter-hardiness traffic-light overview."""
    overview = service.get_hardiness_overview(ctx.tenant_key)
    return WinterHardinessOverviewResponse(**overview.model_dump())


@router.post("", response_model=OverwinteringProfileResponse, status_code=201)
def create_overwintering_profile(
    body: OverwinteringProfileCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: OverwinteringProfileService = Depends(get_overwintering_profile_service),
) -> OverwinteringProfileResponse:
    """Create an overwintering profile for the tenant."""
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
    """Auto-generate an overwintering profile from species, site and frost data."""
    frost_sensitivity = body.frost_sensitivity
    species_zone = body.species_zone
    site_zone = body.site_zone

    # Resolve species frost data from the plant/species when not supplied inline.
    species_key = body.species_key
    if species_key is None and body.plant_key:
        plant = plant_repo.get_by_key(body.plant_key)
        if plant is not None:
            species_key = plant.species_key

    # The species drives frost sensitivity, hardiness zone and — for the tuber
    # dig-and-store path (B3) — whether the plant is a geophyte.
    is_geophyte = False
    if species_key:
        species = species_repo.get_by_key(species_key)
        if species is not None:
            if frost_sensitivity is None:
                frost_sensitivity = species.frost_sensitivity
            if species_zone is None and species.hardiness_zones:
                species_zone = species.hardiness_zones[0]
            is_geophyte = _is_geophyte(species)

    # Resolve the site climate zone (tenant-checked).
    if body.site_key and site_zone is None:
        site = site_repo.get_by_key(body.site_key)
        if site is not None and site.tenant_key == ctx.tenant_key:
            # REQ-039: structured hardiness zone wins over legacy free-text.
            site_zone = getattr(site, "hardiness_zone", None) or site.climate_zone or None

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
        is_geophyte=is_geophyte,
        species_key=species_key,
    )
    return _profile_response(created)


def _template_response(template: OverwinteringProfileTemplate) -> OverwinteringTemplateResponse:
    return to_response(template, OverwinteringTemplateResponse)


@router.post("/link-template", response_model=OverwinteringTemplateResponse)
def link_shared_template(
    body: LinkSharedTemplateRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: OverwinteringProfileService = Depends(get_overwintering_profile_service),
) -> OverwinteringTemplateResponse:
    """Point a plant / planting run at the reusable species template (N:1)."""
    template = service.link_shared_template(
        ctx.tenant_key,
        plant_key=body.plant_key,
        planting_run_key=body.planting_run_key,
        template_key=body.template_key,
        species_key=body.species_key,
        scientific_name=body.scientific_name,
    )
    return _template_response(template)


@router.get("/shared-template", response_model=OverwinteringTemplateResponse)
def get_shared_template(
    plant_key: str | None = Query(default=None, description="Plant instance whose linked template to return."),
    planting_run_key: str | None = Query(default=None, description="Planting run whose linked template to return."),
    ctx: TenantContext = Depends(get_current_tenant),
    service: OverwinteringProfileService = Depends(get_overwintering_profile_service),
) -> OverwinteringTemplateResponse:
    """Return the reusable species template linked to a plant or planting run."""
    template = service.get_shared_template_for_subject(
        ctx.tenant_key, plant_key=plant_key, planting_run_key=planting_run_key
    )
    if template is None:
        raise NotFoundError("OverwinteringProfileTemplate", plant_key or planting_run_key or "")
    return _template_response(template)


@router.delete("/shared-template", status_code=204)
def unlink_shared_template(
    plant_key: str | None = Query(default=None, description="Plant instance to unlink from its template."),
    planting_run_key: str | None = Query(default=None, description="Planting run to unlink from its template."),
    ctx: TenantContext = Depends(get_current_tenant),
    service: OverwinteringProfileService = Depends(get_overwintering_profile_service),
) -> None:
    """Detach a plant or planting run from its shared species template."""
    service.unlink_shared_template(ctx.tenant_key, plant_key=plant_key, planting_run_key=planting_run_key)


@router.get("/{key}", response_model=OverwinteringProfileResponse)
def get_overwintering_profile(
    key: Annotated[str, Path(description="Document key of the overwintering profile.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: OverwinteringProfileService = Depends(get_overwintering_profile_service),
) -> OverwinteringProfileResponse:
    """Return a single overwintering profile by key."""
    profile = service.get_profile(key, ctx.tenant_key)
    return _profile_response(profile)


@router.put("/{key}", response_model=OverwinteringProfileResponse)
def update_overwintering_profile(
    key: Annotated[str, Path(description="Document key of the overwintering profile.")],
    body: OverwinteringProfileUpdate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: OverwinteringProfileService = Depends(get_overwintering_profile_service),
) -> OverwinteringProfileResponse:
    """Update an overwintering profile."""
    updates = body.model_dump(exclude_unset=True)
    updated = service.update_profile(key, ctx.tenant_key, updates)
    return _profile_response(updated)


@router.delete("/{key}", status_code=204)
def delete_overwintering_profile(
    key: Annotated[str, Path(description="Document key of the overwintering profile.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: OverwinteringProfileService = Depends(get_overwintering_profile_service),
) -> None:
    """Delete an overwintering profile."""
    service.delete_profile(key, ctx.tenant_key)
