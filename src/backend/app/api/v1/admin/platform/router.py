from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query

from app.api.v1.admin.platform.schemas import (
    AdminAddMemberRequest,
    AdminAddUserToTenantRequest,
    AdminMembershipRemovalRequest,
    AdminStatsResponse,
    AdminTenantMemberResponse,
    AdminTenantResponse,
    AdminTenantUpdate,
    AdminUpdateMemberRoleRequest,
    AdminUserMembershipResponse,
    AdminUserResponse,
    AdminUserTenantRole,
    AdminUserUpdate,
    SecurityAuditEntryResponse,
)
from app.api.v1.auth.schemas import CREDENTIAL_STEP_UP_FIELDS
from app.api.v1.privacy.schemas import (
    AccountDeletionAcceptedResponse,
    ErasureCreateRequest,
    ErasurePreviewResponse,
    ErasureResponse,
    PersonalTenantErasurePreviewItem,
)
from app.api.v1.tenants.schemas import TenantDeleteRequest, TenantDeletionAcceptedResponse
from app.common.auth import get_authenticated_with_api_key, require_platform_admin
from app.common.dependencies import (
    get_privacy_service,
    get_security_audit_service,
    get_tenant_service,
    get_user_service,
)
from app.common.openapi_responses import AUTH_CRUD_RESPONSES, STEP_UP_RESPONSES
from app.common.request_ip import resolve_client_ip
from app.domain.models.user import User
from app.domain.services.privacy_service import PrivacyService
from app.domain.services.security_audit_service import MAX_READ_LIMIT, SecurityAuditService
from app.domain.services.tenant_service import TenantService
from app.domain.services.user_service import UserService

router = APIRouter(prefix="/admin/platform", tags=["admin-platform"], responses=AUTH_CRUD_RESPONSES)


@router.get("/stats", response_model=AdminStatsResponse)
def get_platform_stats(
    _user: User = Depends(require_platform_admin),
    user_service: UserService = Depends(get_user_service),
    tenant_service: TenantService = Depends(get_tenant_service),
):
    """Get platform-wide statistics. Platform admin only.

    Routes the five counts through the service layer (#1019). This endpoint used
    to call ``get_db()`` and run ``collection.count()`` + ``COLLECT WITH COUNT``
    AQL from the router itself — Presentation straight onto Persistence
    (NFR-001).
    """
    return AdminStatsResponse(
        total_users=user_service.count_users(),
        active_users=user_service.count_users(active_only=True),
        total_tenants=tenant_service.count_tenants(),
        active_tenants=tenant_service.count_tenants(active_only=True),
        total_memberships=tenant_service.count_memberships(),
    )


@router.get("/security-audit", response_model=list[SecurityAuditEntryResponse])
def list_security_audit(
    tenant_key: Annotated[str | None, Query(description="Only the rows of this tenant (document key).")] = None,
    limit: Annotated[int, Query(ge=1, le=MAX_READ_LIMIT, description="Newest rows first, at most this many.")] = 100,
    _user: User = Depends(require_platform_admin),
    audit: SecurityAuditService = Depends(get_security_audit_service),
) -> list[SecurityAuditEntryResponse]:
    """The persistent security audit of membership, role and scope changes. Platform admin only.

    MT-014 (#2111): newest first, optionally of one tenant. Read-only; the rows are written
    by the services that change a membership and kept for two years (NFR-011 R-38).
    """
    return [
        SecurityAuditEntryResponse.model_validate(entry.model_dump(mode="json"))
        for entry in audit.list_recent(tenant_key=tenant_key, limit=limit)
    ]


