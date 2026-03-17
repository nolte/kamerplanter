from datetime import UTC, datetime

from fastapi import APIRouter, Depends

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
from app.common.dependencies import get_db
from app.common.exceptions import DuplicateError, ForbiddenError, NotFoundError
from app.data_access.arango import collections as col
from app.domain.models.user import User

router = APIRouter(prefix="/admin/platform", tags=["admin-platform"])


@router.get("/stats", response_model=AdminStatsResponse)
def get_platform_stats(
    _user: User = Depends(require_platform_admin),
):
    """Get platform-wide statistics."""
    db = get_db()
    total_users = db.collection(col.USERS).count()
    active_users_cursor = db.aql.execute(
        f"FOR u IN {col.USERS} FILTER u.is_active == true COLLECT WITH COUNT INTO c RETURN c"
    )
    active_users = next(active_users_cursor, 0)

    total_tenants = db.collection(col.TENANTS).count()
    active_tenants_cursor = db.aql.execute(
        f"FOR t IN {col.TENANTS} FILTER t.is_active == true COLLECT WITH COUNT INTO c RETURN c"
    )
    active_tenants = next(active_tenants_cursor, 0)

    total_memberships = db.collection(col.MEMBERSHIPS).count()

    return AdminStatsResponse(
        total_users=total_users,
        active_users=active_users,
        total_tenants=total_tenants,
        active_tenants=active_tenants,
        total_memberships=total_memberships,
    )


@router.get("/tenants", response_model=list[AdminTenantResponse])
def list_all_tenants(
    _user: User = Depends(require_platform_admin),
):
    """List all tenants with member counts. Platform admin only."""
    db = get_db()
    query = f"""
    FOR t IN {col.TENANTS}
      LET member_count = LENGTH(
        FOR m IN {col.MEMBERSHIPS}
          FILTER m.tenant_key == t._key AND m.is_active == true
          RETURN 1
      )
      SORT t.created_at DESC
      RETURN MERGE(t, {{member_count: member_count}})
    """
    cursor = db.aql.execute(query)
    results = []
    for doc in cursor:
        results.append(
            AdminTenantResponse(
                key=doc["_key"],
                name=doc["name"],
                slug=doc["slug"],
                tenant_type=doc.get("tenant_type", "personal"),
                description=doc.get("description"),
                owner_user_key=doc.get("owner_user_key", ""),
                is_active=doc.get("is_active", True),
                is_platform=doc.get("is_platform", False),
                max_members=doc.get("max_members", 1),
                member_count=doc["member_count"],
                created_at=doc.get("created_at"),
                updated_at=doc.get("updated_at"),
            )
        )
    return results


@router.get("/users", response_model=list[AdminUserResponse])
def list_all_users(
    _user: User = Depends(require_platform_admin),
):
    """List all users with their tenant memberships. Platform admin only."""
    db = get_db()
    query = f"""
    FOR u IN {col.USERS}
      LET memberships = (
        FOR m IN {col.MEMBERSHIPS}
          FILTER m.user_key == u._key AND m.is_active == true
          LET t = DOCUMENT(CONCAT("{col.TENANTS}/", m.tenant_key))
          FILTER t != null
          RETURN {{
            tenant_key: m.tenant_key,
            tenant_name: t.name,
            tenant_slug: t.slug,
            role: m.role
          }}
      )
      SORT u.created_at DESC
      RETURN {{
        key: u._key,
        email: u.email,
        display_name: u.display_name,
        is_active: u.is_active,
        email_verified: u.email_verified,
        last_login_at: u.last_login_at,
        created_at: u.created_at,
        tenant_count: LENGTH(memberships),
        roles: memberships
      }}
    """
    cursor = db.aql.execute(query)
    results = []
    for doc in cursor:
        results.append(
            AdminUserResponse(
                key=doc["key"],
                email=doc["email"],
                display_name=doc["display_name"],
                is_active=doc.get("is_active", True),
                email_verified=doc.get("email_verified", False),
                last_login_at=doc.get("last_login_at"),
                created_at=doc.get("created_at"),
                tenant_count=doc["tenant_count"],
                roles=[AdminUserTenantRole(**r) for r in doc["roles"]],
            )
        )
    return results


