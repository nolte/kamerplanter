"""MT-044 (#2144): a ``/api/v1/**`` JSON answer carries ``Cache-Control: no-store``.

Tenant-private JSON (plants, tasks, members, the Art. 15 export) was sent without
any caching directive; only HSTS and the other security headers were set. A
shared proxy or the browser's back/forward and disk cache was then free to keep
a copy of a member's view after logout or a tenant switch.

The rule is a default, not an override: a route that decides its own caching
keeps it. The attachment and pest-image downloads answer ``private, no-cache``
with an ETag (revalidated on every reuse, #2254), the token download ``no-store``
and the SSE stream ``no-cache`` — the middleware only fills in a header that is absent.

**The one named exception** (REQ-053 §32.6 Pkt. 13, #2759): ``GET …/sites``, ``GET …/sites/{key}/plan`` and
``GET …/locations/{key}/summary`` answer ``private, no-cache`` so the service worker may keep them in the user's and
tenant's namespace. The sweep below pins that exactly these three routes opt in, the requests that they do and that
every other answer — a sibling read, a refusal of one of the three — stays ``no-store``.
"""

from __future__ import annotations

import inspect
from collections.abc import Iterable, Iterator
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.common.auth import get_current_user
from app.common.cache_control import API_DEFAULT_CACHE_CONTROL, OFFLINE_READ_CACHE_CONTROL, OFFLINE_READ_ROUTES
from app.common.dependencies import (
    get_garden_plan_service,
    get_garden_resource_service,
    get_site_service,
    get_tenant_service,
)
from app.common.enums import TenantRole
from app.common.exceptions import NotFoundError
from app.domain.models.garden_plan import BedCounters, BedSummaryView
from app.domain.models.user import User
from app.domain.services.garden_plan_service import GardenPlanService
from tests.support.garden_plan_fakes import SITE, TENANT, FakePlanRepo, FakeSites, make_location, make_site, rect

with patch("app.main.get_connection"), patch("app.main.ensure_collections"):
    from app.main import app, security_headers_middleware


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_a_real_api_v1_route_answer_is_not_stored(client: TestClient) -> None:
    """A real ``/api/v1`` route through the real middleware stack (the liveness probe is datastore-free)."""
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"


def _request(path: str) -> Request:
    return Request({"type": "http", "method": "GET", "path": path, "headers": [], "query_string": b""})


async def _answer(path: str, response: Response) -> Response:
    async def call_next(_request: Request) -> Response:
        return response

    return await security_headers_middleware(_request(path), call_next)


async def test_an_api_v1_answer_without_a_directive_gets_no_store() -> None:
    answered = await _answer("/api/v1/t/a/tasks", JSONResponse({"x": 1}))
    assert answered.headers["cache-control"] == "no-store"


@pytest.mark.parametrize(
    "directive",
    ["private, no-cache", "no-cache"],
    ids=["attachment-and-pest-image", "sse"],
)
async def test_a_route_that_chose_its_own_directive_keeps_it(directive: str) -> None:
    answered = await _answer("/api/v1/t/a/attachments/x/download", Response(b"x", headers={"Cache-Control": directive}))
    assert answered.headers["cache-control"] == directive


@pytest.mark.parametrize("path", ["/api/health", "/metrics", "/docs"])
async def test_a_path_outside_api_v1_is_left_alone(path: str) -> None:
    answered = await _answer(path, JSONResponse({"x": 1}))
    assert "cache-control" not in answered.headers


# ── The named exception: the three offline reads of the garden plan (REQ-053 §32.6 Pkt. 13, #2759) ─────────────


def _api_routes(routes: Iterable[Any], prefix: str = "", depth: int = 0) -> Iterator[tuple[str, str, APIRoute]]:
    """``(method, full path, route)`` of every ``APIRoute`` of the app, through the nested include contexts."""
    if depth > 12:
        return
    for route in routes:
        if isinstance(route, APIRoute):
            for method in sorted(route.methods or ()):
                yield method, f"{prefix}{route.path}", route
            continue
        nested = getattr(route, "original_router", None)
        if nested is not None:
            yield from _api_routes(nested.routes, prefix + route.include_context.prefix, depth + 1)


