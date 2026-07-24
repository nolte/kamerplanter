"""Response schemas for the Kubernetes liveness/readiness probes (NFR-013)."""

from pydantic import BaseModel, Field


class LivenessResponse(BaseModel):
    """Liveness probe payload."""

    status: str = Field(description="Static liveness marker; always ``alive`` when the process is up.")


class ReadinessResponse(BaseModel):
    """Readiness probe payload (NFR-013 AC-08)."""

    status: str = Field(description="Overall readiness state: ``ready`` or ``not_ready``.")
    database: bool = Field(description="Whether the primary database is reachable.")
    object_storage: bool = Field(description="Whether the configured object-storage backend is reachable.")