@router.patch("/tenants/{key}", response_model=AdminTenantResponse)
def update_tenant(
    key: str,
    body: AdminTenantUpdate,
    _user: User = Depends(require_platform_admin),
):
    """Update a tenant. Platform admin only."""
    db = get_db()
    collection = db.collection(col.TENANTS)

    existing = collection.get(key)
    if not existing:
        raise NotFoundError("Tenant", key)

    update_data = body.model_dump(exclude_none=True)
    if update_data:
        update_data["updated_at"] = datetime.now(UTC).isoformat()
        collection.update({"_key": key, **update_data})
        existing = collection.get(key)

    # Compute member_count
    member_count_cursor = db.aql.execute(
        "FOR m IN @@col FILTER m.tenant_key == @key AND m.is_active == true COLLECT WITH COUNT INTO c RETURN c",
        bind_vars={"@col": col.MEMBERSHIPS, "key": key},
    )
    member_count = next(member_count_cursor, 0)

    return AdminTenantResponse(
        key=existing["_key"],
        name=existing["name"],
        slug=existing["slug"],
        tenant_type=existing.get("tenant_type", "personal"),
        description=existing.get("description"),
        owner_user_key=existing.get("owner_user_key", ""),
        is_active=existing.get("is_active", True),
        is_platform=existing.get("is_platform", False),
        max_members=existing.get("max_members", 1),
        member_count=member_count,
        created_at=existing.get("created_at"),
        updated_at=existing.get("updated_at"),
    )


@router.patch("/users/{key}", response_model=AdminUserResponse)
def update_user(
    key: str,
    body: AdminUserUpdate,
    _user: User = Depends(require_platform_admin),
):
    """Update a user. Platform admin only."""
    db = get_db()
    collection = db.collection(col.USERS)

    existing = collection.get(key)
    if not existing:
        raise NotFoundError("User", key)

    update_data = body.model_dump(exclude_none=True)
    if update_data:
        update_data["updated_at"] = datetime.now(UTC).isoformat()
        collection.update({"_key": key, **update_data})
        existing = collection.get(key)

    # Fetch memberships
    memberships_cursor = db.aql.execute(
        "FOR m IN @@memberships FILTER m.user_key == @key AND m.is_active == true "
        "LET t = DOCUMENT(CONCAT(@tenants_prefix, m.tenant_key)) "
        "FILTER t != null "
        "RETURN { tenant_key: m.tenant_key, tenant_name: t.name, "
        "tenant_slug: t.slug, role: m.role }",
        bind_vars={
            "@memberships": col.MEMBERSHIPS,
            "key": key,
            "tenants_prefix": f"{col.TENANTS}/",
        },
    )
    roles = [AdminUserTenantRole(**r) for r in memberships_cursor]

    return AdminUserResponse(
        key=existing["_key"],
        email=existing["email"],
        display_name=existing["display_name"],
        is_active=existing.get("is_active", True),
        email_verified=existing.get("email_verified", False),
        last_login_at=existing.get("last_login_at"),
        created_at=existing.get("created_at"),
        tenant_count=len(roles),
        roles=roles,
    )


