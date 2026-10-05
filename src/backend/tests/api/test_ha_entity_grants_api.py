"""MT-015 (#2112): one Home Assistant instance, a per-tenant entity allowlist.

Operator decision (model A, 2026-10-04): the instance's entity inventory is listed
only to members holding the TECHNICAL scope, and only the entities the platform
admin granted to the tenant; a sensor, actuator, weather source or notification
destination naming any other entity is refused with 422, and the live read never
asks Home Assistant for an entity the tenant was not granted.

Every route is driven through FastAPI with the **real** services over an in-memory
allowlist (``tests.support.ha_entity_grants``) and a Home Assistant double that
records what it was asked — "refused" is asserted as "Home Assistant was never
asked", not merely as a status code.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.actuators.tenant_router import router as actuators_router
from app.api.v1.locations.tenant_router import router as locations_router
from app.api.v1.sites.tenant_router import router as sites_router
from app.api.v1.tanks.tenant_router import router as tanks_router
from app.api.v1.tenant_scoped.weather.tenant_router import router as weather_router
from app.common.auth import get_current_tenant
from app.common.dependencies import (
    get_actuator_service,
    get_sensor_service,
    get_site_service,
    get_tank_service,
    get_weather_source_service,
)
from app.common.enums import AdminScope, TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError
from app.domain.models.sensor import Sensor
from app.domain.models.site import Location
from app.domain.models.tenant_context import TenantContext
from app.domain.services.actuator_service import ActuatorService
from app.domain.services.sensor_service import SensorService
from app.domain.services.weather_source_service import WeatherSourceService
from tests.support.ha_entity_grants import grant_service

TENANT = "tenant-a"
SLUG = "garten-a"
PREFIX = f"/api/v1/t/{SLUG}"
GRANTED_SENSOR = "sensor.zelt_temperatur"
FOREIGN_SENSOR = "sensor.operator_haustuer"
GRANTED_WEATHER = "weather.zuhause"
FOREIGN_WEATHER = "weather.nachbar"
GRANTED_SWITCH = "switch.zelt_licht"
FOREIGN_SWITCH = "switch.operator_heizung"

INVENTORY = [
    {"entity_id": GRANTED_SENSOR, "friendly_name": "Zelt", "unit_of_measurement": "°C", "device_class": "temperature"},
    {"entity_id": FOREIGN_SENSOR, "friendly_name": "Haustür", "unit_of_measurement": None, "device_class": "door"},
]
WEATHER_INVENTORY = [
    {"entity_id": GRANTED_WEATHER, "friendly_name": "Zuhause", "state": "sunny"},
    {"entity_id": FOREIGN_WEATHER, "friendly_name": "Nachbar", "state": "rainy"},
]


class RecordingHaClient:
    """Answers every state read; records which entity ids were asked for."""

    def __init__(self) -> None:
        self.asked: list[str] = []

    def get_state(self, entity_id: str, timeout: float | None = None) -> dict | None:  # noqa: ARG002
        self.asked.append(entity_id)
        return {
            "value": 21.0,
            "last_changed": "2026-10-05T08:00:00Z",
            "last_updated": "2026-10-05T08:00:00Z",
            "last_reported": "2026-10-05T08:00:00Z",
            "entity_id": entity_id,
            "unit": "°C",
        }

    def list_sensor_entities(self) -> list[dict]:
        return [dict(e, state="21") for e in INVENTORY]

    def list_weather_entities(self) -> list[dict]:
        return [dict(e) for e in WEATHER_INVENTORY]


def _ctx(role: TenantRole = TenantRole.GROWER, *, technical: bool = False) -> TenantContext:
    return TenantContext(
        tenant_key=TENANT,
        tenant_slug=SLUG,
        user_key="user-a",
        role=role,
        admin_scopes=[AdminScope.TECHNICAL] if technical else [],
    )


def _grants() -> Any:
    return grant_service({TENANT: {GRANTED_SENSOR, GRANTED_WEATHER, GRANTED_SWITCH}, "tenant-b": {FOREIGN_SENSOR}})


def _sensor_repo(sensors: list[Sensor] | None = None) -> MagicMock:
    repo = MagicMock()
    repo.create.side_effect = lambda sensor: sensor.model_copy(update={"key": "s-new"})
    repo.find_by_location.return_value = sensors or []
    repo.find_by_site.return_value = sensors or []
    repo.find_by_tank.return_value = sensors or []
    return repo


def _site_service() -> MagicMock:
    site_service = MagicMock()
    site_service.get_location.return_value = Location(_key="loc-1", name="Zelt", site_key="site-1", area_m2=4.0)
    site_service.get_site.return_value = MagicMock()
    return site_service


def _app(ctx: TenantContext, *, ha: RecordingHaClient, sensors: list[Sensor] | None = None) -> tuple[TestClient, Any]:
    grants = _grants()
    sensor_service = SensorService(_sensor_repo(sensors), ha, ha_entity_gate=grants)
    weather_service = WeatherSourceService(
        weather_source_config_repo=MagicMock(get_by_site=MagicMock(return_value=None)),
        site_repo=MagicMock(get_site_by_key=MagicMock(return_value=MagicMock(tenant_key=TENANT, gps_coordinates=None))),
        encryption_engine=MagicMock(),
        ha_client_factory=lambda: ha,
        ha_entity_grants=grants,
    )
    app = FastAPI()
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    for router in (weather_router, tanks_router, locations_router, sites_router):
        app.include_router(router, prefix=PREFIX)
    app.dependency_overrides[get_current_tenant] = lambda: ctx
    app.dependency_overrides[get_sensor_service] = lambda: sensor_service
    app.dependency_overrides[get_weather_source_service] = lambda: weather_service
    app.dependency_overrides[get_site_service] = _site_service
    app.dependency_overrides[get_tank_service] = lambda: MagicMock()
    return TestClient(app), sensor_service


LISTINGS = ["/ha/weather-entities", "/ha/sensor-entities", "/tanks/ha-entities"]


class TestTheInventoryIsTechnicalOnly:
    @pytest.mark.parametrize("path", LISTINGS)
    @pytest.mark.parametrize("role", [TenantRole.VIEWER, TenantRole.GROWER, TenantRole.LEAD])
    def test_a_member_without_the_technical_scope_is_refused(self, path: str, role: TenantRole) -> None:
        client, _ = _app(_ctx(role), ha=RecordingHaClient())

        response = client.get(PREFIX + path)

        assert response.status_code == 403

    @pytest.mark.parametrize("path", LISTINGS)
    def test_a_viewer_with_the_technical_scope_is_admitted(self, path: str) -> None:
        client, _ = _app(_ctx(TenantRole.VIEWER, technical=True), ha=RecordingHaClient())

        assert client.get(PREFIX + path).status_code == 200

    @pytest.mark.parametrize(
        ("path", "granted", "foreign"),
        [
            ("/ha/weather-entities", GRANTED_WEATHER, FOREIGN_WEATHER),
            ("/ha/sensor-entities", GRANTED_SENSOR, FOREIGN_SENSOR),
            ("/tanks/ha-entities", GRANTED_SENSOR, FOREIGN_SENSOR),
        ],
    )
    def test_the_listing_holds_only_the_tenants_granted_entities(self, path: str, granted: str, foreign: str) -> None:
        client, _ = _app(_ctx(technical=True), ha=RecordingHaClient())

        ids = [item["entity_id"] for item in client.get(PREFIX + path).json()]

        assert ids == [granted]
        assert foreign not in ids


SENSOR_CREATE_ROUTES = [
    "/locations/loc-1/sensors",
    "/sites/site-1/sensors",
    "/tanks/tank-1/sensors",
]


class TestASensorNamesOnlyAGrantedEntity:
    @pytest.mark.parametrize("path", SENSOR_CREATE_ROUTES)
    def test_creating_with_an_entity_outside_the_allowlist_is_422(self, path: str) -> None:
        client, sensor_service = _app(_ctx(), ha=RecordingHaClient())

        response = client.post(
            PREFIX + path,
            json={"name": "Haustür", "metric_type": "temperature_celsius", "ha_entity_id": FOREIGN_SENSOR},
        )

        assert response.status_code == 422
        body = response.json()
        assert body["error_code"] == "VALIDATION_ERROR"
        assert [d["code"] for d in body["details"]] == ["HA_ENTITY_NOT_GRANTED"]
        # value-free: the refused id is not echoed back
        assert FOREIGN_SENSOR not in response.text
        sensor_service._repo.create.assert_not_called()

    @pytest.mark.parametrize("path", SENSOR_CREATE_ROUTES)
    def test_creating_with_a_granted_entity_succeeds(self, path: str) -> None:
        client, sensor_service = _app(_ctx(), ha=RecordingHaClient())

        response = client.post(
            PREFIX + path, json={"name": "Zelt", "metric_type": "temperature_celsius", "ha_entity_id": GRANTED_SENSOR}
        )

        assert response.status_code == 201, response.text
        sensor_service._repo.create.assert_called_once()

    @pytest.mark.parametrize("path", SENSOR_CREATE_ROUTES)
    def test_a_sensor_without_an_entity_needs_no_grant(self, path: str) -> None:
        client, _ = _app(_ctx(), ha=RecordingHaClient())

        response = client.post(PREFIX + path, json={"name": "Handmessung", "metric_type": "ph"})

        assert response.status_code == 201, response.text

    @pytest.mark.parametrize("parent", ["locations/loc-1", "sites/site-1", "tanks/tank-1"])
    def test_rebinding_an_existing_sensor_to_an_ungranted_entity_is_422(self, parent: str) -> None:
        field = {"locations": "location_key", "sites": "site_key", "tanks": "tank_key"}[parent.split("/")[0]]
        existing = Sensor(_key="s-1", name="Zelt", metric_type="temperature_celsius", **{field: parent.split("/")[1]})
        client, sensor_service = _app(_ctx(), ha=RecordingHaClient())
        sensor_service._repo.get.return_value = existing

        response = client.put(f"{PREFIX}/{parent}/sensors/s-1", json={"ha_entity_id": FOREIGN_SENSOR})

        assert response.status_code == 422
        sensor_service._repo.update.assert_not_called()


class TestTheLiveReadSkipsUngrantedEntities:
    def _sensors(self) -> list[Sensor]:
        return [
            Sensor(_key="s-own", name="Zelt", metric_type="temperature_celsius", ha_entity_id=GRANTED_SENSOR),
            # stored before the allowlist, or its grant was withdrawn since
            Sensor(_key="s-foreign", name="Tür", metric_type="temperature_celsius", ha_entity_id=FOREIGN_SENSOR),
        ]

    @pytest.mark.parametrize("path", ["/locations/loc-1/sensors/live", "/sites/site-1/sensors/live"])
    def test_home_assistant_is_never_asked_for_an_ungranted_entity(self, path: str) -> None:
        ha = RecordingHaClient()
        client, _ = _app(_ctx(TenantRole.VIEWER), ha=ha, sensors=self._sensors())

        body = client.get(PREFIX + path).json()

        assert ha.asked == [GRANTED_SENSOR]
        assert set(body["readings"]) == {"s-own"}
        assert {"entity_id": FOREIGN_SENSOR, "error": "not_granted"} in body["errors"]

    def test_the_tank_live_read_skips_too(self) -> None:
        ha = RecordingHaClient()
        client, _ = _app(_ctx(TenantRole.VIEWER), ha=ha, sensors=self._sensors())

        client.get(PREFIX + "/tanks/tank-1/states/live")

        assert ha.asked == [GRANTED_SENSOR]

    def test_the_frost_warning_reads_only_granted_entities(self) -> None:
        ha = RecordingHaClient()
        client, _ = _app(_ctx(TenantRole.VIEWER), ha=ha, sensors=self._sensors())

        client.get(PREFIX + "/locations/loc-1/frost-warning")

        assert ha.asked == [GRANTED_SENSOR]


def _weather_body(**ha_config: Any) -> dict:
    return {
        "enabled": True,
        "sources": [{"source_name": "ha_weather", "kind": "home_assistant", "ha_config": ha_config}],
    }


class TestAWeatherSourceNamesOnlyGrantedEntities:
    @pytest.mark.parametrize(
        "ha_config",
        [
            {"mode": "weather_entity", "weather_entity_id": FOREIGN_WEATHER},
            {"mode": "sensor_mapping", "sensor_mapping": {"temp_min_entity": FOREIGN_SENSOR}},
        ],
        ids=["weather_entity", "sensor_mapping"],
    )
    def test_saving_an_ungranted_entity_is_422(self, ha_config: dict) -> None:
        client, _ = _app(_ctx(), ha=RecordingHaClient())

        response = client.put(f"{PREFIX}/sites/site-1/weather-source", json=_weather_body(**ha_config))

        assert response.status_code == 422
        assert [d["code"] for d in response.json()["details"]] == ["HA_ENTITY_NOT_GRANTED"]

    def test_testing_an_unsaved_ungranted_entity_is_422_and_reads_nothing(self) -> None:
        ha = RecordingHaClient()
        client, _ = _app(_ctx(), ha=ha)

        response = client.post(
            f"{PREFIX}/sites/site-1/weather-sources/test",
            json={
                "source_name": "ha_weather",
                "kind": "home_assistant",
                "ha_config": {"mode": "sensor_mapping", "sensor_mapping": {"temp_min_entity": FOREIGN_SENSOR}},
            },
        )

        assert response.status_code == 422
        assert ha.asked == []


class TestAnActuatorNamesOnlyAGrantedEntity:
    def _client(self) -> tuple[TestClient, MagicMock]:
        repo = MagicMock()
        repo.get_location.return_value = Location(_key="loc-1", name="Zelt", site_key="site-1", area_m2=4.0)
        repo.create_actuator.side_effect = lambda actuator: actuator
        site_repo = MagicMock()
        site_repo.get_site_by_key.return_value = MagicMock(tenant_key=TENANT)
        service = ActuatorService(repo, ha_client_factory=lambda: None, site_repo=site_repo, ha_entity_grants=_grants())
        app = FastAPI()
        app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
        app.include_router(actuators_router, prefix=PREFIX)
        app.dependency_overrides[get_current_tenant] = lambda: _ctx(TenantRole.LEAD, technical=True)
        app.dependency_overrides[get_actuator_service] = lambda: service
        return TestClient(app), repo

    def test_the_actuator_entity_listing_holds_only_granted_entities(self) -> None:
        repo = MagicMock()
        service = ActuatorService(repo, ha_client_factory=RecordingHaClient, ha_entity_grants=_grants())
        app = FastAPI()
        app.include_router(actuators_router, prefix=PREFIX)
        app.dependency_overrides[get_current_tenant] = lambda: _ctx(TenantRole.VIEWER, technical=True)
        app.dependency_overrides[get_actuator_service] = lambda: service

        body = TestClient(app).get(f"{PREFIX}/integrations/home-assistant/entities").json()

        assert [e["entity_id"] for e in body] == [GRANTED_SENSOR]

    def _body(self, entity_id: str) -> dict:
        return {"name": "Licht", "actuator_type": "light", "protocol": "home_assistant", "ha_entity_id": entity_id}

    def test_creating_with_an_ungranted_entity_is_422(self) -> None:
        client, repo = self._client()

        response = client.post(f"{PREFIX}/locations/loc-1/actuators", json=self._body(FOREIGN_SWITCH))

        assert response.status_code == 422
        repo.create_actuator.assert_not_called()

    def test_creating_with_a_granted_entity_succeeds(self) -> None:
        client, repo = self._client()

        response = client.post(f"{PREFIX}/locations/loc-1/actuators", json=self._body(GRANTED_SWITCH))

        assert response.status_code == 201, response.text
        repo.create_actuator.assert_called_once()

    def test_rebinding_an_actuator_to_an_ungranted_entity_is_422(self) -> None:
        client, repo = self._client()
        from app.domain.models.actuator import Actuator

        repo.get_or_raise.return_value = Actuator(
            _key="a-1", tenant_key=TENANT, location_key="loc-1", **self._body(GRANTED_SWITCH)
        )

        response = client.put(f"{PREFIX}/actuators/a-1", json={"ha_entity_id": FOREIGN_SWITCH})

        assert response.status_code == 422
        repo.update_actuator.assert_not_called()
