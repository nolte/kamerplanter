"""The Kamerplanter integration."""

from __future__ import annotations

import logging

from aiohttp import ClientSession
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import KamerplanterApi
from .const import (
    CONF_API_KEY,
    CONF_TENANT_SLUG,
    DOMAIN,
    PLATFORMS,
    SERVICE_CLEAR_CACHE,
    SERVICE_CONFIRM_CARE,
    SERVICE_FILL_TANK,
    SERVICE_REFRESH,
    SERVICE_WATER_CHANNEL,
)
from .coordinator import (
    KamerplanterAlertCoordinator,
    KamerplanterLocationCoordinator,
    KamerplanterPlantCoordinator,
    KamerplanterRunCoordinator,
    KamerplanterTaskCoordinator,
)

_LOGGER = logging.getLogger(__name__)

type KamerplanterConfigEntry = ConfigEntry


async def async_setup_entry(hass: HomeAssistant, entry: KamerplanterConfigEntry) -> bool:
    """Set up Kamerplanter from a config entry."""
    session: ClientSession = async_get_clientsession(hass)

    api = KamerplanterApi(
        base_url=entry.data[CONF_URL],
        session=session,
        api_key=entry.data.get(CONF_API_KEY),
        tenant_slug=entry.data.get(CONF_TENANT_SLUG),
    )

    coordinators = {
        "plants": KamerplanterPlantCoordinator(hass, entry, api),
        "locations": KamerplanterLocationCoordinator(hass, entry, api),
        "runs": KamerplanterRunCoordinator(hass, entry, api),
        "alerts": KamerplanterAlertCoordinator(hass, entry, api),
        "tasks": KamerplanterTaskCoordinator(hass, entry, api),
    }

    # First refresh all coordinators
    for coordinator in coordinators.values():
        await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "api": api,
        "coordinators": coordinators,
    }

    # Register services (HA-NFR-002: idempotency guard)
    if not hass.services.has_service(DOMAIN, SERVICE_REFRESH):
        await _async_register_services(hass)

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener for options changes (HA-NFR-006)
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: KamerplanterConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        # Unregister services if no entries remain
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)
            hass.services.async_remove(DOMAIN, SERVICE_REFRESH)
            hass.services.async_remove(DOMAIN, SERVICE_CLEAR_CACHE)
            hass.services.async_remove(DOMAIN, SERVICE_FILL_TANK)
            hass.services.async_remove(DOMAIN, SERVICE_WATER_CHANNEL)
            hass.services.async_remove(DOMAIN, SERVICE_CONFIRM_CARE)
    return unload_ok


