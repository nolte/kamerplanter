"""Seed database with system user and tenant for light mode (REQ-027)."""

import structlog

from app.common.dependencies import get_membership_repo, get_tenant_repo, get_user_repo
from app.common.enums import TenantRole, TenantType
from app.domain.models.membership import Membership
from app.domain.models.tenant import Tenant
from app.domain.models.user import User

logger = structlog.get_logger()

SYSTEM_USER_KEY = "system-user"
SYSTEM_TENANT_KEY = "system-tenant"
SYSTEM_TENANT_SLUG = "mein-garten"


def run_seed_light_mode() -> None:
    """Create system user with personal tenant for light mode if not present."""
    user_repo = get_user_repo()
    tenant_repo = get_tenant_repo()
    membership_repo = get_membership_repo()

    existing = user_repo.get_by_key(SYSTEM_USER_KEY)
    if existing:
        logger.info("light_mode_system_user_exists", key=SYSTEM_USER_KEY)
        return

    user = User(
        _key=SYSTEM_USER_KEY,
        email="system@kamerplanter.example",
        display_name="Gaertner",
        password_hash=None,
        email_verified=True,
        is_active=True,
    )
    user_repo.create(user)
    logger.info("light_mode_system_user_created", key=SYSTEM_USER_KEY)

    tenant = Tenant(
        _key=SYSTEM_TENANT_KEY,
        name="Mein Garten",
        slug=SYSTEM_TENANT_SLUG,
        tenant_type=TenantType.PERSONAL,
        owner_user_key=SYSTEM_USER_KEY,
        is_active=True,
    )
    tenant_repo.create(tenant)
    logger.info("light_mode_system_tenant_created", key=SYSTEM_TENANT_KEY)

    membership = Membership(
        user_key=SYSTEM_USER_KEY,
        tenant_key=SYSTEM_TENANT_KEY,
        role=TenantRole.ADMIN,
        is_active=True,
    )
    membership_repo.create(membership)
    logger.info("light_mode_membership_created", role="admin")

    logger.info("light_mode_seed_complete")
