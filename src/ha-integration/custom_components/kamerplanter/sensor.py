"""Sensor entities for the Kamerplanter integration."""

from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime, timezone
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime, UnitOfVolume
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import (
    KamerplanterAlertCoordinator,
    KamerplanterLocationCoordinator,
    KamerplanterPlantCoordinator,
    KamerplanterTaskCoordinator,
)


def _slugify_key(key: str) -> str:
    """Convert ArangoDB key to entity-id-safe slug."""
    return key.replace("-", "_").lower()


def _slugify_label(label: str) -> str:
    """Convert a free-text label to a valid HA entity-id fragment.

    Transliterates umlauts, strips non-alphanumeric chars, collapses underscores.
    """
    # NFD decompose → strip combining marks (ä→a, ö→o, ü→u, ß stays)
    label = label.replace("ß", "ss")
    nfkd = unicodedata.normalize("NFKD", label)
    ascii_str = nfkd.encode("ascii", "ignore").decode("ascii")
    # Replace non-alphanumeric with underscore, collapse, strip edges
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", ascii_str).strip("_").lower()
    return slug


def _extract_channel_volume(
    channel: dict[str, Any],
    tanks: list[dict[str, Any]] | None = None,
) -> float | None:
    """Extract volume (liters) for a delivery channel.

    Priority:
    1. method_params.volume_per_feeding_liters (drench) or volume_per_spray_liters (foliar)
    2. First tank's volume_liters at the location (fertigation)
    3. Parse number from channel_id or label (e.g. "tank-60l" → 60, "10L Gießkanne" → 10)
    """
    # 1. From method_params
    params = channel.get("method_params")
    if params:
        vol = params.get("volume_per_feeding_liters") or params.get(
            "volume_per_spray_liters"
        )
        if vol and vol > 0:
            return float(vol)

    # 2. From location tanks (for fertigation)
    method = channel.get("application_method", "")
    if method == "fertigation" and tanks:
        for tank in tanks:
            tv = tank.get("volume_liters")
            if tv and tv > 0:
                return float(tv)

    # 3. Parse from channel_id or label
    for text in (channel.get("channel_id", ""), channel.get("label", "")):
        m = re.search(r"(\d+(?:\.\d+)?)\s*[lL]", text)
        if m:
            return float(m.group(1))

    return None


# --- Device info builders ---


def plant_device_info(entry: ConfigEntry, plant: dict[str, Any]) -> DeviceInfo:
    """Build DeviceInfo for a plant instance."""
    key = plant["key"]
    name = plant.get("plant_name") or plant.get("instance_id", key)
    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry.entry_id}_plant_{key}")},
        name=name,
        manufacturer="Kamerplanter",
        model="Plant Instance",
        via_device=(DOMAIN, entry.entry_id),
    )


def run_device_info(entry: ConfigEntry, run: dict[str, Any]) -> DeviceInfo:
    """Build DeviceInfo for a planting run."""
    key = run["key"]
    name = run.get("name", key)
    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry.entry_id}_run_{key}")},
        name=name,
        manufacturer="Kamerplanter",
        model=f"Planting Run ({run.get('run_type', 'unknown')})",
        via_device=(DOMAIN, entry.entry_id),
    )


def location_device_info(entry: ConfigEntry, loc: dict[str, Any]) -> DeviceInfo:
    """Build DeviceInfo for a location."""
    key = loc.get("key") or loc.get("_key", "")
    name = loc.get("name", key)
    loc_type = loc.get("location_type_key", "location")
    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry.entry_id}_location_{key}")},
        name=name,
        manufacturer="Kamerplanter",
        model=f"Location ({loc_type})",
        via_device=(DOMAIN, entry.entry_id),
    )


def tank_device_info(
    entry: ConfigEntry, tank: dict[str, Any], loc: dict[str, Any] | None = None,
) -> DeviceInfo:
    """Build DeviceInfo for a tank (standalone device)."""
    key = tank.get("key", "")
    name = tank.get("name", key)
    tank_type = tank.get("tank_type", "unknown")
    volume = tank.get("volume_liters")
    model = f"Tank ({tank_type})"
    if volume:
        model += f" {volume}L"
    loc_name = loc.get("name", "") if loc else ""
    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry.entry_id}_tank_{key}")},
        name=name,
        manufacturer="Kamerplanter",
        model=model,
        suggested_area=loc_name or None,
        via_device=(DOMAIN, entry.entry_id),
    )


