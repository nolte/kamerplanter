"""REQ-017 Propagation API request / response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import (
    GraftCompatibilityLevel,
    PhenotypeCategory,
    PropagationBatchStatus,
    PropagationEventStatus,
)
from app.domain.models.propagation import PropagationMethod

# ── Events ────────────────────────────────────────────────────────────────────


class PropagationEventCreate(BaseModel):
    method: PropagationMethod
    parent_plant_keys: list[str] = Field(default_factory=list)
    child_plant_keys: list[str] = Field(default_factory=list)
    species_key: str | None = None
    cultivar_key: str | None = None
    protocol_key: str | None = None
    batch_key: str | None = None
    quantity: int = Field(default=1, ge=1, le=1000)
    happened_at: datetime | None = None
    notes: str | None = None


class PropagationEventOutcomeRequest(BaseModel):
    survived_count: int = Field(ge=0)
    failure_reasons: list[str] = Field(default_factory=list)


class PropagationEventProgressRequest(BaseModel):
    callus_observed_at: datetime | None = None
    roots_observed_at: datetime | None = None
    transplant_ready_at: datetime | None = None


class PropagationEventResponse(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    method: PropagationMethod
    status: PropagationEventStatus
    parent_plant_keys: list[str]
    child_plant_keys: list[str]
    species_key: str | None = None
    cultivar_key: str | None = None
    protocol_key: str | None = None
    batch_key: str | None = None
    quantity: int
    survived_count: int | None = None
    success_rate: float | None = None
    callus_observed_at: datetime | None = None
    roots_observed_at: datetime | None = None
    transplant_ready_at: datetime | None = None
    failure_reasons: list[str] = Field(default_factory=list)
    happened_at: datetime | None = None
    notes: str | None = None

    model_config = {"populate_by_name": True}


# ── Batches ───────────────────────────────────────────────────────────────────


class PropagationBatchCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    method: PropagationMethod
    total_quantity: int = Field(default=0, ge=0)
    target_planting_run_key: str | None = None
    notes: str | None = None


class PropagationBatchUpdate(BaseModel):
    status: PropagationBatchStatus | None = None
    completed_at: datetime | None = None
    notes: str | None = None


class BatchFinalizeRequest(BaseModel):
    target_planting_run_key: str = Field(min_length=1)


class PropagationBatchResponse(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    name: str
    method: PropagationMethod
    status: PropagationBatchStatus
    total_quantity: int
    total_survived: int | None = None
    overall_success_rate: float | None = None
    target_planting_run_key: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    notes: str | None = None

    model_config = {"populate_by_name": True}


# ── Protocols ─────────────────────────────────────────────────────────────────


class RootingProtocolCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    method: PropagationMethod
    medium: str | None = None
    is_template: bool = False
    recommended_species_keys: list[str] = Field(default_factory=list)
    hormone_type: str | None = None
    hormone_concentration_ppm: float | None = Field(default=None, ge=0, le=10000)
    expected_root_days: int | None = Field(default=None, ge=0, le=365)
    instructions: str | None = None


class RootingProtocolResponse(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    name: str
    method: PropagationMethod
    medium: str | None = None
    is_template: bool
    is_global: bool = False
    recommended_species_keys: list[str] = Field(default_factory=list)
    hormone_type: str | None = None
    hormone_concentration_ppm: float | None = None
    expected_root_days: int | None = None
    instructions: str | None = None
    author: str | None = None

    model_config = {"populate_by_name": True}


class ProtocolStatsResponse(BaseModel):
    key: str | None = None
    event_count: int = 0
    total_quantity: int = 0
    total_survived: int | None = 0
    success_rate: float | None = None


# ── Mothers ───────────────────────────────────────────────────────────────────


class MotherDesignateRequest(BaseModel):
    priority: str | None = None


class MotherRetireRequest(BaseModel):
    reason: str | None = None


class MotherHealthRequest(BaseModel):
    health_score: int = Field(ge=0, le=100)


class MotherResponse(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    instance_id: str | None = None
    plant_name: str | None = None
    species_key: str | None = None
    is_mother: bool = False
    mother_priority: str | None = None
    mother_health_score: int | None = None
    mother_designated_at: datetime | None = None
    mother_retired_at: datetime | None = None
    mother_retire_reason: str | None = None

    model_config = {"populate_by_name": True, "extra": "ignore"}


# ── Phenotypes ────────────────────────────────────────────────────────────────


class PhenotypeNoteCreate(BaseModel):
    category: PhenotypeCategory = PhenotypeCategory.OTHER
    rating: int | None = Field(default=None, ge=0, le=10)
    note: str = Field(min_length=1, max_length=2000)
    observed_at: datetime | None = None


class PhenotypeNoteResponse(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    plant_key: str
    category: PhenotypeCategory
    rating: int | None = None
    note: str
    observed_at: datetime | None = None

    model_config = {"populate_by_name": True}


# ── Lineage ───────────────────────────────────────────────────────────────────


class LineageNode(BaseModel):
    key: str | None = None
    instance_id: str | None = None
    plant_name: str | None = None
    species_key: str | None = None


class LineageResponse(BaseModel):
    plant_key: str
    paths: list[list[str]]
    ancestors: list[LineageNode]


class DescendantsResponse(BaseModel):
    plant_key: str
    descendants: list[LineageNode]


class GraftCompatibilityResponse(BaseModel):
    scion_key: str
    rootstock_key: str
    scion_species_key: str
    rootstock_species_key: str
    compatible: bool
    level: GraftCompatibilityLevel
    same_genus: bool
    same_family: bool
    message: str


# ── Stats ─────────────────────────────────────────────────────────────────────


class PropagationStatRow(BaseModel):
    key: str | None = None
    event_count: int = 0
    total_quantity: int = 0
    total_survived: int | None = 0
    success_rate: float | None = None
