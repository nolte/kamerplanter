"""REQ-036 §3 — request/response schemas for the KI diagnosis endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.domain.interfaces.knowledge_service import ConfidenceLevel


class SymptomSchema(BaseModel):
    """One curated symptom offered by the wizard's first step."""

    slug: str
    category: str
    label: str
    common_causes_hint: str = ""
    applicable_phases: list[str] = Field(default_factory=list)


class SymptomListResponse(BaseModel):
    symptoms: list[SymptomSchema] = Field(default_factory=list)


class SourceRefSchema(BaseModel):
    source_key: str
    source_type: str
    title: str = ""
    score: float = 0.0
    language: str = "de"


class MatchedTreatmentSchema(BaseModel):
    key: str
    name: str
    name_de: str | None = None
    treatment_type: str = ""
    safety_interval_days: int = 0
    has_karenz: bool = False
    detail_url: str


class DiagnosisCandidateSchema(BaseModel):
    rank: int
    name: str
    scientific_name: str | None = None
    category: str = ""
    confidence: float = 0.0
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    explanation: str = ""
    recommended_actions: list[str] = Field(default_factory=list)
    matched_pest_key: str | None = None
    matched_pest_detail_url: str | None = None
    matched_disease_key: str | None = None
    matched_disease_detail_url: str | None = None
    matched_treatments: list[MatchedTreatmentSchema] = Field(default_factory=list)


class DiagnoseRequest(BaseModel):
    """The wizard's analyse payload (§3)."""

    symptom_slugs: list[str] = Field(min_length=1, max_length=20)
    extra_notes: str | None = Field(default=None, max_length=2000)
    plant_instance_key: str | None = None
    photo_ref: str | None = Field(default=None, max_length=200)
    language: str = Field(default="de", pattern="^(de|en)$")


class DiagnosisResultSchema(BaseModel):
    """The top-3 diagnosis envelope rendered inside ``<AIResponse>``."""

    candidates: list[DiagnosisCandidateSchema] = Field(default_factory=list)
    answer_summary: str = ""
    sources: list[SourceRefSchema] = Field(default_factory=list)
    language: str = "de"
    uses_tenant_data: bool = False
    uses_cloud_provider: bool = False
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    model_name: str = ""
    provider_type: str = ""
    kb_version: str | None = None
    status: str = "ok"
    error_class: str | None = None
