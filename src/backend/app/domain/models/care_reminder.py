from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import CareStyleType, ConfirmAction, ReminderType, WateringMethod


class CareProfile(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    care_style: CareStyleType = CareStyleType.TROPICAL
    watering_interval_days: int = Field(default=7, ge=1, le=90)
    winter_watering_multiplier: float = Field(default=1.5, ge=1.0, le=5.0)
    watering_method: WateringMethod = WateringMethod.TOP_WATER
    water_quality_hint: str | None = None
    fertilizing_interval_days: int = Field(default=14, ge=7, le=90)
    fertilizing_active_months: list[int] = Field(default_factory=lambda: [3, 4, 5, 6, 7, 8, 9])
    repotting_interval_months: int = Field(default=24, ge=6, le=60)
    pest_check_interval_days: int = Field(default=14, ge=3, le=90)
    location_check_enabled: bool = False
    location_check_months: list[int] = Field(default_factory=list)
    humidity_check_enabled: bool = False
    humidity_check_interval_days: int = Field(default=7, ge=3, le=90)
    adaptive_learning_enabled: bool = True
    watering_interval_learned: int | None = None
    fertilizing_interval_learned: int | None = None
    notes: str | None = None
    auto_generated: bool = False
    plant_key: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class CareConfirmation(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    plant_key: str
    care_profile_key: str
    reminder_type: ReminderType
    action: ConfirmAction
    confirmed_at: datetime
    snooze_days: int | None = None
    task_key: str | None = None
    notes: str | None = None
    interval_at_time: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class CareDashboardEntry(BaseModel):
    plant_key: str
    plant_name: str
    species_name: str | None = None
    reminder_type: ReminderType
    urgency: str  # overdue | due_today | upcoming | not_due
    due_date: str | None = None
    care_profile_key: str
    task_key: str | None = None
