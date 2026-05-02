"""REQ-008 Post-Harvest service scaffold.

Orchestrates the curing / drying / storage workflow following a
HarvestBatch. Methods raise NotImplementedError until the REQ-008
implementation PR lands.
"""

from __future__ import annotations

from typing import Any

from app.domain.models.post_harvest import PostHarvestBatch


class PostHarvestService:
    """Scaffold service — pins the public surface for REQ-008."""

    def __init__(self, repo: Any | None = None) -> None:
        self._repo = repo

    def list_for_batch(self, harvest_batch_key: str) -> list[PostHarvestBatch]:
        """Return all post-harvest stages tracked for a HarvestBatch."""
        raise NotImplementedError("REQ-008 PostHarvestService.list_for_batch — pending follow-up.")

    def advance_stage(self, key: str, target_stage: str) -> PostHarvestBatch:
        """Advance a PostHarvestBatch to the next stage."""
        raise NotImplementedError("REQ-008 PostHarvestService.advance_stage — pending follow-up.")
