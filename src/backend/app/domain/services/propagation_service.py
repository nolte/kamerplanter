"""REQ-017 Propagation service.

Only the D10-necessary minimal cut is implemented: persisting a single
``PropagationEvent`` (the monocarpic-mother→clonal-pup event). The listing /
full lineage-traversal surface stays a REQ-017 follow-up (out of scope, R12).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from app.domain.models.propagation import PropagationEvent


class _PropagationEventStore(Protocol):
    """Minimal persistence surface the service needs (a bound repository)."""

    def create(self, model: PropagationEvent) -> PropagationEvent: ...


class PropagationService:
    """Records propagation events. D10 uses only :meth:`record`."""

    def __init__(self, repo: _PropagationEventStore | None = None) -> None:
        self._repo = repo

    def record(self, event: PropagationEvent) -> PropagationEvent:
        """Persist one propagation event, stamping ``happened_at`` when unset.

        No-op-safe: when no repository is wired the event is returned unpersisted,
        so the service stays usable in propagation-less contexts (e.g. tests that
        do not exercise persistence)."""
        if event.happened_at is None:
            event.happened_at = datetime.now(UTC)
        if self._repo is None:
            return event
        return self._repo.create(event)

    def list_for_plant(self, plant_key: str) -> list[PropagationEvent]:
        raise NotImplementedError("REQ-017 PropagationService.list_for_plant — pending follow-up.")