@router.delete("/tenants/{key}", status_code=204)
def delete_tenant(
    key: str,
    _user: User = Depends(require_platform_admin),
):
    """Delete a tenant and all its memberships. Platform admin only.

    Cannot delete the platform tenant.
    """
    db = get_db()
    tenants = db.collection(col.TENANTS)

    existing = tenants.get(key)
    if not existing:
        raise NotFoundError("Tenant", key)

    if existing.get("is_platform"):
        raise ForbiddenError("The platform tenant cannot be deleted.")

    # Delete all memberships + their edges
    db.aql.execute(
        "FOR m IN @@memberships FILTER m.tenant_key == @key "
        "LET mid = CONCAT(@memberships_prefix, m._key) "
        "LET del_has = (FOR e IN @@has_membership FILTER e._to == mid REMOVE e IN @@has_membership) "
        "LET del_in = (FOR e IN @@membership_in FILTER e._from == mid REMOVE e IN @@membership_in) "
        "REMOVE m IN @@memberships",
        bind_vars={
            "@memberships": col.MEMBERSHIPS,
            "@has_membership": col.HAS_MEMBERSHIP,
            "@membership_in": col.MEMBERSHIP_IN,
            "key": key,
            "memberships_prefix": f"{col.MEMBERSHIPS}/",
        },
    )

    # Delete invitations for this tenant
    db.aql.execute(
        "FOR i IN @@invitations FILTER i.tenant_key == @key REMOVE i IN @@invitations",
        bind_vars={"@invitations": col.INVITATIONS, "key": key},
    )

    # Delete the tenant document
    tenants.delete(key)


@router.delete("/users/{key}", status_code=204)
def delete_user(
    key: str,
    current_user: User = Depends(require_platform_admin),
):
    """Delete a user and all associated data. Platform admin only.

    Cannot delete yourself.
    """
    db = get_db()
    users = db.collection(col.USERS)

    existing = users.get(key)
    if not existing:
        raise NotFoundError("User", key)

    if current_user.key == key:
        raise ForbiddenError("You cannot delete your own account from the admin panel.")

    user_id = f"{col.USERS}/{key}"

    # Delete memberships + edges
    db.aql.execute(
        "FOR m IN @@memberships FILTER m.user_key == @key "
        "LET mid = CONCAT(@memberships_prefix, m._key) "
        "LET del_has = (FOR e IN @@has_membership FILTER e._to == mid REMOVE e IN @@has_membership) "
        "LET del_in = (FOR e IN @@membership_in FILTER e._from == mid REMOVE e IN @@membership_in) "
        "REMOVE m IN @@memberships",
        bind_vars={
            "@memberships": col.MEMBERSHIPS,
            "@has_membership": col.HAS_MEMBERSHIP,
            "@membership_in": col.MEMBERSHIP_IN,
            "key": key,
            "memberships_prefix": f"{col.MEMBERSHIPS}/",
        },
    )

    # Delete auth providers + edges
    db.aql.execute(
        "FOR e IN @@edges FILTER e._from == @uid REMOVE e IN @@edges",
        bind_vars={"@edges": col.HAS_AUTH_PROVIDER, "uid": user_id},
    )
    db.aql.execute(
        "FOR doc IN @@col FILTER doc.user_key == @key REMOVE doc IN @@col",
        bind_vars={"@col": col.AUTH_PROVIDERS, "key": key},
    )

    # Delete refresh tokens
    db.aql.execute(
        "FOR doc IN @@col FILTER doc.user_key == @key REMOVE doc IN @@col",
        bind_vars={"@col": col.REFRESH_TOKENS, "key": key},
    )

    # Delete session edges
    db.aql.execute(
        "FOR e IN @@edges FILTER e._from == @uid REMOVE e IN @@edges",
        bind_vars={"@edges": col.HAS_SESSION, "uid": user_id},
    )

    # Delete API keys
    db.aql.execute(
        "FOR doc IN @@col FILTER doc.user_key == @key REMOVE doc IN @@col",
        bind_vars={"@col": col.API_KEYS, "key": key},
    )

    # Delete user preferences
    db.aql.execute(
        "FOR doc IN @@col FILTER doc.user_key == @key REMOVE doc IN @@col",
        bind_vars={"@col": col.USER_PREFERENCES, "key": key},
    )

    # Delete onboarding states
    db.aql.execute(
        "FOR doc IN @@col FILTER doc.user_key == @key REMOVE doc IN @@col",
        bind_vars={"@col": col.ONBOARDING_STATES, "key": key},
    )

    # Delete the user document
    users.delete(key)


