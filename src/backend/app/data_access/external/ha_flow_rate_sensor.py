"""Home Assistant as the source of a zone's flow rate (REQ-053 GP-FR-114, SR-014; WP 7.4).

Every call goes through :class:`~app.data_access.external.ha_client.HomeAssistantClient`, which validates the base
URL and connects through the pinned transport (SSRF guard, #2249). This adapter adds three things: the unit
conversion to litres per minute, the choice of the freshest instant HA reports, and the rule that **nothing of the
entity leaves it** - an error carries neither the entity id nor the URL, and nothing is logged with them (GP-NFR-060).
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import httpx
import structlog

from app.domain.interfaces.flow_rate_sensor import FlowReading, FlowSensorUnavailableError

logger = structlog.get_logger(__name__)

#: Litres per minute per one unit of the entity's ``unit_of_measurement``. An unknown unit is not guessed.
_TO_LITERS_PER_MINUTE: dict[str, float] = {
    "L/min": 1.0,
    "l/min": 1.0,
    "L/h": 1.0 / 60.0,
    "l/h": 1.0 / 60.0,
    "L/s": 60.0,
    "l/s": 60.0,
    "m³/h": 1000.0 / 60.0,
    "m3/h": 1000.0 / 60.0,
    "m³/min": 1000.0,
    "m3/min": 1000.0,
    "mL/min": 0.001,
    "ml/min": 0.001,
    "gal/min": 3.785411784,
}


def _instant(state: dict[str, Any]) -> datetime | None:
    """The freshest honest instant: ``last_reported`` moves on every report, ``last_updated`` only on a change."""
    for name in ("last_reported", "last_updated", "last_changed"):
        raw = state.get(name)
        if not raw:
            continue
        try:
            parsed = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        except ValueError:
            continue
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)
    return None


class HaFlowRateSensor:
    def __init__(self, client_factory: Callable[[], Any]) -> None:
        self._client_factory = client_factory

    def _client(self) -> Any:
        try:
            client = self._client_factory()
        except Exception:  # noqa: BLE001 - a misconfigured URL is "cannot be asked", never an echo of it
            logger.warning("irrigation_zone.flow_sensor_unconfigured")
            raise FlowSensorUnavailableError from None
        if client is None:
            raise FlowSensorUnavailableError
        return client

    def device_class(self, entity_id: str) -> str | None:
        client = self._client()
        try:
            attributes = client.get_state_attributes(entity_id)
        except httpx.HTTPError, ValueError:
            logger.warning("irrigation_zone.flow_sensor_unreachable")
            raise FlowSensorUnavailableError from None
        value = (attributes or {}).get("device_class")
        return str(value) if value else None

    def read(self, entity_id: str) -> FlowReading | None:
        client = self._client()
        try:
            state = client.get_state(entity_id)
        except httpx.HTTPError, ValueError:
            logger.warning("irrigation_zone.flow_sensor_unreachable")
            raise FlowSensorUnavailableError from None
        if not state or state.get("value") is None:
            return None
        factor = _TO_LITERS_PER_MINUTE.get(str(state.get("unit") or ""))
        reported_at = _instant(state)
        if factor is None or reported_at is None:
            return None
        liters = float(state["value"]) * factor
        return FlowReading(liters_per_minute=liters, reported_at=reported_at) if liters > 0 else None
