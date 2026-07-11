"""REQ-039 — API tests for the hardiness-zone endpoints.

Covers the global read-only catalog router and the tenant-scoped per-site
resolution / read endpoints through ``TestClient`` with the real
:class:`HardinessZoneService` backed by in-memory mock repositories.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.v1.hardiness_zones.router import router as global_router
from app.api.v1.sites.tenant_router import router as sites_router
from app.common.auth import get_current_tenant, get_current_user
from app.common.dependencies import get_hardiness_zone_service
from app.common.enums import TenantRole
from app.common.exceptions import KamerplanterError
from app.domain.models.hardiness_zone import HardinessZone
from app.domain.models.site import Site
from app.domain.models.tenant_context import TenantContext
from app.domain.models.weather import ClimateNormal
from app.domain.services.hardiness_zone_service import HardinessZoneService

TENANT_SLUG = "anna"
TENANT_KEY = "tenant_anna"


def _zone(label: str) -> HardinessZone:
    return HardinessZone(
        zone=label,
        zone_number=int(label[:-1]),
        subzone=label[-1],
        temp_min_c=-17.78,
        temp_max_c=-15.0,
        temp_min_f=0.0,
        temp_max_f=5.0,
        description_de="Testzone",
        typical_last_frost_md="05-15",
        typical_first_frost_md="10-10",
    )


def _site(**overrides) -> Site:
    data = {
        "_key": "site1",
        "tenant_key": TENANT_KEY,
        "name": "Beet",
        "type": "outdoor",
        "gps_coordinates": (52.5, 13.4),
    }
    data.update(overrides)
    return Site(**data)


def _normal() -> ClimateNormal:
    return ClimateNormal(
        site_key="site1",
        tenant_key=TENANT_KEY,
        source="nasa-power",
        fetched_at=datetime.now(tz=UTC),
        coldest_month_min_c=-17.0,  # → 7a
        monthly_temp_min_c=[-17.0] * 12,
    )


def _error_handler(request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error_code": exc.error_code, "message": exc.message})


def _build(site: Site | None = None, normals: list[ClimateNormal] | None = None, zone_doc=None):
    site_repo = MagicMock()
    site_repo.get_site_by_key.return_value = site if site is not None else _site()
    site_repo.update_site.side_effect = lambda key, updated: updated
    climate_repo = MagicMock()
    climate_repo.get_by_site.return_value = normals if normals is not None else [_normal()]
    zone_repo = MagicMock()
    zone_repo.get_all_zones.return_value = [_zone("7a"), _zone("7b")]
    zone_repo.get_by_zone.side_effect = lambda z: _zone(z) if (zone_doc is None and z in {"7a", "7b"}) else zone_doc
    service = HardinessZoneService(zone_repo=zone_repo, site_repo=site_repo, climate_normal_repo=climate_repo)

    app = FastAPI()
    app.include_router(global_router, prefix="/api/v1")
    app.include_router(sites_router, prefix="/api/v1/t/{tenant_slug}")
    app.add_exception_handler(KamerplanterError, _error_handler)
    app.dependency_overrides[get_current_user] = lambda: {"user_key": "user_anna"}
    app.dependency_overrides[get_current_tenant] = lambda: TenantContext(
        tenant_key=TENANT_KEY, tenant_slug=TENANT_SLUG, user_key="user_anna", role=TenantRole.ADMIN
    )
    app.dependency_overrides[get_hardiness_zone_service] = lambda: service
    return app, service, zone_repo


class TestCatalog:
    def test_list_zones(self) -> None:
        app, _service, _repo = _build()
        resp = TestClient(app).get("/api/v1/hardiness-zones")
        assert resp.status_code == 200
        labels = [z["zone"] for z in resp.json()]
        assert labels == ["7a", "7b"]

    def test_get_zone(self) -> None:
        app, _service, _repo = _build()
        resp = TestClient(app).get("/api/v1/hardiness-zones/7a")
        assert resp.status_code == 200
        assert resp.json()["zone"] == "7a"
        assert resp.json()["temp_min_f"] == 0.0

    def test_get_unknown_zone_404(self) -> None:
        app, _service, repo = _build()
        repo.get_by_zone.side_effect = lambda z: None
        resp = TestClient(app).get("/api/v1/hardiness-zones/99a")
        assert resp.status_code == 404


class TestSiteResolution:
    def _base(self) -> str:
        return f"/api/v1/t/{TENANT_SLUG}/sites/site1"

    def test_resolve_derives_zone(self) -> None:
        app, _service, _repo = _build()
        resp = TestClient(app).post(f"{self._base()}/resolve-hardiness-zone")
        assert resp.status_code == 200
        body = resp.json()
        assert body["hardiness_zone"] == "7a"
        assert body["hardiness_zone_source"] == "derived_gps"
        assert body["mean_annual_minimum_c"] == -17.0
        assert body["zone"]["zone"] == "7a"

    def test_resolve_without_normals_422(self) -> None:
        app, _service, _repo = _build(normals=[])
        resp = TestClient(app).post(f"{self._base()}/resolve-hardiness-zone")
        assert resp.status_code == 422

    def test_get_site_hardiness(self) -> None:
        site = _site(hardiness_zone="7a", hardiness_zone_source="derived_gps")
        app, _service, _repo = _build(site=site)
        resp = TestClient(app).get(f"{self._base()}/hardiness")
        assert resp.status_code == 200
        assert resp.json()["hardiness_zone"] == "7a"
        assert resp.json()["zone"]["zone"] == "7a"

    def test_foreign_tenant_site_404(self) -> None:
        app, _service, _repo = _build(site=_site(tenant_key="other"))
        resp = TestClient(app).get(f"{self._base()}/hardiness")
        assert resp.status_code == 404