# ── Tenant membership management ──────────────────────────────────────


@router.get(
    "/tenants/{tenant_key}/members",
    response_model=list[AdminTenantMemberResponse],
)
def list_tenant_members(
    tenant_key: str,
    _user: User = Depends(require_platform_admin),
):
    """List all members of a tenant. Platform admin only."""
    db = get_db()

    if not db.collection(col.TENANTS).has(tenant_key):
        raise NotFoundError("Tenant", tenant_key)

    cursor = db.aql.execute(
        "FOR m IN @@memberships FILTER m.tenant_key == @key "
        "LET u = DOCUMENT(CONCAT(@users_prefix, m.user_key)) "
        "FILTER u != null "
        "RETURN { "
        "  membership_key: m._key, user_key: m.user_key, "
        "  display_name: u.display_name, email: u.email, "
        "  role: m.role, is_active: m.is_active, joined_at: m.joined_at "
        "}",
        bind_vars={
            "@memberships": col.MEMBERSHIPS,
            "key": tenant_key,
            "users_prefix": f"{col.USERS}/",
        },
    )
    return [AdminTenantMemberResponse(**doc) for doc in cursor]


@router.post(
    "/tenants/{tenant_key}/members",
    response_model=AdminTenantMemberResponse,
    status_code=201,
)
def add_tenant_member(
    tenant_key: str,
    body: AdminAddMemberRequest,
    _user: User = Depends(require_platform_admin),
):
    """Add a user to a tenant. Platform admin only."""
    db = get_db()

    if not db.collection(col.TENANTS).has(tenant_key):
        raise NotFoundError("Tenant", tenant_key)

    user_doc = db.collection(col.USERS).get(body.user_key)
    if not user_doc:
        raise NotFoundError("User", body.user_key)

    # Check for existing membership
    existing_cursor = db.aql.execute(
        "FOR m IN @@memberships FILTER m.user_key == @uk AND m.tenant_key == @tk LIMIT 1 RETURN m",
        bind_vars={
            "@memberships": col.MEMBERSHIPS,
            "uk": body.user_key,
            "tk": tenant_key,
        },
    )
    existing = next(existing_cursor, None)
    if existing:
        raise DuplicateError("memberships", "user_key+tenant_key", "already a member")

    now = datetime.now(UTC).isoformat()
    result = db.collection(col.MEMBERSHIPS).insert(
        {
            "user_key": body.user_key,
            "tenant_key": tenant_key,
            "role": body.role.value,
            "is_active": True,
            "joined_at": now,
            "created_at": now,
            "updated_at": now,
        },
        return_new=True,
    )
    m_key = result["new"]["_key"]

    # Create graph edges
    db.collection(col.HAS_MEMBERSHIP).insert(
        {
            "_from": f"{col.USERS}/{body.user_key}",
            "_to": f"{col.MEMBERSHIPS}/{m_key}",
            "created_at": now,
        }
    )
    db.collection(col.MEMBERSHIP_IN).insert(
        {
            "_from": f"{col.MEMBERSHIPS}/{m_key}",
            "_to": f"{col.TENANTS}/{tenant_key}",
            "created_at": now,
        }
    )

    return AdminTenantMemberResponse(
        membership_key=m_key,
        user_key=body.user_key,
        display_name=user_doc["display_name"],
        email=user_doc["email"],
        role=body.role,
        is_active=True,
        joined_at=now,
    )


