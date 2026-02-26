from fastapi import APIRouter, Depends, Query

from app.api.v1.feeding_events.schemas import (
    FeedingEventCreate,
    FeedingEventResponse,
    FeedingEventUpdate,
)
from app.common.dependencies import get_feeding_service
from app.domain.models.feeding_event import FeedingEvent
from app.domain.services.feeding_service import FeedingService

router = APIRouter(prefix="/feeding-events", tags=["feeding-events"])


def _event_response(e: FeedingEvent) -> FeedingEventResponse:
    return FeedingEventResponse(key=e.key or "", **e.model_dump(exclude={"key"}))


# ── CRUD ─────────────────────────────────────────────────────────────

@router.get("", response_model=list[FeedingEventResponse])
def list_events(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: FeedingService = Depends(get_feeding_service),
):
    items, _total = service.list_events(offset, limit)
    return [_event_response(e) for e in items]


@router.post("", response_model=FeedingEventResponse, status_code=201)
def create_event(
    body: FeedingEventCreate,
    service: FeedingService = Depends(get_feeding_service),
):
    event = FeedingEvent(**body.model_dump())
    created = service.create_event(event)
    return _event_response(created)


@router.get("/{key}", response_model=FeedingEventResponse)
def get_event(key: str, service: FeedingService = Depends(get_feeding_service)):
    e = service.get_event(key)
    return _event_response(e)


@router.put("/{key}", response_model=FeedingEventResponse)
def update_event(
    key: str,
    body: FeedingEventUpdate,
    service: FeedingService = Depends(get_feeding_service),
):
    data = body.model_dump(exclude_none=True)
    updated = service.update_event(key, data)
    return _event_response(updated)


@router.delete("/{key}", status_code=204)
def delete_event(key: str, service: FeedingService = Depends(get_feeding_service)):
    service.delete_event(key)


# ── Queries ──────────────────────────────────────────────────────────

@router.get("/{key}/runoff")
def analyze_runoff(key: str, service: FeedingService = Depends(get_feeding_service)):
    return service.analyze_runoff(key)


@router.get("/plant/{pk}", response_model=list[FeedingEventResponse])
def get_plant_history(
    pk: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: FeedingService = Depends(get_feeding_service),
):
    events = service.get_by_plant(pk, offset, limit)
    return [_event_response(e) for e in events]
