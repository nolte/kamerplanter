"""API tests for tenant-scoped location CRUD with site_key verification (Issue #717).

Tests the re-verification of the location's site_key against the tenant on both
create and update operations. Ensures that a foreign (unowned) site_key is
rejected with 404 and never persisted (AC-1, AC-2, AC-3).
"""

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


def _build_app(site_service) -> FastAPI:
    app = FastAPI()
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.include_router(locations_router, prefix="/api/v1/t/owned-slug")
    app.dependency_overrides[get_site_service] = lambda: site_service
    app.dependency_overrides[get_current_tenant] = _ctx
    return app


def _make_site(key: str, tenant_key: str = TENANT_KEY) -> Site:
    """Factory: create a Site with the given key and tenant."""
    return Site(
        _key=key,
        name="Test Site",
        tenant_key=tenant_key,
        type=SiteType.INDOOR,
        total_area_m2=10.0,
    )


def _make_location(
    key: str,
    name: str = "Greenhouse",
    site_key: str = "site-1",
    tenant_key: str = TENANT_KEY,
) -> Location:
    """Factory: create a Location with the given key and site."""
    return Location(
        _key=key,
        name=name,
        site_key=site_key,
        tenant_key=tenant_key,
        area_m2=10.0,
        orientation=Orientation.NORTH,
        light_type=LightType.NATURAL,
        irrigation_system=IrrigationSystem.MANUAL,
    )


def test_create_location_with_own_site_succeeds():
    """AC-2: create_location with own site_key → 201, persisted."""
    site_service = MagicMock()
    site_service.get_site.return_value = _make_site("site-1", tenant_key=TENANT_KEY)
    site_service.create_location.return_value = _make_location("loc-1")
    client = TestClient(_build_app(site_service))

    body = LocationCreate(
        name="New Greenhouse",
        site_key="site-1",
        area_m2=20.0,
        orientation=Orientation.SOUTH,
    )
    resp = client.post(
        "/api/v1/t/owned-slug/locations",
        json=body.model_dump(),
    )

    assert resp.status_code == 201
    site_service.create_location.assert_called_once()


def test_create_location_with_foreign_site_returns_404():
    """AC-3: create_location with foreign site_key → 404, not persisted."""
    site_service = MagicMock()
    site_service.get_site.side_effect = NotFoundError("Site", "site-foreign")
    client = TestClient(_build_app(site_service))

    body = LocationCreate(
        name="New Greenhouse",
        site_key="site-foreign",
        area_m2=20.0,
        orientation=Orientation.SOUTH,
    )
    resp = client.post(
        "/api/v1/t/owned-slug/locations",
        json=body.model_dump(),
    )

    assert resp.status_code == 404
    site_service.create_location.assert_not_called()


def test_update_location_keeps_own_site_succeeds():
    """AC-2: update_location keeping own site_key → 200, persisted."""
    site_service = MagicMock()
    # First call: get_location (from _verify_location_tenant)
    site_service.get_location.return_value = _make_location("loc-1", site_key="site-1", tenant_key=TENANT_KEY)
    # Second call: verify the new site_key also belongs to tenant
    site_service.get_site.return_value = _make_site("site-1", tenant_key=TENANT_KEY)
    site_service.update_location.return_value = _make_location("loc-1")
    client = TestClient(_build_app(site_service))

    body = LocationCreate(
        name="Updated Greenhouse",
        site_key="site-1",
        area_m2=25.0,
        orientation=Orientation.EAST,
    )
    resp = client.put(
        "/api/v1/t/owned-slug/locations/loc-1",
        json=body.model_dump(),
    )

    assert resp.status_code == 200
    site_service.update_location.assert_called_once()


def test_update_location_switches_to_own_site_succeeds():
    """AC-2: update_location switching to another own site_key → 200, persisted."""
    site_service = MagicMock()
    # First call: get_location (from _verify_location_tenant)
    site_service.get_location.return_value = _make_location("loc-1", site_key="site-1", tenant_key=TENANT_KEY)
    # Second call: verify the NEW site_key also belongs to tenant
    site_service.get_site.return_value = _make_site("site-2", tenant_key=TENANT_KEY)
    site_service.update_location.return_value = _make_location("loc-1", site_key="site-2")
    client = TestClient(_build_app(site_service))

    body = LocationCreate(
        name="Moved Greenhouse",
        site_key="site-2",
        area_m2=30.0,
        orientation=Orientation.WEST,
    )
    resp = client.put(
        "/api/v1/t/owned-slug/locations/loc-1",
        json=body.model_dump(),
    )

    assert resp.status_code == 200
    site_service.update_location.assert_called_once()


def test_update_location_with_foreign_site_returns_404_does_not_persist():
    """AC-1: update_location with foreign site_key → 404, NOT persisted."""
    site_service = MagicMock()
    # First call: get_location (from _verify_location_tenant) succeeds
    site_service.get_location.return_value = _make_location("loc-1", site_key="site-1", tenant_key=TENANT_KEY)
    # Second call: verify the NEW site_key — FAILS because it belongs to foreign tenant
    site_service.get_site.side_effect = NotFoundError("Site", "site-foreign")
    client = TestClient(_build_app(site_service))

    body = LocationCreate(
        name="Malicious Update",
        site_key="site-foreign",
        area_m2=999.0,
        orientation=Orientation.NORTH,
    )
    resp = client.put(
        "/api/v1/t/owned-slug/locations/loc-1",
        json=body.model_dump(),
    )

    # The key assertion: 404 response AND update_location never called
    assert resp.status_code == 404
    site_service.update_location.assert_not_called()


def test_update_nonexistent_location_returns_404():
    """Regression: update_location on non-existent location → 404."""
    site_service = MagicMock()
    site_service.get_location.side_effect = NotFoundError("Location", "nonexistent-loc")
    client = TestClient(_build_app(site_service))

    body = LocationCreate(
        name="Somewhere",
        site_key="site-1",
        area_m2=10.0,
    )
    resp = client.put(
        "/api/v1/t/owned-slug/locations/nonexistent-loc",
        json=body.model_dump(),
    )

    assert resp.status_code == 404
    site_service.update_location.assert_not_called()
