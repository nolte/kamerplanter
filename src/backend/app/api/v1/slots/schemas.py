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
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [{"thinning_to_cm": 5.0}, {"count": 24, "planted_on": "2026-05-02"}]},
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
    max_count: int


class SlotThinningResponse(BaseModel):
    """``POST /slots/{key}/thinning``: the plants the thinned slot now holds and the ``thinning`` care event."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"plant_keys": ["7710", "7711"], "instance_ids": ["B3_DAU_01", "B3_DAU_02"], "care_event_key": "6610"}
            ]
        }
    )

    plant_keys: list[str]
    instance_ids: list[str]
    care_event_key: str
