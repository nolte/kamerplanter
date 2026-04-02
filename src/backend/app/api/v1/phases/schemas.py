from datetime import datetime

from pydantic import BaseModel


class TransitionRequest(BaseModel):
    target_phase_key: str
    reason: str = "manual"
    force: bool = False


class CurrentPhaseResponse(BaseModel):
    phase: str
    phase_key: str | None
    days_in_phase: int
    next_phase: str | None
    cycle_type: str | None = None
    cycle_number: int = 1
    has_harvest_phase: bool = False


class PhaseHistoryResponse(BaseModel):
    key: str
    phase_name: str
    entered_at: datetime
    exited_at: datetime | None
    actual_duration_days: int | None
    transition_reason: str
    performance_score: float | None


class PhaseHistoryDateUpdate(BaseModel):
    entered_at: datetime | None = None
    exited_at: datetime | None = None
