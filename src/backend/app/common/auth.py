from collections.abc import Callable

from fastapi import Cookie, Depends, Path
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.common.dependencies import get_auth_provider, get_tenant_service
from app.common.enums import AdminScope, TenantRole
from app.common.exceptions import ForbiddenError, UnauthorizedError
from app.config.settings import settings
from app.core.permissions import Action, ResourceType
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.interfaces.auth_provider import IAuthProvider
from app.domain.models.tenant_context import TenantContext
from app.domain.models.user import User
from app.domain.services.tenant_service import TenantService

# Declared as a FastAPI security scheme (not a raw Header parameter) so the
# generated OpenAPI document carries `components.securitySchemes` and a
# `security` requirement on every protected operation. `auto_error=False`
# keeps resolution manual: the auth provider decides how a missing or
# malformed header fails (light mode resolves to the anonymous system user).
bearer_scheme = HTTPBearer(
    auto_error=False,
    scheme_name="BearerAuth",
    description="JWT access token or `kp_`-prefixed service-account API key.",
)


def _raw_authorization(credentials: HTTPAuthorizationCredentials | None) -> str | None:
    """Rebuild the raw Authorization header value the auth providers expect."""
    if credentials is None:
        return None
    return f"{credentials.scheme} {credentials.credentials}"


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    auth_provider: IAuthProvider = Depends(get_auth_provider),
) -> User:
    """Extract and validate user from Bearer token, API key, or system user."""
    return auth_provider.resolve_user(_raw_authorization(credentials))


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    auth_provider: IAuthProvider = Depends(get_auth_provider),
) -> User | None:
    """Extract user from Bearer token, or return None if no token."""
    return auth_provider.resolve_user_optional(_raw_authorization(credentials))


def get_refresh_token_from_cookie(
    kp_refresh: str | None = Cookie(default=None, description="HttpOnly refresh-token cookie set by the login flow."),
) -> str:
    """Extract refresh token from HttpOnly cookie."""
    if not kp_refresh:
        raise UnauthorizedError("Missing refresh token cookie.")
    return kp_refresh


def get_current_tenant(
    tenant_slug: str = Path(description="URL slug of the tenant the request is scoped to (REQ-024)."),
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
        admin_scopes=membership.admin_scopes,
    )


def is_platform_admin(tenant_service: TenantService, user_key: str) -> bool:
    """True when ``user_key`` is a platform admin (a ``lead`` membership in ``platform``).

    Mirrors :func:`require_platform_admin` but returns a boolean instead of
    raising, so a tenant-scoped endpoint can *conditionally* unlock admin-only
    behaviour (e.g. the "show deselected images" curation view) without changing
    its access for normal members. In light mode (REQ-027) the sole anonymous
    system user is the operator and is treated as platform admin.

    The platform role is carried by the top domain role in the technical
    ``platform`` tenant (REQ-049 §2.5). That used to be ``admin``; migration
    ``v0032`` renamed every such membership to ``lead`` along with all the
    others, so this check moved with it rather than the platform tenant keeping
    a retired value of its own.
    """
    if settings.kamerplanter_mode == "light":
        return True
    membership = tenant_service.get_membership(user_key, "platform")
    return bool(membership and membership.is_active and membership.role == TenantRole.LEAD)


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
    """Dependency factory for axis 1: a minimum domain role (REQ-049 §2.3).

    This is the *domain* branch of the authorisation rule. Administrative
    actions — member management, integrations, sensor configuration — belong to
    axis 2 and use :func:`require_admin_scope` instead. The two branches are
    disjoint on purpose: an action reachable through both is exactly the
    conflation REQ-049 was written to end.
    """
    role_order = {TenantRole.VIEWER: 0, TenantRole.GROWER: 1, TenantRole.LEAD: 2}

    def _check(ctx: TenantContext = Depends(get_current_tenant)) -> TenantContext:
        if role_order.get(ctx.role, 0) < role_order[min_role]:
            raise ForbiddenError(f"Requires at least {min_role.value} role.")
        return ctx

    return _check


def require_permission(resource: ResourceType | str, action: Action) -> Callable:
    """Dependency factory: gate a tenant-scoped write on the caller's domain role.

    This is the REQ-024 §1a.6 / REQ-049 §2.3 permission gate finally wired onto
    the routers. It composes on top of :func:`get_current_tenant`, which has
    already established that the caller *is* an active member of the path tenant
    (a non-member is refused there with 403 before this dependency runs), and
    resolved their domain role into :class:`TenantContext`. The gate therefore
    never does its own database lookup — it decides purely on ``ctx.role`` — and
    it fails closed: a role that maps to no rule is refused.

    The authority is the pure :class:`MembershipEngine` predicate matching the
    action, so the router surface and the engine can never drift on the
    grower/lead delete boundary:

    * ``CREATE`` / ``UPDATE`` → :meth:`MembershipEngine.can_edit_resource`
      (lead or grower may write).
    * ``DELETE`` → :meth:`MembershipEngine.can_delete_resource`
      (lead only — the irreversibility boundary of REQ-049 §2.3).
    * ``READ`` → :meth:`MembershipEngine.can_view_resource` (every member),
      so reads stay open; a GET only needs this gate when a specific read is
      privileged.

    ``resource`` does not change the decision today — the engine's predicates are
    role-driven, not yet per-resource-type — but it is required and recorded so
    that the call sites document *what* they guard and a future per-resource
    matrix can tighten individual entries without touching every router. It is
    the axis-1 (domain) counterpart to :func:`require_tenant_role`; use
    :func:`require_admin_scope` for the disjoint axis-2 administrative actions
    (member management, integrations), which must not be gated here.

    Refusal is a 403 ``FORBIDDEN`` (via :class:`ForbiddenError`), never a 404:
    the caller is a legitimate member of this tenant, merely under-privileged, so
    the honest signal is "forbidden". A 404 is reserved for a *foreign* tenant's
    resources (ownership hiding) and would be the wrong signal here.
    """

    def _check(ctx: TenantContext = Depends(get_current_tenant)) -> TenantContext:
        if action in (Action.CREATE, Action.UPDATE):
            allowed = MembershipEngine.can_edit_resource(ctx.role)
        elif action == Action.DELETE:
            allowed = MembershipEngine.can_delete_resource(ctx.role)
        elif action == Action.READ:
            allowed = MembershipEngine.can_view_resource(ctx.role)
        else:
            # Unknown / not-yet-mapped verb (e.g. INVITE belongs on axis 2):
            # fail closed rather than silently allow.
            allowed = False
        if not allowed:
            raise ForbiddenError(f"Your role '{ctx.role.value}' may not '{action.value}' a {resource} in this tenant.")
        return ctx

    return _check


def require_admin_scope(scope: AdminScope) -> Callable:
    """Dependency factory for axis 2: an administrative scope (REQ-049 §2.4).

    Independent of the domain rank — a viewer holding ``MANAGEMENT`` passes, a
    lead without it does not. That independence is the point: authority over
    people and access to technology come apart in practice, and merging them
    would force every club to open its member list to whoever maintains the
    sensors.
    """

    def _check(ctx: TenantContext = Depends(get_current_tenant)) -> TenantContext:
        if scope not in ctx.admin_scopes:
            raise ForbiddenError(f"Requires the {scope.value} administrative scope.")
        return ctx

    return _check
