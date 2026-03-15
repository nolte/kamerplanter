from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends

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
    MessageResponse,
    TenantCreateRequest,
    TenantResponse,
    TenantUpdateRequest,
    TenantWithRoleResponse,
)
from app.common.auth import get_current_tenant, get_current_user, require_tenant_role
from app.common.dependencies import get_tenant_service
from app.common.enums import TenantRole

if TYPE_CHECKING:
    from app.domain.models.tenant import Tenant
    from app.domain.models.tenant_context import TenantContext
    from app.domain.models.user import User
    from app.domain.services.tenant_service import TenantService

router = APIRouter(prefix="/tenants", tags=["tenants"])


def _tenant_response(t: Tenant) -> TenantResponse:
    return TenantResponse(
        key=t.key or "",
        name=t.name,
        slug=t.slug,
        tenant_type=t.tenant_type,
        description=t.description,
        owner_user_key=t.owner_user_key,
        is_active=t.is_active,
        max_members=t.max_members,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


# ── Tenant CRUD ──────────────────────────────────────────────────────


@router.get("/", response_model=list[TenantWithRoleResponse])
def list_my_tenants(
    user: User = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
):
    """List all tenants the current user is a member of."""
    items = service.list_my_tenants(user.key)
    return [TenantWithRoleResponse(**t.model_dump()) for t in items]


@router.post("/", response_model=TenantResponse, status_code=201)
def create_organization(
    body: TenantCreateRequest,
    user: User = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
):
    """Create a new organization tenant."""
    tenant = service.create_organization(
        user_key=user.key,
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
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.ADMIN)),
    service: TenantService = Depends(get_tenant_service),
):
    """Update tenant. Admin only."""
    data = body.model_dump(exclude_none=True)
    tenant = service.update_tenant(ctx.tenant_key, data)
    return _tenant_response(tenant)


@router.delete("/{tenant_slug}", response_model=MessageResponse)
def delete_tenant(
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.ADMIN)),
    service: TenantService = Depends(get_tenant_service),
):
    """Delete tenant and all associated data. Admin only."""
    service.delete_tenant(ctx.tenant_key)
    return MessageResponse(message="Tenant deleted")


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
)
def change_member_role(
    membership_key: str,
    body: ChangeRoleRequest,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.ADMIN)),
    service: TenantService = Depends(get_tenant_service),
):
    """Change a member's role. Admin only."""
    service.change_member_role(ctx.tenant_key, membership_key, body.role, ctx.role)
    return MessageResponse(message="Role updated")


@router.delete(
    "/{tenant_slug}/members/{membership_key}",
    response_model=MessageResponse,
)
def remove_member(
    membership_key: str,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.ADMIN)),
    service: TenantService = Depends(get_tenant_service),
):
    """Remove a member from tenant. Admin only."""
    service.remove_member(ctx.tenant_key, membership_key, ctx.role)
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
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.ADMIN)),
    service: TenantService = Depends(get_tenant_service),
):
    """List all invitations for a tenant. Admin only."""
    invitations = service.list_invitations(ctx.tenant_key)
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
)
def create_email_invitation(
    body: EmailInvitationRequest,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.ADMIN)),
    service: TenantService = Depends(get_tenant_service),
):
    """Create an email invitation. Admin only."""
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
    )


@router.post(
    "/{tenant_slug}/invitations/link",
    response_model=InvitationLinkResponse,
    status_code=201,
)
def create_link_invitation(
    body: LinkInvitationRequest,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.ADMIN)),
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
    )


@router.delete(
    "/{tenant_slug}/invitations/{invitation_key}",
    response_model=MessageResponse,
)
def revoke_invitation(
    invitation_key: str,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.ADMIN)),
    service: TenantService = Depends(get_tenant_service),
):
    """Revoke an invitation. Admin only."""
    service.revoke_invitation(ctx.tenant_key, invitation_key)
    return MessageResponse(message="Invitation revoked")


@router.post("/invitations/accept", response_model=MessageResponse)
def accept_invitation(
    body: AcceptInvitationRequest,
    user: User = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
):
    """Accept an invitation using its token."""
    service.accept_invitation(body.token, user.key)
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
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.ADMIN)),
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
    assignment_key: str,
    body: AssignmentUpdateRequest,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.ADMIN)),
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
    assignment_key: str,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.ADMIN)),
    service: TenantService = Depends(get_tenant_service),
):
    """Delete a location assignment. Admin only."""
    service.delete_assignment(ctx.tenant_key, assignment_key)
    return MessageResponse(message="Assignment deleted")
