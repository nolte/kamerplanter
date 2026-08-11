"""``X-Active-Tenant`` through the HTTP boundary (#1091, R1-R3, ADR-009).

The unit tier pins the resolver's decisions; this tier pins the three things only
a real request can show:

* the header actually **reaches** the resolver from the wire and the resolved key
  is what the consuming route scopes its query with — a resolver that decides
  correctly but is never fed is the inert-guard class;
* the refusal really is an HTTP **403** with one indistinguishable body for both
  invalid cases (unknown slug, non-member), and no rows are served on that path;
* the header is **documented**: it appears as a header parameter on *every*
  operation that depends on the resolver, so clients and generated API types know
  it exists. An undeclared side channel would work in curl and be invisible to
  every consumer.

Datastore-free by construction: the tenant service, the repository and the user
are overridden; only the resolver under test is real.
"""

from __future__ import annotations

import inspect
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi import params as fastapi_params
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.api.v1.botanical_families.router import router as families_router
from app.api.v1.companion_planting.router import router as companion_router
from app.api.v1.cultivars.router import router as cultivars_router
from app.api.v1.species.router import router as species_router
from app.common import auth as auth_mod
from app.common.dependencies import get_family_repo, get_tenant_service
from app.common.enums import AdminScope, TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError, NotFoundError

_PERSONAL = SimpleNamespace(key="tenant_personal_1", slug="user-1-garden")
_ORG = SimpleNamespace(key="tenant_org_1", slug="green-club")
_FOREIGN = SimpleNamespace(key="tenant_foreign", slug="foreign-club")


class _FakeTenantService:
    """The resolver's collaborator: slug lookup raising 404, membership lookup."""

    def __init__(self) -> None:
        self._by_slug = {t.slug: t for t in (_PERSONAL, _ORG, _FOREIGN)}
        self._memberships = {
            ("user_1", "tenant_personal_1"): SimpleNamespace(
                role=TenantRole.LEAD, admin_scopes=[AdminScope.MANAGEMENT], is_active=True
            ),
            ("user_1", "tenant_org_1"): SimpleNamespace(role=TenantRole.VIEWER, admin_scopes=[], is_active=True),
        }

    def get_personal_tenant(self, user_key: str) -> SimpleNamespace | None:
        return _PERSONAL if user_key == "user_1" else None

    def get_tenant_by_slug(self, slug: str) -> SimpleNamespace:
        tenant = self._by_slug.get(slug)
        if tenant is None:
            raise NotFoundError("tenants", slug)
        return tenant

    def get_membership(self, user_key: str, tenant_key: str) -> SimpleNamespace | None:
        return self._memberships.get((user_key, tenant_key))


class _FakeFamilyRepo:
    """Records the tenant key the route scoped its species counts with."""

    def __init__(self) -> None:
        self.scoped_with: list[str] = []

    def get_all_families(self, offset: int, limit: int) -> tuple[list[Any], int]:
        return [], 0

    def get_species_counts_by_family(self, *, tenant_key: str) -> dict[str, int]:
        self.scoped_with.append(tenant_key)
        return {}


def _app(repo: _FakeFamilyRepo) -> FastAPI:
    app = FastAPI()
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.include_router(families_router, prefix="/api/v1")
    app.dependency_overrides[auth_mod.get_current_user] = lambda: SimpleNamespace(key="user_1")
    app.dependency_overrides[get_tenant_service] = _FakeTenantService
    app.dependency_overrides[get_family_repo] = lambda: repo
    return app


def _client(repo: _FakeFamilyRepo) -> TestClient:
    return TestClient(_app(repo))


def _comparable(body: dict[str, Any]) -> dict[str, Any]:
    """The error body minus its two per-occurrence fields.

    ``error_id`` is a fresh UUID per raise and ``timestamp`` is stamped by the
    handler at response time; everything else must match between the two invalid
    cases, or the pair distinguishes "exists" from "you are not in it".
    """
    return {k: v for k, v in body.items() if k not in ("error_id", "timestamp")}


# ── The header reaches the resolver and scopes the route ────────────────────


def test_without_the_header_the_route_scopes_the_personal_tenant():
    repo = _FakeFamilyRepo()

    response = _client(repo).get("/api/v1/botanical-families")

    assert response.status_code == 200
    assert repo.scoped_with == ["tenant_personal_1"]


def test_with_the_header_the_route_scopes_that_tenant():
    repo = _FakeFamilyRepo()

    response = _client(repo).get("/api/v1/botanical-families", headers={"X-Active-Tenant": "green-club"})

    assert response.status_code == 200
    assert repo.scoped_with == ["tenant_org_1"]


