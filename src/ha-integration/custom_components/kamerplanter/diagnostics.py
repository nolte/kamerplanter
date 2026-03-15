"""Diagnostics for the Kamerplanter integration (HA-008)."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_API_KEY, CONF_TENANT_SLUG, DOMAIN


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinators = data["coordinators"]

    plant_data = coordinators["plants"].data or []
    location_data = coordinators["locations"].data or []
    alert_data = coordinators["alerts"].data or []
    task_data = coordinators["tasks"].data or []
    run_data = coordinators.get("runs")
    run_count = len(run_data.data or []) if run_data else 0

    api_key = config_entry.data.get(CONF_API_KEY, "")
    redacted_key = f"{api_key[:8]}..." if len(api_key) > 8 else "***"

    return {
        "tenant_slug": config_entry.data.get(CONF_TENANT_SLUG),
        "light_mode": config_entry.data.get("light_mode", False),
        "plant_count": len(plant_data),
        "location_count": len(location_data),
        "run_count": run_count,
        "active_alerts": len(alert_data),
        "pending_tasks": len(task_data),
        "coordinator_update_intervals": {
            "plants": coordinators["plants"].update_interval.total_seconds(),
            "locations": coordinators["locations"].update_interval.total_seconds(),
            "alerts": coordinators["alerts"].update_interval.total_seconds(),
            "tasks": coordinators["tasks"].update_interval.total_seconds(),
        },
        "api_key_prefix": redacted_key,
    }
