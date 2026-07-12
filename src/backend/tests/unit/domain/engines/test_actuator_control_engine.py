"""REQ-018 ControlEngine unit tests — priority ladder + hysteresis + schedules.

Covers the acceptance scenarios in REQ-018 §6: VPD rule firing, the hysteresis
band, safety-over-schedule priority, manual override winning, schedule windows
(incl. midnight wrap), the HA command mapper and the gradual-transition helper.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.common.enums import (
    ActionCommand,
    ActuatorType,
    ConditionOperator,
    ControlEventSource,
    RuleType,
    ScheduleType,
)
from app.domain.engines.actuator_control_engine import (
    ControlEngine,
    HomeAssistantCommandMapper,
    PhaseTransitionHandler,
    clamp_to_bounds,
)
from app.domain.models.actuator import (
    Actuator,
    ControlRule,
    ControlSchedule,
    HysteresisConfig,
    ManualOverride,
    RuleAction,
    RuleCondition,
    ScheduleEntry,
)


def _actuator(state: str = "off", value: float | None = None, atype=ActuatorType.HUMIDIFIER, **kw) -> Actuator:
    return Actuator(
        _key="act1",
        tenant_key="t1",
        location_key="loc1",
        name="Humidifier",
        actuator_type=atype,
        protocol="home_assistant",
        ha_entity_id="humidifier.zelt_1",
        current_state=state,
        current_value=value,
        **kw,
    )


def _rule(on: float, off: float, op=ConditionOperator.GT, safety=False, param="vpd", **kw) -> ControlRule:
    threshold = on
    condition = RuleCondition(operator=op, threshold=threshold)
    return ControlRule(
        _key="rule1",
        tenant_key="t1",
        actuator_key="act1",
        name="VPD rule",
        rule_type=RuleType.THRESHOLD,
        sensor_parameter=param,
        condition=condition,
        action=RuleAction(command=ActionCommand.TURN_ON),
        hysteresis=HysteresisConfig(
            on_threshold=on, off_threshold=off, min_on_duration_seconds=0, min_off_duration_seconds=0
        ),
        is_safety_rule=safety,
        **kw,
    )


NOW = datetime(2026, 7, 11, 10, 0, tzinfo=UTC)


class TestHysteresis:
    def test_turns_on_above_on_threshold(self):
        engine = ControlEngine()
        actuator = _actuator(state="off")
        rule = _rule(on=1.5, off=1.2)
        decision = engine.evaluate_actuator_state(actuator, [rule], [], None, {"vpd": 1.6}, NOW)
        assert decision is not None
        assert decision.state == "on"
        assert decision.source == ControlEventSource.RULE

    def test_stays_on_inside_hysteresis_band(self):
        # VPD 1.35 is between off (1.2) and on (1.5): no state change while on.
        engine = ControlEngine()
        actuator = _actuator(state="on")
        rule = _rule(on=1.5, off=1.2)
        decision = engine.evaluate_actuator_state(actuator, [rule], [], None, {"vpd": 1.35}, NOW)
        assert decision is None

    def test_turns_off_below_off_threshold(self):
        engine = ControlEngine()
        actuator = _actuator(state="on")
        rule = _rule(on=1.5, off=1.2)
        decision = engine.evaluate_actuator_state(actuator, [rule], [], None, {"vpd": 1.15}, NOW)
        assert decision is not None
        assert decision.state == "off"

    def test_min_on_duration_blocks_early_off(self):
        engine = ControlEngine()
        actuator = _actuator(state="on")
        actuator.last_state_change = NOW - timedelta(seconds=30)
        rule = _rule(on=1.5, off=1.2)
        rule.hysteresis.min_on_duration_seconds = 120
        decision = engine.evaluate_actuator_state(actuator, [rule], [], None, {"vpd": 1.0}, NOW)
        assert decision is None  # still within minimum on-time

    def test_no_reading_no_action(self):
        engine = ControlEngine()
        decision = engine.evaluate_actuator_state(_actuator(), [_rule(1.5, 1.2)], [], None, {}, NOW)
        assert decision is None


class TestPriorityLadder:
    def test_safety_beats_schedule(self):
        engine = ControlEngine()
        actuator = _actuator(state="off", atype=ActuatorType.EXHAUST_FAN)
        actuator.ha_entity_id = "fan.abluft"
        safety = _rule(on=30, off=27, param="temperature", safety=True)
        safety.action = RuleAction(command=ActionCommand.SET_VALUE, value=100)
        schedule = ControlSchedule(
            _key="sch1",
            tenant_key="t1",
            actuator_key="act1",
            name="fan schedule",
            schedule_type=ScheduleType.DAILY,
            entries=[ScheduleEntry(time_on="00:00", time_off="23:59", value=50)],
        )
        decision = engine.evaluate_actuator_state(actuator, [safety], [schedule], None, {"temperature": 31}, NOW)
        assert decision is not None
        assert decision.source == ControlEventSource.SAFETY
        assert decision.value == 100

    def test_override_beats_everything(self):
        engine = ControlEngine()
        actuator = _actuator(state="off", atype=ActuatorType.EXHAUST_FAN)
        actuator.ha_entity_id = "fan.abluft"
        safety = _rule(on=30, off=27, param="temperature", safety=True)
        override = ManualOverride(
            _key="ov1",
            tenant_key="t1",
            actuator_key="act1",
            started_at=NOW - timedelta(minutes=5),
            expires_at=NOW + timedelta(hours=1),
            override_value=100,
            created_by="user1",
        )
        decision = engine.evaluate_actuator_state(actuator, [safety], [], override, {"temperature": 31}, NOW)
        assert decision is not None
        assert decision.source == ControlEventSource.MANUAL
        assert decision.priority == 1000

    def test_expired_override_ignored(self):
        engine = ControlEngine()
        actuator = _actuator(state="off")
        override = ManualOverride(
            _key="ov1",
            tenant_key="t1",
            actuator_key="act1",
            started_at=NOW - timedelta(hours=2),
            expires_at=NOW - timedelta(minutes=1),
            override_value=100,
            created_by="user1",
        )
        decision = engine.evaluate_actuator_state(actuator, [], [], override, {}, NOW)
        assert decision is None


class TestSchedule:
    def test_active_window_turns_on(self):
        engine = ControlEngine()
        actuator = _actuator(state="off", atype=ActuatorType.LIGHT)
        actuator.ha_entity_id = "light.zelt"
        schedule = ControlSchedule(
            _key="sch1",
            tenant_key="t1",
            actuator_key="act1",
            name="veg 18/6",
            schedule_type=ScheduleType.DAILY,
            entries=[ScheduleEntry(time_on="06:00", time_off="00:00", value=100)],
        )
        decision = engine.evaluate_actuator_state(actuator, [], [schedule], None, {}, NOW)
        assert decision is not None
        assert decision.state == "on"
        assert decision.value == 100

    def test_midnight_wrap_active(self):
        engine = ControlEngine()
        # 06:00 -> 00:00 window; at 23:00 the actuator should be on.
        late = datetime(2026, 7, 11, 23, 0, tzinfo=UTC)
        actuator = _actuator(state="off", atype=ActuatorType.LIGHT)
        actuator.ha_entity_id = "light.zelt"
        schedule = ControlSchedule(
            _key="sch1",
            tenant_key="t1",
            actuator_key="act1",
            name="veg",
            schedule_type=ScheduleType.DAILY,
            entries=[ScheduleEntry(time_on="06:00", time_off="00:00", value=100)],
        )
        decision = engine.evaluate_actuator_state(actuator, [], [schedule], None, {}, late)
        assert decision is not None
        assert decision.state == "on"


class TestDryRun:
    def test_would_trigger(self):
        engine = ControlEngine()
        rule = _rule(on=18, off=21, op=ConditionOperator.LT, param="temperature")
        actuator = _actuator(state="off", atype=ActuatorType.HEATER)
        actuator.ha_entity_id = "climate.heater"
        result = engine.test_rule(rule, actuator, {"temperature": 16.5}, NOW)
        assert result["would_trigger"] is True
        assert result["current_sensor_value"] == 16.5

    def test_no_reading(self):
        result = ControlEngine().test_rule(_rule(1.5, 1.2), _actuator(), {}, NOW)
        assert result["would_trigger"] is False


class TestCommandMapper:
    @pytest.mark.parametrize(
        "atype,command,value,expected",
        [
            ("light", "turn_on", None, ("light", "turn_on")),
            ("light", "set_value", 75, ("light", "turn_on")),
            ("exhaust_fan", "set_value", 100, ("fan", "set_percentage")),
            ("humidifier", "turn_off", None, ("humidifier", "turn_off")),
            ("co2_doser", "turn_on", None, ("switch", "turn_on")),  # fallback
        ],
    )
    def test_mapping(self, atype, command, value, expected):
        mapper = HomeAssistantCommandMapper()
        domain, service, data = mapper.map_command(atype, "x.y", command, value)
        assert (domain, service) == expected
        assert data["entity_id"] == "x.y"

    def test_set_value_includes_data_key(self):
        mapper = HomeAssistantCommandMapper()
        _, _, data = mapper.map_command("exhaust_fan", "fan.x", "set_value", 60)
        assert data["percentage"] == 60


class TestGradualTransition:
    def test_linear_interpolation(self):
        handler = PhaseTransitionHandler()
        assert handler.calculate_gradual_transition(18.0, 12.0, 7, 0) == 18.0
        assert handler.calculate_gradual_transition(18.0, 12.0, 7, 7) == 12.0
        mid = handler.calculate_gradual_transition(18.0, 12.0, 6, 3)
        assert mid == 15.0

    def test_zero_days_returns_target(self):
        handler = PhaseTransitionHandler()
        assert handler.calculate_gradual_transition(75.0, 100.0, 0, 0) == 100.0


class TestClampToBounds:
    """SEC (REQ-018): a commanded/overridden value must never exceed the
    actuator's configured [min, max] safe envelope."""

    def test_value_above_max_is_clamped_down(self):
        assert clamp_to_bounds(5000.0, 0.0, 100.0) == 100.0

    def test_value_below_min_is_clamped_up(self):
        assert clamp_to_bounds(-40.0, 10.0, 100.0) == 10.0

    def test_value_inside_bounds_passes_through(self):
        assert clamp_to_bounds(55.0, 0.0, 100.0) == 55.0

    def test_none_value_unchanged(self):
        assert clamp_to_bounds(None, 0.0, 100.0) is None

    def test_unbounded_actuator_passes_through(self):
        assert clamp_to_bounds(9999.0, None, None) == 9999.0

    def test_only_max_configured(self):
        assert clamp_to_bounds(150.0, None, 100.0) == 100.0

    def test_only_min_configured(self):
        assert clamp_to_bounds(-5.0, 0.0, None) == 0.0
