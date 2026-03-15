from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, model_validator

from app.common.enums import (
    EfficacyRating,
    PathogenType,
    PestPressureLevel,
    PlantPart,
    TreatmentApplicationMethod,
    TreatmentType,
)

if TYPE_CHECKING:
    from datetime import datetime


class Pest(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    scientific_name: str = Field(min_length=1, max_length=200)
    common_name: str = Field(min_length=1, max_length=200)
    pest_type: str = Field(default="insect", max_length=50)
    lifecycle_days: int | None = Field(default=None, ge=1)
    optimal_temp_min: float | None = Field(default=None, ge=-10, le=60)
    optimal_temp_max: float | None = Field(default=None, ge=-10, le=60)
    detection_difficulty: str = Field(default="medium", max_length=50)
    description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class Disease(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    scientific_name: str = Field(min_length=1, max_length=200)
    common_name: str = Field(min_length=1, max_length=200)
    pathogen_type: PathogenType
    incubation_period_days: int | None = Field(default=None, ge=1)
    environmental_triggers: list[str] = Field(default_factory=list)
    affected_plant_parts: list[PlantPart] = Field(default_factory=list)
    description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class Treatment(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    name: str = Field(min_length=1, max_length=200)
    treatment_type: TreatmentType
    active_ingredient: str | None = None
    application_method: TreatmentApplicationMethod = TreatmentApplicationMethod.SPRAY
    safety_interval_days: int = Field(default=0, ge=0)
    dosage_per_liter: float | None = Field(default=None, gt=0)
    protective_equipment: list[str] = Field(default_factory=list)
    description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def check_chemical_safety_interval(self) -> Treatment:
        if self.treatment_type == TreatmentType.CHEMICAL and self.safety_interval_days <= 0:
            raise ValueError("Chemical treatments must have a safety_interval_days > 0")
        return self


class Inspection(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    plant_key: str = ""
    inspector: str = Field(default="", max_length=200)
    inspected_at: datetime | None = None
    pressure_level: PestPressureLevel = PestPressureLevel.NONE
    detected_pest_keys: list[str] = Field(default_factory=list)
    detected_disease_keys: list[str] = Field(default_factory=list)
    symptoms_observed: list[str] = Field(default_factory=list)
    environmental_conditions: dict | None = None
    photo_refs: list[str] = Field(default_factory=list)
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class TreatmentApplication(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    treatment_key: str = ""
    plant_key: str = ""
    applied_at: datetime | None = None
    dosage: float | None = Field(default=None, gt=0)
    water_volume_liters: float | None = Field(default=None, gt=0)
    efficacy_rating: EfficacyRating | None = None
    applied_by: str = Field(default="", max_length=200)
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
