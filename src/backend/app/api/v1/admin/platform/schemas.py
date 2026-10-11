from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.api.v1.auth.schemas import CredentialStepUp
from app.api.v1.tenants.schemas import TenantEntitlementsResponse
from app.common.enums import TenantRole, TenantStatus, TenantType
from app.common.validators import DisplayName
from app.domain.models.plan import PLAN_KEY_PATTERN, PlanLimitChange, PlanLimits


class AdminTenantResponse(BaseModel):
    key: str
    name: str
    slug: str
    tenant_type: TenantType
    description: str | None
    owner_user_key: str
    #: Derived from ``status`` — kept for clients written before #2123.
    is_active: bool
    #: Lifecycle state (REQ-024 AK-65, #2123): ``orphaned`` marks an organisation an
    #: account erasure left without anybody who can administer it (#2134).
    status: TenantStatus = TenantStatus.ACTIVE
    #: When a ``pending_deletion`` / ``orphaned`` tenant is erased; ``None`` otherwise.
    deletion_scheduled_at: datetime | None = None
    is_platform: bool
    max_members: int
    member_count: int
    created_at: datetime | None
    updated_at: datetime | None
    #: REQ-056 §7.1 (#2142) — the plan whose quotas apply; assigned with ``PATCH .../tenants/{key}``.
    plan_key: str = "standard"


class AdminTenantDetailResponse(AdminTenantResponse):
    """One tenant for the platform admin, with its plan's limits and the usage of every dimension (#2142)."""

    entitlements: TenantEntitlementsResponse


class PlanLimitsRequest(PlanLimits):
    """The limits of a plan in a request body: as :class:`PlanLimits`, but an unknown dimension is 422.

    The stored read model ignores unknown fields (SEC-001: a plan document a newer build wrote must not
    fail every quota decision); a request naming a dimension that does not exist (``sensors``) is a client
    error and refused. **``0`` means unlimited** for ``storage_mb`` and ``photos_per_instance`` and
    **budget off** for the three KI budgets (REQ-056 §7.2).
    """

    model_config = ConfigDict(extra="forbid")


class PlanCreateRequest(BaseModel):
    """A new plan (REQ-056 §7.6). It is never created as the default; mark it with ``PATCH`` afterwards."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {"key": "community", "name": "Community garden", "limits": {"members": 30, "storage_mb": 5120}}
            ]
        },
    )

    key: str = Field(pattern=PLAN_KEY_PATTERN, description="Immutable key: a-z, 0-9, '_' or '-', 2-40 characters.")
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    #: A limit left out or ``null`` follows the instance setting (REQ-056 §7.2).
    limits: PlanLimitsRequest = Field(default_factory=PlanLimitsRequest)


class PlanUpdateRequest(BaseModel):
    """A partial change of a plan; only the fields sent change (inside ``limits`` too, ``null`` = instance setting)."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [{"limits": {"storage_mb": 10240}}, {"is_default": True}]},
    )

    name: str | None = Field(default=None, min_length=1, max_length=100, description="Omitted = unchanged; never null.")
    description: str | None = Field(default=None, max_length=500)
    limits: PlanLimitsRequest | None = None
    is_default: bool | None = Field(
        default=None, description="true makes this the one default plan of new tenants; false is refused."
    )

    @field_validator("name")
    @classmethod
    def _name_is_not_cleared(cls, value: str | None) -> str | None:
        """A plan always has a name: an explicit ``null`` is 422, not a 500 further down (review I-3)."""
        if value is None:
            raise ValueError("name cannot be null; omit it to keep the current name")
        return value


class PlanResponse(BaseModel):
    key: str
    name: str
    description: str | None
    limits: PlanLimits
    #: SEC-002 — the dimensions this plan sets to ``0``, which means **unlimited** (storage, photos) or
    #: **budget off** (KI), not "nothing allowed". Listed so a reader of the response cannot miss it.
    unlimited: list[str] = Field(
        default_factory=list,
        description="Dimensions set to 0 in this plan: 0 means UNLIMITED (storage, photos) or budget OFF (AI).",
    )
    is_default: bool
    #: How many tenants point at the plan.
    tenant_count: int
    created_at: datetime | None
    updated_at: datetime | None


class AdminUserTenantRole(BaseModel):
    tenant_key: str
    tenant_name: str
    tenant_slug: str
    role: TenantRole


class AdminUserResponse(BaseModel):
    key: str
    email: str
    display_name: str
    is_active: bool
    email_verified: bool
    last_login_at: datetime | None
    created_at: datetime | None
    tenant_count: int
    roles: list[AdminUserTenantRole]


class AdminStatsResponse(BaseModel):
    total_users: int
    active_users: int
    total_tenants: int
    active_tenants: int
    total_memberships: int


class AdminTenantUpdate(CredentialStepUp):
    """A partial platform-admin update of a tenant; the step-up fields are the *admin's* own (#2009).

    They are needed only when the update changes ``is_active`` — deactivating locks
    every member out — and are never written to the tenant.
    """

    name: str | None = None
    description: str | None = None
    max_members: int | None = Field(default=None, ge=1)
    is_active: bool | None = None
    #: REQ-056 §7.6 (#2142) — assign another plan (422 when unknown). No step-up; written to the audit.
    plan_key: str | None = Field(default=None, pattern=PLAN_KEY_PATTERN)

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"name": "Community garden"},
                {"plan_key": "community"},
                {"is_active": False, "current_password": "<the admin's own current password>"},
            ]
        },
    )


