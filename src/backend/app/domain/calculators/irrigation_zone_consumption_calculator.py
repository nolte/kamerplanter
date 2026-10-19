"""A zone's consumption from an actuator's runtime and a flow rate (REQ-053 GP-FR-114, O-13; WP 7.4). Pure.

**Which flow rate.** ``manual`` always uses ``flow_rate_l_per_min``. ``ha_entity`` uses the Home Assistant reading
when it is at most 24 hours old and positive; a stale or missing reading falls back to the manual rate (O-13: "a value
<= 24 h old overrides the manual one"). The provenance travels with the litres.

**Runtime.** The time between a successful switch to ``on`` and the next switch to ``off``, clipped to the window.
The state before the window is the last event before it; an actuator still ``on`` at the end of the window counts up
to its end. An unknown state before the first event counts as ``off``. Failed commands change nothing (the caller
passes successful events only).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

from app.common.enums import FlowRateSource
from app.domain.interfaces.flow_rate_sensor import FlowReading

#: How old a Home Assistant reading may be and still override the manual rate (O-13).
HA_READING_MAX_AGE = timedelta(hours=24)
_SECOND = timedelta(seconds=1)

type FlowRateOrigin = Literal["manual", "ha"]
type ConsumptionSource = Literal["manual_log", "actuator_runtime_manual_rate", "actuator_runtime_ha_rate"]


@dataclass(frozen=True)
class StateChange:
    """A successful switch of the actuator: the instant and the state it switched to (``on`` / ``off``)."""

    at: datetime
    new_state: str


@dataclass(frozen=True)
class FlowRate:
    liters_per_minute: float
    origin: FlowRateOrigin


def resolve_flow_rate(
    source: FlowRateSource, manual: float | None, reading: FlowReading | None, now: datetime
) -> FlowRate | None:
    """The rate in force: a fresh Home Assistant reading overrides the manual value; ``None`` = unknown."""
    if (
        source is FlowRateSource.HA_ENTITY
        and reading is not None
        and reading.liters_per_minute > 0
        and timedelta(0) <= now - reading.reported_at <= HA_READING_MAX_AGE
    ):
        return FlowRate(reading.liters_per_minute, "ha")
    if manual is not None and manual > 0:
        return FlowRate(manual, "manual")
    return None


def runtime_seconds(
    changes: Sequence[StateChange], *, start: datetime, end: datetime, initial_state: str = "off"
) -> float:
    """Seconds the actuator was ``on`` between ``start`` and ``end``.

    ``changes`` may include events before ``start`` (they set the state at ``start``); order does not matter.
    """
    state = initial_state
    on_since: datetime | None = start if state == "on" else None
    total = 0.0
    for change in sorted(changes, key=lambda item: item.at):
        if change.at >= end:
            break
        moment = max(change.at, start)
        if change.new_state == "on" and on_since is None:
            on_since = moment
        elif change.new_state != "on" and on_since is not None:
            total += (moment - on_since) / _SECOND
            on_since = None
    if on_since is not None:
        total += (end - on_since) / _SECOND
    return total


def runtime_liters(seconds: float, rate: FlowRate) -> float:
    return round(seconds / 60.0 * rate.liters_per_minute, 2)


def source_of(rate: FlowRate) -> ConsumptionSource:
    return "actuator_runtime_ha_rate" if rate.origin == "ha" else "actuator_runtime_manual_rate"
