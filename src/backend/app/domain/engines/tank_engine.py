from datetime import datetime, timedelta

from app.common.enums import (
    IrrigationSystem,
    MaintenancePriority,
    MaintenanceStatus,
    MaintenanceType,
    TankType,
)
from app.domain.models.tank import MaintenanceLog, MaintenanceSchedule, Tank, TankState

# Alert thresholds
PH_MIN = 5.0
PH_MAX = 7.0
EC_MAX_NUTRIENT = 3.0
TEMP_ALGAE_WARN = 25.0
TEMP_CRITICAL = 28.0
TEMP_ALGAE_NO_LID = 22.0
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
}


class TankEngine:
    """Pure logic for tank operations — no DB access."""

    def check_alerts(self, tank: Tank, state: TankState) -> list[dict]:
        """Check a tank state for alert conditions. Returns list of alert dicts."""
        alerts: list[dict] = []

        # pH alerts
        if state.ph is not None:
            if state.ph < PH_MIN:
                alerts.append({
                    "type": "ph_low",
                    "severity": "high",
                    "message": f"pH {state.ph:.1f} zu niedrig (min {PH_MIN})",
                    "value": state.ph,
                })
            elif state.ph > PH_MAX:
                alerts.append({
                    "type": "ph_high",
                    "severity": "high",
                    "message": f"pH {state.ph:.1f} zu hoch (max {PH_MAX})",
                    "value": state.ph,
                })

        # EC alerts (nutrient tanks)
        if (
            state.ec_ms is not None
            and tank.tank_type == TankType.NUTRIENT
            and state.ec_ms > EC_MAX_NUTRIENT
        ):
            alerts.append({
                "type": "ec_high",
                "severity": "high",
                "message": f"EC {state.ec_ms:.1f} mS zu hoch — Salzakkumulation?",
                "value": state.ec_ms,
            })

        # Temperature alerts
        if state.water_temp_celsius is not None:
            temp = state.water_temp_celsius
            if temp > TEMP_CRITICAL:
                alerts.append({
                    "type": "temp_critical",
                    "severity": "critical",
                    "message": (
                        f"Wassertemperatur {temp:.1f}°C — kritisch! "
                        "Gelöster Sauerstoff sinkt, Wurzelfäule-Gefahr."
                    ),
                    "value": temp,
                })
            elif temp > TEMP_ALGAE_WARN:
                alerts.append({
                    "type": "temp_high",
                    "severity": "medium",
                    "message": f"Wassertemperatur {temp:.1f}°C — erhöhtes Algenrisiko",
                    "value": temp,
                })

            # Algae risk for tanks without lid
            if not tank.has_lid and temp > TEMP_ALGAE_NO_LID:
                alerts.append({
                    "type": "algae_risk",
                    "severity": "medium",
                    "message": (
                        f"Kein Deckel und Wassertemperatur {temp:.1f}°C "
                        f"> {TEMP_ALGAE_NO_LID}°C — Algenrisiko!"
                    ),
                    "value": temp,
                })

        # Fill level alerts
        if (
            state.fill_level_percent is not None
            and state.fill_level_percent < FILL_LEVEL_LOW_PERCENT
        ):
            alerts.append({
                "type": "fill_low",
                "severity": "high",
                "message": f"Füllstand {state.fill_level_percent:.0f}% — Nachfüllen erforderlich",
                "value": state.fill_level_percent,
            })

        return alerts

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
        """Validate that recirculation tanks are only used with hydro systems."""
        if (
            tank_type == TankType.RECIRCULATION
            and (irrigation_system is None or irrigation_system not in HYDRO_SYSTEMS)
        ):
            allowed = ", ".join(s.value for s in HYDRO_SYSTEMS)
            raise ValueError(
                f"Recirculation tanks require a hydro irrigation system ({allowed}), "
                f"got: {irrigation_system}"
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