@router.delete(
    "/tenants/{tenant_key}/members/{membership_key}",
    status_code=204,
)
def remove_tenant_member(
    tenant_key: str,
    membership_key: str,
    _user: User = Depends(require_platform_admin),
):
    """Remove a member from a tenant. Platform admin only."""
    db = get_db()
    memberships = db.collection(col.MEMBERSHIPS)

    existing = memberships.get(membership_key)
    if not existing or existing["tenant_key"] != tenant_key:
        raise NotFoundError("Membership", membership_key)

    mid = f"{col.MEMBERSHIPS}/{membership_key}"

    # Delete graph edges
    db.aql.execute(
        "FOR e IN @@col FILTER e._to == @mid REMOVE e IN @@col",
        bind_vars={"@col": col.HAS_MEMBERSHIP, "mid": mid},
    )
    db.aql.execute(
        "FOR e IN @@col FILTER e._from == @mid REMOVE e IN @@col",
        bind_vars={"@col": col.MEMBERSHIP_IN, "mid": mid},
    )

    memberships.delete(membership_key)


@router.patch(
    "/tenants/{tenant_key}/members/{membership_key}/role",
    response_model=AdminTenantMemberResponse,
)
def change_member_role(
    tenant_key: str,
    membership_key: str,
    body: AdminUpdateMemberRoleRequest,
    _user: User = Depends(require_platform_admin),
):
    """Change a member's role in a tenant. Platform admin only."""
    db = get_db()
    memberships = db.collection(col.MEMBERSHIPS)

    existing = memberships.get(membership_key)
    if not existing or existing["tenant_key"] != tenant_key:
        raise NotFoundError("Membership", membership_key)

    memberships.update(
        {
            "_key": membership_key,
            "role": body.role.value,
            "updated_at": datetime.now(UTC).isoformat(),
        }
    )
    updated = memberships.get(membership_key)

    user_doc = db.collection(col.USERS).get(updated["user_key"])
    return AdminTenantMemberResponse(
        membership_key=updated["_key"],
        user_key=updated["user_key"],
        display_name=user_doc["display_name"] if user_doc else "",
        email=user_doc["email"] if user_doc else "",
        role=updated["role"],
        is_active=updated.get("is_active", True),
        joined_at=updated.get("joined_at"),
    )


# ── User membership management (from user perspective) ────────────────


@router.get(
    "/users/{user_key}/memberships",
    response_model=list[AdminUserMembershipResponse],
)
def list_user_memberships(
    user_key: str,
    _user: User = Depends(require_platform_admin),
):
    """List all tenant memberships of a user. Platform admin only."""
    db = get_db()

    if not db.collection(col.USERS).has(user_key):
        raise NotFoundError("User", user_key)

    cursor = db.aql.execute(
        "FOR m IN @@memberships FILTER m.user_key == @key "
        "LET t = DOCUMENT(CONCAT(@tenants_prefix, m.tenant_key)) "
        "FILTER t != null "
        "RETURN { "
        "  membership_key: m._key, tenant_key: m.tenant_key, "
        "  tenant_name: t.name, tenant_slug: t.slug, "
        "  role: m.role, is_active: m.is_active, joined_at: m.joined_at "
        "}",
        bind_vars={
            "@memberships": col.MEMBERSHIPS,
            "key": user_key,
            "tenants_prefix": f"{col.TENANTS}/",
        },
    )
    return [AdminUserMembershipResponse(**doc) for doc in cursor]


