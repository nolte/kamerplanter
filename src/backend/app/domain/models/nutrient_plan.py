from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.common.enums import PhaseName, SubstrateType


class FertilizerDosage(BaseModel):
    fertilizer_key: str
    ml_per_liter: float = Field(gt=0, le=50)
    optional: bool = False


class NutrientPlanPhaseEntry(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    plan_key: str
    phase_name: PhaseName
    sequence_order: int = Field(ge=1)
    week_start: int = Field(ge=1)
    week_end: int = Field(ge=1)
    npk_ratio: tuple[float, float, float] = (0.0, 0.0, 0.0)
    target_ec_ms: float = Field(default=1.0, ge=0, le=10)
    target_ph: float = Field(default=6.0, ge=0, le=14)
    calcium_ppm: float | None = Field(default=None, ge=0)
    magnesium_ppm: float | None = Field(default=None, ge=0)
    feeding_frequency_per_week: int = Field(default=1, ge=1, le=14)
    volume_per_feeding_liters: float | None = Field(default=None, gt=0)
    notes: str | None = None
    fertilizer_dosages: list[FertilizerDosage] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @field_validator("npk_ratio")
    @classmethod
    def validate_npk(cls, v: tuple[float, float, float]) -> tuple[float, float, float]:
        for val in v:
            if val < 0:
                raise ValueError("NPK values must be non-negative")
        return v

    @field_validator("week_end")
    @classmethod
    def validate_week_end(cls, v: int, info) -> int:
        if "week_start" in info.data and v <= info.data["week_start"]:
            raise ValueError("week_end must be greater than week_start")
        return v


class NutrientPlan(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    recommended_substrate_type: SubstrateType | None = None
    author: str = ""
    is_template: bool = False
    version: str = "1.0"
    tags: list[str] = Field(default_factory=list)
    cloned_from_key: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, v: list[str]) -> list[str]:
        return [tag.lower().strip() for tag in v]
