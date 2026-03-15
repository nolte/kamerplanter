from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from app.common.enums import (
    FillType,
    IrrigationSystem,
    MaintenancePriority,
    MaintenanceStatus,
    MaintenanceType,
    TankType,
)

if TYPE_CHECKING:
    from app.domain.models.tank import MaintenanceLog, MaintenanceSchedule, Tank, TankFillEvent, TankState

# ── Tank-type-specific alert thresholds ──────────────────────────────

PH_RANGES: dict[TankType, tuple[float, float]] = {
    TankType.NUTRIENT: (5.5, 6.5),
    TankType.RECIRCULATION: (5.5, 6.3),
    TankType.IRRIGATION: (5.8, 6.8),
    TankType.RESERVOIR: (5.0, 8.0),
    TankType.STOCK_SOLUTION: (1.0, 14.0),
}

TEMP_THRESHOLDS: dict[TankType, dict[str, float]] = {
    TankType.NUTRIENT: {"warm_warn": 22, "warm_crit": 26, "cold_warn": 15, "cold_crit": 10},
    TankType.RECIRCULATION: {"warm_warn": 22, "warm_crit": 25, "cold_warn": 16, "cold_crit": 12},
    TankType.IRRIGATION: {"warm_warn": 28, "warm_crit": 35, "cold_warn": 10, "cold_crit": 5},
    TankType.RESERVOIR: {"warm_warn": 30, "warm_crit": 40, "cold_warn": 5, "cold_crit": 1},
    TankType.STOCK_SOLUTION: {"warm_warn": 30, "warm_crit": 40, "cold_warn": 5, "cold_crit": 1},
}

EC_MAX: dict[TankType, float] = {
    TankType.NUTRIENT: 3.0,
    TankType.RECIRCULATION: 3.0,
    TankType.IRRIGATION: 1.5,
    TankType.STOCK_SOLUTION: 250.0,
    # RESERVOIR intentionally omitted — no EC limit for plain water storage
}

# pH drift thresholds per tank type
PH_DRIFT_THRESHOLD: dict[TankType, float] = {
    TankType.RECIRCULATION: 0.3,
}
PH_DRIFT_DEFAULT = 0.5

# Solution age base days at 20°C reference temperature
SOLUTION_AGE_BASE_DAYS: dict[str, float] = {
    "organic": 5.0,
    "mineral": 10.0,
}
SOLUTION_AGE_REF_TEMP = 20.0
SOLUTION_AGE_Q10 = 2.0

FILL_LEVEL_LOW_PERCENT = 20.0

# Hydro-type irrigation systems that allow recirculation tanks
HYDRO_SYSTEMS = {IrrigationSystem.HYDRO, IrrigationSystem.NFT, IrrigationSystem.EBB_FLOW}