def server_device_info(entry: ConfigEntry) -> DeviceInfo:
    """Build DeviceInfo for the Kamerplanter server (hub device)."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="Kamerplanter",
        manufacturer="Kamerplanter",
        model="Kamerplanter Server",
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Kamerplanter sensor entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    plant_coord: KamerplanterPlantCoordinator = data["coordinators"]["plants"]
    run_coord = data["coordinators"].get("runs")
    loc_coord: KamerplanterLocationCoordinator = data["coordinators"]["locations"]
    task_coord: KamerplanterTaskCoordinator = data["coordinators"]["tasks"]
    alert_coord: KamerplanterAlertCoordinator = data["coordinators"]["alerts"]

    entities: list[SensorEntity] = []

    # Plant instance sensors — only active (not removed)
    if plant_coord.data:
        for plant in plant_coord.data:
            if plant.get("removed_on"):
                continue
            key = plant["key"]
            dev = plant_device_info(entry, plant)
            entities.extend([
                PlantPhaseSensor(plant_coord, entry, key, dev),
                PlantDaysInPhaseSensor(plant_coord, entry, key, dev),
                PlantNutrientPlanSensor(plant_coord, entry, key, dev),
                PlantPhaseTimelineSensor(plant_coord, entry, key, dev),
                PlantNextPhaseSensor(plant_coord, entry, key, dev),
                PlantActiveChannelsSensor(plant_coord, entry, key, dev),
            ])

    # Plant channel sensors — one per delivery channel, dosages as attributes
    if plant_coord.data:
        for plant in plant_coord.data:
            if plant.get("removed_on"):
                continue
            key = plant["key"]
            dev = plant_device_info(entry, plant)
            dosage_data = plant.get("_current_dosages")
            if dosage_data and isinstance(dosage_data, dict):
                for channel in dosage_data.get("channels", []):
                    ch_id = channel.get("channel_id", "")
                    ch_label = channel.get("label", ch_id)
                    dosages = {
                        d.get("product_name", d.get("fertilizer_key", "?")): d.get("ml_per_liter")
                        for d in channel.get("dosages", [])
                        if d.get("ml_per_liter") is not None
                    }
                    if dosages:
                        entities.append(
                            PlantChannelSensor(
                                plant_coord, entry, key, dev,
                                ch_id, ch_label, dosages,
                            )
                        )

    # Planting run sensors — only active/planned runs
    if run_coord and run_coord.data:
        for run in run_coord.data:
            if run.get("status") in ("completed", "cancelled"):
                continue
            key = run["key"]
            dev = run_device_info(entry, run)
            entities.extend([
                RunStatusSensor(run_coord, entry, key, dev),
                RunPlantCountSensor(run_coord, entry, key, dev),
                RunNutrientPlanSensor(run_coord, entry, key, dev),
                RunPhaseTimelineSensor(run_coord, entry, key, dev),
                RunNextPhaseSensor(run_coord, entry, key, dev),
            ])
            # Run channel sensors — discover from ALL phase entries so entities
            # exist for every channel; _handle_coordinator_update filters to
            # the current week dynamically.
            current_entries = run.get("_phase_entries", [])
            channel_labels: dict[str, str] = {}
            channel_dosages: dict[str, dict[str, float]] = {}
            channel_volumes: dict[str, float | None] = {}
            for pe in current_entries:
                for channel in pe.get("delivery_channels", []):
                    ch_id = channel.get("channel_id", "")
                    if not ch_id:
                        continue
                    if ch_id not in channel_labels:
                        channel_labels[ch_id] = channel.get("label", ch_id)
                    if ch_id not in channel_dosages:
                        channel_dosages[ch_id] = {}
                    if ch_id not in channel_volumes:
                        channel_volumes[ch_id] = _extract_channel_volume(channel)
                    for dosage in channel.get("fertilizer_dosages", []):
                        product = dosage.get("product_name", dosage.get("fertilizer_key", "?"))
                        ml = dosage.get("ml_per_liter")
                        if product and ml is not None and product not in channel_dosages[ch_id]:
                            channel_dosages[ch_id][product] = ml
            for ch_id, dosages in channel_dosages.items():
                if dosages:
                    entities.append(
                        RunChannelSensor(
                            run_coord, entry, key, dev,
                            ch_id, channel_labels[ch_id], dosages,
                            channel_volumes.get(ch_id),
                        )
                    )

    # Location sensors — each location becomes a device
    if loc_coord.data:
        for loc in loc_coord.data:
            loc_key = loc.get("key") or loc.get("_key", "")
            if not loc_key:
                continue
            dev = location_device_info(entry, loc)
            entities.extend([
                LocationTypeSensor(loc_coord, entry, loc_key, dev),
                LocationActiveRunCountSensor(loc_coord, entry, loc_key, dev),
                LocationActivePlantCountSensor(loc_coord, entry, loc_key, dev),
            ])
            # When an active run is assigned, add run-like sensors
            primary_run = loc.get("_primary_run")
            if primary_run:
                entities.extend([
                    LocationRunPhaseSensor(loc_coord, entry, loc_key, dev),
                    LocationRunDaysInPhaseSensor(loc_coord, entry, loc_key, dev),
                    LocationRunNutrientPlanSensor(loc_coord, entry, loc_key, dev),
                    LocationRunNextPhaseSensor(loc_coord, entry, loc_key, dev),
                    LocationRunPhaseTimelineSensor(loc_coord, entry, loc_key, dev),
                ])
                # Channel sensors from primary run
                # Channel sensors from current week's phase entry only
                current_entries = primary_run.get(
                    "_current_phase_entries",
                    primary_run.get("_phase_entries", []),
                )
                loc_tanks = loc.get("_tanks", [])
                channel_labels: dict[str, str] = {}
                channel_dosages: dict[str, dict[str, float]] = {}
                channel_volumes: dict[str, float | None] = {}
                for pe in current_entries:
                    for channel in pe.get("delivery_channels", []):
                        ch_id = channel.get("channel_id", "")
                        if not ch_id:
                            continue
                        if ch_id not in channel_labels:
                            channel_labels[ch_id] = channel.get("label", ch_id)
                        if ch_id not in channel_dosages:
                            channel_dosages[ch_id] = {}
                        if ch_id not in channel_volumes:
                            channel_volumes[ch_id] = _extract_channel_volume(
                                channel, loc_tanks
                            )
                        for dosage in channel.get("fertilizer_dosages", []):
                            product = dosage.get(
                                "product_name", dosage.get("fertilizer_key", "?")
                            )
                            ml = dosage.get("ml_per_liter")
                            if (
                                product
                                and ml is not None
                                and product not in channel_dosages[ch_id]
                            ):
                                channel_dosages[ch_id][product] = ml
                for ch_id, dosages in channel_dosages.items():
                    if dosages:
                        entities.append(
                            LocationChannelSensor(
                                loc_coord, entry, loc_key, dev,
                                ch_id, channel_labels[ch_id], dosages,
                                channel_volumes.get(ch_id),
                            )
                        )

            # Legacy tank sensor under location (kept for backwards compat)
            for tank in loc.get("_tanks", []):
                tank_key = tank.get("key", "")
                if tank_key:
                    entities.append(
                        LocationTankSensor(loc_coord, entry, loc_key, tank_key, dev)
                    )
                    if tank.get("volume_liters"):
                        entities.append(
                            LocationTankVolumeSensor(
                                loc_coord, entry, loc_key, tank_key, dev
                            )
                        )

    # --- Standalone Tank devices ---
    seen_tanks: set[str] = set()
    if loc_coord.data:
        for loc in loc_coord.data:
            for tank in loc.get("_tanks", []):
                tank_key = tank.get("key", "")
                if not tank_key or tank_key in seen_tanks:
                    continue
                seen_tanks.add(tank_key)
                loc_key = loc.get("key") or loc.get("_key", "")
                t_dev = tank_device_info(entry, tank, loc)

                # Info sensor with HA entity IDs from KA + fill data
                entities.append(
                    TankInfoSensor(loc_coord, entry, tank_key, loc_key, t_dev)
                )
                # Volume sensor (tank capacity in liters)
                entities.append(
                    TankVolumeSensor(loc_coord, entry, tank_key, loc_key, t_dev)
                )

    # --- Task / care notification sensors (REQ-030) ---
    srv_dev = server_device_info(entry)
    entities.extend([
        TasksDueTodaySensor(task_coord, alert_coord, entry, srv_dev),
        TasksOverdueSensor(alert_coord, entry, srv_dev),
        NextWateringSensor(task_coord, entry, srv_dev),
    ])

    async_add_entities(entities)


# --- Base class ---


class KpSensorBase(CoordinatorEntity, RestoreEntity, SensorEntity):
    """Base class for Kamerplanter sensor entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: Any,
        entry: ConfigEntry,
        resource_key: str,
        suffix: str,
        device_info: DeviceInfo,
    ) -> None:
        super().__init__(coordinator)
        self._resource_key = resource_key
        self._entry = entry
        slug = _slugify_key(resource_key)
        self._attr_unique_id = f"{entry.entry_id}_kp_{slug}_{suffix}"
        self.entity_id = f"sensor.kp_{slug}_{suffix}"
        self._attr_device_info = device_info

    def _find_resource(self) -> dict[str, Any] | None:
        if not self.coordinator.data:
            return None
        for item in self.coordinator.data:
            if item.get("key") == self._resource_key:
                return item
        return None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last and last.state not in ("unknown", "unavailable", ""):
            self._attr_native_value = last.state
            self.async_write_ha_state()
        # Populate state immediately from existing coordinator data
        if self.coordinator.data:
            self._handle_coordinator_update()


# --- Plant sensors ---


class PlantPhaseSensor(KpSensorBase):
    """Current growth phase."""

    _attr_icon = "mdi:sprout"

    def __init__(self, coordinator: Any, entry: ConfigEntry, key: str, dev: DeviceInfo) -> None:
        super().__init__(coordinator, entry, key, "phase", dev)
        self._attr_name = "Phase"

    @callback
    def _handle_coordinator_update(self) -> None:
        resource = self._find_resource()
        if resource:
            self._attr_native_value = resource.get("current_phase", "unknown")
        self.async_write_ha_state()


class PlantDaysInPhaseSensor(KpSensorBase):
    """Days in current phase."""

    _attr_icon = "mdi:calendar-clock"
    _attr_native_unit_of_measurement = UnitOfTime.DAYS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: Any, entry: ConfigEntry, key: str, dev: DeviceInfo) -> None:
        super().__init__(coordinator, entry, key, "days_in_phase", dev)
        self._attr_name = "Days in Phase"

    @callback
    def _handle_coordinator_update(self) -> None:
        resource = self._find_resource()
        if resource:
            entered_at = resource.get("current_phase_started_at")
            if entered_at:
                entered = datetime.fromisoformat(entered_at)
                delta = datetime.now(tz=timezone.utc) - entered
                self._attr_native_value = delta.days
            else:
                self._attr_native_value = None
        self.async_write_ha_state()


