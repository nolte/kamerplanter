"""MT-035 (#2131) — every route that answers with a list reads a bounded window, or says why it need not.

The defect class: a route whose response is ``list[...]`` and whose query reads
every row the filter matches. For a seeded catalogue that is a few hundred rows
and harmless. For a collection that grows with a tenant's activity — tasks,
conversations, invitations, observations — or with the platform — tenants,
users — the response, the database scan and the Pydantic serialisation all grow
without bound, one request at a time. The audit counted ~90 such routes beside a
shared ``get_pagination`` dependency that already capped ``limit`` at 200.

**Predicate** — every leaf ``APIRoute`` of ``app.main.app``, walked through the
nested ``_IncludedRouter.original_router`` wrappers (``include_router`` does not
flatten, see ``test_tenant_selector_routes_depend_on_a_resolver``), whose
``response_model`` is ``list[...]``. A member must

* reach one of :data:`app.common.pagination.PAGINATION_DEPENDENCIES` anywhere in
  its dependency tree (the leaf's own dependant or an ``include_router``-level
  dependency), compared by identity, or
* be classified in :data:`_CLASSIFIED` with a kind and a reason.

The predicate deliberately does **not** try to decide "backed by a tenant-scoped
repository" from the route: that would need the call graph from handler to AQL,
and every list route of a catalogue is just as easy to classify by hand as to
derive. Every list route is a member; the catalogues are the classified ones.

**Kinds** (:data:`_KINDS`):

``catalogue``         a global or hybrid reference catalogue, seeded and curated —
                      it grows with the seed data, not with a tenant's activity.
``per-parent``        the children of one parent document the route resolves first;
                      the parent bounds them (a workflow's phases, a run's plants).
``per-subject``       the caller's own rows over a fixed vocabulary or a retention
                      window (consents per purpose, sessions, linked providers).
``tenant-config``     configuration rows a person creates one by one (actuators,
                      rules, connections) — they do not accrue with time.
``computed``          a computed answer whose length an enum, a fixed window or the
                      request bounds (stats per method, chart of the last 60 tests).
``capped-query``      the route takes its own ``limit`` query parameter with an upper
                      bound. **Checked**: the parameter and its ``le`` must exist.
``external``          rows another system returns (Home Assistant, enrichment
                      sources); their size is that system's.
``write-echo``        a ``PUT``/``POST`` answering with the rows its body carried.
``remaining``         grows with tenant data and is **not** bounded yet. Pinned by
                      count (:data:`_REMAINING_COUNT`): a conversion lowers the
                      number, a new route cannot join without changing it.

A classification whose route is gone, no longer a list, or now paginated fails
(stale entries cannot outlive what they excused).

**What it cannot see**: a list wrapped in an object (``{"items": [...]}``) — the
envelope routes carry their own ``limit`` today; a route without a
``response_model`` that returns a list (``response_class=JSONResponse``); and
whether a paginated route's repository really pushes ``LIMIT`` into its query
rather than slicing in Python (the route and repository tests own that).
"""

from __future__ import annotations

import typing
from typing import Any

import pytest
from fastapi import APIRouter, Depends, FastAPI, Query
from fastapi.routing import APIRoute

from app.common.pagination import (
    PAGINATION_DEPENDENCIES,
    CursorPaginationParams,
    PaginationParams,
    get_cursor_pagination,
    get_pagination,
)

_KINDS = frozenset(
    {
        "catalogue",
        "per-parent",
        "per-subject",
        "tenant-config",
        "computed",
        "capped-query",
        "external",
        "write-echo",
        "remaining",
    }
)

_V1 = "/api/v1"
_T = f"{_V1}/t/{{tenant_slug}}"

