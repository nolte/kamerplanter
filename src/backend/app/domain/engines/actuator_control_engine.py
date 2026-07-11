"""REQ-018 Environment-control engines.

:class:`ControlEngine` is the priority-and-hysteresis core: given an actuator,
its active rules/schedules/override and the latest sensor readings it decides the
single winning desired state. The priority ladder is
``manual override > safety rule > sensor rule > schedule`` (REQ-018 §1); sensor
rules apply hysteresis (separate on/off thresholds plus minimum on/off dwell
time) so the actuator never oscillates.

:class:`HomeAssistantCommandMapper` translates a Kamerplanter command into a
concrete HA ``(domain, service, data)`` service call.

:class:`PhaseTransitionHandler` derives gradual actuator transitions (e.g. an
18h -> 12h photoperiod ramp over N days) from a phase control profile.

Pure domain logic — no I/O, no DB, no HTTP — so it is exhaustively unit-testable
(REQ-018 §6 scenarios 1-10). Source code is English (NFR-003).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.common.enums import ActionCommand, ConditionOperator, ControlEventSource
from app.domain.models.actuator import (
    Actuator,
    ControlRule,
    ControlSchedule,
    ManualOverride,
    RuleCondition,
)

# Priority levels — higher wins. A regular/safety rule's own ``priority``
# (1..100) is added on top so ties inside a band resolve deterministically.
PRIORITY_MANUAL_OVERRIDE = 1000
PRIORITY_SAFETY_RULE = 900
PRIORITY_RULE = 500
PRIORITY_SCHEDULE = 100


@dataclass
class DesiredState:
    """The winning control decision for an actuator (or ``None`` = no change)."""

    command: str
    value: float | None
    state: str  # "on" | "off"
    source: ControlEventSource
    source_key: str | None
    priority: int
    sensor_reading: float | None = None


class ControlEngine:
    """Decides the desired state of an actuator from all active control inputs."""

    def evaluate_actuator_state(
        self,
        actuator: Actuator,
        active_rules: list[ControlRule],
        active_schedules: list[ControlSchedule],
        active_override: ManualOverride | None,
        sensor_readings: dict[str, float],
        now: datetime,
    ) -> DesiredState | None:
        """Return the highest-priority desired state, or ``None`` if unchanged."""
        candidates: list[DesiredState] = []

        override_state = self._evaluate_override(active_override, now)
        if override_state is not None:
            candidates.append(override_state)

        # Safety rules first, then regular rules (distinct priority bands).
        for rule in active_rules:
            if not rule.is_active or not rule.is_safety_rule:
                continue
            result = self._evaluate_rule(rule, sensor_readings, actuator, now)
            if result is not None:
                result.priority = PRIORITY_SAFETY_RULE + rule.priority
                candidates.append(result)

        for rule in active_rules:
            if not rule.is_active or rule.is_safety_rule:
                continue
            result = self._evaluate_rule(rule, sensor_readings, actuator, now)
            if result is not None:
                result.priority = PRIORITY_RULE + rule.priority
                candidates.append(result)

        for schedule in active_schedules:
            if not schedule.is_active:
                continue
            result = self._evaluate_schedule(schedule, now)
            if result is not None:
                result.priority = PRIORITY_SCHEDULE + schedule.priority
                candidates.append(result)

        if not candidates:
            return None

        candidates.sort(key=lambda c: c.priority, reverse=True)
        winner = candidates[0]

        if self._is_same_state(actuator, winner):
            return None
        return winner

    # ── Override ─────────────────────────────────────────────────────────

    def _evaluate_override(self, override: ManualOverride | None, now: datetime) -> DesiredState | None:
        if override is None or not override.is_active:
            return None
        if now >= override.expires_at:
            return None
        if override.override_value is not None:
            state = "off" if override.override_value == 0 else "on"
            return DesiredState(
                command=ActionCommand.SET_VALUE.value,
                value=override.override_value,
                state=state,
                source=ControlEventSource.MANUAL,
                source_key=override.key,
                priority=PRIORITY_MANUAL_OVERRIDE,
            )
        state = override.override_state or "on"
        return DesiredState(
            command=ActionCommand.TURN_ON.value if state != "off" else ActionCommand.TURN_OFF.value,
            value=None,
            state=state,
            source=ControlEventSource.MANUAL,
            source_key=override.key,
            priority=PRIORITY_MANUAL_OVERRIDE,
        )

    # ── Rules ────────────────────────────────────────────────────────────

    def _evaluate_rule(
        self,
        rule: ControlRule,
        sensor_readings: dict[str, float],
        actuator: Actuator,
        now: datetime,
    ) -> DesiredState | None:
        reading = sensor_readings.get(rule.sensor_parameter)
        if reading is None:
            return None

        is_on = (actuator.current_state or "off") != "off"
        hysteresis = rule.hysteresis

        should_turn_on = self._check_condition(rule.condition, reading, hysteresis.on_threshold)
        should_turn_off = not self._check_condition(rule.condition, reading, hysteresis.off_threshold)

        # Minimum dwell time (debounce): honour min on/off duration before flipping.
        if actuator.last_state_change is not None:
            seconds_since = (now - actuator.last_state_change).total_seconds()
            if is_on and seconds_since < hysteresis.min_on_duration_seconds:
                return None
            if not is_on and seconds_since < hysteresis.min_off_duration_seconds:
                return None

        source = ControlEventSource.SAFETY if rule.is_safety_rule else ControlEventSource.RULE

        if not is_on and should_turn_on:
            return DesiredState(
                command=rule.action.command.value,
                value=rule.action.value,
                state="off" if rule.action.value == 0 else "on",
                source=source,
                source_key=rule.key,
                priority=0,
                sensor_reading=reading,
            )
        if is_on and should_turn_off:
            return DesiredState(
                command=ActionCommand.TURN_OFF.value,
                value=None,
                state="off",
                source=source,
                source_key=rule.key,
                priority=0,
                sensor_reading=reading,
            )
        return None

    def _check_condition(self, condition: RuleCondition, value: float, threshold: float) -> bool:
        op = condition.operator
        if op == ConditionOperator.GT:
            return value > threshold
        if op == ConditionOperator.LT:
            return value < threshold
        if op == ConditionOperator.GTE:
            return value >= threshold
        if op == ConditionOperator.LTE:
            return value <= threshold
        if op == ConditionOperator.BETWEEN:
            return (condition.range_min or 0) <= value <= (condition.range_max or 0)
        if op == ConditionOperator.OUTSIDE:
            return value < (condition.range_min or 0) or value > (condition.range_max or 0)
        return False

    # ── Schedules ────────────────────────────────────────────────────────

    def _evaluate_schedule(self, schedule: ControlSchedule, now: datetime) -> DesiredState | None:
        current_time = now.strftime("%H:%M")
        current_weekday = now.weekday()

        for entry in schedule.entries:
            if entry.days_of_week and current_weekday not in entry.days_of_week:
                continue
            if entry.time_on <= entry.time_off:
                active = entry.time_on <= current_time < entry.time_off
            else:  # midnight wrap (e.g. 06:00 -> 00:00)
                active = current_time >= entry.time_on or current_time < entry.time_off
            if active:
                return DesiredState(
                    command=ActionCommand.SET_VALUE.value if entry.value is not None else ActionCommand.TURN_ON.value,
                    value=entry.value,
                    state="on",
                    source=ControlEventSource.SCHEDULE,
                    source_key=schedule.key,
                    priority=0,
                )
        # No matching window -> the schedule wants the actuator off.
        return DesiredState(
            command=ActionCommand.TURN_OFF.value,
            value=None,
            state="off",
            source=ControlEventSource.SCHEDULE,
            source_key=schedule.key,
            priority=0,
        )

    def _is_same_state(self, actuator: Actuator, desired: DesiredState) -> bool:
        if (actuator.current_state or "off") != desired.state:
            return False
        return not (desired.value is not None and actuator.current_value != desired.value)

    def test_rule(
        self,
        rule: ControlRule,
        actuator: Actuator,
        sensor_readings: dict[str, float],
        now: datetime,
    ) -> dict:
        """Dry-run a rule against current readings (REQ-018 §6 scenario 10)."""
        reading = sensor_readings.get(rule.sensor_parameter)
        if reading is None:
            return {
                "would_trigger": False,
                "reason": "no_sensor_reading",
                "sensor_parameter": rule.sensor_parameter,
            }
        result = self._evaluate_rule(rule, sensor_readings, actuator, now)
        return {
            "would_trigger": result is not None,
            "command": result.command if result else None,
            "value": result.value if result else None,
            "current_sensor_value": reading,
            "on_threshold": rule.hysteresis.on_threshold,
            "off_threshold": rule.hysteresis.off_threshold,
            "sensor_parameter": rule.sensor_parameter,
        }


class HomeAssistantCommandMapper:
    """Translates a Kamerplanter command into an HA ``(domain, service, data)``."""

    _MAPPING: dict[str, dict[str, tuple[str, str, str | None]]] = {
        "light": {
            "turn_on": ("light", "turn_on", None),
            "turn_off": ("light", "turn_off", None),
            "set_value": ("light", "turn_on", "brightness_pct"),
        },
        "exhaust_fan": {
            "turn_on": ("fan", "turn_on", None),
            "turn_off": ("fan", "turn_off", None),
            "set_value": ("fan", "set_percentage", "percentage"),
        },
        "circulation_fan": {
            "turn_on": ("fan", "turn_on", None),
            "turn_off": ("fan", "turn_off", None),
            "set_value": ("fan", "set_percentage", "percentage"),
        },
        "heater": {
            "turn_on": ("climate", "turn_on", None),
            "turn_off": ("climate", "turn_off", None),
            "set_value": ("climate", "set_temperature", "temperature"),
        },
        "humidifier": {
            "turn_on": ("humidifier", "turn_on", None),
            "turn_off": ("humidifier", "turn_off", None),
            "set_value": ("humidifier", "set_humidity", "humidity"),
        },
    }

    def map_command(
        self,
        actuator_type: str,
        entity_id: str,
        command: str,
        value: float | None,
    ) -> tuple[str, str, dict]:
        """Return ``(domain, service, service_data)`` for an HA service call."""
        type_map = self._MAPPING.get(actuator_type)
        if type_map is None:
            # Fallback: treat as a generic switch.
            service = "turn_off" if command == "turn_off" else "turn_on"
            return ("switch", service, {"entity_id": entity_id})

        entry = type_map.get(command)
        if entry is None:
            service = "turn_off" if command == "turn_off" else "turn_on"
            domain = type_map.get("turn_on", ("switch", "turn_on", None))[0]
            return (domain, service, {"entity_id": entity_id})

        domain, service, data_key = entry
        data: dict = {"entity_id": entity_id}
        if data_key is not None and value is not None:
            data[data_key] = value
        return (domain, service, data)


class PhaseTransitionHandler:
    """Derives gradual actuator transitions from a phase control profile."""

    def calculate_gradual_transition(
        self,
        current_value: float,
        target_value: float,
        transition_days: int,
        current_day: int,
    ) -> float:
        """Linearly interpolate a value for ``current_day`` of the transition."""
        if transition_days <= 0 or current_day >= transition_days:
            return target_value
        progress = current_day / transition_days
        return round(current_value + (target_value - current_value) * progress, 2)