class PlantNutrientPlanSensor(KpSensorBase):
    """Assigned nutrient plan name."""

    _attr_icon = "mdi:flask-outline"

    def __init__(self, coordinator: Any, entry: ConfigEntry, key: str, dev: DeviceInfo) -> None:
        super().__init__(coordinator, entry, key, "nutrient_plan", dev)
        self._attr_name = "Nutrient Plan"

    @callback
    def _handle_coordinator_update(self) -> None:
        resource = self._find_resource()
        if resource:
            plan = resource.get("_nutrient_plan")
            self._attr_native_value = plan.get("name") if plan else None
        self.async_write_ha_state()


class PlantChannelSensor(KpSensorBase):
    """Delivery channel sensor grouping all fertilizer dosages as attributes."""

    _attr_icon = "mdi:bottle-tonic"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: Any,
        entry: ConfigEntry,
        key: str,
        dev: DeviceInfo,
        channel_id: str,
        channel_label: str,
        dosages: dict[str, float],
    ) -> None:
        suffix = _slugify_label(channel_id)
        super().__init__(coordinator, entry, key, f"{suffix}_mix", dev)
        self._attr_name = channel_label
        self._channel_id = channel_id
        self._attr_native_value = len(dosages)
        self._attr_extra_state_attributes = {
            "plant_key": key,
            "channel_id": channel_id,
            **{f"{name} (ml/L)": val for name, val in dosages.items()},
        }

    async def async_added_to_hass(self) -> None:
        """Skip string-based restore — coordinator data takes precedence."""
        await CoordinatorEntity.async_added_to_hass(self)

    @callback
    def _handle_coordinator_update(self) -> None:
        resource = self._find_resource()
        if resource:
            dosage_data = resource.get("_current_dosages")
            if dosage_data and isinstance(dosage_data, dict):
                for channel in dosage_data.get("channels", []):
                    ch_id = channel.get("channel_id", "")
                    if ch_id == self._channel_id:
                        dosages = {
                            d.get("product_name", d.get("fertilizer_key", "?")): d.get("ml_per_liter")
                            for d in channel.get("dosages", [])
                            if d.get("ml_per_liter") is not None
                        }
                        self._attr_native_value = len(dosages)
                        self._attr_extra_state_attributes = {
                            "plant_key": self._resource_key,
                            "channel_id": self._channel_id,
                            **{f"{name} (ml/L)": val for name, val in dosages.items()},
                        }
                        self.async_write_ha_state()
                        return
            self._attr_native_value = 0
            self._attr_extra_state_attributes = {
                "plant_key": self._resource_key,
                "channel_id": self._channel_id,
            }
        self.async_write_ha_state()


class PlantActiveChannelsSensor(KpSensorBase):
    """Overview sensor listing all active delivery channels for a plant."""

    _attr_icon = "mdi:water-pump"

    def __init__(self, coordinator: Any, entry: ConfigEntry, key: str, dev: DeviceInfo) -> None:
        super().__init__(coordinator, entry, key, "active_channels", dev)
        self._attr_name = "Active Channels"
        resource = self._find_resource()
        if resource:
            self._update_from_channels(resource)

    def _update_from_channels(self, plant: dict[str, Any]) -> None:
        channels = plant.get("_active_channels", [])
        self._attr_native_value = len(channels)
        attrs: dict[str, Any] = {"plant_key": self._resource_key, "channel_ids": []}
        for ch in channels:
            ch_id = ch.get("channel_id", "")
            attrs["channel_ids"].append(ch_id)
            dosage_summary = {
                d.get("product_name", d.get("fertilizer_key", "?")): d.get("ml_per_liter")
                for d in ch.get("dosages", [])
                if d.get("ml_per_liter") is not None
            }
            attrs[ch_id] = {
                "label": ch.get("label", ch_id),
                "application_method": ch.get("application_method", ""),
                "target_ec_ms": ch.get("target_ec_ms"),
                "target_ph": ch.get("target_ph"),
                "phase_name": ch.get("phase_name", ""),
                "week_start": ch.get("week_start"),
                "week_end": ch.get("week_end"),
                "dosages": dosage_summary,
            }
        self._attr_extra_state_attributes = attrs

    @callback
    def _handle_coordinator_update(self) -> None:
        resource = self._find_resource()
        if resource:
            self._update_from_channels(resource)
        else:
            self._attr_native_value = 0
            self._attr_extra_state_attributes = {
                "plant_key": self._resource_key,
                "channel_ids": [],
            }
        self.async_write_ha_state()


class PlantPhaseTimelineSensor(KpSensorBase):
    """Phase timeline with all phases from history as structured attributes."""

    _attr_icon = "mdi:timeline-clock-outline"

    def __init__(self, coordinator: Any, entry: ConfigEntry, key: str, dev: DeviceInfo) -> None:
        super().__init__(coordinator, entry, key, "phase_timeline", dev)
        self._attr_name = "Phase Timeline"
        resource = self._find_resource()
        if resource:
            self._update_from_history(resource)

    def _update_from_history(self, plant: dict[str, Any]) -> None:
        history = plant.get("_phase_history", [])
        current_phase = plant.get("current_phase")
        current_started = plant.get("current_phase_started_at")

        phases: list[dict[str, Any]] = []
        seen_phases: set[str] = set()
        for h in history:
            entered = h.get("entered_at", "")
            exited = h.get("exited_at")
            days = h.get("actual_duration_days")
            if days is None and entered and not exited:
                entered_dt = datetime.fromisoformat(entered) if isinstance(entered, str) else entered
                if hasattr(entered_dt, "tzinfo") and entered_dt.tzinfo is None:
                    entered_dt = entered_dt.replace(tzinfo=timezone.utc)
                days = (datetime.now(tz=timezone.utc) - entered_dt).days

            phase_name = h.get("phase_name", "unknown")
            entered_str = str(entered)[:10] if entered else None
            seen_phases.add(phase_name.lower())

            # Determine status
            if exited:
                status = "completed"
            elif phase_name.lower() == (current_phase or "").lower():
                status = "current"
            else:
                status = "unknown"

            phases.append({
                "phase": phase_name,
                "status": status,
                "started": entered_str,
                "date": entered_str,
                "days": days,
            })

        # Fallback: if current_phase is not in history, synthesize an entry
        if current_phase and current_phase.lower() not in seen_phases:
            days_in = None
            started_str = None
            if current_started:
                try:
                    entered_dt = datetime.fromisoformat(current_started)
                    if entered_dt.tzinfo is None:
                        entered_dt = entered_dt.replace(tzinfo=timezone.utc)
                    days_in = (datetime.now(tz=timezone.utc) - entered_dt).days
                    started_str = str(current_started)[:10]
                except (ValueError, TypeError):
                    pass
            phases.append({
                "phase": current_phase,
                "status": "current",
                "started": started_str,
                "date": started_str,
                "days": days_in,
            })

        current = next((p["phase"] for p in phases if p["status"] == "current"), None)
        if not current:
            completed = [p["phase"] for p in phases if p["status"] == "completed"]
            current = completed[-1] if completed else current_phase
        self._attr_native_value = current or "unknown"

        attrs: dict[str, Any] = {
            p["phase"]: {
                "status": p["status"],
                "started": p["started"],
                "date": p.get("date"),
                "days": p["days"],
            }
            for p in phases
        }

        # Add progress info for current phase
        if current_started:
            try:
                entered_dt = datetime.fromisoformat(current_started)
                if entered_dt.tzinfo is None:
                    entered_dt = entered_dt.replace(tzinfo=timezone.utc)
                days_in = (datetime.now(tz=timezone.utc) - entered_dt).days
                attrs["current_phase_name"] = current or "unknown"
                attrs["days_in_phase"] = days_in
            except (ValueError, TypeError):
                pass

        self._attr_extra_state_attributes = attrs

    async def async_added_to_hass(self) -> None:
        """Skip string-based restore for timeline sensor."""
        await CoordinatorEntity.async_added_to_hass(self)

    @callback
    def _handle_coordinator_update(self) -> None:
        resource = self._find_resource()
        if resource:
            self._update_from_history(resource)
        self.async_write_ha_state()


