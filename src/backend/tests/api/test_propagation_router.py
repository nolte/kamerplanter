"""API tests for the REQ-017 tenant-scoped propagation / lineage router.

Focus: the SEC-B4 (c) role gate on destructive phenotype-note deletion — a
grower must be forbidden (403) while an admin is allowed (204), mirroring the
existing protocol-deletion gate. ``get_current_tenant`` is overridden so the
REAL ``require_tenant_role`` dependency runs against the injected context.
"""

from unittest.mock import MagicMock

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.v1.propagation.tenant_router import router as propagation_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_propagation_service
from app.common.enums import TenantRole
from app.common.exceptions import KamerplanterError
from app.domain.models.tenant_context import TenantContext

TENANT_SLUG = "anna"


def _tenant_ctx(role: TenantRole = TenantRole.GROWER) -> TenantContext:
    return TenantContext(tenant_key="tenant_anna", tenant_slug=TENANT_SLUG, user_key="user_anna", role=role)


def _app_error_handler(request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error_code": exc.error_code, "message": exc.message})


def _build_app(service, role: TenantRole = TenantRole.GROWER) -> FastAPI:
    app = FastAPI()
    app.include_router(propagation_router, prefix="/api/v1/t/{tenant_slug}")
    app.add_exception_handler(KamerplanterError, _app_error_handler)
    app.dependency_overrides[get_propagation_service] = lambda: service
    app.dependency_overrides[get_current_tenant] = lambda: _tenant_ctx(role)
    return app


def test_delete_phenotype_grower_forbidden() -> None:
    service = MagicMock()
    client = TestClient(_build_app(service, role=TenantRole.GROWER))

    resp = client.delete(f"/api/v1/t/{TENANT_SLUG}/plant-instances/plant-1/phenotypes/note-1")

    assert resp.status_code == 403
    service.delete_phenotype.assert_not_called()


def test_delete_phenotype_viewer_forbidden() -> None:
    service = MagicMock()
    client = TestClient(_build_app(service, role=TenantRole.VIEWER))

    resp = client.delete(f"/api/v1/t/{TENANT_SLUG}/plant-instances/plant-1/phenotypes/note-1")

    assert resp.status_code == 403
    service.delete_phenotype.assert_not_called()


def test_delete_phenotype_admin_allowed() -> None:
    service = MagicMock()
    service.delete_phenotype.return_value = None
    client = TestClient(_build_app(service, role=TenantRole.LEAD))

    resp = client.delete(f"/api/v1/t/{TENANT_SLUG}/plant-instances/plant-1/phenotypes/note-1")

    assert resp.status_code == 204
    service.delete_phenotype.assert_called_once_with("plant-1", "note-1", "tenant_anna")
