from fastapi import APIRouter, Depends, Query

from app.api.v1.activities.schemas import ActivityCreate, ActivityResponse, ActivityUpdate
from app.common.dependencies import get_activity_service
from app.domain.models.activity import Activity
from app.domain.services.activity_service import ActivityService

router = APIRouter(prefix="/activities", tags=["activities"])


def _to_response(a: Activity) -> ActivityResponse:
    return ActivityResponse(key=a.key or "", **a.model_dump(exclude={"key"}))


@router.get("", response_model=list[ActivityResponse])
def list_activities(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    category: str | None = None,
    scope: str | None = Query(None, pattern="^(universal|restricted)$"),
    species: str | None = Query(None, description="Filter by species name (substring match in species_compatible)"),
    service: ActivityService = Depends(get_activity_service),
) -> list[ActivityResponse]:
    filters: dict = {}
    if category:
        filters["category"] = category
    if scope:
        filters["scope"] = scope
    if species:
        filters["species"] = species
    items, _ = service.list_activities(offset, limit, filters or None)
    return [_to_response(a) for a in items]


@router.post("", response_model=ActivityResponse, status_code=201)
def create_activity(
    body: ActivityCreate,
    service: ActivityService = Depends(get_activity_service),
) -> ActivityResponse:
    activity = Activity(**body.model_dump())
    created = service.create_activity(activity)
    return _to_response(created)


@router.get("/{key}", response_model=ActivityResponse)
def get_activity(
    key: str,
    service: ActivityService = Depends(get_activity_service),
) -> ActivityResponse:
    return _to_response(service.get_activity(key))


@router.put("/{key}", response_model=ActivityResponse)
def update_activity(
    key: str,
    body: ActivityUpdate,
    service: ActivityService = Depends(get_activity_service),
) -> ActivityResponse:
    data = body.model_dump(exclude_none=True)
    updated = service.update_activity(key, data)
    return _to_response(updated)


@router.delete("/{key}", status_code=204)
def delete_activity(
    key: str,
    service: ActivityService = Depends(get_activity_service),
) -> None:
    service.delete_activity(key)
