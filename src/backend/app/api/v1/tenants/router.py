from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path

from app.api.v1.tenants.schemas import (
    AcceptInvitationRequest,
    AssignmentCreateRequest,
    AssignmentResponse,
    AssignmentUpdateRequest,
    ChangeRoleRequest,
    EmailInvitationRequest,
    InvitationLinkResponse,
    InvitationResponse,
    LinkInvitationRequest,
    MemberInfoResponse,
    MemberRemovalRequest,
    MessageResponse,
    TenantCreateRequest,
    TenantDeleteRequest,
    TenantDeletionAcceptedResponse,
    TenantErasureCancelRequest,
    TenantResponse,
    TenantUpdateRequest,
    TenantWithRoleResponse,
)
from app.common.auth import (
    get_authenticated_with_api_key,
    get_current_tenant,
    get_current_user,
    refuse_in_light_mode,
    require_account_principal,
    require_admin_scope,
)
from app.common.dependencies import get_tenant_service
from app.common.enums import AdminScope
from app.common.openapi_responses import AUTH_CRUD_RESPONSES, STEP_UP_RESPONSES
from app.common.pagination import PaginationParams, get_pagination
from app.common.request_ip import resolve_client_ip
from app.domain.models.auth import api_key_scope_admits
from app.domain.models.tenant import Tenant
from app.domain.models.tenant_context import TenantContext
from app.domain.models.user import User
from app.domain.services.tenant_service import TenantService

router = APIRouter(prefix="/tenants", tags=["tenants"], responses=AUTH_CRUD_RESPONSES)