#: ``(method, full path)`` → ``(kind, reason)``. Ordered as the app mounts them.
_CLASSIFIED: dict[tuple[str, str], tuple[str, str]] = {
    # ── platform administration ────────────────────────────────────────────
    ("GET", f"{_V1}/admin/ha-entity-grants/tenants/{{tenant_key}}"): (
        "per-parent",
        "one tenant's Home Assistant entity allowlist, curated entity by entity by a platform admin (#2112)",
    ),
    ("GET", f"{_V1}/admin/oidc-providers"): ("tenant-config", "OIDC providers configured by a platform admin"),
    ("GET", f"{_V1}/admin/platform/security-audit"): ("capped-query", "newest rows first, ?limit ≤ MAX_READ_LIMIT"),
    ("GET", f"{_V1}/admin/platform/tenants/{{tenant_key}}/members"): (
        "per-parent",
        "the members of one tenant; same bound as the tenant member list (see remaining entry)",
    ),
    ("GET", f"{_V1}/admin/platform/users/{{user_key}}/memberships"): (
        "per-parent",
        "the memberships of one user — one per tenant the user belongs to",
    ),
    ("GET", f"{_V1}/admin/glossary/terms"): ("catalogue", "the glossary, curated by platform admins"),
    # ── the caller's own account ───────────────────────────────────────────
    ("GET", f"{_V1}/auth/api-keys"): ("per-subject", "the caller's own API keys, created one by one"),
    ("GET", f"{_V1}/auth/oauth/providers"): ("tenant-config", "the enabled sign-in providers of the installation"),
    ("GET", f"{_V1}/privacy/consents"): ("per-subject", "one consent record per processing purpose (NFR-011)"),
    ("GET", f"{_V1}/privacy/mcp-activity"): (
        "computed",
        "the caller's MCP audit rows, capped at 200 inside the handler (limit=200)",
    ),
    ("GET", f"{_V1}/users/me/providers"): ("per-subject", "the caller's linked sign-in providers, one per provider"),
    ("GET", f"{_V1}/users/me/sessions"): (
        "per-subject",
        "the caller's live refresh-token families; expired ones are purged by retention",
    ),
    ("GET", f"{_V1}/tenants"): ("per-subject", "the tenants the caller is a member of"),
    # ── global and hybrid catalogues ───────────────────────────────────────
    ("GET", f"{_V1}/botanical-families/{{key}}/species"): (
        "catalogue",
        "the species of one botanical family: seed catalogue plus the tenant's own rows",
    ),
    ("GET", f"{_V1}/hardiness-zones"): ("catalogue", "the USDA hardiness zones, a fixed set"),
    ("GET", f"{_V1}/companion-planting/species/{{species_key}}/compatible"): (
        "catalogue",
        "companion edges of one species in the seeded companion graph",
    ),
    ("GET", f"{_V1}/companion-planting/species/{{species_key}}/incompatible"): (
        "catalogue",
        "antagonist edges of one species in the seeded companion graph",
    ),
    ("GET", f"{_V1}/crop-rotation/families/{{family_key}}/successors"): (
        "catalogue",
        "rotation successors of one family in the seeded rotation graph",
    ),
    ("GET", f"{_V1}/species/{{species_key}}/cultivars"): (
        "catalogue",
        "the cultivars of one species: seed catalogue plus the tenant's own rows",
    ),
    ("GET", f"{_V1}/species/{{species_key}}/cultivars/{{cultivar_key}}/grants"): (
        "per-parent",
        "the tenants one cultivar is shared with, granted one by one",
    ),
    ("GET", f"{_V1}/growth-phases"): ("catalogue", "the phases of one lifecycle definition"),
    ("GET", f"{_V1}/location-types"): ("catalogue", "the location-type vocabulary"),
    ("GET", f"{_V1}/species/{{key}}/grants"): ("per-parent", "the tenants one species is shared with"),
    ("GET", f"{_V1}/enrichment/sources"): ("catalogue", "the configured external enrichment sources"),
    ("GET", f"{_V1}/enrichment/sources/{{source_key}}/history"): ("capped-query", "?limit ≤ 100 sync runs"),
    ("GET", f"{_V1}/enrichment/species/{{species_key}}/enrichments"): (
        "per-parent",
        "the external mappings of one species, one per source",
    ),
    ("POST", f"{_V1}/enrichment/search"): ("external", "search hits the external source returns"),
    ("GET", f"{_V1}/enrichment/health"): ("computed", "one health row per configured source"),
    ("GET", f"{_V1}/family-relationships/families/{{family_key}}/pest-risks"): (
        "catalogue",
        "pest edges of one family in the seeded graph",
    ),
    ("GET", f"{_V1}/family-relationships/families/{{family_key}}/compatible"): (
        "catalogue",
        "compatible families of one family in the seeded graph",
    ),
    ("GET", f"{_V1}/family-relationships/families/{{family_key}}/incompatible"): (
        "catalogue",
        "incompatible families of one family in the seeded graph",
    ),
    ("GET", f"{_V1}/fish-species"): ("catalogue", "the seeded aquaponics fish catalogue"),
    ("GET", f"{_V1}/fish-species/by-temperature-zone/{{zone}}"): (
        "catalogue",
        "the seeded fish catalogue filtered by one zone",
    ),
    ("GET", f"{_V1}/starter-kits"): ("catalogue", "the seeded starter kits"),
    ("GET", f"{_V1}/phase-definitions/{{key}}/sequences"): (
        "catalogue",
        "the phase sequences using one phase definition",
    ),
    ("GET", f"{_V1}/phase-definitions/{{key}}/species"): (
        "catalogue",
        "the species whose lifecycle uses one phase definition",
    ),
    ("GET", f"{_V1}/phase-sequences/{{key}}/species"): ("catalogue", "the species assigned one phase sequence"),
    ("GET", f"{_V1}/phase-sequences/{{seq_key}}/entries"): ("per-parent", "the entries of one phase sequence"),
    ("POST", f"{_V1}/phase-sequences/{{seq_key}}/entries/reorder"): (
        "write-echo",
        "answers with the entries it reordered",
    ),
    ("GET", f"{_V1}/public/glossary/terms"): ("catalogue", "the public glossary"),
    ("GET", f"{_T}/glossary/terms"): ("catalogue", "the glossary, curated by platform admins"),
    ("GET", f"{_T}/service-accounts"): (
        "tenant-config",
        "service accounts a lead creates one by one, capped by TENANT_MAX_SERVICE_ACCOUNTS (default 20, #2137)",
    ),
    # ── computations ───────────────────────────────────────────────────────
    ("POST", f"{_V1}/calculations/sun-times-range"): (
        "computed",
        "one row per day of the requested range; the range is capped at MAX_SUN_TIMES_RANGE_DAYS",
    ),
    ("GET", f"{_V1}/plant-instances/{{plant_key}}/phases/history"): (
        "per-parent",
        "the phase transitions of one plant",
    ),
    ("GET", f"{_V1}/substrates/{{substrate_key}}/batches"): ("per-parent", "the batches of one substrate"),
    ("GET", f"{_V1}/care-reminders/plants/{{plant_key}}/history"): ("capped-query", "?limit ≤ 200 confirmations"),
    # ── tenant membership ──────────────────────────────────────────────────
    ("GET", f"{_V1}/tenants/{{tenant_slug}}/members"): (
        "remaining",
        "grows with the organisation; max_members is not enforced (MT-037)",
    ),
    ("GET", f"{_V1}/tenants/{{tenant_slug}}/assignments"): (
        "remaining",
        "location assignments of a tenant; grows with members x locations",
    ),
    # ── sites, locations, slots ────────────────────────────────────────────
    ("GET", f"{_T}/sites/{{key}}/location-tree"): (
        "per-parent",
        "the whole location tree of one site: the UI renders the tree, a window would cut it",
    ),
    ("GET", f"{_T}/sites/{{key}}/sensors"): ("per-parent", "the sensors of one site"),
    ("GET", f"{_T}/locations"): (
        "per-parent",
        "the locations of one site (or children of one location); the physical layout bounds it",
    ),
    ("GET", f"{_T}/locations/{{key}}/children"): ("per-parent", "the child locations of one location"),
    ("GET", f"{_T}/locations/{{key}}/sensors"): ("per-parent", "the sensors of one location"),
    ("GET", f"{_T}/slots"): ("per-parent", "the slots of one location"),
    ("GET", f"{_T}/locations/{{location_key}}/actuators"): ("per-parent", "the actuators of one location"),
    ("GET", f"{_T}/equipment/by-location/{{location_key}}"): ("per-parent", "the equipment of one location"),
    # ── plants and runs ────────────────────────────────────────────────────
    ("GET", f"{_T}/plant-instances/{{key}}/active-channels"): (
        "computed",
        "the delivery channels of one plant's active nutrient plan phase",
    ),
    ("GET", f"{_T}/plant-instances/{{key}}/planting-runs"): ("per-parent", "the runs one plant belongs to"),
    ("GET", f"{_T}/planting-runs/{{key}}/entries"): ("per-parent", "the species entries of one run"),
    ("GET", f"{_T}/planting-runs/{{key}}/plants"): ("per-parent", "the plants of one run"),
    ("GET", f"{_T}/planting-runs/{{key}}/active-channels"): (
        "computed",
        "the delivery channels of one run's active nutrient plan phase",
    ),
    ("GET", f"{_T}/plant-instances/{{plant_key}}/phenotypes"): ("per-parent", "the phenotype notes of one plant"),
    # ── tanks ──────────────────────────────────────────────────────────────
    ("GET", f"{_T}/tanks/maintenance/due"): (
        "computed",
        "one due row per active maintenance schedule of the tenant's tanks",
    ),
    ("GET", f"{_T}/tanks/ha-entities"): ("external", "the entities the tenant's Home Assistant reports"),
    ("GET", f"{_T}/tanks/{{key}}/alerts"): ("computed", "the alerts one tank's current state raises"),
    ("GET", f"{_T}/tanks/{{key}}/maintenance/due"): ("computed", "one due row per schedule of one tank"),
    ("GET", f"{_T}/tanks/{{key}}/schedules"): ("per-parent", "the maintenance schedules of one tank"),
    ("GET", f"{_T}/tanks/{{key}}/active-nutrient-plans"): ("per-parent", "the nutrient plans active on one tank"),
    ("GET", f"{_T}/tanks/{{key}}/sensors"): ("per-parent", "the sensors of one tank"),
    # ── fertilizers and nutrient plans ─────────────────────────────────────
    ("GET", f"{_T}/fertilizers/{{key}}/stocks"): ("per-parent", "the stock batches of one fertilizer"),
    ("GET", f"{_T}/fertilizers/{{key}}/incompatibilities"): (
        "per-parent",
        "the incompatibility edges of one fertilizer",
    ),
    ("GET", f"{_T}/fertilizers/{{key}}/nutrient-plans"): ("per-parent", "the plans one fertilizer is used in"),
    ("GET", f"{_T}/nutrient-plans/{{key}}/entries"): ("per-parent", "the phase entries of one nutrient plan"),
    ("GET", f"{_T}/favorites/nutrient-plans/matching"): (
        "computed",
        "the plans matching the given favourite keys; the request bounds the keys",
    ),
    # ── harvest and post-harvest ───────────────────────────────────────────
    ("GET", f"{_T}/harvest/species/{{species_key}}/indicators"): (
        "catalogue",
        "the harvest indicators of one species",
    ),
    ("GET", f"{_T}/post-harvest/{{key}}/drying-progress"): (
        "per-parent",
        "the drying measurements of one batch over its drying weeks",
    ),
    ("GET", f"{_T}/post-harvest/{{key}}/mold-alerts"): ("per-parent", "the mould alerts of one batch"),
    # ── tasks and workflows ────────────────────────────────────────────────
    ("GET", f"{_T}/tasks/workflows/{{key}}/executions"): (
        "remaining",
        "every execution of one workflow template accrues over seasons",
    ),
    ("GET", f"{_T}/tasks/workflows/{{wf_key}}/phases"): ("per-parent", "the phases of one workflow"),
    ("GET", f"{_T}/tasks/phases/suggestions"): ("computed", "suggested phase names, a fixed vocabulary"),
    ("PUT", f"{_T}/tasks/phases/reorder"): ("write-echo", "answers with the phases it reordered"),
    ("GET", f"{_T}/tasks/workflows/{{wf_key}}/templates"): ("per-parent", "the task templates of one workflow"),
    ("GET", f"{_T}/tasks/queue"): (
        "remaining",
        "the tenant-wide branch is capped at QUEUE_LIMIT; the ?plant_key branch reads every pending "
        "task of one plant, and care-task de-duplication runs after the read, so a window before it "
        "would return short pages",
    ),
    ("GET", f"{_T}/tasks/overdue"): (
        "remaining",
        "every overdue pending task of the tenant; de-duplication runs after the read (see queue)",
    ),
    ("GET", f"{_T}/tasks/{{task_key}}/comments"): ("per-parent", "the comments of one task"),
    ("GET", f"{_T}/tasks/{{task_key}}/history"): ("per-parent", "the state changes of one task"),
    # ── IPM, recognition, diagnosis ────────────────────────────────────────
    ("GET", f"{_T}/ipm/plants/{{plant_key}}/karenz"): (
        "per-parent",
        "the running waiting periods of one plant",
    ),
    ("GET", f"{_T}/ipm/pests/{{pest_key}}/images"): (
        "remaining",
        "tenant contributions, inspection photos and recognition images of one pest accrue",
    ),
    ("GET", f"{_T}/pests/plants/{{plant_key}}/history"): ("capped-query", "?limit ≤ 100 detections"),
    ("GET", f"{_T}/identification/history"): ("capped-query", "?limit ≤ 100 identifications"),
    ("GET", f"{_T}/cv-diagnosis/history"): ("capped-query", "?limit ≤ 100 diagnoses"),
    # ── care, calendar, favourites, notifications ──────────────────────────
    ("GET", f"{_T}/calendar/feeds"): ("per-subject", "the caller's calendar feeds, created one by one"),
    ("GET", f"{_T}/care-reminders/dashboard"): (
        "remaining",
        "one row per plant with a care profile: grows with the tenant's plants",
    ),
    ("GET", f"{_T}/ai/providers"): ("tenant-config", "the AI providers configured for the tenant"),
    ("GET", f"{_T}/starter-kits"): ("catalogue", "the seeded starter kits for the tenant"),
    ("GET", f"{_T}/favorites"): ("per-subject", "the caller's favourites, starred one by one"),
    ("GET", f"{_T}/notifications/channels/status"): ("computed", "one row per notification channel type"),
    ("GET", f"{_T}/ha-publish"): ("tenant-config", "the entities the tenant chose to publish to Home Assistant"),
    ("PUT", f"{_T}/ha-publish"): ("write-echo", "answers with the settings it wrote"),
    ("GET", f"{_T}/ha/weather-entities"): ("external", "the weather entities the tenant's Home Assistant reports"),
    ("GET", f"{_T}/ha/sensor-entities"): ("external", "the sensor entities the tenant's Home Assistant reports"),
    # ── aquaponics ─────────────────────────────────────────────────────────
    ("GET", f"{_T}/aquaponics/systems"): ("tenant-config", "the tenant's aquaponic systems"),
    ("GET", f"{_T}/aquaponics/systems/{{system_key}}/fish-stocks"): ("per-parent", "the fish stocks of one system"),
    ("GET", f"{_T}/aquaponics/systems/{{system_key}}/water-quality-status"): (
        "computed",
        "one evaluation per water parameter",
    ),
    ("GET", f"{_T}/aquaponics/systems/{{system_key}}/nitrogen-cycle-chart"): (
        "computed",
        "the last 60 water tests (service limit=60)",
    ),
    ("GET", f"{_T}/aquaponics/systems/{{system_key}}/alerts"): ("computed", "the alerts of one system's state"),
    ("GET", f"{_T}/aquaponics/systems/{{system_key}}/fish-health"): (
        "computed",
        "the health alerts of one system's stocks",
    ),
    # ── actuators, equipment, inventory ────────────────────────────────────
    ("GET", f"{_T}/actuators"): ("tenant-config", "the tenant's actuators, registered one by one"),
    ("GET", f"{_T}/actuators/{{actuator_key}}/schedules"): ("per-parent", "the schedules of one actuator"),
    ("GET", f"{_T}/actuators/{{actuator_key}}/rules"): ("per-parent", "the rules of one actuator"),
    ("GET", f"{_T}/rules"): ("tenant-config", "the tenant's control rules"),
    ("GET", f"{_T}/phase-control-profiles"): ("tenant-config", "the tenant's phase control profiles"),
    ("GET", f"{_T}/inventree/connections"): ("tenant-config", "the tenant's InvenTree connections"),
    ("GET", f"{_T}/inventree/references"): (
        "remaining",
        "one reference per linked entity; grows with the linked inventory",
    ),
    ("GET", f"{_T}/equipment"): ("tenant-config", "the tenant's equipment, registered one by one"),
    # ── propagation ────────────────────────────────────────────────────────
    ("GET", f"{_T}/propagation/batches/{{batch_key}}/events"): ("per-parent", "the events of one batch"),
    ("GET", f"{_T}/propagation/stats"): ("computed", "one row per propagation method"),
    ("GET", f"{_T}/propagation/stats/by-cultivar"): (
        "remaining",
        "one row per cultivar the tenant propagated",
    ),
    ("GET", f"{_T}/propagation/stats/by-protocol"): ("computed", "one row per protocol of the tenant"),
}

