from fastapi import APIRouter, Depends, Query

from app.api.v1.watering_events.schemas import (
    WateringConfirmRequest,
    WateringConfirmResponse,
    WateringEventCreate,
    WateringEventResponse,
    WateringEventWithWarnings,
    WateringQuickConfirmRequest,
    WateringStatsResponse,
)
from app.common.dependencies import get_watering_service
from app.domain.models.watering_event import WateringEvent
from app.domain.services.watering_service import WateringService

router = APIRouter(tags=["watering-events"])


def _event_response(e: WateringEvent) -> WateringEventResponse:
    return WateringEventResponse(key=e.key or "", **e.model_dump(exclude={"key"}))


# ── CRUD ─────────────────────────────────────────────────────────────

@router.post("/watering-events", response_model=WateringEventWithWarnings, status_code=201)
def create_event(
    body: WateringEventCreate,
    service: WateringService = Depends(get_watering_service),
):
    event = WateringEvent(**body.model_dump())
    result = service.create_event(event)
    return WateringEventWithWarnings(
        event=_event_response(result["event"]),
        warnings=result["warnings"],
    )


@router.get("/watering-events", response_model=list[WateringEventResponse])
def list_events(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: WateringService = Depends(get_watering_service),
):
    items, _total = service.list_events(offset, limit)
    return [_event_response(e) for e in items]


# ── Queries ──────────────────────────────────────────────────────────

@router.get(
    "/slots/{slot_key}/watering-events",
    response_model=list[WateringEventResponse],
)
def get_slot_events(
    slot_key: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: WateringService = Depends(get_watering_service),
):
    events = service.get_by_slot(slot_key, offset, limit)
    return [_event_response(e) for e in events]


@router.get(
    "/locations/{location_key}/watering-events",
    response_model=list[WateringEventResponse],
)
def get_location_events(
    location_key: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: WateringService = Depends(get_watering_service),
):
    events = service.get_by_location(location_key, offset, limit)
    return [_event_response(e) for e in events]


@router.get(
    "/locations/{location_key}/watering-stats",
    response_model=WateringStatsResponse,
)
def get_location_stats(
    location_key: str,
    service: WateringService = Depends(get_watering_service),
):
    stats = service.get_stats(location_key)
    return WateringStatsResponse(**stats)


# ── Confirm / Quick-confirm ──────────────────────────────────────────

@router.post("/watering-events/confirm", response_model=WateringConfirmResponse, status_code=201)
def confirm_watering(
    body: WateringConfirmRequest,
    service: WateringService = Depends(get_watering_service),
):
    result = service.confirm_watering(
        run_key=body.run_key,
        task_key=body.task_key,
        measured_ec=body.measured_ec,
        measured_ph=body.measured_ph,
        volume_liters=body.volume_liters,
        overrides=body.overrides,
    )
    return WateringConfirmResponse(**result)


@router.post("/watering-events/quick-confirm", response_model=WateringConfirmResponse, status_code=201)
def quick_confirm_watering(
    body: WateringQuickConfirmRequest,
    service: WateringService = Depends(get_watering_service),
):
    result = service.quick_confirm_watering(body.run_key, body.task_key)
    return WateringConfirmResponse(**result)
