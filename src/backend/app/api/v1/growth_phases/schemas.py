from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import StressTolerance


class PhaseCreate(BaseModel):
    name: str
    display_name: str = ""
    lifecycle_key: str = ""
    typical_duration_days: int = Field(ge=1)
    sequence_order: int = Field(ge=0)
    is_terminal: bool = False
    allows_harvest: bool = False
    stress_tolerance: StressTolerance = StressTolerance.MEDIUM

class PhaseResponse(BaseModel):
    key: str
    name: str
    display_name: str
    lifecycle_key: str
    typical_duration_days: int
    sequence_order: int
    is_terminal: bool
    allows_harvest: bool
    stress_tolerance: StressTolerance
    created_at: datetime | None = None
    updated_at: datetime | None = None