#: The ``remaining`` entries, pinned. Lower it with each conversion; a new
#: unbounded route of a growing collection must be paginated, not added here.
_REMAINING_COUNT = 9


def _routes(routes: list[Any], prefix: str = "", inherited: tuple[Any, ...] = ()) -> list[tuple[str, APIRoute, list]]:
    """Every leaf route as ``(full path, route, dependants)``, include-level dependencies included."""
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


def _calls(dependant: Any) -> set[Any]:
    found = {dependant.call}
    for sub in dependant.dependencies:
        found |= _calls(sub)
    return found


def _is_list(route: APIRoute) -> bool:
    return typing.get_origin(route.response_model) is list


def _is_bounded(dependants: list[Any]) -> bool:
    calls = set().union(*(_calls(d) for d in dependants))
    return any(dep in calls for dep in PAGINATION_DEPENDENCIES)


def _method(route: APIRoute) -> str:
    return ",".join(sorted(route.methods))


def _has_capped_limit(route: APIRoute) -> bool:
    for param in route.dependant.query_params:
        if param.name == "limit" and any(getattr(m, "le", None) is not None for m in param.field_info.metadata):
            return True
    return False


def _unbounded_list_routes(app: Any) -> dict[tuple[str, str], APIRoute]:
    return {
        (_method(route), path): route
        for path, route, dependants in _routes(app.routes)
        if _is_list(route) and not _is_bounded(dependants)
    }


