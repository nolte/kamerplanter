"""REQ-035 §3 — request/response schemas for the glossary API.

The read responses reuse the domain DTOs
(:class:`~app.domain.models.glossary_term.GlossaryTermAnswer` /
:class:`~app.domain.models.glossary_term.GlossaryTermSummary`) directly as
``response_model`` — they are already clean, PII-free value objects. Only the
platform-admin write bodies need dedicated request schemas.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.domain.models.glossary_term import ExpertiseLevel


class GlossaryTermUpsertRequest(BaseModel):
    """Platform-admin create/edit body for a curated term (§3.3)."""

    slug: str = Field(min_length=1, max_length=80, pattern=r"^[a-z0-9-]+$")
    labels: dict[str, str] = Field(default_factory=dict)
    long_labels: dict[str, str] = Field(default_factory=dict)
    aliases: dict[str, list[str]] = Field(default_factory=dict)
    category: str = Field(default="allgemein", min_length=1, max_length=40)
    default_expertise_level: ExpertiseLevel = "beginner"
    applicable_phases: list[str] = Field(default_factory=list)
    related_term_slugs: list[str] = Field(default_factory=list)
    fallback_text: dict[str, str] = Field(default_factory=dict)
    rag_query_template: str = Field(default="", max_length=1000)
    is_active: bool = True


class CacheInvalidateResponse(BaseModel):
    """Number of cache rows removed by an invalidation call (§3.3)."""

    removed: int
