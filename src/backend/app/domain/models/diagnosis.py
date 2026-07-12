"""REQ-036 — domain models for the structured KI diagnosis assistant.

This is the *symptom-based* structured assistant (distinct from the REQ-038 CV
image classifier). The flow is stateless: a caller submits a set of catalogue
symptoms plus optional plant context, the Knowledge-Service reasons over the RAG
base, and the backend returns the **top-3 candidate diagnoses** enriched with a
bridge to the existing REQ-010 IPM stammdaten (pests / diseases / treatments).

No ArangoDB collection backs these models — nothing is persisted beyond the
privacy-preserving ``ai_audit_log`` entry written by the REQ-031 foundation.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from app.domain.interfaces.knowledge_service import ConfidenceLevel
from app.domain.models.ai_assistant import SourceReference


class SymptomCategory(StrEnum):
    """The seven curated symptom groups (REQ-036 §2.1)."""

    LEAF_COLOR_CHANGE = "leaf_color_change"
    LEAF_SHAPE_CHANGE = "leaf_shape_change"
    GROWTH_ANOMALY = "growth_anomaly"
    PEST_VISIBLE = "pest_visible"
    DISEASE_VISIBLE = "disease_visible"
    FLOWERING_ISSUE = "flowering_issue"
    ENVIRONMENTAL = "environmental"


class SymptomCatalogEntry(BaseModel):
    """A single curated symptom the wizard offers for selection."""

    slug: str
    category: SymptomCategory
    label_de: str
    label_en: str
    applicable_phases: list[str] = Field(default_factory=list)
    common_causes_hint_de: str = ""
    common_causes_hint_en: str = ""


class LlmDiagnosis(BaseModel):
    """One raw candidate as parsed from the (JSON-constrained) LLM answer.

    The Knowledge-Service is prompted to emit a ``diagnoses`` array of these; the
    backend validates every item against this schema before enriching it.
    """

    name: str = Field(min_length=1, max_length=200)
    scientific_name: str | None = Field(default=None, max_length=200)
    category: str = Field(default="", max_length=60)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    explanation: str = ""
    recommended_actions: list[str] = Field(default_factory=list)


class MatchedTreatment(BaseModel):
    """A REQ-010 treatment suggested for a matched pest (bridge, read-only)."""

    key: str
    name: str
    name_de: str | None = None
    treatment_type: str = ""
    safety_interval_days: int = 0
    has_karenz: bool = False
    detail_url: str


class DiagnosisCandidate(BaseModel):
    """An enriched top-N diagnosis returned to the client (IPM-bridged)."""

    rank: int
    name: str
    scientific_name: str | None = None
    category: str = ""
    confidence: float = 0.0
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    explanation: str = ""
    recommended_actions: list[str] = Field(default_factory=list)
    # ── IPM bridge (REQ-010) ──
    matched_pest_key: str | None = None
    matched_pest_detail_url: str | None = None
    matched_disease_key: str | None = None
    matched_disease_detail_url: str | None = None
    matched_treatments: list[MatchedTreatment] = Field(default_factory=list)


DiagnosisStatus = str  # "ok" | "knowledge_service_error" | "error"


class DiagnosisResult(BaseModel):
    """REQ-036 — the full diagnosis envelope rendered inside ``<AIResponse>``."""

    candidates: list[DiagnosisCandidate] = Field(default_factory=list)
    answer_summary: str = ""
    sources: list[SourceReference] = Field(default_factory=list)
    language: str = "de"
    uses_tenant_data: bool = False
    uses_cloud_provider: bool = False
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    model_name: str = ""
    provider_type: str = ""
    kb_version: str | None = None
    status: DiagnosisStatus = "ok"
    error_class: str | None = None
