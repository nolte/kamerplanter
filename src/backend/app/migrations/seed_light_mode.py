"""Seed database with system user and tenant for light mode (REQ-027)."""

from datetime import UTC, datetime

import structlog

from app.common.dependencies import get_connection
from app.data_access.arango import collections as col
from app.migrations.yaml_loader import load_yaml

logger = structlog.get_logger()


def run_seed_light_mode() -> None:
    """Create system user with personal tenant for light mode if not present.

    Uses direct collection inserts (not repositories) to preserve
    deterministic _key values required by LightAuthProvider.
    """
    data = load_yaml("light_mode.yaml")
    su = data["system_user"]
    st = data["system_tenant"]
    now = datetime.now(UTC).isoformat()

    db = get_connection().db

    users = db.collection(col.USERS)
    if users.has(su["key"]):
        logger.info("light_mode_system_user_exists", key=su["key"])
        return

    users.insert({
        "_key": su["key"],
        "email": su["email"],
        "display_name": su["display_name"],
        "password_hash": None,
        "email_verified": True,
        "is_active": True,
        "failed_login_attempts": 0,
        "locale": "de",
        "timezone": "Europe/Berlin",
        "created_at": now,
        "updated_at": now,
    })
    logger.info("light_mode_system_user_created", key=su["key"])

    tenants = db.collection(col.TENANTS)
    if not tenants.has(st["key"]):
        tenants.insert({
            "_key": st["key"],
            "name": st["name"],
            "slug": st["slug"],
            "tenant_type": "personal",
            "owner_user_key": su["key"],
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        })
        logger.info("light_mode_system_tenant_created", key=st["key"])

    memberships = db.collection(col.MEMBERSHIPS)
    membership_key = f"{su['key']}--{st['key']}"
    if not memberships.has(membership_key):
        memberships.insert({
            "_key": membership_key,
            "user_key": su["key"],
            "tenant_key": st["key"],
            "role": "admin",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        })
        logger.info("light_mode_membership_created", role="admin")

    logger.info("light_mode_seed_complete")
