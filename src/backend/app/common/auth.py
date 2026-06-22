from collections.abc import Callable

from fastapi import Cookie, Depends, Header, Path

from app.common.dependencies import get_auth_provider, get_tenant_service
from app.common.enums import TenantRole
from app.common.exceptions import ForbiddenError, UnauthorizedError
from app.config.settings import settings
from app.domain.interfaces.auth_provider import IAuthProvider
from app.domain.models.tenant_context import TenantContext
from app.domain.models.user import User
from app.domain.services.tenant_service import TenantService


def get_current_user(
    authorization: str | None = Header(default=None),
    auth_provider: IAuthProvider = Depends(get_auth_provider),
) -> User:
    """Extract and validate user from Bearer token, API key, or system user."""
    return auth_provider.resolve_user(authorization)


def get_current_user_optional(
    authorization: str | None = Header(default=None),
    auth_provider: IAuthProvider = Depends(get_auth_provider),
) -> User | None:
    """Extract user from Bearer token, or return None if no token."""
    return auth_provider.resolve_user_optional(authorization)


def get_refresh_token_from_cookie(
    kp_refresh: str | None = Cookie(default=None),
) -> str:
    """Extract refresh token from HttpOnly cookie."""
    if not kp_refresh:
        raise UnauthorizedError("Missing refresh token cookie.")
    return kp_refresh


def get_current_tenant(
    tenant_slug: str = Path(...),
    user: User = Depends(get_current_user),
    tenant_service: TenantService = Depends(get_tenant_service),
) -> TenantContext:
    """Resolve tenant from URL slug and verify user membership."""
    tenant = tenant_service.get_tenant_by_slug(tenant_slug)
    membership = tenant_service.get_membership(user.key, tenant.key)
    if not membership or not membership.is_active:
        raise ForbiddenError("You are not a member of this tenant.")

    return TenantContext(
        tenant_key=tenant.key,
        tenant_slug=tenant.slug,
        user_key=user.key,
        role=membership.role,
    )


def is_platform_admin(tenant_service: TenantService, user_key: str) -> bool:
    """True when ``user_key`` is a platform admin (admin membership in ``platform``).

    Mirrors :func:`require_platform_admin` but returns a boolean instead of
    raising, so a tenant-scoped endpoint can *conditionally* unlock admin-only
    behaviour (e.g. the "show deselected images" curation view) without changing
    its access for normal members. In light mode (REQ-027) the sole anonymous
    system user is the operator and is treated as platform admin.
    """
    if settings.kamerplanter_mode == "light":
        return True
    membership = tenant_service.get_membership(user_key, "platform")
    return bool(membership and membership.is_active and membership.role == TenantRole.ADMIN)


def require_platform_admin(
    user: User = Depends(get_current_user),
    tenant_service: TenantService = Depends(get_tenant_service),
) -> User:
    """Require the user to be a platform admin (admin membership in platform tenant).

    In light mode (REQ-027) there is no platform tenant and only the single
    anonymous system user exists — that user is the sole operator and therefore
    treated as platform admin.
    """
    if not is_platform_admin(tenant_service, user.key or ""):
        raise ForbiddenError("Platform admin role required.")
    return user


def require_tenant_role(min_role: TenantRole) -> Callable:
    """Dependency factory for minimum role enforcement."""
    role_order = {TenantRole.VIEWER: 0, TenantRole.GROWER: 1, TenantRole.ADMIN: 2}

    def _check(ctx: TenantContext = Depends(get_current_tenant)) -> TenantContext:
        if role_order.get(ctx.role, 0) < role_order[min_role]:
            raise ForbiddenError(f"Requires at least {min_role.value} role.")
        return ctx

    return _check
