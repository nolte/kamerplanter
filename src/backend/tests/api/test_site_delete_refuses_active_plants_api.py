"""#2513 WP-3 — ``DELETE /sites/{key}`` with a plant still on the site answers 409 ``site.has_active_plants``.

Drives the real router, the real ``SiteService`` and the application's real ``KamerplanterError`` handler over a
fake repository whose transactional delete refuses, so the asserted body is the shape a client actually receives
(``error_code`` top level, ``details[0].code`` and ``details[0].active_plant_count``).
"""

from __future__ import annotations

from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.sites.tenant_router import router as sites_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_site_service
from app.common.enums import TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError, PlanError
from app.domain.models.site import Site
from app.domain.models.tenant_context import TenantContext
from app.domain.services.site_service import SiteService

TENANT_SLUG = "anna"
TENANT_KEY = "tenant_anna"


def _client(repo: MagicMock) -> TestClient:
    app = FastAPI()
    app.include_router(sites_router, prefix="/api/v1/t/{tenant_slug}")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[get_site_service] = lambda: SiteService(repo)
    app.dependency_overrides[get_current_tenant] = lambda: TenantContext(
        tenant_key=TENANT_KEY, tenant_slug=TENANT_SLUG, user_key="user_anna", role=TenantRole.LEAD
    )
    return TestClient(app)


def _repo() -> MagicMock:
    repo = MagicMock()
    repo.get_site_or_raise.return_value = Site(_key="site-1", name="Garden", tenant_key=TENANT_KEY, type="outdoor")
    return repo


def test_a_site_with_an_active_plant_answers_409_with_the_published_code() -> None:
    repo = _repo()
    repo.delete_site.side_effect = PlanError(
        "site.has_active_plants",
        "A site with active plants cannot be deleted.",
        status_code=409,
        active_plant_count=1,
    )

    resp = _client(repo).delete(f"/api/v1/t/{TENANT_SLUG}/sites/site-1")

    assert resp.status_code == 409
    body = resp.json()
    assert body["error_code"] == "site.has_active_plants"
    assert body["details"][0]["code"] == "site.has_active_plants"
    assert body["details"][0]["active_plant_count"] == 1
    repo.delete_site.assert_called_once_with("site-1", tenant_key=TENANT_KEY, user_key="user_anna")


def test_a_site_without_active_plants_is_deleted_with_204() -> None:
    repo = _repo()
    repo.delete_site.return_value = True

    resp = _client(repo).delete(f"/api/v1/t/{TENANT_SLUG}/sites/site-1")

    assert resp.status_code == 204
    repo.delete_site.assert_called_once_with("site-1", tenant_key=TENANT_KEY, user_key="user_anna")


def test_the_409_is_documented_on_the_delete_route() -> None:
    app = FastAPI()
    app.include_router(sites_router, prefix="/api/v1/t/{tenant_slug}")
    operation = app.openapi()["paths"]["/api/v1/t/{tenant_slug}/sites/{key}"]["delete"]
    assert "409" in operation["responses"]
