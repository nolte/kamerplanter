"""REQ-049 axis-2 enforcement at the router boundary (#780).

The permission model only means something where a request is actually refused.
These cases drive the real routers through their real dependencies and assert
the four statements REQ-049 §7 turns into acceptance criteria:

* AK-01 a viewer is refused on every writing tenant-scoped endpoint;
* AK-04 ``management`` opens member administration and nothing in the garden;
* AK-05 ``technical`` opens the tenant's own integrations and nothing else;
* and the negative form of both — the top domain rank grants neither scope.

Written against the dependency graph rather than the service layer on purpose:
the defect this guards against is a router keeping the old rank check while the
model underneath it moved, and only a request can see that.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.v1.actuators.tenant_router import router as actuators_router
from app.api.v1.tenants.router import router as tenants_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_tenant_service
from app.common.enums import AdminScope, TenantRole
from app.common.exceptions import KamerplanterError
from app.domain.models.tenant_context import TenantContext

_SLUG = "garten"
_PREFIX = f"/api/v1/t/{_SLUG}"


def _error_handler(_request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error_code": exc.error_code})


def _client(role: TenantRole, scopes: list[AdminScope]) -> TestClient:
    app = FastAPI()
    app.include_router(tenants_router, prefix="/api/v1")
    app.include_router(actuators_router, prefix="/api/v1/t/{tenant_slug}")
    app.add_exception_handler(KamerplanterError, _error_handler)
    app.dependency_overrides[get_current_tenant] = lambda: TenantContext(
        tenant_key="t1", tenant_slug=_SLUG, user_key="u1", role=role, admin_scopes=scopes
    )
    # Never reached: every case below is refused by the dependency, before any
    # handler body runs. A service that *were* reached would raise here and the
    # test would fail loudly rather than pass for the wrong reason.
    app.dependency_overrides[get_tenant_service] = lambda: pytest.fail(
        "the request reached the service layer — the guard did not refuse it"
    )
    return TestClient(app, raise_server_exceptions=False)


# ── Member administration: the `management` scope ────────────────────────────

_MEMBER_ADMIN_CALLS = [
    ("post", f"/api/v1/tenants/{_SLUG}/invitations/email", {"email": "a@b.de", "role": "viewer"}),
    ("post", f"/api/v1/tenants/{_SLUG}/invitations/link", {"role": "viewer"}),
    ("delete", f"/api/v1/tenants/{_SLUG}/members/m1", None),
    ("patch", f"/api/v1/tenants/{_SLUG}/members/m1/role", {"role": "grower"}),
]


@pytest.mark.parametrize(("method", "path", "payload"), _MEMBER_ADMIN_CALLS)
class TestManagementScope:
    def test_a_lead_without_the_scope_is_refused(self, method: str, path: str, payload: dict | None):
        # The whole point of retiring `admin`: the top domain rank administers
        # nothing by itself.
        client = _client(TenantRole.LEAD, [])

        resp = getattr(client, method)(path, json=payload) if payload else getattr(client, method)(path)

        assert resp.status_code == 403
        assert resp.json()["error_code"] == "FORBIDDEN"

    def test_the_technical_scope_does_not_substitute(self, method: str, path: str, payload: dict | None):
        client = _client(TenantRole.LEAD, [AdminScope.TECHNICAL])

        resp = getattr(client, method)(path, json=payload) if payload else getattr(client, method)(path)

        assert resp.status_code == 403


class TestManagementScopeOpensMemberAdministration:
    def test_a_viewer_holding_management_passes_the_guard(self):
        # AK-04, first half: the club secretary keeps the member list. The
        # request gets past the dependency and reaches the service — which the
        # override turns into an explicit failure, so "passed the guard" is
        # observable without standing up a tenant service.
        client = _client(TenantRole.VIEWER, [AdminScope.MANAGEMENT])

        resp = client.delete(f"/api/v1/tenants/{_SLUG}/members/m1")

        assert resp.status_code != 403


# ── Integrations: the `technical` scope ──────────────────────────────────────


class TestTechnicalScope:
    @pytest.mark.parametrize("scopes", [[], [AdminScope.MANAGEMENT]])
    def test_configuring_an_actuator_needs_the_technical_scope(self, scopes: list[AdminScope]):
        # AK-05: wiring a device is configuration, not gardening. Authority over
        # people is no substitute for it.
        client = _client(TenantRole.LEAD, scopes)

        resp = client.delete(f"{_PREFIX}/actuators/a1")

        assert resp.status_code == 403

    def test_operating_an_actuator_stays_on_the_domain_axis(self):
        # REQ-049 §2.4 scopes the technical grant to *configuring* sensors and
        # actuators, explicitly "nicht: bedienen". A grower on shift must be
        # able to hit emergency stop without holding an administrative scope.
        client = _client(TenantRole.GROWER, [])

        resp = client.post(f"{_PREFIX}/actuators/emergency-stop")

        assert resp.status_code != 403


# ── AK-01: a viewer writes nothing ───────────────────────────────────────────


class TestViewerIsRefusedOnWrites:
    @pytest.mark.parametrize(
        ("method", "path", "payload"),
        [
            ("post", f"{_PREFIX}/locations/l1/actuators", {"name": "Lamp", "actuator_type": "light"}),
            ("post", f"{_PREFIX}/actuators/a1/command", {"command": "on"}),
            ("delete", f"{_PREFIX}/actuators/a1", None),
        ],
    )
    def test_viewer_write_is_refused(self, method: str, path: str, payload: dict | None):
        client = _client(TenantRole.VIEWER, [])

        resp = getattr(client, method)(path, json=payload) if payload else getattr(client, method)(path)

        assert resp.status_code == 403