def _findings(app: Any, classified: dict[tuple[str, str], tuple[str, str]]) -> list[str]:
    out = []
    for (method, path), route in sorted(_unbounded_list_routes(app).items(), key=lambda kv: kv[0][1]):
        entry = classified.get((method, path))
        if entry is None:
            out.append(f"{method} {path}")
        elif entry[0] == "capped-query" and not _has_capped_limit(route):
            out.append(f"{method} {path} (classified capped-query, but has no ?limit with an upper bound)")
    return out


# ── the guard on the assembled app ──────────────────────────────────────────


def test_every_list_route_is_paginated_or_classified() -> None:
    from app.main import app

    routes = _routes(app.routes)
    list_routes = [(path, route, deps) for path, route, deps in routes if _is_list(route)]
    bounded = [path for path, _, deps in list_routes if _is_bounded(deps)]

    # Non-vacuity: the walk reaches the nested /t/{slug}/ routers, sees the list
    # routes, and recognises the dependency on both the plain and cursor form.
    assert len(routes) > 700, len(routes)
    assert len(list_routes) > 150, len(list_routes)
    assert len(bounded) >= 50, len(bounded)
    assert f"{_T}/plant-instances" in bounded
    assert f"{_T}/watering-logs" in bounded

    findings = _findings(app, _CLASSIFIED)
    assert findings == [], (
        "list routes that read every matching row: depend on get_pagination / get_cursor_pagination "
        f"or classify the route in _CLASSIFIED with the reason it cannot grow (MT-035, #2131): {findings}"
    )