def _opts_into_the_offline_cache(route: APIRoute) -> bool:
    """Whether the handler's own code names the opt-in helper, the directive's constant or its literal value.

    Read from the compiled code object (the names and constants it loads), not from the source text: a formatting,
    an alias of the call or a wrapped handler does not hide it.
    """
    code = inspect.unwrap(route.endpoint).__code__
    names = set(code.co_names)
    return bool(names & {"allow_offline_read_cache", "OFFLINE_READ_CACHE_CONTROL"}) or (
        OFFLINE_READ_CACHE_CONTROL in code.co_consts
    )


def test_exactly_the_three_offline_reads_opt_out_of_no_store() -> None:
    """The sweep: every other route of the app keeps the MT-044 default."""
    opted = {(method, path) for method, path, route in _api_routes(app.routes) if _opts_into_the_offline_cache(route)}
    assert opted == OFFLINE_READ_ROUTES


def test_the_offline_reads_are_real_routes_of_the_app() -> None:
    """The constant names mounted routes, so the sweep above cannot pass on a stale path list."""
    mounted = {(method, path) for method, path, _ in _api_routes(app.routes)}
    assert mounted >= OFFLINE_READ_ROUTES


class _Tenants:
    def get_tenant_by_slug(self, slug: str) -> SimpleNamespace:
        if slug != "own":
            raise NotFoundError("Tenant", slug)
        return SimpleNamespace(key=TENANT, slug=slug, is_active=True)

    def get_membership(self, user_key: str, tenant_key: str) -> SimpleNamespace:
        return SimpleNamespace(role=TenantRole.VIEWER, admin_scopes=[], is_active=True)

    def get_personal_tenant(self, user_key: str) -> None:
        return None


class _Sites:
    """``SiteService`` as the two site reads use it: an empty list, an unknown single site."""

    def list_sites_window(self, offset: int, limit: int, *, tenant_key: str) -> list:
        return []

    def get_site(self, key: str, *, tenant_key: str):
        raise NotFoundError("Site", key)


class _Summaries:
    """``GardenResourceService.get_summary``: one known bed, everything else unknown."""

    def get_summary(self, key: str, *, tenant_key: str) -> BedSummaryView:
        if key != "bed":
            raise NotFoundError("Location", key)
        return BedSummaryView(
            location=make_location("bed", geometry=rect(1, 1, 2, 1)),
            counters=BedCounters(),
            season_state="empty",
            is_bed=True,
        )


@pytest.fixture
def tenant_client() -> Iterator[TestClient]:
    repo = FakePlanRepo(FakeSites(make_site()))
    repo.locations["bed"] = make_location("bed", geometry=rect(1, 1, 2, 1))
    plans = GardenPlanService(repo._sites, repo)
    app.dependency_overrides[get_current_user] = lambda: User(_key="u_sabine", email="s@example.org", display_name="S")
    app.dependency_overrides[get_tenant_service] = _Tenants
    app.dependency_overrides[get_garden_plan_service] = lambda: plans
    app.dependency_overrides[get_site_service] = _Sites
    app.dependency_overrides[get_garden_resource_service] = _Summaries
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize(
    "path",
    [f"/api/v1/t/own/sites/{SITE}/plan", "/api/v1/t/own/sites", "/api/v1/t/own/locations/bed/summary"],
    ids=["plan", "sites", "location-summary"],
)
def test_an_offline_read_answers_private_no_cache(tenant_client: TestClient, path: str) -> None:
    response = tenant_client.get(path)
    assert response.status_code == 200
    assert response.headers["cache-control"] == OFFLINE_READ_CACHE_CONTROL


@pytest.mark.parametrize(
    ("path", "status"),
    [
        # A sibling read of the same routers stays on the default ...
        (f"/api/v1/t/own/sites/{SITE}/plan/audit", 200),
        # ... and so does a refusal of an offline read: nothing of it is for the worker to keep.
        ("/api/v1/t/own/sites/unknown", 404),
        ("/api/v1/t/own/sites/unknown/plan", 404),
        ("/api/v1/t/own/locations/unknown/summary", 404),
    ],
    ids=["plan-audit", "single-site", "unknown-plan", "unknown-summary"],
)
def test_every_other_answer_stays_no_store(tenant_client: TestClient, path: str, status: int) -> None:
    response = tenant_client.get(path)
    assert response.status_code == status
    assert response.headers["cache-control"] == API_DEFAULT_CACHE_CONTROL
