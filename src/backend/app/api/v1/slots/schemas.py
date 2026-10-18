from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import GeometrySource, SlotRole
from app.domain.models.garden_plan import SlotBatchRequest, SlotPatch
from app.domain.models.geometry import BedFrameGeometry

__all__ = ["ManualAdjacencyRequest", "SlotBatchRequest", "SlotBatchResponse", "SlotCreate", "SlotPatch", "SlotResponse"]


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