class PlantNextPhaseSensor(KpSensorBase):
    """Next upcoming phase after the current one."""

    _attr_icon = "mdi:skip-next"

    def __init__(self, coordinator: Any, entry: ConfigEntry, key: str, dev: DeviceInfo) -> None:
        super().__init__(coordinator, entry, key, "next_phase", dev)
        self._attr_name = "Next Phase"
        resource = self._find_resource()
        if resource:
            self._update_from_history(resource)

    def _update_from_history(self, plant: dict[str, Any]) -> None:
        history = plant.get("_phase_history", [])
        current_phase = (plant.get("current_phase") or "").lower()

        # Find the current phase in history, then look for the next one
        found_current = False
        for h in history:
            if found_current:
                self._attr_native_value = h.get("phase_name")
                return
            phase_name = (h.get("phase_name") or "").lower()
            if phase_name == current_phase and not h.get("exited_at"):
                found_current = True

        # No next phase found in history — try standard phase sequence
        _STANDARD_PHASES = [
            "germination", "seedling", "vegetative", "flowering",
            "ripening", "harvest",
        ]
        _EXTENDED_PHASES = [
            "germination", "seedling", "juvenile", "vegetative",
            "climbing", "short_day_induction", "leaf_phase",
            "flowering", "ripening", "harvest", "flushing",
            "drying", "curing", "senescence", "dormancy",
        ]
        if current_phase:
            # Try extended phases first, fall back to standard
            for phase_list in (_EXTENDED_PHASES, _STANDARD_PHASES):
                try:
                    idx = next(
                        i for i, p in enumerate(phase_list)
                        if p == current_phase
                    )
                    if idx + 1 < len(phase_list):
                        self._attr_native_value = phase_list[idx + 1]
                        return
                except StopIteration:
                    continue

        self._attr_native_value = None

    async def async_added_to_hass(self) -> None:
        await CoordinatorEntity.async_added_to_hass(self)

    @callback
    def _handle_coordinator_update(self) -> None:
        resource = self._find_resource()
        if resource:
            self._update_from_history(resource)
        self.async_write_ha_state()


# --- Planting Run sensors ---


class RunStatusSensor(KpSensorBase):
    """Planting run status."""

    _attr_icon = "mdi:sprout-outline"

    def __init__(self, coordinator: Any, entry: ConfigEntry, key: str, dev: DeviceInfo) -> None:
        super().__init__(coordinator, entry, key, "status", dev)
        self._attr_name = "Status"

    @callback
    def _handle_coordinator_update(self) -> None:
        resource = self._find_resource()
        if resource:
            self._attr_native_value = resource.get("status", "unknown")
        self.async_write_ha_state()


class RunPlantCountSensor(KpSensorBase):
    """Planting run actual plant count."""

    _attr_icon = "mdi:flower"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: Any, entry: ConfigEntry, key: str, dev: DeviceInfo) -> None:
        super().__init__(coordinator, entry, key, "plant_count", dev)
        self._attr_name = "Plant Count"

    @callback
    def _handle_coordinator_update(self) -> None:
        resource = self._find_resource()
        if resource:
            self._attr_native_value = resource.get("actual_quantity", 0)
        self.async_write_ha_state()


class RunNutrientPlanSensor(KpSensorBase):
    """Assigned nutrient plan name for a planting run."""

    _attr_icon = "mdi:flask-outline"

    def __init__(self, coordinator: Any, entry: ConfigEntry, key: str, dev: DeviceInfo) -> None:
        super().__init__(coordinator, entry, key, "nutrient_plan", dev)
        self._attr_name = "Nutrient Plan"

    @callback
    def _handle_coordinator_update(self) -> None:
        resource = self._find_resource()
        if resource:
            plan = resource.get("_nutrient_plan")
            self._attr_native_value = plan.get("name") if plan else None
        self.async_write_ha_state()


