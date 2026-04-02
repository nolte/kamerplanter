from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.common.enums import TransitionTriggerType


class RequirementProfile(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    phase_key: str = ""
    light_ppfd_target: int = Field(default=400, ge=0)
    photoperiod_hours: float = Field(default=18.0, ge=0, le=24)
    light_spectrum: dict[str, float] = Field(default_factory=lambda: {"red": 0.6, "blue": 0.3, "far_red": 0.1})
    temperature_day_c: float = Field(default=25.0)
    temperature_night_c: float = Field(default=20.0)
    humidity_day_percent: int = Field(default=60, ge=0, le=100)
    humidity_night_percent: int = Field(default=65, ge=0, le=100)
    vpd_target_kpa: float = Field(default=1.0, ge=0)
    co2_ppm: int | None = Field(default=None, ge=0)
    irrigation_frequency_days: float | None = Field(default=1.0, gt=0)
    irrigation_volume_ml_per_plant: int = Field(default=250, ge=0)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_temp_night_lt_day(self) -> RequirementProfile:
        if self.temperature_night_c >= self.temperature_day_c:
            raise ValueError("Night temperature must be lower than day temperature")
        return self


class NutrientProfile(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    phase_key: str = ""
    npk_ratio: tuple[int, int, int] = (3, 1, 2)
    target_ec_ms: float = Field(default=1.5, ge=0)
    target_ph: float = Field(default=6.0, ge=0, le=14)
    calcium_ppm: int | None = Field(default=None, ge=0)
    magnesium_ppm: int | None = Field(default=None, ge=0)
    micro_nutrients: dict[str, int] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_npk(self) -> NutrientProfile:
        total = sum(self.npk_ratio)
        # Flushing phase allows (0,0,0)
        if total < 0:
            raise ValueError("NPK ratio values cannot be negative")
        return self


class PhaseTransitionRule(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    from_phase_key: str = ""
    to_phase_key: str = ""
    trigger_type: TransitionTriggerType = TransitionTriggerType.MANUAL
    auto_transition_after_days: int | None = Field(default=None, ge=1)
    required_conditions: dict[str, float | int | str | bool] | None = None
    notification_before_days: int = Field(default=3, ge=0)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class PhaseHistory(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    plant_instance_key: str = ""
    phase_key: str = ""
    phase_name: str = ""
    entered_at: datetime
    exited_at: datetime | None = None
    actual_duration_days: int | None = None
    cycle_number: int = Field(default=1, ge=1)
    transition_reason: str = ""
    performance_score: float | None = Field(default=None, ge=0, le=100)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
