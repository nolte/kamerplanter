from typing import Annotated

from fastapi import APIRouter, Depends, Path

from app.api.mapping import to_response
from app.api.v1.feeding_events.schemas import (
    FeedingEventCreate,
    FeedingEventResponse,
    FeedingEventUpdate,
    RunoffAnalysisResponse,
)
from app.common.auth import get_current_tenant
from app.common.dependencies import get_feeding_service
from app.common.openapi_responses import NOT_FOUND_RESPONSE
from app.common.pagination import PaginationParams, get_pagination
from app.domain.models.feeding_event import FeedingEvent
from app.domain.models.tenant_context import TenantContext
from app.domain.services.feeding_service import FeedingService

router = APIRouter(prefix="/feeding-events", tags=["feeding-events"], responses=NOT_FOUND_RESPONSE)


def _event_response(e: FeedingEvent) -> FeedingEventResponse:
    return to_response(e, FeedingEventResponse)


@router.get("", response_model=list[FeedingEventResponse])
def list_events(
    pagination: PaginationParams = Depends(get_pagination),
    ctx: TenantContext = Depends(get_current_tenant),
    service: FeedingService = Depends(get_feeding_service),
):
    """List the tenant's feeding events (paginated)."""
    items, _total = service.list_events(pagination.offset, pagination.limit, tenant_key=ctx.tenant_key)
    return [_event_response(e) for e in items]


@router.post("", response_model=FeedingEventResponse, status_code=201)
def create_event(
    body: FeedingEventCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: FeedingService = Depends(get_feeding_service),
):
    """Record a new feeding event for the tenant."""
    event = FeedingEvent(**body.model_dump(), tenant_key=ctx.tenant_key)
    created = service.create_event(event)
    return _event_response(created)


@router.get("/{key}", response_model=FeedingEventResponse)
def get_event(
    key: Annotated[str, Path(description="Document key of the feeding event.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: FeedingService = Depends(get_feeding_service),
):
    """Return a single feeding event by key."""
    e = service.get_event(key, tenant_key=ctx.tenant_key)
    return _event_response(e)


@router.put("/{key}", response_model=FeedingEventResponse)
def update_event(
    key: Annotated[str, Path(description="Document key of the feeding event.")],
    body: FeedingEventUpdate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: FeedingService = Depends(get_feeding_service),
):
    """Update an existing feeding event."""
    service.get_event(key, tenant_key=ctx.tenant_key)
    data = body.model_dump(exclude_none=True)
    updated = service.update_event(key, data)
    return _event_response(updated)


@router.delete("/{key}", status_code=204)
def delete_event(
    key: Annotated[str, Path(description="Document key of the feeding event.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: FeedingService = Depends(get_feeding_service),
):
    """Delete a feeding event."""
    service.get_event(key, tenant_key=ctx.tenant_key)
    service.delete_event(key)


@router.get("/{key}/runoff", response_model=RunoffAnalysisResponse, response_model_exclude_unset=True)
def analyze_runoff(
    key: Annotated[str, Path(description="Document key of the feeding event.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: FeedingService = Depends(get_feeding_service),
):
    """Analyze a feeding event's drain-to-waste runoff (EC/pH/volume)."""
    service.get_event(key, tenant_key=ctx.tenant_key)
    return service.analyze_runoff(key)


@router.get("/plant/{pk}", response_model=list[FeedingEventResponse])
def get_plant_history(
    pk: Annotated[str, Path(description="Document key of the plant.")],
    pagination: PaginationParams = Depends(get_pagination),
    ctx: TenantContext = Depends(get_current_tenant),
    service: FeedingService = Depends(get_feeding_service),
):
    """List a plant's feeding-event history (paginated)."""
    events = service.get_by_plant(pk, pagination.offset, pagination.limit)
    return [_event_response(e) for e in events]