class RunPhaseTimelineSensor(KpSensorBase):
    """Phase timeline with all phases as structured attributes."""

    _attr_icon = "mdi:timeline-clock-outline"

    def __init__(self, coordinator: Any, entry: ConfigEntry, key: str, dev: DeviceInfo) -> None:
        super().__init__(coordinator, entry, key, "phase_timeline", dev)
        self._attr_name = "Phase Timeline"
        resource = self._find_resource()
        if resource:
            self._update_from_timeline(resource.get("_timeline", []), resource)

    def _update_from_timeline(
        self, timeline: list[dict[str, Any]], run: dict[str, Any] | None = None,
    ) -> None:
        phases = self._extract_phases(timeline)
        current = next((p["phase"] for p in phases if p["status"] == "current"), None)
        if not current:
            # Fall back to last completed phase
            completed = [p["phase"] for p in phases if p["status"] == "completed"]
            current = completed[-1] if completed else None
        self._attr_native_value = current or "unknown"
        attrs: dict[str, Any] = {
            p["phase"]: {
                "status": p["status"],
                "started": p["started"],
                "date": p.get("date"),
                "days": p["days"],
            }
            for p in phases
        }
        if run:
            _enrich_phase_progress(attrs, run)
        self._attr_extra_state_attributes = attrs

    @staticmethod
    def _extract_phases(timeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
        phases: list[dict[str, Any]] = []
        for species in timeline:
            for p in species.get("phases", []):
                started = p.get("actual_entered_at")
                days = p.get("actual_duration_days")
                if days is None and started:
                    entered = datetime.fromisoformat(started)
                    if entered.tzinfo is None:
                        entered = entered.replace(tzinfo=timezone.utc)
                    days = (datetime.now(tz=timezone.utc) - entered).days
                # Determine display date: actual start or projected start
                proj_start = p.get("projected_start")
                proj_end = p.get("projected_end")
                display_date = started[:10] if started else None
                if not display_date and proj_start:
                    ds = str(proj_start)
                    display_date = ds[:10] if len(ds) >= 10 else ds
                phases.append({
                    "phase": p.get("display_name", p.get("phase_name", "?")),
                    "status": p.get("status", "unknown"),
                    "started": started[:10] if started else None,
                    "date": display_date,
                    "days": days,
                })
        return phases

    async def async_added_to_hass(self) -> None:
        """Skip string-based restore for timeline sensor."""
        await CoordinatorEntity.async_added_to_hass(self)

    @callback
    def _handle_coordinator_update(self) -> None:
        resource = self._find_resource()
        if resource:
            self._update_from_timeline(resource.get("_timeline", []), resource)
        self.async_write_ha_state()


class RunNextPhaseSensor(KpSensorBase):
    """Next upcoming phase after the current one."""

    _attr_icon = "mdi:skip-next"

    def __init__(self, coordinator: Any, entry: ConfigEntry, key: str, dev: DeviceInfo) -> None:
        super().__init__(coordinator, entry, key, "next_phase", dev)
        self._attr_name = "Next Phase"
        resource = self._find_resource()
        if resource:
            self._update_from_timeline(resource.get("_timeline", []))

    def _update_from_timeline(self, timeline: list[dict[str, Any]]) -> None:
        phases = RunPhaseTimelineSensor._extract_phases(timeline)
        found_current = False
        for p in phases:
            if found_current:
                self._attr_native_value = p["phase"]
                return
            if p["status"] == "current":
                found_current = True
        self._attr_native_value = None

    async def async_added_to_hass(self) -> None:
        await CoordinatorEntity.async_added_to_hass(self)

    @callback
    def _handle_coordinator_update(self) -> None:
        resource = self._find_resource()
        if resource:
            self._update_from_timeline(resource.get("_timeline", []))
        self.async_write_ha_state()


class RunChannelSensor(KpSensorBase):
    """Delivery channel sensor grouping all fertilizer dosages as attributes."""

    _attr_icon = "mdi:bottle-tonic"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: Any,
        entry: ConfigEntry,
        key: str,
        dev: DeviceInfo,
        channel_id: str,
        channel_label: str,
        dosages: dict[str, float],
        volume_liters: float | None = None,
    ) -> None:
        suffix = _slugify_label(channel_id)
        super().__init__(coordinator, entry, key, f"{suffix}_mix", dev)
        self._attr_name = channel_label
        self._channel_id = channel_id
        self._attr_native_value = len(dosages)
        attrs: dict[str, Any] = {
            f"{name} (ml/L)": val for name, val in dosages.items()
        }
        if volume_liters:
            attrs["volume_liters"] = volume_liters
        self._attr_extra_state_attributes = attrs

    async def async_added_to_hass(self) -> None:
        """Skip string-based restore — coordinator data takes precedence."""
        await CoordinatorEntity.async_added_to_hass(self)

    @callback
    def _handle_coordinator_update(self) -> None:
        resource = self._find_resource()
        if resource:
            current_entries = resource.get(
                "_current_phase_entries", resource.get("_phase_entries", [])
            )
            dosages: dict[str, float] = {}
            volume: float | None = None
            for pe in current_entries:
                for channel in pe.get("delivery_channels", []):
                    if channel.get("channel_id") == self._channel_id:
                        for d in channel.get("fertilizer_dosages", []):
                            product = d.get("product_name", d.get("fertilizer_key", "?"))
                            ml = d.get("ml_per_liter")
                            if product and ml is not None and product not in dosages:
                                dosages[product] = ml
                        if volume is None:
                            volume = _extract_channel_volume(channel)
            self._attr_native_value = len(dosages)
            week = resource.get("_current_week")
            attrs: dict[str, Any] = {
                f"{name} (ml/L)": val for name, val in dosages.items()
            }
            if week is not None:
                attrs["current_week"] = week
            if volume:
                attrs["volume_liters"] = volume
            self._attr_extra_state_attributes = attrs
        self.async_write_ha_state()


def _enrich_phase_progress(attrs: dict[str, Any], run: dict[str, Any]) -> None:
    """Add phase progress attributes from timeline data.

    Calculates remaining time directly from the timeline phases
    (typical_duration_days + actual_entered_at) without requiring a NutrientPlan.
    Falls back to NutrientPlan week data if available.
    """
    timeline = run.get("_timeline", [])

    # Flatten timeline phases
    all_phases: list[dict[str, Any]] = []
    for species in timeline:
        for p in species.get("phases", []):
            all_phases.append(p)

    # Find current phase — fall back to last completed if none is "current"
    current_phase = None
    current_idx = -1
    last_completed = None
    last_completed_idx = -1
    for i, p in enumerate(all_phases):
        if p.get("status") == "current":
            current_phase = p
            current_idx = i
            break
        if p.get("status") == "completed":
            last_completed = p
            last_completed_idx = i

    if not current_phase:
        # No explicit "current" — use last completed phase (transition not yet recorded)
        if last_completed:
            current_phase = last_completed
            current_idx = last_completed_idx
        else:
            return

    phase_name = current_phase.get("phase_name", current_phase.get("display_name", ""))
    entered_str = current_phase.get("actual_entered_at")
    typical_days = current_phase.get("typical_duration_days", 0)

    if not entered_str or not typical_days:
        # At minimum set the phase name so the card shows something
        if phase_name:
            attrs["current_phase_name"] = phase_name
        return

    entered = datetime.fromisoformat(entered_str)
    if entered.tzinfo is None:
        entered = entered.replace(tzinfo=timezone.utc)
    days_in = (datetime.now(tz=timezone.utc) - entered).days

    planned_weeks = max(1, typical_days // 7)
    week_in_phase = max(1, days_in // 7 + 1)
    remaining = max(0, planned_weeks - week_in_phase)
    progress_pct = round(min(100, (days_in / typical_days) * 100)) if typical_days > 0 else 0

    attrs["current_phase_name"] = phase_name
    display_name = current_phase.get("display_name", "")
    if display_name:
        attrs["current_phase_display_name"] = display_name
    attrs["phase_week"] = week_in_phase
    attrs["phase_planned_weeks"] = planned_weeks
    attrs["phase_remaining_weeks"] = remaining
    attrs["phase_progress_pct"] = progress_pct
    attrs["days_in_phase"] = days_in
    attrs["typical_duration_days"] = typical_days
    remaining_days = max(0, typical_days - days_in)
    attrs["remaining_days"] = remaining_days

    # Next phase info
    if current_idx + 1 < len(all_phases):
        next_p = all_phases[current_idx + 1]
        next_name = next_p.get("phase_name", next_p.get("display_name", ""))
        next_typical = next_p.get("typical_duration_days", 0)
        next_weeks = max(1, next_typical // 7) if next_typical else 0
        weeks_until = max(0, remaining)
        attrs["next_plan_phase"] = next_name
        attrs["next_plan_phase_weeks"] = next_weeks
        attrs["weeks_until_next_phase"] = weeks_until


# --- Location sensors ---


class _LocationSensorBase(KpSensorBase):
    """Base for location sensors — finds resource by location key."""

    def _find_resource(self) -> dict[str, Any] | None:
        if not self.coordinator.data:
            return None
        for loc in self.coordinator.data:
            key = loc.get("key") or loc.get("_key", "")
            if key == self._resource_key:
                return loc
        return None


class LocationTypeSensor(_LocationSensorBase):
    """Location type."""

    _attr_icon = "mdi:map-marker"

    def __init__(self, coordinator: Any, entry: ConfigEntry, key: str, dev: DeviceInfo) -> None:
        super().__init__(coordinator, entry, key, "location_type", dev)
        self._attr_name = "Location Type"

    @callback
    def _handle_coordinator_update(self) -> None:
        resource = self._find_resource()
        if resource:
            self._attr_native_value = resource.get("location_type_key", "unknown")
            self._attr_extra_state_attributes = {
                "light_type": resource.get("light_type"),
                "irrigation_system": resource.get("irrigation_system"),
                "area_m2": resource.get("area_m2"),
            }
        self.async_write_ha_state()


class LocationActiveRunCountSensor(_LocationSensorBase):
    """Number of active planting runs at this location."""

    _attr_icon = "mdi:sprout-outline"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: Any, entry: ConfigEntry, key: str, dev: DeviceInfo) -> None:
        super().__init__(coordinator, entry, key, "active_runs", dev)
        self._attr_name = "Active Runs"

    @callback
    def _handle_coordinator_update(self) -> None:
        resource = self._find_resource()
        if resource:
            self._attr_native_value = resource.get("_active_run_count", 0)
            runs = resource.get("_active_runs", [])
            self._attr_extra_state_attributes = {
                "run_names": [r.get("name", r.get("key", "")) for r in runs],
            }
        self.async_write_ha_state()


class LocationActivePlantCountSensor(_LocationSensorBase):
    """Number of active plant instances at this location."""

    _attr_icon = "mdi:flower"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: Any, entry: ConfigEntry, key: str, dev: DeviceInfo) -> None:
        super().__init__(coordinator, entry, key, "active_plants", dev)
        self._attr_name = "Active Plants"

    @callback
    def _handle_coordinator_update(self) -> None:
        resource = self._find_resource()
        if resource:
            self._attr_native_value = resource.get("_active_plant_count", 0)
            plants = resource.get("_active_plants", [])
            runs = resource.get("_active_runs", [])
            self._attr_extra_state_attributes = {
                "plant_names": [
                    p.get("plant_name") or p.get("instance_id", p.get("key", ""))
                    for p in plants
                ],
                "from_runs": resource.get("_run_plant_count", 0),
                "run_names": [r.get("name", "") for r in runs],
            }
        self.async_write_ha_state()


class LocationRunPhaseSensor(_LocationSensorBase):
    """Current growth phase from the primary assigned run."""

    _attr_icon = "mdi:sprout"

    def __init__(self, coordinator: Any, entry: ConfigEntry, key: str, dev: DeviceInfo) -> None:
        super().__init__(coordinator, entry, key, "phase", dev)
        self._attr_name = "Phase"

    @callback
    def _handle_coordinator_update(self) -> None:
        resource = self._find_resource()
        if resource:
            run = resource.get("_primary_run")
            if run:
                timeline = run.get("_timeline", [])
                phases = RunPhaseTimelineSensor._extract_phases(timeline)
                current = next(
                    (p["phase"] for p in phases if p["status"] == "current"), None
                )
                self._attr_native_value = current or run.get("status", "unknown")
                self._attr_extra_state_attributes = {
                    "run_name": run.get("name"),
                    "run_key": run.get("key"),
                }
            else:
                self._attr_native_value = "empty"
                self._attr_extra_state_attributes = {}
        self.async_write_ha_state()


class LocationRunDaysInPhaseSensor(_LocationSensorBase):
    """Days in current phase from the primary assigned run."""

    _attr_icon = "mdi:calendar-clock"
    _attr_native_unit_of_measurement = UnitOfTime.DAYS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: Any, entry: ConfigEntry, key: str, dev: DeviceInfo) -> None:
        super().__init__(coordinator, entry, key, "days_in_phase", dev)
        self._attr_name = "Days in Phase"

    @callback
    def _handle_coordinator_update(self) -> None:
        resource = self._find_resource()
        if resource:
            run = resource.get("_primary_run")
            if run:
                timeline = run.get("_timeline", [])
                phases = RunPhaseTimelineSensor._extract_phases(timeline)
                current = next(
                    (p for p in phases if p["status"] == "current"), None
                )
                self._attr_native_value = current["days"] if current else None
            else:
                self._attr_native_value = None
        self.async_write_ha_state()


