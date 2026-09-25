"""#1817 — an API key's ``tenant_scope`` binds every place a REST request gets a tenant.

The defect: the scope was read by the MCP authenticator only. On the REST path a
``kp_`` key became its owner's account, and every tenant decision after that was
taken on the owner's memberships — a key scoped to tenant A acted in any tenant
B its owner belonged to.

The fix enforces the scope in the tenant resolvers. This guard does not re-test
that behaviour (``tests/unit/common/test_api_key_tenant_scope.py`` and
``tests/api/test_api_key_tenant_scope_api.py`` do); it holds the **funnel** the
fix relies on, so a new tenant-resolution site cannot bypass it:

1. **Where a tenant context is born.** ``TenantContext(...)`` is constructed only
   inside the enumerated resolvers of ``app/common/auth.py``. Every class in
   ``app/`` is scanned — a new construction site anywhere fails, not just one in
   a file someone remembered to list.
2. **Every slug-to-tenant step states the key scope.** ``_membership_for_slug``
   takes ``key_scope`` keyword-only *without a default*, and every call site in
   ``app/`` passes it. A default would let the next caller forget it silently.
3. **Every tenant-in-path route reaches the resolver.** Each route of the
   assembled application whose path carries ``{tenant_slug}`` depends —
   transitively — on ``get_current_tenant``. A route binding the slug itself would
   skip the scope check.
4. **One predicate decides a scope.** Outside ``app/domain/models/auth.py`` no
   code compares against ``tenant_scope`` directly; REST and MCP both call
   ``api_key_scope_admits``. Two hand-written copies are the drift that let one
   surface enforce the scope and the other not.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
from typing import Any

import pytest

_APP = Path(__file__).resolve().parents[3] / "app"
_AUTH = _APP / "common" / "auth.py"
_PREDICATE_HOME = _APP / "domain" / "models" / "auth.py"

#: The resolvers allowed to build a ``TenantContext``. Both take their tenant
#: from ``_resolve_active_tenant`` / ``_membership_for_slug``, which apply the scope.
_CONTEXT_BUILDERS = {"get_current_tenant", "get_active_tenant_context"}


def _modules() -> list[tuple[Path, ast.Module]]:
    return [(path, ast.parse(path.read_text(encoding="utf-8"))) for path in sorted(_APP.rglob("*.py"))]


def _call_name(node: ast.Call) -> str | None:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _enclosing_functions(tree: ast.Module) -> dict[int, str]:
    """Map the id of every node to the name of the outermost function holding it."""
    owner: dict[int, str] = {}
    for top in ast.walk(tree):
        if isinstance(top, ast.FunctionDef | ast.AsyncFunctionDef):
            for node in ast.walk(top):
                owner.setdefault(id(node), top.name)
    return owner


def _tenant_context_sites() -> list[str]:
    sites = []
    for path, tree in _modules():
        owner = _enclosing_functions(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and _call_name(node) == "TenantContext":
                sites.append(f"{path.relative_to(_APP.parent)}:{node.lineno}:{owner.get(id(node), '<module>')}")
    return sites


def test_a_tenant_context_is_built_only_by_the_scope_checking_resolvers():
    sites = _tenant_context_sites()
    stray = [s for s in sites if not (s.startswith("app/common/auth.py:") and s.rsplit(":", 1)[1] in _CONTEXT_BUILDERS)]

    assert len(sites) >= len(_CONTEXT_BUILDERS), sites  # non-vacuity: the scan finds the real ones
    assert stray == [], (
        "TenantContext built outside the scope-checking resolvers — a tenant chosen there never "
        f"meets the API key's tenant_scope (#1817): {stray}"
    )


def test_membership_for_slug_takes_the_key_scope_keyword_only_without_a_default():
    from app.common import auth

    param = inspect.signature(auth._membership_for_slug).parameters.get("key_scope")

    assert param is not None, "_membership_for_slug must take the API key's scope (#1817)"
    assert param.kind is inspect.Parameter.KEYWORD_ONLY
    assert param.default is inspect.Parameter.empty


def test_the_scope_the_resolvers_read_is_the_field_authentication_sets():
    # ``_key_scope`` reads by name (``getattr``) so namespace doubles stay usable;
    # this pins that the name is the real field, or the read would be inert.
    from app.common import auth
    from app.domain.models.user import User

    assert isinstance(User.__dict__.get("api_key_tenant_scope"), property)
    assert '"api_key_tenant_scope"' in inspect.getsource(auth._key_scope)
    assert "with_api_key_tenant_scope" in inspect.getsource(
        __import__("app.domain.services.auth_service", fromlist=["AuthService"]).AuthService.authenticate_api_key
    )


def test_every_call_of_membership_for_slug_passes_the_key_scope():
    calls = []
    for path, tree in _modules():
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and _call_name(node) == "_membership_for_slug":
                passed = {kw.arg for kw in node.keywords}
                calls.append((f"{path.relative_to(_APP.parent)}:{node.lineno}", "key_scope" in passed))

    assert calls, "no call of _membership_for_slug found — the scan is looking in the wrong place"
    assert [site for site, ok in calls if not ok] == []


def _dependency_calls(dependant) -> set:  # noqa: ANN001 - fastapi.dependencies.models.Dependant
    found = set()
    for sub in dependant.dependencies:
        found.add(sub.call)
        found |= _dependency_calls(sub)
    return found


def _routes(routes, prefix: str = "", inherited: tuple = ()) -> list[tuple[str, Any, set]]:  # noqa: ANN001
    """Every leaf route as ``(full path, route, include-level dependency calls)``.

    FastAPI keeps included routers nested: the wrapper carries no ``path``, the
    prefix of the *including* router sits on ``include_context.prefix`` and the
    included router's own prefix is already baked into its leaf paths
    (pinned in ``tests/unit/test_frontend_calls_served_check.py``). Dependencies
    given to ``include_router(dependencies=...)`` live on the same context, not on
    the leaf's dependant, so they are carried down too.
    """
    from fastapi.routing import APIRoute

    out = []
    for route in routes:
        if isinstance(route, APIRoute):
            out.append((prefix + route.path_format, route, set(inherited)))
        elif hasattr(route, "original_router"):
            ctx = route.include_context
            extra = tuple(d.dependency for d in ctx.dependencies)
            out.extend(_routes(route.original_router.routes, prefix + ctx.prefix, inherited + extra))
    return out


def test_every_tenant_slug_route_depends_on_get_current_tenant() -> None:
    from app.common.auth import get_current_tenant
    from app.main import app

    slug_routes = [(path, r, deps) for path, r, deps in _routes(app.routes) if "{tenant_slug}" in path]
    missing = [
        f"{sorted(r.methods)} {path}"
        for path, r, deps in slug_routes
        if get_current_tenant not in (_dependency_calls(r.dependant) | deps)
    ]

    assert len(slug_routes) > 100, len(slug_routes)  # non-vacuity: the walk reaches nested routers
    assert missing == [], f"tenant-slug routes that bypass the scope-checking resolver: {missing}"


def _scope_comparisons(tree: ast.Module) -> list[int]:
    lines = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            operands = [node.left, *node.comparators]
            names = {n.id for n in operands if isinstance(n, ast.Name)} | {
                n.attr for n in operands if isinstance(n, ast.Attribute)
            }
            if "tenant_scope" in names:
                lines.append(node.lineno)
    return lines


def test_only_the_shared_predicate_compares_a_tenant_scope() -> None:
    offenders = [
        f"{path.relative_to(_APP.parent)}:{line}"
        for path, tree in _modules()
        if path != _PREDICATE_HOME
        for line in _scope_comparisons(tree)
    ]

    assert offenders == [], f"hand-written tenant_scope comparison — use api_key_scope_admits (#1817): {offenders}"


@pytest.mark.parametrize(
    "source",
    [
        "def f(t, tenant_scope):\n    return t.slug == tenant_scope\n",
        "def f(t, key):\n    return key.tenant_scope in (t.slug, t.key)\n",
    ],
    ids=["name", "attribute"],
)
def test_the_comparison_scan_sees_both_spellings(source: str):
    # Self-test: the scan must catch the pre-#1817 MCP spelling and its attribute form.
    assert _scope_comparisons(ast.parse(source)) != []
