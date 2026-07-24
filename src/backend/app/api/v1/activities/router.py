from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.api.mapping import to_response
from app.api.v1.activities.schemas import ActivityCreate, ActivityResponse, ActivityUpdate
from app.common.auth import get_current_user
from app.common.dependencies import get_activity_service
from app.common.openapi_responses import AUTH_CRUD_RESPONSES
from app.common.pagination import PaginationParams, get_pagination
from app.domain.models.activity import Activity
from app.domain.services.activity_service import ActivityService

router = APIRouter(
    prefix="/activities",
    tags=["activities"],
    dependencies=[Depends(get_current_user)],
    responses=AUTH_CRUD_RESPONSES,
)


@router.get("", response_model=list[ActivityResponse])
def list_activities(
    pagination: PaginationParams = Depends(get_pagination),
    category: str | None = Query(None, description="Filter by activity category."),
    scope: str | None = Query(
        None, pattern="^(universal|restricted)$", description="Filter by activity scope (universal or restricted)."
    ),
    species: str | None = Query(None, description="Filter by species name (substring match in species_compatible)"),
    service: ActivityService = Depends(get_activity_service),
) -> list[ActivityResponse]:
    """List catalog activities, optionally filtered by category, scope or species."""
    filters: dict = {}
    if category:
        filters["category"] = category
    if scope:
        filters["scope"] = scope
    if species:
        filters["species"] = species
    items, _ = service.list_activities(pagination.offset, pagination.limit, filters or None)
    return [to_response(a, ActivityResponse) for a in items]


@router.post("", response_model=ActivityResponse, status_code=201)
def create_activity(
    body: ActivityCreate,
    service: ActivityService = Depends(get_activity_service),
) -> ActivityResponse:
    """Create a new catalog activity."""
    activity = Activity(**body.model_dump())
    created = service.create_activity(activity)
    return to_response(created, ActivityResponse)


@router.get("/{key}", response_model=ActivityResponse)
def get_activity(
    key: Annotated[str, Path(description="Document key of the activity.")],
    service: ActivityService = Depends(get_activity_service),
) -> ActivityResponse:
    """Return a single catalog activity by key."""
    return to_response(service.get_activity(key), ActivityResponse)


@router.put("/{key}", response_model=ActivityResponse)
def update_activity(
    key: Annotated[str, Path(description="Document key of the activity.")],
    body: ActivityUpdate,
    service: ActivityService = Depends(get_activity_service),
) -> ActivityResponse:
    """Update an existing catalog activity."""
    data = body.model_dump(exclude_none=True)
    updated = service.update_activity(key, data)
    return to_response(updated, ActivityResponse)


@router.delete("/{key}", status_code=204)
def delete_activity(
    key: Annotated[str, Path(description="Document key of the activity.")],
    service: ActivityService = Depends(get_activity_service),
) -> None:
    """Delete a catalog activity."""
    service.delete_activity(key)
