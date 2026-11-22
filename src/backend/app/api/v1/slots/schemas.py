from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import GeometrySource, SlotRole
from app.domain.models.garden_plan import SlotBatchRequest, SlotPatch
from app.domain.models.geometry import BedFrameGeometry
from app.domain.models.planting_reservation import SlotThinningInput

__all__ = [
    "ManualAdjacencyRequest",
    "SlotBatchRequest",
    "SlotBatchResponse",
    "SlotCreate",
    "SlotPatch",
    "SlotResponse",
    "SlotSowingRequest",
    "SlotThinningPlanResponse",
    "SlotThinningRequest",
    "SlotThinningResponse",
]


class SlotCreate(BaseModel):
    slot_id: str
    location_key: str
    capacity_plants: int = Field(default=1, ge=1, le=20)


class SlotResponse(BaseModel):
    key: str
    slot_id: str
    location_key: str
    capacity_plants: int
    currently_occupied: bool
    last_sanitization: datetime | None
    # ── Garden plan (REQ-053 §20.5, WP 1.7) — read-only here; the editor writes them (WP 1.8/1.9) ──
    slot_role: SlotRole = SlotRole.POSITION
    #: In the bed frame of the slot's location (§9.2, coordinates may be negative); ``None`` = unplaced.
    geometry: BedFrameGeometry | None = None
    row_index: int | None = None
    sequence: int | None = None
    geometry_source: GeometrySource | None = None
    container_volume_l: float | None = None
    sown_at: date | None = None
    #: Thinning day of a zone recorded as a target stand (§11.3 "Zonen-Bestand", #2862); ``None`` otherwise.
    thinned_at: date | None = None
    archived_at: datetime | None = None
    planned_spacing_cm: float | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SlotBatchResponse(BaseModel):
    """What ``POST /locations/{key}/slots/batch`` did (GP-API-015)."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"created_keys": ["slot_1", "slot_2"], "deleted_count": 4, "kept_count": 1}]}
    )

    #: Keys of the created slots, in the order of the request's ``slots``.
    created_keys: list[str]
    deleted_count: int
    #: Slots of the bed that were left as they were (occupied, reserved, archived, or all of them on ``append``).
    kept_count: int


class ManualAdjacencyRequest(BaseModel):
    """Body of ``PUT /slots/{key}/adjacent/{other_key}`` (SR-021)."""

    model_config = ConfigDict(extra="forbid", json_schema_extra={"examples": [{"distance_cm": 35.0}]})

    #: Centre distance to record on the edge; ``None`` leaves it unset (the geometry is not consulted).
    distance_cm: float | None = Field(default=None, ge=0, le=100_000)


class SlotSowingRequest(BaseModel):
    """Body of ``PUT /slots/{key}/sowing``: the day a ``row``/``zone`` slot was sown (REQ-053 §11.3, W-015)."""

    model_config = ConfigDict(extra="forbid", json_schema_extra={"examples": [{"sown_at": "2026-04-12"}]})

    sown_at: date


class SlotThinningRequest(SlotThinningInput):
    """Body of ``POST /slots/{key}/thinning`` (REQ-053 §11.3, W-015).

    ``thinning_to_cm`` overrides the run's spacing for this count, ``count`` the computed number. Without a spacing on
    the run or here and without a count the request is refused (422 ``thinning.spacing_required``) — no default.
    ``row_spacing_cm`` (5–1 500 cm, zones only, #2862) replaces the run's / species profile's row spacing; ``null``
    counts the zone on the square-grid estimate; leaving it out takes the run's, else the species profile's value.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {"thinning_to_cm": 5.0},
                {"thinning_to_cm": 4.0, "row_spacing_cm": 25.0},
                {"count": 24, "planted_on": "2026-05-02"},
            ]
        },
    )


class SlotThinningPlanResponse(BaseModel):
    """``GET /slots/{key}/thinning``: what thinning the sown slot would do, before the grower confirms."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "slot_key": "8841",
                    "slot_id": "BEET3_R01",
                    "slot_role": "row",
                    "sown_at": "2026-04-12",
                    "run_key": "9302",
                    "entry_key": "9303",
                    "species_key": "5120",
                    "cultivar_key": None,
                    "measure_kind": "length",
                    "measure_value": 1.2,
                    "thinning_to_cm": 5.0,
                    "suggested_count": 24,
                    "max_count": 500,
                    "max_stand_count": None,
                    "row_spacing_cm": None,
                    "row_spacing_source": None,
                    "species_row_spacing_cm": "20-30",
                    "count_formula": "along_row",
                }
            ]
        }
    )

    slot_key: str
    slot_id: str
    slot_role: SlotRole
    sown_at: date
    run_key: str
    entry_key: str
    species_key: str
    cultivar_key: str | None = None
    measure_kind: Literal["length", "area"] | None = Field(
        default=None, description="`length` (m) for a row, `area` (m²) for a zone; `null` without a geometry."
    )
    measure_value: float | None = None
    thinning_to_cm: float | None = Field(
        default=None, description="The run entry's spacing after thinning; `null` when the run has none."
    )
    suggested_count: int | None = Field(
        default=None, description="Plants for `thinning_to_cm` over the measure; `null` without either."
    )
    max_count: int = Field(description="The most single plants one thinning creates (GP-NFR-017).")
    max_stand_count: int | None = Field(
        default=None,
        description=(
            "Zones only: a count above `max_count` is recorded as a target stand of at most this many plants instead "
            "of single plants (#2862); `null` for a row."
        ),
    )
    row_spacing_cm: float | None = Field(
        default=None,
        description=(
            "Row spacing a zone is counted with: the run entry's, else the lower value of the species profile's range; "
            "`null` without either (square-grid estimate)."
        ),
    )
    row_spacing_source: Literal["run", "species"] | None = Field(
        default=None, description="Where `row_spacing_cm` came from; `null` when there is none."
    )
    species_row_spacing_cm: str | None = Field(
        default=None, description="The species profile's row spacing as stored (a range like `20-30`), for display."
    )
    count_formula: Literal["along_row", "rows", "square_grid"] | None = Field(
        default=None,
        description=(
            "The rule behind `suggested_count`: one plant per spacing along a row, row spacing x in-row spacing, or "
            "the square-grid estimate; `null` without a measure."
        ),
    )


class SlotThinningResponse(BaseModel):
    """``POST /slots/{key}/thinning``: the plants the thinned slot now holds and the ``thinning`` care event.

    A zone above the quota of single plants holds a target stand instead (#2862): ``plant_keys`` and ``instance_ids``
    are empty and ``stand_quantity`` is the count recorded on the run.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "plant_keys": ["7710", "7711"],
                    "instance_ids": ["B3_DAU_01", "B3_DAU_02"],
                    "care_event_key": "6610",
                    "stand_quantity": None,
                },
                {"plant_keys": [], "instance_ids": [], "care_event_key": "6611", "stand_quantity": 1250},
            ]
        }
    )

    plant_keys: list[str]
    instance_ids: list[str]
    care_event_key: str
    stand_quantity: int | None = Field(
        default=None,
        description="Target stand a zone above the quota recorded instead of single plants; `null` when plants stand.",
    )
