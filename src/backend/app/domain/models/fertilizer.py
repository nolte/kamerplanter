from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from app.common.enums import (
    ApplicationMethod,
    Bioavailability,
    FertilizerType,
    PhEffect,
)


class Fertilizer(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    product_name: str = Field(min_length=1, max_length=200)
    brand: str = Field(default="", max_length=200)
    fertilizer_type: FertilizerType
    is_organic: bool = False
    tank_safe: bool = True
    recommended_application: ApplicationMethod = ApplicationMethod.ANY
    npk_ratio: tuple[float, float, float] = (0.0, 0.0, 0.0)
    ec_contribution_per_ml: float = Field(default=0.0, ge=0)
    ec_contribution_uncertain: bool = False
    max_dose_ml_per_liter: float | None = Field(default=None, ge=0.1)
    mixing_priority: int = Field(default=50, ge=1, le=100)
    ph_effect: PhEffect = PhEffect.NEUTRAL
    bioavailability: Bioavailability = Bioavailability.IMMEDIATE
    shelf_life_days: int | None = Field(default=None, ge=1)
    storage_temp_min: float | None = None
    storage_temp_max: float | None = None
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @field_validator("npk_ratio")
    @classmethod
    def validate_npk(cls, v: tuple[float, float, float]) -> tuple[float, float, float]:
        for val in v:
            if val < 0:
                raise ValueError("NPK values must be non-negative")
        if sum(v) > 100:
            raise ValueError(f"NPK sum ({sum(v)}) exceeds 100")
        return v

    @model_validator(mode="after")
    def validate_tank_safe_application(self) -> Fertilizer:
        if (
            not self.tank_safe
            and self.recommended_application == ApplicationMethod.FERTIGATION
        ):
            raise ValueError(
                "Fertilizer marked as not tank-safe cannot have fertigation as recommended application"
            )
        return self

    @model_validator(mode="after")
    def validate_storage_temp(self) -> Fertilizer:
        if (
            self.storage_temp_min is not None
            and self.storage_temp_max is not None
            and self.storage_temp_min >= self.storage_temp_max
        ):
            raise ValueError("storage_temp_min must be less than storage_temp_max")
        return self


class FertilizerStock(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    fertilizer_key: str
    current_volume_ml: float = Field(ge=0)
    purchase_date: date | None = None
    expiry_date: date | None = None
    batch_number: str = ""
    cost_per_liter: float | None = Field(default=None, ge=0)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_dates(self) -> FertilizerStock:
        if (
            self.purchase_date is not None
            and self.expiry_date is not None
            and self.expiry_date <= self.purchase_date
        ):
            raise ValueError("expiry_date must be after purchase_date")
        return self
