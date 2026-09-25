"""#1853 — a route that lets the caller name a tenant must resolve it through a membership check.

The defect: ``GET /api/v1/dashboard/summary?tenant_key=<key>`` depended on
``get_current_user`` only and handed the query value straight to
``DashboardService.get_summary``. The service filtered correctly — on a value the
caller chose. Tenant keys are not secrets (``TenantResponse.key``, assignment and
notification payloads carry them), so any signed-in caller, or an API key scoped
to another tenant (#1817), read any tenant's dashboard.

The class is not "the dashboard". It is **every route of the assembled app that
takes a tenant selector from the request without depending on a resolver that
proves the caller may act in that tenant**. This guard enumerates that class:

1. **Routes.** Every leaf ``APIRoute`` of ``app.main.app`` is walked through the
   nested ``_IncludedRouter.original_router`` wrappers (``include_router`` does not
   flatten, see ``test_api_key_scope_binds_every_tenant_resolution``). For each,
   every parameter of the whole dependant tree is inspected — path, query, header,
   cookie and body — by *name and alias*, and every field of a Pydantic body
   model, recursively. A selector a resolver declares itself — the
   ``{tenant_slug}`` path of ``get_current_tenant``, the ``X-Active-Tenant``
   header of ``get_active_tenant_*`` — is the checked one. Every *other* selector
   is foreign: a resolver on the same route binds its own parameter, never a
   sibling ``?tenant_key=``, so "the route has a resolver" is not enough. A
   foreign selector must be listed in :data:`_FOREIGN_SELECTORS_WITH_REASON`
   together with the gate that authorises it on that route.
2. **Raw reads.** A handler that reads the selector itself —
   ``request.query_params.get("tenant_key")``, ``body["tenant_key"]`` on an
   untyped ``dict`` body — has no parameter to inspect, so the walk in (1) cannot
   see it. Those spellings are held by an AST scan over ``app/api/`` for a
   subscript or ``.get()``/``.pop()`` whose key names a tenant selector; each hit
   is either absent or listed in :data:`_RAW_READS_WITH_REASON`.

Residual spelling neither check sees: a selector under a name that does not say
"tenant" (``owner=<tenant key>``). Naming is the only handle a static guard has;
the route test in ``tests/api/test_dashboard_summary_tenant_isolation.py`` holds
the behaviour for the one route that had the defect.
"""

from __future__ import annotations

import ast
import re
import typing
from pathlib import Path
from typing import Any

import pytest
from fastapi import APIRouter, Body, Depends, FastAPI, Header, Query
from fastapi.routing import APIRoute
from pydantic import BaseModel

_API = Path(__file__).resolve().parents[3] / "app" / "api"

#: A parameter or body field whose name or alias ends in one of these names a
#: tenant: ``tenant``, ``tenant_key``, ``tenant_id``, ``tenant_slug``, and the
#: prefixed forms (``default_tenant_key``, ``grantee_tenant_key``,
#: ``active_tenant_slug``, ``X-Active-Tenant``).
_SELECTOR = re.compile(r"tenant([_-]?(key|id|slug))?$", re.IGNORECASE)


def _resolvers() -> set[Any]:
    """The dependencies that turn a caller-named tenant into a checked one.

    ``get_current_tenant`` binds the ``/t/{tenant_slug}/`` path parameter,
    ``get_active_tenant_key`` / ``get_active_tenant_context`` the
    ``X-Active-Tenant`` header; both prove active membership and the API key's
    scope (``_membership_for_slug``). A selector these functions **declare
    themselves** is the checked one. Any *other* selector on the same route is
    not: the resolver binds its own parameter, never a sibling ``?tenant_key=``.
    """
    from app.common import auth

    return {auth.get_current_tenant, auth.get_active_tenant_key, auth.get_active_tenant_context}


#: Selectors that are not the resolver's own parameter, admitted with a reason.
#: ``(route path, parameter or body-field name)`` → (the dependency that must
#: gate the route, reason). An entry whose route or gate disappears fails the guard.
_FOREIGN_SELECTORS_WITH_REASON: dict[tuple[str, str], tuple[str, str]] = {
    **{
        (path, "tenant_key"): (
            "require_platform_admin",
            "platform-admin member management names any tenant by design; the role is the authorisation",
        )
        for path in (
            "/api/v1/admin/platform/tenants/{tenant_key}/members",
            "/api/v1/admin/platform/tenants/{tenant_key}/members/{membership_key}",
            "/api/v1/admin/platform/tenants/{tenant_key}/members/{membership_key}/role",
            "/api/v1/admin/platform/users/{user_key}/memberships",
        )
    },
    **{
        (path, "default_tenant_key"): (
            "require_platform_admin",
            "an OIDC provider's default tenant for new sign-ins is platform configuration",
        )
        for path in ("/api/v1/admin/oidc-providers", "/api/v1/admin/oidc-providers/{key}")
    },
    **{
        (path, "grantee_tenant_key"): (
            "get_active_tenant_context",
            "the grant is authorised on the caller's resolved tenant (ctx); the grantee is only "
            "the target of the edge and nothing about it is read back (#1092)",
        )
        for path in (
            "/api/v1/species/{key}/grants",
            "/api/v1/species/{species_key}/cultivars/{cultivar_key}/grants",
        )
    },
}