def test_every_classification_names_an_unbounded_list_route() -> None:
    from app.main import app

    unbounded = _unbounded_list_routes(app)
    stale = sorted(set(_CLASSIFIED) - set(unbounded))
    assert stale == [], f"classified route is gone, no longer a list, or now paginated — drop the entry: {stale}"


def test_the_classification_kinds_and_reasons_are_stated() -> None:
    unknown = {key: kind for key, (kind, _) in _CLASSIFIED.items() if kind not in _KINDS}
    silent = [key for key, (_, reason) in _CLASSIFIED.items() if len(reason.strip()) < 15]
    assert unknown == {}
    assert silent == []


def test_the_remaining_unbounded_routes_are_pinned() -> None:
    remaining = sorted(key for key, (kind, _) in _CLASSIFIED.items() if kind == "remaining")
    assert len(remaining) == _REMAINING_COUNT, remaining


def test_the_cursor_routes_are_the_heavy_collections() -> None:
    # The keyset option exists where a tenant's rows grow fastest and the list is
    # ordered by ``_key``; pin it so a refactor cannot silently drop it.
    from app.main import app

    cursor_routes = sorted(
        path for path, _route, deps in _routes(app.routes) if get_cursor_pagination in set().union(*map(_calls, deps))
    )
    assert cursor_routes == sorted(
        [
            f"{_T}/feeding-events",
            f"{_T}/plant-instances",
            f"{_T}/watering-events",
            f"{_T}/watering-logs",
        ]
    )


