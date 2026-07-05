"""Survival-rate / failure-cause analytics read models (REQ-003 G1).

Aggregates a tenant's plant instances so the UI can show how many plants
survived versus were lost, which termination outcome dominates, and — the key
REQ-003 ask — in which frozen growth phase most unplanned losses occur.

``survived`` counts every plant that was NOT an unplanned loss: harvested,
senesced, cancelled *and* still-growing instances all count as survived; only
``termination_type='died'`` is a loss. The raw breakdowns are exposed so a
consumer can recompute the rate under a different definition.
"""

from pydantic import BaseModel, Field

from app.common.enums import TerminationCause, TerminationType


class TerminationTypeCount(BaseModel):
    """Number of terminated instances per ``termination_type``."""

    termination_type: TerminationType
    count: int = Field(ge=0)


class TerminationCauseCount(BaseModel):
    """Number of unplanned losses per ``termination_cause`` (died only)."""

    termination_cause: TerminationCause
    count: int = Field(ge=0)


class PhaseLossCount(BaseModel):
    """Number of unplanned losses that occurred in a frozen growth phase.

    Counts are aggregated by the resolved phase *name* (not key), so the same
    canonical phase across different species' lifecycles is summed together.
    An empty ``phase_name`` denotes losses of instances that had no phase set.
    """

    phase_name: str
    count: int = Field(ge=0)


class SurvivalStats(BaseModel):
    """Aggregated survival / failure-cause statistics for one tenant (REQ-003 G1)."""

    total: int = Field(ge=0, description="All plant instances of the tenant.")
    terminated: int = Field(ge=0, description="Instances with any termination_type set.")
    active: int = Field(ge=0, description="Still-growing instances (total minus terminated).")
    died: int = Field(ge=0, description="Instances lost to an unplanned death.")
    survived: int = Field(ge=0, description="Instances that were NOT an unplanned death (total minus died).")
    survival_rate: float = Field(
        ge=0,
        le=1,
        description="survived / total as a fraction in [0, 1]; 0 when there are no instances.",
    )
    by_termination_type: list[TerminationTypeCount] = Field(default_factory=list)
    by_termination_cause: list[TerminationCauseCount] = Field(default_factory=list)
    loss_by_phase: list[PhaseLossCount] = Field(
        default_factory=list,
        description="Unplanned losses grouped by frozen growth phase, most-affected phase first.",
    )
