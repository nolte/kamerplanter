from unittest.mock import MagicMock

import pytest

from app.domain.models.sensor import Sensor
from app.domain.services.sensor_service import SensorService


@pytest.fixture
def mock_repo():
    return MagicMock()


@pytest.fixture
def mock_ha_client():
    return MagicMock()


@pytest.fixture
def service(mock_repo, mock_ha_client):
    return SensorService(mock_repo, mock_ha_client)


@pytest.fixture
def service_no_ha(mock_repo):
    return SensorService(mock_repo, None)


class TestGetLiveState:
    def test_no_ha_client(self, service_no_ha, mock_repo):
        mock_repo.find_by_tank.return_value = [
            Sensor(name="EC", metric_type="ec_ms", ha_entity_id="sensor.ec", tank_key="t1"),
        ]
        result = service_no_ha.get_live_state("t1")
        assert result["source"] == "unavailable"
        assert result["values"] == {}
        assert result["message"] == "Home Assistant not configured"

    def test_no_sensors(self, service, mock_repo, mock_ha_client):
        mock_repo.find_by_tank.return_value = []
        result = service.get_live_state("t1")
        assert result["source"] == "ha_live"
        assert result["values"] == {}
        assert result["errors"] == []

    def test_success(self, service, mock_repo, mock_ha_client):
        mock_repo.find_by_tank.return_value = [
            Sensor(name="EC Sensor", metric_type="ec_ms", ha_entity_id="sensor.tank_ec", tank_key="t1"),
        ]
        mock_ha_client.get_state.return_value = {
            "value": 1.45,
            "last_changed": "2026-03-01T10:00:00Z",
            "entity_id": "sensor.tank_ec",
            "unit": "mS/cm",
        }
        result = service.get_live_state("t1")
        assert result["source"] == "ha_live"
        assert "ec_ms" in result["values"]
        assert result["values"]["ec_ms"]["value"] == 1.45
        assert result["values"]["ec_ms"]["entity_id"] == "sensor.tank_ec"
        assert result["values"]["ec_ms"]["unit"] == "mS/cm"
        assert result["errors"] == []

    def test_ha_error(self, service, mock_repo, mock_ha_client):
        mock_repo.find_by_tank.return_value = [
            Sensor(name="EC Sensor", metric_type="ec_ms", ha_entity_id="sensor.tank_ec", tank_key="t1"),
        ]
        mock_ha_client.get_state.side_effect = Exception("Connection refused")
        result = service.get_live_state("t1")
        assert result["source"] == "ha_live"
        assert result["values"] == {}
        assert len(result["errors"]) == 1
        assert result["errors"][0]["entity_id"] == "sensor.tank_ec"
        assert "Connection refused" in result["errors"][0]["error"]

    def test_entity_unavailable(self, service, mock_repo, mock_ha_client):
        mock_repo.find_by_tank.return_value = [
            Sensor(name="EC Sensor", metric_type="ec_ms", ha_entity_id="sensor.tank_ec", tank_key="t1"),
        ]
        mock_ha_client.get_state.return_value = {
            "value": None,
            "last_changed": "2026-03-01T10:00:00Z",
            "entity_id": "sensor.tank_ec",
            "unit": None,
        }
        result = service.get_live_state("t1")
        assert result["source"] == "ha_live"
        assert result["values"] == {}  # value was None, not included
        assert result["errors"] == []

    def test_multiple_sensors(self, service, mock_repo, mock_ha_client):
        mock_repo.find_by_tank.return_value = [
            Sensor(name="EC", metric_type="ec_ms", ha_entity_id="sensor.ec", tank_key="t1"),
            Sensor(name="pH", metric_type="ph", ha_entity_id="sensor.ph", tank_key="t1"),
        ]
        mock_ha_client.get_state.side_effect = [
            {"value": 1.2, "last_changed": "2026-03-01T10:00:00Z", "entity_id": "sensor.ec", "unit": "mS/cm"},
            {"value": 6.1, "last_changed": "2026-03-01T10:01:00Z", "entity_id": "sensor.ph", "unit": "pH"},
        ]
        result = service.get_live_state("t1")
        assert len(result["values"]) == 2
        assert result["values"]["ec_ms"]["value"] == 1.2
        assert result["values"]["ph"]["value"] == 6.1

    def test_sensor_without_entity_id_skipped(self, service, mock_repo, mock_ha_client):
        mock_repo.find_by_tank.return_value = [
            Sensor(name="MQTT only", metric_type="ec_ms", mqtt_topic="tank/ec", tank_key="t1"),
        ]
        result = service.get_live_state("t1")
        assert result["source"] == "ha_live"
        assert result["values"] == {}
        mock_ha_client.get_state.assert_not_called()


class TestCreateSensor:
    def test_create(self, service, mock_repo):
        sensor = Sensor(name="EC", metric_type="ec_ms", tank_key="t1")
        mock_repo.create.return_value = Sensor(
            _key="s1", name="EC", metric_type="ec_ms", tank_key="t1",
        )
        result = service.create_sensor(sensor)
        assert result.key == "s1"
        mock_repo.create.assert_called_once_with(sensor)


class TestDeleteSensor:
    def test_delete(self, service, mock_repo):
        mock_repo.delete.return_value = True
        result = service.delete_sensor("s1")
        assert result is True
        mock_repo.delete.assert_called_once_with("s1")


class TestGetSensorsForSite:
    def test_get_sensors_for_site(self, service, mock_repo):
        mock_repo.find_by_site.return_value = [
            Sensor(name="Weather Station", metric_type="temperature_celsius", site_key="site1"),
        ]
        result = service.get_sensors_for_site("site1")
        assert len(result) == 1
        assert result[0].site_key == "site1"
        mock_repo.find_by_site.assert_called_once_with("site1")

    def test_get_sensors_for_site_empty(self, service, mock_repo):
        mock_repo.find_by_site.return_value = []
        result = service.get_sensors_for_site("site1")
        assert result == []


class TestGetSensorsForLocation:
    def test_get_sensors_for_location(self, service, mock_repo):
        mock_repo.find_by_location.return_value = [
            Sensor(name="Tent Climate", metric_type="humidity_percent", location_key="loc1"),
        ]
        result = service.get_sensors_for_location("loc1")
        assert len(result) == 1
        assert result[0].location_key == "loc1"
        mock_repo.find_by_location.assert_called_once_with("loc1")


class TestGetLiveStateForSensors:
    def test_direct_sensor_list(self, service, mock_ha_client):
        sensors = [
            Sensor(name="Temp", metric_type="temperature_celsius", ha_entity_id="sensor.outdoor_temp", site_key="s1"),
        ]
        mock_ha_client.get_state.return_value = {
            "value": 22.5,
            "last_changed": "2026-03-01T12:00:00Z",
            "entity_id": "sensor.outdoor_temp",
            "unit": "°C",
        }
        result = service.get_live_state_for_sensors(sensors)
        assert result["source"] == "ha_live"
        assert result["values"]["temperature_celsius"]["value"] == 22.5

    def test_no_ha_client_returns_unavailable(self, service_no_ha):
        sensors = [
            Sensor(name="Temp", metric_type="temperature_celsius", ha_entity_id="sensor.temp", site_key="s1"),
        ]
        result = service_no_ha.get_live_state_for_sensors(sensors)
        assert result["source"] == "unavailable"
        assert result["message"] == "Home Assistant not configured"
