import pytest
from pydantic import ValidationError

from app.domain.models.sensor import Sensor


class TestSensor:
    def test_sensor_valid_creation(self):
        sensor = Sensor(
            name="Tank EC Sensor",
            metric_type="ec_ms",
            ha_entity_id="sensor.tank_ec",
            tank_key="tank-001",
        )
        assert sensor.name == "Tank EC Sensor"
        assert sensor.metric_type == "ec_ms"
        assert sensor.ha_entity_id == "sensor.tank_ec"
        assert sensor.tank_key == "tank-001"
        assert sensor.is_active is True
        assert sensor.mqtt_topic is None
        assert sensor.key is None

    def test_sensor_metric_type_examples(self):
        metric_types = [
            "ec_ms",
            "ph",
            "water_temp_celsius",
            "fill_level_percent",
            "tds_ppm",
            "dissolved_oxygen_mgl",
            "orp_mv",
        ]
        for mt in metric_types:
            sensor = Sensor(name=f"Sensor {mt}", metric_type=mt)
            assert sensor.metric_type == mt

    def test_sensor_defaults(self):
        sensor = Sensor(name="Minimal", metric_type="ph")
        assert sensor.is_active is True
        assert sensor.ha_entity_id is None
        assert sensor.mqtt_topic is None
        assert sensor.tank_key is None
        assert sensor.site_key is None
        assert sensor.location_key is None
        assert sensor.created_at is None
        assert sensor.updated_at is None

    def test_sensor_with_mqtt(self):
        sensor = Sensor(
            name="MQTT pH",
            metric_type="ph",
            mqtt_topic="kamerplanter/tank/ph",
            tank_key="tank-002",
        )
        assert sensor.mqtt_topic == "kamerplanter/tank/ph"
        assert sensor.ha_entity_id is None

    def test_sensor_key_alias(self):
        sensor = Sensor(_key="s-001", name="Test", metric_type="ec_ms")
        assert sensor.key == "s-001"


class TestSensorParentValidation:
    def test_single_parent_tank_valid(self):
        sensor = Sensor(name="Tank Sensor", metric_type="ec_ms", tank_key="t1")
        assert sensor.tank_key == "t1"
        assert sensor.site_key is None
        assert sensor.location_key is None

    def test_single_parent_site_valid(self):
        sensor = Sensor(name="Site Sensor", metric_type="temperature_celsius", site_key="s1")
        assert sensor.site_key == "s1"
        assert sensor.tank_key is None
        assert sensor.location_key is None

    def test_single_parent_location_valid(self):
        sensor = Sensor(name="Location Sensor", metric_type="humidity_percent", location_key="l1")
        assert sensor.location_key == "l1"
        assert sensor.tank_key is None
        assert sensor.site_key is None

    def test_no_parent_valid(self):
        sensor = Sensor(name="Orphan Sensor", metric_type="ph")
        assert sensor.tank_key is None
        assert sensor.site_key is None
        assert sensor.location_key is None

    def test_two_parents_tank_and_site_raises(self):
        with pytest.raises(ValidationError, match="at most one"):
            Sensor(name="Bad", metric_type="ec_ms", tank_key="t1", site_key="s1")

    def test_two_parents_tank_and_location_raises(self):
        with pytest.raises(ValidationError, match="at most one"):
            Sensor(name="Bad", metric_type="ec_ms", tank_key="t1", location_key="l1")

    def test_two_parents_site_and_location_raises(self):
        with pytest.raises(ValidationError, match="at most one"):
            Sensor(name="Bad", metric_type="ec_ms", site_key="s1", location_key="l1")

    def test_three_parents_raises(self):
        with pytest.raises(ValidationError, match="at most one"):
            Sensor(name="Bad", metric_type="ec_ms", tank_key="t1", site_key="s1", location_key="l1")
