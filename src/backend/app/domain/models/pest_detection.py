"""REQ-044 §5 — persistiertes Datenmodell der Schädlingserkennung.

Es wird **kein Bild** dauerhaft gespeichert (§8): nur Hash + Findings +
Provenienz bleiben. ``PestFeedback`` deckt die Human-in-the-Loop-Schleife (§5.3)
ab — Quelle für Kalibrierung (WP-5) und den Aufbau des Indoor-Datensets (WP-3).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import (
    PestDetectionNextStep,
    PestDetectionSource,
    PestDetectionTrigger,
)
from app.domain.interfaces.pest_detection_adapter import PestFinding


class PestFeedback(BaseModel):
    """REQ-044 §5.3 — Nutzer-Feedback pro Finding (HITL)."""

    finding_label: str
    confirmed: bool
    actual_label: str | None = None
    was_beneficial: bool = False
    created_at: datetime | None = None


class PestDetection(BaseModel):
    """A persisted pest-detection request (no user image retained, §8)."""

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    user_key: str = ""
    plant_instance_key: str | None = None
    planting_run_key: str | None = None
    source: PestDetectionSource = PestDetectionSource.LOCAL_SYMPTOM
    adapter_key: str = ""
    is_confident: bool = True
    trigger: PestDetectionTrigger = PestDetectionTrigger.USER_PHOTO
    findings: list[PestFinding] = Field(default_factory=list)
    tiles_processed: int = 0
    suggested_next_step: PestDetectionNextStep = PestDetectionNextStep.NONE
    llm_explanation: str | None = None  # optional Phase 2 (RAG-(V)LM, WP-6)
    image_hash: str = ""  # SHA-256, Bild selbst nicht persistiert
    image_deleted_at: datetime | None = None
    disclaimer: str = ""
    feedback: list[PestFeedback] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