@router.get("/tenants", response_model=list[AdminTenantResponse])
def list_all_tenants(
    _user: User = Depends(require_platform_admin),
    tenant_service: TenantService = Depends(get_tenant_service),
):
    """List all tenants with member counts. Platform admin only.

    Routes through ``TenantService.list_all_tenants`` (#1019). The per-tenant
    active-member count is derived from ``list_members``, the same way
    ``update_tenant`` already does it — the router no longer hand-writes the
    tenant/member-count AQL.
    """
    results: list[AdminTenantResponse] = []
    for tenant in tenant_service.list_all_tenants():
        tenant_key = tenant.key or ""
        member_count = sum(1 for member in tenant_service.list_members(tenant_key) if member.is_active)
        results.append(
            AdminTenantResponse(
                key=tenant_key,
                name=tenant.name,
                slug=tenant.slug,
                tenant_type=tenant.tenant_type,
                description=tenant.description,
                owner_user_key=tenant.owner_user_key,
                is_active=tenant.is_active,
                is_platform=tenant.is_platform,
                max_members=tenant.max_members,
                member_count=member_count,
                created_at=tenant.created_at,
                updated_at=tenant.updated_at,
            )
        )
    return results


@router.get("/users", response_model=list[AdminUserResponse])
def list_all_users(
    _user: User = Depends(require_platform_admin),
    user_service: UserService = Depends(get_user_service),
    tenant_service: TenantService = Depends(get_tenant_service),
):
    """List all users with their tenant memberships. Platform admin only.

    Routes through ``UserService.list_all_users`` for the user read and
    ``TenantService.list_user_memberships`` for each user's tenant roles (#1019).
    Both replace raw AQL the router used to run itself; the membership join now
    lives once in the data-access layer.
    """
    results: list[AdminUserResponse] = []
    for user in user_service.list_all_users():
        user_key = user.key or ""
        active = [m for m in tenant_service.list_user_memberships(user_key) if m.is_active]
        roles = [
            AdminUserTenantRole(
                tenant_key=m.tenant_key,
                tenant_name=m.tenant_name,
                tenant_slug=m.tenant_slug,
                role=m.role,
            )
            for m in active
        ]
        results.append(
            AdminUserResponse(
                key=user_key,
                email=user.email,
                display_name=user.display_name,
                is_active=user.is_active,
                email_verified=user.email_verified,
                last_login_at=user.last_login_at,
                created_at=user.created_at,
                tenant_count=len(roles),
                roles=roles,
            )
        )
    return results


@router.patch("/tenants/{key}", response_model=AdminTenantResponse, responses=STEP_UP_RESPONSES)
def update_tenant(
    key: Annotated[str, Path(description="Document key of the tenant.")],
    body: AdminTenantUpdate,
    admin: User = Depends(require_platform_admin),
    via_api_key: bool = Depends(get_authenticated_with_api_key),
    client_ip: str | None = Depends(resolve_client_ip),
    tenant_service: TenantService = Depends(get_tenant_service),
):
    """Update a tenant. Platform admin only.

    Routes through ``TenantService.update_tenant`` (#997). This endpoint used to
    call ``get_db()`` and write to ``db.collection(TENANTS)`` from here, which
    put the Presentation layer straight onto Persistence (NFR-001) and — the
    part that actually bit — outside every guard the repository layer applies:
    the #968/#982/#996 model re-validation, the reserved-attribute strip, the
    error-code-1202 → :class:`NotFoundError` mapping, and ``updated_at``
    maintenance. Each invariant added to the repositories since simply did not
    reach this path, and nothing signalled that.

    Two consequences of the move, both intended:

    * ``AdminTenantUpdate.name`` is a bare ``str | None`` where the
      tenant-scoped ``TenantUpdateRequest`` carries ``min_length``/
      ``max_length``. Names the domain forbids (empty, blank, one character,
      over 200 characters) were persisted verbatim; they are now rejected by
      ``TenantEngine.validate_tenant_name`` and the ``Tenant`` model, 422.
    * A rename now **re-derives the slug**, exactly as ``PATCH /t/{slug}``
      already does, so an admin rename can no longer leave a slug contradicting
      the tenant's name. The new slug is returned in the response.

    ``is_active`` is the one field the tenant-scoped request schema does not
    carry; the closed ``AdminTenantUpdate`` schema keeps ``owner_user_key``,
    ``is_platform``, ``tenant_type``, ``slug`` and ``settings`` out of it.

    **Step-up (#2009, REQ-024 AK-56):** any *change* of ``is_active`` —
    deactivating locks every member out — passes the admin's own step-up —
    ``current_password`` (or ``step_up_token`` / ``step_up_code`` obtained for
    ``admin_tenant_update`` with the tenant's key, for an admin without one); 401
    without it, 403 from an API-key request, 429 ``STEP_UP_LOCKED``; nothing is
    written then. Decided in ``TenantService.admin_update_tenant``. The step-up
    fields are never written.
    """
    update_data = body.model_dump(exclude_none=True, exclude=set(CREDENTIAL_STEP_UP_FIELDS))
    tenant = (
        tenant_service.admin_update_tenant(
            key,
            update_data,
            requester=admin,
            current_password=body.current_password,
            step_up_code=body.step_up_code,
            step_up_token=body.step_up_token,
            authenticated_with_api_key=via_api_key,
            client_ip=client_ip,
        )
        if update_data
        else tenant_service.get_tenant(key)
    )

    member_count = sum(1 for member in tenant_service.list_members(key) if member.is_active)

    return AdminTenantResponse(
        key=tenant.key or key,
        name=tenant.name,
        slug=tenant.slug,
        tenant_type=tenant.tenant_type,
        description=tenant.description,
        owner_user_key=tenant.owner_user_key,
        is_active=tenant.is_active,
        is_platform=tenant.is_platform,
        max_members=tenant.max_members,
        member_count=member_count,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
    )


