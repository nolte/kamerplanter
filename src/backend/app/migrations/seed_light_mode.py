"""Seed database with system user and tenant for light mode (REQ-027)."""

import structlog

from app.common.dependencies import get_membership_repo, get_tenant_repo, get_user_repo
from app.common.enums import TenantRole, TenantType
from app.domain.models.membership import Membership
from app.domain.models.tenant import Tenant
from app.domain.models.user import User
from app.migrations.yaml_loader import load_yaml

logger = structlog.get_logger()


def run_seed_light_mode() -> None:
    """Create system user with personal tenant for light mode if not present."""
    data = load_yaml("light_mode.yaml")
    su = data["system_user"]
    st = data["system_tenant"]

    user_repo = get_user_repo()
    tenant_repo = get_tenant_repo()
    membership_repo = get_membership_repo()

    existing = user_repo.get_by_key(su["key"])
    if existing:
        logger.info("light_mode_system_user_exists", key=su["key"])
        return

    user = User(
        _key=su["key"],
        email=su["email"],
        display_name=su["display_name"],
        password_hash=None,
        email_verified=True,
        is_active=True,
    )
    user_repo.create(user)
    logger.info("light_mode_system_user_created", key=su["key"])

    tenant = Tenant(
        _key=st["key"],
        name=st["name"],
        slug=st["slug"],
        tenant_type=TenantType.PERSONAL,
        owner_user_key=su["key"],
        is_active=True,
    )
    tenant_repo.create(tenant)
    logger.info("light_mode_system_tenant_created", key=st["key"])

    membership = Membership(
        user_key=su["key"],
        tenant_key=st["key"],
        role=TenantRole.ADMIN,
        is_active=True,
    )
    membership_repo.create(membership)
    logger.info("light_mode_membership_created", role="admin")

    logger.info("light_mode_seed_complete")
