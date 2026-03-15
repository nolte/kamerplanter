"""DataUpdateCoordinators for the Kamerplanter integration."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import KamerplanterApi, KamerplanterAuthError, KamerplanterConnectionError
from .const import (
    CONF_POLL_ALERTS,
    CONF_POLL_LOCATIONS,
    CONF_POLL_PLANTS,
    CONF_POLL_TASKS,
    DEFAULT_POLL_ALERTS,
    DEFAULT_POLL_LOCATIONS,
    DEFAULT_POLL_PLANTS,
    DEFAULT_POLL_TASKS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def _normalize_phase_name(name: str) -> str:
    """Normalize phase name for comparison (lowercase, stripped)."""
    return name.strip().lower()


def _phase_names_match(a: str, b: str) -> bool:
    """Check if two phase names refer to the same phase.

    Handles mismatches between GrowthPhase.name (free text, e.g. 'Vegetative')
    and NutrientPlanPhaseEntry.phase_name (PhaseName enum, e.g. 'vegetative').
    """
    return _normalize_phase_name(a) == _normalize_phase_name(b)


def _calc_current_week(started_at_iso: str) -> int:
    """Calculate current week number from phase start date (1-based)."""
    started = datetime.fromisoformat(started_at_iso)
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    delta = datetime.now(tz=timezone.utc) - started
    return max(1, delta.days // 7 + 1)


def _calc_effective_plan_week(
    timeline: list[dict[str, Any]],
    entries: list[dict[str, Any]],
) -> int | None:
    """Calculate the effective plan week based on current phase + weeks into it.

    The plan's week numbering assumes ideal phase durations. When phases run
    longer or shorter than planned, absolute week-from-start diverges from
    the plan's week grid. Instead we:
    1. Find the current phase from the timeline
    2. Calculate how many weeks into the current phase we are
    3. Find the plan's first week_start for that phase_name
    4. Return phase_plan_start + weeks_in_phase
    """
    # Find the current phase from timeline
    current_phase_name: str | None = None
    current_phase_entered: str | None = None
    for species in timeline:
        for phase in species.get("phases", []):
            if phase.get("status") == "current":
                current_phase_name = phase.get("phase_name")
                current_phase_entered = phase.get("actual_entered_at")
                break
        if current_phase_name:
            break

    if not current_phase_name or not current_phase_entered:
        return None

    # Calculate weeks into the current phase
    weeks_in_phase = _calc_current_week(current_phase_entered) - 1  # 0-based

    # Find the plan's first week_start for this phase
    phase_plan_start: int | None = None
    for entry in entries:
        if _phase_names_match(entry.get("phase_name", ""), current_phase_name):
            ws = entry.get("week_start", 0)
            if phase_plan_start is None or ws < phase_plan_start:
                phase_plan_start = ws
            break  # entries are ordered, first match is earliest

    if phase_plan_start is None:
        return None

    return phase_plan_start + weeks_in_phase


def _filter_current_phase_entries(
    entries: list[dict[str, Any]], current_week: int
) -> list[dict[str, Any]]:
    """Filter phase entries to only the one matching the current week."""
    for entry in entries:
        ws = entry.get("week_start", 0)
        we = entry.get("week_end", 0)
        if ws <= current_week < we:
            return [entry]
    # Fallback: return last entry if we're past all weeks
    if entries:
        return [entries[-1]]
    return []


class KamerplanterPlantCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Coordinator for plant data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: KamerplanterApi) -> None:
        interval = entry.options.get(CONF_POLL_PLANTS, DEFAULT_POLL_PLANTS)
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_plants",
            update_interval=timedelta(seconds=interval),
            config_entry=entry,
        )
        self.api = api

    async def _async_update_data(self) -> list[dict[str, Any]]:
        try:
            plants = await self.api.async_get_plants()
            for plant in plants:
                if plant.get("removed_on"):
                    continue
                plan = await self.api.async_get_plant_nutrient_plan(plant["key"])
                plant["_nutrient_plan"] = plan
                # Fetch current dosages based on phase week
                started = plant.get("current_phase_started_at")
                if started and plan:
                    week = _calc_current_week(started)
                    dosages = await self.api.async_get_plant_current_dosages(
                        plant["key"], week
                    )
                    plant["_current_dosages"] = dosages
                    # Fetch active channels
                    try:
                        channels = await self.api.async_get_plant_active_channels(
                            plant["key"], week
                        )
                        plant["_active_channels"] = channels
                    except Exception:  # noqa: BLE001
                        plant["_active_channels"] = []
                # Fetch phase history for calendar
                try:
                    history = await self.api.async_get_plant_phase_history(
                        plant["key"]
                    )
                    plant["_phase_history"] = history
                except Exception:  # noqa: BLE001
                    plant["_phase_history"] = []
            return plants
        except KamerplanterAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except KamerplanterConnectionError as err:
            raise UpdateFailed(str(err)) from err


class KamerplanterLocationCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Coordinator for location data enriched with assigned runs/instances."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: KamerplanterApi) -> None:
        interval = entry.options.get(CONF_POLL_LOCATIONS, DEFAULT_POLL_LOCATIONS)
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_locations",
            update_interval=timedelta(seconds=interval),
            config_entry=entry,
        )
        self.api = api

    async def _async_update_data(self) -> list[dict[str, Any]]:
        try:
            locations = await self.api.async_get_all_locations()

            # Build fertilizer name lookup
            fert_lookup: dict[str, str] = {}
            try:
                fertilizers = await self.api.async_get_fertilizers()
                for f in fertilizers:
                    fert_lookup[f.get("key", "")] = f.get(
                        "product_name", f.get("name", "")
                    )
            except Exception:  # noqa: BLE001
                _LOGGER.debug("Could not fetch fertilizer names for location enrichment")

            for loc in locations:
                loc_key = loc.get("key") or loc.get("_key", "")
                if not loc_key:
                    continue
                # Fetch runs assigned to this location
                try:
                    runs = await self.api.async_get_runs_by_location(loc_key)
                except Exception:  # noqa: BLE001
                    runs = []
                active_runs = [
                    r for r in runs
                    if r.get("status") not in ("completed", "cancelled")
                ]
                loc["_active_runs"] = active_runs
                loc["_active_run_count"] = len(active_runs)

                # Derive plant count from active runs + slot-based instances
                run_plant_count = sum(
                    r.get("actual_quantity", 0) for r in active_runs
                )
                try:
                    slot_plants = await self.api.async_get_plant_instances_by_location(loc_key)
                except Exception:  # noqa: BLE001
                    slot_plants = []
                active_slot_plants = [p for p in slot_plants if not p.get("removed_on")]
                loc["_active_plants"] = active_slot_plants
                loc["_active_plant_count"] = max(run_plant_count, len(active_slot_plants))
                loc["_run_plant_count"] = run_plant_count
                _LOGGER.debug(
                    "Location %s: %d active runs, %d run_plants, %d slot_plants → count=%d",
                    loc_key, len(active_runs), run_plant_count,
                    len(active_slot_plants), loc["_active_plant_count"],
                )

                # Enrich primary run (first active) with timeline + nutrient plan
                primary = active_runs[0] if active_runs else None
                if primary:
                    run_key = primary.get("key", "")
                    plan = await self.api.async_get_run_nutrient_plan(run_key)
                    primary["_nutrient_plan"] = plan
                    if plan and plan.get("key"):
                        entries = await self.api.async_get_plan_phase_entries(
                            plan["key"]
                        )
                        for entry in entries:
                            for channel in entry.get("delivery_channels", []):
                                for dosage in channel.get("fertilizer_dosages", []):
                                    fk = dosage.get("fertilizer_key", "")
                                    if (
                                        fk
                                        and fk in fert_lookup
                                        and "product_name" not in dosage
                                    ):
                                        dosage["product_name"] = fert_lookup[fk]
                        primary["_phase_entries"] = entries
                    timeline = await self.api.async_get_run_phase_timeline(run_key)
                    primary["_timeline"] = timeline
                    # Calculate effective plan week and filter entries
                    all_entries = primary.get("_phase_entries", [])
                    eff_week = _calc_effective_plan_week(timeline, all_entries)
                    if eff_week is not None:
                        primary["_current_week"] = eff_week
                        primary["_current_phase_entries"] = _filter_current_phase_entries(
                            all_entries, eff_week
                        )
                    loc["_primary_run"] = primary

            # Enrich locations with tank data (latest fill)
            try:
                all_tanks = await self.api.async_get_tanks()
            except Exception:  # noqa: BLE001
                all_tanks = []
            tanks_by_loc: dict[str, list[dict[str, Any]]] = {}
            for tank in all_tanks:
                tlk = tank.get("location_key")
                if tlk:
                    tanks_by_loc.setdefault(tlk, []).append(tank)

            for loc in locations:
                loc_key = loc.get("key") or loc.get("_key", "")
                loc_tanks = tanks_by_loc.get(loc_key, [])
                for tank in loc_tanks:
                    tk = tank.get("key", "")
                    try:
                        latest = await self.api.async_get_tank_latest_fill(tk)
                        tank["_latest_fill"] = latest
                    except Exception:  # noqa: BLE001
                        tank["_latest_fill"] = None
                    try:
                        tank["_ha_sensors"] = await self.api.async_get_tank_sensors(tk)
                    except Exception:  # noqa: BLE001
                        tank["_ha_sensors"] = []
                loc["_tanks"] = loc_tanks

            return locations
        except KamerplanterAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except KamerplanterConnectionError as err:
            raise UpdateFailed(str(err)) from err


class KamerplanterAlertCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Coordinator for alerts (derived from overdue tasks)."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: KamerplanterApi) -> None:
        interval = entry.options.get(CONF_POLL_ALERTS, DEFAULT_POLL_ALERTS)
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_alerts",
            update_interval=timedelta(seconds=interval),
            config_entry=entry,
        )
        self.api = api

    async def _async_update_data(self) -> list[dict[str, Any]]:
        try:
            return await self.api.async_get_overdue_tasks()
        except KamerplanterAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except KamerplanterConnectionError as err:
            raise UpdateFailed(str(err)) from err


class KamerplanterRunCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Coordinator for planting run data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: KamerplanterApi) -> None:
        interval = entry.options.get(CONF_POLL_PLANTS, DEFAULT_POLL_PLANTS)
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_runs",
            update_interval=timedelta(seconds=interval),
            config_entry=entry,
        )
        self.api = api

    async def _async_update_data(self) -> list[dict[str, Any]]:
        try:
            runs = await self.api.async_get_planting_runs()
            # Build fertilizer name lookup (key → product_name)
            fert_lookup: dict[str, str] = {}
            needs_lookup = any(
                r.get("status") not in ("completed", "cancelled") for r in runs
            )
            if needs_lookup:
                try:
                    fertilizers = await self.api.async_get_fertilizers()
                    for f in fertilizers:
                        fert_lookup[f.get("key", "")] = f.get("product_name", f.get("name", ""))
                except Exception:  # noqa: BLE001
                    _LOGGER.debug("Could not fetch fertilizer names for lookup")

            for run in runs:
                if run.get("status") in ("completed", "cancelled"):
                    continue
                plan = await self.api.async_get_run_nutrient_plan(run["key"])
                run["_nutrient_plan"] = plan
                if plan and plan.get("key"):
                    entries = await self.api.async_get_plan_phase_entries(plan["key"])
                    # Enrich dosages with product_name from lookup
                    for entry in entries:
                        for channel in entry.get("delivery_channels", []):
                            for dosage in channel.get("fertilizer_dosages", []):
                                fk = dosage.get("fertilizer_key", "")
                                if fk and fk in fert_lookup and "product_name" not in dosage:
                                    dosage["product_name"] = fert_lookup[fk]
                    run["_phase_entries"] = entries
                # Fetch phase timeline
                timeline = await self.api.async_get_run_phase_timeline(run["key"])
                run["_timeline"] = timeline
                # Calculate effective plan week and filter entries
                all_entries = run.get("_phase_entries", [])
                eff_week = _calc_effective_plan_week(timeline, all_entries)
                if eff_week is not None:
                    run["_current_week"] = eff_week
                    run["_current_phase_entries"] = _filter_current_phase_entries(
                        all_entries, eff_week
                    )
                # Fetch active channels
                try:
                    channels = await self.api.async_get_run_active_channels(
                        run["key"], eff_week
                    )
                    run["_active_channels"] = channels
                except Exception:  # noqa: BLE001
                    run["_active_channels"] = []
            return runs
        except KamerplanterAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except KamerplanterConnectionError as err:
            raise UpdateFailed(str(err)) from err


class KamerplanterTaskCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Coordinator for pending tasks."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: KamerplanterApi) -> None:
        interval = entry.options.get(CONF_POLL_TASKS, DEFAULT_POLL_TASKS)
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_tasks",
            update_interval=timedelta(seconds=interval),
            config_entry=entry,
        )
        self.api = api

    async def _async_update_data(self) -> list[dict[str, Any]]:
        try:
            return await self.api.async_get_pending_tasks()
        except KamerplanterAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except KamerplanterConnectionError as err:
            raise UpdateFailed(str(err)) from err
