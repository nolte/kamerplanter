"""REQ-017 Propagation service scaffold."""

from __future__ import annotations

from typing import Any

from app.domain.models.propagation import PropagationEvent


class PropagationService:
    """Scaffold service — pins the public surface for REQ-017."""

    def __init__(self, repo: Any | None = None) -> None:
        self._repo = repo

    def record(self, event: PropagationEvent) -> PropagationEvent:
        raise NotImplementedError("REQ-017 PropagationService.record — pending follow-up.")

    def list_for_plant(self, plant_key: str) -> list[PropagationEvent]:
        raise NotImplementedError("REQ-017 PropagationService.list_for_plant — pending follow-up.")
