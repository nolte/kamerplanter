from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Cookie, Depends, Header, Path
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.common.dependencies import get_auth_provider, get_tenant_service
from app.common.enums import AdminScope, TenantRole
from app.common.exceptions import ForbiddenError, NotFoundError, UnauthorizedError
from app.config.settings import settings
from app.core.permissions import Action, ResourceType
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.interfaces.auth_provider import IAuthProvider
from app.domain.models.membership import Membership
from app.domain.models.tenant import Tenant
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


#: Name of the request header that carries the tenant a caller is acting in on a
#: global (path-less tenant-aware) route — the mechanism ADR-009 records. The
#: value is a tenant **slug**, not a key: it is human-readable, it is what the
#: ``/api/v1/t/{slug}/`` routes already bind, and it is what the frontend keeps in
#: ``kp_active_tenant_slug``. Exported so routers, tests and the frontend contract
#: can name it once.
ACTIVE_TENANT_HEADER = "X-Active-Tenant"

#: The header parameter both resolvers declare. Written in the ``Annotated`` form
#: (``Annotated[str | None, Header(...)] = None``) rather than as a
#: ``Header(default=None, ...)`` *default value*: FastAPI reads both, but only
#: this one leaves the Python default a real ``None``, so the resolvers stay
#: callable as plain functions — which is how every unit test and the two
#: pre-#1091 test modules invoke them. With the default-value form those calls
#: receive the ``Header`` marker object itself and fail on it.
ActiveTenantHeader = Annotated[
    str | None,
    Header(
        alias=ACTIVE_TENANT_HEADER,
        description=(
            "Slug of the tenant the caller is acting in, for global (path-less) tenant-aware routes "
            "such as the species and botanical-family catalogues (ADR-009, REQ-049 §2.11). "
            "Omit it to act in your personal tenant. A slug you hold no active membership in is refused with 403."
        ),
    ),
]

#: The single refusal message for *both* invalid-header cases. Deliberately says
#: nothing about whether the slug exists: answering "unknown tenant" for one case
#: and "not a member" for the other would turn any authenticated request into a
#: tenant-existence oracle (R2 / REQ-025 minimisation). Kept as one constant so
#: the two raise sites cannot drift into two distinguishable answers.
_ACTIVE_TENANT_DENIED = "You do not have access to the requested tenant."


@dataclass(frozen=True)
class _ActiveTenant:
    """The tenant one request is acting in, as resolved from header or personal fallback.

    ``membership`` is a *callable* rather than a value on purpose: the read path
    (:func:`get_active_tenant_key`) needs only the key and must not pay for a
    membership lookup it never reads, while the context path needs the role. On
    the header path the membership has already been fetched and validated, so the
    callable just hands it back — the lookup happens at most once either way.
    """

    key: str
    tenant: Tenant | None
    membership: Callable[[], Membership | None]

    @property
    def slug(self) -> str:
        return self.tenant.slug if self.tenant else ""


def _resolve_active_tenant(
    user: User,
    tenant_service: TenantService,
    active_tenant_slug: str | None,
) -> _ActiveTenant:
    """Resolve *which tenant* this request acts in — the one shared resolution (ADR-009).

    Both public resolvers below delegate here, so the read scope
    (:func:`get_active_tenant_key`), the write stamping
    (:data:`get_creating_tenant_key`) and the role decision
    (:func:`get_active_tenant_context`) can never end up on different notions of
    "the caller's tenant". A second, copy-pasted resolution is the drift this
    function exists to make impossible.

    Two input classes:

    * **No header** (absent, empty or whitespace-only — see
      :func:`get_active_tenant_key` for why blank counts as absent): the caller's
      personal tenant, ``""`` when they have none. Unvalidated, exactly as before
      #1091 — a user's own personal tenant needs no membership proof, and the
      fallback must stay fail-open-to-*narrow* (global-only), never an error.
    * **A slug**: resolved and then *validated*. The caller must hold an active
      membership in it; otherwise the request is refused.

    Raises:
        ForbiddenError: The header names a tenant that does not exist, or one the
            caller holds no active membership in. Both raise the same message —
            see :data:`_ACTIVE_TENANT_DENIED`. Never a silent fallback to the
            personal tenant or to global scope: acting in the wrong tenant is the
            confusion this mechanism removes, so an unhonourable header fails the
            request instead of quietly changing its meaning.
    """
    user_key = user.key or ""
    slug = (active_tenant_slug or "").strip()

    if not slug:
        personal = tenant_service.get_personal_tenant(user_key)
        key = personal.key if personal and personal.key else ""
        return _ActiveTenant(
            key=key,
            tenant=personal,
            membership=(lambda: tenant_service.get_membership(user_key, key)) if (user_key and key) else (lambda: None),
        )

    try:
        tenant = tenant_service.get_tenant_by_slug(slug)
    except NotFoundError as exc:
        # NOT a 404. ``get_tenant_by_slug`` raises NotFoundError, and forwarding it
        # would make this resolver a tenant-existence oracle: any authenticated
        # caller could probe slugs and read "404 = no such tenant" versus
        # "403 = it exists but you are not in it". Both invalid cases must be one
        # indistinguishable answer, so the 404 is converted here — at the only
        # place that knows the lookup was driven by an untrusted header value.
        raise ForbiddenError(_ACTIVE_TENANT_DENIED) from exc

    membership = tenant_service.get_membership(user_key, tenant.key or "") if user_key else None
    if not membership or not membership.is_active:
        raise ForbiddenError(_ACTIVE_TENANT_DENIED)
    return _ActiveTenant(key=tenant.key or "", tenant=tenant, membership=lambda: membership)


