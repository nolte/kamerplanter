"""REQ-017 Propagation / lineage scaffold.

Tracks clones / seed crosses / grafts / divisions and the genetic
lineage edges that connect them. Concrete domain model lands with
the REQ-017 implementation PR.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

PropagationMethod = Literal["clone", "seed", "graft", "division"]


class PropagationEvent(BaseModel):
    """REQ-017 v1.0 scaffold — one propagation event with provenance."""

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    method: PropagationMethod
    parent_plant_keys: list[str] = Field(default_factory=list)
    child_plant_keys: list[str] = Field(default_factory=list)
    happened_at: datetime | None = None
    notes: str | None = None

    model_config = {"populate_by_name": True}