DEFAULT_MAINTENANCE_SCHEDULES: dict[TankType, list[dict]] = {
    TankType.NUTRIENT: [
        {"type": MaintenanceType.WATER_CHANGE, "interval_days": 7, "priority": MaintenancePriority.HIGH},
        {"type": MaintenanceType.CLEANING, "interval_days": 30, "priority": MaintenancePriority.MEDIUM},
        {"type": MaintenanceType.SANITIZATION, "interval_days": 90, "priority": MaintenancePriority.HIGH},
        {"type": MaintenanceType.CALIBRATION, "interval_days": 14, "priority": MaintenancePriority.MEDIUM},
        {"type": MaintenanceType.PUMP_INSPECTION, "interval_days": 30, "priority": MaintenancePriority.LOW},
    ],
    TankType.IRRIGATION: [
        {"type": MaintenanceType.WATER_CHANGE, "interval_days": 14, "priority": MaintenancePriority.MEDIUM},
        {"type": MaintenanceType.CLEANING, "interval_days": 60, "priority": MaintenancePriority.MEDIUM},
        {"type": MaintenanceType.SANITIZATION, "interval_days": 90, "priority": MaintenancePriority.MEDIUM},
        {"type": MaintenanceType.FILTER_CHANGE, "interval_days": 90, "priority": MaintenancePriority.MEDIUM},
    ],
    TankType.RESERVOIR: [
        {"type": MaintenanceType.CLEANING, "interval_days": 90, "priority": MaintenancePriority.LOW},
        {"type": MaintenanceType.SANITIZATION, "interval_days": 180, "priority": MaintenancePriority.LOW},
        {"type": MaintenanceType.FILTER_CHANGE, "interval_days": 60, "priority": MaintenancePriority.MEDIUM},
    ],
    TankType.RECIRCULATION: [
        {"type": MaintenanceType.WATER_CHANGE, "interval_days": 7, "priority": MaintenancePriority.CRITICAL},
        {"type": MaintenanceType.CLEANING, "interval_days": 14, "priority": MaintenancePriority.HIGH},
        {"type": MaintenanceType.SANITIZATION, "interval_days": 60, "priority": MaintenancePriority.HIGH},
        {"type": MaintenanceType.CALIBRATION, "interval_days": 14, "priority": MaintenancePriority.HIGH},
        {"type": MaintenanceType.PUMP_INSPECTION, "interval_days": 14, "priority": MaintenancePriority.MEDIUM},
        {"type": MaintenanceType.FILTER_CHANGE, "interval_days": 30, "priority": MaintenancePriority.HIGH},
    ],
    TankType.STOCK_SOLUTION: [
        {"type": MaintenanceType.CLEANING, "interval_days": 90, "priority": MaintenancePriority.MEDIUM},
        {"type": MaintenanceType.CALIBRATION, "interval_days": 28, "priority": MaintenancePriority.LOW},
    ],
}


