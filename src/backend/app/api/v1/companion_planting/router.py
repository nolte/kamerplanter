from typing import Annotated

from fastapi import APIRouter, Depends, Path

from app.api.v1.companion_planting.schemas import (
    CompanionEdgeCreatedResponse,
    CompanionRecommendationsResponse,
    CompatibilitySet,
    CompatibleSpeciesResponse,
    IncompatibilitySet,
    IncompatibleSpeciesResponse,
    SpeciesCompanionCounts,
)
from app.common.auth import get_current_user, require_platform_admin
from app.common.dependencies import get_species_service
from app.common.openapi_responses import AUTH_RESPONSES, NOT_FOUND_RESPONSE
from app.domain.services.species_service import SpeciesService

router = APIRouter(
    prefix="/companion-planting",
    tags=["companion-planting"],
    dependencies=[Depends(get_current_user)],
    responses={**AUTH_RESPONSES, **NOT_FOUND_RESPONSE},
)


@router.get("/counts", response_model=dict[str, SpeciesCompanionCounts])
def get_counts(service: SpeciesService = Depends(get_species_service)) -> dict[str, dict[str, int]]:
    """Return per-species compatible/incompatible companion counts for the whole catalogue."""
    # Whole-catalogue aggregate keyed by species_key: one batch request feeds the
    # per-species companion badges in the selection dropdown (no N+1). Companion
    # data is global reference data — no tenant scoping needed.
    return service.get_companion_counts()


@router.get("/species/{species_key}/compatible", response_model=list[CompatibleSpeciesResponse])
def get_compatible(
    species_key: Annotated[str, Path(description="Document key of the species.")],
    service: SpeciesService = Depends(get_species_service),
):
    """List the species that are compatible companions of the given species."""
    return service.get_compatible_species(species_key)


@router.get("/species/{species_key}/incompatible", response_model=list[IncompatibleSpeciesResponse])
def get_incompatible(
    species_key: Annotated[str, Path(description="Document key of the species.")],
    service: SpeciesService = Depends(get_species_service),
):
    """List the species that are incompatible companions of the given species."""
    return service.get_incompatible_species(species_key)


@router.post(
    "/compatible",
    status_code=201,
    dependencies=[Depends(require_platform_admin)],
    response_model=CompanionEdgeCreatedResponse,
)
def set_compatible(body: CompatibilitySet, service: SpeciesService = Depends(get_species_service)):
    """Create or update a global compatibility edge between two species (platform admin)."""
    # Global companion edges are shared across all tenants; only platform admins
    # may write them. require_platform_admin bypasses in light mode (REQ-027).
    from app.common.dependencies import get_graph_repo

    graph = get_graph_repo()
    graph.set_compatibility(body.from_species_key, body.to_species_key, body.score)
    return {"status": "created"}


@router.post(
    "/incompatible",
    status_code=201,
    dependencies=[Depends(require_platform_admin)],
    response_model=CompanionEdgeCreatedResponse,
)
def set_incompatible(body: IncompatibilitySet, service: SpeciesService = Depends(get_species_service)):
    """Create or update a global incompatibility edge between two species (platform admin)."""
    # Global companion edges are shared across all tenants; only platform admins
    # may write them. require_platform_admin bypasses in light mode (REQ-027).
    from app.common.dependencies import get_graph_repo

    graph = get_graph_repo()
    graph.set_incompatibility(body.from_species_key, body.to_species_key, body.reason)
    return {"status": "created"}


@router.get(
    "/species/{species_key}/recommendations",
    response_model=CompanionRecommendationsResponse,
    response_model_exclude_unset=True,
)
def get_companion_recommendations(
    species_key: Annotated[str, Path(description="Document key of the species.")],
    service: SpeciesService = Depends(get_species_service),
):
    """Return companion recommendations for a species, with family-level fallback."""
    return service.get_companion_recommendations(species_key)
