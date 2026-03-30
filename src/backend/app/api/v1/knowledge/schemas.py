"""Pydantic v2 schemas for the knowledge/RAG API endpoints."""

from pydantic import BaseModel, Field


class KnowledgeChunkResponse(BaseModel):
    """A single retrieved knowledge chunk."""

    source_key: str = Field(description="Unique key of the source chunk")
    source_type: str = Field(description="Type of source (e.g. 'knowledge_guide')")
    title: str = Field(description="Title of the source document")
    content: str = Field(description="Text content of the chunk")
    score: float = Field(description="Cosine similarity score (0.0 to 1.0)")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")

    model_config = {"from_attributes": True}


class KnowledgeSearchResponse(BaseModel):
    """Response for semantic search."""

    query: str = Field(description="The original search query")
    results: list[KnowledgeChunkResponse] = Field(description="Matching chunks ordered by relevance")
    total: int = Field(description="Number of results returned")


class KnowledgeAskRequest(BaseModel):
    """Request body for the RAG ask endpoint."""

    question: str = Field(min_length=3, max_length=2000, description="The question to answer")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of context chunks to retrieve")


class KnowledgeAskResponse(BaseModel):
    """Response for the RAG ask endpoint."""

    answer: str = Field(description="Generated answer from the LLM")
    model: str = Field(description="LLM model used for generation")
    usage: dict[str, int] = Field(description="Token usage (prompt_tokens, completion_tokens)")
    sources: list[KnowledgeChunkResponse] = Field(description="Context chunks used for generation")
