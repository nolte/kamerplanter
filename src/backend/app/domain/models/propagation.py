"""REQ-017 Propagation / lineage domain models.

Tracks clones / seed crosses / grafts / divisions, the rooting protocols they
follow, the batches that group them, and the free-text phenotype notes recorded
against a plant instance. The genetic lineage itself is stored as the
``descended_from`` graph edge (child -> mother); these documents carry the
provenance metadata around each propagation action.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.common.enums import (
    PhenotypeCategory,
    PropagationBatchStatus,
    PropagationEventStatus,
)

#: Coarse propagation method as persisted on the event. ``clone`` is the D10
#: monocarpic-mother -> pup value and MUST stay valid (see PropagationService.record).
PropagationMethod = Literal[
    "clone",
    "seed",
    "cutting",
    "graft",
    "division",
    "layering",
    "offset",
    "other",
]


class PropagationEvent(BaseModel):
    """One propagation action with provenance.

    The D10 clone path only sets ``method`` / ``parent_plant_keys`` /
    ``child_plant_keys`` / ``happened_at``; every other field is optional so the
    minimal clone event stays valid while the full propagation surface can enrich
    the same document.
    """

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    method: PropagationMethod
    status: PropagationEventStatus = PropagationEventStatus.IN_PROGRESS
    parent_plant_keys: list[str] = Field(default_factory=list)
    child_plant_keys: list[str] = Field(default_factory=list)
    species_key: str | None = None
    cultivar_key: str | None = None
    protocol_key: str | None = None
    batch_key: str | None = None
    quantity: int = Field(default=1, ge=1, le=1000)
    survived_count: int | None = Field(default=None, ge=0)
    success_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    # ── Progress milestones (REQ-017 §3) ──
    callus_observed_at: datetime | None = None
    roots_observed_at: datetime | None = None
    transplant_ready_at: datetime | None = None
    failure_reasons: list[str] = Field(default_factory=list)
    happened_at: datetime | None = None
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class PropagationBatch(BaseModel):
    """Groups multiple propagation events started together (REQ-017 §2)."""

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    name: str = Field(min_length=1, max_length=200)
    method: PropagationMethod
    status: PropagationBatchStatus = PropagationBatchStatus.IN_PROGRESS
    total_quantity: int = Field(default=0, ge=0)
    total_survived: int | None = Field(default=None, ge=0)
    overall_success_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    target_planting_run_key: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class RootingProtocol(BaseModel):
    """Reusable rooting / propagation protocol template (REQ-017 seed data).

    ``tenant_key == ""`` marks a global system template; a non-empty value is a
    tenant-owned protocol. The hybrid catalog union (global + own tenant) is
    resolved in the repository.
    """

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    name: str = Field(min_length=1, max_length=200)
    method: PropagationMethod
    medium: str | None = None
    is_template: bool = False
    recommended_species_keys: list[str] = Field(default_factory=list)
    hormone_type: str | None = None
    hormone_concentration_ppm: float | None = Field(default=None, ge=0, le=10000)
    expected_root_days: int | None = Field(default=None, ge=0, le=365)
    instructions: str | None = None
    author: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class PhenotypeNote(BaseModel):
    """Free-text phenotype observation recorded against a plant instance (REQ-017)."""

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    plant_key: str
    category: PhenotypeCategory = PhenotypeCategory.OTHER
    rating: int | None = Field(default=None, ge=0, le=10)
    note: str = Field(min_length=1, max_length=2000)
    observed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
