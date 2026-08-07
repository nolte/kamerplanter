"""REQ-033 §2.1 — the aggregated diagnostic snapshot (``get_plant_diagnostics``).

§2.1 specifies this as "Aggregierter Diagnose-Snapshot fuer eine Pflanze:
Sensorwerte, EC/pH-Trend, IPM-Inspections, Karenz, juengste Tips", and AC-5
requires it to answer in **one** call rather than five round-trips.

The load-bearing part is the **trend**, not the snapshot. A single EC reading
cannot distinguish a rising salt load from a stable one, and the direction of
drift is exactly what separates "correct and holding" from "heading for
oversupply". So every series here is returned with its samples *and* a derived
``first``/``latest``/``delta``/``direction``, computed once here instead of being
re-derived differently by every recipe.

**Where the numbers come from, and why they are kept apart.** Feeding events
carry three distinct EC/pH readings and conflating them would be a wrong answer,
not a rounded one:

* ``input`` — ``measured_ec_before`` / ``measured_ph_before``: the solution that
  went in. This is the supply side of REQ-050's evidence ladder, tier 2.
* ``after`` — ``measured_ec_after`` / ``measured_ph_after``: the same solution
  measured again after the feed.
* ``runoff`` — ``runoff_ec`` / ``runoff_ph``: what came back out of the pot. A
  runoff EC above the input EC is accumulation in the substrate; reading it as a
  tank value inverts the conclusion.

The open ``measurements`` object on a diary entry could not tell these apart at
all, which is the open question §2 left standing. It is answered here.

**Tenant binding.** Every read below is bound to the acting tenant, in one of two
ways. ``feeding_service.get_by_plant`` and ``observation_service`` take
``tenant_key`` in the query itself (#927/#947). The IPM history and the Karenz
periods have no tenant predicate of their own, so the plant is resolved against
the tenant *first* and only its ``_key`` — never a caller-supplied one — reaches
them: the same fetch-then-use guard ``get_plant_inspections`` and
``get_plant_care_log`` already apply. Sensors are likewise reached through the
resolved plant's own ``location_key``, and the readings themselves are filtered
on ``tenant_key`` in TimescaleDB.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from pydantic import Field

from app.common.datetimes import ensure_aware_utc, now_utc
from app.common.enums import McpPermission
from app.common.exceptions import KamerplanterError
from app.domain.models.mcp import McpToolResponse
from app.mcp_server.base import TenantToolInput, ToolBase, mcp_tool
from app.mcp_server.context import ToolContext

#: Default observation window. Two weeks spans several feedings on any realistic
#: schedule, which is the minimum for a drift statement to mean anything.
DEFAULT_WINDOW_DAYS = 14

#: Ceiling on the window. Beyond a season the "trend" stops describing the
#: current phase and starts averaging over phase changes that legitimately move
#: the EC target — a number that looks like drift and is not.
MAX_WINDOW_DAYS = 365

#: Feeding events read before the window filter is applied. The repository has no
#: date predicate, so filtering inside a page would report "no feedings" for a
#: plant whose page-1 rows happen to be older than the window.
_FEEDING_SCAN_LIMIT = 200

#: Rows returned per collection. The answer is read by a language model; a longer
#: list is a worse answer, not a more complete one.
_MAX_ITEMS = 50

#: An EC/pH change smaller than this is noise from the meter, not drift. Applied
#: per series so ``direction`` never claims a trend a probe cannot resolve.
_EC_STABLE_BAND = 0.1
_PH_STABLE_BAND = 0.1

#: Sensor metric types that carry an EC or a pH. Anything else at the location is
#: reported in the snapshot but stays out of the EC/pH trend.
_EC_METRIC_TYPES = frozenset({"ec_ms", "ec", "ec_ms_cm"})
_PH_METRIC_TYPES = frozenset({"ph"})


def _iso(value: Any) -> str | None:
    """Render a timestamp as ISO-8601 UTC, or ``None``."""

    moment = ensure_aware_utc(value)
    return moment.isoformat() if moment is not None else None


def _series(samples: list[tuple[datetime, float]], *, stable_band: float) -> dict[str, Any]:
    """Turn timestamped samples into the trend shape every series shares.

    ``samples`` arrive newest-first (the repositories sort that way) and are
    re-sorted oldest-first here, because a delta is only readable as
    "later minus earlier". ``direction`` is ``stable`` inside ``stable_band``:
    below that the change is meter noise, and reporting it as ``rising`` would
    manufacture a trend out of the third decimal place.

    Every key is always present — an empty series answers with ``null`` values
    and ``sample_count: 0`` rather than an omitted object, so a recipe can read
    it unconditionally.
    """

    ordered = sorted(samples, key=lambda pair: pair[0])
    if not ordered:
        return {
            "sample_count": 0,
            "first": None,
            "first_at": None,
            "latest": None,
            "latest_at": None,
            "delta": None,
            "direction": "unknown",
            "samples": [],
        }

    first_at, first_value = ordered[0]
    latest_at, latest_value = ordered[-1]
    delta = round(latest_value - first_value, 4)
    within_noise = len(ordered) < 2 or abs(delta) < stable_band
    direction = "stable" if within_noise else ("rising" if delta > 0 else "falling")
    return {
        "sample_count": len(ordered),
        "first": first_value,
        "first_at": _iso(first_at),
        "latest": latest_value,
        "latest_at": _iso(latest_at),
        "delta": delta,
        "direction": direction,
        # Newest first, matching every other list in the palette.
        "samples": [{"at": _iso(at), "value": value} for at, value in reversed(ordered[-_MAX_ITEMS:])],
    }


def _in_window(value: Any, cutoff: datetime) -> bool:
    moment = ensure_aware_utc(value)
    # A record with no timestamp is kept: dropping it would silently shorten the
    # history, and the repositories default the stamp on write so this is rare.
    return moment is None or moment >= cutoff


@mcp_tool(name="get_plant_diagnostics", permission=McpPermission.READ)
class GetPlantDiagnostics(ToolBase):
    """One plant's diagnostic snapshot: EC/pH trend, sensors, IPM, Karenz, care — in one call."""

    class Input(TenantToolInput):
        plant_key: str = Field(description="Key of the plant to diagnose. Resolve it with list_plants.")
        window_days: int = Field(
            default=DEFAULT_WINDOW_DAYS,
            ge=1,
            le=MAX_WINDOW_DAYS,
            description=(
                "How far back the EC/pH trend and the event histories reach, in days. "
                "The trend needs several feedings to mean anything — the default of 14 days "
                "spans them on a typical schedule."
            ),
        )
        include_sensors: bool = Field(
            default=True,
            description="Also read the latest value of every sensor at the plant's location.",
        )

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        # SEC-001: the plant is resolved against the acting tenant before anything
        # else, and only its resolved key reaches the reads that carry no tenant
        # predicate of their own (IPM history, Karenz).
        plant = ctx.plant_service.get_plant(args.plant_key, tenant_key=ctx.tenant_key)
        now = now_utc()
        cutoff = now - timedelta(days=args.window_days)

        feedings = self._feedings(ctx, plant.key, cutoff)
        sensors = self._sensors(ctx, plant, cutoff) if args.include_sensors else None
        trend = self._trend(feedings, sensors)
        inspections = self._inspections(ctx, plant.key, cutoff)
        karenz = self._karenz(ctx, plant.key)
        care = self._care(ctx, plant.key, cutoff)

        name = plant.plant_name or plant.instance_id
        data: dict[str, Any] = {
            "plant": {
                "plant_key": plant.key,
                "plant_name": plant.plant_name,
                "instance_id": plant.instance_id,
                "species_key": plant.species_key,
                "cultivar_key": plant.cultivar_key,
                "location_key": plant.location_key,
                "substrate_key": plant.substrate_key,
                "current_phase_key": plant.current_phase_key,
            },
            "window": {"days": args.window_days, "from": _iso(cutoff), "to": _iso(now)},
            "ec_ph_trend": trend,
            "feeding_events": [self._feeding_payload(event) for event in feedings[:_MAX_ITEMS]],
            "sensors": sensors if sensors is not None else {"available": False, "reason": "not_requested", "items": []},
            "inspections": inspections,
            "karenz": karenz,
            "care_events": care,
        }
        return self._response(
            summary=self._summary(name, trend, karenz, inspections),
            data=data,
            links=[
                ctx.api_link(f"/feeding-events/plant/{plant.key}"),
                ctx.ui_link(f"/plants/{plant.key}"),
            ],
        )

    # ── collectors ───────────────────────────────────────────────────────
    @staticmethod
    def _feedings(ctx: ToolContext, plant_key: str, cutoff: datetime) -> list[Any]:
        """The plant's fertigation records inside the window, newest first.

        ``get_by_plant`` takes ``tenant_key`` keyword-only and without a default
        (#927), so the tenant predicate is in the query rather than in this call
        site's memory. The window filter runs here because the repository has no
        date predicate — and over the whole scan, not one page, for the reason
        ``_FEEDING_SCAN_LIMIT`` documents.
        """

        events = ctx.feeding_service.get_by_plant(
            plant_key,
            0,
            _FEEDING_SCAN_LIMIT,
            tenant_key=ctx.tenant_key,
        )
        return [event for event in events if _in_window(event.timestamp, cutoff)]

    @staticmethod
    def _sensors(ctx: ToolContext, plant: Any, cutoff: datetime) -> dict[str, Any]:
        """Latest value per sensor at the plant's own location.

        Sensors carry no tenant of their own; the binding is the plant's
        ``location_key``, which came off a plant already resolved against the
        acting tenant, and the readings query filters on ``tenant_key`` in
        TimescaleDB. A missing time-series backend is reported as
        ``available: false`` and never as "no readings" — those are different
        answers and a recipe must be able to tell them apart.
        """

        location_key = getattr(plant, "location_key", None)
        if not location_key:
            return {"available": False, "reason": "plant_has_no_location", "items": []}

        try:
            sensors = ctx.sensor_service.get_sensors_for_location(location_key)
        except KamerplanterError:
            return {"available": False, "reason": "sensor_lookup_failed", "items": []}

        observations = ctx.observation_service
        if not observations.is_available():
            return {
                "available": False,
                "reason": "timeseries_unavailable",
                "sensor_count": len(sensors),
                "items": [],
            }

        items: list[dict[str, Any]] = []
        for sensor in sensors[:_MAX_ITEMS]:
            reading = observations.get_latest_reading(sensor.key, ctx.tenant_key)
            items.append(
                {
                    "sensor_key": sensor.key,
                    "name": sensor.name,
                    "metric_type": sensor.metric_type,
                    "unit": sensor.unit_of_measurement,
                    "value": getattr(reading, "value", None),
                    "at": _iso(getattr(reading, "time", None)),
                    "source": getattr(reading, "source", None),
                    # A stale reading is worse than none if it is read as current.
                    "in_window": bool(reading is not None and _in_window(reading.time, cutoff)),
                }
            )
        return {"available": True, "location_key": location_key, "sensor_count": len(sensors), "items": items}

    @staticmethod
    def _trend(feedings: list[Any], sensors: dict[str, Any] | None) -> dict[str, Any]:
        """Six series: EC and pH, each as input / after / runoff, plus the sensor line."""

        def collect(ec_field: str) -> list[tuple[datetime, float]]:
            out: list[tuple[datetime, float]] = []
            for event in feedings:
                value = getattr(event, ec_field, None)
                stamp = ensure_aware_utc(event.timestamp)
                if value is not None and stamp is not None:
                    out.append((stamp, float(value)))
            return out

        def sensor_series(metric_types: frozenset[str]) -> list[tuple[datetime, float]]:
            if not sensors or not sensors.get("available"):
                return []
            out: list[tuple[datetime, float]] = []
            for item in sensors.get("items", []):
                if str(item.get("metric_type") or "").lower() not in metric_types:
                    continue
                stamp = ensure_aware_utc(item.get("at"))
                if item.get("value") is not None and stamp is not None:
                    out.append((stamp, float(item["value"])))
            return out

        return {
            "ec": {
                "unit": "mS/cm",
                "input": _series(collect("measured_ec_before"), stable_band=_EC_STABLE_BAND),
                "after": _series(collect("measured_ec_after"), stable_band=_EC_STABLE_BAND),
                "runoff": _series(collect("runoff_ec"), stable_band=_EC_STABLE_BAND),
                "sensor": _series(sensor_series(_EC_METRIC_TYPES), stable_band=_EC_STABLE_BAND),
            },
            "ph": {
                "unit": "pH",
                "input": _series(collect("measured_ph_before"), stable_band=_PH_STABLE_BAND),
                "after": _series(collect("measured_ph_after"), stable_band=_PH_STABLE_BAND),
                "runoff": _series(collect("runoff_ph"), stable_band=_PH_STABLE_BAND),
                "sensor": _series(sensor_series(_PH_METRIC_TYPES), stable_band=_PH_STABLE_BAND),
            },
        }

    @staticmethod
    def _feeding_payload(event: Any) -> dict[str, Any]:
        return {
            "feeding_event_key": event.key,
            "timestamp": _iso(event.timestamp),
            "application_method": str(event.application_method),
            "is_supplemental": event.is_supplemental,
            "volume_applied_liters": event.volume_applied_liters,
            "fertilizers_used": [
                {"fertilizer_key": f.fertilizer_key, "ml_applied": f.ml_applied} for f in event.fertilizers_used
            ],
            "measured_ec_before": event.measured_ec_before,
            "measured_ec_after": event.measured_ec_after,
            "measured_ph_before": event.measured_ph_before,
            "measured_ph_after": event.measured_ph_after,
            "runoff_ec": event.runoff_ec,
            "runoff_ph": event.runoff_ph,
            "runoff_volume_liters": event.runoff_volume_liters,
            "tank_fill_event_key": event.tank_fill_event_key,
            "notes": event.notes,
        }

    @staticmethod
    def _inspections(ctx: ToolContext, plant_key: str, cutoff: datetime) -> list[dict[str, Any]]:
        inspections, _total = ctx.ipm_service.get_inspections(plant_key, offset=0, limit=_MAX_ITEMS)
        return [
            {
                "inspected_at": _iso(i.inspected_at),
                "pressure_level": str(i.pressure_level),
                "detected_pest_keys": list(i.detected_pest_keys),
                "detected_disease_keys": list(i.detected_disease_keys),
                "symptoms_observed": list(i.symptoms_observed),
                "findings": [
                    {
                        "symptom": f.symptom,
                        "confidence": f.confidence,
                        "affected_plant_part": str(f.affected_plant_part) if f.affected_plant_part else None,
                        "pest_key": f.pest_key,
                        "disease_key": f.disease_key,
                        "rationale": f.rationale,
                    }
                    for f in getattr(i, "findings", [])
                ],
                "notes": i.notes,
            }
            for i in inspections
            if _in_window(i.inspected_at, cutoff)
        ]

    @staticmethod
    def _karenz(ctx: ToolContext, plant_key: str) -> dict[str, Any]:
        """Active safety intervals — deliberately **not** windowed.

        A Karenz that started before the window is still in force, and hiding it
        because the treatment was applied a month ago would turn the harvest gate
        into a function of how the caller happened to size ``window_days``.
        """

        can_harvest, blockers = ctx.ipm_service.check_harvest_safety(plant_key)
        return {
            "harvest_allowed": bool(can_harvest),
            "active_periods": [
                {
                    "treatment_name": period.get("treatment_name"),
                    "active_ingredient": period.get("active_ingredient"),
                    "applied_at": period.get("applied_at"),
                    "safety_interval_days": period.get("safety_interval_days"),
                    "safe_date": period.get("safe_date"),
                }
                for period in (blockers or [])
            ],
        }

    @staticmethod
    def _care(ctx: ToolContext, plant_key: str, cutoff: datetime) -> list[dict[str, Any]]:
        entries = ctx.care_service.get_confirmation_history(plant_key, None, limit=_MAX_ITEMS)
        return [
            {
                "confirmed_at": _iso(e.confirmed_at),
                "reminder_type": str(e.reminder_type),
                "action": e.action,
                "notes": e.notes,
            }
            for e in entries
            if _in_window(e.confirmed_at, cutoff)
        ]

    @staticmethod
    def _summary(
        name: str,
        trend: dict[str, Any],
        karenz: dict[str, Any],
        inspections: list[dict[str, Any]],
    ) -> str:
        """One line a model may act on without reading ``data``.

        The Karenz belongs here for the same reason ``get_treatment`` puts it in
        its summary: advice to harvest inside a safety interval is unsafe advice,
        and a model that only reads the summary must still see the gate.
        """

        ec_input = trend["ec"]["input"]
        ph_input = trend["ph"]["input"]
        parts = [f"Diagnostics for '{name}'."]
        if ec_input["sample_count"]:
            parts.append(f"Input EC {ec_input['direction']} at {ec_input['latest']} mS/cm.")
        runoff = trend["ec"]["runoff"]
        if runoff["sample_count"]:
            parts.append(f"Runoff EC {runoff['direction']} at {runoff['latest']} mS/cm.")
        if ph_input["sample_count"]:
            parts.append(f"Input pH {ph_input['direction']} at {ph_input['latest']}.")
        if not ec_input["sample_count"] and not runoff["sample_count"]:
            parts.append("No EC measurements recorded in this window.")
        if inspections:
            parts.append(f"{len(inspections)} IPM inspections.")
        if not karenz["harvest_allowed"]:
            parts.append(f"Harvest BLOCKED by {len(karenz['active_periods'])} active Karenz period(s).")
        return " ".join(parts)


__all__ = ["DEFAULT_WINDOW_DAYS", "MAX_WINDOW_DAYS", "GetPlantDiagnostics"]
