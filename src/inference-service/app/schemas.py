"""Pydantic v2 schemas for the Inference Service API."""

from pydantic import BaseModel, Field


class EmbedResponse(BaseModel):
    """A single embedding vector."""

    embedding: list[float]
    dim: int
    model: str


class BatchEmbedResponse(BaseModel):
    """Multiple embedding vectors (reference indexing)."""

    embeddings: list[list[float]]
    dim: int
    model: str
    count: int


class MatchSuggestion(BaseModel):
    """One matched species suggestion."""

    rank: int
    species_key: str
    scientific_name: str
    score: float = Field(description="Raw cosine similarity (1 - cosine distance)")
    confidence: float = Field(description="Calibrated confidence in [0, 1] (REQ-029-A 3.5)")


class MatchResponse(BaseModel):
    """Result of a /match request."""

    suggestions: list[MatchSuggestion]
    is_plant: bool = Field(description="True when at least one suggestion was found")
    model: str


class ReferenceResponse(BaseModel):
    """Result of upserting a reference embedding."""

    status: str
    species_key: str
    dim: int
    model: str


class DeleteReferenceResponse(BaseModel):
    """Result of deleting all references for a species."""

    status: str
    species_key: str
    deleted: int


class ModelInfoResponse(BaseModel):
    """Static model metadata."""

    model: str
    dim: int
    input_size: int
    license: str
    checksum: str | None = None


class HealthResponse(BaseModel):
    """Liveness probe response."""

    status: str
    model_loaded: bool
    vectordb: bool