def _tenant_response(t: Tenant) -> TenantResponse:
    return TenantResponse(
        key=t.key or "",
        name=t.name,
        slug=t.slug,
        tenant_type=t.tenant_type,
        description=t.description,
        owner_user_key=t.owner_user_key,
        is_active=t.is_active,
        status=t.status,
        deletion_scheduled_at=t.deletion_scheduled_at,
        max_members=t.max_members,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


# ── Tenant CRUD ──────────────────────────────────────────────────────


@router.get("", response_model=list[TenantWithRoleResponse])
def list_my_tenants(
    user: User = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
):
    """List all tenants the current user is a member of.

    A tenant-scoped API key sees only the tenant it is restricted to (#1851):
    the list is the account's, and the key must not learn the owner's other
    tenants. Admitted rather than refused because the Home Assistant
    integration reads it to find its tenant.
    """
    scope = user.api_key_tenant_scope
    items = [t for t in service.list_my_tenants(user.key) if api_key_scope_admits(scope, tenant_key=t.key)]
    return [TenantWithRoleResponse(**t.model_dump()) for t in items]


@router.post("", response_model=TenantResponse, status_code=201)
def create_organization(
    body: TenantCreateRequest,
    user: User = Depends(require_account_principal),
    service: TenantService = Depends(get_tenant_service),
):
    """Create a new organization tenant.

    A service account is refused (403, #2137): it founds no tenant.
    """
    tenant = service.create_organization(
        founder=user,
        name=body.name,
        description=body.description,
        max_members=body.max_members,
    )
    return _tenant_response(tenant)


@router.get("/{tenant_slug}", response_model=TenantResponse)
def get_tenant(
    ctx: TenantContext = Depends(get_current_tenant),
    service: TenantService = Depends(get_tenant_service),
):
    """Get tenant details."""
    tenant = service.get_tenant(ctx.tenant_key)
    return _tenant_response(tenant)


@router.patch("/{tenant_slug}", response_model=TenantResponse)
def update_tenant(
    body: TenantUpdateRequest,
    ctx: TenantContext = Depends(require_admin_scope(AdminScope.MANAGEMENT)),
    service: TenantService = Depends(get_tenant_service),
):
    """Update tenant. Admin only."""
    data = body.model_dump(exclude_none=True)
    tenant = service.update_tenant(ctx.tenant_key, data)
    return _tenant_response(tenant)


@router.delete(
    "/{tenant_slug}",
    status_code=202,
    response_model=TenantDeletionAcceptedResponse,
    responses=STEP_UP_RESPONSES,
)
def delete_tenant(
    body: TenantDeleteRequest,
    ctx: TenantContext = Depends(require_admin_scope(AdminScope.MANAGEMENT)),
    user: User = Depends(get_current_user),
    via_api_key: bool = Depends(get_authenticated_with_api_key),
    client_ip: str | None = Depends(resolve_client_ip),
    service: TenantService = Depends(get_tenant_service),
):
    """Accept the deletion of the tenant and all its data (declared tenant-erasure inventory, #1769).

    **Scheduled since #2123 (breaking, REQ-024 AK-52).** With a grace
    (``RETENTION_TENANT_ERASURE_GRACE_DAYS``, default 90 days) nothing is erased and no
    membership is touched: the tenant becomes ``pending_deletion`` — closed for every
    member, API key and MCP client like a suspended one (#2105) — its members are mailed
    the date (Art. 20 export window), and the body says ``scheduled`` with
    ``scheduled_for``. ``POST /tenants/{slug}/erasure/cancel`` withdraws it until then;
    the daily ``resume_tenant_erasures`` beat erases it afterwards. A grace of ``0``
    keeps the contract below.

    **Asynchronous since #1792 (breaking: ``200`` -> ``202``).** The request
    authorises, records the deletion and freezes the tenant (every membership is
    deactivated), then answers ``202 Accepted``; a Celery task runs the external
    phase and the ArangoDB inventory in bounded batches with a claim heartbeat.
    Nothing is erased when the response arrives — the tenant is gone once the
    record says ``completed``. A failed run is retried by the daily beat and
    escalates after repeated failures; the caller no longer sees it as a 5xx.

    **Lead role and management scope, plus a step-up (#1791).** The management
    scope gate here is the first filter; ``TenantService.delete_tenant`` decides —
    from the stored membership — that the requester holds the lead role *and*
    ``management`` (403 otherwise; a service account never), that ``confirm_slug``
    is this tenant's slug (422) and, for an account with a local password, that
    ``password`` is its current one (401) — for an account without one, that
    ``step_up_code`` is the code from ``POST /users/me/step-up-code`` (401
    ``STEP_UP_CODE_REQUIRED`` without it, #1815) — throttled per account and
    address, 429 ``STEP_UP_LOCKED`` after too many failures (#1816).

    Same path as ``DELETE /admin/platform/tenants/{key}``: 403 for the platform
    tenant, 409 while another deletion runs, 503 when the deployment cannot erase
    (nothing changed). The 502 (external store) and 500 ``TENANT_ERASURE_INCOMPLETE``
    answers of the synchronous contract no longer reach the caller: they happen in
    the worker and are recorded and retried there.
    """
    record = service.delete_tenant(
        ctx.tenant_key,
        requester=user,
        authenticated_with_api_key=via_api_key,
        confirmation=body.to_confirmation(),
        origin="tenant_management",
        client_ip=client_ip,
    )
    return TenantDeletionAcceptedResponse.from_record(record)


@router.post(
    "/{tenant_slug}/erasure/cancel",
    response_model=TenantResponse,
    responses=STEP_UP_RESPONSES,
)
def cancel_tenant_erasure(
    body: TenantErasureCancelRequest,
    tenant_slug: str = Path(description="URL slug of the tenant whose scheduled deletion is cancelled."),
    user: User = Depends(require_account_principal),
    via_api_key: bool = Depends(get_authenticated_with_api_key),
    client_ip: str | None = Depends(resolve_client_ip),
    service: TenantService = Depends(get_tenant_service),
):
    """Cancel the scheduled deletion of a tenant inside its grace (#2123, REQ-024 AK-52).

    **Not behind** :func:`~app.common.auth.get_current_tenant`: a ``pending_deletion``
    tenant resolves for nobody (#2105), so the slug is resolved by the service, which
    then requires — from the stored membership — the lead role **and** the
    ``management`` scope (the rule of the deletion itself), never an API key, plus the
    requester's own step-up (``tenant_erasure_cancel``, bound to the tenant's key).
    An unknown slug and a tenant the caller may not administer are one answer (403).

    422 when nothing is scheduled any more (the grace has ended and the erasure runs —
    ``deleted`` — or the tenant is not pending); 401/429 for the step-up. On success
    the tenant is ``active`` again with every membership as it was.
    """
    tenant = service.cancel_tenant_erasure_by_slug(
        tenant_slug,
        requester=user,
        authenticated_with_api_key=via_api_key,
        confirmation=body.to_confirmation(),
        origin="tenant_management",
        client_ip=client_ip,
    )
    return _tenant_response(tenant)


# ── Members ──────────────────────────────────────────────────────────


@router.get("/{tenant_slug}/members", response_model=list[MemberInfoResponse])
def list_members(
    ctx: TenantContext = Depends(get_current_tenant),
    service: TenantService = Depends(get_tenant_service),
):
    """List all members of a tenant."""
    members = service.list_members(ctx.tenant_key)
    return [MemberInfoResponse(**m.model_dump()) for m in members]


@router.patch(
    "/{tenant_slug}/members/{membership_key}/role",
    response_model=MessageResponse,
    responses=STEP_UP_RESPONSES,
)
def change_member_role(
    membership_key: Annotated[str, Path(description="Document key of the membership.")],
    body: ChangeRoleRequest,
    ctx: TenantContext = Depends(require_admin_scope(AdminScope.MANAGEMENT)),
    user: User = Depends(get_current_user),
    via_api_key: bool = Depends(get_authenticated_with_api_key),
    client_ip: str | None = Depends(resolve_client_ip),
    service: TenantService = Depends(get_tenant_service),
):
    """Change a member's role. Admin only.

    **Step-up (#2032, REQ-024 AK-57):** an actual change of the role — a member demoted or
    promoted — passes the acting administrator's own step-up: the body carries
    ``current_password`` (or ``step_up_token`` / ``step_up_code`` obtained for
    ``tenant_member_role_change`` with the membership's key); 401 without it, 403 from an
    API-key request, 429 ``STEP_UP_LOCKED``; nothing is written then. A role re-sent
    unchanged needs none. The step-up fields are never written.

    **Escalation (#2078, REQ-024 AK-58):** 403 when a member raises their *own* role, and
    when anyone but a platform admin grants ``lead`` in the ``platform`` tenant (there it is the
    platform role) — checked before the step-up, nothing written. The invitation routes apply
    the same rule to the role they hand out.
    """
    service.change_member_role(
        ctx.tenant_key,
        membership_key,
        body.role,
        ctx.admin_scopes,
        actor_user_key=ctx.user_key,
        requester=user,
        current_password=body.current_password,
        step_up_code=body.step_up_code,
        step_up_token=body.step_up_token,
        authenticated_with_api_key=via_api_key,
        client_ip=client_ip,
    )
    return MessageResponse(message="Role updated")


@router.delete(
    "/{tenant_slug}/members/{membership_key}",
    response_model=MessageResponse,
    responses=STEP_UP_RESPONSES,
)
def remove_member(
    membership_key: Annotated[str, Path(description="Document key of the membership.")],
    body: Annotated[MemberRemovalRequest | None, Body()] = None,
    ctx: TenantContext = Depends(require_admin_scope(AdminScope.MANAGEMENT)),
    user: User = Depends(get_current_user),
    via_api_key: bool = Depends(get_authenticated_with_api_key),
    client_ip: str | None = Depends(resolve_client_ip),
    service: TenantService = Depends(get_tenant_service),
):
    """Remove a member from tenant. Admin only.

    **Step-up (#2032, REQ-024 AK-57):** removing a member — also the tenant's last ``lead`` —
    passes the acting administrator's own step-up: the body carries ``current_password`` (or
    ``step_up_token`` / ``step_up_code`` obtained for ``tenant_member_removal`` with the
    membership's key); 401 without it — also without a body —, 403 from an API-key request,
    429 ``STEP_UP_LOCKED``; the membership stays then. The last ``management`` holder is
    refused first (422, INV-1).
    """
    step_up = body or MemberRemovalRequest()
    service.remove_member(
        ctx.tenant_key,
        membership_key,
        ctx.admin_scopes,
        requester=user,
        current_password=step_up.current_password,
        step_up_code=step_up.step_up_code,
        step_up_token=step_up.step_up_token,
        authenticated_with_api_key=via_api_key,
        client_ip=client_ip,
    )
    return MessageResponse(message="Member removed")


@router.post("/{tenant_slug}/leave", response_model=MessageResponse)
def leave_tenant(
    ctx: TenantContext = Depends(get_current_tenant),
    service: TenantService = Depends(get_tenant_service),
):
    """Leave a tenant."""
    service.leave_tenant(ctx.tenant_key, ctx.user_key)
    return MessageResponse(message="Left tenant")


# ── Invitations ──────────────────────────────────────────────────────


@router.get(
    "/{tenant_slug}/invitations",
    response_model=list[InvitationResponse],
)
def list_invitations(
    pagination: PaginationParams = Depends(get_pagination),
    ctx: TenantContext = Depends(require_admin_scope(AdminScope.MANAGEMENT)),
    service: TenantService = Depends(get_tenant_service),
):
    """List a tenant's invitations, newest first (paginated, MT-035). Admin only."""
    invitations = service.list_invitations(ctx.tenant_key, offset=pagination.offset, limit=pagination.limit)
    return [
        InvitationResponse(
            key=inv.key or "",
            tenant_key=inv.tenant_key,
            invitation_type=inv.invitation_type,
            email=inv.email,
            role=inv.role,
            status=inv.status,
            expires_at=inv.expires_at,
            created_at=inv.created_at,
        )
        for inv in invitations
    ]


@router.post(
    "/{tenant_slug}/invitations/email",
    response_model=InvitationLinkResponse,
    status_code=201,
    # #1844: a light-mode caller is the unauthenticated system account, which is the
    # light tenant's lead; a token issued here would outlive the mode and admit
    # whoever asked for it once the instance runs in full mode.
    dependencies=[Depends(refuse_in_light_mode)],
)
def create_email_invitation(
    body: EmailInvitationRequest,
    ctx: TenantContext = Depends(require_admin_scope(AdminScope.MANAGEMENT)),
    service: TenantService = Depends(get_tenant_service),
):
    """Create an email invitation and mail its accept link to the address. Admin only.

    **Delivery is reported, not assumed (#2162).** The invitation is stored first; ``delivered`` says
    whether the mail left. ``false`` (no mail adapter that delivers, the console adapter outside
    debug, a refusing or unreachable mail service) still answers 201: the invitation exists and
    ``accept_url`` is what the inviter passes on themselves - only the invited, proven address can
    accept it (#2115).
    """
    link = service.create_email_invitation(
        tenant_key=ctx.tenant_key,
        invited_by_user_key=ctx.user_key,
        email=body.email,
        role=body.role,
    )
    return InvitationLinkResponse(
        invitation_key=link.invitation_key,
        token=link.token,
        expires_at=link.expires_at,
        accept_url=link.accept_url,
        delivered=link.delivered,
    )


@router.post(
    "/{tenant_slug}/invitations/link",
    response_model=InvitationLinkResponse,
    status_code=201,
    # #1844: a light-mode caller is the unauthenticated system account, which is the
    # light tenant's lead; a token issued here would outlive the mode and admit
    # whoever asked for it once the instance runs in full mode.
    dependencies=[Depends(refuse_in_light_mode)],
)
def create_link_invitation(
    body: LinkInvitationRequest,
    ctx: TenantContext = Depends(require_admin_scope(AdminScope.MANAGEMENT)),
    service: TenantService = Depends(get_tenant_service),
):
    """Create a shareable invitation link. Admin only."""
    link = service.create_link_invitation(
        tenant_key=ctx.tenant_key,
        invited_by_user_key=ctx.user_key,
        role=body.role,
    )
    return InvitationLinkResponse(
        invitation_key=link.invitation_key,
        token=link.token,
        expires_at=link.expires_at,
        accept_url=link.accept_url,
        delivered=link.delivered,
    )


@router.delete(
    "/{tenant_slug}/invitations/{invitation_key}",
    response_model=MessageResponse,
)
def revoke_invitation(
    invitation_key: Annotated[str, Path(description="Document key of the invitation.")],
    ctx: TenantContext = Depends(require_admin_scope(AdminScope.MANAGEMENT)),
    service: TenantService = Depends(get_tenant_service),
):
    """Revoke an invitation. Admin only."""
    service.revoke_invitation(ctx.tenant_key, invitation_key)
    return MessageResponse(message="Invitation revoked")


@router.post("/invitations/accept", response_model=MessageResponse)
def accept_invitation(
    body: AcceptInvitationRequest,
    user: User = Depends(require_account_principal),
    service: TenantService = Depends(get_tenant_service),
):
    """Accept an invitation using its token.

    **An e-mail invitation is bound to its address (#2115, REQ-024 AK-61):** 403 unless the signed-in
    account carries the invited address and has confirmed it; the invitation then stays pending and nothing
    is written. A link invitation is open to any signed-in account. A service account is refused (403,
    #2137): it is placed in its tenant by that tenant's lead, never by an invitation.
    """
    service.accept_invitation(body.token, user)
    return MessageResponse(message="Invitation accepted")


# ── Location Assignments ─────────────────────────────────────────────


@router.get(
    "/{tenant_slug}/assignments",
    response_model=list[AssignmentResponse],
)
def list_assignments(
    ctx: TenantContext = Depends(get_current_tenant),
    service: TenantService = Depends(get_tenant_service),
):
    """List all location assignments in a tenant."""
    assignments = service.list_assignments(ctx.tenant_key)
    return [
        AssignmentResponse(
            key=a.key or "",
            membership_key=a.membership_key,
            location_key=a.location_key,
            tenant_key=a.tenant_key,
            can_edit=a.can_edit,
            notes=a.notes,
            created_at=a.created_at,
            updated_at=a.updated_at,
        )
        for a in assignments
    ]


@router.post(
    "/{tenant_slug}/assignments",
    response_model=AssignmentResponse,
    status_code=201,
)
def create_assignment(
    body: AssignmentCreateRequest,
    ctx: TenantContext = Depends(require_admin_scope(AdminScope.MANAGEMENT)),
    service: TenantService = Depends(get_tenant_service),
):
    """Create a location assignment. Admin only."""
    assignment = service.create_assignment(
        tenant_key=ctx.tenant_key,
        membership_key=body.membership_key,
        location_key=body.location_key,
        can_edit=body.can_edit,
        notes=body.notes,
    )
    return AssignmentResponse(
        key=assignment.key or "",
        membership_key=assignment.membership_key,
        location_key=assignment.location_key,
        tenant_key=assignment.tenant_key,
        can_edit=assignment.can_edit,
        notes=assignment.notes,
        created_at=assignment.created_at,
        updated_at=assignment.updated_at,
    )


@router.patch(
    "/{tenant_slug}/assignments/{assignment_key}",
    response_model=AssignmentResponse,
)
def update_assignment(
    assignment_key: Annotated[str, Path(description="Document key of the location assignment.")],
    body: AssignmentUpdateRequest,
    ctx: TenantContext = Depends(require_admin_scope(AdminScope.MANAGEMENT)),
    service: TenantService = Depends(get_tenant_service),
):
    """Update a location assignment. Admin only."""
    data = body.model_dump(exclude_none=True)
    assignment = service.update_assignment(ctx.tenant_key, assignment_key, data)
    return AssignmentResponse(
        key=assignment.key or "",
        membership_key=assignment.membership_key,
        location_key=assignment.location_key,
        tenant_key=assignment.tenant_key,
        can_edit=assignment.can_edit,
        notes=assignment.notes,
        created_at=assignment.created_at,
        updated_at=assignment.updated_at,
    )


@router.delete(
    "/{tenant_slug}/assignments/{assignment_key}",
    response_model=MessageResponse,
)
def delete_assignment(
    assignment_key: Annotated[str, Path(description="Document key of the location assignment.")],
    ctx: TenantContext = Depends(require_admin_scope(AdminScope.MANAGEMENT)),
    service: TenantService = Depends(get_tenant_service),
):
    """Delete a location assignment. Admin only."""
    service.delete_assignment(ctx.tenant_key, assignment_key)
    return MessageResponse(message="Assignment deleted")
