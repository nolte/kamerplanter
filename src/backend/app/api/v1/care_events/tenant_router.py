"""The care log of the tenant (REQ-053 §13, §21.2): GP-API-033…037 and GP-API-041.

Every route resolves its bed, its event and every key of the body **in the service** through the tenant anchor
(§22.3); the gate here only decides the caller's rank. A foreign and an absent event answer 404 alike, a foreign
reference inside the body 422 ``reference.not_found``. The role rules the gate cannot express (the author may
correct their own entry, the author may undo within ten minutes, only the lead cancels or redacts the rest) are
the service's.
"""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Request

from app.api.v1.auth.router import limiter, user_rate_limit_key
from app.api.v1.care_events.schemas import (
    CareEventCreate,
    CareEventRedactRequest,
    CareEventResponse,
    CareEventSupersedeRequest,
    CareEventVoidRequest,
    care_event_to_response,
)
from app.common.auth import get_current_tenant, require_permission
from app.common.dependencies import get_care_event_service
from app.common.exceptions import ValidationError
from app.common.openapi_responses import FORBIDDEN_RESPONSE, NOT_FOUND_RESPONSE, VALIDATION_RESPONSE
from app.common.pagination import PaginationParams, get_pagination
from app.config.settings import settings
from app.core.permissions import Action, ResourceType
from app.domain.interfaces.care_event_repository import CareEventFilter
from app.domain.models.care_event import CARE_EVENT_CATEGORIES
from app.domain.models.tenant_context import TenantContext
from app.domain.services.care_event_service import CareEventService

router = APIRouter(prefix="/care-events", tags=["care-events"], responses=NOT_FOUND_RESPONSE)

_EVENT_KEY = Annotated[str, Path(description="Document key of the care event.")]


def _as_utc(moment: datetime | None) -> datetime | None:
    """A naive ``from`` / ``to`` is read as UTC, as ``performed_at`` is on the way in (§20.13)."""
    return moment.replace(tzinfo=UTC) if moment is not None and moment.tzinfo is None else moment


@router.get("", response_model=list[CareEventResponse], summary="List the care log")
def list_care_events(
    location_key: str | None = Query(None, description="Only the events of this bed."),
    plant_key: str | None = Query(None, description="Only the events that name this plant."),
    category: str | None = Query(None, description="Only this category."),
    performed_from: datetime | None = Query(None, alias="from", description="`performed_at` from (inclusive)."),
    performed_to: datetime | None = Query(None, alias="to", description="`performed_at` until (inclusive)."),
    performed_by: str | None = Query(None, description="Account key of a member, as the member list names it."),
    include_superseded: bool = Query(False, description="Also the entries a correction replaced."),
    pagination: PaginationParams = Depends(get_pagination),
    ctx: TenantContext = Depends(get_current_tenant),
    service: CareEventService = Depends(get_care_event_service),
) -> list[CareEventResponse]:
    """The tenant's care log, newest first (GP-API-034, GP-FR-107); the last 90 days when no range is given.

    `performed_by` is shown as a display name or `anonymisiert`, never as an account key.
    """
    if category is not None and category not in CARE_EVENT_CATEGORIES:
        raise ValidationError(
            f"Unknown category '{category}'.", details=[{"field": "category", "message": "unknown category"}]
        )
    if performed_from and performed_to and performed_to < performed_from:
        raise ValidationError(
            "'to' lies before 'from'.", details=[{"field": "to", "message": "must not be before 'from'"}]
        )
    criteria = CareEventFilter(
        location_key=location_key,
        plant_key=plant_key,
        category=category,
        performed_from=_as_utc(performed_from),
        performed_to=_as_utc(performed_to),
        performed_by=performed_by,
        include_superseded=include_superseded,
    )
    views = service.list_window(
        criteria, tenant_key=ctx.tenant_key, user_key=ctx.user_key, offset=pagination.offset, limit=pagination.limit
    )
    return [care_event_to_response(view) for view in views]