@router.post(
    "/users/{user_key}/memberships",
    response_model=AdminUserMembershipResponse,
    status_code=201,
)
def add_user_to_tenant(
    user_key: str,
    body: AdminAddUserToTenantRequest,
    _user: User = Depends(require_platform_admin),
):
    """Add a user to a tenant. Platform admin only."""
    db = get_db()

    if not db.collection(col.USERS).has(user_key):
        raise NotFoundError("User", user_key)

    tenant_doc = db.collection(col.TENANTS).get(body.tenant_key)
    if not tenant_doc:
        raise NotFoundError("Tenant", body.tenant_key)

    # Check for existing membership
    existing_cursor = db.aql.execute(
        "FOR m IN @@memberships FILTER m.user_key == @uk AND m.tenant_key == @tk LIMIT 1 RETURN m",
        bind_vars={
            "@memberships": col.MEMBERSHIPS,
            "uk": user_key,
            "tk": body.tenant_key,
        },
    )
    if next(existing_cursor, None):
        raise DuplicateError("memberships", "user_key+tenant_key", "already a member")

    now = datetime.now(UTC).isoformat()
    result = db.collection(col.MEMBERSHIPS).insert(
        {
            "user_key": user_key,
            "tenant_key": body.tenant_key,
            "role": body.role.value,
            "is_active": True,
            "joined_at": now,
            "created_at": now,
            "updated_at": now,
        },
        return_new=True,
    )
    m_key = result["new"]["_key"]

    db.collection(col.HAS_MEMBERSHIP).insert(
        {
            "_from": f"{col.USERS}/{user_key}",
            "_to": f"{col.MEMBERSHIPS}/{m_key}",
            "created_at": now,
        }
    )
    db.collection(col.MEMBERSHIP_IN).insert(
        {
            "_from": f"{col.MEMBERSHIPS}/{m_key}",
            "_to": f"{col.TENANTS}/{body.tenant_key}",
            "created_at": now,
        }
    )

    return AdminUserMembershipResponse(
        membership_key=m_key,
        tenant_key=body.tenant_key,
        tenant_name=tenant_doc["name"],
        tenant_slug=tenant_doc["slug"],
        role=body.role,
        is_active=True,
        joined_at=now,
    )


@router.delete(
    "/users/{user_key}/memberships/{membership_key}",
    status_code=204,
)
def remove_user_from_tenant(
    user_key: str,
    membership_key: str,
    _user: User = Depends(require_platform_admin),
):
    """Remove a user from a tenant. Platform admin only."""
    db = get_db()
    memberships = db.collection(col.MEMBERSHIPS)

    existing = memberships.get(membership_key)
    if not existing or existing["user_key"] != user_key:
        raise NotFoundError("Membership", membership_key)

    mid = f"{col.MEMBERSHIPS}/{membership_key}"

    db.aql.execute(
        "FOR e IN @@col FILTER e._to == @mid REMOVE e IN @@col",
        bind_vars={"@col": col.HAS_MEMBERSHIP, "mid": mid},
    )
    db.aql.execute(
        "FOR e IN @@col FILTER e._from == @mid REMOVE e IN @@col",
        bind_vars={"@col": col.MEMBERSHIP_IN, "mid": mid},
    )

    memberships.delete(membership_key)


@router.patch(
    "/users/{user_key}/memberships/{membership_key}/role",
    response_model=AdminUserMembershipResponse,
)
def change_user_membership_role(
    user_key: str,
    membership_key: str,
    body: AdminUpdateMemberRoleRequest,
    _user: User = Depends(require_platform_admin),
):
    """Change a user's role in a tenant. Platform admin only."""
    db = get_db()
    memberships = db.collection(col.MEMBERSHIPS)

    existing = memberships.get(membership_key)
    if not existing or existing["user_key"] != user_key:
        raise NotFoundError("Membership", membership_key)

    memberships.update(
        {
            "_key": membership_key,
            "role": body.role.value,
            "updated_at": datetime.now(UTC).isoformat(),
        }
    )
    updated = memberships.get(membership_key)

    tenant_doc = db.collection(col.TENANTS).get(updated["tenant_key"])
    return AdminUserMembershipResponse(
        membership_key=updated["_key"],
        tenant_key=updated["tenant_key"],
        tenant_name=tenant_doc["name"] if tenant_doc else "",
        tenant_slug=tenant_doc["slug"] if tenant_doc else "",
        role=updated["role"],
        is_active=updated.get("is_active", True),
        joined_at=updated.get("joined_at"),
    )
