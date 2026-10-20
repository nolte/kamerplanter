from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, field_validator, model_validator

from app.api.v1.plant_instances.schemas import CultivarSummary, SpeciesSummary
from app.common.enums import DepthKind, LayoutStrategy, PlacementHint, PlanRole, RowDirection
from app.domain.models.planting_run import (
    MAX_DEPTH_CM,
    MAX_EDGE_MARGIN_CM,
    MAX_ROTATION_OVERRIDE_REASON,
    MAX_SPACING_CM,
    MIN_ROW_SPACING_CM,
    RUN_SOURCES,
    check_row_assignment,
)
from app.domain.services.planting_reservation_service import MAX_RESERVED_SLOTS

#: A mixed culture has at most this many species (one run each).
MAX_MIXED_CULTURE_RUNS = 12

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
    spacing_cm: float | None = Field(default=None, ge=0, le=MAX_SPACING_CM)
    row_spacing_cm: float | None = Field(default=None, ge=MIN_ROW_SPACING_CM, le=MAX_SPACING_CM)
    row_direction: RowDirection | None = None
    edge_margin_along_cm: float | None = Field(default=None, ge=0, le=MAX_EDGE_MARGIN_CM)
    edge_margin_across_cm: float | None = Field(default=None, ge=0, le=MAX_EDGE_MARGIN_CM)
    depth_cm: float | None = Field(default=None, ge=0, le=MAX_DEPTH_CM)
    depth_kind: DepthKind | None = None
    sowing_spacing_cm: float | None = Field(default=None, gt=0, le=MAX_SPACING_CM)
    thinning_to_cm: float | None = Field(default=None, gt=0, le=MAX_SPACING_CM)
    layout_strategy: LayoutStrategy | None = None
    placement_hint: PlacementHint | None = None
    row_assignment: list[int] | None = None
    notes: str | None = None

    @field_validator("row_assignment")
    @classmethod
    def validate_row_assignment(cls, value: list[int] | None) -> list[int] | None:
        return check_row_assignment(value)


class EntryUpdate(BaseModel):
    species_key: str | None = None
    cultivar_key: str | None = None
    quantity: int | None = Field(default=None, ge=1)
    id_prefix: str | None = Field(default=None, pattern=r"^[A-Z]{2,5}$")
    spacing_cm: float | None = Field(default=None, ge=0, le=MAX_SPACING_CM)
    row_spacing_cm: float | None = Field(default=None, ge=MIN_ROW_SPACING_CM, le=MAX_SPACING_CM)
    row_direction: RowDirection | None = None
    edge_margin_along_cm: float | None = Field(default=None, ge=0, le=MAX_EDGE_MARGIN_CM)
    edge_margin_across_cm: float | None = Field(default=None, ge=0, le=MAX_EDGE_MARGIN_CM)
    depth_cm: float | None = Field(default=None, ge=0, le=MAX_DEPTH_CM)
    depth_kind: DepthKind | None = None
    sowing_spacing_cm: float | None = Field(default=None, gt=0, le=MAX_SPACING_CM)
    thinning_to_cm: float | None = Field(default=None, gt=0, le=MAX_SPACING_CM)
    layout_strategy: LayoutStrategy | None = None
    placement_hint: PlacementHint | None = None
    row_assignment: list[int] | None = None
    notes: str | None = None

    @field_validator("row_assignment")
    @classmethod
    def validate_row_assignment(cls, value: list[int] | None) -> list[int] | None:
        return check_row_assignment(value)


