from typing import Annotated

from fastapi import APIRouter, Depends, Path

from app.api.v1.admin.platform.schemas import (
    AdminAddMemberRequest,
    AdminAddUserToTenantRequest,
    AdminStatsResponse,
    AdminTenantMemberResponse,
    AdminTenantResponse,
    AdminTenantUpdate,
    AdminUpdateMemberRoleRequest,
    AdminUserMembershipResponse,
    AdminUserResponse,
    AdminUserTenantRole,
    AdminUserUpdate,
)
from app.common.auth import require_platform_admin
from app.common.dependencies import get_privacy_service, get_tenant_service, get_user_service
from app.common.exceptions import ForbiddenError
from app.common.openapi_responses import AUTH_CRUD_RESPONSES
from app.domain.models.user import User
from app.domain.services.privacy_service import PrivacyService
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


@router.patch("/tenants/{key}", response_model=AdminTenantResponse)
def update_tenant(
    key: Annotated[str, Path(description="Document key of the tenant.")],
    body: AdminTenantUpdate,
    _user: User = Depends(require_platform_admin),
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
    carry; ``update_tenant`` takes a partial payload and does not refuse it, so
    the platform-admin path needs no separate service method — only the closed
    ``AdminTenantUpdate`` schema that keeps ``owner_user_key``, ``is_platform``,
    ``tenant_type``, ``slug`` and ``settings`` out of it.
    """
    update_data = body.model_dump(exclude_none=True)
    tenant = tenant_service.update_tenant(key, update_data) if update_data else tenant_service.get_tenant(key)

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


@router.patch("/users/{key}", response_model=AdminUserResponse)
def update_user(
    key: Annotated[str, Path(description="Document key of the user.")],
    body: AdminUserUpdate,
    _user: User = Depends(require_platform_admin),
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
    """
    update_data = body.model_dump(exclude_none=True)
    user = user_service.admin_update_user(key, update_data) if update_data else user_service.get_user(key)

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


@router.delete("/tenants/{key}", status_code=204)
def delete_tenant(
    key: Annotated[str, Path(description="Document key of the tenant.")],
    _user: User = Depends(require_platform_admin),
    tenant_service: TenantService = Depends(get_tenant_service),
):
    """Delete a tenant and all its associated data. Platform admin only.

    Cannot delete the platform tenant. Routes through
    ``TenantService.delete_tenant`` so this admin path shares the exact same
    NFR-013 §6.1 purge as the tenant-scoped ``DELETE /t/{slug}`` endpoint:
    object-storage prefix (``t/{key}/``) + contributed reference-index vectors
    are removed alongside memberships, invitations and assignments (SEC-002 —
    previously this raw-AQL path orphaned the tenant's binary data).

    The existence check and the ``is_platform`` guard read the tenant through
    ``TenantService.get_tenant`` (#1019) instead of ``get_db()``, so the router
    no longer touches Persistence directly (NFR-001).
    """
    tenant = tenant_service.get_tenant(key)
    if tenant.is_platform:
        raise ForbiddenError("The platform tenant cannot be deleted.")

    tenant_service.delete_tenant(key)


@router.delete("/users/{key}", status_code=204)
def delete_user(
    key: Annotated[str, Path(description="Document key of the user.")],
    current_user: User = Depends(require_platform_admin),
    privacy_service: PrivacyService = Depends(get_privacy_service),
    user_service: UserService = Depends(get_user_service),
):
    """Delete a user and all associated data. Platform admin only.

    Cannot delete yourself.

    SEC-003: runs the REQ-025 Phase 0 / 0.5 storage cleanup
    (``run_user_storage_erasure`` — object storage + contributed reference-index
    vectors) **before** the account hard-delete. That cleanup resolves the user's
    tenants via their memberships, so it must run while they still exist —
    otherwise the user's binary data and contributed embeddings would be
    orphaned, the same gap the scheduled erasure closes.

    The ArangoDB cascade routes through ``UserService.delete_account_permanently``
    (#1019): eight raw-AQL ``REMOVE``s used to run from this router past the
    service layer (NFR-001). It now removes the user's memberships (+ edges) via
    the membership repository, then the user document and its remaining
    single-user artefacts (auth providers, tokens, sessions, API keys,
    preferences, onboarding state) via the user repository. Membership removal
    stays after the storage cleanup, preserving the SEC-003 ordering.
    """
    from app.common.async_bridge import run_async

    user_service.get_user(key)

    if current_user.key == key:
        raise ForbiddenError("You cannot delete your own account from the admin panel.")

    # ── REQ-025 Phase 0 / 0.5 (SEC-003) — must precede membership removal ──
    run_async(privacy_service.run_user_storage_erasure(key))

    user_service.delete_account_permanently(key)


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
)
def add_tenant_member(
    tenant_key: Annotated[str, Path(description="Document key of the tenant.")],
    body: AdminAddMemberRequest,
    _user: User = Depends(require_platform_admin),
    tenant_service: TenantService = Depends(get_tenant_service),
    user_service: UserService = Depends(get_user_service),
):
    """Add a user to a tenant (tenant perspective). Platform admin only.

    Converges on ``TenantService.admin_add_membership`` (#1019), the single
    implementation shared with the user-perspective ``add_user_to_tenant`` — the
    membership row and its two graph edges are created once, in the service. The
    user is loaded here (404 when unknown) because the member-centric response
    needs its name and email.
    """
    user = user_service.get_user(body.user_key)
    membership = tenant_service.admin_add_membership(tenant_key, body.user_key, body.role)
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
)
def remove_tenant_member(
    tenant_key: Annotated[str, Path(description="Document key of the tenant.")],
    membership_key: Annotated[str, Path(description="Document key of the membership.")],
    _user: User = Depends(require_platform_admin),
    tenant_service: TenantService = Depends(get_tenant_service),
):
    """Remove a member from a tenant (tenant perspective). Platform admin only.

    Converges on ``TenantService.admin_remove_membership`` (#1019), which also
    drops the membership's location assignments — the raw-AQL router copy removed
    only the two graph edges and orphaned them. The ``tenant_key`` constraint
    404s a membership addressed under the wrong tenant.
    """
    tenant_service.admin_remove_membership(membership_key, tenant_key=tenant_key)


