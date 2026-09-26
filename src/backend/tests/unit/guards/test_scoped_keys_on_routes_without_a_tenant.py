"""#1851 — every route that resolves no tenant has decided what a tenant-scoped API key may do there.

#1817 made an API key's ``tenant_scope`` bind in the tenant resolvers. A route
that resolves *no* tenant never meets that check and authorises on the key
owner's whole account: create or join tenants, list every tenant, mint keys,
change the password, run the GDPR rights over every tenant. A key restricted to
one tenant must not be the whole account again.

The decision per route class (recorded in REQ-023):

* **account, credentials, privacy, tenant lifecycle** — refused: the route
  depends on ``require_account_principal`` (403 for a scoped key);
* **platform administration** — refused already: ``require_platform_admin`` /
  ``get_is_platform_admin`` answer "not an admin" for a scoped key (#1854);
* **tenant-resolving routes** — bound by the scope in the resolver (#1817);
* **the rest** — admitted, each listed below with its class: the identity read
  and the tenant list the Home Assistant integration uses (the list narrowed to
  the scope), and global reference data that carries no tenant's and no
  account's data.

A second class sits *inside* the tenant surface (security review of #1851): a
``/t/{slug}/`` write whose handler reads only ``ctx.user_key`` and never a tenant
key changes the caller's **account-wide** settings — notification delivery
targets, Web Push endpoints, preferences, onboarding state. The resolver admits a
scoped key for its own tenant, so without a refusal a key for tenant A redirects
the digest of every tenant of its owner. Those routes must depend on
``require_account_principal`` as well (``test_account_wide_writes_under_a_tenant_refuse_scoped_keys``).

This guard walks every leaf route of the assembled app (through the nested
``_IncludedRouter`` wrappers, include-level dependencies included) that depends
on ``get_current_user`` / ``get_current_user_optional``. Each must be refused,
tenant-resolving, platform-admin, or listed in :data:`_ADMITTED`; a listed route
that no longer exists fails too, so the list cannot rot.
"""

from __future__ import annotations

import ast
import inspect
import textwrap
from typing import Any

from fastapi import APIRouter, Depends, FastAPI
from fastapi.dependencies.utils import get_dependant
from fastapi.routing import APIRoute

_IDENTITY = "identity read: the Home Assistant integration reads its account here; the platform flag is scope-aware"
_NARROWED = "the account's tenant list, narrowed to the key's scope (the HA integration reads it to find its tenant)"
_CATALOGUE = "global reference data or a stateless calculation: no tenant's and no account's data"
_CATALOGUE_ADMIN_WRITE = (
    "global catalogue write gated by get_is_platform_admin, which is False for a scoped key: refused as a non-admin"
)
_PROMOTED = "a promoted pest image is a global release (status PROMOTED is the authorisation, REQ-010)"

