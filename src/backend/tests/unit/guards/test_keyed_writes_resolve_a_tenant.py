"""#1864 — a write that addresses an object by key knows whose objects it may touch.

``POST /api/v1/substrates/batches/{batch_key}/assign-slot/{slot_key}`` depended on
``get_current_user`` only. Without a tenant the service had nothing to compare
the two keys with, and wrote a ``filled_with`` edge between any tenant's batch
and any tenant's slot.

**Why the #1619 hook did not catch it.** ``scripts/check_plant_scoped_route_tenant.py``
asks, for every *non-terminal* path key naming a collection in
``OWNERSHIP_VERIFIABLE_COLLECTIONS`` (``OWNABLE_PARAMS``: plant, run, observation,
fertilizer, tank, equipment, cultivar), whether the handler passes it on with a
tenant argument. ``batch_key`` and ``slot_key`` name collections outside that
allowlist, and ``slot_key`` is terminal — the route was outside its class twice
over. Its question is also "is the key scoped *given* a tenant"; this route had
no tenant to scope with.

**The class held here** is the precondition that question assumes: every write
route of the assembled app (walked through the nested ``_IncludedRouter``
wrappers, include-level dependencies included) that takes a key from its path
must resolve a tenant (``get_current_tenant`` / ``get_active_tenant_*``) or be
platform-admin-gated — or be listed in :data:`_NO_TENANT_WITH_REASON` because its
key addresses something that is not a tenant's (the caller's own account rows, a
global catalogue row gated inside the handler, an MCP tool name). A listed route
that stops matching fails too.

Whether each key is then *verified* within the tenant is the second half of the
class; the sweep for #1864 found three child-key routes that verify only the
parent (#1867), which carries that guard.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, FastAPI
from fastapi.dependencies.utils import get_dependant
from fastapi.routing import APIRoute

_ACCOUNT_OWNED = "the key addresses a row of the caller's own account; the service matches it against the user key"

_NO_TENANT_WITH_REASON: dict[tuple[str, str], str] = {
    ("DELETE", "/api/v1/auth/api-keys/{key_id}"): _ACCOUNT_OWNED,
    ("DELETE", "/api/v1/privacy/restrict/{restriction_key}"): _ACCOUNT_OWNED,
    ("DELETE", "/api/v1/privacy/consents/{purpose}"): "a consent purpose of the caller's own account, not a key",
    ("DELETE", "/api/v1/users/me/providers/{provider_key}"): _ACCOUNT_OWNED,
    ("DELETE", "/api/v1/users/me/sessions/{session_key}"): _ACCOUNT_OWNED,
    ("DELETE", "/api/v1/botanical-families/{key}"): (
        "global catalogue row (no tenant_key); the handler refuses anyone but a platform admin"
    ),
    ("POST", "/api/v1/mcp/tools/{tool_name}"): (
        "a tool name, not an object key; the MCP dispatcher resolves the tenant per call from the principal"
    ),
}

_WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _routes(routes: list[Any], prefix: str = "", inherited: tuple[Any, ...] = ()) -> list[tuple[str, APIRoute, list]]:
    out = []
    for route in routes:
        if isinstance(route, APIRoute):
            path = prefix + route.path_format
            out.append((path, route, [route.dependant, *(get_dependant(path=path, call=c) for c in inherited)]))
        elif hasattr(route, "original_router"):
            ctx = route.include_context
            calls = tuple(d.dependency for d in ctx.dependencies)
            out.extend(_routes(route.original_router.routes, prefix + ctx.prefix, inherited + calls))
    return out


def _calls(dependants: list[Any]) -> set[Any]:
    found: set[Any] = set()
    stack = list(dependants)
    while stack:
        dependant = stack.pop()
        found.add(dependant.call)
        stack.extend(dependant.dependencies)
    return found


def _keyed_writes_without_a_tenant(app: Any) -> tuple[list[tuple[str, str]], int]:
    from app.common import auth

    resolvers = {
        auth.get_current_tenant,
        auth.get_active_tenant_key,
        auth.get_active_tenant_context,
        auth.require_platform_admin,
    }
    offenders, keyed_writes = [], 0
    for path, route, dependants in _routes(app.routes):
        methods = sorted(route.methods & _WRITE_METHODS)
        path_keys = [p.name for dependant in dependants for p in dependant.path_params if p.name != "tenant_slug"]
        if not methods or not path_keys:
            continue
        keyed_writes += 1
        if _calls(dependants) & resolvers:
            continue
        offenders.extend((method, path) for method in methods)
    return offenders, keyed_writes


def test_every_keyed_write_resolves_a_tenant_or_says_why_not() -> None:
    from app.main import app

    offenders, keyed_writes = _keyed_writes_without_a_tenant(app)
    unexplained = sorted(set(offenders) - set(_NO_TENANT_WITH_REASON))
    stale = sorted(set(_NO_TENANT_WITH_REASON) - set(offenders))

    assert keyed_writes > 250, keyed_writes  # non-vacuity: the walk reaches the nested routers
    assert unexplained == [], (
        f"write routes that take a key from the path but resolve no tenant to verify it against (#1864): {unexplained}"
    )
    assert stale == [], f"listed routes that now resolve a tenant or are gone — drop the entry: {stale}"


def test_the_walk_flags_a_keyed_write_and_admits_a_resolved_one() -> None:
    from app.common.auth import get_active_tenant_context, get_current_user

    router = APIRouter()

    @router.post("/things/{thing_key}/link/{other_key}")
    def link(thing_key: str, other_key: str) -> None: ...

    @router.post("/things/{thing_key}/scoped", dependencies=[Depends(get_active_tenant_context)])
    def scoped(thing_key: str) -> None: ...

    @router.post("/things")
    def create() -> None: ...

    app = FastAPI()
    app.include_router(router, prefix="/api/v1", dependencies=[Depends(get_current_user)])

    assert _keyed_writes_without_a_tenant(app) == ([("POST", "/api/v1/things/{thing_key}/link/{other_key}")], 2)