# ── the predicate on a synthetic app (self-test) ────────────────────────────


class _Row(PaginationParams):
    pass


def _paged_dep(pagination: PaginationParams = Depends(get_pagination)) -> PaginationParams:
    return pagination


def _probe_app() -> FastAPI:
    router = APIRouter(prefix="/probe")

    @router.get("/unbounded", response_model=list[_Row])
    def unbounded() -> list[_Row]: ...

    @router.get("/annotated")
    def annotated() -> list[_Row]: ...

    @router.get("/paged", response_model=list[_Row])
    def paged(pagination: PaginationParams = Depends(get_pagination)) -> list[_Row]: ...

    @router.get("/cursor", response_model=list[_Row])
    def cursor(pagination: CursorPaginationParams = Depends(get_cursor_pagination)) -> list[_Row]: ...

    @router.get("/nested", response_model=list[_Row])
    def nested(pagination: PaginationParams = Depends(_paged_dep)) -> list[_Row]: ...

    @router.get("/capped", response_model=list[_Row])
    def capped(limit: int = Query(20, ge=1, le=100)) -> list[_Row]: ...

    @router.get("/uncapped", response_model=list[_Row])
    def uncapped(limit: int = Query(20, ge=1)) -> list[_Row]: ...

    @router.get("/single", response_model=_Row)
    def single() -> _Row: ...

    included = APIRouter(prefix="/included")

    @included.get("/rows", response_model=list[_Row])
    def included_rows() -> list[_Row]: ...

    inner = FastAPI()
    inner.include_router(router, prefix="/api")
    inner.include_router(included, prefix="/api", dependencies=[Depends(get_pagination)])
    return inner


