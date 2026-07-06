"""API tests for the tenant-scoped location frost-warning endpoint.

Backs ``binary_sensor.kp_{location}_frost_warning`` (Home Assistant read path).
"""

from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.locations.tenant_router import router as locations_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_sensor_service, get_site_service
from app.common.enums import TenantRole
from app.domain.models.site import Location
from app.domain.models.tenant_context import TenantContext

TENANT_KEY = "t-test-1"


def _ctx() -> TenantContext:
    return TenantContext(
        tenant_key=TENANT_KEY,
        tenant_slug="test-slug",
        user_key="user-1",
        role=TenantRole.GROWER,
    )


def _build_app(site_service, sensor_service) -> FastAPI:
    app = FastAPI()
    app.include_router(locations_router, prefix="/api/v1/t/test-slug")
    app.dependency_overrides[get_site_service] = lambda: site_service
    app.dependency_overrides[get_sensor_service] = lambda: sensor_service
    app.dependency_overrides[get_current_tenant] = _ctx
    return app


def _site_service_owning(location_key: str) -> MagicMock:
    site_service = MagicMock()
    site_service.get_location.return_value = Location(
        _key=location_key, name="Greenhouse", site_key="site-1", area_m2=10.0
    )
    site_service.get_site.return_value = MagicMock()
    return site_service


def test_frost_warning_true():
    site_service = _site_service_owning("loc-1")
    sensor_service = MagicMock()
    sensor_service.get_location_frost_warning.return_value = {
        "location_key": "loc-1",
        "frost_warning": True,
        "temperature_celsius": 1.5,
        "threshold_celsius": 3.0,
        "source": "ha_live",
        "entity_id": "sensor.loc_temp",
    }
    client = TestClient(_build_app(site_service, sensor_service))
    resp = client.get("/api/v1/t/test-slug/locations/loc-1/frost-warning")
    assert resp.status_code == 200
    body = resp.json()
    assert body["frost_warning"] is True
    assert body["threshold_celsius"] == 3.0
    assert body["source"] == "ha_live"
    sensor_service.get_location_frost_warning.assert_called_once_with("loc-1", site_key="site-1", tenant_key=TENANT_KEY)


def test_frost_warning_unknown_when_no_temperature():
    site_service = _site_service_owning("loc-2")
    sensor_service = MagicMock()
    sensor_service.get_location_frost_warning.return_value = {
        "location_key": "loc-2",
        "frost_warning": None,
        "temperature_celsius": None,
        "threshold_celsius": 3.0,
        "source": "no_temperature",
        "entity_id": None,
    }
    client = TestClient(_build_app(site_service, sensor_service))
    resp = client.get("/api/v1/t/test-slug/locations/loc-2/frost-warning")
    assert resp.status_code == 200
    body = resp.json()
    assert body["frost_warning"] is None
    assert body["source"] == "no_temperature"
    # Additive forecast fields default to null when the service omits them.
    assert body["forecast_frost_warning"] is None
    assert body["forecast_expected_date"] is None


def test_additive_forecast_fields_flow_through():
    # Issue #392: the additive proactive fields are carried on the same response;
    # the reactive ``frost_warning`` keeps its meaning (HA compatibility).
    site_service = _site_service_owning("loc-3")
    sensor_service = MagicMock()
    sensor_service.get_location_frost_warning.return_value = {
        "location_key": "loc-3",
        "frost_warning": False,
        "temperature_celsius": 8.0,
        "threshold_celsius": 3.0,
        "source": "ha_live",
        "entity_id": "sensor.loc_temp",
        "forecast_frost_warning": True,
        "forecast_min_temperature": -1.5,
        "forecast_expected_date": "2026-07-07",
        "forecast_source": "open-meteo",
    }
    client = TestClient(_build_app(site_service, sensor_service))
    resp = client.get("/api/v1/t/test-slug/locations/loc-3/frost-warning")
    assert resp.status_code == 200
    body = resp.json()
    # Reactive field unchanged.
    assert body["frost_warning"] is False
    # Proactive fields surfaced additively.
    assert body["forecast_frost_warning"] is True
    assert body["forecast_min_temperature"] == -1.5
    assert body["forecast_expected_date"] == "2026-07-07"
    assert body["forecast_source"] == "open-meteo"
