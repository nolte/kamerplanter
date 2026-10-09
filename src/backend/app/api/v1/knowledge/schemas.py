"""Pydantic v2 schemas for the knowledge/RAG API endpoints."""

from typing import Literal

from pydantic import BaseModel, Field


class QuestionContext(BaseModel):
    """Optional context about the plant/situation.

    Bounded like the question (SEC-002, #2175): the values end up in the same LLM
    prompt, so an unbounded context would lift the question's 2 000-character
    limit — and the token budget only counts after the call. 100 characters
    hold the longest seeded scientific name (under 80); EC and pH carry the
    physical ranges the feeding model uses.
    """

    species: str | None = Field(default=None, max_length=100, description="Plant species name")
    phase: str | None = Field(default=None, max_length=100, description="Current growth phase")
    substrate: str | None = Field(default=None, max_length=100, description="Growing medium")
    ec: float | None = Field(default=None, ge=0, le=20, description="Current EC value (mS/cm)")
    ph: float | None = Field(default=None, ge=0, le=14, description="Current pH value")


class KnowledgeChunkResponse(BaseModel):
    """A single retrieved knowledge chunk."""

    source_key: str = Field(description="Unique key of the source chunk")
    source_type: str = Field(description="Type of source (e.g. 'knowledge_guide')")
    title: str = Field(description="Title of the source document")
    content: str = Field(description="Text content of the chunk")
    score: float = Field(description="Similarity score (0.0 to 1.0)")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
    language: str = Field(default="de", description="Language of the chunk (de, en)")

    model_config = {"from_attributes": True}


class KnowledgeSearchResponse(BaseModel):
    """Response for semantic search."""

    query: str = Field(description="The original search query")
    results: list[KnowledgeChunkResponse] = Field(description="Matching chunks ordered by relevance")
    total: int = Field(description="Number of results returned")
    doc_language: str | None = Field(default=None, description="Language filter applied")


class KnowledgeAskRequest(BaseModel):
    """Request body of ``POST /t/{tenant_slug}/ai/knowledge/ask`` (#2175)."""

    question: str = Field(min_length=3, max_length=2000, description="The question to answer")
    top_k: int = Field(default=5, ge=1, le=10, description="Number of context chunks to retrieve")
    doc_language: Literal["de", "en", "all"] | None = Field(
        default=None,
        description="Filter chunks by language. None uses server default.",
    )
    prompt_language: Literal["de", "en"] | None = Field(
        default=None,
        description="System prompt language for LLM thinking. None uses server default.",
    )
    context: QuestionContext | None = Field(
        default=None,
        description="Optional context about the plant/situation for better answers.",
    )


class KnowledgeAskResponse(BaseModel):
    """Response for the RAG ask endpoint."""

    answer: str = Field(description="Generated answer from the LLM")
    question_type: str = Field(default="factual", description="Detected question type (diagnosis/howto/factual)")
    model: str = Field(description="LLM model used for generation")
    usage: dict[str, int] = Field(description="Token usage (prompt_tokens, completion_tokens)")
    sources: list[KnowledgeChunkResponse] = Field(description="Context chunks used for generation")
