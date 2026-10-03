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
    retired_indexes_refused: int = Field(
        default=0,
        description=(
            "How many retired unique indexes an older image re-created that this replica's boot "
            "could not retire again because their replacement is missing (#2064); the boot log "
            "event ``retired_index_refused_without_replacement`` names them. Does not change "
            "``status``: the stricter constraint loses no data and no restart creates the "
            "replacement — an operator has to. ``0`` when every catalogued index is retired."
        ),
    )
