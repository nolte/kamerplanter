from datetime import datetime

from pydantic import BaseModel


class TransitionRequest(BaseModel):
    target_phase_key: str
    reason: str = "manual"

class CurrentPhaseResponse(BaseModel):
    phase: str
    phase_key: str | None
    days_in_phase: int
    next_phase: str | None

class PhaseHistoryResponse(BaseModel):
    key: str
    phase_name: str
    entered_at: datetime
    exited_at: datetime | None
    actual_duration_days: int | None
    transition_reason: str
    performance_score: float | None