def get_active_tenant_key(
    user: User = Depends(get_current_user),
    tenant_service: TenantService = Depends(get_tenant_service),
    active_tenant_slug: ActiveTenantHeader = None,
) -> str:
    """Resolve the caller's active tenant on a *global-but-tenant-aware* route (F-5, #808).

    Design note — tenant resolution for global routes (#808 A1, resolved by ADR-009)
    -------------------------------------------------------------------------------
    Most tenant-scoped surfaces live under ``/api/v1/t/{slug}/`` and resolve
    their tenant with :func:`get_current_tenant`, which reads the ``tenant_slug``
    *path parameter* and verifies membership. A handful of catalogues, however,
    are mounted **globally** — ``/api/v1/species`` and ``/api/v1/botanical-
    families`` are the first — because their rows are a *hybrid catalogue*: global
    seed data (``tenant_key == ""``) shared by everyone, plus a tenant's own
    additions. Those routes carry no ``{slug}`` segment, so ``get_current_tenant``
    structurally cannot bind there. Before this resolver they therefore had **no**
    tenant context at all, and the reads returned every tenant's rows to every
    caller — the leak F-5 closes.

    This dependency is that missing mechanism. It answers a single question —
    *"which tenant is this caller acting in, on a route that names none?"* — and
    is deliberately the **one** resolver shared by both the read path (species /
    botanical-family listing) and the write path (species create, via the
    :data:`get_creating_tenant_key` alias below), so read scope and write stamping
    can never drift onto different notions of "the caller's tenant".

    The signal (#1091, ADR-009, REQ-049 §2.11):
        The :data:`ACTIVE_TENANT_HEADER` (``X-Active-Tenant``) request header
        carries the **slug** of the tenant the caller is acting in. It is declared
        here as a FastAPI ``Header`` parameter, so every operation that depends on
        this resolver advertises it in the generated OpenAPI document rather than
        it being an undocumented side channel. A slug the caller holds no *active*
        membership in — and an unknown slug, indistinguishably — is refused with
        403; see :func:`_resolve_active_tenant`.

    Without the header:
        The caller's auto-created **personal** tenant — the single ``PERSONAL``
        tenant every user owns since registration (REQ-024), resolved by
        :meth:`TenantService.get_personal_tenant`. This is the pre-#1091
        behaviour, kept byte-for-byte: a single-tenant caller (the common case)
        and every existing client are unaffected by the new mechanism.

    An empty or whitespace-only header value counts as *absent*, deliberately:
        A client that clears its active tenant may send the header empty rather
        than dropping it from the request, and "" is not the name of a tenant.
        Treating it as a lookup would refuse exactly those callers with a 403 for
        having no org context — a fail-*closed* answer to the one input that
        unambiguously means "no org context".

    Behaviour when there is no resolvable tenant (anonymous / light-mode /
    a user without a personal tenant, and no header):
        Returns ``""``. Because the read predicate is the three-arm hybrid union
        (:func:`~app.data_access.arango.tenant_scope.tenant_union_predicate`), an
        empty key collapses the union to *global-only* (``tenant_key == "" OR
        null``). So a caller with no tenant sees exactly the shared seed catalogue
        and nothing tenant-owned — never an error, never a foreign tenant's rows.
        This is the fail-safe direction: absence of context narrows visibility, it
        never widens it. Note the asymmetry that makes the whole design safe:
        *absence* of context narrows, a *rejected* context fails the request; only
        a validated header widens anything.

    Scope (R6): the header binds exactly the surfaces that depend on this
    resolver — the species, cultivar, botanical-family and companion-planting
    catalogues. ``/api/v1/t/{slug}/`` routes keep binding their tenant from the
    path (:func:`get_current_tenant`), and favourites stay personal across
    tenants; a future consumer opts in by depending on this function.
    """
    return _resolve_active_tenant(user, tenant_service, active_tenant_slug).key


