from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from app.common.enums import DepthKind, LayoutStrategy, PlacementHint, PlantingRunStatus, PlantingRunType, RowDirection

#: GP-FR-060: ``spacing_cm`` / ``row_spacing_cm`` reach 1 500 cm (woody plants, orchards — W-004).
MAX_SPACING_CM = 1_500.0
#: GP-FR-060: ``spacing_cm`` / ``row_spacing_cm`` start at 5 cm (the layout calculator refuses less).
MIN_SPACING_CM = 5.0
MIN_ROW_SPACING_CM = MIN_SPACING_CM
#: GP-FR-060: ``edge_margin_along_cm`` / ``edge_margin_across_cm`` 0–200 cm.
MAX_EDGE_MARGIN_CM = 200.0
#: GP-FR-060: ``depth_cm`` 0–100 cm.
MAX_DEPTH_CM = 100.0

ALLOWED_STATUS_TRANSITIONS: dict[PlantingRunStatus, list[PlantingRunStatus]] = {
    PlantingRunStatus.PLANNED: [PlantingRunStatus.ACTIVE, PlantingRunStatus.CANCELLED],
    PlantingRunStatus.ACTIVE: [PlantingRunStatus.HARVESTING, PlantingRunStatus.COMPLETED, PlantingRunStatus.CANCELLED],
    PlantingRunStatus.HARVESTING: [PlantingRunStatus.COMPLETED, PlantingRunStatus.CANCELLED],
    PlantingRunStatus.COMPLETED: [],
    PlantingRunStatus.CANCELLED: [],
}


#: GP-FR-062: positions one layout may carry bound the rows an entry can name.
MAX_ROW_ASSIGNMENTS = 2_000


def check_row_assignment(value: list[int] | None) -> list[int] | None:
    """Row indices (0-based) an entry occupies: non-negative, distinct, at most :data:`MAX_ROW_ASSIGNMENTS`."""
    if value is None:
        return None
    if len(value) > MAX_ROW_ASSIGNMENTS:
        raise ValueError(f"row_assignment names at most {MAX_ROW_ASSIGNMENTS} rows")
    if any(index < 0 for index in value):
        raise ValueError("row_assignment holds row indices of 0 or more")
    if len(set(value)) != len(value):
        raise ValueError("row_assignment must not repeat a row")
    return value


class PlantingRunEntry(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    run_key: str = ""
    #: The owning tenant, copied from the parent run by ``PlantingRunService``
    #: (SEC-004, #1112).
    #:
    #: An entry is not independently addressable — every route reaches it through
    #: its run, which is tenant-verified — so this field carries no *access*
    #: decision. It exists because
    #: :meth:`BaseArangoRepository._verify_owned_references` compares a referenced
    #: document against **the row's own** ``tenant_key`` and skips a row that has
    #: none. Declaring ``cultivar_key`` as an owned reference without this field
    #: would ship a guard that never runs — the inertness #1112 warns about by
    #: name.
    tenant_key: str = ""
    species_key: str
    cultivar_key: str | None = None
    quantity: int = Field(ge=1)
    id_prefix: str = Field(pattern=r"^[A-Z]{2,5}$")
    #: The upper bound of 1 500 cm is enforced at the API (``EntryCreate``/``EntryUpdate``), not here: a stored
    #: entry that predates it must keep loading.
    spacing_cm: float | None = Field(default=None, ge=0)
    # ── Layout (REQ-053 GP-FR-060) — all optional: an entry without them has no planned layout ──
    row_spacing_cm: float | None = Field(default=None, ge=MIN_ROW_SPACING_CM, le=MAX_SPACING_CM)
    row_direction: RowDirection | None = None
    #: Distance of the first position from the start of a row; the layout defaults it to ``spacing / 2``.
    edge_margin_along_cm: float | None = Field(default=None, ge=0, le=MAX_EDGE_MARGIN_CM)
    #: Distance of the first row from the bed side; the layout defaults it to ``row_spacing / 2``.
    edge_margin_across_cm: float | None = Field(default=None, ge=0, le=MAX_EDGE_MARGIN_CM)
    depth_cm: float | None = Field(default=None, ge=0, le=MAX_DEPTH_CM)
    depth_kind: DepthKind | None = None
    #: Direct sowing: seed spacing in the row, and the spacing the seedlings are thinned to.
    sowing_spacing_cm: float | None = Field(default=None, gt=0, le=MAX_SPACING_CM)
    thinning_to_cm: float | None = Field(default=None, gt=0, le=MAX_SPACING_CM)
    layout_strategy: LayoutStrategy | None = None
    placement_hint: PlacementHint | None = None
    #: Row indices (0-based) this entry occupies when rows alternate between entries (GP-FR-070);
    #: ``None`` for a monoculture.
    row_assignment: list[int] | None = None
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @field_validator("row_assignment")
    @classmethod
    def validate_row_assignment(cls, value: list[int] | None) -> list[int] | None:
        return check_row_assignment(value)


class PlantingRun(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    name: str = Field(min_length=1, max_length=200)
    run_type: PlantingRunType
    status: PlantingRunStatus = PlantingRunStatus.PLANNED
    planned_quantity: int = Field(default=0, ge=0)
    actual_quantity: int = Field(default=0, ge=0)
    current_phase_key: str | None = None
    current_phase_started_at: datetime | None = None
    lifecycle_config_key: str | None = None
    location_key: str | None = None
    substrate_batch_key: str | None = None
    planned_start_date: date | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    source_plant_key: str | None = None
    nutrient_plan_key: str | None = None
    notes: str | None = None
    # REQ-013 §2 — succession (staggered sowing) linkage. Populated when the run
    # was generated by a SuccessionPlan; ``clone_from_run_key`` copies the
    # configuration of an existing run (not its plants).
    succession_plan_key: str | None = None
    clone_from_run_key: str | None = None
    succession_sequence: int | None = None
    succession_total: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_clone_has_source(self) -> PlantingRun:
        if self.run_type == PlantingRunType.CLONE and not self.source_plant_key:
            raise ValueError("Clone runs require a source_plant_key.")
        return self

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: PlantingRunStatus) -> PlantingRunStatus:
        if v not in PlantingRunStatus:
            raise ValueError(f"Invalid status: {v}")
        return v
