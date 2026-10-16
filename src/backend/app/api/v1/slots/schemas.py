from datetime import date, datetime

from pydantic import BaseModel, Field

from app.common.enums import GeometrySource, SlotRole
from app.domain.models.geometry import BedFrameGeometry


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
