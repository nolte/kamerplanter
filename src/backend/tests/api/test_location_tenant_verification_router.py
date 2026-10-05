"""API tests for tenant-scoped location CRUD with site_key verification (Issue #717).

Tests the re-verification of the location's site_key against the tenant on both
create and update operations. Ensures that a foreign (unowned) site_key is
rejected with 404 and never persisted (AC-1, AC-2, AC-3).

#2107 (MT-010) moved the check from the router into ``SiteService``: the handler
used to call ``get_site``/``get_location`` and then an unscoped write. These tests
therefore run the **real** service over a repository double — a service mock would
agree with any router, including one that no longer checks anything.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.locations.schemas import LocationCreate
from app.api.v1.locations.tenant_router import router as locations_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_site_service
from app.common.enums import IrrigationSystem, LightType, Orientation, SiteType, TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError, NotFoundError
from app.domain.models.site import Location, Site
from app.domain.models.tenant_context import TenantContext
from app.domain.services.site_service import SiteService

TENANT_KEY = "t-owned-1"
TENANT_KEY_FOREIGN = "t-foreign-1"


def _ctx() -> TenantContext:
    """Current tenant context (own tenant)."""
    return TenantContext(
        tenant_key=TENANT_KEY,
        tenant_slug="owned-slug",
        user_key="user-1",
        role=TenantRole.GROWER,
    )


def _make_site(key: str, tenant_key: str = TENANT_KEY) -> Site:
    return Site(_key=key, name="Test Site", tenant_key=tenant_key, type=SiteType.INDOOR, total_area_m2=10.0)


def _make_location(key: str, name: str = "Greenhouse", site_key: str = "site-1") -> Location:
    return Location(
        _key=key,
        name=name,
        site_key=site_key,
        area_m2=10.0,
        orientation=Orientation.NORTH,
        light_type=LightType.NATURAL,
        irrigation_system=IrrigationSystem.MANUAL,
    )


def _repo() -> MagicMock:
    """A site repository with two own sites, one foreign site and one own location."""
    sites = {
        "site-1": _make_site("site-1"),
        "site-2": _make_site("site-2"),
        "site-foreign": _make_site("site-foreign", tenant_key=TENANT_KEY_FOREIGN),
    }
    locations = {"loc-1": _make_location("loc-1", site_key="site-1")}

    def site_or_raise(key: str) -> Site:
        if key not in sites:
            raise NotFoundError("Site", key)
        return sites[key]

    def location_or_raise(key: str) -> Location:
        if key not in locations:
            raise NotFoundError("Location", key)
        return locations[key]

    repo = MagicMock()
    repo.get_site_or_raise.side_effect = site_or_raise
    repo.get_site_by_key.side_effect = sites.get
    repo.get_location_or_raise.side_effect = location_or_raise
    repo.get_location_by_key.side_effect = locations.get
    repo.create_location.side_effect = lambda loc: loc.model_copy(update={"key": "loc-new"})
    repo.update_location.side_effect = lambda key, loc: loc.model_copy(update={"key": key})
    return repo


def _client(repo: MagicMock) -> TestClient:
    app = FastAPI()
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.include_router(locations_router, prefix="/api/v1/t/owned-slug")
    app.dependency_overrides[get_site_service] = lambda: SiteService(repo)
    app.dependency_overrides[get_current_tenant] = _ctx
    return TestClient(app)


def _body(site_key: str, name: str = "Greenhouse") -> dict:
    return LocationCreate(name=name, site_key=site_key, area_m2=20.0, orientation=Orientation.SOUTH).model_dump()


def test_create_location_with_own_site_succeeds():
    """AC-2: create_location with own site_key → 201, persisted."""
    repo = _repo()
    resp = _client(repo).post("/api/v1/t/owned-slug/locations", json=_body("site-1"))

    assert resp.status_code == 201, resp.text
    repo.create_location.assert_called_once()


def test_create_location_with_foreign_site_returns_404():
    """AC-3: create_location with foreign site_key → 404, not persisted."""
    repo = _repo()
    resp = _client(repo).post("/api/v1/t/owned-slug/locations", json=_body("site-foreign"))

    assert resp.status_code == 404
    repo.create_location.assert_not_called()


def test_update_location_keeps_own_site_succeeds():
    """AC-2: update_location keeping own site_key → 200, persisted."""
    repo = _repo()
    resp = _client(repo).put("/api/v1/t/owned-slug/locations/loc-1", json=_body("site-1", "Updated"))

    assert resp.status_code == 200, resp.text
    repo.update_location.assert_called_once()


def test_update_location_switches_to_own_site_succeeds():
    """AC-2: update_location switching to another own site_key → 200, persisted."""
    repo = _repo()
    resp = _client(repo).put("/api/v1/t/owned-slug/locations/loc-1", json=_body("site-2", "Moved"))

    assert resp.status_code == 200, resp.text
    repo.update_location.assert_called_once()


def test_update_location_with_foreign_site_returns_404_does_not_persist():
    """AC-1: update_location with foreign site_key → 404, NOT persisted."""
    repo = _repo()
    resp = _client(repo).put("/api/v1/t/owned-slug/locations/loc-1", json=_body("site-foreign", "Malicious"))

    assert resp.status_code == 404
    repo.update_location.assert_not_called()


def test_update_nonexistent_location_returns_404():
    """Regression: update_location on non-existent location → 404."""
    repo = _repo()
    resp = _client(repo).put("/api/v1/t/owned-slug/locations/nonexistent-loc", json=_body("site-1"))

    assert resp.status_code == 404
    repo.update_location.assert_not_called()


def test_delete_of_a_location_in_a_foreign_site_is_404_and_deletes_nothing():
    """#2107: the delete handler no longer pre-checks; the service does."""
    repo = _repo()
    repo.get_location_or_raise.side_effect = lambda key: _make_location(key, site_key="site-foreign")
    client = _client(repo)
    lead = _ctx().model_copy(update={"role": TenantRole.LEAD})  # delete is lead-only (REQ-049 §2.3)
    client.app.dependency_overrides[get_current_tenant] = lambda: lead  # type: ignore[attr-defined]
    resp = client.delete("/api/v1/t/owned-slug/locations/loc-x")

    assert resp.status_code == 404
    repo.delete_location.assert_not_called()
