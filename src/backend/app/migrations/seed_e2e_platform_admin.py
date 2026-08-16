"""Seed a second, platform-admin account for the full-mode E2E suite (#1155).

## Why a second account

#1120 made the global catalogue mutations platform-admin-only. The E2E suite
authenticates as the demo user, who is an ordinary member — correctly, because a
large part of the suite exists to assert what an ordinary member is *refused*,
#1120's own case among them. Promoting that one account would turn every one of
those assertions vacuous while leaving them green, which is the failure class
NFR-018 §1 catalogues.

The alternative considered and rejected was wiring the existing
``run_seed_auth``: it grants platform admin to the **demo user** (see its call to
``_ensure_platform_admin``), so wiring it does exactly the damage above. It also
still has no caller anywhere, which is a separate matter.

## Why this is not simply an environment variable

Creating a platform administrator from an env var is a backdoor shape, and
naming it ``E2E_...`` does not make it one bit less powerful in a deployment that
happens to set it. So the variable is necessary but not sufficient: the seed also
refuses unless ``cookie_secure`` is off.

That second condition was chosen because it is the one setting a real deployment
cannot have: ``cookie_secure`` defaults to ``True``, must stay ``True`` anywhere
the app is reachable over the network, and is off here only because the E2E stack
speaks plain HTTP inside a compose network. ``debug`` would not have worked — the
E2E stack runs with ``DEBUG=false`` on purpose, to exercise the same startup
gates production does.

The result is that a stray environment variable alone cannot mint an
administrator; it takes a deployment that has *also* disabled cookie security,
which is already broken in a way this seed does not meaningfully worsen.

Both conditions are logged when they refuse, because a seed that silently does
nothing is how the suite would end up asserting against a missing account and
reporting the confusing half of the problem.
"""

from __future__ import annotations

import structlog

from app.common.dependencies import get_membership_repo, get_tenant_repo, get_user_repo
from app.common.enums import TenantRole, TenantType
from app.config.settings import settings
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.tenant_engine import TenantEngine
from app.domain.models.membership import Membership
from app.domain.models.tenant import Tenant
from app.domain.models.user import User

logger = structlog.get_logger()

password_engine = PasswordEngine()
tenant_engine = TenantEngine()


def run_seed_e2e_platform_admin() -> None:
    """Create the E2E platform-admin account, if and only if both gates allow it.

    Idempotent: an existing account is left untouched, including its password —
    re-seeding must not silently reset a credential the running suite already
    holds a token for.
    """
    email = settings.e2e_platform_admin_email
    password = settings.e2e_platform_admin_password

    if not email or not password:
        # Half-configured is a configuration error, not a reason to invent the
        # missing half. Loud, because the suite fails far away from here.
        if email or password:
            logger.error(
                "e2e_platform_admin_half_configured",
                has_email=bool(email),
                has_password=bool(password),
            )
        return

    if settings.cookie_secure:
        logger.error(
            "e2e_platform_admin_refused",
            reason="cookie_secure is on, so this is not an E2E stack",
            email=email,
        )
        return

    user_repo = get_user_repo()
    tenant_repo = get_tenant_repo()
    membership_repo = get_membership_repo()

    existing = user_repo.get_by_email(email)
    if existing:
        # Still ensure the membership: the account can survive a database that
        # was seeded before this seed existed, or have lost the platform tenant.
        _grant_platform_admin(existing.key or "", tenant_repo, membership_repo)
        logger.info("e2e_platform_admin_exists", email=email)
        return

    logger.warning(
        "e2e_platform_admin_seeding",
        email=email,
        note="test-only account with full platform-admin rights",
    )

    user = User(
        email=email,
        display_name="E2E Platform Admin",
        password_hash=password_engine.hash_password(password),
        email_verified=True,
        is_active=True,
    )
    created = user_repo.create(user)
    user_key = created.key or ""

    # A personal tenant, so the account behaves like any other user outside the
    # platform surfaces — the suite navigates tenant-scoped routes as this user
    # too, and an account with no tenant would fail those for the wrong reason.
    tenant = Tenant(
        name="E2E Admin's Garden",
        slug=tenant_engine.generate_slug("E2E Admin"),
        tenant_type=TenantType.PERSONAL,
        owner_user_key=user_key,
        is_active=True,
    )
    created_tenant = tenant_repo.create(tenant)
    membership_repo.create(
        Membership(
            user_key=user_key,
            tenant_key=created_tenant.key or "",
            role=TenantRole.LEAD,
            is_active=True,
        )
    )

    _grant_platform_admin(user_key, tenant_repo, membership_repo)
    logger.info("e2e_platform_admin_created", email=email, key=user_key)


def _grant_platform_admin(user_key: str, tenant_repo, membership_repo) -> None:  # noqa: ANN001
    """Delegate to the existing platform-admin grant so there is one such path."""
    if not user_key:
        logger.error("e2e_platform_admin_no_user_key")
        return

    from app.migrations.seed_auth import _ensure_platform_admin

    _ensure_platform_admin(user_key, tenant_repo, membership_repo)
