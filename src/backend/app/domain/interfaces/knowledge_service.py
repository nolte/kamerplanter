"""REQ-031 §4.1 — ``IKnowledgeService`` ABC (SSOT for the Knowledge-Service port).

The Kamerplanter backend never talks to pgvector or an LLM directly. All RAG
access goes through this async port to the standalone Knowledge-Service
microservice (``src/knowledge-service/``). The concrete
:class:`~app.data_access.external.knowledge_service_adapter.HttpKnowledgeServiceAdapter`
adds retry + circuit-breaker resilience (NFR-007); tests inject a fake through
the same ABC.

The DTOs here mirror the microservice contract (``src/knowledge-service/app/
schemas.py``) plus the ADR-002 confidence/cultivar-hint extension that the
backend attaches before the call.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum

from pydantic import BaseModel, Field


class ConfidenceLevel(StrEnum):
    """ADR-002 — how well a tenant species maps onto the KS knowledge base.

    ``HIGH`` a global species is used directly; ``MEDIUM`` a tenant species was
    resolved via its ``parent_species_key``; ``LOW`` only a genus/family fallback
    was possible; ``NONE`` no botanical anchor exists (KS call is skipped and the
    backend answers rule-based).
    """

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class KnowledgeChunk(BaseModel):
    """A single retrieved knowledge chunk returned by the Knowledge Service."""

    source_key: str
    source_type: str
    title: str
    content: str = ""
    score: float
    language: str = "de"
    metadata: dict = Field(default_factory=dict)


class QuestionContext(BaseModel):
    """PII-free plant context passed to the Knowledge Service (REQ-031 §4.2).

    Only master values are allowed here (NFR-007 §LLM-Sicherheit). The ADR-002
    ``cultivar_hint`` and ``confidence`` fields are backend-only annotations; the
    KS ignores ``confidence`` and embeds ``cultivar_hint`` into the prompt.
    """

    species: str | None = None
    cultivar_hint: str | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    phase: str | None = None
    substrate: str | None = None
    ec: float | None = None
    ph: float | None = None

    def to_ks_payload(self) -> dict:
        """Serialise to the microservice ``QuestionContext`` schema.

        The KS only knows ``species``/``phase``/``substrate``/``ec``/``ph``. The
        backend-only ``confidence`` field is dropped; ``cultivar_hint`` is passed
        through so the KS prompt engine can reference the tenant sort note.
        """
        payload: dict = {}
        for field in ("species", "phase", "substrate", "ec", "ph", "cultivar_hint"):
            value = getattr(self, field)
            if value is not None:
                payload[field] = value
        return payload


class AskResult(BaseModel):
    """Normalised result of a Knowledge-Service ``/ask`` call."""

    answer: str
    question_type: str = "factual"
    model_name: str
    provider_type: str | None = None
    kb_version: str | None = None
    sources: list[KnowledgeChunk] = Field(default_factory=list)
    usage: dict[str, int] = Field(default_factory=dict)


class IKnowledgeService(ABC):
    """Async port to the Knowledge-Service microservice (REQ-031 §4.1)."""

    @abstractmethod
    async def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        doc_language: str | None = None,
    ) -> list[KnowledgeChunk]:
        """Semantic/hybrid search over the knowledge base."""

    @abstractmethod
    async def ask(
        self,
        question: str,
        *,
        top_k: int = 10,
        context: QuestionContext | None = None,
        doc_language: str | None = None,
        prompt_language: str | None = None,
    ) -> AskResult:
        """RAG question answering with optional PII-free plant context."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True when the Knowledge Service is reachable and ready.

        Implementations back this with a circuit breaker so a flapping service
        degrades gracefully instead of blocking every request (NFR-007).
        """