class AdminUserUpdate(CredentialStepUp):
    """A partial platform-admin update; the step-up fields are the *admin's* own (#1857).

    They are needed only when the update raises trust — ``email_verified`` or
    ``is_active`` turning true — and are never written to the user.
    """

    display_name: DisplayName | None = None
    is_active: bool | None = None
    email_verified: bool | None = None


class AdminTenantMemberResponse(BaseModel):
    membership_key: str
    user_key: str
    display_name: str
    email: str
    role: TenantRole
    is_active: bool
    joined_at: datetime | None


class AdminMembershipRemovalRequest(CredentialStepUp):
    """The body of a platform-admin membership removal: the *admin's* own step-up (#2009).

    ``current_password`` for an admin with a local password; for one without,
    ``step_up_token`` / ``step_up_code`` obtained for ``admin_membership_removal``
    with the membership's key as the target. Never written anywhere.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"current_password": "<the admin's own current password>"}, {"step_up_code": "48213907"}]
        },
    )


class AdminAddMemberRequest(CredentialStepUp):
    """The account to add and its role; the step-up fields are the *admin's* own (#2106).

    Adding an account to a tenant — the ``platform`` tenant with ``lead`` makes it a platform
    admin — passes the admin's step-up (REQ-024 AK-59): ``current_password`` for an admin with a
    local password; for one without, ``step_up_token`` / ``step_up_code`` obtained for
    ``admin_membership_add`` with ``<tenant_key>|<user_key>`` as the target. Never written anywhere.
    """

    user_key: str
    role: TenantRole = TenantRole.VIEWER

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"user_key": "u-4711", "role": "grower", "current_password": "<the admin's own current password>"},
                {"user_key": "u-4711", "role": "viewer", "step_up_code": "48213907"},
            ]
        },
    )


class AdminUpdateMemberRoleRequest(CredentialStepUp):
    """A member's new role; the step-up fields are the *admin's* own (#2032).

    Needed only when the role actually changes (REQ-024 AK-57) — a role re-sent unchanged
    needs none — and never written to the membership. ``current_password`` for an admin
    with a local password; for one without, ``step_up_token`` / ``step_up_code`` obtained
    for ``admin_membership_role_change`` with the membership's key.
    """

    role: TenantRole

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"role": "viewer", "current_password": "<the admin's own current password>"},
                {"role": "grower", "step_up_code": "48213907"},
            ]
        },
    )


class AdminUserMembershipResponse(BaseModel):
    membership_key: str
    tenant_key: str
    tenant_name: str
    tenant_slug: str
    role: TenantRole
    is_active: bool
    joined_at: datetime | None


class AdminAddUserToTenantRequest(CredentialStepUp):
    """The tenant to add the path's account to and its role; the step-up fields are the *admin's* own (#2106).

    The same step-up as :class:`AdminAddMemberRequest`, bound to ``<tenant_key>|<user_key>``.
    """

    # tenant-body-ok: the tenant is the OBJECT of this operation, not the
    # isolation container of the caller. `POST /admin/platform/users/{key}/
    # tenants` is a platform-admin endpoint (`Depends(require_platform_admin)`,
    # router.py) whose whole purpose is to grant a membership in a named
    # tenant; the handler loads that tenant and 404s when it does not exist.
    # There is no caller tenant to take it from — a platform admin operates
    # across all of them — so the body is the only place it can come from.
    tenant_key: str
    role: TenantRole = TenantRole.VIEWER

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"tenant_key": "t-17", "role": "grower", "current_password": "<the admin's own current password>"},
                {"tenant_key": "t-17", "role": "viewer", "step_up_code": "48213907"},
            ]
        },
    )


class SecurityAuditEntryResponse(BaseModel):
    """One row of the persistent security audit (MT-014, #2111, NFR-011 R-38)."""

    key: str | None = None
    action: str
    via: str
    actor_user_key: str
    #: ``None`` on a row about a whole tenant (suspension, deletion; #2111).
    target_user_key: str | None = None
    #: ``None`` on a row about an account's trust flags (``is_active``, ``email_verified``; #2111).
    tenant_key: str | None = None
    membership_key: str | None = None
    old_role: str | None = None
    new_role: str | None = None
    old_scopes: list[str] | None = None
    new_scopes: list[str] | None = None
    #: REQ-056 §7.6 (#2142) — plan rows: the plan concerned, the tenant's previous plan, the changed fields.
    plan_key: str | None = None
    old_plan_key: str | None = None
    changed_fields: list[str] | None = None
    #: SEC-005 — the old and new value of each changed limit, flagged when it lifts the limit.
    limit_changes: list[PlanLimitChange] | None = None
    #: #1855 SEC-005 — a take-over decision: whether it made the actor the first platform admin.
    platform_admin_granted: bool | None = None
    #: #1855 SEC-005 — a sealed light-mode system account: what the start revoked (counts only).
    revoked_counts: dict[str, int] | None = None
    request_id: str | None = None
    created_at: datetime | None = None