def get_active_tenant_context(
    user: User = Depends(get_current_user),
    tenant_service: TenantService = Depends(get_tenant_service),
    active_tenant_slug: ActiveTenantHeader = None,
) -> TenantContext:
    """Resolve the caller's active tenant into a role-bearing context (SEC-002, #808; #1091).

    The *write* sibling of :func:`get_active_tenant_key`. A global-but-tenant-aware
    *read* only needs the tenant *key* to scope the hybrid-catalogue union; a
    *mutation* additionally needs the caller's domain *role* — a viewer must not
    write (REQ-049 §2.3) — and their admin scopes. This mirrors
    :func:`get_current_tenant`, but binds the tenant from the
    :data:`ACTIVE_TENANT_HEADER` (falling back to the personal tenant) because the
    global route (``/api/v1/species``) carries no ``/t/{slug}/`` segment to bind
    to. Crucially it does not re-derive that tenant: it calls the very same
    :func:`_resolve_active_tenant` the read path calls, so a mutation's ownership
    stamp can never drift from the read scope, and an invalid header fails here
    exactly as it fails there.

    The role comes from the membership **in the resolved tenant** (#1091 R3): an
    organisation viewer acting in their club is a ``viewer`` here, never the
    ``lead`` of their own personal tenant. Reading the role from the wrong tenant
    would hand every user lead rights everywhere — the defect this binding exists
    to prevent.

    A caller with no resolvable personal tenant / no active membership (and no
    header) resolves to an empty tenant at the lowest role
    (:attr:`TenantRole.VIEWER`) — fail-safe: absence of context yields the least
    privilege, never more. The light-mode operator (REQ-027) is admitted via the
    separate platform-admin bypass (:func:`get_is_platform_admin`), not by
    widening the role here.
    """
    resolved = _resolve_active_tenant(user, tenant_service, active_tenant_slug)
    membership = resolved.membership()
    active = membership if (membership and membership.is_active) else None
    return TenantContext(
        tenant_key=resolved.key,
        tenant_slug=resolved.slug,
        user_key=user.key or "",
        role=active.role if active else TenantRole.VIEWER,
        admin_scopes=active.admin_scopes if active else [],
    )


def get_is_platform_admin(
    user: User = Depends(get_current_user),
    tenant_service: TenantService = Depends(get_tenant_service),
) -> bool:
    """Whether the caller is a platform admin, as a resolvable dependency (SEC-002, #808).

    Dependency wrapper over :func:`is_platform_admin` so a global-catalogue
    mutation route can thread the boolean into :class:`SpeciesService`, which
    decides conditionally: only a platform admin may mutate a *global* seed row
    (``tenant_key == ""``). In light mode (REQ-027) the sole anonymous operator is
    treated as platform admin, so light-mode curation of the shared catalogue
    keeps working.
    """
    return is_platform_admin(tenant_service, user.key or "")


#: F-3 back-compat alias. The write-stamping dependency the species create route
#: depends on (``Depends(get_creating_tenant_key)``) is the *same* "caller's
#: active tenant on a global route" resolver the F-5 read path uses. Keeping it as
#: an alias (identical function object) means a test overriding
#: ``get_creating_tenant_key`` still reaches the resolver, and read scope can
#: never diverge from write stamping. The name is retained because F-3 and its
#: tests reference it and it reads well at the create call site. Since #1091 the
#: alias therefore also carries the :data:`ACTIVE_TENANT_HEADER`: a create on a
#: global route is stamped with the tenant the caller is *acting in*, and a header
#: the caller may not use fails the create rather than stamping the personal one.
get_creating_tenant_key = get_active_tenant_key


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
