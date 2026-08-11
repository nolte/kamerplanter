"""The ``/t/{slug}/`` slug-existence oracle, through the HTTP boundary (#1091 A-11).

The unit tier (``tests/unit/common/test_path_tenant_oracle.py``) pins the
resolver's decision; this tier pins the two things only a real request shows:

* the refusal really arrives as an HTTP **403** on a mounted ``/t/{slug}/``
  router — the exception is converted where the dependency runs, not somewhere a
  handler could still turn it back into a 404 — and **no route body executes**;
* the ``/t/{slug}/`` refusal and the ``X-Active-Tenant`` refusal (A-2, global
  routes) are the *same* rendered answer. Two surfaces refusing "both with 403
  but differently" would still be correlatable, and would drift apart at the next
  edit of either.

The sites router stands in for all ~54 tenant-scoped routers: it binds
:func:`~app.common.auth.get_current_tenant` the ordinary way, so what holds here
holds wherever that dependency is declared.

Datastore-free by construction: tenant service, site service, family repository
and the user are overridden; only the resolver under test is real.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.botanical_families.router import router as families_router
from app.api.v1.sites.tenant_router import router as sites_router
from app.common import auth as auth_mod
from app.common.dependencies import get_family_repo, get_site_service, get_tenant_service
from app.common.enums import AdminScope, TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError, NotFoundError
from app.domain.models.site import Site

_OWN = SimpleNamespace(key="tenant_own", slug="green-club")
_FOREIGN = SimpleNamespace(key="tenant_foreign", slug="foreign-club")

#: A slug that resolves to nothing. Used verbatim in the "does it leak?" checks.
_UNKNOWN_SLUG = "competitor-gmbh"


class _FakeTenantService:
    """Slug lookup that raises 404 like the real service, plus membership lookup."""

    def __init__(self) -> None:
        self._by_slug = {t.slug: t for t in (_OWN, _FOREIGN)}
        self._memberships = {
            ("user_1", "tenant_own"): SimpleNamespace(
                role=TenantRole.GROWER, admin_scopes=[AdminScope.TECHNICAL], is_active=True
            ),
        }

    def get_personal_tenant(self, user_key: str) -> SimpleNamespace | None:
        return _OWN if user_key == "user_1" else None

    def get_tenant_by_slug(self, slug: str) -> SimpleNamespace:
        tenant = self._by_slug.get(slug)
        if tenant is None:
            raise NotFoundError("tenants", slug)
        return tenant

    def get_membership(self, user_key: str, tenant_key: str) -> SimpleNamespace | None:
        return self._memberships.get((user_key, tenant_key))


class _RecordingSiteService:
    """Records whether the route body ran at all."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def list_sites(self, offset: int, limit: int, *, tenant_key: str) -> tuple[list[Site], int]:
        self.calls.append(f"list_sites:{tenant_key}")
        return [], 0

    def get_water_warnings(self, site: Site) -> list[Any]:  # pragma: no cover - no sites are returned
        return []


class _FakeFamilyRepo:
    """The global-route collaborator, for the cross-surface comparison."""

    def get_all_families(self, offset: int, limit: int) -> tuple[list[Any], int]:
        return [], 0

    def get_species_counts_by_family(self, *, tenant_key: str) -> dict[str, int]:
        return {}


def _app(site_service: _RecordingSiteService) -> FastAPI:
    """One app carrying both surfaces: the path-bound router and a global one."""
    app = FastAPI()
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.include_router(sites_router, prefix="/api/v1/t/{tenant_slug}")
    app.include_router(families_router, prefix="/api/v1")
    app.dependency_overrides[auth_mod.get_current_user] = lambda: SimpleNamespace(key="user_1")
    app.dependency_overrides[get_tenant_service] = _FakeTenantService
    app.dependency_overrides[get_site_service] = lambda: site_service
    app.dependency_overrides[get_family_repo] = _FakeFamilyRepo
    return app


def _client(site_service: _RecordingSiteService | None = None) -> TestClient:
    return TestClient(_app(site_service or _RecordingSiteService()))


