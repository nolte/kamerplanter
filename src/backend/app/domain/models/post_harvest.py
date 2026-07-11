"""REQ-008 Post-Harvest domain models.

Captures the per-batch drying / curing / storage lifecycle that follows a
HarvestBatch (REQ-007). REQ-008 §5 (U-006) chooses a *dedicated* per-batch state
machine (``fresh`` is skipped here — a batch enters tracking at ``drying``)
because one plant instance can spawn several batches (partial harvest). REQ-003
tracks the plant lifecycle; REQ-008 tracks the batch lifecycle.

All documents are tenant-scoped (REQ-024): ``PostHarvestBatch`` carries the
``tenant_key`` and the child documents (drying progress, observations, mold
alerts, burping events) are reached only through a tenant-owned batch.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import (
    DryingMethod,
    MoldAlertSeverity,
    PesticideResidueStatus,
    PostHarvestSpeciesType,
    PostHarvestStage,
    StorageAromaQuality,
    StorageVisualCondition,
)


class PostHarvestBatch(BaseModel):
    """REQ-008 v1.0 — a harvest batch progressing through post-harvest stages."""

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    harvest_batch_key: str
    plant_key: str = ""
    stage: PostHarvestStage = PostHarvestStage.DRYING
    species_type: PostHarvestSpeciesType = PostHarvestSpeciesType.FLOWER
    drying_method: DryingMethod = DryingMethod.HANG_DRY

    # Drying tracking (REQ-008 §3 DryingProtocol)
    start_weight_g: float | None = Field(default=None, gt=0)
    current_weight_g: float | None = Field(default=None, gt=0)
    target_moisture_percent: float = Field(default=10, ge=5, le=15)
    dryness_progress_percent: float = Field(default=0, ge=0, le=100)
    ready_for_curing: bool = False
    snap_test_passed: bool | None = None
    water_activity: float | None = Field(default=None, ge=0, le=1)

    # Storage / compliance
    storage_location: str | None = None
    pesticide_residue_status: PesticideResidueStatus = PesticideResidueStatus.UNTESTED

    # Stage timestamps (REQ-008 §5 U-006 batch-status machine)
    started_at: datetime | None = None
    drying_started_at: datetime | None = None
    curing_started_at: datetime | None = None
    stored_at: datetime | None = None
    released_at: datetime | None = None
    completed_at: datetime | None = None

    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class DryingProgress(BaseModel):
    """REQ-008 §2 :DryingProgress — one weight-based drying measurement."""

    key: str | None = Field(default=None, alias="_key")
    batch_key: str = ""
    start_weight_g: float = Field(gt=0)
    current_weight_g: float = Field(gt=0)
    target_weight_g: float = Field(default=0, ge=0)
    weight_loss_percent: float = Field(default=0, ge=0, le=100)
    dryness_progress_percent: float = Field(default=0, ge=0, le=100)
    snap_test_ready: bool = False
    snap_test_passed: bool | None = None
    over_dried: bool = False
    estimated_days_remaining: int = Field(default=0, ge=0)
    next_action: str = ""
    water_activity: float | None = Field(default=None, ge=0, le=1)
    co2_ppm_current: int | None = Field(default=None, ge=0)
    recorded_at: datetime | None = None
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class StorageObservation(BaseModel):
    """REQ-008 §2 :StorageObservation — an environmental/condition reading."""

    key: str | None = Field(default=None, alias="_key")
    batch_key: str = ""
    weight_g: float | None = Field(default=None, ge=0)
    temperature_c: float | None = None
    rh_percent: float | None = Field(default=None, ge=0, le=100)
    water_activity: float | None = Field(default=None, ge=0, le=1)
    co2_ppm: int | None = Field(default=None, ge=0)
    visual_condition: StorageVisualCondition = StorageVisualCondition.GOOD
    aroma_quality: StorageAromaQuality = StorageAromaQuality.GOOD
    defects_observed: list[str] = Field(default_factory=list)
    photo_refs: list[str] = Field(default_factory=list)
    observer: str = Field(default="", max_length=200)
    notes: str | None = None
    observed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class MoldAlert(BaseModel):
    """REQ-008 §2 :MoldAlert — auto-raised warning on RH/a_w excursion."""

    key: str | None = Field(default=None, alias="_key")
    batch_key: str = ""
    severity: MoldAlertSeverity = MoldAlertSeverity.WARNING
    trigger_reason: str = Field(default="", max_length=300)
    affected_location: str = Field(default="", max_length=200)
    action_taken: str | None = None
    triggered_at: datetime | None = None
    resolved_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class BurpingEvent(BaseModel):
    """REQ-008 §2 :BurpingEvent — a jar-venting event during curing."""

    key: str | None = Field(default=None, alias="_key")
    batch_key: str = ""
    duration_minutes: int = Field(default=0, ge=0)
    jar_rh_before: int | None = Field(default=None, ge=0, le=100)
    jar_rh_after: int | None = Field(default=None, ge=0, le=100)
    condensation_observed: bool = False
    aroma_notes: str | None = None
    burped_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
