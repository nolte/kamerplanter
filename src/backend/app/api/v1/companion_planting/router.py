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
from app.common.auth import get_active_tenant_key, get_current_user, require_platform_admin
from app.common.dependencies import get_companion_edge_service, get_species_service
from app.common.openapi_responses import AUTH_RESPONSES, NOT_FOUND_RESPONSE
from app.domain.services.companion_edge_service import CompanionEdgeService
from app.domain.services.species_service import SpeciesService

router = APIRouter(
    prefix="/companion-planting",
    tags=["companion-planting"],
    dependencies=[Depends(get_current_user)],
    responses={**AUTH_RESPONSES, **NOT_FOUND_RESPONSE},
)


@router.get("/counts", response_model=dict[str, SpeciesCompanionCounts])
def get_counts(
    service: SpeciesService = Depends(get_species_service),
    tenant_key: str = Depends(get_active_tenant_key),
) -> dict[str, dict[str, int]]:
    """Return per-species compatible/incompatible companion counts for the catalogue the caller sees."""
    # Whole-catalogue aggregate keyed by species_key: one batch request feeds the
    # per-species companion badges in the selection dropdown (no N+1). Counted over
    # the edges whose both ends the caller can see (MT-054, #2144).
    return service.get_companion_counts(tenant_key=tenant_key)


@router.get("/species/{species_key}/compatible", response_model=list[CompatibleSpeciesResponse])
def get_compatible(
    species_key: Annotated[str, Path(description="Document key of the species.")],
    service: SpeciesService = Depends(get_species_service),
    tenant_key: str = Depends(get_active_tenant_key),
):
    """List the species that are compatible companions of the given species."""
    # SEC-005 (#808): a *foreign* anchor answers 404; MT-054 (#2144): the far end of
    # each edge is filtered with the same visibility.
    return service.get_compatible_species(species_key, tenant_key=tenant_key)


@router.get("/species/{species_key}/incompatible", response_model=list[IncompatibleSpeciesResponse])
def get_incompatible(
    species_key: Annotated[str, Path(description="Document key of the species.")],
    service: SpeciesService = Depends(get_species_service),
    tenant_key: str = Depends(get_active_tenant_key),
):
    """List the species that are incompatible companions of the given species."""
    # SEC-005: foreign anchor → 404; MT-054: the far end is filtered too.
    return service.get_incompatible_species(species_key, tenant_key=tenant_key)


@router.post(
    "/compatible",
    status_code=201,
    dependencies=[Depends(require_platform_admin)],
    response_model=CompanionEdgeCreatedResponse,
)
def set_compatible(body: CompatibilitySet, service: CompanionEdgeService = Depends(get_companion_edge_service)):
    """Create or update a global compatibility edge between two species (platform admin)."""
    # Global companion edges are shared across all tenants; only platform admins
    # may write them, and only between two global species (MT-054, #2144).
    # require_platform_admin bypasses in light mode (REQ-027).
    service.set_compatibility(body.from_species_key, body.to_species_key, body.score)
    return {"status": "created"}


@router.post(
    "/incompatible",
    status_code=201,
    dependencies=[Depends(require_platform_admin)],
    response_model=CompanionEdgeCreatedResponse,
)
def set_incompatible(body: IncompatibilitySet, service: CompanionEdgeService = Depends(get_companion_edge_service)):
    """Create or update a global incompatibility edge between two species (platform admin)."""
    # Global companion edges are shared across all tenants; only platform admins
    # may write them, and only between two global species (MT-054, #2144).
    service.set_incompatibility(body.from_species_key, body.to_species_key, body.reason)
    return {"status": "created"}


@router.get(
    "/species/{species_key}/recommendations",
    response_model=CompanionRecommendationsResponse,
    response_model_exclude_unset=True,
)
def get_companion_recommendations(
    species_key: Annotated[str, Path(description="Document key of the species.")],
    service: SpeciesService = Depends(get_species_service),
    tenant_key: str = Depends(get_active_tenant_key),
):
    """Return companion recommendations for a species, with family-level fallback."""
    # SEC-005: foreign anchor → 404; MT-054: every listed species is one the caller can see.
    return service.get_companion_recommendations(species_key, tenant_key=tenant_key)
