"""Tenant-scoped favorites router.

Wraps favorites endpoints under /t/{tenant_slug}/favorites so that
get_current_tenant enforces membership. Favorites are user-global
(not per-tenant).
"""

from fastapi import APIRouter, Depends, Query

from app.api.v1.favorites.schemas import (
    FavoriteCreateRequest,
    FavoriteResponse,
    NutrientPlanMatchResponse,
)
from app.common.auth import get_current_tenant
from app.common.dependencies import get_favorites_service
from app.domain.models.tenant_context import TenantContext
from app.domain.services.favorites_service import FavoritesService

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


@router.get("", response_model=list[FavoriteResponse])
def list_favorites(
    type: str | None = Query(default=None, description="Filter by entity type: species, nutrient_plans, fertilizers"),
    ctx: TenantContext = Depends(get_current_tenant),
    service: FavoritesService = Depends(get_favorites_service),
):
    edges = service.list_favorites(ctx.user_key, entity_type=type)
    return [_edge_to_response(e) for e in edges]


@router.post("", response_model=FavoriteResponse, status_code=201)
def add_favorite(
    body: FavoriteCreateRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: FavoritesService = Depends(get_favorites_service),
):
    edge = service.add_favorite(ctx.user_key, body.target_key, source=body.source)
    return _edge_to_response(edge)


@router.delete("/{target_key}")
def remove_favorite(
    target_key: str,
    cascade_cleanup: bool = Query(default=True),
    ctx: TenantContext = Depends(get_current_tenant),
    service: FavoritesService = Depends(get_favorites_service),
):
    removed = service.remove_favorite(ctx.user_key, target_key, cascade_cleanup=cascade_cleanup)
    return {"removed": removed}


@router.get("/nutrient-plans/matching", response_model=list[NutrientPlanMatchResponse])
def get_matching_nutrient_plans(
    species_keys: str = Query(description="Comma-separated species keys"),
    ctx: TenantContext = Depends(get_current_tenant),
    service: FavoritesService = Depends(get_favorites_service),
):
    keys = [k.strip() for k in species_keys.split(",") if k.strip()]
    return service.get_matching_nutrient_plans(keys)