@router.post(
    "",
    response_model=CareEventResponse,
    status_code=201,
    summary="Log a care event without a task",
    responses={**FORBIDDEN_RESPONSE, **VALIDATION_RESPONSE},
)
@limiter.limit(settings.rate_limit_care_events, key_func=user_rate_limit_key)
def create_care_event(
    request: Request,
    body: CareEventCreate,
    ctx: TenantContext = Depends(require_permission(ResourceType.CARE_EVENT, Action.CREATE)),
    service: CareEventService = Depends(get_care_event_service),
) -> CareEventResponse:
    """Log a care event (GP-API-033). The performer is the caller (GP-NFR-054).

    `trigger` is `manual` or `observation`; every other trigger, `task_key`, `source_ref` and the server-only
    categories are refused. 404 for a foreign bed; 422 `reference.not_found` for a plant outside the bed, a foreign
    photo, product or member; 422 `care_event.performed_in_future` / `care_event.too_old` (V-11).
    """
    view = service.create(
        body,
        tenant_key=ctx.tenant_key,
        user_key=ctx.user_key,
        role=ctx.role,
    )
    return care_event_to_response(view)


@router.get("/{key}", response_model=CareEventResponse, summary="One care event with its supersede chain")
def get_care_event(
    key: _EVENT_KEY,
    ctx: TenantContext = Depends(get_current_tenant),
    service: CareEventService = Depends(get_care_event_service),
) -> CareEventResponse:
    """One event and, in `chain`, the keys of its supersede chain, oldest first (GP-API-035)."""
    return care_event_to_response(service.get(key, tenant_key=ctx.tenant_key, user_key=ctx.user_key))


@router.post(
    "/{key}/supersede",
    response_model=CareEventResponse,
    status_code=201,
    summary="Correct a care event",
    responses={**FORBIDDEN_RESPONSE, **VALIDATION_RESPONSE},
)
@limiter.limit(settings.rate_limit_care_events, key_func=user_rate_limit_key)
def supersede_care_event(
    request: Request,
    key: _EVENT_KEY,
    body: CareEventSupersedeRequest,
    ctx: TenantContext = Depends(require_permission(ResourceType.CARE_EVENT, Action.UPDATE)),
    service: CareEventService = Depends(get_care_event_service),
) -> CareEventResponse:
    """Correct an entry (GP-API-036): a new entry supersedes it, the old one stays readable.

    The author corrects their own entry, a lead any (403 otherwise). 422 `care_event.sequence` when the entry is
    superseded or voided already (V-13).
    """
    view = service.supersede(
        key,
        body,
        tenant_key=ctx.tenant_key,
        user_key=ctx.user_key,
        role=ctx.role,
    )
    return care_event_to_response(view)


@router.post(
    "/{key}/void",
    response_model=CareEventResponse,
    summary="Cancel a care event",
    responses={**FORBIDDEN_RESPONSE, **VALIDATION_RESPONSE},
)
@limiter.limit(settings.rate_limit_care_events, key_func=user_rate_limit_key)
def void_care_event(
    request: Request,
    key: _EVENT_KEY,
    body: CareEventVoidRequest,
    ctx: TenantContext = Depends(require_permission(ResourceType.CARE_EVENT, Action.UPDATE)),
    service: CareEventService = Depends(get_care_event_service),
) -> CareEventResponse:
    """Cancel an entry (GP-API-037). A lead any time; the author their own within ten minutes with `reason: undo`."""
    view = service.void(key, reason=body.reason, tenant_key=ctx.tenant_key, user_key=ctx.user_key, role=ctx.role)
    return care_event_to_response(view)


@router.post(
    "/{key}/redact",
    response_model=CareEventResponse,
    summary="Redact a care event and its supersede chain",
    responses={**FORBIDDEN_RESPONSE, **VALIDATION_RESPONSE},
)
@limiter.limit(settings.rate_limit_care_events, key_func=user_rate_limit_key)
async def redact_care_event(
    request: Request,
    key: _EVENT_KEY,
    body: CareEventRedactRequest,
    ctx: TenantContext = Depends(require_permission(ResourceType.CARE_EVENT, Action.DELETE)),
    service: CareEventService = Depends(get_care_event_service),
) -> CareEventResponse:
    """Lead only (GP-API-041, GP-FR-109): the free texts of the entry and its whole chain become `[redacted]`,
    the photos are detached and — unless another carrier holds them — deleted. Written to `garden_plan_audit`.

    `reason` is stored on the entry and stays after the redaction: give the ground ("personal data of a third
    party"), never the data itself.
    """
    view = await service.redact(
        key, reason=body.reason, tenant_key=ctx.tenant_key, user_key=ctx.user_key, role=ctx.role
    )
    return care_event_to_response(view)
