"""Every write route of `/admin/oidc-providers` consults the scope check (#1477).

A guard opted into at the call site drifts between siblings — #948 repaired two
of four routes of the same shape and the other two stayed open for months. The
scope check is exactly that shape: `create_provider` and `update_provider` each
call it by hand, and a third write route added by copy-paste would inherit
nothing.

So the wiring is asserted over the module's AST rather than trusted. Both forms
count, because the two are the same predicate with different reporting:

* `require_supported_scopes` — refuses (422); what a route that STORES a
  configuration must call.
* `check_provider_scopes` — reports; what `/{key}/test` calls, since refusing an
  already-stored configuration there would hide the very finding the endpoint
  exists to deliver.

`delete_provider` is exempt: removing a provider cannot leave a broken one
behind. The exemption is listed explicitly, so widening it is a visible edit.

Since #1883 the storing routes delegate to ``OidcProviderAdminService`` (the step-up
lives there), so the check is looked for one call deep: a route counts when it calls
the check itself or calls a method of that service that does. Read off both ASTs —
the delegation is not trusted by name.
"""

from __future__ import annotations

import ast
import inspect

import pytest

import app.api.v1.admin.oidc_providers.router as router_module
import app.domain.services.oidc_provider_admin_service as service_module

WRITE_METHODS = {"post", "put", "patch", "delete"}
SCOPE_CHECK_CALLS = {"require_supported_scopes", "check_provider_scopes"}
#: Write routes that legitimately never consult the check.
EXEMPT = {"delete_provider"}


def _module_tree() -> ast.Module:
    return ast.parse(inspect.getsource(router_module))


def _route_methods(func: ast.FunctionDef) -> set[str]:
    """The HTTP methods this handler is mounted with, read off its decorators."""
    methods: set[str] = set()
    for decorator in func.decorator_list:
        if not isinstance(decorator, ast.Call):
            continue
        target = decorator.func
        if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "router":
            methods.add(target.attr)
    return methods


def _write_handlers() -> list[ast.FunctionDef]:
    return [
        node
        for node in ast.walk(_module_tree())
        if isinstance(node, ast.FunctionDef) and _route_methods(node) & WRITE_METHODS
    ]


def _calls_directly(func: ast.FunctionDef) -> bool:
    return any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in SCOPE_CHECK_CALLS
        for node in ast.walk(func)
    )


def _service_methods_that_check() -> set[str]:
    """The ``OidcProviderAdminService`` methods whose own body calls the check."""
    tree = ast.parse(inspect.getsource(service_module.OidcProviderAdminService))
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and _calls_directly(node)}


def _calls_the_check(func: ast.FunctionDef) -> bool:
    checking = _service_methods_that_check()
    return _calls_directly(func) or any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "service"
        and node.func.attr in checking
        for node in ast.walk(func)
    )


def test_the_service_side_of_the_sweep_is_not_empty() -> None:
    """The control for the one-call-deep lookup: both storing service methods call the check."""
    assert {"create_provider", "update_provider"} <= _service_methods_that_check()


def test_the_sweep_finds_the_write_routes() -> None:
    """The control: a sweep over an empty set proves nothing.

    Named handlers, not a count — a renamed route should surface here rather than
    silently shrink the set the assertion below runs over.
    """
    found = {func.name for func in _write_handlers()}
    assert {"create_provider", "update_provider", "delete_provider", "test_provider"} <= found, found


@pytest.mark.parametrize("name", ["create_provider", "update_provider", "test_provider"])
def test_each_storing_write_route_consults_the_scope_check(name: str) -> None:
    handler = next(func for func in _write_handlers() if func.name == name)
    assert _calls_the_check(handler), (
        f"{name} writes an OIDC provider configuration without consulting the "
        f"#1477 scope check ({' or '.join(sorted(SCOPE_CHECK_CALLS))})."
    )


def test_no_unlisted_write_route_skips_the_check() -> None:
    """Catches the route that does not exist yet — the drift this guard is for."""
    offenders = [func.name for func in _write_handlers() if func.name not in EXEMPT and not _calls_the_check(func)]
    assert not offenders, (
        "New write route(s) on /admin/oidc-providers without the #1477 scope check: "
        f"{', '.join(offenders)}. Call `require_supported_scopes` before storing, or "
        "add the route to EXEMPT with a reason."
    )
