"""#2105 — every tenant lookup either reads ``is_active`` on the tenant it loaded, or is decided.

The defect class: a tenant becomes an authorization context without anyone reading
``tenant.is_active``. ``PATCH /admin/platform/tenants/{key}`` with ``is_active=false``
(REQ-024 AK-56) then locks nobody out — exactly what shipped until #2105: the
``/t/{slug}/`` path, the ``X-Active-Tenant`` header and the header-less personal
fallback all resolved a deactivated tenant, because :func:`app.common.auth._membership_for_slug`
read ``membership.is_active`` — and **only** that. A check that "some ``is_active``
is read in this function" would have passed that very code, which is why this guard
binds the read to the variable the lookup's result was assigned to.

The population is derived from the **sources**, not from the found sites: every place
in ``app/`` that loads a tenant document goes through one of

* :class:`~app.domain.services.tenant_service.TenantService` — ``get_tenant``,
  ``get_tenant_by_slug``, ``get_personal_tenant`` (receiver named ``*tenant_service*``);
* the tenant repository — ``get_by_key``, ``get_by_slug``, ``list_by_owner``,
  ``list_all`` (receiver named ``*tenant_repo*``).

``list_my_tenants`` is deliberately **not** a source: it is itself a resolver (the one
the MCP authenticator and ``GET /tenants`` stand on), and its own repository read is
one of the sites below, checked like any other. Each site is listed in
:data:`_SITES` with a verdict:

* ``reads`` — checked **against the code**: the function assigns the named variable
  and reads ``<variable>.is_active`` (or ``getattr(<variable>, "is_active", ...)``).
  When the lookup is assigned directly, the variable must be the one it is assigned
  to — a register entry naming a different variable is refused.
* ``decided`` — the site is not a resolution into an authorization context (platform
  administration, a mutation behind an already-resolved context, a migration, a
  lookup that only returns the document to a caller that is itself a site). The
  reason is the review record.

What this does not see: a tenant loaded by a path that names none of the sources —
raw AQL over the ``tenants`` collection, or a ``DOCUMENT("tenants/…")`` join inside a
repository (``list_by_user_with_tenant`` is one; it feeds only the platform-admin
listing today). The behaviour itself is held end to end by
``tests/integration/test_inactive_tenant_resolution_reach.py``.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[3] / "app"
ROOT = APP.parent

_SERVICE_LOOKUPS = {"get_tenant", "get_tenant_by_slug", "get_personal_tenant"}
_REPO_LOOKUPS = {"get_by_key", "get_by_slug", "list_by_owner", "list_all"}

_READS = "reads"
_DECIDED = "decided"

_TS = "app/domain/services/tenant_service.py"
_ADMIN = "app/api/v1/admin/platform/router.py"

#: ``"path:qualified name"`` → ``(verdict, variable for "reads" | "", reason)``.
_SITES: dict[str, tuple[str, str, str]] = {
    # -- the resolvers into an authorization context ------------------------------------
    "app/common/auth.py:_membership_for_slug": (
        _READS,
        "tenant",
        "the /t/{slug}/ path and the X-Active-Tenant header (#2105)",
    ),
    "app/common/auth.py:_resolve_active_tenant": (
        _READS,
        "personal",
        "the header-less personal fallback narrows to global scope (#2105)",
    ),
    f"{_TS}:TenantService.list_my_tenants": (
        _READS,
        "tenant",
        "GET /tenants and the MCP authenticator's memberships (McpAuthenticator._resolve_memberships)",
    ),
    "app/domain/services/auth_service.py:AuthService._canonical_tenant_scope": (
        _READS,
        "tenant",
        "an API key's tenant_scope may only name an active tenant (#1852)",
    ),
    # -- lookups that hand the document to a caller which is itself a site --------------
    f"{_TS}:TenantService.get_tenant": (_DECIDED, "", "returns the document; its callers are sites"),
    f"{_TS}:TenantService.get_tenant_by_slug": (_DECIDED, "", "returns the document; its callers are sites"),
    f"{_TS}:TenantService.get_personal_tenant": (_DECIDED, "", "returns the document; its callers are sites"),
    # -- platform administration: must reach a deactivated tenant (#2105 decision) -------
    f"{_ADMIN}:update_tenant": (_DECIDED, "", "platform admin; reactivating needs the deactivated tenant"),
    f"{_ADMIN}:list_tenant_members": (_DECIDED, "", "platform admin administers a deactivated tenant"),
    f"{_ADMIN}:add_user_to_tenant": (_DECIDED, "", "platform admin; the membership resolves only once active"),
    f"{_ADMIN}:change_user_membership_role": (_DECIDED, "", "platform admin administers a deactivated tenant"),
    f"{_TS}:TenantService.admin_update_tenant": (_DECIDED, "", "platform admin; reads is_active to step-up"),
    f"{_TS}:TenantService.admin_add_membership": (
        _DECIDED,
        "",
        "platform admin; a membership in a deactivated tenant resolves for nobody",
    ),
    f"{_TS}:TenantService.list_all_tenants": (_DECIDED, "", "platform-admin catalogue listing"),
    # -- reads behind an already-resolved context, mutations, erasure -------------------
    "app/api/v1/ki_assistent/deps.py:require_ai_tenant_enabled": (
        _DECIDED,
        "",
        "reads AI settings of ctx.tenant_key, which get_current_tenant already resolved",
    ),
    f"{_TS}:TenantService._apply_tenant_update": (_DECIDED, "", "mutation; the route resolved the tenant"),
    f"{_TS}:TenantService.delete_tenant": (_DECIDED, "", "erasure must reach a deactivated tenant"),
    f"{_TS}:TenantService.erase_personal_tenant_of": (_DECIDED, "", "erasure must reach a deactivated tenant"),
    f"{_TS}:TenantService.personal_tenant_erasure_preview": (_DECIDED, "", "erasure preview of the owner's tenants"),
    f"{_TS}:TenantService._refuse_invitation_while_owner_erasing": (_DECIDED, "", "erasure-freeze check only"),
    f"{_TS}:TenantService._refuse_beyond_member_limit": (
        _DECIDED,
        "",
        "member-limit check of a join (#2133); a membership in a deactivated tenant resolves for nobody",
    ),
    f"{_TS}:TenantService._refuse_role_grant": (_DECIDED, "", "escalation check inside a resolved context"),
    f"{_TS}:TenantService._ensure_unique_slug": (_DECIDED, "", "slug collision probe; no tenant is resolved"),
    # -- migrations: no request, no principal --------------------------------------------
    "app/migrations/add_platform_admin.py:add_platform_admin": (_DECIDED, "", "migration; the platform tenant"),
    "app/migrations/seed_auth.py:_ensure_platform_admin": (_DECIDED, "", "migration; the platform tenant"),
}


@dataclass
class _Site:
    function: ast.FunctionDef | ast.AsyncFunctionDef
    #: The variables a lookup in this function is assigned to directly (``x = lookup(...)``).
    bound: set[str]


def _is_lookup(node: ast.AST) -> bool:
    if not isinstance(node, ast.Attribute):
        return False
    receiver = ast.unparse(node.value)
    return (node.attr in _SERVICE_LOOKUPS and "tenant_service" in receiver) or (
        node.attr in _REPO_LOOKUPS and "tenant_repo" in receiver
    )


def _sites_in(source: str, rel: str) -> dict[str, _Site]:
    """Every function in *source* that references a tenant lookup, by ``rel:qualname``."""
    found: dict[str, _Site] = {}

    def visit(node: ast.AST, stack: list[str], function: ast.FunctionDef | ast.AsyncFunctionDef | None) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                visit(child, [*stack, child.name], function)
                continue
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                visit(child, [*stack, child.name], child)
                continue
            if _is_lookup(child) and function is not None:
                site = found.setdefault(f"{rel}:{'.'.join(stack)}", _Site(function, set()))
                site.bound |= _directly_bound(function, child)
            visit(child, stack, function)

    visit(ast.parse(source), [], None)
    return found


def _directly_bound(function: ast.AST, lookup: ast.Attribute) -> set[str]:
    """The names ``x`` of ``x = <lookup>(...)`` in *function* for this *lookup* node."""
    names: set[str] = set()
    for node in ast.walk(function):
        if (
            isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Call)
            and node.value.func is lookup
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            names.add(node.targets[0].id)
    return names


def _assigns(function: ast.AST, name: str) -> bool:
    return any(
        isinstance(node, ast.Name) and node.id == name and isinstance(node.ctx, ast.Store)
        for node in ast.walk(function)
    )


def _reads_is_active_of(function: ast.AST, name: str) -> bool:
    for node in ast.walk(function):
        if (
            isinstance(node, ast.Attribute)
            and node.attr == "is_active"
            and isinstance(node.value, ast.Name)
            and node.value.id == name
        ):
            return True
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "getattr"
            and len(node.args) >= 2
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id == name
            and isinstance(node.args[1], ast.Constant)
            and node.args[1].value == "is_active"
        ):
            return True
    return False


def _violation(site: _Site, verdict: tuple[str, str, str]) -> str | None:
    """Why *site* does not hold its register *verdict*, or ``None`` when it does."""
    kind, variable, _reason = verdict
    if kind == _DECIDED:
        return None
    if site.bound and variable not in site.bound:
        return f"the lookup is assigned to {sorted(site.bound)}, the register names {variable!r}"
    if not _assigns(site.function, variable):
        return f"{variable!r} is never assigned in the function"
    if not _reads_is_active_of(site.function, variable):
        return f"{variable!r}.is_active is never read — the tenant resolves whether or not it is deactivated"
    return None


@cache
def _all_sites() -> dict[str, _Site]:
    found: dict[str, _Site] = {}
    for path in sorted(APP.rglob("*.py")):
        found.update(_sites_in(path.read_text(encoding="utf-8"), str(path.relative_to(ROOT))))
    return found


# ── The guard ────────────────────────────────────────────────────────────────


def test_every_tenant_lookup_is_registered():
    unregistered = sorted(set(_all_sites()) - set(_SITES))

    assert not unregistered, (
        "A tenant lookup the register does not decide (#2105). A function that turns a tenant into an "
        "authorization context must read `<tenant>.is_active` and be registered as 'reads'; anything "
        "else is registered as 'decided' with the reason:\n  " + "\n  ".join(unregistered)
    )


def test_no_registered_site_is_stale():
    stale = sorted(set(_SITES) - set(_all_sites()))

    assert not stale, "Register entries with no tenant lookup left — remove them:\n  " + "\n  ".join(stale)


@pytest.mark.parametrize("key", sorted(k for k, v in _SITES.items() if v[0] == _READS))
def test_a_resolver_reads_is_active_on_the_tenant_it_loaded(key: str):
    site = _all_sites().get(key)
    assert site is not None, f"{key} no longer looks a tenant up"

    assert _violation(site, _SITES[key]) is None, f"{key}: {_violation(site, _SITES[key])}"


# ── Self-test: the detector sees what it claims to see ───────────────────────

_FIXTURE_REL = "app/fixture.py"

_CHECKS_THE_TENANT = """
def resolve(tenant_service, slug, user_key):
    tenant = tenant_service.get_tenant_by_slug(slug)
    if not tenant.is_active:
        raise PermissionError
    membership = tenant_service.get_membership(user_key, tenant.key)
    if not membership.is_active:
        raise PermissionError
    return tenant
