from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.api.v1.auth.schemas import CredentialStepUp
from app.common.enums import (
    AdminScope,
    InvitationStatus,
    InvitationType,
    TenantRole,
    TenantStatus,
    TenantType,
)
from app.domain.models.tenant_erasure import (
    TenantDeletionConfirmation,
    TenantErasureCancelConfirmation,
    TenantErasureRecord,
    TenantErasureStatus,
)

# ── Tenant schemas ───────────────────────────────────────────────────


class TenantCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    #: REQ-024 AK-64 (#2133): at most ``TENANT_MAX_MEMBERS_CEILING`` (422 above it); omitted, the ceiling.
    max_members: int | None = Field(
        default=None,
        ge=1,
        description="Member limit, at most the platform ceiling (TENANT_MAX_MEMBERS_CEILING); omitted = the ceiling.",
    )


class TenantUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    #: Omitted = unchanged. At most the platform ceiling (REQ-024 AK-65, #2133); lowering it below the
    #: current member count removes nobody and stops the next join.
    max_members: int | None = Field(
        default=None,
        ge=1,
        description="New member limit, at most the platform ceiling (TENANT_MAX_MEMBERS_CEILING); omitted = unchanged.",
    )


class TenantDeleteRequest(BaseModel):
    """The step-up a tenant deletion must carry (#1791, REQ-024 §1a.2).

    Both deletion routes — ``DELETE /tenants/{slug}`` and
    ``DELETE /admin/platform/tenants/{key}`` — take this body.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {"confirm_slug": "gemeinschaftsgarten-lindenhof", "password": "<your current password>"},
                {"confirm_slug": "gemeinschaftsgarten-lindenhof", "step_up_code": "48213907"},
            ]
        },
    )

    confirm_slug: str = Field(
        min_length=1,
        max_length=200,
        description="The tenant's slug, typed back by the requester to confirm which tenant is erased.",
    )
    password: str | None = Field(
        default=None,
        max_length=1024,
        description=(
            "The requester's current password. Required when the account has a local password; "
            "an account that signs in only through a federated provider omits it and sends step_up_code."
        ),
    )
    step_up_code: str | None = Field(
        default=None,
        max_length=32,
        description=(
            "The one-time code mailed by POST /users/me/step-up-code. Required when the requester's account has "
            "no local password (federated sign-in only); 401 STEP_UP_CODE_REQUIRED without it."
        ),
    )
    step_up_token: str | None = Field(
        default=None,
        max_length=128,
        description=(
            "The one-time token of a fresh sign-in at the account's identity provider, from the fragment of "
            "/auth/step-up/callback after POST /users/me/step-up/oidc (#1815). Required instead of step_up_code "
            "when the account has no local password but a provider that can re-authenticate "
            "(401 STEP_UP_REAUTH_REQUIRED without it); valid five minutes, for one act, once."
        ),
    )

    def to_confirmation(self) -> TenantDeletionConfirmation:
        return TenantDeletionConfirmation(
            confirm_slug=self.confirm_slug,
            password=self.password,
            step_up_code=self.step_up_code,
            step_up_token=self.step_up_token,
        )


class TenantDeletionAcceptedResponse(BaseModel):
    """The ``202 Accepted`` body of both tenant-deletion routes (#1792, #2123, REQ-024 AK-52/53).

    **Scheduled since #2123 (breaking).** With a grace
    (``RETENTION_TENANT_ERASURE_GRACE_DAYS``, default 90) the deletion is
    *scheduled*: ``status`` is ``scheduled`` and ``scheduled_for`` says when the
    erasure runs; until then the tenant is closed for everybody
    (``pending_deletion``) and its management can cancel
    (``POST /tenants/{slug}/erasure/cancel``). With a grace of ``0`` the deletion is
    *recorded* and the tenant *frozen* (memberships deactivated) and a Celery task
    erases it: ``status`` is ``in_progress`` for a deletion just recorded and
    ``partially_completed`` for one an earlier run left open and this request
    re-dispatched. Never "deleted". Names no slug and no account.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "tenant_key": "4711",
                    "status": "scheduled",
                    "requested_at": "2026-10-02T10:00:00Z",
                    "scheduled_for": "2026-12-31T10:00:00Z",
                    "message": "Tenant deletion scheduled: the tenant is closed and is erased after the grace period.",
                }
            ]
        }
    )

    tenant_key: str
    status: TenantErasureStatus
    requested_at: datetime | None = None
    #: The end of the cancellable grace; ``None`` when the erasure runs at once.
    scheduled_for: datetime | None = None
    message: str = "Tenant deletion accepted: the tenant is frozen and its data is being erased."

    @classmethod
    def from_record(cls, record: TenantErasureRecord) -> TenantDeletionAcceptedResponse:
        if record.status == "scheduled":
            return cls(
                tenant_key=record.tenant_key,
                status=record.status,
                requested_at=record.requested_at,
                scheduled_for=record.scheduled_for,
                message="Tenant deletion scheduled: the tenant is closed and is erased after the grace period.",
            )
        return cls(tenant_key=record.tenant_key, status=record.status, requested_at=record.requested_at)


