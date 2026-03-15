from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import datetime


class SlotCreate(BaseModel):
    slot_id: str
    location_key: str
    position: tuple[int, int] = (0, 0)
    capacity_plants: int = Field(default=1, ge=1, le=20)


class SlotResponse(BaseModel):
    key: str
    slot_id: str
    location_key: str
    position: tuple[int, int]
    capacity_plants: int
    currently_occupied: bool
    last_sanitization: datetime | None
    created_at: datetime | None = None
    updated_at: datetime | None = None