"""

#: The #2105 shape: an ``is_active`` read in the function — on the *membership*.
_CHECKS_ONLY_THE_MEMBERSHIP = """
def resolve(tenant_service, slug, user_key):
    tenant = tenant_service.get_tenant_by_slug(slug)
    membership = tenant_service.get_membership(user_key, tenant.key)
    if not membership.is_active:
        raise PermissionError
    return tenant
"""

_CHECKS_BY_GETATTR = """
class Service:
    def scope(self, value):
        for lookup in (self._tenant_service.get_tenant, self._tenant_service.get_tenant_by_slug):
            tenant = lookup(value)
        if not getattr(tenant, "is_active", True):
            raise PermissionError
"""


def _only_site(source: str) -> tuple[str, _Site]:
    (item,) = _sites_in(source, _FIXTURE_REL).items()
    return item


def test_self_test_a_tenant_check_satisfies_the_register():
    key, site = _only_site(_CHECKS_THE_TENANT)

    assert key == f"{_FIXTURE_REL}:resolve"
    assert site.bound == {"tenant"}
    assert _violation(site, (_READS, "tenant", "")) is None


def test_self_test_a_membership_check_alone_is_the_defect():
    _key, site = _only_site(_CHECKS_ONLY_THE_MEMBERSHIP)

    violation = _violation(site, (_READS, "tenant", ""))

    assert violation is not None
    assert "never read" in violation
    # Naming the membership in the register does not launder it either.
    assert _violation(site, (_READS, "membership", "")) is not None


def test_self_test_a_lookup_passed_by_reference_is_found_and_held_by_getattr():
    key, site = _only_site(_CHECKS_BY_GETATTR)

    assert key == f"{_FIXTURE_REL}:Service.scope"
    assert site.bound == set()
    assert _violation(site, (_READS, "tenant", "")) is None
    assert _violation(site, (_READS, "other", "")) is not None


def test_self_test_an_unrelated_receiver_is_not_a_tenant_lookup():
    source = """
def read(plant_repo, key):
    return plant_repo.get_by_key(key)
"""

    assert _sites_in(source, _FIXTURE_REL) == {}