class LocationRunNutrientPlanSensor(_LocationSensorBase):
    """Nutrient plan name from the primary assigned run."""

    _attr_icon = "mdi:flask-outline"

    def __init__(self, coordinator: Any, entry: ConfigEntry, key: str, dev: DeviceInfo) -> None:
        super().__init__(coordinator, entry, key, "nutrient_plan", dev)
        self._attr_name = "Nutrient Plan"

    @callback
    def _handle_coordinator_update(self) -> None:
        resource = self._find_resource()
        if resource:
            run = resource.get("_primary_run")
            if run:
                plan = run.get("_nutrient_plan")
                self._attr_native_value = plan.get("name") if plan else None
            else:
                self._attr_native_value = None
        self.async_write_ha_state()


class LocationRunNextPhaseSensor(_LocationSensorBase):
    """Next phase from the primary assigned run."""

    _attr_icon = "mdi:skip-next"

    def __init__(self, coordinator: Any, entry: ConfigEntry, key: str, dev: DeviceInfo) -> None:
        super().__init__(coordinator, entry, key, "next_phase", dev)
        self._attr_name = "Next Phase"

    @callback
    def _handle_coordinator_update(self) -> None:
        resource = self._find_resource()
        if resource:
            run = resource.get("_primary_run")
            if run:
                timeline = run.get("_timeline", [])
                phases = RunPhaseTimelineSensor._extract_phases(timeline)
                found_current = False
                for p in phases:
                    if found_current:
                        self._attr_native_value = p["phase"]
                        self.async_write_ha_state()
                        return
                    if p["status"] == "current":
                        found_current = True
            self._attr_native_value = None
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await CoordinatorEntity.async_added_to_hass(self)


class LocationRunPhaseTimelineSensor(_LocationSensorBase):
    """Full phase timeline from the primary assigned run."""

    _attr_icon = "mdi:timeline-clock-outline"

    def __init__(self, coordinator: Any, entry: ConfigEntry, key: str, dev: DeviceInfo) -> None:
        super().__init__(coordinator, entry, key, "phase_timeline", dev)
        self._attr_name = "Phase Timeline"

    @callback
    def _handle_coordinator_update(self) -> None:
        resource = self._find_resource()
        if resource:
            run = resource.get("_primary_run")
            if run:
                timeline = run.get("_timeline", [])
                phases = RunPhaseTimelineSensor._extract_phases(timeline)
                current = next(
                    (p["phase"] for p in phases if p["status"] == "current"), None
                )
                self._attr_native_value = current or "unknown"
                attrs: dict[str, Any] = {
                    p["phase"]: {
                        "status": p["status"],
                        "started": p["started"],
                        "date": p.get("date"),
                        "days": p["days"],
                    }
                    for p in phases
                }
                # Add phase progress info from nutrient plan entries
                _enrich_phase_progress(attrs, run)
                self._attr_extra_state_attributes = attrs
            else:
                self._attr_native_value = "empty"
                self._attr_extra_state_attributes = {}
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await CoordinatorEntity.async_added_to_hass(self)