@router.patch("/users/{key}", response_model=AdminUserResponse, responses=STEP_UP_RESPONSES)
def update_user(
    key: Annotated[str, Path(description="Document key of the user.")],
    body: AdminUserUpdate,
    admin: User = Depends(require_platform_admin),
    via_api_key: bool = Depends(get_authenticated_with_api_key),
    client_ip: str | None = Depends(resolve_client_ip),
    user_service: UserService = Depends(get_user_service),
    tenant_service: TenantService = Depends(get_tenant_service),
):
    """Update a user. Platform admin only.

    Routes the write through ``UserService.admin_update_user`` (#1018) and the
    ``roles`` block through ``TenantService.list_user_memberships`` (#1019). This
    endpoint used to call ``get_db()`` for both — ``collection.update`` for the
    write (past the #982/#996 model re-validation, the reserved-attribute strip
    and the 1202 → :class:`NotFoundError` mapping) and raw AQL for the membership
    read. Both now go through the service layer (NFR-001), and the membership
    join is the same one ``list_user_memberships`` / ``list_all_users`` use.

    **Step-up (#1857, #1992):** any *change* of ``email_verified`` or ``is_active`` —
    raising or lowering — passes the admin's own step-up — ``current_password`` (or ``step_up_token`` /
    ``step_up_code`` for an admin without one); 401 without it, 403 from an
    API-key request, 429 ``STEP_UP_LOCKED``. The step-up fields are never written.
    """
    update_data = body.model_dump(exclude_none=True, exclude=set(CREDENTIAL_STEP_UP_FIELDS))
    user = (
        user_service.admin_update_user(
            key,
            update_data,
            requester=admin,
            current_password=body.current_password,
            step_up_code=body.step_up_code,
            step_up_token=body.step_up_token,
            authenticated_with_api_key=via_api_key,
            client_ip=client_ip,
        )
        if update_data
        else user_service.get_user(key)
    )

    roles = [
        AdminUserTenantRole(
            tenant_key=m.tenant_key,
            tenant_name=m.tenant_name,
            tenant_slug=m.tenant_slug,
            role=m.role,
        )
        for m in tenant_service.list_user_memberships(user.key or key)
        if m.is_active
    ]

    return AdminUserResponse(
        key=user.key or key,
        email=user.email,
        display_name=user.display_name,
        is_active=user.is_active,
        email_verified=user.email_verified,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        tenant_count=len(roles),
        roles=roles,
    )