class EntryResponse(BaseModel):
    key: str
    run_key: str
    species_key: str
    cultivar_key: str | None
    quantity: int
    id_prefix: str
    spacing_cm: float | None
    row_spacing_cm: float | None = None
    row_direction: RowDirection | None = None
    edge_margin_along_cm: float | None = None
    edge_margin_across_cm: float | None = None
    depth_cm: float | None = None
    depth_kind: DepthKind | None = None
    sowing_spacing_cm: float | None = None
    thinning_to_cm: float | None = None
    layout_strategy: LayoutStrategy | None = None
    placement_hint: PlacementHint | None = None
    row_assignment: list[int] | None = None
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
    # ── Garden plan (REQ-053 §16.3, §20.6, GP-FR-065/132) ──
    plan_role: PlanRole = PlanRole.MAIN_CROP
    rotation_override_reason: str | None = Field(default=None, max_length=MAX_ROTATION_OVERRIDE_REASON)
    reserved_area_m2: float | None = Field(default=None, gt=0)
    planned_from: date | None = Field(
        default=None, description="Start of the reservation window; defaults to `planned_start_date`."
    )
    planned_until: date | None = Field(
        default=None, description="End of the reservation window (inclusive); `null` = open."
    )
    source: str | None = Field(default=None, max_length=50, description="`manual`, `plan_editor`, `succession` …")

    @field_validator("plan_role")
    @classmethod
    def validate_plan_role(cls, value: PlanRole) -> PlanRole:
        if value is PlanRole.FALLOW:
            raise ValueError("A fallow period has no planting run.")
        return value

    @field_validator("source")
    @classmethod
    def validate_source(cls, value: str | None) -> str | None:
        if value is not None and value not in RUN_SOURCES:
            raise ValueError(f"source must be one of: {', '.join(sorted(RUN_SOURCES))}")
        return value

    @model_validator(mode="after")
    def validate_window(self) -> PlantingRunCreate:
        start = self.planned_from or self.planned_start_date
        if start and self.planned_until and self.planned_until < start:
            raise ValueError("planned_until must not lie before the start of the window.")
        return self


class MixedCultureRunCreate(BaseModel):
    """One species of a mixed culture: its run's name, its single entry and, for a `free` entry, its points."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "name": "Tomato – Raised bed 3",
                    "entry": {
                        "species_key": "412",
                        "quantity": 6,
                        "id_prefix": "TOM",
                        "spacing_cm": 50,
                        "layout_strategy": "rows",
                        "row_assignment": [0, 2],
                    },
                }
            ]
        },
    )

    name: str = Field(min_length=1, max_length=200)
    notes: str | None = Field(default=None, max_length=2000)
    entry: EntryCreate
    free_points: list[tuple[FiniteFloat, FiniteFloat]] = Field(
        default_factory=list,
        max_length=MAX_RESERVED_SLOTS,
        description="Bed-frame points of a `free` entry (m); each becomes a reserved position of the run.",
    )
    container_volume_l: float | None = Field(
        default=None, gt=0, allow_inf_nan=False, description="Pot volume of the freely placed positions, in litres."
    )

    @model_validator(mode="after")
    def validate_free_points_belong_to_a_free_entry(self) -> MixedCultureRunCreate:
        if (self.free_points or self.container_volume_l is not None) and self.entry.layout_strategy is not (
            LayoutStrategy.FREE
        ):
            raise ValueError("free_points and container_volume_l belong to an entry with layout_strategy `free`.")
        return self


class MixedCultureCreate(BaseModel):
    """Body of `POST /planting-runs/mixed-culture`: every run of a mixed culture on one bed, atomically (#2463)."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "location_key": "7710",
                    "planned_start_date": "2026-05-20",
                    "plan_role": "main_crop",
                    "source": "manual",
                    "runs": [
                        {
                            "name": "Tomato – Raised bed 3",
                            "entry": {
                                "species_key": "412",
                                "quantity": 6,
                                "id_prefix": "TOM",
                                "spacing_cm": 50,
                                "layout_strategy": "rows",
                                "row_assignment": [0, 2],
                            },
                        },
                        {
                            "name": "Basil – Raised bed 3",
                            "entry": {
                                "species_key": "415",
                                "quantity": 6,
                                "id_prefix": "BAS",
                                "spacing_cm": 25,
                                "layout_strategy": "rows",
                                "row_assignment": [1],
                            },
                        },
                    ],
                }
            ]
        },
    )

    location_key: str = Field(min_length=1, max_length=200, description="The bed all runs are planted in.")
    runs: list[MixedCultureRunCreate] = Field(
        min_length=1, max_length=MAX_MIXED_CULTURE_RUNS, description="One run per species, in the order of the dialog."
    )
    planned_start_date: date | None = None
    planned_from: date | None = Field(
        default=None, description="Start of the reservation window; defaults to `planned_start_date`."
    )
    planned_until: date | None = Field(
        default=None, description="End of the reservation window (inclusive); `null` = open."
    )
    plan_role: PlanRole = PlanRole.MAIN_CROP
    rotation_override_reason: str | None = Field(default=None, max_length=MAX_ROTATION_OVERRIDE_REASON)
    source: str | None = Field(default=None, max_length=50, description="`manual`, `plan_editor`, `succession` …")

    @field_validator("plan_role")
    @classmethod
    def validate_plan_role(cls, value: PlanRole) -> PlanRole:
        if value is PlanRole.FALLOW:
            raise ValueError("A fallow period has no planting run.")
        return value

    @field_validator("source")
    @classmethod
    def validate_source(cls, value: str | None) -> str | None:
        if value is not None and value not in RUN_SOURCES:
            raise ValueError(f"source must be one of: {', '.join(sorted(RUN_SOURCES))}")
        return value

    @model_validator(mode="after")
    def validate_window(self) -> MixedCultureCreate:
        start = self.planned_from or self.planned_start_date
        if start and self.planned_until and self.planned_until < start:
            raise ValueError("planned_until must not lie before the start of the window.")
        return self