def _classifying(body: dict[str, Any]) -> dict[str, Any]:
    """The part of the error body that could *classify* the failure.

    Dropped, with reason:

    * ``error_id`` — a fresh UUID per raise, ``timestamp`` — stamped at response
      time. Per-occurrence, not per-case (same exclusion as A-2's header tests).
    * ``path`` and ``method`` — the request's *own* URL and verb echoed back. They
      necessarily differ between two requests that probe two different slugs, and
      they carry nothing the caller did not just send. What must not differ is
      everything that describes *why* the request failed: ``error_code``,
      ``message``, ``details`` (and the status code, asserted separately).
    """
    return {k: v for k, v in body.items() if k not in ("error_id", "timestamp", "path", "method")}


def _without_the_echo(body: dict[str, Any]) -> str:
    """The response body minus the echoed request path, as text.

    The probed slug is legitimately in ``path`` (the caller put it there); the
    leak this guards against is it appearing anywhere *else* — which is exactly
    what the old 404 did, in ``message`` and in ``details``.
    """
    return json.dumps(_classifying(body))


# ── Non-vacuity: the valid case still reaches the route body ────────────────


def test_a_member_still_reaches_the_route():
    service = _RecordingSiteService()

    response = _client(service).get("/api/v1/t/green-club/sites")

    assert response.status_code == 200
    assert service.calls == ["list_sites:tenant_own"]


# ── Both invalid classes: one 403, nothing served ───────────────────────────


@pytest.mark.parametrize(("case", "slug"), [("unknown slug", _UNKNOWN_SLUG), ("non-member", "foreign-club")])
def test_an_invalid_slug_is_refused_with_403_and_serves_nothing(case: str, slug: str):
    service = _RecordingSiteService()

    response = _client(service).get(f"/api/v1/t/{slug}/sites")

    assert response.status_code == 403, case
    assert response.json()["error_code"] == "FORBIDDEN", case
    assert service.calls == [], case


def test_the_two_invalid_path_cases_are_indistinguishable():
    unknown = _client().get(f"/api/v1/t/{_UNKNOWN_SLUG}/sites")
    non_member = _client().get("/api/v1/t/foreign-club/sites")

    assert unknown.status_code == non_member.status_code == 403
    assert _classifying(unknown.json()) == _classifying(non_member.json())
    assert unknown.json()["error_id"] != non_member.json()["error_id"]
    # The probed slug appears only where the caller put it — the request path.
    assert _UNKNOWN_SLUG not in _without_the_echo(unknown.json())
    assert unknown.json()["path"] == f"/api/v1/t/{_UNKNOWN_SLUG}/sites"


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", f"/api/v1/t/{_UNKNOWN_SLUG}/sites"),
        ("get", f"/api/v1/t/{_UNKNOWN_SLUG}/sites/site-1"),
        ("post", f"/api/v1/t/{_UNKNOWN_SLUG}/sites"),
        ("put", f"/api/v1/t/{_UNKNOWN_SLUG}/sites/site-1"),
        ("delete", f"/api/v1/t/{_UNKNOWN_SLUG}/sites/site-1"),
    ],
)
def test_the_unknown_slug_is_a_403_on_every_verb(method: str, path: str):
    # The conversion sits in the shared dependency, so it cannot hold for the read
    # and be missing on the write — one raise site, every operation.
    response = _client().request(method, path, json={"name": "Bed 2"})

    assert response.status_code == 403


# ── The decisive property: the two surfaces render one answer ───────────────


@pytest.mark.parametrize(("case", "slug"), [("unknown slug", _UNKNOWN_SLUG), ("non-member", "foreign-club")])
def test_the_path_403_and_the_header_403_are_the_same_answer(case: str, slug: str):
    """``/t/{slug}/`` and ``X-Active-Tenant`` refuse identically (A-2 ↔ A-11).

    Both surfaces resolve a caller-supplied slug and both must refuse the two
    invalid classes as one fact. Comparing the *rendered* bodies (not just the
    two constants) is what keeps a future divergence — a router that catches and
    re-raises, a handler that rewrites one path — visible.
    """
    client = _client()
    from_path = client.get(f"/api/v1/t/{slug}/sites")
    from_header = client.get("/api/v1/botanical-families", headers={auth_mod.ACTIVE_TENANT_HEADER: slug})

    assert from_path.status_code == from_header.status_code == 403, case
    assert _classifying(from_path.json()) == _classifying(from_header.json()), case
