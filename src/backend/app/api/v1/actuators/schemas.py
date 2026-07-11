"""REQ-018 Environment-control API request/response schemas."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.common.enums import (
    ActuatorCapability,
    ActuatorProtocol,
    ActuatorType,
    ControlEventSource,
    EmergencyStopScenario,
    RuleType,
    ScheduleType,
)
from app.domain.models.actuator import (
    HysteresisConfig,
    RuleAction,
    RuleCondition,
    ScheduleEntry,
)

# ── Actuator ─────────────────────────────────────────────────────────────


class ActuatorCreate(BaseModel):
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
    power_watts: float | None = Field(default=None, ge=0, le=100000)
    fail_safe_state: str | None = None
    fail_safe_value: float | None = None
    conflict_group: str | None = Field(default=None, max_length=50)
    installed_on: date | None = None
    notes: str | None = Field(default=None, max_length=2000)


class ActuatorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    ha_entity_id: str | None = Field(default=None, max_length=200)
    mqtt_command_topic: str | None = Field(default=None, max_length=500)
    mqtt_state_topic: str | None = Field(default=None, max_length=500)
    capabilities: list[ActuatorCapability] | None = None
    min_value: float | None = None
    max_value: float | None = None
    unit: str | None = Field(default=None, max_length=20)
    power_watts: float | None = Field(default=None, ge=0, le=100000)
    fail_safe_state: str | None = None
    fail_safe_value: float | None = None
    conflict_group: str | None = Field(default=None, max_length=50)
    installed_on: date | None = None
    notes: str | None = Field(default=None, max_length=2000)


class ActuatorResponse(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    tenant_key: str
    location_key: str
    name: str
    actuator_type: ActuatorType
    protocol: ActuatorProtocol
    ha_entity_id: str | None = None
    mqtt_command_topic: str | None = None
    mqtt_state_topic: str | None = None
    capabilities: list[ActuatorCapability]
    min_value: float | None = None
    max_value: float | None = None
    unit: str | None = None
    current_state: str | None = None
    current_value: float | None = None
    last_state_change: datetime | None = None
    is_online: bool
    last_seen: datetime | None = None
    power_watts: float | None = None
    fail_safe_state: str | None = None
    fail_safe_value: float | None = None
    conflict_group: str | None = None
    installed_on: date | None = None
    notes: str | None = None

    model_config = {"populate_by_name": True}


# ── Command & override ───────────────────────────────────────────────────


class CommandRequest(BaseModel):
    command: str = Field(pattern=r"^(turn_on|turn_off|set_value)$")
    value: float | None = None


class OverrideCreate(BaseModel):
    expires_at: datetime
    override_value: float | None = None
    override_state: str | None = Field(default=None, pattern=r"^(on|off)$")
    reason: str | None = Field(default=None, max_length=500)


class ControlEventResponse(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    actuator_key: str
    location_key: str
    timestamp: datetime | None = None
    event_source: ControlEventSource
    command: str
    value: float | None = None
    previous_state: str | None = None
    new_state: str
    success: bool
    error_message: str | None = None
    triggered_by_rule_key: str | None = None
    triggered_by_schedule_key: str | None = None
    triggered_by_user: str | None = None
    sensor_reading_at_trigger: float | None = None

    model_config = {"populate_by_name": True}


# ── Schedules ────────────────────────────────────────────────────────────


class ScheduleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    schedule_type: ScheduleType = ScheduleType.DAILY
    is_active: bool = True
    priority: int = Field(default=50, ge=1, le=100)
    entries: list[ScheduleEntry] = Field(min_length=1)
    valid_from: date | None = None
    valid_until: date | None = None
    notes: str | None = Field(default=None, max_length=2000)


class ScheduleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    is_active: bool | None = None
    priority: int | None = Field(default=None, ge=1, le=100)
    entries: list[ScheduleEntry] | None = None
    valid_from: date | None = None
    valid_until: date | None = None
    notes: str | None = Field(default=None, max_length=2000)


class ScheduleResponse(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    actuator_key: str
    name: str
    schedule_type: ScheduleType
    is_active: bool
    priority: int
    entries: list[ScheduleEntry]
    valid_from: date | None = None
    valid_until: date | None = None
    notes: str | None = None

    model_config = {"populate_by_name": True}


# ── Rules ────────────────────────────────────────────────────────────────


class RuleCreate(BaseModel):
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


class RuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    is_active: bool | None = None
    priority: int | None = Field(default=None, ge=1, le=100)
    sensor_parameter: str | None = Field(default=None, min_length=1, max_length=50)
    condition: RuleCondition | None = None
    action: RuleAction | None = None
    hysteresis: HysteresisConfig | None = None
    is_safety_rule: bool | None = None
    notes: str | None = Field(default=None, max_length=2000)


class RuleResponse(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    actuator_key: str
    name: str
    is_active: bool
    priority: int
    rule_type: RuleType
    sensor_parameter: str
    sensor_location_key: str | None = None
    condition: RuleCondition
    action: RuleAction
    hysteresis: HysteresisConfig
    is_safety_rule: bool
    notes: str | None = None

    model_config = {"populate_by_name": True}


class RuleTestRequest(BaseModel):
    sensor_readings: dict[str, float] = Field(default_factory=dict)


# ── Phase control profiles ───────────────────────────────────────────────


class PhaseControlProfileCreate(BaseModel):
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


class PhaseControlProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    target_photoperiod_hours: float | None = Field(default=None, ge=0, le=24)
    target_light_ppfd: int | None = Field(default=None, ge=0, le=2000)
    target_light_dimmer_percent: float | None = Field(default=None, ge=0, le=100)
    target_temperature_day_c: float | None = Field(default=None, ge=5, le=45)
    target_temperature_night_c: float | None = Field(default=None, ge=5, le=45)
    target_humidity_day_percent: int | None = Field(default=None, ge=0, le=100)
    target_humidity_night_percent: int | None = Field(default=None, ge=0, le=100)
    target_vpd_kpa: float | None = Field(default=None, ge=0, le=5)
    co2_enrichment_ppm: int | None = Field(default=None, ge=0, le=2000)
    transition_days: int | None = Field(default=None, ge=0, le=30)
    notes: str | None = Field(default=None, max_length=2000)


class PhaseControlProfileResponse(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    tenant_key: str
    name: str
    target_photoperiod_hours: float
    target_light_ppfd: int
    target_light_dimmer_percent: float | None = None
    target_temperature_day_c: float
    target_temperature_night_c: float
    target_humidity_day_percent: int
    target_humidity_night_percent: int
    target_vpd_kpa: float | None = None
    co2_enrichment_ppm: int | None = None
    co2_only_during_lights_on: bool
    co2_min_ppfd_threshold: int | None = None
    target_dli_mol: float | None = None
    photoperiod_is_critical: bool
    dif_target_c: float | None = None
    irrigation_frequency_per_day: int | None = None
    irrigation_duration_seconds: int | None = None
    transition_days: int
    is_template: bool
    notes: str | None = None

    model_config = {"populate_by_name": True}


class ApplyProfileRequest(BaseModel):
    location_key: str = Field(min_length=1)


class EmergencyStopRequest(BaseModel):
    scenario: EmergencyStopScenario