@router.delete(
    "/tenants/{key}",
    status_code=202,
    response_model=TenantDeletionAcceptedResponse,
    responses=STEP_UP_RESPONSES,
)
def delete_tenant(
    key: Annotated[str, Path(description="Document key of the tenant.")],
    body: TenantDeleteRequest,
    user: User = Depends(require_platform_admin),
    via_api_key: bool = Depends(get_authenticated_with_api_key),
    client_ip: str | None = Depends(resolve_client_ip),
    tenant_service: TenantService = Depends(get_tenant_service),
):
    """Accept the deletion of a tenant and all its data (declared tenant-erasure inventory). Platform admin only.

    Routes through ``TenantService.delete_tenant`` — the same path as the
    tenant-scoped ``DELETE /t/{slug}`` (#1769). **Asynchronous since #1792
    (breaking: ``204`` -> ``202`` with a body):** the request records the deletion
    (``tenant_erasure_records``, the proof) and freezes the tenant, then a Celery
    task runs the external phase (reference vectors, pest prototypes, storage
    prefix) and the inventory in bounded batches — every tenant-scoped collection
    deleted, CanG/PflSchG records kept with their account keys pseudonymised — with
    a claim heartbeat. Nothing is erased when the response arrives.

    **Step-up (#1791):** the body echoes the tenant's slug (422 otherwise) and
    carries the admin's current password when the account has one (401
    otherwise), the code from ``POST /users/me/step-up-code`` as ``step_up_code``
    when not (401 ``STEP_UP_CODE_REQUIRED``, #1815); 403 for an API-key request,
    429 ``STEP_UP_LOCKED`` after too many failures; the service re-proves the
    platform-admin membership.

    Answers: 202 accepted (recorded, frozen, erasure running); 403 the platform
    tenant; 404 no such tenant; 409 another deletion of it is running; 503 the
    deployment cannot erase (nothing changed). A failure of the run itself (an
    external store, residue) is recorded on the record and retried by the beat,
    escalating after repeated failures — it is no longer an HTTP answer.
    """
    record = tenant_service.delete_tenant(
        key,
        requester=user,
        authenticated_with_api_key=via_api_key,
        confirmation=body.to_confirmation(),
        origin="platform_admin",
        client_ip=client_ip,
    )
    return TenantDeletionAcceptedResponse.from_record(record)


@router.get("/users/{key}/erasure-preview", response_model=ErasurePreviewResponse)
def get_user_erasure_preview(
    key: Annotated[str, Path(description="Document key of the user the admin considers deleting.")],
    _admin: User = Depends(require_platform_admin),
    user_service: UserService = Depends(get_user_service),
    privacy_service: PrivacyService = Depends(get_privacy_service),
):
    """Which personal tenants deleting this account takes with it, before the admin confirms (REQ-025 AK-FK-06, #1961).

    The platform-admin counterpart of ``GET /privacy/erasure-preview``, in the
    same shape: the target's own tenant name and a *count* of the other active
    members — never their names, e-mails or roles. Read-only and scoped to the
    one account in the path (404 when it does not exist); it returns nothing about
    any other tenant. The deletion itself, ``DELETE /admin/platform/users/{key}``,
    gives the other members no grace period: they are told it happens now.
    """
    user_service.get_user(key)
    return ErasurePreviewResponse(
        personal_tenants=[
            PersonalTenantErasurePreviewItem(name=item.name, other_member_count=item.other_member_count)
            for item in privacy_service.erasure_preview(key)
        ]
    )