@router.patch(
    "/tenants/{tenant_key}/members/{membership_key}/role",
    response_model=AdminTenantMemberResponse,
)
def change_member_role(
    tenant_key: Annotated[str, Path(description="Document key of the tenant.")],
    membership_key: Annotated[str, Path(description="Document key of the membership.")],
    body: AdminUpdateMemberRoleRequest,
    _user: User = Depends(require_platform_admin),
    tenant_service: TenantService = Depends(get_tenant_service),
    user_service: UserService = Depends(get_user_service),
):
    """Change a member's role in a tenant (tenant perspective). Platform admin only.

    Converges on ``TenantService.admin_change_membership_role`` (#1019), shared
    with the user-perspective ``change_user_membership_role``; the write goes
    through the membership repository's re-validated ``update_fields``.
    """
    membership = tenant_service.admin_change_membership_role(membership_key, body.role, tenant_key=tenant_key)
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
)
def add_user_to_tenant(
    user_key: Annotated[str, Path(description="Document key of the user.")],
    body: AdminAddUserToTenantRequest,
    _user: User = Depends(require_platform_admin),
    tenant_service: TenantService = Depends(get_tenant_service),
    user_service: UserService = Depends(get_user_service),
):
    """Add a user to a tenant (user perspective). Platform admin only.

    Converges on ``TenantService.admin_add_membership`` (#1019), the single
    implementation shared with the tenant-perspective ``add_tenant_member``. The
    user (path entity, 404) and the tenant (response name/slug, 404) are loaded
    here; the membership and its edges are created once, in the service.
    """
    user_service.get_user(user_key)
    tenant = tenant_service.get_tenant(body.tenant_key)
    membership = tenant_service.admin_add_membership(body.tenant_key, user_key, body.role)
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
)
def remove_user_from_tenant(
    user_key: Annotated[str, Path(description="Document key of the user.")],
    membership_key: Annotated[str, Path(description="Document key of the membership.")],
    _user: User = Depends(require_platform_admin),
    tenant_service: TenantService = Depends(get_tenant_service),
):
    """Remove a user from a tenant (user perspective). Platform admin only.

    Converges on ``TenantService.admin_remove_membership`` (#1019), shared with
    the tenant-perspective ``remove_tenant_member``. The ``user_key`` constraint
    404s a membership addressed under the wrong user.
    """
    tenant_service.admin_remove_membership(membership_key, user_key=user_key)


@router.patch(
    "/users/{user_key}/memberships/{membership_key}/role",
    response_model=AdminUserMembershipResponse,
)
def change_user_membership_role(
    user_key: Annotated[str, Path(description="Document key of the user.")],
    membership_key: Annotated[str, Path(description="Document key of the membership.")],
    body: AdminUpdateMemberRoleRequest,
    _user: User = Depends(require_platform_admin),
    tenant_service: TenantService = Depends(get_tenant_service),
):
    """Change a user's role in a tenant (user perspective). Platform admin only.

    Converges on ``TenantService.admin_change_membership_role`` (#1019), shared
    with the tenant-perspective ``change_member_role``; the tenant is loaded for
    the tenant-centric response.
    """
    membership = tenant_service.admin_change_membership_role(membership_key, body.role, user_key=user_key)
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
