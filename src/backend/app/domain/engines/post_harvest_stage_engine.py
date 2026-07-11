"""REQ-008 §5 (U-006) — post-harvest batch stage state machine.

A batch moves forward only: ``drying → curing → stored → released``. Backward
transitions (a batch cannot become wetter again) and stage skips are rejected.
The engine is pure (no I/O); the service applies it and persists the result.
"""

from __future__ import annotations

from app.common.enums import PostHarvestStage
from app.common.exceptions import InvalidStatusTransitionError

#: Forward order of the batch lifecycle. Index = progression rank.
STAGE_ORDER: list[PostHarvestStage] = [
    PostHarvestStage.DRYING,
    PostHarvestStage.CURING,
    PostHarvestStage.STORED,
    PostHarvestStage.RELEASED,
]


def stage_rank(stage: PostHarvestStage) -> int:
    """Return the forward-progression rank of ``stage``."""
    return STAGE_ORDER.index(stage)


def next_stage(current: PostHarvestStage) -> PostHarvestStage | None:
    """Return the immediate next stage, or ``None`` if already terminal."""
    rank = stage_rank(current)
    if rank + 1 >= len(STAGE_ORDER):
        return None
    return STAGE_ORDER[rank + 1]


def validate_transition(current: PostHarvestStage, target: PostHarvestStage) -> None:
    """Validate a forward, single-step transition.

    Raises :class:`InvalidStatusTransitionError` (HTTP 422) when the target is
    not exactly the next stage — this rejects backward transitions
    (``stored → curing``), no-op transitions and stage skips
    (``drying → stored``).
    """
    expected = next_stage(current)
    if expected is None or target != expected:
        raise InvalidStatusTransitionError(current.value, target.value)
