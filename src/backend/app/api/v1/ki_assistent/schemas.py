"""REQ-031 §5.5 — request/response schemas for the KI-Assistent API."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.domain.interfaces.knowledge_service import ConfidenceLevel


class AiStatusResponse(BaseModel):
    """Public feature-availability payload for the KI-Assistent (issue #685).

    Mirrors ``settings.ai_features_enabled`` so the frontend can hide the
    KI-Assistent nav entry and degrade its page instead of hitting the
    404 that the feature-flag guard returns when AI is off cluster-wide.
    """

    available: bool


class SourceRefSchema(BaseModel):
    """A cited knowledge chunk (Quellenpflicht)."""

    source_key: str
    source_type: str
    title: str = ""
    score: float = 0.0
    language: str = "de"


class AiResponseSchema(BaseModel):
    """The common KI answer envelope rendered by ``<AIResponse>`` (§5.5)."""

    answer_text: str
    sources: list[SourceRefSchema] = Field(default_factory=list)
    language: str = "de"
    language_mismatch_warning: bool = False
    uses_tenant_data: bool = False
    uses_cloud_provider: bool = False
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    fallback_species: str | None = None
    cultivar_hint: str | None = None
    model_name: str = ""
    provider_type: str = ""
    kb_version: str | None = None
    generated_at: datetime | None = None


class TipCardSchema(BaseModel):
    """A single tip card returned to the frontend."""

    key: str | None = None
    context_type: str
    context_key: str
    tip_type: str
    priority: str
    title: str
    body: str
    action_url: str | None = None
    sources: list[SourceRefSchema] = Field(default_factory=list)
    language: str = "de"
    language_mismatch_warning: bool = False
    uses_tenant_data: bool = False
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    model_name: str = ""
    generated_at: datetime | None = None


class TipListResponse(BaseModel):
    tips: list[TipCardSchema] = Field(default_factory=list)


class ExplainRequest(BaseModel):
    subject_type: Literal["task", "reminder", "phase_transition", "feeding_event"]
    subject_key: str = Field(min_length=1, max_length=200)
    question_template_id: str = Field(min_length=1, max_length=120)
    language: Literal["de", "en"] | None = None


class PublicAskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    language: Literal["de", "en"] | None = None


class ConversationCreateRequest(BaseModel):
    context_type: Literal["plant_instance", "planting_run", "general"] = "general"
    context_key: str | None = None
    language: Literal["de", "en"] | None = None


class ChatMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    language: Literal["de", "en"] | None = None


class ConversationSummary(BaseModel):
    key: str | None = None
    title: str | None = None
    context_type: str
    context_key: str | None = None
    message_count: int = 0
    updated_at: datetime | None = None


class ProviderSummary(BaseModel):
    """Provider info for the settings UI — never carries the API key."""

    key: str | None = None
    provider_type: str
    display_name: str
    model_name: str
    requires_consent: bool
    is_default: bool
    is_system: bool


class AiTenantSettingsSchema(BaseModel):
    ai_features_enabled: bool = False
    ai_default_provider_key: str | None = None
    ai_allow_cloud_providers: bool = False
    ai_daily_tip_enabled: bool = True


class HealthResponse(BaseModel):
    healthy: bool
