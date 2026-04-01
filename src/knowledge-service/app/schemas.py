"""Pydantic v2 schemas for the Knowledge Service API."""

from typing import Literal

from pydantic import BaseModel, Field


class QuestionContext(BaseModel):
    """Optional context about the plant/situation."""

    species: str | None = Field(default=None, description="Plant species name")
    phase: str | None = Field(default=None, description="Current growth phase")
    substrate: str | None = Field(default=None, description="Growing medium")
    ec: float | None = Field(default=None, description="Current EC value")
    ph: float | None = Field(default=None, description="Current pH value")


class KnowledgeChunkResponse(BaseModel):
    """A single retrieved knowledge chunk."""

    source_key: str
    source_type: str
    title: str
    content: str
    score: float
    metadata: dict = Field(default_factory=dict)
    language: str = "de"


class SearchRequest(BaseModel):
    """Query params for search (used internally)."""

    q: str = Field(min_length=1, max_length=500)
    top_k: int = Field(default=5, ge=1, le=50)
    doc_language: Literal["de", "en", "all"] | None = None


class SearchResponse(BaseModel):
    """Response for semantic search."""

    query: str
    results: list[KnowledgeChunkResponse]
    total: int
    doc_language: str | None = None


class AskRequest(BaseModel):
    """Request body for RAG question answering."""

    question: str = Field(min_length=3, max_length=2000)
    top_k: int = Field(default=10, ge=1, le=20)
    doc_language: Literal["de", "en", "all"] | None = None
    prompt_language: Literal["de", "en"] | None = None
    context: QuestionContext | None = None


class AskResponse(BaseModel):
    """Response for RAG question answering."""

    answer: str
    question_type: str
    model: str
    usage: dict[str, int]
    sources: list[KnowledgeChunkResponse]


class ClassifyRequest(BaseModel):
    """Request body for question classification."""

    question: str = Field(min_length=3, max_length=2000)


class ClassifyResponse(BaseModel):
    """Response for question classification."""

    question_type: str


class IngestResponse(BaseModel):
    """Response for knowledge ingestion."""

    status: str
    files: int = 0
    chunks: int = 0
    reason: str | None = None
