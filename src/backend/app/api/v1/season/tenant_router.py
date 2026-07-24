"""REQ-047 §4.4 — tenant-scoped season & overwintering-automation endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path

from app.api.mapping import to_response
from app.api.v1.overwintering_profiles.schemas import (
    OverwinteringOverrideRequest,
    OverwinteringProfileResponse,
)
from app.api.v1.season.schemas import SeasonOverviewResponse, SeasonStateResponse
from app.common.auth import get_current_tenant
from app.common.dependencies import (
    get_overwintering_profile_service,
    get_season_state_service,
)
from app.common.openapi_responses import NOT_FOUND_RESPONSE
from app.domain.models.overwintering_profile import (
    OverwinteringProfile,
    PlantOverwinteringStatus,
)
from app.domain.models.season_state import SeasonState
from app.domain.models.tenant_context import TenantContext
from app.domain.services.overwintering_profile_service import OverwinteringProfileService
from app.domain.services.season_state_service import SeasonStateService

router = APIRouter(tags=["season"], responses=NOT_FOUND_RESPONSE)


def _season_response(state: SeasonState) -> SeasonStateResponse:
    return to_response(state, SeasonStateResponse)


def _profile_response(profile: OverwinteringProfile) -> OverwinteringProfileResponse:
    return to_response(profile, OverwinteringProfileResponse)


@router.get("/sites/{site_key}/season-state", response_model=SeasonStateResponse)
def get_site_season_state(
    site_key: Annotated[str, Path(description="Document key of the site.")],
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
    plant_key: Annotated[str, Path(description="Document key of the plant instance.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: OverwinteringProfileService = Depends(get_overwintering_profile_service),
) -> OverwinteringProfileResponse:
    """Read the auto-materialised overwintering profile of a plant instance."""
    profile = service.get_plant_profile(plant_key, ctx.tenant_key)
    return _profile_response(profile)


@router.get("/plants/{plant_key}/overwintering/status", response_model=PlantOverwinteringStatus)
def get_plant_overwintering_status(
    plant_key: Annotated[str, Path(description="Document key of the plant instance.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: OverwinteringProfileService = Depends(get_overwintering_profile_service),
) -> PlantOverwinteringStatus:
    """Winter-hardiness status of a plant instance — always 200, even without a profile.

    Additive companion to ``GET /plants/{plant_key}/overwintering`` (whose 404
    "no profile" contract is unchanged). Lets the detail page tell the genuinely
    winter-hardy plant (ampel green) apart from one whose profile is only
    materialised later at the ``growing → pre_winter`` transition (ampel
    yellow/red), so a protection-needing plant is never mislabelled as hardy.
    """
    return service.get_plant_hardiness_status(plant_key, ctx.tenant_key)


@router.patch("/plants/{plant_key}/overwintering", response_model=OverwinteringProfileResponse)
def override_plant_overwintering(
    plant_key: Annotated[str, Path(description="Document key of the plant instance.")],
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
    plant_key: Annotated[str, Path(description="Document key of the plant instance.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: OverwinteringProfileService = Depends(get_overwintering_profile_service),
) -> OverwinteringProfileResponse:
    """Reset to the automatic derivation (``user_overridden=False``) and re-materialise.

    The species/site resolution and geophyte classification live in the service
    (NFR-001: no business logic in the API layer, C1).
    """
    updated = service.reset_plant_profile(plant_key, ctx.tenant_key)
    return _profile_response(updated)
