"""A tenant's service accounts — ``/t/{slug}/service-accounts`` (REQ-023 §5b, #2137 / MT-041).

Every route takes the ``technical`` scope at the route (:func:`require_admin_scope`) **and** the
``lead`` role (:func:`require_tenant_role`); the service re-checks both from the stored membership. The
three writes pass the acting lead's own step-up (``service_account_change``): 401 without it, 403 from
an API-key request or a service account, 429 ``STEP_UP_LOCKED``. Light mode answers 403 — its one
account is reached without authenticating, so a credential minted there proves nothing (#1844).
"""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path

from app.api.v1.service_accounts.schemas import (
    ServiceAccountCreatedResponse,
    ServiceAccountCreateRequest,
    ServiceAccountKeyRotatedResponse,
    ServiceAccountRemovalRequest,
    ServiceAccountResponse,
    ServiceAccountRotateRequest,
)
from app.api.v1.tenants.schemas import MessageResponse
from app.common.auth import (
    get_authenticated_with_api_key,
    get_current_user,
    refuse_in_light_mode,
    require_admin_scope,
    require_tenant_role,
)
from app.common.dependencies import get_tenant_service
from app.common.enums import AdminScope, TenantRole
from app.common.openapi_responses import STEP_UP_RESPONSES
from app.common.request_ip import resolve_client_ip
from app.domain.models.service_account import ServiceAccountCreated, ServiceAccountInfo, ServiceAccountKeyRotated
from app.domain.models.tenant_context import TenantContext
from app.domain.models.user import User
from app.domain.services.tenant_service import TenantService

router = APIRouter(
    prefix="/service-accounts",
    tags=["service-accounts"],
    # Light mode first: its one account is reached without authenticating, so a credential minted there
    # proves nothing about who asked for it (#1844); the service refuses it too.
    dependencies=[Depends(refuse_in_light_mode), Depends(require_tenant_role(TenantRole.LEAD))],
)

ServiceAccountKey = Annotated[str, Path(description="Account key of the service account.")]


@router.post("", response_model=ServiceAccountCreatedResponse, status_code=201, responses=STEP_UP_RESPONSES)
def create_service_account(
    body: ServiceAccountCreateRequest,
    ctx: TenantContext = Depends(require_admin_scope(AdminScope.TECHNICAL)),
    user: User = Depends(get_current_user),
    via_api_key: bool = Depends(get_authenticated_with_api_key),
    client_ip: str | None = Depends(resolve_client_ip),
    service: TenantService = Depends(get_tenant_service),
) -> ServiceAccountCreated:
    """Create a service account with its first API key — the raw key is in this response only.

    The account is a ``viewer`` or ``grower`` of this tenant; its key is always scoped to it and carries
    the requested ``ip_allowlist`` / ``rate_limit_per_minute`` / ``expires_at``. 422 for an unusable
    control, ``SERVICE_ACCOUNT_LIMIT_REACHED`` (``TENANT_MAX_SERVICE_ACCOUNTS``) or
    ``MEMBER_LIMIT_REACHED`` — all before the password is asked for.
    """
    # The domain model goes out as it is: FastAPI validates it against ``response_model``.
    return service.create_service_account(
        tenant_key=ctx.tenant_key,
        name=body.name,
        role=body.role,
        ip_allowlist=body.ip_allowlist,
        rate_limit_per_minute=body.rate_limit_per_minute,
        expires_at=body.expires_at,
        requester=user,
        current_password=body.current_password,
        step_up_code=body.step_up_code,
        step_up_token=body.step_up_token,
        authenticated_with_api_key=via_api_key,
        client_ip=client_ip,
    )


@router.get("", response_model=list[ServiceAccountResponse])
def list_service_accounts(
    ctx: TenantContext = Depends(require_admin_scope(AdminScope.TECHNICAL)),
    user: User = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
) -> list[ServiceAccountInfo]:
    """The tenant's active service accounts with the keys each holds here (metadata only, never a raw key)."""
    return service.list_service_accounts(tenant_key=ctx.tenant_key, requester=user)


@router.post(
    "/{service_account_key}/rotate-key",
    response_model=ServiceAccountKeyRotatedResponse,
    status_code=201,
    responses=STEP_UP_RESPONSES,
)
def rotate_service_account_key(
    service_account_key: ServiceAccountKey,
    body: ServiceAccountRotateRequest,
    ctx: TenantContext = Depends(require_admin_scope(AdminScope.TECHNICAL)),
    user: User = Depends(get_current_user),
    via_api_key: bool = Depends(get_authenticated_with_api_key),
    client_ip: str | None = Depends(resolve_client_ip),
    service: TenantService = Depends(get_tenant_service),
) -> ServiceAccountKeyRotated:
    """Mint a new key; the previous keys are revoked at once (``overlap_minutes`` 0) or end after the overlap.

    The new key keeps the newest previous key's allowlist and rate limit. 404 for an account that is not
    a service account of this tenant.
    """
    return service.rotate_service_account_key(
        service_account_key,
        tenant_key=ctx.tenant_key,
        overlap_minutes=body.overlap_minutes,
        expires_at=body.expires_at,
        requester=user,
        current_password=body.current_password,
        step_up_code=body.step_up_code,
        step_up_token=body.step_up_token,
        authenticated_with_api_key=via_api_key,
        client_ip=client_ip,
    )


@router.delete("/{service_account_key}", response_model=MessageResponse, responses=STEP_UP_RESPONSES)
def remove_service_account(
    service_account_key: ServiceAccountKey,
    body: Annotated[ServiceAccountRemovalRequest | None, Body()] = None,
    ctx: TenantContext = Depends(require_admin_scope(AdminScope.TECHNICAL)),
    user: User = Depends(get_current_user),
    via_api_key: bool = Depends(get_authenticated_with_api_key),
    client_ip: str | None = Depends(resolve_client_ip),
    service: TenantService = Depends(get_tenant_service),
) -> MessageResponse:
    """Remove the service account from the tenant: its keys here are revoked, its membership ends.

    The account is deactivated once it holds no other membership; what it wrote keeps its author.
    """
    step_up = body or ServiceAccountRemovalRequest()
    service.remove_service_account(
        service_account_key,
        tenant_key=ctx.tenant_key,
        requester=user,
        current_password=step_up.current_password,
        step_up_code=step_up.step_up_code,
        step_up_token=step_up.step_up_token,
        authenticated_with_api_key=via_api_key,
        client_ip=client_ip,
    )
    return MessageResponse(message="Service account removed")
