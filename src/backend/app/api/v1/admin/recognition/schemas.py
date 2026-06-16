"""REQ-029-A — Admin API schemas for the DINOv2 recognition status view."""

from pydantic import BaseModel


class InferenceServiceStatus(BaseModel):
    """Live status of the self-hosted inference-service."""

    enabled: bool
    url: str
    ready: bool
    model: str | None = None
    dim: int | None = None
    license: str | None = None


class CoverageSummary(BaseModel):
    """Reference-index coverage + acquisition progress summary.

    ``processed_species`` is the number of species an acquisition run has already
    handled (one ``reference_image_jobs`` entry each); the UI derives progress
    (processed / total) and a coarse state from these counts.
    """

    total_species: int
    processed_species: int
    usable_species: int


class RecognitionConfig(BaseModel):
    """Non-secret recognition configuration values."""

    primary_adapter: str
    confidence_auto_accept: float
    confidence_min_show: float
    reference_image_min_usable: int
    use_wikimedia: bool


class RecognitionStatusResponse(BaseModel):
    """Aggregated DINOv2 recognition status for the admin UI."""

    feature_enabled: bool
    local_adapter_available: bool
    inference_service: InferenceServiceStatus
    coverage: CoverageSummary
    config: RecognitionConfig


class AcquisitionStartResponse(BaseModel):
    """Result of dispatching a reference-image acquisition run from the UI."""

    status: str  # "queued"
    task_id: str | None = None
