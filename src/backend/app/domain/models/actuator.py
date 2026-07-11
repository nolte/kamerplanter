"""REQ-018 Environment-control / actuator domain models.

Closes the sensor -> actuator loop (REQ-005 is the input side): an
:class:`Actuator` is a controllable device (light, fan, heater, humidifier,
CO2 doser, irrigation valve, ...) reachable over Home Assistant, MQTT or manual
task fallback. Control is layered by priority — manual override > safety rule >
sensor rule > schedule — and sensor rules use hysteresis to prevent oscillation.

All persisted control models carry ``tenant_key``/``location_key`` for isolation
(REQ-024). Source code is English (NFR-003); the specification lives in
``spec/req/REQ-018_Umgebungssteuerung.md`` (German).
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from app.common.enums import (
    ActionCommand,
    ActuatorCapability,
    ActuatorProtocol,
    ActuatorType,
    ConditionOperator,
    ControlEventSource,
    RuleType,
    ScheduleType,
)

# ── Embedded models ─────────────────────────────────────────────────────


class ScheduleEntry(BaseModel):
    """A single on/off window inside a control schedule."""

    time_on: str = Field(pattern=r"^\d{2}:\d{2}$")
    time_off: str = Field(pattern=r"^\d{2}:\d{2}$")
    value: float | None = None
    days_of_week: list[int] | None = Field(default=None, description="0=Mon..6=Sun, null=daily")

    @model_validator(mode="after")
    def validate_days(self) -> ScheduleEntry:
        if self.days_of_week is not None:
            for d in self.days_of_week:
                if d < 0 or d > 6:
                    raise ValueError(f"Invalid weekday {d} (0=Mon..6=Sun)")
        return self


class RuleCondition(BaseModel):
    """Threshold / range condition for a control rule."""

    operator: ConditionOperator
    threshold: float | None = None
    range_min: float | None = None
    range_max: float | None = None
    compound_operator: str | None = Field(default=None, pattern=r"^(and|or)$")
    sub_conditions: list[RuleCondition] | None = None

    @model_validator(mode="after")
    def validate_condition(self) -> RuleCondition:
        if self.operator in (
            ConditionOperator.GT,
            ConditionOperator.LT,
            ConditionOperator.GTE,
            ConditionOperator.LTE,
        ):
            if self.threshold is None:
                raise ValueError(f"threshold required for operator {self.operator}")
        elif self.operator in (ConditionOperator.BETWEEN, ConditionOperator.OUTSIDE):
            if self.range_min is None or self.range_max is None:
                raise ValueError(f"range_min and range_max required for operator {self.operator}")
            if self.range_min >= self.range_max:
                raise ValueError("range_min must be smaller than range_max")
        return self


class RuleAction(BaseModel):
    """Action performed when a rule fires."""

    command: ActionCommand
    value: float | None = None
    step: float | None = None

    @model_validator(mode="after")
    def validate_action(self) -> RuleAction:
        if self.command == ActionCommand.SET_VALUE and self.value is None:
            raise ValueError("value required for set_value")
        if self.command in (ActionCommand.INCREASE, ActionCommand.DECREASE) and self.step is None:
            raise ValueError(f"step required for {self.command}")
        return self


class HysteresisConfig(BaseModel):
    """Hysteresis / debouncing configuration guarding against oscillation."""

    on_threshold: float
    off_threshold: float
    min_on_duration_seconds: int = Field(default=60, ge=0, le=3600)
    min_off_duration_seconds: int = Field(default=60, ge=0, le=3600)
    cooldown_seconds: int = Field(default=30, ge=0, le=600)

    @model_validator(mode="after")
    def validate_thresholds(self) -> HysteresisConfig:
        if self.on_threshold == self.off_threshold:
            raise ValueError("on_threshold and off_threshold must differ (otherwise no hysteresis)")
        return self


# ── Persisted models ────────────────────────────────────────────────────


class Actuator(BaseModel):
    """A controllable device assigned to a location (REQ-018 §2)."""

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    location_key: str = ""
    name: str = Field(min_length=1, max_length=200)
    actuator_type: ActuatorType
    protocol: ActuatorProtocol = ActuatorProtocol.HOME_ASSISTANT
    ha_entity_id: str | None = Field(default=None, max_length=200)
    mqtt_command_topic: str | None = Field(default=None, max_length=500)
    mqtt_state_topic: str | None = Field(default=None, max_length=500)
    capabilities: list[ActuatorCapability] = Field(default_factory=lambda: [ActuatorCapability.ON_OFF])
    min_value: float | None = None
    max_value: float | None = None
    unit: str | None = Field(default=None, max_length=20)
    current_state: str | None = "off"
    current_value: float | None = None
    last_state_change: datetime | None = None
    is_online: bool = True
    last_seen: datetime | None = None
    power_watts: float | None = Field(default=None, ge=0, le=100000)
    fail_safe_state: str | None = None
    fail_safe_value: float | None = None
    conflict_group: str | None = Field(default=None, max_length=50)
    installed_on: date | None = None
    notes: str | None = Field(default=None, max_length=2000)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_protocol_fields(self) -> Actuator:
        if self.protocol == ActuatorProtocol.HOME_ASSISTANT and not self.ha_entity_id:
            raise ValueError("ha_entity_id required for Home Assistant protocol")
        if self.protocol == ActuatorProtocol.MQTT and not self.mqtt_command_topic:
            raise ValueError("mqtt_command_topic required for MQTT protocol")
        return self

    @model_validator(mode="after")
    def validate_dimmable_range(self) -> Actuator:
        if ActuatorCapability.DIMMABLE in self.capabilities and (self.min_value is None or self.max_value is None):
            raise ValueError("min_value and max_value required for dimmable actuators")
        return self


class ControlSchedule(BaseModel):
    """Time-based control plan for one actuator (REQ-018 §2)."""

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    actuator_key: str = ""
    name: str = Field(min_length=1, max_length=200)
    schedule_type: ScheduleType = ScheduleType.DAILY
    is_active: bool = True
    priority: int = Field(default=50, ge=1, le=100)
    entries: list[ScheduleEntry] = Field(min_length=1)
    valid_from: date | None = None
    valid_until: date | None = None
    notes: str | None = Field(default=None, max_length=2000)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_date_range(self) -> ControlSchedule:
        if self.valid_from and self.valid_until and self.valid_from >= self.valid_until:
            raise ValueError("valid_from must precede valid_until")
        return self


class ControlRule(BaseModel):
    """Sensor-driven automation rule for one actuator (REQ-018 §2)."""

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    actuator_key: str = ""
    name: str = Field(min_length=1, max_length=200)
    is_active: bool = True
    priority: int = Field(default=50, ge=1, le=100)
    rule_type: RuleType = RuleType.THRESHOLD
    sensor_parameter: str = Field(min_length=1, max_length=50)
    sensor_location_key: str | None = None
    condition: RuleCondition
    action: RuleAction
    hysteresis: HysteresisConfig
    is_safety_rule: bool = False
    notes: str | None = Field(default=None, max_length=2000)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class ControlEvent(BaseModel):
    """Immutable log of one control action (REQ-018 §2)."""

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    actuator_key: str = ""
    location_key: str = ""
    timestamp: datetime | None = None
    event_source: ControlEventSource
    command: str = Field(min_length=1, max_length=100)
    value: float | None = None
    previous_state: str | None = None
    new_state: str
    success: bool
    error_message: str | None = Field(default=None, max_length=1000)
    triggered_by_rule_key: str | None = None
    triggered_by_schedule_key: str | None = None
    triggered_by_user: str | None = None
    sensor_reading_at_trigger: float | None = None
    notes: str | None = Field(default=None, max_length=2000)

    model_config = {"populate_by_name": True}


class ManualOverride(BaseModel):
    """Temporary manual override that supersedes automation (REQ-018 §2)."""

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    actuator_key: str = ""
    started_at: datetime
    expires_at: datetime
    override_value: float | None = None
    override_state: str | None = None
    reason: str | None = Field(default=None, max_length=500)
    created_by: str = Field(min_length=1, max_length=100)
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_expiry(self) -> ManualOverride:
        if self.expires_at <= self.started_at:
            raise ValueError("expires_at must be after started_at")
        return self

    @model_validator(mode="after")
    def validate_override_value(self) -> ManualOverride:
        if self.override_value is None and self.override_state is None:
            raise ValueError("either override_value or override_state is required")
        return self


class PhaseControlProfile(BaseModel):
    """Actuator target configuration for a growth phase (REQ-018 §2)."""

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    name: str = Field(min_length=1, max_length=200)
    target_photoperiod_hours: float = Field(ge=0, le=24)
    target_light_ppfd: int = Field(ge=0, le=2000)
    target_light_dimmer_percent: float | None = Field(default=None, ge=0, le=100)
    target_temperature_day_c: float = Field(ge=5, le=45)
    target_temperature_night_c: float = Field(ge=5, le=45)
    target_humidity_day_percent: int = Field(ge=0, le=100)
    target_humidity_night_percent: int = Field(ge=0, le=100)
    target_vpd_kpa: float | None = Field(default=None, ge=0, le=5)
    co2_enrichment_ppm: int | None = Field(default=None, ge=0, le=2000)
    co2_only_during_lights_on: bool = True
    co2_min_ppfd_threshold: int | None = Field(default=None, ge=0, le=2000)
    target_dli_mol: float | None = Field(default=None, ge=0, le=65)
    photoperiod_is_critical: bool = False
    dif_target_c: float | None = Field(default=None, ge=-4, le=12)
    irrigation_frequency_per_day: int | None = Field(default=None, ge=0, le=48)
    irrigation_duration_seconds: int | None = Field(default=None, ge=0, le=3600)
    transition_days: int = Field(default=0, ge=0, le=30)
    is_template: bool = False
    notes: str | None = Field(default=None, max_length=2000)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_temperature_differential(self) -> PhaseControlProfile:
        dif = self.target_temperature_day_c - self.target_temperature_night_c
        if dif > 12:
            raise ValueError(f"Day/night temperature difference too large ({dif:.1f} C, max DIF 12 C)")
        if dif < -4:
            raise ValueError(f"Negative DIF of {dif:.1f} C is physiologically extreme (max -4 C)")
        return self