@router.delete(
    "/users/{key}",
    status_code=202,
    response_model=AccountDeletionAcceptedResponse,
    responses=STEP_UP_RESPONSES,
)
def delete_user(
    key: Annotated[str, Path(description="Document key of the user.")],
    body: ErasureCreateRequest,
    current_user: User = Depends(require_platform_admin),
    via_api_key: bool = Depends(get_authenticated_with_api_key),
    client_ip: str | None = Depends(resolve_client_ip),
    privacy_service: PrivacyService = Depends(get_privacy_service),
):
    """Accept the immediate erasure of a user account and all its data. Platform admin only.

    **Asynchronous since #1949 (breaking: ``204`` -> ``202`` with a body).** The
    request records the erasure (the proof: ``origin="platform_admin"``, the
    ``step_up`` and the admin as a salted ``requested_by_subject``), closes the
    account (deactivated, sessions and invitations revoked) and tells the other
    members of its personal gardens *now* (no grace period), then a Celery task runs
    the declared REQ-025 erasure plan — object storage, the personal tenants in
    bounded batches with a claim heartbeat, the ArangoDB plan. **Nothing is erased
    when the response arrives.** Read the outcome from
    ``GET /admin/platform/erasures/{erasure_key}``: ``completed``, or
    ``partially_completed`` for a run that failed or left a declared step open — the
    daily beat retries it, so it is no longer an HTTP answer (it used to be 500
    ``ERASURE_INCOMPLETE`` / 502).

    **Step-up (#1814):** the body echoes the *target's* e-mail (422 otherwise) and
    carries the *admin's own* current password when the admin's account has one
    (401 otherwise), or the code mailed to the admin when it has none (401
    ``STEP_UP_CODE_REQUIRED``, #1815); a request authenticated with an API key is
    refused (403), and too many failed confirmations answer 429 ``STEP_UP_LOCKED``
    (#1816). All of it is decided in
    ``PrivacyService.request_account_erasure_by_admin``, which also refuses the
    admin's own account (403) and re-proves the platform-admin membership from the
    store.

    Answers: 202 accepted (recorded, closed, erasure running); 404 no such account;
    409 another run holds the request; 503 the deployment cannot erase — nothing was
    changed. A repeated request re-dispatches the open erasure and answers 202 again.
    """
    erasure = privacy_service.request_account_erasure_by_admin(
        key,
        requester=current_user,
        confirmation=body.to_confirmation(),
        authenticated_with_api_key=via_api_key,
        client_ip=client_ip,
    )
    return AccountDeletionAcceptedResponse(
        erasure_key=erasure.key or "", status=erasure.status, requested_at=erasure.requested_at
    )


@router.get("/erasures/{erasure_key}", response_model=ErasureResponse)
def get_erasure(
    erasure_key: Annotated[str, Path(description="Key of the erasure request, from the 202 of the account deletion.")],
    _admin: User = Depends(require_platform_admin),
    privacy_service: PrivacyService = Depends(get_privacy_service),
):
    """Status of an account erasure a platform admin accepted (#1949). Platform admin only.

    ``completed`` once the run accounted for every declared step; ``in_progress``
    while a worker holds it; ``partially_completed`` after a run that failed or left a
    step open — the daily beat retries it with backoff. Names no account.
    """
    return ErasureResponse.from_request(privacy_service.get_erasure_for_admin(erasure_key))


# ── Tenant membership management ──────────────────────────────────────
#
# The tenant perspective (below) and the user perspective (further down) are two
# views of the *same* membership operations. Before #1019 each view hand-wrote
# the insert / role update / delete with its own edge management, so a fix to one
# copy silently missed the other. Both now converge on the shared
# ``TenantService.admin_*_membership`` methods; the only per-view code left is
# the response shape (member-centric vs. tenant-centric) and the parent-entity
# ownership constraint passed to the service.


@router.get(
    "/tenants/{tenant_key}/members",
    response_model=list[AdminTenantMemberResponse],
)
def list_tenant_members(
    tenant_key: Annotated[str, Path(description="Document key of the tenant.")],
    _user: User = Depends(require_platform_admin),
    tenant_service: TenantService = Depends(get_tenant_service),
):
    """List all members of a tenant. Platform admin only.

    Routes through ``TenantService.get_tenant`` (existence, 404) and
    ``list_members`` (#1019) — the member/user join now lives in the membership
    repository, not in raw AQL here.
    """
    tenant_service.get_tenant(tenant_key)
    return [
        AdminTenantMemberResponse(
            membership_key=member.key,
            user_key=member.user_key,
            display_name=member.display_name,
            email=member.email,
            role=member.role,
            is_active=member.is_active,
            joined_at=member.joined_at,
        )
        for member in tenant_service.list_members(tenant_key)
    ]