#: Raw reads of a selector-named key inside ``app/api/`` that are not a caller
#: choosing a tenant. ``(file relative to app/api, enclosing function)`` → reason.
_RAW_READS_WITH_REASON: dict[tuple[str, str], str] = {
    ("v1/admin/reference_images/router.py", "list_curation_images"): (
        "reads the tenant_key of a row the knowledge service returned, to display "
        "provenance on a platform-admin curation page; not request input"
    ),
    ("v1/attachments/token_router.py", "redeem_token"): (
        "reads the tenant_key from an HMAC-verified download token the backend "
        "signed, and refuses the token unless the storage key lives under it (SEC-001)"
    ),
}


def _routes(routes: list[Any], prefix: str = "", inherited: tuple[Any, ...] = ()) -> list[tuple[str, APIRoute, list]]:
    """Every leaf route as ``(full path, route, dependants)``.

    ``dependants`` is the leaf's own dependant plus one per dependency given to
    ``include_router(dependencies=...)`` on the way down: FastAPI keeps those on
    the include context, not on the leaf, but their parameters reach the request
    all the same.
    """
    from fastapi.dependencies.utils import get_dependant

    out = []
    for route in routes:
        if isinstance(route, APIRoute):
            path = prefix + route.path_format
            extra = [get_dependant(path=path, call=call) for call in inherited]
            out.append((path, route, [route.dependant, *extra]))
        elif hasattr(route, "original_router"):
            ctx = route.include_context
            calls = tuple(d.dependency for d in ctx.dependencies)
            out.extend(_routes(route.original_router.routes, prefix + ctx.prefix, inherited + calls))
    return out


def _dependency_calls(dependant: Any) -> set[Any]:
    found = set()
    for sub in dependant.dependencies:
        found.add(sub.call)
        found |= _dependency_calls(sub)
    return found


def _model_field_names(annotation: Any, seen: set[type]) -> list[str]:
    names: list[str] = []
    candidates = [annotation, *typing.get_args(annotation)]
    for candidate in candidates:
        if isinstance(candidate, type) and issubclass(candidate, BaseModel):
            if candidate in seen:
                continue
            seen.add(candidate)
            for name, field in candidate.model_fields.items():
                names.append(name)
                if field.alias:
                    names.append(field.alias)
                names.extend(_model_field_names(field.annotation, seen))
        elif candidate is not annotation and typing.get_args(candidate):
            names.extend(_model_field_names(candidate, seen))
    return names


def _parameters(dependant: Any) -> list[tuple[str, Any]]:
    """Every parameter name and alias of the dependant tree, with the callable declaring it."""
    out: list[tuple[str, Any]] = []
    for kind in ("path_params", "query_params", "header_params", "cookie_params", "body_params"):
        for param in getattr(dependant, kind):
            names = [param.name, param.alias]
            if kind == "body_params":
                names.extend(_model_field_names(param.field_info.annotation, set()))
            out.extend((name, dependant.call) for name in names if name)
    for sub in dependant.dependencies:
        out.extend(_parameters(sub))
    return out


def _all_parameters(dependants: list[Any]) -> list[tuple[str, Any]]:
    return [pair for dependant in dependants for pair in _parameters(dependant)]


def _all_calls(dependants: list[Any]) -> set[Any]:
    return {d.call for d in dependants} | {c for d in dependants for c in _dependency_calls(d)}


def _foreign_selectors(dependants: list[Any]) -> set[str]:
    """Selector names on a route that no resolver declared itself."""
    resolvers = _resolvers()
    names_by_owner: dict[str, set[Any]] = {}
    for name, owner in _all_parameters(dependants):
        if _SELECTOR.search(name):
            names_by_owner.setdefault(name, set()).add(owner)
    # A name counts as the resolver's own only if *every* declaration of it is a
    # resolver's: FastAPI merges same-named parameters, so a handler repeating
    # ``tenant_slug`` would share the value, but a handler reading its own
    # ``?tenant_key=`` next to ``get_current_tenant`` is exactly the defect.
    return {name for name, owners in names_by_owner.items() if not owners <= resolvers}


