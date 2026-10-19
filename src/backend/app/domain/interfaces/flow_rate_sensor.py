"""The question a zone asks Home Assistant about its flow-rate entity (REQ-053 GP-FR-114, SR-014; WP 7.4).

A port, so the zone service reads a flow rate without importing the Home Assistant adapter. The raw state of the
entity never leaves the adapter: the caller gets a flow in litres per minute and the instant it was reported - not
the state string, not the attributes, not the entity id back.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


class FlowSensorUnavailableError(Exception):
    """Home Assistant cannot be asked (not configured, unreachable, refused). Carries no entity id and no URL."""


@dataclass(frozen=True)
class FlowReading:
    """One reading, converted to litres per minute, and when the entity last reported it."""

    liters_per_minute: float
    reported_at: datetime


class IFlowRateSensor(Protocol):
    def device_class(self, entity_id: str) -> str | None:
        """``device_class`` of the entity, ``None`` when it has none or does not exist.

        Raises:
            FlowSensorUnavailableError: Home Assistant cannot be asked - the caller must not bind the entity.
        """
        ...

    def read(self, entity_id: str) -> FlowReading | None:
        """The current flow in L/min, or ``None`` when the state is not a number, has no known unit or no instant.

        Raises:
            FlowSensorUnavailableError: Home Assistant cannot be asked.
        """
        ...


class NoFlowRateSensor:
    """The sensor of a component assembled without Home Assistant: it cannot be asked, so nothing is bound."""

    def device_class(self, entity_id: str) -> str | None:  # noqa: ARG002
        raise FlowSensorUnavailableError

    def read(self, entity_id: str) -> FlowReading | None:  # noqa: ARG002
        raise FlowSensorUnavailableError