@router.post(
    "/tenants/{tenant_key}/members",
    response_model=AdminTenantMemberResponse,
    status_code=201,
    responses=STEP_UP_RESPONSES,
)
def add_tenant_member(
    tenant_key: Annotated[str, Path(description="Document key of the tenant.")],
    body: AdminAddMemberRequest,
    admin: User = Depends(require_platform_admin),
    via_api_key: bool = Depends(get_authenticated_with_api_key),
    client_ip: str | None = Depends(resolve_client_ip),
    tenant_service: TenantService = Depends(get_tenant_service),
    user_service: UserService = Depends(get_user_service),
):
    """Add a user to a tenant (tenant perspective). Platform admin only.

    Converges on ``TenantService.admin_add_membership`` (#1019), the single
    implementation shared with the user-perspective ``add_user_to_tenant`` — the
    membership row and its two graph edges are created once, in the service. The
    user is loaded here (404 when unknown) because the member-centric response
    needs its name and email.

    **Step-up (#2106, REQ-024 AK-59):** adding an account to a tenant — the ``platform`` tenant
    with ``lead`` makes it a platform admin — passes the admin's own step-up: the body carries
    ``current_password`` (or ``step_up_token`` / ``step_up_code`` obtained for
    ``admin_membership_add`` with ``<tenant_key>|<user_key>`` as the target); 401 without it,
    403 from an API-key request, 429 ``STEP_UP_LOCKED``; nothing is written then. A platform
    admin cannot add themselves to the platform tenant (400). Every add writes a security-audit
    row (#2111). The step-up fields are never written.
    """
    user = user_service.get_user(body.user_key)
    membership = tenant_service.admin_add_membership(
        tenant_key,
        body.user_key,
        body.role,
        requester=admin,
        current_password=body.current_password,
        step_up_code=body.step_up_code,
        step_up_token=body.step_up_token,
        authenticated_with_api_key=via_api_key,
        client_ip=client_ip,
    )
    return AdminTenantMemberResponse(
        membership_key=membership.key or "",
        user_key=body.user_key,
        display_name=user.display_name,
        email=user.email,
        role=membership.role,
        is_active=membership.is_active,
        joined_at=membership.joined_at,
    )


@router.delete(
    "/tenants/{tenant_key}/members/{membership_key}",
    status_code=204,
    responses=STEP_UP_RESPONSES,
)
def remove_tenant_member(
    tenant_key: Annotated[str, Path(description="Document key of the tenant.")],
    membership_key: Annotated[str, Path(description="Document key of the membership.")],
    body: Annotated[AdminMembershipRemovalRequest | None, Body()] = None,
    admin: User = Depends(require_platform_admin),
    via_api_key: bool = Depends(get_authenticated_with_api_key),
    client_ip: str | None = Depends(resolve_client_ip),
    tenant_service: TenantService = Depends(get_tenant_service),
):
    """Remove a member from a tenant (tenant perspective). Platform admin only.

    Converges on ``TenantService.admin_remove_membership`` (#1019), which also
    drops the membership's location assignments — the raw-AQL router copy removed
    only the two graph edges and orphaned them. The ``tenant_key`` constraint
    404s a membership addressed under the wrong tenant.

    **Step-up (#2009, REQ-024 AK-56):** the body carries the admin's own
    ``current_password`` (or ``step_up_token`` / ``step_up_code`` obtained for
    ``admin_membership_removal`` with the membership's key); 401 without it — also
    without a body —, 403 from an API-key request, 429 ``STEP_UP_LOCKED``; the
    membership stays then.
    """
    step_up = body or AdminMembershipRemovalRequest()
    tenant_service.admin_remove_membership(
        membership_key,
        tenant_key=tenant_key,
        requester=admin,
        current_password=step_up.current_password,
        step_up_code=step_up.step_up_code,
        step_up_token=step_up.step_up_token,
        authenticated_with_api_key=via_api_key,
        client_ip=client_ip,
    )