def test_a_blank_header_is_treated_as_absent_over_the_wire():
    repo = _FakeFamilyRepo()

    response = _client(repo).get("/api/v1/botanical-families", headers={"X-Active-Tenant": "  "})

    assert response.status_code == 200
    assert repo.scoped_with == ["tenant_personal_1"]


def test_the_header_name_is_matched_case_insensitively():
    # HTTP header names are case-insensitive; a client sending ``x-active-tenant``
    # must not silently fall back to personal scope.
    repo = _FakeFamilyRepo()

    response = _client(repo).get("/api/v1/botanical-families", headers={"x-active-tenant": "green-club"})

    assert response.status_code == 200
    assert repo.scoped_with == ["tenant_org_1"]


# ── Both invalid classes: one 403, no rows served ───────────────────────────


@pytest.mark.parametrize(("case", "slug"), [("unknown slug", "no-such-org"), ("non-member", "foreign-club")])
def test_an_invalid_header_is_refused_with_403_and_serves_nothing(case: str, slug: str):
    repo = _FakeFamilyRepo()

    response = _client(repo).get("/api/v1/botanical-families", headers={"X-Active-Tenant": slug})

    assert response.status_code == 403, case
    assert response.json()["error_code"] == "FORBIDDEN", case
    # Refused before the repository: no fallback to personal or global scope
    # sneaked a 200 with the wrong rows past the failed resolution.
    assert repo.scoped_with == [], case


def test_the_two_invalid_cases_are_indistinguishable():
    unknown = _client(_FakeFamilyRepo()).get("/api/v1/botanical-families", headers={"X-Active-Tenant": "no-such-org"})
    non_member = _client(_FakeFamilyRepo()).get(
        "/api/v1/botanical-families", headers={"X-Active-Tenant": "foreign-club"}
    )

    assert unknown.status_code == non_member.status_code == 403
    assert _comparable(unknown.json()) == _comparable(non_member.json())
    assert unknown.json()["error_id"] != non_member.json()["error_id"]
    # And neither answer names the slug that was probed.
    assert "no-such-org" not in unknown.text
    assert "foreign-club" not in non_member.text


# ── The header is documented on every consuming operation ──────────────────


#: The four surfaces that consume the resolver (R-1: the companion-planting
#: router is the easily-forgotten fourth).
_CONSUMER_ROUTERS = (species_router, cultivars_router, families_router, companion_router)


def _consumer_app() -> FastAPI:
    """All four resolver consumers mounted, for document-level assertions."""
    app = FastAPI()
    for router in _CONSUMER_ROUTERS:
        app.include_router(router, prefix="/api/v1")
    return app


def _routes_depending_on_the_resolver() -> list[APIRoute]:
    """Every operation of the four consumer routers that depends on the resolver.

    Walks the routers' own ``routes`` rather than ``app.routes``: an included
    router is mounted as a single wrapper object, so the app's route list does not
    expose the individual operations.
    """
    resolvers = {auth_mod.get_active_tenant_key, auth_mod.get_active_tenant_context}
    found: list[APIRoute] = []
    for router in _CONSUMER_ROUTERS:
        for route in router.routes:
            if not isinstance(route, APIRoute):
                continue
            for param in inspect.signature(route.endpoint).parameters.values():
                default = param.default
                if isinstance(default, fastapi_params.Depends) and default.dependency in resolvers:
                    found.append(route)
                    break
    return found


def test_every_consuming_operation_documents_the_header():
    document = _consumer_app().openapi()
    consuming = _routes_depending_on_the_resolver()

    # Guard against a vacuous pass: the finder must actually find the consumers
    # (species, cultivars, botanical families, companion planting — R-1 counted
    # four surfaces, and a refactor that unhooks one must fail here, not silently).
    assert len(consuming) >= 14
    assert {route.path.split("/")[1] for route in consuming} == {
        "species",
        "botanical-families",
        "companion-planting",
    }

    for route in consuming:
        for method in sorted(route.methods - {"HEAD", "OPTIONS"}):
            parameters = document["paths"]["/api/v1" + route.path][method.lower()].get("parameters", [])
            headers = [p for p in parameters if p.get("in") == "header"]
            assert any(p["name"] == "X-Active-Tenant" for p in headers), f"{method} {route.path}"
            declared = next(p for p in headers if p["name"] == "X-Active-Tenant")
            # Optional: omitting it must stay legal (that is the personal-tenant
            # path every existing client takes).
            assert declared.get("required", False) is False
            assert declared.get("description")
