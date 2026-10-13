"""Every tenant resolver records the tenant on the request's telemetry (#2130).

The class: a function in ``app/common/auth.py`` that turns the caller's choice into
a tenant — it calls ``_membership_for_slug`` (the path and header surfaces) or
``_resolve_active_tenant`` (the header-or-personal resolution). Each such resolver
that a route depends on must call ``bind_tenant`` so the request's log lines,
error events and dispatched tasks name the tenant (as ``ten_…``). The two
helpers themselves are excluded — they are not dependencies, their callers are.

Measured at #2130: three resolvers (``get_current_tenant``,
``get_active_tenant_key``, ``get_active_tenant_context``), none bound anything.
A fourth resolver added without the call would log without a tenant, silently;
this makes it a red build instead.

Limits: a resolver living outside ``auth.py``, or one resolving a tenant through
another helper, is not seen (the MCP dispatcher binds on its own, covered by
``tests/unit/mcp_server/test_audit_row_correlation.py`` and the dispatcher).
"""

from __future__ import annotations

import ast
from pathlib import Path

AUTH = Path(__file__).resolve().parents[3] / "app" / "common" / "auth.py"
_HELPERS = frozenset({"_membership_for_slug", "_resolve_active_tenant"})
_BINDER = "bind_tenant"


def _called_names(node: ast.AST) -> set[str]:
    names = set()
    for call in ast.walk(node):
        if isinstance(call, ast.Call):
            func = call.func
            names.add(func.id if isinstance(func, ast.Name) else getattr(func, "attr", ""))
    return names


def resolvers_without_binding(source: str) -> tuple[list[str], list[str]]:
    """``(resolvers, offenders)`` of a module's source: resolvers found, and those not binding."""
    resolvers, offenders = [], []
    for node in ast.parse(source).body:
        if not isinstance(node, ast.FunctionDef) or node.name in _HELPERS:
            continue
        called = _called_names(node)
        if called & _HELPERS:
            resolvers.append(node.name)
            if _BINDER not in called:
                offenders.append(node.name)
    return resolvers, offenders


def test_every_tenant_resolver_binds_the_tenant() -> None:
    resolvers, offenders = resolvers_without_binding(AUTH.read_text())

    # Non-vacuity: the class is not empty, and it still holds the three it was written for.
    assert {"get_current_tenant", "get_active_tenant_key", "get_active_tenant_context"} <= set(resolvers)
    assert offenders == [], f"tenant resolvers that never call {_BINDER}: {offenders}"


def test_the_detector_flags_a_resolver_without_the_binding() -> None:
    source = (
        "def get_current_tenant(slug, user, service):\n"
        "    tenant, membership = _membership_for_slug(service, user.key, slug, key_scope=None)\n"
        "    return tenant\n"
        "def get_other(user, service, slug):\n"
        "    resolved = _resolve_active_tenant(user, service, slug)\n"
        "    bind_tenant(resolved.key)\n"
        "    return resolved\n"
        "def _resolve_active_tenant(user, service, slug):\n"
        "    return _membership_for_slug(service, user.key, slug, key_scope=None)\n"
    )

    resolvers, offenders = resolvers_without_binding(source)

    assert resolvers == ["get_current_tenant", "get_other"]
    assert offenders == ["get_current_tenant"]