async def _async_reload_entry(hass: HomeAssistant, entry: KamerplanterConfigEntry) -> None:
    """Reload entry on options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def _async_register_services(hass: HomeAssistant) -> None:
    """Register Kamerplanter services."""

    async def handle_refresh(call: ServiceCall) -> None:
        target_id = call.data.get("entry_id", "")
        entries = [
            e
            for e in hass.config_entries.async_entries(DOMAIN)
            if not target_id or e.entry_id == target_id
        ]
        for entry in entries:
            data = hass.data[DOMAIN].get(entry.entry_id)
            if data:
                for coordinator in data["coordinators"].values():
                    await coordinator.async_request_refresh()

    async def handle_clear_cache(call: ServiceCall) -> None:
        target_id = call.data.get("entry_id", "")
        entries = [
            e
            for e in hass.config_entries.async_entries(DOMAIN)
            if not target_id or e.entry_id == target_id
        ]
        for entry in entries:
            data = hass.data[DOMAIN].get(entry.entry_id)
            if data:
                for coordinator in data["coordinators"].values():
                    coordinator.data = None
                    await coordinator.async_request_refresh()

    # Known suffixes for tank entities (used to extract tank_key from entity_id)
    _TANK_ENTITY_SUFFIXES = (
        "_info", "_volume", "_fill_level", "_ec", "_ph",
        "_water_temp", "_solution_age_days", "_alert_active",
    )

    def _resolve_tank_key(call_data: dict) -> str | None:
        """Resolve tank_key from entity_id or direct tank_key.

        Accepts either:
        - entity_id: a HA entity ID (e.g. sensor.kp_abc123_info) → extracts tank_key
        - tank_key: direct ArangoDB key (legacy, backwards-compatible)

        Strategy order:
        1. Read tank_key from entity state attributes (if entity is loaded)
        2. Parse tank_key from the entity_id string pattern: sensor.kp_{key}_{suffix}
        3. Fall back to direct tank_key parameter
        """
        if "entity_id" in call_data:
            entity_id = str(call_data["entity_id"])

            # Strategy 1: Read tank_key from state attributes
            state = hass.states.get(entity_id)
            if state and state.attributes.get("tank_key"):
                _LOGGER.debug("Resolved tank_key from state attributes")
                return str(state.attributes["tank_key"])

            # Strategy 2: Parse from entity_id pattern
            # Entity IDs follow: sensor.kp_{slug}_{suffix} or binary_sensor.kp_{slug}_{suffix}
            # where slug == tank_key.replace("-", "_").lower()
            entity_name = entity_id.split(".", 1)[-1]  # remove "sensor." prefix
            if entity_name.startswith("kp_"):
                rest = entity_name[3:]  # remove "kp_"
                # Also handle legacy "kp_tank_{slug}" pattern
                if rest.startswith("tank_"):
                    rest = rest[5:]
                for suffix in _TANK_ENTITY_SUFFIXES:
                    if rest.endswith(suffix):
                        tank_key = rest[: -len(suffix)]
                        _LOGGER.debug(
                            "Resolved tank_key '%s' from entity_id pattern", tank_key
                        )
                        return tank_key

            _LOGGER.error("Could not resolve tank_key from entity_id %s", entity_id)
            return None

        if "tank_key" in call_data:
            return str(call_data["tank_key"])

        return None

    async def handle_fill_tank(call: ServiceCall) -> None:
        """Handle the fill_tank service call.

        Accepts entity_id (any tank entity) or tank_key (direct ArangoDB key).
        Resolves current dosages from the location coordinator and sends
        a fill event to the Kamerplanter backend.
        """
        _LOGGER.debug("fill_tank call.data keys: %s, values: %s", list(call.data.keys()), dict(call.data))
        tank_key = _resolve_tank_key(dict(call.data))
        if not tank_key:
            _LOGGER.error(
                "No tank_key or entity_id provided. Received data: %s",
                dict(call.data),
            )
            return
        fill_type = call.data.get("fill_type", "full_change")

        # Find the API instance from the first config entry
        entry = hass.config_entries.async_entries(DOMAIN)[0]
        data = hass.data[DOMAIN].get(entry.entry_id)
        if not data:
            _LOGGER.error("No Kamerplanter instance found")
            return

        api: KamerplanterApi = data["api"]

        # Fetch tank details for default volume
        tanks = await api.async_get_tanks()
        tank = next((t for t in tanks if t.get("key") == tank_key), None)
        if not tank:
            _LOGGER.error("Tank %s not found", tank_key)
            return

        volume = call.data.get("volume_liters") or tank.get("volume_liters", 0)

        # Resolve current dosages from the location coordinator
        fertilizers_used: list[dict[str, object]] = []
        loc_coord = data["coordinators"].get("locations")
        if loc_coord and loc_coord.data:
            tank_location_key = tank.get("location_key")
            for loc in loc_coord.data:
                loc_key = loc.get("key") or loc.get("_key", "")
                if loc_key != tank_location_key:
                    continue
                run = loc.get("_primary_run")
                if not run:
                    break
                current_entries = run.get(
                    "_current_phase_entries", run.get("_phase_entries", [])
                )
                for pe in current_entries:
                    for channel in pe.get("delivery_channels", []):
                        # Match channel to tank by label containing tank name or volume
                        ch_label = channel.get("label", "")
                        tank_name = tank.get("name", "")
                        tank_vol = str(int(tank.get("volume_liters", 0)))
                        if (
                            tank_name.lower() in ch_label.lower()
                            or f"{tank_vol}l" in ch_label.lower().replace(" ", "")
                            or f"{tank_vol} l" in ch_label.lower()
                        ):
                            for dosage in channel.get("fertilizer_dosages", []):
                                ml = dosage.get("ml_per_liter")
                                if ml is not None and ml > 0:
                                    fertilizers_used.append({
                                        "product_key": dosage.get("fertilizer_key"),
                                        "product_name": dosage.get(
                                            "product_name",
                                            dosage.get("fertilizer_key", "unknown"),
                                        ),
                                        "ml_per_liter": ml,
                                    })
                break

        # Build fill event payload
        payload: dict[str, object] = {
            "fill_type": fill_type,
            "volume_liters": volume,
            "fertilizers_used": fertilizers_used,
            "performed_by": "home_assistant",
        }
        if call.data.get("measured_ec_ms") is not None:
            payload["measured_ec_ms"] = call.data["measured_ec_ms"]
        if call.data.get("measured_ph") is not None:
            payload["measured_ph"] = call.data["measured_ph"]
        if call.data.get("notes"):
            payload["notes"] = call.data["notes"]

        _LOGGER.info(
            "Filling tank %s (%s): %.1fL, %d fertilizers",
            tank_key, fill_type, volume, len(fertilizers_used),
        )

        try:
            result = await api.async_fill_tank(tank_key, payload)
            _LOGGER.info("Tank fill recorded: %s", result.get("fill_event", {}).get("key"))

            # Refresh coordinators to reflect new state
            for coordinator in data["coordinators"].values():
                await coordinator.async_request_refresh()
        except Exception:
            _LOGGER.exception("Failed to fill tank %s", tank_key)

    # Known suffixes for plant channel entities (used to extract plant_key + channel_id)
    _CHANNEL_SUFFIX = "_mix"

    def _resolve_plant_channel(call_data: dict) -> tuple[str | None, str | None]:
        """Resolve plant_key and channel_id from entity_id or direct parameters.

        Strategy order:
        1. Read plant_key/channel_id from entity state attributes
        2. Parse from entity_id pattern: sensor.kp_{plant_key}_{channel_slug}_mix
        3. Fall back to direct plant_key + channel_id parameters
        """
        if "entity_id" in call_data:
            entity_id = str(call_data["entity_id"])

            # Strategy 1: Read from state attributes
            state = hass.states.get(entity_id)
            if state:
                attrs = state.attributes or {}
                if attrs.get("plant_key") and attrs.get("channel_id"):
                    _LOGGER.debug("Resolved plant/channel from state attributes")
                    return str(attrs["plant_key"]), str(attrs["channel_id"])

            # Strategy 2: Parse from entity_id pattern
            # Channel entities: sensor.kp_{plant_slug}_{channel_slug}_mix
            entity_name = entity_id.split(".", 1)[-1]  # remove "sensor." prefix
            if entity_name.startswith("kp_") and entity_name.endswith(_CHANNEL_SUFFIX):
                rest = entity_name[3:-len(_CHANNEL_SUFFIX)]  # remove "kp_" and "_mix"
                # The plant coordinator has the plant_key — search for a match
                for entry_data in hass.data.get(DOMAIN, {}).values():
                    plant_coord = entry_data.get("coordinators", {}).get("plants")
                    if plant_coord and plant_coord.data:
                        for plant in plant_coord.data:
                            pk = plant.get("key", "")
                            slug = pk.replace("-", "_").lower()
                            if rest.startswith(slug + "_"):
                                channel_slug = rest[len(slug) + 1:]
                                # Find matching channel_id from dosages
                                dosage_data = plant.get("_current_dosages")
                                if dosage_data and isinstance(dosage_data, dict):
                                    for ch in dosage_data.get("channels", []):
                                        ch_id = ch.get("channel_id", "")
                                        if _slugify_label(ch_id) == channel_slug:
                                            _LOGGER.debug(
                                                "Resolved plant_key='%s', channel_id='%s' from entity_id",
                                                pk, ch_id,
                                            )
                                            return pk, ch_id

                _LOGGER.error("Could not resolve plant/channel from entity_id %s", entity_id)
                return None, None

        plant_key = call_data.get("plant_key")
        channel_id = call_data.get("channel_id")
        if plant_key:
            return str(plant_key), str(channel_id) if channel_id else None
        return None, None

    def _slugify_label(text: str) -> str:
        """Slugify a label for entity ID matching (simplified)."""
        import re
        import unicodedata
        text = unicodedata.normalize("NFKD", text)
        text = text.encode("ascii", "ignore").decode("ascii")
        text = re.sub(r"[^a-z0-9]+", "_", text.lower())
        return text.strip("_")

    async def handle_water_channel(call: ServiceCall) -> None:
        """Handle the water_channel service call.

        Resolves plant_key + channel_id, looks up current dosages,
        and creates a watering log in the Kamerplanter backend.
        """
        _LOGGER.debug(
            "water_channel call.data keys: %s, values: %s",
            list(call.data.keys()), dict(call.data),
        )
        plant_key, channel_id = _resolve_plant_channel(dict(call.data))
        if not plant_key:
            _LOGGER.error(
                "No plant_key or entity_id provided. Received data: %s",
                dict(call.data),
            )
            return

        # Find API + coordinator from first config entry
        entry = hass.config_entries.async_entries(DOMAIN)[0]
        data = hass.data[DOMAIN].get(entry.entry_id)
        if not data:
            _LOGGER.error("No Kamerplanter instance found")
            return

        api: KamerplanterApi = data["api"]

        # Resolve dosages and volume from plant coordinator
        fertilizers_used: list[dict[str, object]] = []
        volume_liters: float | None = call.data.get("volume_liters")
        plant_coord = data["coordinators"].get("plants")

        if plant_coord and plant_coord.data:
            plant = next(
                (p for p in plant_coord.data if p.get("key") == plant_key), None
            )
            if plant:
                dosage_data = plant.get("_current_dosages")
                if dosage_data and isinstance(dosage_data, dict):
                    for ch in dosage_data.get("channels", []):
                        ch_id = ch.get("channel_id", "")
                        if channel_id and ch_id != channel_id:
                            continue
                        # If no channel_id specified, use first channel
                        if not channel_id:
                            channel_id = ch_id
                        # Extract volume from channel if not provided
                        if volume_liters is None:
                            volume_liters = ch.get("volume_liters")
                        for dosage in ch.get("dosages", []):
                            ml = dosage.get("ml_per_liter")
                            fert_key = dosage.get("fertilizer_key")
                            if ml is not None and ml > 0 and fert_key:
                                fertilizers_used.append({
                                    "fertilizer_key": fert_key,
                                    "ml_per_liter": ml,
                                })
                        break

        if volume_liters is None or volume_liters <= 0:
            _LOGGER.error(
                "No volume resolved for plant %s channel %s. "
                "Provide volume_liters or ensure the nutrient plan defines a channel volume.",
                plant_key, channel_id,
            )
            return

        # Build watering log payload
        payload: dict[str, object] = {
            "application_method": call.data.get("application_method", "drench"),
            "volume_liters": volume_liters,
            "plant_keys": [plant_key],
            "channel_id": channel_id,
            "fertilizers_used": fertilizers_used,
            "performed_by": "home_assistant",
        }
        if call.data.get("measured_ec_ms") is not None:
            payload["ec_before"] = call.data["measured_ec_ms"]
        if call.data.get("measured_ph") is not None:
            payload["ph_before"] = call.data["measured_ph"]
        if call.data.get("notes"):
            payload["notes"] = call.data["notes"]

        _LOGGER.info(
            "Watering plant %s channel '%s': %.2fL, %d fertilizers",
            plant_key, channel_id, volume_liters, len(fertilizers_used),
        )

        try:
            result = await api.async_create_watering_log(payload)
            log_data = result.get("log", result)
            _LOGGER.info(
                "Watering log created: %s", log_data.get("key", "unknown")
            )

            # Refresh coordinators to reflect new state
            for coordinator in data["coordinators"].values():
                await coordinator.async_request_refresh()
        except Exception:
            _LOGGER.exception("Failed to create watering log for plant %s", plant_key)

    async def handle_confirm_care(call: ServiceCall) -> None:
        """Handle the confirm_care service call (REQ-030).

        Confirms a care reminder notification as completed or skipped.
        Called by HA Companion App actionable notification buttons.
        """
        notification_key = call.data.get("notification_key")
        if not notification_key:
            _LOGGER.error(
                "No notification_key provided. Received data: %s",
                dict(call.data),
            )
            return

        action = call.data.get("action", "confirmed")

        # Find API instance from first config entry
        entry = hass.config_entries.async_entries(DOMAIN)[0]
        data = hass.data[DOMAIN].get(entry.entry_id)
        if not data:
            _LOGGER.error("No Kamerplanter instance found")
            return

        api: KamerplanterApi = data["api"]

        _LOGGER.info(
            "Confirming care reminder %s with action '%s'",
            notification_key, action,
        )

        try:
            result = await api.async_confirm_care_reminder(
                notification_key=notification_key,
                action=action,
            )
            _LOGGER.info(
                "Care reminder %s confirmed: %s",
                notification_key, result,
            )

            # Refresh task coordinators to reflect updated state
            for coordinator in data["coordinators"].values():
                await coordinator.async_request_refresh()
        except Exception:
            _LOGGER.exception(
                "Failed to confirm care reminder %s", notification_key
            )

    hass.services.async_register(DOMAIN, SERVICE_REFRESH, handle_refresh)
    hass.services.async_register(DOMAIN, SERVICE_CLEAR_CACHE, handle_clear_cache)
    hass.services.async_register(DOMAIN, SERVICE_FILL_TANK, handle_fill_tank)
    hass.services.async_register(DOMAIN, SERVICE_WATER_CHANNEL, handle_water_channel)
    hass.services.async_register(DOMAIN, SERVICE_CONFIRM_CARE, handle_confirm_care)
