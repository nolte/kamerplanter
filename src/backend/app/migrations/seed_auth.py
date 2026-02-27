"""Seed database with a demo admin user and personal tenant (dev only)."""

import structlog

from app.common.dependencies import get_membership_repo, get_tenant_repo, get_user_repo
from app.common.enums import EmailVerificationStatus, TenantRole, TenantType
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.tenant_engine import TenantEngine
from app.domain.models.membership import Membership
from app.domain.models.tenant import Tenant
from app.domain.models.user import User

logger = structlog.get_logger()

DEMO_EMAIL = "demo@kamerplanter.local"
DEMO_PASSWORD = "demo-passwort-2024"
DEMO_DISPLAY_NAME = "Demo Admin"

password_engine = PasswordEngine()
tenant_engine = TenantEngine()


def run_seed_auth() -> None:
    """Create a demo user with personal tenant if not already present."""
    user_repo = get_user_repo()
    tenant_repo = get_tenant_repo()
    membership_repo = get_membership_repo()

    # Check if demo user already exists
    existing = user_repo.get_by_email(DEMO_EMAIL)
    if existing:
        logger.info("demo_user_exists", email=DEMO_EMAIL)
        return

    # Create demo user (pre-verified)
    user = User(
        email=DEMO_EMAIL,
        display_name=DEMO_DISPLAY_NAME,
        password_hash=password_engine.hash_password(DEMO_PASSWORD),
        email_verified=EmailVerificationStatus.VERIFIED,
        is_active=True,
    )
    created_user = user_repo.create(user)
    user_key = created_user.key or ""
    logger.info("demo_user_created", email=DEMO_EMAIL, key=user_key)

    # Create personal tenant
    slug = tenant_engine.generate_slug(DEMO_DISPLAY_NAME)
    tenant = Tenant(
        name=f"{DEMO_DISPLAY_NAME}'s Garden",
        slug=slug,
        tenant_type=TenantType.PERSONAL,
        owner_user_key=user_key,
        is_active=True,
    )
    created_tenant = tenant_repo.create(tenant)
    tenant_key = created_tenant.key or ""
    logger.info("demo_tenant_created", slug=slug, key=tenant_key)

    # Create admin membership
    membership = Membership(
        user_key=user_key,
        tenant_key=tenant_key,
        role=TenantRole.ADMIN,
        is_active=True,
    )
    membership_repo.create(membership)
    logger.info("demo_membership_created", role="admin")

    logger.info(
        "demo_seed_complete",
        email=DEMO_EMAIL,
        password=DEMO_PASSWORD,
        tenant_slug=slug,
    )


if __name__ == "__main__":
    from app.config.logging import setup_logging

    setup_logging()
    run_seed_auth()
