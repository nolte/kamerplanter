from datetime import date, datetime

from pydantic import BaseModel, Field

# ── Phase summary ────────────────────────────────────────────────────


class PhaseSummary(BaseModel):
    dominant_phase: str | None = None
    dominant_phase_count: int = 0
    total_plant_count: int = 0
    all_phases: dict[str, int] = Field(default_factory=dict)


# ── Phase timeline ───────────────────────────────────────────────────


class PhaseTimelineEntry(BaseModel):
    phase_key: str
    phase_name: str
    display_name: str
    sequence_order: int
    typical_duration_days: int
    status: str  # "completed" | "current" | "projected"
    actual_entered_at: datetime | None = None
    actual_exited_at: datetime | None = None
    actual_duration_days: int | None = None
    projected_start: datetime | None = None
    projected_end: datetime | None = None


class SpeciesPhaseTimeline(BaseModel):
    species_key: str
    species_name: str | None = None
    lifecycle_key: str
    cycle_type: str | None = None
    plant_count: int
    phases: list[PhaseTimelineEntry]


# ── Entry schemas ────────────────────────────────────────────────────


class EntryCreate(BaseModel):
    species_key: str
    cultivar_key: str | None = None
    quantity: int = Field(ge=1)
    id_prefix: str = Field(pattern=r"^[A-Z]{2,5}$")
    spacing_cm: float | None = Field(default=None, ge=0)
    notes: str | None = None


class EntryUpdate(BaseModel):
    species_key: str | None = None
    cultivar_key: str | None = None
    quantity: int | None = Field(default=None, ge=1)
    id_prefix: str | None = Field(default=None, pattern=r"^[A-Z]{2,5}$")
    spacing_cm: float | None = Field(default=None, ge=0)
    notes: str | None = None


class EntryResponse(BaseModel):
    key: str
    run_key: str
    species_key: str
    cultivar_key: str | None
    quantity: int
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
    location_key: str | None = None
    notes: str | None = None
    planned_start_date: date | None = None


class PlantingRunResponse(BaseModel):
    key: str
    name: str
    run_type: str
    status: str
    planned_quantity: int
    actual_quantity: int
    current_phase_key: str | None = None
    current_phase_started_at: datetime | None = None
    lifecycle_config_key: str | None = None
    location_key: str | None
    substrate_batch_key: str | None
    planned_start_date: date | None
    started_at: datetime | None
    completed_at: datetime | None
    source_plant_key: str | None
    notes: str | None
    phase_summary: PhaseSummary | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ── Batch operation schemas ──────────────────────────────────────────


class BatchCreatePlantsResponse(BaseModel):
    run_key: str
    created_count: int
    plant_keys: list[str]
    instance_ids: list[str]
    slots_assigned: int = 0


class AdoptPlantsRequest(BaseModel):
    plant_keys: list[str] = Field(min_length=1)


class AdoptPlantsResponse(BaseModel):
    run_key: str
    adopted_count: int
    adopted_keys: list[str]
    skipped: list[dict]
    run_status: str
    run_phase: str | None


class RunTransitionRequest(BaseModel):
    target_phase_key: str
    target_phase_name: str = ""
    override_reason: str | None = None


class RunTransitionResponse(BaseModel):
    run_key: str
    previous_phase: str | None
    new_phase: str
    new_phase_name: str = ""
    transitioned_at: str


class BatchRemoveRequest(BaseModel):
    reason: str = "batch_remove"
    target_status: str | None = None  # "completed" or "cancelled"; None = auto


class BatchRemoveResponse(BaseModel):
    run_key: str
    removed_count: int
    removed_keys: list[str]
    final_status: str


class BatchUpdatePhaseDatesRequest(BaseModel):
    phase_key: str
    entered_at: datetime | None = None
    exited_at: datetime | None = None


class BatchUpdatePhaseDatesResponse(BaseModel):
    run_key: str
    phase_key: str
    updated_count: int
    skipped_count: int


class DetachPlantRequest(BaseModel):
    reason: str


class DetachPlantResponse(BaseModel):
    plant_key: str
    detached_from_run: str
    copied_phase: str | None
    standalone: bool


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


# ── Nutrient plan assignment schemas ─────────────────────────────────


class NutrientPlanAssignRequest(BaseModel):
    plan_key: str
    assigned_by: str = ""


class NutrientPlanAssignResponse(BaseModel):
    run_key: str
    plan_key: str
    edge_key: str


class ChannelCalendarEntry(BaseModel):
    channel_id: str
    label: str
    application_method: str
    phase_name: str
    dates: list[str] = Field(default_factory=list)
    times_per_day: int = 1


class WateringScheduleCalendarResponse(BaseModel):
    run_key: str
    has_schedule: bool
    plan_key: str | None = None
    plan_name: str | None = None
    schedule: dict | None = None
    dates: list[str] = Field(default_factory=list)
    channel_calendars: list[ChannelCalendarEntry] = Field(default_factory=list)
    times_per_day: int = 1