class TankEngine:
    """Pure logic for tank operations — no DB access."""

    def check_alerts(
        self,
        tank: Tank,
        state: TankState,
        last_fill_event: TankFillEvent | None = None,
        target_ec_ms: float | None = None,
    ) -> list[dict]:
        """Check a tank state for alert conditions. Returns list of alert dicts.

        Args:
            tank: The tank definition.
            state: Current tank state readings.
            last_fill_event: Most recent full_change fill event (for drift/age alerts).
            target_ec_ms: EC target from nutrient plan (for plan-relative EC alerts).
        """
        alerts: list[dict] = []
        tt = tank.tank_type

        # ── pH range alerts (tank-type-specific) ──────────────────────
        if state.ph is not None:
            ph_min, ph_max = PH_RANGES.get(tt, (5.0, 7.0))
            if state.ph < ph_min:
                severity = "critical" if state.ph < ph_min - 0.5 else "high"
                alerts.append(
                    {
                        "type": "ph_out_of_range",
                        "severity": severity,
                        "message": f"pH {state.ph:.1f} below range [{ph_min}–{ph_max}] for {tt.value}",
                        "value": state.ph,
                    }
                )
            elif state.ph > ph_max:
                severity = "critical" if state.ph > ph_max + 0.5 else "high"
                alerts.append(
                    {
                        "type": "ph_out_of_range",
                        "severity": severity,
                        "message": f"pH {state.ph:.1f} above range [{ph_min}–{ph_max}] for {tt.value}",
                        "value": state.ph,
                    }
                )

        # ── pH drift (vs last fill) ──────────────────────────────────
        if state.ph is not None and last_fill_event is not None and last_fill_event.measured_ph is not None:
            drift = abs(state.ph - last_fill_event.measured_ph)
            threshold = PH_DRIFT_THRESHOLD.get(tt, PH_DRIFT_DEFAULT)
            if drift > threshold:
                severity = "high" if drift > threshold * 2 else "medium"
                alerts.append(
                    {
                        "type": "ph_drift",
                        "severity": severity,
                        "message": (
                            f"pH drift {drift:.2f} since last fill "
                            f"(was {last_fill_event.measured_ph:.1f}, now {state.ph:.1f})"
                        ),
                        "value": drift,
                    }
                )

        # ── EC alerts (absolute + plan-relative) ─────────────────────
        if state.ec_ms is not None:
            ec_limit = EC_MAX.get(tt)
            if ec_limit is not None and state.ec_ms > ec_limit:
                alerts.append(
                    {
                        "type": "ec_high",
                        "severity": "high",
                        "message": f"EC {state.ec_ms:.1f} mS exceeds limit {ec_limit} for {tt.value}",
                        "value": state.ec_ms,
                    }
                )

            if target_ec_ms is not None and target_ec_ms > 0:
                deviation_pct = abs(state.ec_ms - target_ec_ms) / target_ec_ms * 100
                if deviation_pct > 30:
                    alerts.append(
                        {
                            "type": "ec_deviation_alarm",
                            "severity": "high",
                            "message": (
                                f"EC {state.ec_ms:.1f} deviates {deviation_pct:.0f}% from target {target_ec_ms:.1f}"
                            ),
                            "value": state.ec_ms,
                        }
                    )
                elif deviation_pct > 20:
                    alerts.append(
                        {
                            "type": "ec_deviation_warning",
                            "severity": "medium",
                            "message": (
                                f"EC {state.ec_ms:.1f} deviates {deviation_pct:.0f}% from target {target_ec_ms:.1f}"
                            ),
                            "value": state.ec_ms,
                        }
                    )

        # ── Temperature alerts (tank-type-specific) ──────────────────
        if state.water_temp_celsius is not None:
            temp = state.water_temp_celsius
            thresholds = TEMP_THRESHOLDS.get(tt, TEMP_THRESHOLDS[TankType.RESERVOIR])

            if temp >= thresholds["warm_crit"]:
                alerts.append(
                    {
                        "type": "temperature_warm_critical",
                        "severity": "critical",
                        "message": f"Water temp {temp:.1f}°C — critical for {tt.value}",
                        "value": temp,
                    }
                )
            elif temp >= thresholds["warm_warn"]:
                alerts.append(
                    {
                        "type": "temperature_warm_warning",
                        "severity": "medium",
                        "message": f"Water temp {temp:.1f}°C — warm for {tt.value}",
                        "value": temp,
                    }
                )

            if temp <= thresholds["cold_crit"]:
                alerts.append(
                    {
                        "type": "temperature_cold_critical",
                        "severity": "critical",
                        "message": f"Water temp {temp:.1f}°C — critically cold for {tt.value}",
                        "value": temp,
                    }
                )
            elif temp <= thresholds["cold_warn"]:
                alerts.append(
                    {
                        "type": "temperature_cold_warning",
                        "severity": "medium",
                        "message": f"Water temp {temp:.1f}°C — cold for {tt.value}",
                        "value": temp,
                    }
                )

        # ── Dissolved Oxygen alerts ──────────────────────────────────
        if state.dissolved_oxygen_mgl is not None and tt in (TankType.NUTRIENT, TankType.RECIRCULATION):
            do = state.dissolved_oxygen_mgl
            if do < 4:
                alerts.append(
                    {
                        "type": "do_critical",
                        "severity": "critical",
                        "message": f"Dissolved oxygen {do:.1f} mg/L — critically low",
                        "value": do,
                    }
                )
            elif do < 6:
                alerts.append(
                    {
                        "type": "do_suboptimal",
                        "severity": "medium",
                        "message": f"Dissolved oxygen {do:.1f} mg/L — suboptimal",
                        "value": do,
                    }
                )

        # ── Compound: temp + DO ──────────────────────────────────────
        if (
            state.water_temp_celsius is not None
            and state.dissolved_oxygen_mgl is not None
            and tt in (TankType.NUTRIENT, TankType.RECIRCULATION)
            and state.water_temp_celsius > 22
            and state.dissolved_oxygen_mgl < 6
        ):
            alerts.append(
                {
                    "type": "compound_temp_do",
                    "severity": "critical",
                    "message": (
                        f"Warm water ({state.water_temp_celsius:.1f}°C) + low DO "
                        f"({state.dissolved_oxygen_mgl:.1f} mg/L) — root rot risk"
                    ),
                    "value": state.water_temp_celsius,
                }
            )

        # ── ORP alerts (recirculation with UV/ozone only) ────────────
        if (
            state.orp_mv is not None
            and tt == TankType.RECIRCULATION
            and (tank.has_uv_sterilizer or tank.has_ozone_generator)
        ):
            if state.orp_mv < 250:
                alerts.append(
                    {
                        "type": "orp_pathogen_risk",
                        "severity": "critical",
                        "message": f"ORP {state.orp_mv} mV — pathogen risk (< 250 mV)",
                        "value": state.orp_mv,
                    }
                )
            elif state.orp_mv < 650:
                alerts.append(
                    {
                        "type": "orp_sterilization_low",
                        "severity": "medium",
                        "message": f"ORP {state.orp_mv} mV — sterilization suboptimal (< 650 mV)",
                        "value": state.orp_mv,
                    }
                )

        # ── Fill level ───────────────────────────────────────────────
        if state.fill_level_percent is not None and state.fill_level_percent < FILL_LEVEL_LOW_PERCENT:
            alerts.append(
                {
                    "type": "fill_level_low",
                    "severity": "medium",
                    "message": f"Fill level {state.fill_level_percent:.0f}% — refill needed",
                    "value": state.fill_level_percent,
                }
            )

        # ── Algae risk (multi-factor) ────────────────────────────────
        alerts.extend(self._check_algae_risk(tank, state))

        # ── Solution age (Q10-corrected) ─────────────────────────────
        if last_fill_event is not None:
            alerts.extend(self._check_solution_age(tank, state, last_fill_event))

        # ── Chlorine/chloramine from last fill ───────────────────────
        if last_fill_event is not None:
            alerts.extend(self._check_water_chemistry(last_fill_event))

        # ── Biofilm risk (recirculation) ─────────────────────────────
        if last_fill_event is not None:
            alerts.extend(self._check_biofilm_risk(tank, state, last_fill_event))

        return alerts

    def _check_algae_risk(self, tank: Tank, state: TankState) -> list[dict]:
        """Multi-factor algae risk: is_light_proof (primary), temp, lid, nutrient type."""
        if tank.is_light_proof:
            return []

        risk_factors = 0
        if not tank.has_lid:
            risk_factors += 1
        if state.water_temp_celsius is not None and state.water_temp_celsius > 22:
            risk_factors += 1
        if tank.tank_type in (TankType.NUTRIENT, TankType.RECIRCULATION):
            risk_factors += 1

        if risk_factors >= 2:
            severity = "high" if risk_factors >= 3 else "medium"
            return [
                {
                    "type": "algae_risk",
                    "severity": severity,
                    "message": (
                        f"Algae risk ({risk_factors} factors: not light-proof, "
                        f"{'no lid, ' if not tank.has_lid else ''}"
                        f"{'warm water, ' if state.water_temp_celsius and state.water_temp_celsius > 22 else ''}"
                        f"{'nutrient-rich' if tank.tank_type in (TankType.NUTRIENT, TankType.RECIRCULATION) else ''})"
                    ),
                    "value": risk_factors,
                }
            ]
        return []

    def _check_solution_age(
        self,
        tank: Tank,
        state: TankState,
        last_fill: TankFillEvent,
    ) -> list[dict]:
        """Q10-corrected solution age alert."""
        if last_fill.filled_at is None:
            return []
        if tank.tank_type not in (TankType.NUTRIENT, TankType.RECIRCULATION):
            return []

        from datetime import UTC

        now = datetime.now(UTC)
        age_days = (now - last_fill.filled_at).total_seconds() / 86400

        kind = "organic" if last_fill.is_organic_fertilizers else "mineral"
        base_days = SOLUTION_AGE_BASE_DAYS[kind]

        # Q10 temperature correction: halve shelf life per 10°C above reference
        avg_temp = state.water_temp_celsius if state.water_temp_celsius is not None else SOLUTION_AGE_REF_TEMP
        q10_factor = SOLUTION_AGE_Q10 ** ((avg_temp - SOLUTION_AGE_REF_TEMP) / 10.0)
        adjusted_max = base_days / q10_factor

        if age_days > adjusted_max:
            severity = "high" if age_days > adjusted_max * 1.5 else "medium"
            return [
                {
                    "type": "solution_age",
                    "severity": severity,
                    "message": (
                        f"Solution age {age_days:.1f}d exceeds {kind} limit "
                        f"{adjusted_max:.1f}d (Q10-adjusted at {avg_temp:.0f}°C)"
                    ),
                    "value": age_days,
                }
            ]
        return []

    def _check_water_chemistry(self, last_fill: TankFillEvent) -> list[dict]:
        """Chlorine/chloramine alerts from last fill event."""
        alerts: list[dict] = []
        if last_fill.chlorine_ppm is not None and last_fill.chlorine_ppm > 0.5 and last_fill.is_organic_fertilizers:
            alerts.append(
                {
                    "type": "chlorine_warning",
                    "severity": "medium",
                    "message": (
                        f"Chlorine {last_fill.chlorine_ppm:.1f} ppm with biological additives — may harm microbes"
                    ),
                    "value": last_fill.chlorine_ppm,
                }
            )
        if last_fill.chloramine_ppm is not None and last_fill.chloramine_ppm > 0.5:
            alerts.append(
                {
                    "type": "chloramine_warning",
                    "severity": "high",
                    "message": (
                        f"Chloramine {last_fill.chloramine_ppm:.1f} ppm — "
                        "requires activated carbon or ascorbic acid treatment"
                    ),
                    "value": last_fill.chloramine_ppm,
                }
            )
        return alerts

    def _check_biofilm_risk(
        self,
        tank: Tank,
        state: TankState,
        last_fill: TankFillEvent,
    ) -> list[dict]:
        """Biofilm risk for recirculation tanks."""
        if tank.tank_type != TankType.RECIRCULATION:
            return []
        if tank.has_uv_sterilizer or tank.has_ozone_generator:
            return []
        if not last_fill.is_organic_fertilizers:
            return []
        if state.water_temp_celsius is None or state.water_temp_celsius <= 22:
            return []
        if last_fill.filled_at is None:
            return []

        from datetime import UTC

        age_days = (datetime.now(UTC) - last_fill.filled_at).total_seconds() / 86400
        if age_days <= 3:
            return []

        return [
            {
                "type": "biofilm_risk",
                "severity": "medium",
                "message": (
                    f"Biofilm risk: recirculation, warm ({state.water_temp_celsius:.0f}°C), "
                    f"organic, no UV/ozone, age {age_days:.0f}d"
                ),
                "value": age_days,
            }
        ]

    def calculate_next_maintenance(
        self,
        schedule: MaintenanceSchedule,
        last_log: MaintenanceLog | None,
        now: datetime | None = None,
    ) -> dict:
        """Calculate next due date and status for a maintenance schedule."""
        if now is None:
            from datetime import UTC

            now = datetime.now(UTC)

        if last_log and last_log.performed_at:
            next_due = last_log.performed_at + timedelta(days=schedule.interval_days)
        else:
            # No maintenance ever performed — due now
            next_due = now

        days_until = (next_due - now).total_seconds() / 86400

        if days_until < 0:
            status = MaintenanceStatus.OVERDUE
        elif days_until <= schedule.reminder_days_before:
            status = MaintenanceStatus.DUE_SOON
        else:
            status = MaintenanceStatus.OK

        return {
            "schedule_key": schedule.key,
            "maintenance_type": schedule.maintenance_type.value,
            "next_due": next_due.isoformat(),
            "days_until": round(days_until, 1),
            "status": status.value,
            "priority": schedule.priority.value,
        }

    def validate_tank_assignment(
        self,
        tank_type: TankType,
        irrigation_system: IrrigationSystem | None,
    ) -> None:
        """Validate tank assignment rules.

        - Recirculation tanks require hydro irrigation systems.
        - Stock solution tanks cannot be assigned directly to a location
          (they must use feeds_from edges to feed other tanks).
        """
        if tank_type == TankType.STOCK_SOLUTION:
            raise ValueError(
                "Stock solution tanks cannot be assigned directly to a location. "
                "Use feeds_from to connect them to other tanks."
            )
        if tank_type == TankType.RECIRCULATION and (
            irrigation_system is None or irrigation_system not in HYDRO_SYSTEMS
        ):
            allowed = ", ".join(s.value for s in HYDRO_SYSTEMS)
            raise ValueError(
                f"Recirculation tanks require a hydro irrigation system ({allowed}), got: {irrigation_system}"
            )

    def validate_fill_level(
        self,
        volume_liters: float,
        fill_liters: float | None,
        fill_percent: float | None,
    ) -> tuple[float | None, float | None]:
        """Validate and auto-calculate fill level. Returns (liters, percent)."""
        if fill_liters is not None and fill_percent is not None:
            # Both provided — check consistency
            expected_percent = (fill_liters / volume_liters) * 100
            if abs(expected_percent - fill_percent) > 5:
                raise ValueError(
                    f"Inconsistent fill levels: {fill_liters}L = {expected_percent:.1f}%, but {fill_percent}% given"
                )
            return fill_liters, fill_percent

        if fill_liters is not None:
            return fill_liters, round((fill_liters / volume_liters) * 100, 1)

        if fill_percent is not None:
            return round((fill_percent / 100) * volume_liters, 1), fill_percent

        return None, None

    def get_default_schedules(self, tank_type: TankType) -> list[dict]:
        """Return default maintenance schedules for a tank type."""
        return DEFAULT_MAINTENANCE_SCHEDULES.get(tank_type, [])

    # ── Fill Event Logic ────────────────────────────────────────────────

    def validate_fill_event(
        self,
        tank: Tank,
        event: TankFillEvent,
    ) -> list[str]:
        """Validate a fill event and return warnings (not errors)."""
        warnings: list[str] = []

        # Volume > capacity for full_change
        if event.fill_type == FillType.FULL_CHANGE and event.volume_liters > tank.volume_liters:
            warnings.append(f"Volume {event.volume_liters}L exceeds tank capacity {tank.volume_liters}L")

        # EC deviation target vs measured
        if event.target_ec_ms is not None and event.measured_ec_ms is not None:
            dev = abs(event.measured_ec_ms - event.target_ec_ms)
            if dev > 0.3:
                warnings.append(
                    f"EC deviation: target {event.target_ec_ms} vs measured {event.measured_ec_ms} "
                    f"(diff {dev:.2f} mS/cm)"
                )

        # pH deviation target vs measured
        if event.target_ph is not None and event.measured_ph is not None:
            dev = abs(event.measured_ph - event.target_ph)
            if dev > 0.3:
                warnings.append(
                    f"pH deviation: target {event.target_ph} vs measured {event.measured_ph} (diff {dev:.2f})"
                )

        # Chlorine/chloramine warning with biological fertilizers
        if event.is_organic_fertilizers:
            if event.chlorine_ppm is not None and event.chlorine_ppm > 0.5:
                warnings.append(
                    f"Chlorine {event.chlorine_ppm} ppm with organic/biological fertilizers — "
                    "may harm beneficial microbes"
                )
            if event.chloramine_ppm is not None and event.chloramine_ppm > 0.5:
                warnings.append(
                    f"Chloramine {event.chloramine_ppm} ppm — requires activated carbon or ascorbic acid treatment"
                )

        return warnings

    def resolve_water_defaults(
        self,
        event_data: dict,
        nutrient_plan: dict | None = None,
        site_water_config: dict | None = None,
    ) -> dict:
        """4-level cascade: explicit → nutrient_plan → site_profile → manual.

        Returns dict with resolved water fields + water_defaults_source.
        """
        resolved = {}
        source = "manual"

        # Fields to cascade
        cascade_fields = [
            "water_source",
            "water_mix_ratio_ro_percent",
            "base_water_ec_ms",
        ]

        for field in cascade_fields:
            # Level 1: explicit in event_data
            if event_data.get(field) is not None:
                resolved[field] = event_data[field]
                if source == "manual":
                    source = "explicit"
                continue

            # Level 2: from nutrient plan
            if nutrient_plan and nutrient_plan.get(field) is not None:
                resolved[field] = nutrient_plan[field]
                if source in ("manual",):
                    source = "nutrient_plan"
                continue

            # Level 3: from site water config
            if site_water_config and site_water_config.get(field) is not None:
                resolved[field] = site_water_config[field]
                if source in ("manual",):
                    source = "site_profile"
                continue

            # Level 4: not resolved — remains manual

        resolved["water_defaults_source"] = source
        return resolved
