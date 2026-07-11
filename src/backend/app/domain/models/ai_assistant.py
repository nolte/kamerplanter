"""REQ-031 §3 — domain models for the KI-Assistent (AI assistant).

Only KI-specific tenant/user data is persisted in the Kamerplanter backend; the
vectors live in the Knowledge-Service microservice (REQ-031 §3.3). These Pydantic
v2 models back the ArangoDB collections ``ai_provider_configs``,
``ai_conversations``, ``ai_tip_cache`` and ``ai_audit_log``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.domain.interfaces.knowledge_service import ConfidenceLevel

# ── Type aliases ───────────────────────────────────────────────────

type AiProviderConfigKey = str
type AiConversationKey = str
type AiTipCardKey = str
type AiAuditLogKey = str

ProviderType = Literal["ollama", "anthropic", "openai_compatible"]
ContextType = Literal["plant_instance", "planting_run", "general", "daily", "term", "explain"]
TipType = Literal["care", "warning", "optimization", "diagnosis", "milestone", "explanation"]
TipPriority = Literal["critical", "high", "medium", "low"]
AuditStatus = Literal["ok", "denied", "provider_error", "knowledge_service_error", "timeout"]
Language = Literal["de", "en"]


# ── Shared value objects ───────────────────────────────────────────


class SourceReference(BaseModel):
    """A cited knowledge chunk attached to every KI answer (Quellenpflicht)."""

    source_key: str
    source_type: str
    title: str = ""
    score: float = 0.0
    language: str = "de"


class AiResponse(BaseModel):
    """REQ-031 §5.5 — the common answer envelope rendered by ``<AIResponse>``."""

    answer_text: str
    sources: list[SourceReference] = Field(default_factory=list)
    language: Language = "de"
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


# ── Persisted collections ──────────────────────────────────────────


class AiProviderConfig(BaseModel):
    """REQ-031 §3.1 — an LLM provider configuration (tenant or system default).

    The ``api_key_encrypted`` value is Fernet-encrypted (REQ-031 §4.7) and is
    never serialised to the API or any log.
    """

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str | None = None
    provider_type: ProviderType = "ollama"
    display_name: str
    base_url: str = ""
    model_name: str
    api_key_encrypted: str | None = None
    requires_consent: bool = False
    is_active: bool = True
    is_default: bool = False
    max_tokens: int = 2048
    temperature: float = 0.1
    timeout_seconds: int = 60
    language_default: Language = "de"
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class ConversationMessage(BaseModel):
    """A single chat turn stored inside an :class:`AiConversation`."""

    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime | None = None
    source_chunks: list[SourceReference] = Field(default_factory=list)


class AiConversation(BaseModel):
    """REQ-031 §3.1 — a chat history (retention 90 days, NFR-011)."""

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str
    user_key: str
    title: str | None = None
    context_type: ContextType = "general"
    context_key: str | None = None
    provider_key: str = ""
    model_name: str = ""
    language: Language = "de"
    message_count: int = 0
    messages: list[ConversationMessage] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    expires_at: datetime | None = None

    model_config = {"populate_by_name": True}


class AiTipCard(BaseModel):
    """REQ-031 §3.1 — a cached tip card / daily tip / "why" explanation."""

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str
    context_type: ContextType = "general"
    context_key: str = ""
    tip_type: TipType = "care"
    priority: TipPriority = "medium"
    title: str
    body: str
    action_url: str | None = None
    sources: list[SourceReference] = Field(default_factory=list)
    language: Language = "de"
    language_mismatch_warning: bool = False
    uses_tenant_data: bool = False
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    provider_key: str = ""
    model_name: str = ""
    generated_at: datetime | None = None
    valid_until: datetime | None = None
    dismissed_at: datetime | None = None
    dismissed_by: str | None = None
    acted_on_at: datetime | None = None

    model_config = {"populate_by_name": True}


class AiAuditLogEntry(BaseModel):
    """REQ-031 §3.1 — one audit record per KI call (retention 30 days, NFR-011).

    Never stores question/answer plaintext — only ``question_hash`` (sha256) and
    ``answer_length`` (NFR-007).
    """

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str
    user_key: str | None = None
    endpoint: str
    context_type: str | None = None
    context_key: str | None = None
    question_hash: str
    answer_length: int = 0
    model_name: str = ""
    provider_type: str = ""
    kb_version: str | None = None
    language: str = "de"
    uses_tenant_data: bool = False
    uses_cloud_provider: bool = False
    latency_ms: int = 0
    status: AuditStatus = "ok"
    error_class: str | None = None
    created_at: datetime | None = None

    model_config = {"populate_by_name": True}


class AiTenantSettings(BaseModel):
    """REQ-031 §3.1 — the ``ai_*`` sub-object stored on the tenant document."""

    ai_features_enabled: bool = False
    ai_default_provider_key: str | None = None
    ai_allow_cloud_providers: bool = False
    ai_daily_tip_enabled: bool = True