class LocationChannelSensor(_LocationSensorBase):
    """Delivery channel dosages from the primary assigned run."""

    _attr_icon = "mdi:bottle-tonic"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: Any,
        entry: ConfigEntry,
        key: str,
        dev: DeviceInfo,
        channel_id: str,
        channel_label: str,
        dosages: dict[str, float],
        volume_liters: float | None = None,
    ) -> None:
        suffix = _slugify_label(channel_id)
        super().__init__(coordinator, entry, key, f"{suffix}_mix", dev)
        self._attr_name = channel_label
        self._channel_id = channel_id
        self._attr_native_value = len(dosages)
        attrs: dict[str, Any] = {
            f"{name} (ml/L)": val for name, val in dosages.items()
        }
        if volume_liters:
            attrs["volume_liters"] = volume_liters
        self._attr_extra_state_attributes = attrs

    async def async_added_to_hass(self) -> None:
        """Skip string-based restore — coordinator data takes precedence."""
        await CoordinatorEntity.async_added_to_hass(self)

    @callback
    def _handle_coordinator_update(self) -> None:
        resource = self._find_resource()
        if resource:
            run = resource.get("_primary_run")
            tanks = resource.get("_tanks", [])
            if run:
                current_entries = run.get(
                    "_current_phase_entries", run.get("_phase_entries", [])
                )
                dosages: dict[str, float] = {}
                volume: float | None = None
                for pe in current_entries:
                    for channel in pe.get("delivery_channels", []):
                        if channel.get("channel_id") == self._channel_id:
                            for d in channel.get("fertilizer_dosages", []):
                                product = d.get(
                                    "product_name",
                                    d.get("fertilizer_key", "?"),
                                )
                                ml = d.get("ml_per_liter")
                                if (
                                    product
                                    and ml is not None
                                    and product not in dosages
                                ):
                                    dosages[product] = ml
                            if volume is None:
                                volume = _extract_channel_volume(channel, tanks)
                self._attr_native_value = len(dosages)
                week = run.get("_current_week")
                attrs: dict[str, Any] = {
                    f"{name} (ml/L)": val for name, val in dosages.items()
                }
                if week is not None:
                    attrs["current_week"] = week
                if volume:
                    attrs["volume_liters"] = volume
                self._attr_extra_state_attributes = attrs
            else:
                self._attr_native_value = 0
                self._attr_extra_state_attributes = {}
        self.async_write_ha_state()


class LocationTankVolumeSensor(_LocationSensorBase):
    """Tank volume sensor — exposes assigned tank capacity in liters."""

    _attr_icon = "mdi:barrel"
    _attr_device_class = SensorDeviceClass.VOLUME
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfVolume.LITERS

    def __init__(
        self,
        coordinator: Any,
        entry: ConfigEntry,
        location_key: str,
        tank_key: str,
        dev: DeviceInfo,
    ) -> None:
        slug = _slugify_key(tank_key)
        super().__init__(coordinator, entry, location_key, f"tank_{slug}_volume", dev)
        self._tank_key = tank_key
        self._attr_name = "Tank Volume"

    def _find_tank(self) -> dict[str, Any] | None:
        resource = self._find_resource()
        if not resource:
            return None
        for tank in resource.get("_tanks", []):
            if tank.get("key") == self._tank_key:
                return tank
        return None

    @callback
    def _handle_coordinator_update(self) -> None:
        tank = self._find_tank()
        if tank:
            self._attr_native_value = tank.get("volume_liters")
            self._attr_extra_state_attributes = {
                "tank_key": self._tank_key,
                "tank_name": tank.get("name", ""),
                "tank_type": tank.get("tank_type"),
            }
        else:
            self._attr_native_value = None
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await CoordinatorEntity.async_added_to_hass(self)


class LocationTankSensor(_LocationSensorBase):
    """Tank sensor showing last fill date and tank details."""

    _attr_icon = "mdi:barrel"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(
        self,
        coordinator: Any,
        entry: ConfigEntry,
        location_key: str,
        tank_key: str,
        dev: DeviceInfo,
    ) -> None:
        slug = _slugify_key(tank_key)
        super().__init__(coordinator, entry, location_key, f"tank_{slug}", dev)
        self._tank_key = tank_key
        self._attr_name = "Tank"

    def _find_tank(self) -> dict[str, Any] | None:
        resource = self._find_resource()
        if not resource:
            return None
        for tank in resource.get("_tanks", []):
            if tank.get("key") == self._tank_key:
                return tank
        return None

    @callback
    def _handle_coordinator_update(self) -> None:
        tank = self._find_tank()
        if tank:
            latest = tank.get("_latest_fill")
            if latest and latest.get("filled_at"):
                self._attr_native_value = datetime.fromisoformat(
                    latest["filled_at"]
                )
            else:
                self._attr_native_value = None
            self._attr_extra_state_attributes = {
                "tank_key": self._tank_key,
                "tank_name": tank.get("name", ""),
                "volume_liters": tank.get("volume_liters"),
                "tank_type": tank.get("tank_type"),
                "material": tank.get("material"),
                "location_key": tank.get("location_key"),
            }
            if latest:
                self._attr_extra_state_attributes.update({
                    "last_fill_type": latest.get("fill_type"),
                    "last_fill_volume": latest.get("volume_liters"),
                    "last_fill_ec": latest.get("measured_ec_ms"),
                    "last_fill_ph": latest.get("measured_ph"),
                    "last_fill_performed_by": latest.get("performed_by"),
                    "fertilizers_count": len(latest.get("fertilizers_used", [])),
                })
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await CoordinatorEntity.async_added_to_hass(self)


# --- Standalone Tank device sensor ---


class TankInfoSensor(KpSensorBase):
    """Tank info sensor exposing KA-linked HA sensor entity IDs as attributes.

    The tank device has a single sensor whose attributes contain:
    - ha_ph_entity_id, ha_ec_entity_id, ha_temp_entity_id (from KA sensor config)
    - volume_liters, tank_type, material (from KA tank)
    - last_fill_at, fill_age_days, last_fill_type (from KA fill events)
    """

    _attr_icon = "mdi:barrel"

    def __init__(
        self,
        coordinator: Any,
        entry: ConfigEntry,
        tank_key: str,
        location_key: str,
        device_info: DeviceInfo,
    ) -> None:
        super().__init__(coordinator, entry, tank_key, "info", device_info)
        self._tank_key = tank_key
        self._location_key = location_key
        self._attr_name = "Tank"

    def _find_tank(self) -> dict[str, Any] | None:
        if not self.coordinator.data:
            return None
        for loc in self.coordinator.data:
            for tank in loc.get("_tanks", []):
                if tank.get("key") == self._tank_key:
                    return tank
        return None

    @callback
    def _handle_coordinator_update(self) -> None:
        tank = self._find_tank()
        if not tank:
            self.async_write_ha_state()
            return

        self._attr_native_value = tank.get("name", "unknown")

        # Build HA sensor entity ID mapping from KA sensor config
        # Only include sensors that are active and configured in KA
        ha_sensors = tank.get("_ha_sensors", [])
        sensor_map: dict[str, str] = {}
        metric_to_attr = {
            "ph": "ha_ph_entity_id",
            "ec_ms": "ha_ec_entity_id",
            "water_temp_celsius": "ha_temp_entity_id",
        }
        for s in ha_sensors:
            if not s.get("is_active"):
                continue
            attr_key = metric_to_attr.get(s.get("metric_type", ""))
            if attr_key and s.get("ha_entity_id"):
                sensor_map[attr_key] = s["ha_entity_id"]

        # Fill data
        fill = tank.get("_latest_fill") or {}
        filled_at = fill.get("filled_at")
        fill_age = None
        if filled_at:
            filled = datetime.fromisoformat(filled_at)
            if filled.tzinfo is None:
                filled = filled.replace(tzinfo=timezone.utc)
            fill_age = (datetime.now(tz=timezone.utc) - filled).days

        attrs_dict: dict[str, Any] = {
            # HA sensor entity IDs (only those configured in KA)
            **sensor_map,
            # Tank properties
            "tank_key": self._tank_key,
            "volume_liters": tank.get("volume_liters"),
            "tank_type": tank.get("tank_type"),
            "material": tank.get("material"),
            # Fill data
            "last_fill_at": filled_at,
            "fill_age_days": fill_age,
            "last_fill_type": fill.get("fill_type"),
        }
        # Fill details (only if fill exists)
        if fill:
            if fill.get("volume_liters"):
                attrs_dict["last_fill_volume"] = fill["volume_liters"]
            if fill.get("measured_ph") is not None:
                attrs_dict["last_fill_ph"] = fill["measured_ph"]
            if fill.get("measured_ec_ms") is not None:
                attrs_dict["last_fill_ec"] = fill["measured_ec_ms"]
            ferts = fill.get("fertilizers_used") or []
            if ferts:
                attrs_dict["last_fill_fert_count"] = len(ferts)
        self._attr_extra_state_attributes = attrs_dict
        self.async_write_ha_state()


