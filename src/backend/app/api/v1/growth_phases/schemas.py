
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from app.common.enums import StressTolerance

if TYPE_CHECKING:
    from datetime import datetime


class PhaseCreate(BaseModel):
    name: str
    display_name: str = ""
    description: str = ""
    lifecycle_key: str = ""
    typical_duration_days: int = Field(ge=1)
    sequence_order: int = Field(ge=0)
    is_terminal: bool = False
    allows_harvest: bool = False
    stress_tolerance: StressTolerance = StressTolerance.MEDIUM
    watering_interval_days: int | None = Field(default=None, ge=1, le=90)

class PhaseResponse(BaseModel):
    key: str
    name: str
    display_name: str
    description: str = ""
    lifecycle_key: str
    typical_duration_days: int
    sequence_order: int
    is_terminal: bool
    allows_harvest: bool
    stress_tolerance: StressTolerance
    watering_interval_days: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