def _selector_routes(app: Any) -> list[tuple[str, APIRoute, list]]:
    return [
        (path, route, dependants)
        for path, route, dependants in _routes(app.routes)
        if any(_SELECTOR.search(name) for name, _ in _all_parameters(dependants))
    ]


def _unexplained(app: Any, allowed: dict[tuple[str, str], tuple[str, str]]) -> list[str]:
    out = []
    for path, route, dependants in _routes(app.routes):
        calls = {getattr(c, "__name__", None) for c in _all_calls(dependants)}
        for name in sorted(_foreign_selectors(dependants)):
            entry = allowed.get((path, name))
            if entry is None or entry[0] not in calls:
                out.append(f"{sorted(route.methods)} {path} :: {name}")
    return out


def test_every_tenant_selector_is_a_resolver_parameter_or_explained() -> None:
    from app.main import app

    selector_routes = _selector_routes(app)
    unexplained = _unexplained(app, _FOREIGN_SELECTORS_WITH_REASON)

    # Non-vacuity: the walk reaches the nested /t/{slug}/ routers and the
    # header-bound catalogues ...
    assert len(selector_routes) > 400, len(selector_routes)
    assert any("/species" in path for path, _, _ in selector_routes)
    # ... and it sees the selectors that are *not* a resolver's own: every
    # allowlisted one is found on its route (stale entries fail here).
    seen = {(path, name) for path, _, dependants in _routes(app.routes) for name in _foreign_selectors(dependants)}
    assert sorted(set(_FOREIGN_SELECTORS_WITH_REASON) - seen) == []
    assert unexplained == [], (
        f"routes that take a tenant selector from the request that no resolver checks (#1853): {unexplained}"
    )


def test_only_routes_and_included_routers_are_mounted() -> None:
    # The walk sees APIRoute leaves only. A websocket route or a mounted sub-app
    # would carry parameters it never inspects — make adding one a decision here.
    from starlette.routing import Mount, Route, WebSocketRoute

    from app.main import app

    def others(routes: list[Any]) -> list[str]:
        out = []
        for route in routes:
            if isinstance(route, APIRoute):
                continue
            if hasattr(route, "original_router"):
                out.extend(others(route.original_router.routes))
            elif isinstance(route, WebSocketRoute | Mount) or not isinstance(route, Route):
                out.append(f"{type(route).__name__} {getattr(route, 'path', '?')}")
            elif not route.path.endswith(("/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc")):
                out.append(f"Route {route.path}")
        return out

    assert others(app.routes) == []


# --- the predicate sees every parameter spelling ------------------------------


class _Inner(BaseModel):
    tenant_key: str


class _Outer(BaseModel):
    target: _Inner


class _Flat(BaseModel):
    grantee_tenant_key: str


def _query_dep(tenant_key: str = Query("")) -> str:
    return tenant_key


def _unguarded_app() -> FastAPI:
    router = APIRouter(prefix="/probe")

    @router.get("/query")
    def by_query(tenant_key: str = Query("")) -> None: ...

    @router.get("/aliased")
    def by_alias(t: str = Query("", alias="tenant")) -> None: ...

    @router.get("/path/{tenant_id}")
    def by_path(tenant_id: str) -> None: ...

    @router.get("/header")
    def by_header(slug: str | None = Header(None, alias="X-Active-Tenant")) -> None: ...

    @router.post("/body-flat")
    def by_flat_body(payload: _Flat) -> None: ...

    @router.post("/body-nested")
    def by_nested_body(payload: _Outer) -> None: ...

    @router.post("/body-list")
    def by_list_body(payload: list[_Inner] = Body(...)) -> None: ...

    @router.get("/via-dependency")
    def by_dependency(key: str = Depends(_query_dep)) -> None: ...

    @router.get("/unrelated")
    def unrelated(name: str = Query("")) -> None: ...

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    return app


def test_the_predicate_flags_every_parameter_spelling_of_a_selector() -> None:
    flagged = {line.split(" ", 1)[1].split(" :: ")[0] for line in _unexplained(_unguarded_app(), {})}

    assert flagged == {
        "/api/v1/probe/query",
        "/api/v1/probe/aliased",
        "/api/v1/probe/path/{tenant_id}",
        "/api/v1/probe/header",
        "/api/v1/probe/body-flat",
        "/api/v1/probe/body-nested",
        "/api/v1/probe/body-list",
        "/api/v1/probe/via-dependency",
    }