class TankVolumeSensor(KpSensorBase):
    """Sensor exposing the tank's total volume in liters."""

    _attr_icon = "mdi:water-outline"
    _attr_device_class = SensorDeviceClass.VOLUME
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfVolume.LITERS

    def __init__(
        self,
        coordinator: Any,
        entry: ConfigEntry,
        tank_key: str,
        location_key: str,
        device_info: DeviceInfo,
    ) -> None:
        super().__init__(coordinator, entry, tank_key, "volume", device_info)
        self._tank_key = tank_key
        self._location_key = location_key
        self._attr_name = "Volume"

    def _find_tank(self) -> dict[str, Any] | None:
        if not self.coordinator.data:
            return None
        for loc in self.coordinator.data:
            for tank in loc.get("_tanks", []):
                if tank.get("key") == self._tank_key:
                    return tank
        return None

    @callback
    def _handle_coordinator_update(self) -> None:
        tank = self._find_tank()
        if not tank:
            self.async_write_ha_state()
            return
        self._attr_native_value = tank.get("volume_liters")
        self.async_write_ha_state()


# --- Task / care notification sensors (REQ-030) ---


class TasksDueTodaySensor(CoordinatorEntity, RestoreEntity, SensorEntity):
    """Sensor showing the number of tasks due today."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:clipboard-text-clock"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        task_coordinator: KamerplanterTaskCoordinator,
        alert_coordinator: KamerplanterAlertCoordinator,
        entry: ConfigEntry,
        device_info: DeviceInfo,
    ) -> None:
        super().__init__(task_coordinator)
        self._alert_coordinator = alert_coordinator
        self._attr_unique_id = f"{entry.entry_id}_kp_tasks_due_today"
        self.entity_id = "sensor.kp_tasks_due_today"
        self._attr_name = "Tasks Due Today"
        self._attr_device_info = device_info

    @callback
    def _handle_coordinator_update(self) -> None:
        today = date.today().isoformat()
        due_today: list[dict[str, Any]] = []
        overdue_count = 0
        upcoming_count = 0

        if self.coordinator.data:
            for task in self.coordinator.data:
                due = task.get("due_date", "")
                if due == today:
                    due_today.append(task)
                elif due and due < today:
                    overdue_count += 1
                elif due and due > today:
                    upcoming_count += 1

        # Also count overdue from alert coordinator
        if self._alert_coordinator.data:
            overdue_count = max(overdue_count, len(self._alert_coordinator.data))

        self._attr_native_value = len(due_today)

        # Build summary and plant list
        plant_names: list[str] = []
        plants_detail: list[dict[str, str]] = []
        for task in due_today:
            name = task.get("plant_name") or task.get("name", "")
            category = task.get("category", "")
            if name:
                plant_names.append(name)
            plants_detail.append({
                "name": name,
                "task_key": task.get("key", ""),
                "category": category,
                "plant_key": task.get("plant_key", ""),
            })

        summary = ", ".join(plant_names) if plant_names else "Keine Aufgaben heute"
        self._attr_extra_state_attributes = {
            "summary": summary,
            "plants": plants_detail,
            "urgency_counts": {
                "overdue": overdue_count,
                "due_today": len(due_today),
                "upcoming": upcoming_count,
            },
        }
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last and last.state not in ("unknown", "unavailable", ""):
            try:
                self._attr_native_value = int(last.state)
            except (ValueError, TypeError):
                self._attr_native_value = 0
            self.async_write_ha_state()
        if self.coordinator.data:
            self._handle_coordinator_update()


class TasksOverdueSensor(CoordinatorEntity, RestoreEntity, SensorEntity):
    """Sensor showing the number of overdue tasks."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:clipboard-alert"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: KamerplanterAlertCoordinator,
        entry: ConfigEntry,
        device_info: DeviceInfo,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_kp_tasks_overdue"
        self.entity_id = "sensor.kp_tasks_overdue"
        self._attr_name = "Tasks Overdue"
        self._attr_device_info = device_info

    @callback
    def _handle_coordinator_update(self) -> None:
        if not self.coordinator.data:
            self._attr_native_value = 0
            self._attr_extra_state_attributes = {
                "plants": [],
                "oldest_overdue_days": 0,
            }
            self.async_write_ha_state()
            return

        today = date.today()
        plants: list[dict[str, str]] = []
        oldest_days = 0

        for alert in self.coordinator.data:
            due = alert.get("due_date", "")
            plant_name = alert.get("plant_name") or alert.get("name", "")
            plant_key = alert.get("plant_key", "")
            plants.append({
                "name": plant_name,
                "plant_key": plant_key,
                "due_date": due,
                "task_key": alert.get("key", ""),
            })
            if due:
                try:
                    due_date = date.fromisoformat(due)
                    days_overdue = (today - due_date).days
                    if days_overdue > oldest_days:
                        oldest_days = days_overdue
                except (ValueError, TypeError):
                    pass

        self._attr_native_value = len(self.coordinator.data)
        self._attr_extra_state_attributes = {
            "plants": plants,
            "oldest_overdue_days": oldest_days,
        }
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last and last.state not in ("unknown", "unavailable", ""):
            try:
                self._attr_native_value = int(last.state)
            except (ValueError, TypeError):
                self._attr_native_value = 0
            self.async_write_ha_state()
        if self.coordinator.data:
            self._handle_coordinator_update()


class NextWateringSensor(CoordinatorEntity, RestoreEntity, SensorEntity):
    """Sensor showing the next plant due for watering."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:watering-can"

    def __init__(
        self,
        coordinator: KamerplanterTaskCoordinator,
        entry: ConfigEntry,
        device_info: DeviceInfo,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_kp_next_watering"
        self.entity_id = "sensor.kp_next_watering"
        self._attr_name = "Next Watering"
        self._attr_device_info = device_info

    @callback
    def _handle_coordinator_update(self) -> None:
        if not self.coordinator.data:
            self._attr_native_value = None
            self._attr_extra_state_attributes = {}
            self.async_write_ha_state()
            return

        # Find the earliest watering task by due_date
        watering_keywords = {"watering", "giessen", "water", "bewässerung"}
        earliest_task: dict[str, Any] | None = None
        earliest_due: str | None = None

        for task in self.coordinator.data:
            category = (task.get("category") or "").lower()
            name = (task.get("name") or task.get("title") or "").lower()
            is_watering = (
                category in watering_keywords
                or any(kw in name for kw in watering_keywords)
            )
            if not is_watering:
                continue
            due = task.get("due_date", "")
            if due and (earliest_due is None or due < earliest_due):
                earliest_due = due
                earliest_task = task

        if earliest_task:
            plant_name = (
                earliest_task.get("plant_name")
                or earliest_task.get("name")
                or "Unknown"
            )
            self._attr_native_value = plant_name
            self._attr_extra_state_attributes = {
                "due_date": earliest_due or "",
                "plant_key": earliest_task.get("plant_key", ""),
                "task_key": earliest_task.get("key", ""),
            }
        else:
            self._attr_native_value = None
            self._attr_extra_state_attributes = {}

        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last and last.state not in ("unknown", "unavailable", ""):
            self._attr_native_value = last.state
            self.async_write_ha_state()
        if self.coordinator.data:
            self._handle_coordinator_update()