_ADMITTED: dict[tuple[str, str], str] = {
    ("GET", "/api/v1/users/me"): _IDENTITY,
    ("GET", "/api/v1/tenants"): _NARROWED,
    **{
        ("GET", path): _CATALOGUE
        for path in (
            "/api/v1/hardiness-zones",
            "/api/v1/hardiness-zones/{zone}",
            "/api/v1/companion-planting/counts",
            "/api/v1/crop-rotation/counts",
            "/api/v1/crop-rotation/families/{family_key}/successors",
            "/api/v1/growth-phases",
            "/api/v1/growth-phases/{key}",
            "/api/v1/species/{species_key}/lifecycle",
            "/api/v1/species/{species_key}/phase-sequence",
            "/api/v1/location-types",
            "/api/v1/location-types/{key}",
            "/api/v1/profiles/requirements/{phase_key}",
            "/api/v1/profiles/nutrients/{phase_key}",
            "/api/v1/enrichment/sources",
            "/api/v1/enrichment/sources/{source_key}",
            "/api/v1/enrichment/sources/{source_key}/history",
            "/api/v1/enrichment/species/{species_key}/enrichments",
            "/api/v1/enrichment/health",
            "/api/v1/family-relationships/families/{family_key}/pest-risks",
            "/api/v1/family-relationships/families/{family_key}/compatible",
            "/api/v1/family-relationships/families/{family_key}/incompatible",
            "/api/v1/fish-species",
            "/api/v1/fish-species/by-temperature-zone/{zone}",
            "/api/v1/fish-species/{species_key}",
            "/api/v1/fish-species/{species_key}/compatible-plants",
            "/api/v1/ipm/pests",
            "/api/v1/ipm/pests/{key}",
            "/api/v1/ipm/pests/{key}/detail",
            "/api/v1/ipm/diseases",
            "/api/v1/ipm/diseases/{key}",
            "/api/v1/ipm/treatments",
            "/api/v1/ipm/treatments/{key}",
            "/api/v1/ipm/treatments/{key}/detail",
            "/api/v1/starter-kits",
            "/api/v1/starter-kits/{kit_id}",
            "/api/v1/import/templates/{entity_type}",
            "/api/v1/activities",
            "/api/v1/activities/{key}",
            "/api/v1/observations/status",
            "/api/v1/phase-definitions",
            "/api/v1/phase-definitions/{key}",
            "/api/v1/phase-definitions/{key}/sequences",
            "/api/v1/phase-definitions/{key}/species",
            "/api/v1/phase-sequences",
            "/api/v1/phase-sequences/{key}",
            "/api/v1/phase-sequences/{key}/species",
            "/api/v1/phase-sequences/{seq_key}/entries",
        )
    },
    **{
        ("POST", path): _CATALOGUE
        for path in (
            "/api/v1/calculations/vpd",
            "/api/v1/calculations/gdd",
            "/api/v1/calculations/photoperiod-transition",
            "/api/v1/calculations/sun-times",
            "/api/v1/calculations/sun-times-range",
            "/api/v1/calculations/slot-capacity",
            "/api/v1/calculations/vernalization",
        )
    },
    **{
        ("POST", path): _CATALOGUE_ADMIN_WRITE
        for path in (
            "/api/v1/family-relationships/pest-risk",
            "/api/v1/family-relationships/compatible",
            "/api/v1/family-relationships/incompatible",
        )
    },
    ("DELETE", "/api/v1/botanical-families/{key}"): _CATALOGUE_ADMIN_WRITE,
    ("GET", "/api/v1/ipm/pest-images/{contribution_id}"): _PROMOTED,
    ("GET", "/api/v1/ipm/pest-images/{contribution_id}/thumbnails/{size}"): _PROMOTED,
}

#: Routes another open change removes; exempt from the stale-entry check so the
#: two changes merge in either order.
_REMOVED_ELSEWHERE: dict[tuple[str, str], str] = {
    ("GET", "/api/v1/dashboard/summary"): "removed by #1853 (PR #1863)",
}


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


def _undecided(app: Any) -> tuple[list[tuple[str, str]], int]:
    from app.common import auth

    principal = {auth.get_current_user, auth.get_current_user_optional}
    decided = {
        auth.require_account_principal,
        auth.get_current_tenant,
        auth.get_active_tenant_key,
        auth.get_active_tenant_context,
        auth.require_platform_admin,
    }
    undecided, authenticated = [], 0
    for path, route, dependants in _routes(app.routes):
        calls = _calls(dependants)
        if not calls & principal:
            continue
        authenticated += 1
        if calls & decided:
            continue
        undecided.extend((method, path) for method in sorted(route.methods))
    return undecided, authenticated


def test_every_route_without_a_tenant_decides_on_scoped_keys() -> None:
    from app.main import app

    undecided, authenticated = _undecided(app)
    unexplained = sorted(r for r in undecided if r not in _ADMITTED and r not in _REMOVED_ELSEWHERE)
    stale = sorted(set(_ADMITTED) - set(undecided))

    assert authenticated > 700, authenticated  # non-vacuity: the walk reaches the nested routers
    assert unexplained == [], (
        "routes that resolve no tenant and never decided whether a tenant-scoped API key may act there "
        f"(#1851) — depend on require_account_principal or list the route with its class: {unexplained}"
    )
    assert stale == [], f"admitted routes that no longer take the undecided path — drop the entry: {stale}"