class TenantErasureCancelRequest(CredentialStepUp):
    """The step-up a cancellation of a scheduled tenant deletion carries (#2123, REQ-024 AK-52).

    The requester's own factor (``tenant_erasure_cancel``, bound to the tenant's key):
    ``current_password`` for an account with a local password, otherwise
    ``step_up_token`` / ``step_up_code``. No slug echo — cancelling destroys nothing.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [{"current_password": "<your current password>"}]},
    )

    def to_confirmation(self) -> TenantErasureCancelConfirmation:
        return TenantErasureCancelConfirmation(
            password=self.current_password, step_up_code=self.step_up_code, step_up_token=self.step_up_token
        )


class TenantResponse(BaseModel):
    key: str
    name: str
    slug: str
    tenant_type: TenantType
    description: str | None
    owner_user_key: str
    #: Derived from ``status`` (only ``active`` is active) — kept for clients written before #2123.
    is_active: bool
    #: Lifecycle state (REQ-024 AK-65, #2123).
    status: TenantStatus = TenantStatus.ACTIVE
    #: When a ``pending_deletion`` / ``orphaned`` tenant is erased; ``None`` otherwise.
    deletion_scheduled_at: datetime | None = None
    max_members: int
    created_at: datetime | None
    updated_at: datetime | None


class TenantWithRoleResponse(BaseModel):
    key: str
    name: str
    slug: str
    tenant_type: TenantType
    description: str | None
    role: TenantRole
    # REQ-049 axis 2 — what the caller may administer in this tenant. The UI
    # needs both axes to decide what to show; the rank alone no longer says.
    admin_scopes: list[AdminScope] = Field(default_factory=list)
    is_active: bool
    #: Lifecycle state (#2166). Always ``active`` in the default listing;
    #: ``pending_deletion`` / ``orphaned`` appear only with ``include_scheduled_deletion=true``.
    status: TenantStatus = TenantStatus.ACTIVE
    #: End of the cancellable grace of a scheduled deletion; ``None`` otherwise.
    deletion_scheduled_at: datetime | None = None


# ── Member schemas ───────────────────────────────────────────────────


class MemberInfoResponse(BaseModel):
    key: str
    user_key: str
    display_name: str
    email: str
    role: TenantRole
    admin_scopes: list[AdminScope] = Field(default_factory=list)
    is_active: bool
    joined_at: datetime | None


class ChangeRoleRequest(CredentialStepUp):
    """A member's new role; the step-up fields are the *acting administrator's* own (#2032).

    They are needed only when the role actually changes (REQ-024 AK-57) — a role re-sent
    unchanged needs none — and are never written to the membership. ``current_password``
    for an administrator with a local password; for one without, ``step_up_token`` /
    ``step_up_code`` obtained for ``tenant_member_role_change`` with the membership's key.
    """

    role: TenantRole

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"role": "viewer", "current_password": "<the acting administrator's own current password>"},
                {"role": "grower", "step_up_code": "48213907"},
            ]
        },
    )


class MemberRemovalRequest(CredentialStepUp):
    """The body of a member removal: the *acting administrator's* own step-up (#2032).

    ``current_password`` for an administrator with a local password; for one without,
    ``step_up_token`` / ``step_up_code`` obtained for ``tenant_member_removal`` with the
    membership's key as the target. Never written anywhere.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"current_password": "<the acting administrator's own current password>"},
                {"step_up_code": "48213907"},
            ]
        },
    )


class ChangeScopesRequest(BaseModel):
    admin_scopes: list[AdminScope] = Field(default_factory=list)


# ── Invitation schemas ───────────────────────────────────────────────


class EmailInvitationRequest(BaseModel):
    email: EmailStr
    role: TenantRole = TenantRole.VIEWER


class LinkInvitationRequest(BaseModel):
    role: TenantRole = TenantRole.VIEWER


class InvitationResponse(BaseModel):
    key: str
    tenant_key: str
    invitation_type: InvitationType
    email: str | None
    role: TenantRole
    status: InvitationStatus
    expires_at: datetime
    created_at: datetime | None


class InvitationLinkResponse(BaseModel):
    invitation_key: str
    token: str
    expires_at: datetime
    #: The accept page's link with the token (#2162): what the inviter copies and shares.
    accept_url: str
    #: E-mail invitations: whether the invitation mail left (#2162). ``false`` - the invitation
    #: exists but reached nobody; the inviter passes ``accept_url`` on. ``null`` for a link invitation.
    delivered: bool | None = None


class AcceptInvitationRequest(BaseModel):
    token: str


# ── Assignment schemas ───────────────────────────────────────────────


class AssignmentCreateRequest(BaseModel):
    membership_key: str
    location_key: str
    can_edit: bool = True
    notes: str | None = None


class AssignmentUpdateRequest(BaseModel):
    can_edit: bool | None = None
    notes: str | None = None


class AssignmentResponse(BaseModel):
    key: str
    membership_key: str
    location_key: str
    tenant_key: str
    can_edit: bool
    notes: str | None
    created_at: datetime | None
    updated_at: datetime | None


class MessageResponse(BaseModel):
    message: str