@router.patch(
    "/tenants/{tenant_key}/members/{membership_key}/role",
    response_model=AdminTenantMemberResponse,
    responses=STEP_UP_RESPONSES,
)
def change_member_role(
    tenant_key: Annotated[str, Path(description="Document key of the tenant.")],
    membership_key: Annotated[str, Path(description="Document key of the membership.")],
    body: AdminUpdateMemberRoleRequest,
    admin: User = Depends(require_platform_admin),
    via_api_key: bool = Depends(get_authenticated_with_api_key),
    client_ip: str | None = Depends(resolve_client_ip),
    tenant_service: TenantService = Depends(get_tenant_service),
    user_service: UserService = Depends(get_user_service),
):
    """Change a member's role in a tenant (tenant perspective). Platform admin only.

    Converges on ``TenantService.admin_change_membership_role`` (#1019), shared
    with the user-perspective ``change_user_membership_role``; the write goes
    through the membership repository's re-validated ``update_fields``.

    **Step-up (#2032, REQ-024 AK-57):** an actual change of the role — a tenant's last
    ``lead`` demoted, a member promoted — passes the admin's own step-up: the body
    carries ``current_password`` (or ``step_up_token`` / ``step_up_code`` obtained for
    ``admin_membership_role_change`` with the membership's key); 401 without it, 403
    from an API-key request, 429 ``STEP_UP_LOCKED``; nothing is written then. A role
    re-sent unchanged needs none. The step-up fields are never written.
    """
    membership = tenant_service.admin_change_membership_role(
        membership_key,
        body.role,
        tenant_key=tenant_key,
        requester=admin,
        current_password=body.current_password,
        step_up_code=body.step_up_code,
        step_up_token=body.step_up_token,
        authenticated_with_api_key=via_api_key,
        client_ip=client_ip,
    )
    user = user_service.get_user(membership.user_key)
    return AdminTenantMemberResponse(
        membership_key=membership.key or membership_key,
        user_key=membership.user_key,
        display_name=user.display_name,
        email=user.email,
        role=membership.role,
        is_active=membership.is_active,
        joined_at=membership.joined_at,
    )


# ── User membership management (from user perspective) ────────────────


@router.get(
    "/users/{user_key}/memberships",
    response_model=list[AdminUserMembershipResponse],
)
def list_user_memberships(
    user_key: Annotated[str, Path(description="Document key of the user.")],
    _user: User = Depends(require_platform_admin),
    user_service: UserService = Depends(get_user_service),
    tenant_service: TenantService = Depends(get_tenant_service),
):
    """List all tenant memberships of a user. Platform admin only.

    Routes through ``UserService.get_user`` (existence, 404) and
    ``TenantService.list_user_memberships`` (#1019) — the same membership/tenant
    join ``list_all_users`` and ``update_user`` use.
    """
    user_service.get_user(user_key)
    return [
        AdminUserMembershipResponse(
            membership_key=membership.membership_key,
            tenant_key=membership.tenant_key,
            tenant_name=membership.tenant_name,
            tenant_slug=membership.tenant_slug,
            role=membership.role,
            is_active=membership.is_active,
            joined_at=membership.joined_at,
        )
        for membership in tenant_service.list_user_memberships(user_key)
    ]


@router.post(
    "/users/{user_key}/memberships",
    response_model=AdminUserMembershipResponse,
    status_code=201,
    responses=STEP_UP_RESPONSES,
)
def add_user_to_tenant(
    user_key: Annotated[str, Path(description="Document key of the user.")],
    body: AdminAddUserToTenantRequest,
    admin: User = Depends(require_platform_admin),
    via_api_key: bool = Depends(get_authenticated_with_api_key),
    client_ip: str | None = Depends(resolve_client_ip),
    tenant_service: TenantService = Depends(get_tenant_service),
    user_service: UserService = Depends(get_user_service),
):
    """Add a user to a tenant (user perspective). Platform admin only.

    Converges on ``TenantService.admin_add_membership`` (#1019), the single
    implementation shared with the tenant-perspective ``add_tenant_member``. The
    user (path entity, 404) and the tenant (response name/slug, 404) are loaded
    here; the membership and its edges are created once, in the service.

    **Step-up (#2106, REQ-024 AK-59):** the same as the tenant perspective — the body carries the
    admin's own ``current_password`` (or ``step_up_token`` / ``step_up_code`` for
    ``admin_membership_add`` with ``<tenant_key>|<user_key>``); 401 without it, 403 from an
    API-key request, 429 ``STEP_UP_LOCKED``; nothing is written then.
    """
    user_service.get_user(user_key)
    tenant = tenant_service.get_tenant(body.tenant_key)
    membership = tenant_service.admin_add_membership(
        body.tenant_key,
        user_key,
        body.role,
        requester=admin,
        current_password=body.current_password,
        step_up_code=body.step_up_code,
        step_up_token=body.step_up_token,
        authenticated_with_api_key=via_api_key,
        client_ip=client_ip,
    )
    return AdminUserMembershipResponse(
        membership_key=membership.key or "",
        tenant_key=body.tenant_key,
        tenant_name=tenant.name,
        tenant_slug=tenant.slug,
        role=membership.role,
        is_active=membership.is_active,
        joined_at=membership.joined_at,
    )


