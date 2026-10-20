"""REQ-053 WP 7.4 (#2470) - the Home Assistant flow-rate adapter: units, instants, and nothing of the entity leaks."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx
import pytest
import structlog

from app.data_access.external.ha_flow_rate_sensor import HaFlowRateSensor
from app.domain.interfaces.flow_rate_sensor import FlowSensorUnavailableError

ENTITY = "sensor.south_flow"
REPORTED = "2026-10-19T10:00:00+00:00"


class _Client:
    def __init__(self, state: dict[str, Any] | None = None, attributes: dict[str, Any] | None = None) -> None:
        self.state = state
        self.attributes = attributes
        self.error: Exception | None = None

    def get_state(self, entity_id: str) -> dict[str, Any] | None:
        if self.error:
            raise self.error
        return self.state

    def get_state_attributes(self, entity_id: str) -> dict[str, Any] | None:
        if self.error:
            raise self.error
        return self.attributes


def _sensor(client: _Client | None) -> HaFlowRateSensor:
    return HaFlowRateSensor(lambda: client)


def _state(value: float | None, unit: str | None, **moments: str) -> dict[str, Any]:
    return {"value": value, "unit": unit, "last_changed": None, "last_updated": None, "last_reported": None} | moments


class TestRead:
    @pytest.mark.parametrize(
        ("unit", "value", "liters"),
        [
            ("L/min", 6.0, 6.0),
            ("L/h", 120.0, 2.0),
            ("m³/h", 0.6, 10.0),
            ("gal/min", 1.0, 3.785411784),
            ("mL/min", 5000, 5),
        ],
    )
    def test_the_value_is_converted_to_litres_per_minute(self, unit, value, liters) -> None:
        reading = _sensor(_Client(_state(value, unit, last_reported=REPORTED))).read(ENTITY)

        assert reading is not None and reading.liters_per_minute == pytest.approx(liters)
        assert reading.reported_at == datetime(2026, 10, 19, 10, 0, tzinfo=UTC)

    def test_the_freshest_honest_instant_wins_and_a_naive_one_is_read_as_utc(self) -> None:
        state = _state(1.0, "L/min", last_changed="2026-10-18T08:00:00Z", last_updated="2026-10-19T09:00:00")
        reading = _sensor(_Client(state)).read(ENTITY)

        assert reading is not None and reading.reported_at == datetime(2026, 10, 19, 9, 0, tzinfo=UTC)

    @pytest.mark.parametrize(
        "state",
        [
            None,
            _state(None, "L/min", last_reported=REPORTED),  # unavailable / unknown
            _state(3.0, "furlongs/fortnight", last_reported=REPORTED),  # an unknown unit is not guessed
            _state(3.0, None, last_reported=REPORTED),
            _state(3.0, "L/min"),  # no instant at all
            _state(0.0, "L/min", last_reported=REPORTED),  # nothing flows
        ],
    )
    def test_an_unreadable_state_is_no_reading(self, state) -> None:
        assert _sensor(_Client(state)).read(ENTITY) is None


class TestDeviceClass:
    def test_it_returns_the_device_class_or_none(self) -> None:
        assert _sensor(_Client(attributes={"device_class": "volume_flow_rate"})).device_class(ENTITY) == (
            "volume_flow_rate"
        )
        assert _sensor(_Client(attributes={})).device_class(ENTITY) is None
        assert _sensor(_Client(attributes=None)).device_class(ENTITY) is None


class TestUnavailable:
    def test_no_client_or_a_broken_factory_means_it_cannot_be_asked(self) -> None:
        def broken():
            raise ValueError("http://169.254.169.254/ is not allowed")

        with pytest.raises(FlowSensorUnavailableError):
            _sensor(None).read(ENTITY)
        with pytest.raises(FlowSensorUnavailableError):
            HaFlowRateSensor(broken).device_class(ENTITY)

    @pytest.mark.parametrize(
        "error", [httpx.ConnectError("boom http://ha.local"), httpx.ReadTimeout("t"), ValueError("x")]
    )
    def test_a_transport_failure_carries_neither_entity_nor_url_and_logs_neither(self, error) -> None:
        client = _Client()
        client.error = error

        with structlog.testing.capture_logs() as logs, pytest.raises(FlowSensorUnavailableError) as raised:
            _sensor(client).read(ENTITY)

        assert raised.value.args == () and raised.value.__cause__ is None
        assert ENTITY not in repr(logs) and "ha.local" not in repr(logs)


class TestNonFiniteValues:
    """#2522: ``"inf"`` and ``"nan"`` parse as floats; a non-finite rate must never become a reading."""

    @pytest.mark.parametrize("value", ["inf", "-inf", "nan", float("inf"), float("nan")])
    def test_a_non_finite_value_is_no_reading(self, value) -> None:
        assert _sensor(_Client(_state(value, "L/min", last_reported=REPORTED))).read(ENTITY) is None  # type: ignore[arg-type]

    def test_an_unparsable_value_is_no_reading(self) -> None:
        assert _sensor(_Client(_state("unavailable", "L/min", last_reported=REPORTED))).read(ENTITY) is None  # type: ignore[arg-type]
