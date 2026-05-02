"""REQ-008 Post-Harvest data model (scaffold).

Captures the curing / drying / storage lifecycle that follows a
HarvestBatch. Concrete Pydantic fields will land with the REQ-008
implementation PR; this scaffold pins the model name + namespace so
the router and service can wire up.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

PostHarvestStage = Literal["drying", "curing", "stored", "released"]


class PostHarvestBatch(BaseModel):
    """REQ-008 v1.0 scaffold — links to a HarvestBatch and tracks stage."""

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    harvest_batch_key: str
    stage: PostHarvestStage = "drying"
    started_at: datetime | None = None
    completed_at: datetime | None = None
    notes: str | None = None

    model_config = {"populate_by_name": True}
