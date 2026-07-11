"""REQ-008 Post-Harvest API request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class StartDryingRequest(BaseModel):
    harvest_batch_key: str
    species_type: str = "flower"
    drying_method: str = "hang_dry"
    start_weight_g: float | None = Field(default=None, gt=0)
    target_moisture_percent: float = Field(default=10, ge=5, le=15)
    notes: str | None = None


class AdvanceStageRequest(BaseModel):
    target_stage: str


class DryingProgressCreate(BaseModel):
    current_weight_g: float = Field(gt=0)
    water_activity: float | None = Field(default=None, ge=0, le=1)
    co2_ppm: int | None = Field(default=None, ge=0)
    snap_test_passed: bool | None = None
    notes: str | None = None


class ObservationCreate(BaseModel):
    weight_g: float | None = Field(default=None, ge=0)
    temperature_c: float | None = None
    rh_percent: float | None = Field(default=None, ge=0, le=100)
    water_activity: float | None = Field(default=None, ge=0, le=1)
    co2_ppm: int | None = Field(default=None, ge=0)
    visual_condition: str = "good"
    aroma_quality: str = "good"
    defects_observed: list[str] = Field(default_factory=list)
    observer: str = ""
    notes: str | None = None


class PostHarvestBatchResponse(BaseModel):
    key: str
    harvest_batch_key: str
    plant_key: str
    stage: str
    species_type: str
    drying_method: str
    start_weight_g: float | None = None
    current_weight_g: float | None = None
    target_moisture_percent: float
    dryness_progress_percent: float
    ready_for_curing: bool
    snap_test_passed: bool | None = None
    water_activity: float | None = None
    storage_location: str | None = None
    pesticide_residue_status: str
    started_at: datetime | None = None
    drying_started_at: datetime | None = None
    curing_started_at: datetime | None = None
    stored_at: datetime | None = None
    released_at: datetime | None = None
    completed_at: datetime | None = None
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class DryingProgressResponse(BaseModel):
    key: str
    batch_key: str
    start_weight_g: float
    current_weight_g: float
    target_weight_g: float
    weight_loss_percent: float
    dryness_progress_percent: float
    snap_test_ready: bool
    snap_test_passed: bool | None = None
    over_dried: bool
    estimated_days_remaining: int
    next_action: str
    water_activity: float | None = None
    co2_ppm_current: int | None = None
    recorded_at: datetime | None = None
    notes: str | None = None


class StorageObservationResponse(BaseModel):
    key: str
    batch_key: str
    weight_g: float | None = None
    temperature_c: float | None = None
    rh_percent: float | None = None
    water_activity: float | None = None
    co2_ppm: int | None = None
    visual_condition: str
    aroma_quality: str
    defects_observed: list[str]
    observer: str
    notes: str | None = None
    observed_at: datetime | None = None


class MoldAlertResponse(BaseModel):
    key: str
    batch_key: str
    severity: str
    trigger_reason: str
    affected_location: str
    action_taken: str | None = None
    triggered_at: datetime | None = None
    resolved_at: datetime | None = None


class PostHarvestBatchDetailResponse(BaseModel):
    batch: PostHarvestBatchResponse
    latest_drying_progress: DryingProgressResponse | None = None
    open_mold_alerts: int = 0