def test_an_undecided_route_is_flagged_through_an_include_level_dependency() -> None:
    from app.common.auth import get_current_user, require_account_principal

    router = APIRouter()

    @router.get("/me/thing")
    def thing() -> None: ...

    @router.get("/me/refused", dependencies=[Depends(require_account_principal)])
    def refused() -> None: ...

    app = FastAPI()
    app.include_router(router, prefix="/api/v1", dependencies=[Depends(get_current_user)])

    assert _undecided(app) == ([("GET", "/api/v1/me/thing")], 2)


#: ``/t/{slug}/`` READS of account-wide data a tenant-scoped key may keep: the
#: account's own UI settings, which carry no other tenant's data.
_ACCOUNT_WIDE_READS_ADMITTED: dict[tuple[str, str], str] = {
    ("GET", "/api/v1/t/{tenant_slug}/dashboard/widgets/catalog"): "the widget catalogue with per-user availability",
    ("GET", "/api/v1/t/{tenant_slug}/onboarding/state"): "the account's onboarding progress",
    ("GET", "/api/v1/t/{tenant_slug}/notifications/preferences"): "the account's own delivery settings",
    ("GET", "/api/v1/t/{tenant_slug}/user-preferences"): "the account's own UI preferences",
}


def _account_wide_tenant_writes(app: Any) -> tuple[list[tuple[str, str]], int]:
    """``/t/{slug}/`` routes whose handler reads ``ctx.user_key`` and no tenant key, not refusing scoped keys.

    Writes always; reads unless listed in :data:`_ACCOUNT_WIDE_READS_ADMITTED`
    (a read of the account's favourites returns keys from every tenant).
    """
    from app.common import auth

    offenders, tenant_writes = [], 0
    for path, route, dependants in _routes(app.routes):
        methods = sorted(route.methods - {"HEAD", "OPTIONS"})
        methods = [m for m in methods if (m, path) not in _ACCOUNT_WIDE_READS_ADMITTED]
        if "{tenant_slug}" not in path or not methods:
            continue
        tenant_writes += 1
        tree = ast.parse(textwrap.dedent(inspect.getsource(route.endpoint)))
        attrs = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
        names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | {
            a.arg for n in ast.walk(tree) if isinstance(n, ast.keyword) for a in [n] if a.arg
        }
        if "user_key" not in attrs or "tenant_key" in attrs or "tenant_key" in names:
            continue
        if auth.require_account_principal in _calls(dependants):
            continue
        offenders.extend((method, path) for method in methods)
    return offenders, tenant_writes


def test_account_wide_writes_under_a_tenant_refuse_scoped_keys() -> None:
    from app.main import app

    offenders, tenant_writes = _account_wide_tenant_writes(app)

    assert tenant_writes > 300, tenant_writes  # non-vacuity: the walk reaches the /t/ routers
    assert offenders == [], (
        "tenant-scoped routes that write (or read, unlisted) the caller's account-wide data without refusing a "
        f"tenant-scoped API key (#1851): {offenders}"
    )


def test_the_account_wide_write_scan_sees_user_only_handlers() -> None:
    from app.common.auth import get_current_tenant, require_account_principal

    router = APIRouter()

    @router.put("/t/{tenant_slug}/prefs")
    def prefs(ctx: Any = Depends(get_current_tenant)) -> None:
        return ctx.user_key

    @router.put("/t/{tenant_slug}/scoped")
    def scoped(ctx: Any = Depends(get_current_tenant)) -> None:
        return (ctx.user_key, ctx.tenant_key)

    @router.put("/t/{tenant_slug}/refused", dependencies=[Depends(require_account_principal)])
    def refused(ctx: Any = Depends(get_current_tenant)) -> None:
        return ctx.user_key

    app = FastAPI()
    app.include_router(router)

    assert _account_wide_tenant_writes(app) == ([("PUT", "/t/{tenant_slug}/prefs")], 3)
