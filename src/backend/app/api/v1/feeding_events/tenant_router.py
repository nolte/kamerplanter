from fastapi import APIRouter, Depends

from app.api.v1.feeding_events.schemas import (
    FeedingEventCreate,
    FeedingEventResponse,
    FeedingEventUpdate,
)
from app.common.auth import get_current_tenant
from app.common.dependencies import get_feeding_service
from app.common.pagination import PaginationParams, get_pagination
from app.domain.models.feeding_event import FeedingEvent
from app.domain.models.tenant_context import TenantContext
from app.domain.services.feeding_service import FeedingService

router = APIRouter(prefix="/feeding-events", tags=["feeding-events"])


def _event_response(e: FeedingEvent) -> FeedingEventResponse:
    return FeedingEventResponse(key=e.key or "", **e.model_dump(exclude={"key"}))


@router.get("", response_model=list[FeedingEventResponse])
def list_events(
    pagination: PaginationParams = Depends(get_pagination),
    ctx: TenantContext = Depends(get_current_tenant),
    service: FeedingService = Depends(get_feeding_service),
):
    items, _total = service.list_events(pagination.offset, pagination.limit, tenant_key=ctx.tenant_key)
    return [_event_response(e) for e in items]


@router.post("", response_model=FeedingEventResponse, status_code=201)
def create_event(
    body: FeedingEventCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: FeedingService = Depends(get_feeding_service),
):
    event = FeedingEvent(**body.model_dump(), tenant_key=ctx.tenant_key)
    created = service.create_event(event)
    return _event_response(created)


@router.get("/{key}", response_model=FeedingEventResponse)
def get_event(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: FeedingService = Depends(get_feeding_service),
):
    e = service.get_event(key, tenant_key=ctx.tenant_key)
    return _event_response(e)


@router.put("/{key}", response_model=FeedingEventResponse)
def update_event(
    key: str,
    body: FeedingEventUpdate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: FeedingService = Depends(get_feeding_service),
):
    service.get_event(key, tenant_key=ctx.tenant_key)
    data = body.model_dump(exclude_none=True)
    updated = service.update_event(key, data)
    return _event_response(updated)


@router.delete("/{key}", status_code=204)
def delete_event(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: FeedingService = Depends(get_feeding_service),
):
    service.get_event(key, tenant_key=ctx.tenant_key)
    service.delete_event(key)


@router.get("/{key}/runoff")
def analyze_runoff(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: FeedingService = Depends(get_feeding_service),
):
    service.get_event(key, tenant_key=ctx.tenant_key)
    return service.analyze_runoff(key)


@router.get("/plant/{pk}", response_model=list[FeedingEventResponse])
def get_plant_history(
    pk: str,
    pagination: PaginationParams = Depends(get_pagination),
    ctx: TenantContext = Depends(get_current_tenant),
    service: FeedingService = Depends(get_feeding_service),
):
    events = service.get_by_plant(pk, pagination.offset, pagination.limit)
    return [_event_response(e) for e in events]
