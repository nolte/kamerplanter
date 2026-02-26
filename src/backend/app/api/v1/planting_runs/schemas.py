from datetime import date, datetime

from pydantic import BaseModel, Field

# ── Entry schemas ────────────────────────────────────────────────────

class EntryCreate(BaseModel):
    species_key: str
    cultivar_key: str | None = None
    quantity: int = Field(ge=1)
    role: str = "primary"
    id_prefix: str = Field(pattern=r"^[A-Z]{2,5}$")
    spacing_cm: float | None = Field(default=None, ge=0)
    notes: str | None = None


class EntryUpdate(BaseModel):
    species_key: str | None = None
    cultivar_key: str | None = None
    quantity: int | None = Field(default=None, ge=1)
    role: str | None = None
    id_prefix: str | None = Field(default=None, pattern=r"^[A-Z]{2,5}$")
    spacing_cm: float | None = Field(default=None, ge=0)
    notes: str | None = None


class EntryResponse(BaseModel):
    key: str
    run_key: str
    species_key: str
    cultivar_key: str | None
    quantity: int
    role: str
    id_prefix: str
    spacing_cm: float | None
    notes: str | None
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ── Run schemas ──────────────────────────────────────────────────────

class PlantingRunCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    run_type: str
    location_key: str | None = None
    substrate_batch_key: str | None = None
    planned_start_date: date | None = None
    source_plant_key: str | None = None
    notes: str | None = None
    entries: list[EntryCreate] | None = None


class PlantingRunUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    notes: str | None = None
    planned_start_date: date | None = None


class PlantingRunResponse(BaseModel):
    key: str
    name: str
    run_type: str
    status: str
    planned_quantity: int
    actual_quantity: int
    location_key: str | None
    substrate_batch_key: str | None
    planned_start_date: date | None
    started_at: datetime | None
    completed_at: datetime | None
    source_plant_key: str | None
    notes: str | None
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ── Batch operation schemas ──────────────────────────────────────────

class BatchCreatePlantsResponse(BaseModel):
    run_key: str
    created_count: int
    plant_keys: list[str]
    instance_ids: list[str]


class BatchTransitionRequest(BaseModel):
    target_phase_key: str
    target_phase_name: str
    exclude_keys: list[str] | None = None


class BatchTransitionResponse(BaseModel):
    run_key: str
    target_phase: str
    transitioned_count: int
    skipped_count: int
    failed_count: int
    transitioned_keys: list[str]
    skipped_keys: list[str]
    failed_keys: list[str]


class BatchRemoveRequest(BaseModel):
    reason: str = "batch_remove"


class BatchRemoveResponse(BaseModel):
    run_key: str
    removed_count: int
    removed_keys: list[str]


class DetachPlantRequest(BaseModel):
    reason: str


class PlantInRunResponse(BaseModel):
    key: str
    instance_id: str
    species_key: str
    cultivar_key: str | None
    plant_name: str | None
    planted_on: date
    removed_on: date | None
    current_phase: str
    detached_at: str | None = None
    detach_reason: str | None = None