class MixedCultureResponse(BaseModel):
    """The runs a mixed-culture request created, in the order of the request."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "runs": [
                        {
                            "key": "9311",
                            "name": "Tomato – Raised bed 3",
                            "run_type": "monoculture",
                            "status": "planned",
                            "planned_quantity": 6,
                            "actual_quantity": 0,
                            "location_key": "7710",
                            "substrate_batch_key": None,
                            "planned_start_date": "2026-05-20",
                            "started_at": None,
                            "completed_at": None,
                            "source_plant_key": None,
                            "notes": None,
                        }
                    ]
                }
            ]
        }
    )

    runs: list[PlantingRunResponse]


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
    plan_role: PlanRole = PlanRole.MAIN_CROP
    rotation_override_reason: str | None = None
    reserved_area_m2: float | None = None
    planned_from: date | None = None
    planned_until: date | None = None
    source: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ── Batch operation schemas ──────────────────────────────────────────


class BatchCreatePlantsRequest(BaseModel):
    """Body of `POST /planting-runs/{key}/create-plants`; the whole body is optional (GP-API-023)."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"assign_to_slots": True, "planted_on": "2026-05-20"}]})

    assign_to_slots: bool = Field(
        default=True,
        description=(
            "Place the plants on the slots the run reserved (`run_planned_at`, in `sequence` order per entry), "
            "then on free slots of the bed. `false` creates the plants without a slot."
        ),
    )
    planted_on: date | None = Field(default=None, description="Planting date; default today (UTC).")


class BatchCreatePlantsResponse(BaseModel):
    run_key: str
    created_count: int
    plant_keys: list[str]
    instance_ids: list[str]
    slots_assigned: int = 0
    assigned_slots: list[str] = Field(
        default_factory=list,
        description="Slot keys of the plants that got a slot, in the order of `plant_keys`.",
    )
    warnings: list[str] = Field(default_factory=list, description="Hints that never block; none yet.")


class PlanSlotsRequest(BaseModel):
    """Body of `POST /planting-runs/{key}/plan-slots` (GP-API-021)."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"entry_key": "9303", "slot_keys": ["8841", "8842"]}]})

    entry_key: str = Field(min_length=1, max_length=200)
    slot_keys: list[str] = Field(
        max_length=MAX_RESERVED_SLOTS,
        description="Ordered: the position is the `sequence` `create-plants` fills them in. Empty releases.",
    )


class ReservedSlotResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"slot_key": "8841", "sequence": 1}]})

    slot_key: str
    sequence: int


class PlanSlotsResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "run_key": "9302",
                    "entry_key": "9303",
                    "planned_from": "2026-10-05",
                    "planned_until": None,
                    "slots": [{"slot_key": "8841", "sequence": 1}, {"slot_key": "8842", "sequence": 2}],
                }
            ]
        }
    )

    run_key: str
    entry_key: str
    planned_from: date
    planned_until: date | None
    slots: list[ReservedSlotResponse]


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
    species: SpeciesSummary | None = None
    cultivar: CultivarSummary | None = None
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