def test_the_predicate_flags_unbounded_lists_in_either_spelling() -> None:
    assert _findings(_probe_app(), {}) == [
        "GET /api/probe/annotated",
        "GET /api/probe/capped",
        "GET /api/probe/unbounded",
        "GET /api/probe/uncapped",
    ]


def test_the_predicate_admits_both_dependencies_nested_and_include_level() -> None:
    unbounded = _unbounded_list_routes(_probe_app())
    for admitted in ("/api/probe/paged", "/api/probe/cursor", "/api/probe/nested", "/api/included/rows"):
        assert ("GET", admitted) not in unbounded


def test_a_capped_query_classification_is_checked() -> None:
    classified = {
        ("GET", "/api/probe/annotated"): ("catalogue", "a probe catalogue for the self-test"),
        ("GET", "/api/probe/unbounded"): ("catalogue", "a probe catalogue for the self-test"),
        ("GET", "/api/probe/capped"): ("capped-query", "?limit ≤ 100 in the probe"),
        ("GET", "/api/probe/uncapped"): ("capped-query", "claims a cap it does not declare"),
    }
    assert _findings(_probe_app(), classified) == [
        "GET /api/probe/uncapped (classified capped-query, but has no ?limit with an upper bound)"
    ]


@pytest.mark.parametrize("dependency", PAGINATION_DEPENDENCIES)
def test_every_pagination_dependency_caps_limit_at_200(dependency: Any) -> None:
    # The bound the guard trusts: a dependency that let ``limit`` grow would
    # make every "bounded" route unbounded again.
    router = APIRouter()

    @router.get("/rows", response_model=list[_Row])
    def rows(p: Any = Depends(dependency)) -> list[_Row]: ...

    app = FastAPI()
    app.include_router(router)
    (_, route, deps) = _routes(app.routes)[0]
    limits = [p for d in deps for sub in d.dependencies for p in sub.query_params if p.name == "limit"]
    assert len(limits) == 1
    assert [getattr(m, "le", None) for m in limits[0].field_info.metadata if getattr(m, "le", None)] == [200]
