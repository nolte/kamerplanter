from datetime import datetime

from pydantic import BaseModel, Field


class HarvestIndicatorCreate(BaseModel):
    indicator_type: str
    measurement_unit: str = ""
    measurement_method: str = ""
    observation_frequency: str = "daily"
    reliability_score: float = 0.5
    species_key: str | None = None
    description: str | None = None


class HarvestIndicatorResponse(BaseModel):
    key: str
    indicator_type: str
    measurement_unit: str
    measurement_method: str
    observation_frequency: str
    reliability_score: float
    species_key: str | None = None
    description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ObservationCreate(BaseModel):
    indicator_key: str = ""
    observer: str = ""
    measurements: dict = Field(default_factory=dict)
    ripeness_assessment: str = "immature"
    days_to_harvest_estimate: int | None = None
    photo_refs: list[str] = Field(default_factory=list)
    notes: str | None = None


class ObservationResponse(BaseModel):
    key: str
    plant_key: str
    observed_at: datetime | None = None
    observer: str
    indicator_key: str
    measurements: dict
    ripeness_assessment: str
    days_to_harvest_estimate: int | None = None
    photo_refs: list[str]
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class HarvestBatchCreate(BaseModel):
    batch_id: str = ""
    harvest_type: str = "final"
    wet_weight_g: float | None = None
    estimated_dry_weight_g: float | None = None
    harvester: str = ""
    notes: str | None = None


class HarvestBatchUpdate(BaseModel):
    harvest_type: str | None = None
    wet_weight_g: float | None = None
    estimated_dry_weight_g: float | None = None
    actual_dry_weight_g: float | None = None
    quality_grade: str | None = None
    harvester: str | None = None
    notes: str | None = None


class HarvestBatchResponse(BaseModel):
    key: str
    batch_id: str
    plant_key: str
    harvest_date: datetime | None = None
    harvest_type: str
    wet_weight_g: float | None = None
    estimated_dry_weight_g: float | None = None
    actual_dry_weight_g: float | None = None
    quality_grade: str | None = None
    harvester: str
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class QualityAssessmentCreate(BaseModel):
    assessed_by: str = ""
    appearance_score: float = 0
    aroma_score: float = 0
    color_score: float = 0
    defects: list[str] = Field(default_factory=list)
    notes: str | None = None


class QualityAssessmentResponse(BaseModel):
    key: str
    batch_key: str
    assessed_at: datetime | None = None
    assessed_by: str
    appearance_score: float
    aroma_score: float
    color_score: float
    defects: list[str]
    overall_score: float
    grade: str | None = None
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class YieldMetricCreate(BaseModel):
    yield_per_plant_g: float = 0
    yield_per_m2_g: float = 0
    total_yield_g: float = 0
    trim_waste_percent: float = 0
    usable_yield_g: float = 0


class YieldMetricResponse(BaseModel):
    key: str
    batch_key: str
    yield_per_plant_g: float
    yield_per_m2_g: float
    total_yield_g: float
    trim_waste_percent: float
    usable_yield_g: float
    created_at: datetime | None = None
    updated_at: datetime | None = None
