from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import CareStyleType, ConfirmAction, ReminderType, WateringMethod


class CareProfileResponse(BaseModel):
    key: str
    care_style: CareStyleType
    watering_interval_days: int
    winter_watering_multiplier: float
    watering_method: WateringMethod
    water_quality_hint: str | None = None
    fertilizing_interval_days: int
    fertilizing_active_months: list[int]
    repotting_interval_months: int
    pest_check_interval_days: int
    location_check_enabled: bool
    location_check_months: list[int]
    humidity_check_enabled: bool
    humidity_check_interval_days: int
    adaptive_learning_enabled: bool
    auto_create_watering_task: bool
    auto_create_fertilizing_task: bool
    auto_create_repotting_task: bool
    auto_create_pest_check_task: bool
    watering_interval_learned: int | None = None
    fertilizing_interval_learned: int | None = None
    notes: str | None = None
    auto_generated: bool
    plant_key: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CareProfileUpdate(BaseModel):
    care_style: CareStyleType | None = None
    watering_interval_days: int | None = Field(default=None, ge=1, le=90)
    winter_watering_multiplier: float | None = Field(default=None, ge=1.0, le=5.0)
    watering_method: WateringMethod | None = None
    water_quality_hint: str | None = None
    fertilizing_interval_days: int | None = Field(default=None, ge=7, le=90)
    fertilizing_active_months: list[int] | None = None
    repotting_interval_months: int | None = Field(default=None, ge=6, le=60)
    pest_check_interval_days: int | None = Field(default=None, ge=3, le=90)
    location_check_enabled: bool | None = None
    location_check_months: list[int] | None = None
    humidity_check_enabled: bool | None = None
    humidity_check_interval_days: int | None = Field(default=None, ge=3, le=90)
    adaptive_learning_enabled: bool | None = None
    auto_create_watering_task: bool | None = None
    auto_create_fertilizing_task: bool | None = None
    auto_create_repotting_task: bool | None = None
    auto_create_pest_check_task: bool | None = None
    notes: str | None = None


class FeedingDetailSchema(BaseModel):
    fertilizer_key: str
    ml_applied: float = Field(gt=0)


class ConfirmRequest(BaseModel):
    reminder_type: ReminderType
    notes: str | None = None
    volume_liters: float | None = Field(default=None, gt=0)
    fertilizers_used: list[FeedingDetailSchema] | None = None
    measured_ec: float | None = Field(default=None, ge=0)
    measured_ph: float | None = Field(default=None, ge=0, le=14)


class SnoozeRequest(BaseModel):
    reminder_type: ReminderType
    snooze_days: int = Field(default=1, ge=1, le=7)


class CareConfirmationResponse(BaseModel):
    key: str
    plant_key: str
    care_profile_key: str
    reminder_type: ReminderType
    action: ConfirmAction
    confirmed_at: datetime
    snooze_days: int | None = None
    watering_log_key: str | None = None
    notes: str | None = None
    interval_at_time: int | None = None


class CareDashboardEntryResponse(BaseModel):
    plant_key: str
    plant_name: str
    species_name: str | None = None
    reminder_type: ReminderType
    urgency: str
    due_date: str | None = None
    care_profile_key: str
    task_key: str | None = None