@pytest.mark.parametrize("where", ["route", "include"])
def test_the_resolvers_own_parameter_is_admitted(where: str) -> None:
    from app.common.auth import get_current_tenant

    router = APIRouter(dependencies=[Depends(get_current_tenant)] if where == "route" else [])

    @router.get("/t/{tenant_slug}/thing")
    def thing() -> None: ...

    app = FastAPI()
    app.include_router(router, dependencies=[Depends(get_current_tenant)] if where == "include" else [])

    assert _selector_routes(app), "the probe route must be seen as taking a selector"
    assert _unexplained(app, {}) == []


def test_a_sibling_selector_next_to_a_resolver_is_flagged() -> None:
    # The #1853 shape on a tenant route: the resolver checks the slug, the
    # handler reads its own ``?tenant_key=``. The resolver does not bind that.
    from app.common.auth import get_current_tenant

    router = APIRouter(dependencies=[Depends(get_current_tenant)])

    @router.get("/t/{tenant_slug}/thing")
    def thing(tenant_key: str = Query("")) -> None: ...

    app = FastAPI()
    app.include_router(router)

    assert _unexplained(app, {}) == ["['GET'] /t/{tenant_slug}/thing :: tenant_key"]


def test_a_selector_on_an_include_level_dependency_is_flagged() -> None:
    # ``include_router(dependencies=...)`` keeps the dependency on the include
    # context, not on the leaf's dependant; its parameters still reach the request.
    router = APIRouter()

    @router.get("/thing")
    def thing() -> None: ...

    app = FastAPI()
    app.include_router(router, prefix="/api/v1", dependencies=[Depends(_query_dep)])

    assert _unexplained(app, {}) == ["['GET'] /api/v1/thing :: tenant_key"]


def test_an_allowlisted_selector_needs_its_gate() -> None:
    router = APIRouter()

    @router.get("/admin/{tenant_key}")
    def admin(tenant_key: str) -> None: ...

    app = FastAPI()
    app.include_router(router)
    allowed = {("/admin/{tenant_key}", "tenant_key"): ("require_platform_admin", "test")}

    assert _unexplained(app, allowed) == ["['GET'] /admin/{tenant_key} :: tenant_key"]


# --- raw reads the parameter walk cannot see ----------------------------------


def _raw_selector_reads(source: str) -> list[tuple[str, int]]:
    tree = ast.parse(source)
    owner: dict[int, str] = {}
    for top in ast.walk(tree):
        if isinstance(top, ast.FunctionDef | ast.AsyncFunctionDef):
            for node in ast.walk(top):
                owner[id(node)] = top.name  # innermost wins: ast.walk visits outer first
    hits = []
    for node in ast.walk(tree):
        key = None
        if isinstance(node, ast.Subscript) and isinstance(node.ctx, ast.Load) and isinstance(node.slice, ast.Constant):
            key = node.slice.value
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in {"get", "getlist", "pop"}
            and node.args
            and isinstance(node.args[0], ast.Constant)
        ):
            key = node.args[0].value
        if isinstance(key, str) and _SELECTOR.search(key):
            hits.append((owner.get(id(node), "<module>"), node.lineno))
    return hits


@pytest.mark.parametrize(
    "source",
    [
        "def h(request):\n    return request.query_params.get('tenant_key')\n",
        "def h(request):\n    return request.query_params['tenant_slug']\n",
        "async def h(request):\n    body = await request.json()\n    return body['tenant_key']\n",
        "def h(payload: dict):\n    return payload.pop('tenant_id')\n",
        "def h(request):\n    return request.headers.get('X-Active-Tenant')\n",
    ],
)
def test_the_raw_read_scan_flags_each_spelling(source: str) -> None:
    assert _raw_selector_reads(source) == [("h", 2 if source.count("\n") == 2 else 3)]


@pytest.mark.parametrize(
    "source",
    [
        "def h(doc, ctx):\n    doc['tenant_key'] = ctx.tenant_key\n",
        "def h(doc):\n    del doc['tenant_key']\n",
    ],
)
def test_the_raw_read_scan_ignores_writes(source: str) -> None:
    # Stamping the resolved tenant onto a document is the correct pattern, not a read.
    assert _raw_selector_reads(source) == []


def test_no_api_handler_reads_a_tenant_selector_raw() -> None:
    found: dict[tuple[str, str], int] = {}
    for path in sorted(_API.rglob("*.py")):
        rel = str(path.relative_to(_API))
        for func, line in _raw_selector_reads(path.read_text(encoding="utf-8")):
            found.setdefault((rel, func), line)

    unexplained = {site: line for site, line in found.items() if site not in _RAW_READS_WITH_REASON}
    stale = sorted(set(_RAW_READS_WITH_REASON) - set(found))

    assert unexplained == {}, f"handler reads a tenant selector without a resolver (#1853): {unexplained}"
    assert stale == [], f"allowlisted raw read no longer exists — drop the entry: {stale}"