@router.delete(
    "/users/{user_key}/memberships/{membership_key}",
    status_code=204,
    responses=STEP_UP_RESPONSES,
)
def remove_user_from_tenant(
    user_key: Annotated[str, Path(description="Document key of the user.")],
    membership_key: Annotated[str, Path(description="Document key of the membership.")],
    body: Annotated[AdminMembershipRemovalRequest | None, Body()] = None,
    admin: User = Depends(require_platform_admin),
    via_api_key: bool = Depends(get_authenticated_with_api_key),
    client_ip: str | None = Depends(resolve_client_ip),
    tenant_service: TenantService = Depends(get_tenant_service),
):
    """Remove a user from a tenant (user perspective). Platform admin only.

    Converges on ``TenantService.admin_remove_membership`` (#1019), shared with
    the tenant-perspective ``remove_tenant_member``. The ``user_key`` constraint
    404s a membership addressed under the wrong user.

    **Step-up (#2009, REQ-024 AK-56):** the same as the tenant perspective — the
    admin's own ``current_password`` (or ``step_up_token`` / ``step_up_code`` for
    ``admin_membership_removal`` with the membership's key) in the body; 401
    without it, 403 from an API-key request, 429 ``STEP_UP_LOCKED``.
    """
    step_up = body or AdminMembershipRemovalRequest()
    tenant_service.admin_remove_membership(
        membership_key,
        user_key=user_key,
        requester=admin,
        current_password=step_up.current_password,
        step_up_code=step_up.step_up_code,
        step_up_token=step_up.step_up_token,
        authenticated_with_api_key=via_api_key,
        client_ip=client_ip,
    )


@router.patch(
    "/users/{user_key}/memberships/{membership_key}/role",
    response_model=AdminUserMembershipResponse,
    responses=STEP_UP_RESPONSES,
)
def change_user_membership_role(
    user_key: Annotated[str, Path(description="Document key of the user.")],
    membership_key: Annotated[str, Path(description="Document key of the membership.")],
    body: AdminUpdateMemberRoleRequest,
    admin: User = Depends(require_platform_admin),
    via_api_key: bool = Depends(get_authenticated_with_api_key),
    client_ip: str | None = Depends(resolve_client_ip),
    tenant_service: TenantService = Depends(get_tenant_service),
):
    """Change a user's role in a tenant (user perspective). Platform admin only.

    Converges on ``TenantService.admin_change_membership_role`` (#1019), shared
    with the tenant-perspective ``change_member_role``; the tenant is loaded for
    the tenant-centric response.

    **Step-up (#2032, REQ-024 AK-57):** the same as the tenant perspective — an actual
    change of the role passes the admin's own ``current_password`` (or ``step_up_token`` /
    ``step_up_code`` for ``admin_membership_role_change`` with the membership's key) in the
    body; 401 without it, 403 from an API-key request, 429 ``STEP_UP_LOCKED``.
    """
    membership = tenant_service.admin_change_membership_role(
        membership_key,
        body.role,
        user_key=user_key,
        requester=admin,
        current_password=body.current_password,
        step_up_code=body.step_up_code,
        step_up_token=body.step_up_token,
        authenticated_with_api_key=via_api_key,
        client_ip=client_ip,
    )
    tenant = tenant_service.get_tenant(membership.tenant_key)
    return AdminUserMembershipResponse(
        membership_key=membership.key or membership_key,
        tenant_key=membership.tenant_key,
        tenant_name=tenant.name,
        tenant_slug=tenant.slug,
        role=membership.role,
        is_active=membership.is_active,
        joined_at=membership.joined_at,
    )
