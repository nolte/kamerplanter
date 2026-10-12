"""#2138 (REQ-056 AK-26, AK-43, §14) — the export/import routes over HTTP.

* full mode mounts all eight routes, light mode none of them (AK-43);
* ``POST /tenants/{slug}/exports`` answers ``202`` with the request; an API key reaches the
  service flagged and is refused there with ``403``; a missing step-up is ``401``; a foreign or
  unknown slug is the same ``403`` (AK-26) — through the production router and the real
  :class:`TenantExportService` over the unit tier's doubles;
* ``POST /admin/platform/tenant-imports`` refuses a member who is no platform admin (``403``).
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient

from app.api.v1.tenant_exports.router import admin_router, tenant_router
from app.common.auth import get_authenticated_with_api_key, get_current_user, get_is_platform_admin
from app.common.dependencies import get_tenant_export_service
from app.common.error_handlers import app_error_handler, validation_error_handler
from app.common.exceptions import KamerplanterError
from tests.api.test_ai_public_routes_light_mode_only import _all_routes
from tests.unit.domain.services.test_tenant_export_service import LEAD
from tests.unit.domain.services.test_tenant_export_service import world as service_world  # noqa: F401 - fixture

ROUTES = {
    "POST /api/v1/tenants/{tenant_slug}/exports",
    "GET /api/v1/tenants/{tenant_slug}/exports",
    "GET /api/v1/tenants/{tenant_slug}/exports/{export_key}/download",
    "POST /api/v1/admin/platform/tenants/{key}/exports",
    "GET /api/v1/admin/platform/tenants/{key}/exports",
    "GET /api/v1/admin/platform/tenants/{key}/exports/{export_key}/download",
    "POST /api/v1/admin/platform/tenant-imports",
    "GET /api/v1/admin/platform/tenant-imports/{import_key}",
}


def test_full_mode_mounts_the_routes_light_mode_none() -> None:
    assert _all_routes("full") >= ROUTES
    assert ROUTES & _all_routes("light") == set()


@pytest.fixture
def client(service_world) -> SimpleNamespace:  # noqa: F811 - the imported fixture
    state = SimpleNamespace(api_key=False, admin=False, world=service_world)
    app = FastAPI()
    app.include_router(tenant_router, prefix="/api/v1")
    app.include_router(admin_router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[get_current_user] = lambda: LEAD
    app.dependency_overrides[get_authenticated_with_api_key] = lambda: state.api_key
    app.dependency_overrides[get_is_platform_admin] = lambda: state.admin
    service = service_world.build()
    app.dependency_overrides[get_tenant_export_service] = lambda: service
    state.http = TestClient(app)
    return state


def test_the_management_requests_an_export(client) -> None:
    response = client.http.post("/api/v1/tenants/garden/exports", json={"current_password": "right"})

    assert response.status_code == 202, response.text
    assert response.json()["status"] == "pending"
    listed = client.http.get("/api/v1/tenants/garden/exports")
    assert [row["key"] for row in listed.json()] == [response.json()["key"]]


def test_an_api_key_is_403(client) -> None:
    client.api_key = True
    response = client.http.post("/api/v1/tenants/garden/exports", json={"current_password": "right"})
    assert response.status_code == 403


def test_no_step_up_is_401(client) -> None:
    response = client.http.post("/api/v1/tenants/garden/exports", json={})
    assert response.status_code == 401
    assert client.world.exports.rows == {}


@pytest.mark.parametrize("slug", ["other", "no-such-garden"])
def test_a_foreign_and_an_unknown_slug_are_the_same_403(client, slug: str) -> None:
    response = client.http.post(f"/api/v1/tenants/{slug}/exports", json={"current_password": "right"})
    assert response.status_code == 403
    assert response.json()["message"] == "Exporting a tenant requires the lead role and the management scope."


def test_an_import_by_a_member_who_is_no_platform_admin_is_403(client) -> None:
    response = client.http.post(
        "/api/v1/admin/platform/tenant-imports",
        files={"archive": ("a.zip", b"PK", "application/zip")},
        data={"current_password": "right"},
    )
    assert response.status_code == 403
