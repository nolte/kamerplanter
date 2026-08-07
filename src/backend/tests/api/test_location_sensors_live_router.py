"""API tests for the tenant-scoped live-sensor endpoint.

``GET /locations/{key}/sensors/live`` is a published contract: the Home
Assistant integration and the frontend read it. These tests drive the real
``SensorService`` and the real response model through the router, because the
thing under test is the *shape that leaves the process* — a service that keeps
two readings and a schema that drops one would still look green in a unit test
(Issue #977).
"""

from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.locations.tenant_router import router as locations_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_sensor_service, get_site_service
from app.common.enums import TenantRole
from app.domain.models.sensor import Sensor
from app.domain.models.site import Location
from app.domain.models.tenant_context import TenantContext
from app.domain.services.sensor_service import SensorService

TENANT_KEY = "t-test-1"
LOCATION_KEY = "loc-1"

FRONT = {
    "value": 21.4,
    "last_changed": "2026-08-06T05:50:00Z",
    "last_updated": "2026-08-06T05:50:00Z",
    "last_reported": "2026-08-06T05:50:00Z",
    "entity_id": "sensor.zelt_vorne",
    "unit": "°C",
}
BACK = {
    "value": 23.9,
    "last_changed": "2026-08-06T05:59:00Z",
    "last_updated": "2026-08-06T05:59:00Z",
    "last_reported": "2026-08-06T05:59:00Z",
    "entity_id": "sensor.zelt_hinten",
    "unit": "°C",
}


def _ctx() -> TenantContext:
    return TenantContext(
        tenant_key=TENANT_KEY,
        tenant_slug="test-slug",
        user_key="user-1",
        role=TenantRole.GROWER,
    )


def _site_service_owning(location_key: str) -> MagicMock:
    site_service = MagicMock()
    site_service.get_location.return_value = Location(_key=location_key, name="Zelt", site_key="site-1", area_m2=4.0)
    site_service.get_site.return_value = MagicMock()
    return site_service


class FakeHaClient:
    def __init__(self, states: dict[str, dict]) -> None:
        self._states = states

    def get_state(self, entity_id: str, timeout: float | None = None) -> dict | None:  # noqa: ARG002
        return self._states.get(entity_id)


def _client(sensors: list[Sensor], states: dict[str, dict]) -> TestClient:
    sensor_repo = MagicMock()
    sensor_repo.find_by_location.return_value = sensors
    sensor_service = SensorService(sensor_repo, FakeHaClient(states))

    app = FastAPI()
    app.include_router(locations_router, prefix="/api/v1/t/test-slug")
    app.dependency_overrides[get_site_service] = lambda: _site_service_owning(LOCATION_KEY)
    app.dependency_overrides[get_sensor_service] = lambda: sensor_service
    app.dependency_overrides[get_current_tenant] = _ctx
    return TestClient(app)


def _two_thermometers() -> list[Sensor]:
    return [
        Sensor(
            _key="s-front",
            name="Zelt vorne",
            metric_type="temperature_celsius",
            ha_entity_id="sensor.zelt_vorne",
            location_key=LOCATION_KEY,
        ),
        Sensor(
            _key="s-back",
            name="Zelt hinten",
            metric_type="temperature_celsius",
            ha_entity_id="sensor.zelt_hinten",
            location_key=LOCATION_KEY,
        ),
    ]


def _get_live(client: TestClient) -> dict:
    resp = client.get(f"/api/v1/t/test-slug/locations/{LOCATION_KEY}/sensors/live")
    assert resp.status_code == 200
    return resp.json()


def test_both_sensors_of_one_metric_reach_the_client():
    body = _get_live(_client(_two_thermometers(), {"sensor.zelt_vorne": FRONT, "sensor.zelt_hinten": BACK}))

    assert set(body["readings"]) == {"s-front", "s-back"}
    assert body["readings"]["s-front"]["value"] == 21.4
    assert body["readings"]["s-back"]["value"] == 23.9
    assert body["source"] == "ha_live"


def test_each_reading_carries_its_sensor_identity():
    body = _get_live(_client(_two_thermometers(), {"sensor.zelt_vorne": FRONT, "sensor.zelt_hinten": BACK}))

    front = body["readings"]["s-front"]
    assert front["sensor_key"] == "s-front"
    assert front["sensor_name"] == "Zelt vorne"
    assert front["metric_type"] == "temperature_celsius"
    assert front["entity_id"] == "sensor.zelt_vorne"
    assert front["last_reported"] == "2026-08-06T05:50:00Z"


def test_the_derived_view_reports_the_collapse():
    body = _get_live(_client(_two_thermometers(), {"sensor.zelt_vorne": FRONT, "sensor.zelt_hinten": BACK}))

    entry = body["values"]["temperature_celsius"]
    assert entry["value"] == 23.9
    assert entry["sensor_key"] == "s-back"
    assert entry["sensor_count"] == 2
    assert entry["superseded_sensor_keys"] == ["s-front"]


def test_a_single_sensor_looks_exactly_as_it_did_before():
    body = _get_live(_client(_two_thermometers()[:1], {"sensor.zelt_vorne": FRONT}))

    entry = body["values"]["temperature_celsius"]
    assert entry["value"] == 21.4
    assert entry["entity_id"] == "sensor.zelt_vorne"
    assert entry["unit"] == "°C"
    assert entry["last_changed"] == "2026-08-06T05:50:00Z"
    assert entry["sensor_count"] == 1
    assert entry["superseded_sensor_keys"] == []


def test_ha_not_configured_answers_with_both_maps_empty():
    sensor_repo = MagicMock()
    sensor_repo.find_by_location.return_value = _two_thermometers()
    app = FastAPI()
    app.include_router(locations_router, prefix="/api/v1/t/test-slug")
    app.dependency_overrides[get_site_service] = lambda: _site_service_owning(LOCATION_KEY)
    app.dependency_overrides[get_sensor_service] = lambda: SensorService(sensor_repo, None)
    app.dependency_overrides[get_current_tenant] = _ctx

    body = _get_live(TestClient(app))

    assert body["readings"] == {}
    assert body["values"] == {}
    assert body["source"] == "unavailable"
    assert body["message"] == "Home Assistant not configured"
