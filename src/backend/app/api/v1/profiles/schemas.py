from datetime import datetime

from pydantic import BaseModel, Field


class RequirementProfileCreate(BaseModel):
    phase_key: str
    light_ppfd_target: int = Field(default=400, ge=0)
    photoperiod_hours: float = Field(default=18.0, ge=0, le=24)
    light_spectrum: dict[str, float] = Field(default_factory=lambda: {"red": 0.6, "blue": 0.3, "far_red": 0.1})
    temperature_day_c: float = 25.0
    temperature_night_c: float = 20.0
    humidity_day_percent: int = Field(default=60, ge=0, le=100)
    humidity_night_percent: int = Field(default=65, ge=0, le=100)
    vpd_target_kpa: float = Field(default=1.0, ge=0)
    co2_ppm: int | None = Field(default=None, ge=0)
    irrigation_frequency_days: float = Field(default=1.0, gt=0)
    irrigation_volume_ml_per_plant: int = Field(default=250, ge=0)

class RequirementProfileResponse(RequirementProfileCreate):
    key: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

class NutrientProfileCreate(BaseModel):
    phase_key: str
    npk_ratio: tuple[int, int, int] = (3, 1, 2)
    target_ec_ms: float = Field(default=1.5, ge=0)
    target_ph: float = Field(default=6.0, ge=0, le=14)
    calcium_ppm: int | None = Field(default=None, ge=0)
    magnesium_ppm: int | None = Field(default=None, ge=0)
    micro_nutrients: dict[str, int] = Field(default_factory=dict)

class NutrientProfileResponse(NutrientProfileCreate):
    key: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
