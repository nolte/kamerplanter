"""Seed database with a demo admin user and personal tenant (dev only)."""

import structlog

from app.common.dependencies import get_membership_repo, get_tenant_repo, get_user_repo
from app.common.enums import EmailVerificationStatus, TenantRole, TenantType
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.tenant_engine import TenantEngine
from app.domain.models.membership import Membership
from app.domain.models.tenant import Tenant
from app.domain.models.user import User
from app.migrations.yaml_loader import load_yaml

logger = structlog.get_logger()

password_engine = PasswordEngine()
tenant_engine = TenantEngine()


def run_seed_auth() -> None:
    """Create a demo user with personal tenant if not already present."""
    data = load_yaml("auth.yaml")
    demo = data["demo_user"]

    user_repo = get_user_repo()
    tenant_repo = get_tenant_repo()
    membership_repo = get_membership_repo()

    existing = user_repo.get_by_email(demo["email"])
    if existing:
        logger.info("demo_user_exists", email=demo["email"])
        return

    user = User(
        email=demo["email"],
        display_name=demo["display_name"],
        password_hash=password_engine.hash_password(demo["password"]),
        email_verified=EmailVerificationStatus.VERIFIED,
        is_active=True,
    )
    created_user = user_repo.create(user)
    user_key = created_user.key or ""
    logger.info("demo_user_created", email=demo["email"], key=user_key)

    slug = tenant_engine.generate_slug(demo["display_name"])
    tenant = Tenant(
        name=f"{demo['display_name']}'s Garden",
        slug=slug,
        tenant_type=TenantType.PERSONAL,
        owner_user_key=user_key,
        is_active=True,
    )
    created_tenant = tenant_repo.create(tenant)
    tenant_key = created_tenant.key or ""
    logger.info("demo_tenant_created", slug=slug, key=tenant_key)

    membership = Membership(
        user_key=user_key,
        tenant_key=tenant_key,
        role=TenantRole.ADMIN,
        is_active=True,
    )
    membership_repo.create(membership)
    logger.info("demo_membership_created", role="admin")

    # Ensure platform tenant exists and user is platform admin
    _ensure_platform_admin(user_key, tenant_repo, membership_repo)

    logger.info(
        "demo_seed_complete",
        email=demo["email"],
        tenant_slug=slug,
    )


def _ensure_platform_admin(
    user_key: str,
    tenant_repo,
    membership_repo,
) -> None:
    """Ensure platform tenant exists and user has admin membership."""
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

    existing_membership = membership_repo.get_by_user_and_tenant(user_key, "platform")
    if not existing_membership:
        membership = Membership(
            user_key=user_key,
            tenant_key="platform",
            role=TenantRole.ADMIN,
            is_active=True,
        )
        membership_repo.create(membership)
        logger.info("platform_admin_membership_created", user_key=user_key)


def ensure_platform_admin_for_user(user_key: str) -> None:
    """Add a user as platform admin. Can be called standalone."""
    tenant_repo = get_tenant_repo()
    membership_repo = get_membership_repo()
    _ensure_platform_admin(user_key, tenant_repo, membership_repo)


if __name__ == "__main__":
    from app.config.logging import setup_logging

    setup_logging()
    run_seed_auth()
