
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from app.common.enums import (
    HarvestIndicatorType,
    HarvestType,
    QualityGrade,
    RipenessStage,
)

if TYPE_CHECKING:
    from datetime import datetime


class HarvestIndicator(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    indicator_type: HarvestIndicatorType
    measurement_unit: str = Field(default="", max_length=50)
    measurement_method: str = Field(default="", max_length=200)
    observation_frequency: str = Field(default="daily", max_length=50)
    reliability_score: float = Field(default=0.5, ge=0, le=1)
    species_key: str | None = None
    description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class HarvestObservation(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    plant_key: str = ""
    observed_at: datetime | None = None
    observer: str = Field(default="", max_length=200)
    indicator_key: str = ""
    measurements: dict = Field(default_factory=dict)
    ripeness_assessment: RipenessStage = RipenessStage.IMMATURE
    days_to_harvest_estimate: int | None = Field(default=None, ge=0)
    photo_refs: list[str] = Field(default_factory=list)
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class HarvestBatch(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    batch_id: str = Field(default="", max_length=100)
    plant_key: str = ""
    harvest_date: datetime | None = None
    harvest_type: HarvestType = HarvestType.FINAL
    wet_weight_g: float | None = Field(default=None, ge=0)
    estimated_dry_weight_g: float | None = Field(default=None, ge=0)
    actual_dry_weight_g: float | None = Field(default=None, ge=0)
    quality_grade: QualityGrade | None = None
    harvester: str = Field(default="", max_length=200)
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class QualityAssessment(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    batch_key: str = ""
    assessed_at: datetime | None = None
    assessed_by: str = Field(default="", max_length=200)
    appearance_score: float = Field(default=0, ge=0, le=100)
    aroma_score: float = Field(default=0, ge=0, le=100)
    color_score: float = Field(default=0, ge=0, le=100)
    defects: list[str] = Field(default_factory=list)
    overall_score: float = Field(default=0, ge=0, le=100)
    grade: QualityGrade | None = None
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class YieldMetric(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    batch_key: str = ""
    yield_per_plant_g: float = Field(default=0, ge=0)
    yield_per_m2_g: float = Field(default=0, ge=0)
    total_yield_g: float = Field(default=0, ge=0)
    trim_waste_percent: float = Field(default=0, ge=0, le=100)
    usable_yield_g: float = Field(default=0, ge=0)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
