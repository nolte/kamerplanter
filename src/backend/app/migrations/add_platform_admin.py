"""Add a user as platform admin by email. Creates platform tenant if needed.

Usage:
    python -m app.migrations.add_platform_admin <email>

Example:
    python -m app.migrations.add_platform_admin nolte@example.com
"""

import sys

import structlog

from app.common.dependencies import get_membership_repo, get_tenant_repo, get_user_repo
from app.common.enums import TenantRole, TenantType
from app.config.logging import setup_logging
from app.domain.models.membership import Membership
from app.domain.models.tenant import Tenant

logger = structlog.get_logger()


def add_platform_admin(email: str) -> None:
    user_repo = get_user_repo()
    tenant_repo = get_tenant_repo()
    membership_repo = get_membership_repo()

    user = user_repo.get_by_email(email)
    if not user:
        logger.error("user_not_found", email=email)
        print(f"User with email '{email}' not found.")

        # List all users to help find the right one
        from app.common.dependencies import get_db
        from app.data_access.arango import collections as col

        db = get_db()
        cursor = db.aql.execute(
            f"FOR u IN {col.USERS} RETURN {{key: u._key, email: u.email, display_name: u.display_name}}"
        )
        users = list(cursor)
        if users:
            print("\nExisting users:")
            for u in users:
                print(f"  - {u['email']} ({u['display_name']}, key={u['key']})")
        return

    user_key = user.key or ""
    logger.info("user_found", email=email, key=user_key)

    # Ensure platform tenant exists
    platform = tenant_repo.get_by_key("platform")
    if not platform:
        platform = Tenant(
            _key="platform",
            name="Kamerplanter Platform",
            slug="platform",
            tenant_type=TenantType.ORGANIZATION,
            owner_user_key=user_key,
            is_active=True,
            is_platform=True,
            max_members=999,
        )
        tenant_repo.create(platform)
        logger.info("platform_tenant_created")
        print("Platform tenant created.")

    # Check existing membership
    existing = membership_repo.get_by_user_and_tenant(user_key, "platform")
    if existing:
        if existing.role == TenantRole.ADMIN and existing.is_active:
            print(f"User '{email}' is already a platform admin.")
            return
        # Update to admin
        membership_repo.update(existing.key, {"role": TenantRole.ADMIN, "is_active": True})
        print(f"User '{email}' upgraded to platform admin.")
        return

    # Create admin membership
    membership = Membership(
        user_key=user_key,
        tenant_key="platform",
        role=TenantRole.ADMIN,
        is_active=True,
    )
    membership_repo.create(membership)
    print(f"User '{email}' is now a platform admin.")
    logger.info("platform_admin_added", email=email, user_key=user_key)


if __name__ == "__main__":
    setup_logging()
    if len(sys.argv) < 2:
        print("Usage: python -m app.migrations.add_platform_admin <email>")
        print("\nIf you don't know the email, run without argument to list all users.")
        # List all users
        from app.common.dependencies import get_db
        from app.data_access.arango import collections as col

        db = get_db()
        cursor = db.aql.execute(
            f"FOR u IN {col.USERS} RETURN {{key: u._key, email: u.email, display_name: u.display_name}}"
        )
        users = list(cursor)
        if users:
            print("\nExisting users:")
            for u in users:
                print(f"  - {u['email']} ({u['display_name']}, key={u['key']})")
        sys.exit(1)

    add_platform_admin(sys.argv[1])
