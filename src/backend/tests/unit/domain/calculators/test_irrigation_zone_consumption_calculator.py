"""REQ-053 WP 7.4 (#2470) - flow rate choice (O-13) and actuator runtime, as pure functions."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.common.enums import FlowRateSource
from app.domain.calculators.irrigation_zone_consumption_calculator import (
    FlowRate,
    StateChange,
    resolve_flow_rate,
    runtime_liters,
    runtime_seconds,
    source_of,
)
from app.domain.interfaces.flow_rate_sensor import FlowReading

NOW = datetime(2026, 10, 19, 12, 0, tzinfo=UTC)
START = NOW - timedelta(days=30)


def _reading(age: timedelta, liters: float = 9.0) -> FlowReading:
    return FlowReading(liters_per_minute=liters, reported_at=NOW - age)


class TestResolveFlowRate:
    def test_manual_source_uses_the_manual_rate_even_with_a_fresh_reading(self) -> None:
        rate = resolve_flow_rate(FlowRateSource.MANUAL, 6.0, _reading(timedelta(minutes=1)), NOW)

        assert rate == FlowRate(6.0, "manual")

    def test_a_reading_up_to_24_hours_old_overrides_the_manual_rate(self) -> None:
        assert resolve_flow_rate(FlowRateSource.HA_ENTITY, 6.0, _reading(timedelta(hours=24)), NOW) == FlowRate(
            9.0, "ha"
        )

    @pytest.mark.parametrize("age", [timedelta(hours=24, seconds=1), timedelta(days=9)])
    def test_a_stale_reading_falls_back_to_the_manual_rate(self, age: timedelta) -> None:
        assert resolve_flow_rate(FlowRateSource.HA_ENTITY, 6.0, _reading(age), NOW) == FlowRate(6.0, "manual")

    def test_a_reading_from_the_future_is_not_trusted(self) -> None:
        assert resolve_flow_rate(FlowRateSource.HA_ENTITY, 6.0, _reading(timedelta(minutes=-5)), NOW) == FlowRate(
            6.0, "manual"
        )

    @pytest.mark.parametrize(
        ("source", "manual", "reading"),
        [
            (FlowRateSource.MANUAL, None, None),
            (FlowRateSource.HA_ENTITY, None, None),
            (FlowRateSource.HA_ENTITY, None, _reading(timedelta(days=2))),
            (FlowRateSource.HA_ENTITY, 0.0, _reading(timedelta(days=2))),
            (FlowRateSource.HA_ENTITY, None, _reading(timedelta(hours=1), liters=0.0)),
        ],
    )
    def test_without_any_usable_value_the_rate_is_unknown(self, source, manual, reading) -> None:
        assert resolve_flow_rate(source, manual, reading, NOW) is None

    def test_the_provenance_names_the_source_of_the_rate(self) -> None:
        assert source_of(FlowRate(1.0, "manual")) == "actuator_runtime_manual_rate"
        assert source_of(FlowRate(1.0, "ha")) == "actuator_runtime_ha_rate"


def _on(minutes: float) -> StateChange:
    return StateChange(START + timedelta(minutes=minutes), "on")


def _off(minutes: float) -> StateChange:
    return StateChange(START + timedelta(minutes=minutes), "off")


class TestRuntimeSeconds:
    def test_it_adds_up_the_on_intervals(self) -> None:
        assert runtime_seconds([_on(0), _off(20), _on(100), _off(110)], start=START, end=NOW) == 30 * 60

    def test_an_actuator_still_on_counts_up_to_the_end_of_the_window(self) -> None:
        assert runtime_seconds([_on(60 * 24 * 30 - 15)], start=START, end=NOW) == 15 * 60

    def test_the_state_before_the_window_counts_inside_it(self) -> None:
        before = StateChange(START - timedelta(hours=3), "on")

        assert runtime_seconds([before, _off(10)], start=START, end=NOW) == 10 * 60

    def test_an_off_without_an_on_is_nothing_and_events_arrive_in_any_order(self) -> None:
        assert runtime_seconds([_off(5)], start=START, end=NOW) == 0
        assert runtime_seconds([_off(20), _on(0)], start=START, end=NOW) == 20 * 60

    def test_a_repeated_on_does_not_restart_the_interval(self) -> None:
        assert runtime_seconds([_on(0), _on(10), _off(30)], start=START, end=NOW) == 30 * 60

    def test_events_at_or_after_the_end_are_ignored(self) -> None:
        assert runtime_seconds([_on(0), StateChange(NOW, "off")], start=START, end=NOW) == (NOW - START).total_seconds()

    def test_nothing_recorded_is_zero(self) -> None:
        assert runtime_seconds([], start=START, end=NOW) == 0


def test_liters_are_minutes_times_the_rate() -> None:
    assert runtime_liters(30 * 60, FlowRate(6.0, "manual")) == 180.0
