"""Tenant-scoped favorites router.

Wraps favorites endpoints under /t/{tenant_slug}/favorites so that
get_current_tenant enforces membership. Favorites are user-global
(not per-tenant).
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.api.v1.favorites.schemas import (
    FavoriteCreateRequest,
    FavoriteRemovedResponse,
    FavoriteResponse,
    NutrientPlanMatchResponse,
)
from app.common.auth import get_current_tenant, require_account_principal
from app.common.dependencies import get_favorites_service
from app.domain.models.tenant_context import TenantContext
from app.domain.services.favorites_service import FavoritesService

# Writes of the caller's ACCOUNT-WIDE settings below depend on
# ``require_account_principal``: the tenant in the path admits a tenant-scoped API
# key, but these settings span every tenant of its owner (#1851).
router = APIRouter(prefix="/favorites", tags=["favorites"])


def _edge_to_response(edge: dict) -> FavoriteResponse:
    to_id = edge.get("_to", "")
    target_key = to_id.split("/", 1)[-1] if "/" in to_id else to_id
    return FavoriteResponse(
        key=edge.get("_key", ""),
        target_key=target_key,
        target_type=edge.get("target_type", ""),
        source=edge.get("source", "manual"),
        cascade_from_key=edge.get("cascade_from_key"),
        favorited_at=edge.get("favorited_at", ""),
    )


@router.get("", response_model=list[FavoriteResponse], dependencies=[Depends(require_account_principal)])
def list_favorites(
    type: str | None = Query(default=None, description="Filter by entity type: species, nutrient_plans, fertilizers"),
    ctx: TenantContext = Depends(get_current_tenant),
    service: FavoritesService = Depends(get_favorites_service),
):
    """List the calling user's favorites, optionally filtered by entity type."""
    edges = service.list_favorites(ctx.user_key, entity_type=type)
    return [_edge_to_response(e) for e in edges]


@router.post("", response_model=FavoriteResponse, status_code=201)
def add_favorite(
    body: FavoriteCreateRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: FavoritesService = Depends(get_favorites_service),
):
    """Add an entity to the calling user's favorites.

    Favourites are personal and span tenants: a global catalogue entry or one
    owned by the caller's active tenant may be favourited, a foreign tenant's
    entry is refused (#965). The active ``ctx.tenant_key`` is the tenant anchor.
    """
    edge = service.add_favorite(ctx.user_key, body.target_key, tenant_key=ctx.tenant_key, source=body.source)
    return _edge_to_response(edge)


@router.delete(
    "/{target_key}", response_model=FavoriteRemovedResponse, dependencies=[Depends(require_account_principal)]
)
def remove_favorite(
    target_key: Annotated[str, Path(description="Document key of the favorited entity.")],
    cascade_cleanup: bool = Query(default=True, description="Also remove cascaded favorites (e.g. plan fertilizers)."),
    ctx: TenantContext = Depends(get_current_tenant),
    service: FavoritesService = Depends(get_favorites_service),
):
    """Remove an entity from the calling user's favorites."""
    removed = service.remove_favorite(ctx.user_key, target_key, cascade_cleanup=cascade_cleanup)
    return {"removed": removed}


@router.get("/nutrient-plans/matching", response_model=list[NutrientPlanMatchResponse])
def get_matching_nutrient_plans(
    species_keys: str = Query(description="Comma-separated species keys"),
    ctx: TenantContext = Depends(get_current_tenant),
    service: FavoritesService = Depends(get_favorites_service),
):
    """List the template nutrient plans linked to any of the given species.

    Returns the template plans visible to the active tenant (own ∪ global, #1561)
    whose species relation contains at least one of ``species_keys`` (#1618),
    most-matching first. A plan linked to no species is never returned, so an
    empty list means "no plan is written for these species yet", not an error.
    """
    # REQ-020's example spells the keys as document ids (``species/<key>``); the
    # wizard sends bare keys. Both name the same species, so both are accepted.
    keys = [k.strip().removeprefix("species/") for k in species_keys.split(",") if k.strip()]
    return service.get_matching_nutrient_plans(keys, tenant_key=ctx.tenant_key)
