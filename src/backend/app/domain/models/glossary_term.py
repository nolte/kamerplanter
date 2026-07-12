"""REQ-035 §2 — domain models for the KI terminology glossary.

Two ArangoDB collections back the glossary: ``glossary_terms`` (the curated,
editorially maintained ~30-term skeleton) and ``glossary_term_cache`` (the
per-term/language/level RAG answer cache, analogous to ``ai_tip_cache`` from
REQ-031). The RAG answer text itself comes from the Knowledge-Service
microservice; the backend only persists the curated metadata and the cached
answers.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

# ── Type aliases ───────────────────────────────────────────────────

type GlossaryTermKey = str
type GlossaryTermCacheKey = str

#: REQ-021 experience levels. The glossary varies the RAG prompt per level.
ExpertiseLevel = Literal["beginner", "intermediate", "expert"]
Language = Literal["de", "en"]

#: Curated top-level categories (§2.3). Kept open (``str``) on the model so the
#: seed can grow without a schema change, but the initial set is documented here.
GlossaryCategory = str


# ── Shared value objects ───────────────────────────────────────────


class GlossarySource(BaseModel):
    """A cited knowledge chunk attached to a glossary answer (Quellenpflicht)."""

    source_key: str
    source_type: str = ""
    title: str = ""
    score: float = 0.0
    language: str = "de"


# ── Persisted collections ──────────────────────────────────────────


class GlossaryTerm(BaseModel):
    """REQ-035 §2.1 — one curated glossary term.

    The ``labels``/``long_labels``/``aliases``/``fallback_text`` maps are keyed by
    language code (``de``/``en``). Alias resolution is language-sensitive: an
    English request only matches English aliases (§7).
    """

    key: str | None = Field(default=None, alias="_key")
    slug: str
    labels: dict[str, str] = Field(default_factory=dict)
    long_labels: dict[str, str] = Field(default_factory=dict)
    aliases: dict[str, list[str]] = Field(default_factory=dict)
    category: GlossaryCategory = "allgemein"
    default_expertise_level: ExpertiseLevel = "beginner"
    applicable_phases: list[str] = Field(default_factory=list)
    related_term_slugs: list[str] = Field(default_factory=list)
    fallback_text: dict[str, str] = Field(default_factory=dict)
    rag_query_template: str = ""
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    def label_for(self, language: str) -> str:
        """Return the short label for ``language`` (falls back to ``de``/slug)."""
        return self.labels.get(language) or self.labels.get("de") or self.slug

    def long_label_for(self, language: str) -> str:
        """Return the long label for ``language`` (falls back to short label)."""
        return self.long_labels.get(language) or self.long_labels.get("de") or self.label_for(language)

    def fallback_for(self, language: str) -> str:
        """Return the editorial fallback text for ``language`` (falls back to ``de``)."""
        return self.fallback_text.get(language) or self.fallback_text.get("de") or ""


class GlossaryTermCacheEntry(BaseModel):
    """REQ-035 §2.2 — a cached RAG answer for a term/language/level/kb-version."""

    key: str | None = Field(default=None, alias="_key")
    term_slug: str
    language: Language = "de"
    expertise_level: ExpertiseLevel = "beginner"
    answer_text: str
    sources: list[GlossarySource] = Field(default_factory=list)
    language_mismatch_warning: bool = False
    model_name: str = ""
    provider_type: str = ""
    kb_version: str | None = None
    is_fallback: bool = False
    generated_at: datetime | None = None
    valid_until: datetime | None = None

    model_config = {"populate_by_name": True}


# ── API response value objects ─────────────────────────────────────


class GlossaryRelatedTerm(BaseModel):
    """A related-term reference rendered as a clickable chip (§3.4)."""

    slug: str
    label: str


class GlossaryTermSummary(BaseModel):
    """A single row of the term browser / sitemap (§3.1 ``/terms``)."""

    slug: str
    label: str
    category: str


class GlossaryTermAnswer(BaseModel):
    """REQ-035 §3.4 — the full ``get_term`` response envelope.

    Mirrors the KI ``<AIResponse>`` shell (KI badge, sources, disclaimer) plus the
    glossary-specific ``is_fallback`` / ``related_terms`` fields.
    """

    slug: str
    label: str
    long_label: str
    category: str
    answer_text: str
    expertise_level: ExpertiseLevel
    language: Language
    language_mismatch_warning: bool = False
    sources: list[GlossarySource] = Field(default_factory=list)
    related_terms: list[GlossaryRelatedTerm] = Field(default_factory=list)
    is_fallback: bool = False
    model_name: str = ""
    provider_type: str = ""
    uses_tenant_data: bool = False
    uses_cloud_provider: bool = False
    kb_version: str | None = None
    generated_at: datetime | None = None
