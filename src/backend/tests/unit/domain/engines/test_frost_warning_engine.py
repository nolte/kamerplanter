"""Unit tests for the reactive frost-warning engine (REQ-005/018/039)."""

from app.domain.engines.frost_warning_engine import (
    AIR_TEMPERATURE_METRIC_TYPES,
    DEFAULT_FROST_WARNING_THRESHOLD_CELSIUS,
    evaluate_frost_warning,
    pick_air_temperature,
)


class TestEvaluateFrostWarning:
    def test_below_threshold_warns(self):
        assert evaluate_frost_warning(-2.0) is True

    def test_at_threshold_warns(self):
        assert evaluate_frost_warning(DEFAULT_FROST_WARNING_THRESHOLD_CELSIUS) is True

    def test_above_threshold_no_warning(self):
        assert evaluate_frost_warning(5.0) is False

    def test_none_temperature_is_unknown_not_false(self):
        # Honest unknown — never fabricate "no frost" from a missing reading.
        assert evaluate_frost_warning(None) is None

    def test_custom_threshold(self):
        assert evaluate_frost_warning(1.0, threshold_celsius=0.0) is False
        assert evaluate_frost_warning(0.0, threshold_celsius=0.0) is True

    def test_default_threshold_is_three_celsius(self):
        assert DEFAULT_FROST_WARNING_THRESHOLD_CELSIUS == 3.0


class TestPickAirTemperature:
    def test_prefers_canonical_temperature_celsius(self):
        values = {
            "temperature_celsius": {"value": 2.5, "entity_id": "sensor.air"},
            "water_temp_celsius": {"value": 18.0, "entity_id": "sensor.water"},
        }
        temp, entity_id = pick_air_temperature(values)
        assert temp == 2.5
        assert entity_id == "sensor.air"

    def test_falls_back_to_water_temp_celsius(self):
        values = {"water_temp_celsius": {"value": 1.0, "entity_id": "sensor.temp"}}
        temp, entity_id = pick_air_temperature(values)
        assert temp == 1.0
        assert entity_id == "sensor.temp"

    def test_no_temperature_metric_returns_none(self):
        values = {"humidity_percent": {"value": 55.0, "entity_id": "sensor.hum"}}
        temp, entity_id = pick_air_temperature(values)
        assert temp is None
        assert entity_id is None

    def test_none_value_skipped(self):
        values = {"temperature_celsius": {"value": None, "entity_id": "sensor.air"}}
        temp, entity_id = pick_air_temperature(values)
        assert temp is None
        assert entity_id is None

    def test_non_numeric_value_skipped_not_raised(self):
        # Home Assistant reports "unavailable"/"unknown" as the entity value; that
        # must not raise ValueError (→ 500 on the frost-warning endpoint).
        for bad in ("unavailable", "unknown", ""):
            values = {"temperature_celsius": {"value": bad, "entity_id": "sensor.air"}}
            temp, entity_id = pick_air_temperature(values)
            assert temp is None
            assert entity_id is None

    def test_non_numeric_primary_falls_back_to_numeric_secondary(self):
        # A non-numeric canonical metric is skipped; the numeric fallback wins.
        values = {
            "temperature_celsius": {"value": "unavailable", "entity_id": "sensor.air"},
            "water_temp_celsius": {"value": 1.5, "entity_id": "sensor.water"},
        }
        temp, entity_id = pick_air_temperature(values)
        assert temp == 1.5
        assert entity_id == "sensor.water"

    def test_numeric_string_is_parsed(self):
        # A numeric HA state delivered as a string still parses.
        values = {"temperature_celsius": {"value": "2.5", "entity_id": "sensor.air"}}
        temp, entity_id = pick_air_temperature(values)
        assert temp == 2.5
        assert entity_id == "sensor.air"

    def test_empty_values(self):
        temp, entity_id = pick_air_temperature({})
        assert temp is None
        assert entity_id is None

    def test_metric_priority_order(self):
        assert AIR_TEMPERATURE_METRIC_TYPES[0] == "temperature_celsius"
