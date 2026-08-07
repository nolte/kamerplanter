"""The one place ``Sensor.metric_type`` is classified (Issue #961).

These tests pin the *reconciliation* rather than just the happy path, because
this module replaced two heuristics that disagreed with each other:

* ``pick_air_temperature`` accepted ``water_temp_celsius``;
* ``QuarterClimateService._is_air_temperature`` rejected it but accepted
  ``substrate_temp_celsius``.

Both behaviours cannot survive, so the tests below state which one did and why —
a future reader who finds a probe suddenly ignored should land here, not in a
bisect.
"""

from __future__ import annotations

import pytest

from app.domain.engines.sensor_metrics import (
    AIR_TEMPERATURE_LIVE_PRIORITY,
    AIR_TEMPERATURE_METRIC_TYPES,
    HUMIDITY_METRIC_TYPES,
    TOLERATED_AIR_TEMPERATURE_ALIASES,
    is_air_temperature,
    is_humidity,
    normalize_metric_type,
)


class TestCanonicalAirTemperature:
    @pytest.mark.parametrize("metric_type", AIR_TEMPERATURE_METRIC_TYPES)
    def test_canonical_names_are_air_temperature(self, metric_type: str):
        assert is_air_temperature(metric_type) is True

    def test_case_and_whitespace_are_normalised(self):
        assert is_air_temperature("  Temperature_Celsius ") is True

    def test_unknown_temperature_name_is_accepted(self):
        # The vocabulary is open (REQ-005 §2). An imported ``room_temp_c`` must
        # keep working; an exhaustive allow-list would silently drop it.
        assert is_air_temperature("room_temp_c") is True

    def test_non_temperature_metric_is_not(self):
        assert is_air_temperature("humidity_percent") is False
        assert is_air_temperature("ec_ms") is False

    def test_blank_and_none_are_not(self):
        assert is_air_temperature(None) is False
        assert is_air_temperature("   ") is False


class TestNonAirTemperatureProbes:
    """The narrowing side of the reconciliation.

    Each of these was accepted by the old quarter-climate heuristic ("temp" and
    not "water"). They measure a different physical quantity at a differently
    placed probe, and a winter quarter that reads "too cold" off a substrate
    sensor is answering a question nobody asked.
    """

    @pytest.mark.parametrize(
        "metric_type",
        [
            "substrate_temp_celsius",
            "soil_temp_celsius",
            "root_temp_celsius",
            "leaf_temp_celsius",
            "canopy_temp_celsius",
            "nutrient_temp_celsius",
            "reservoir_temp_celsius",
        ],
    )
    def test_probe_temperatures_are_not_ambient_air(self, metric_type: str):
        assert is_air_temperature(metric_type) is False
        assert is_air_temperature(metric_type, accept_aliases=True) is False


class TestToleratedAlias:
    """``water_temp_celsius`` is an alias only where it was already tolerated."""

    def test_rejected_by_default(self):
        assert is_air_temperature("water_temp_celsius") is False

    def test_accepted_only_on_explicit_opt_in(self):
        assert is_air_temperature("water_temp_celsius", accept_aliases=True) is True

    def test_alias_is_not_in_the_canonical_tuple(self):
        # If it ever slid into the canonical names, every consumer would silently
        # start reading reservoir probes as room temperature.
        assert "water_temp_celsius" not in AIR_TEMPERATURE_METRIC_TYPES
        assert "water_temp_celsius" in TOLERATED_AIR_TEMPERATURE_ALIASES

    def test_live_priority_puts_canonical_names_first(self):
        # The frost path reads the *first* match out of a live-state map, so the
        # order is behaviour, not cosmetics.
        assert AIR_TEMPERATURE_LIVE_PRIORITY[0] == "temperature_celsius"
        assert AIR_TEMPERATURE_LIVE_PRIORITY[-1] == "water_temp_celsius"


class TestHumidity:
    @pytest.mark.parametrize("metric_type", HUMIDITY_METRIC_TYPES)
    def test_canonical_names_are_humidity(self, metric_type: str):
        assert is_humidity(metric_type) is True

    def test_unknown_humidity_name_is_accepted(self):
        assert is_humidity("air_humidity") is True

    @pytest.mark.parametrize("metric_type", ["substrate_humidity", "soil_humidity_percent"])
    def test_substrate_moisture_is_not_air_humidity(self, metric_type: str):
        assert is_humidity(metric_type) is False

    def test_temperature_is_not_humidity(self):
        assert is_humidity("temperature_celsius") is False

    def test_blank_and_none_are_not(self):
        assert is_humidity(None) is False
        assert is_humidity("") is False


class TestNormalize:
    def test_none_becomes_empty_string(self):
        assert normalize_metric_type(None) == ""

    def test_trims_and_lowercases(self):
        assert normalize_metric_type("  CO2_PPM ") == "co2_ppm"
