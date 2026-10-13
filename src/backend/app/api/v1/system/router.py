"""The light-to-full take-over (REQ-027 §7a.2/§7a.4, #1855). Mounted in full mode only."""

from fastapi import APIRouter, Depends, Request

from app.api.v1.auth.router import limiter, user_rate_limit_key
from app.api.v1.system.schemas import (
    TakeoverDecisionRequest,
    TakeoverResourceCountsResponse,
    TakeoverResultResponse,
    TakeoverStatusResponse,
)
from app.common.auth import get_authenticated_with_api_key, require_account_principal
from app.common.dependencies import get_mode_switch_service
from app.common.openapi_responses import AUTH_CRUD_RESPONSES, STEP_UP_RESPONSES
from app.common.request_ip import resolve_client_ip
from app.config.settings import settings
from app.domain.models.user import User
from app.domain.services.mode_switch_service import ModeSwitchService, TakeoverConfirmation

router = APIRouter(prefix="/system", tags=["system"], responses=AUTH_CRUD_RESPONSES)


@router.get("/takeover-status", response_model=TakeoverStatusResponse)
@limiter.limit(settings.rate_limit_takeover, key_func=user_rate_limit_key)
def get_takeover_status(
    request: Request,
    user: User = Depends(require_account_principal),
    service: ModeSwitchService = Depends(get_mode_switch_service),
) -> TakeoverStatusResponse:
    """Whether the data of a former light-mode installation wait to be taken over.

    ``eligible`` says whether the caller may decide it - the platform administrator or, on an
    instance without one, the first account. Only then are the tenant's name, slug and size
    (plants, sites, runs, nutrient plans, tasks) returned.
    """
    status = service.takeover_status(user)
    counts = status.resource_counts
    return TakeoverStatusResponse(
        pending=status.pending,
        eligible=status.eligible,
        tenant_key=status.tenant_key,
        tenant_name=status.tenant_name,
        tenant_slug=status.tenant_slug,
        resource_counts=None
        if counts is None
        else TakeoverResourceCountsResponse(
            plants=counts.plants,
            sites=counts.sites,
            planting_runs=counts.planting_runs,
            nutrient_plans=counts.nutrient_plans,
            tasks=counts.tasks,
        ),
    )


@router.post("/takeover", response_model=TakeoverResultResponse, responses=STEP_UP_RESPONSES)
@limiter.limit(settings.rate_limit_takeover, key_func=user_rate_limit_key)
def decide_takeover(
    request: Request,
    body: TakeoverDecisionRequest,
    user: User = Depends(require_account_principal),
    authenticated_with_api_key: bool = Depends(get_authenticated_with_api_key),
    client_ip: str | None = Depends(resolve_client_ip),
    service: ModeSwitchService = Depends(get_mode_switch_service),
) -> TakeoverResultResponse:
    """Accept (``accept: true``) or decline the take-over of the light-mode data.

    Accepting makes the caller ``lead`` of the light-mode tenant (with both administrative scopes);
    the data stay where they are. Declining leaves the tenant without owner for a platform
    administrator. Either decision makes an instance without a platform administrator hand that role
    to the caller. Passes the caller's step-up (``light_mode_takeover``, target ``system-tenant``).
    403 for anyone else and for an API key (a person decides this in a session); 404 when no
    take-over is open or another decision is running.
    """
    result = service.decide_takeover(
        user,
        accept=body.accept,
        confirmation=TakeoverConfirmation(
            password=body.current_password, step_up_code=body.step_up_code, step_up_token=body.step_up_token
        ),
        authenticated_with_api_key=authenticated_with_api_key,
        client_ip=client_ip,
    )
    return TakeoverResultResponse(
        accepted=result.accepted,
        tenant_slug=result.tenant_slug,
        platform_admin_granted=result.platform_admin_granted,
    )
