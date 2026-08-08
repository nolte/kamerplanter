"""REQ-024 §1a.6 / REQ-049 §2.3 — the require_permission write gate, end to end.

These tests drive a *real* ``require_permission`` dependency (composed on top of
the real ``get_current_tenant``) through the sites router — a representative
plant-domain resource with a create, an update and a delete — for every domain
role plus a caller who is not a member of the tenant.

The point is both directions:

* the refusals (viewer write, grower delete, non-member) must be 403, and
* the allowances (grower create/update, lead everything) must still succeed,

so the gate is a real permission boundary and not a blanket refusal (the #324
half). ``get_current_tenant`` is overridden with a concrete ``TenantContext`` so
the genuine engine predicate runs against a genuine role — no mock that never
becomes a model (#996).
"""

from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.v1.sites.tenant_router import router as sites_router
from app.common.auth import get_current_tenant, get_current_user
from app.common.dependencies import get_site_service, get_tenant_service
from app.common.enums import TenantRole
from app.common.exceptions import KamerplanterError
from app.domain.models.site import Site
from app.domain.models.tenant_context import TenantContext
from app.domain.models.user import User

TENANT_SLUG = "anna"
TENANT_KEY = "tenant_anna"


def _ctx(role: TenantRole) -> TenantContext:
    return TenantContext(tenant_key=TENANT_KEY, tenant_slug=TENANT_SLUG, user_key="user_anna", role=role)


def _app_error_handler(_request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error_code": exc.error_code, "message": exc.message})


def _site() -> Site:
    return Site(_key="site-1", name="Bed 1", tenant_key=TENANT_KEY)


def _build_app(role: TenantRole) -> tuple[FastAPI, MagicMock]:
    service = MagicMock()
    service.get_site.return_value = _site()
    service.create_site.return_value = _site()
    service.update_site.return_value = _site()
    service.delete_site.return_value = None
    service.get_water_warnings.return_value = []

    app = FastAPI()
    app.include_router(sites_router, prefix="/api/v1/t/{tenant_slug}")
    app.add_exception_handler(KamerplanterError, _app_error_handler)
    app.dependency_overrides[get_site_service] = lambda: service
    app.dependency_overrides[get_current_tenant] = lambda: _ctx(role)
    return app, service


def _client(role: TenantRole) -> tuple[TestClient, MagicMock]:
    app, service = _build_app(role)
    return TestClient(app), service


# --------------------------------------------------------------------------
# viewer — every write refused
# --------------------------------------------------------------------------


def test_viewer_create_forbidden() -> None:
    client, service = _client(TenantRole.VIEWER)
    resp = client.post(f"/api/v1/t/{TENANT_SLUG}/sites", json={"name": "Bed 2"})
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "FORBIDDEN"
    service.create_site.assert_not_called()


def test_viewer_update_forbidden() -> None:
    client, service = _client(TenantRole.VIEWER)
    resp = client.put(f"/api/v1/t/{TENANT_SLUG}/sites/site-1", json={"name": "Bed 2"})
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "FORBIDDEN"
    service.update_site.assert_not_called()


def test_viewer_delete_forbidden() -> None:
    client, service = _client(TenantRole.VIEWER)
    resp = client.delete(f"/api/v1/t/{TENANT_SLUG}/sites/site-1")
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "FORBIDDEN"
    service.delete_site.assert_not_called()


# --------------------------------------------------------------------------
# grower — create/update allowed, delete refused (LEAD-only boundary)
# --------------------------------------------------------------------------


def test_grower_create_allowed() -> None:
    client, service = _client(TenantRole.GROWER)
    resp = client.post(f"/api/v1/t/{TENANT_SLUG}/sites", json={"name": "Bed 2"})
    assert resp.status_code == 201
    service.create_site.assert_called_once()


def test_grower_update_allowed() -> None:
    client, service = _client(TenantRole.GROWER)
    resp = client.put(f"/api/v1/t/{TENANT_SLUG}/sites/site-1", json={"name": "Bed 2"})
    assert resp.status_code == 200
    service.update_site.assert_called_once()


def test_grower_delete_forbidden() -> None:
    client, service = _client(TenantRole.GROWER)
    resp = client.delete(f"/api/v1/t/{TENANT_SLUG}/sites/site-1")
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "FORBIDDEN"
    service.delete_site.assert_not_called()


# --------------------------------------------------------------------------
# lead — everything allowed
# --------------------------------------------------------------------------


def test_lead_create_allowed() -> None:
    client, service = _client(TenantRole.LEAD)
    resp = client.post(f"/api/v1/t/{TENANT_SLUG}/sites", json={"name": "Bed 2"})
    assert resp.status_code == 201
    service.create_site.assert_called_once()


def test_lead_update_allowed() -> None:
    client, service = _client(TenantRole.LEAD)
    resp = client.put(f"/api/v1/t/{TENANT_SLUG}/sites/site-1", json={"name": "Bed 2"})
    assert resp.status_code == 200
    service.update_site.assert_called_once()


def test_lead_delete_allowed() -> None:
    client, service = _client(TenantRole.LEAD)
    resp = client.delete(f"/api/v1/t/{TENANT_SLUG}/sites/site-1")
    assert resp.status_code == 204
    service.delete_site.assert_called_once()


# --------------------------------------------------------------------------
# reads stay open for a viewer
# --------------------------------------------------------------------------


def test_viewer_read_allowed() -> None:
    client, _service = _client(TenantRole.VIEWER)
    resp = client.get(f"/api/v1/t/{TENANT_SLUG}/sites/site-1")
    assert resp.status_code == 200


# --------------------------------------------------------------------------
# non-member — refused at get_current_tenant, before the gate even runs
# --------------------------------------------------------------------------


def _build_non_member_app() -> FastAPI:
    """Drive the *real* get_current_tenant with a tenant_service that reports
    no membership for the caller, so the fail-closed refusal is observed."""
    service = MagicMock()
    tenant = MagicMock()
    tenant.key = TENANT_KEY
    tenant.slug = TENANT_SLUG
    tenant_service = MagicMock()
    tenant_service.get_tenant_by_slug.return_value = tenant
    tenant_service.get_membership.return_value = None  # not a member

    app = FastAPI()
    app.include_router(sites_router, prefix="/api/v1/t/{tenant_slug}")
    app.add_exception_handler(KamerplanterError, _app_error_handler)
    app.dependency_overrides[get_site_service] = lambda: service
    app.dependency_overrides[get_current_user] = lambda: User(
        _key="outsider", email="out@example.com", display_name="Outsider"
    )
    app.dependency_overrides[get_tenant_service] = lambda: tenant_service
    return app


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("post", f"/api/v1/t/{TENANT_SLUG}/sites"),
        ("put", f"/api/v1/t/{TENANT_SLUG}/sites/site-1"),
        ("delete", f"/api/v1/t/{TENANT_SLUG}/sites/site-1"),
    ],
)
def test_non_member_write_forbidden(method: str, path: str) -> None:
    client = TestClient(_build_non_member_app())
    resp = client.request(method, path, json={"name": "Bed 2"})
    # 403 (not 404): the tenant exists; the caller simply has no standing in it.
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "FORBIDDEN"
