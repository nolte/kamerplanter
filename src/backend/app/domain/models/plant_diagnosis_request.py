"""REQ-038 §4 — persisted CV disease-diagnosis request.

One document per diagnosis. Only the classifications, optional phenotype metrics
and model provenance are stored — the original image is NEVER persisted
(``image_deleted_at`` is set at creation, only the ``image_hash`` remains for
dedup/audit, §4.4). Tenant-scoped via ``tenant_key`` (REQ-024 isolation).
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.interfaces.cv_diagnosis_adapter import (
    DEFAULT_DISEASE_DISCLAIMER,
    DiagnosisModelMeta,
    DiseaseClassification,
    PhenotypeMetrics,
)


class PlantDiagnosisRequest(BaseModel):
    """A stored CV disease-diagnosis request and its (mapped) result."""

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str
    user_key: str

    # Optional binding to a plant / run (drives the cv_diagnosed_for edge).
    plant_instance_key: str | None = None
    planting_run_key: str | None = None
    # Set once a suggestion is confirmed into an IPM inspection (never a treatment).
    inspection_key: str | None = None
    # Optional harvest observation this phenotype belongs to (REQ-007 bridge).
    harvest_observation_key: str | None = None

    classifications: list[DiseaseClassification] = Field(default_factory=list)
    phenotype: PhenotypeMetrics | None = None
    model_meta: DiagnosisModelMeta = Field(default_factory=DiagnosisModelMeta)
    adapter_key: str = ""
    is_confident: bool = False
    # ALWAYS non-empty (§4.4) — a CV diagnosis is only a hypothesis.
    disclaimer: str = DEFAULT_DISEASE_DISCLAIMER

    # Confirmed class labels (human-in-the-loop). Never auto-populated.
    confirmed_labels: list[str] = Field(default_factory=list)

    # Provenance of the (discarded) image. The image itself is never stored.
    image_hash: str
    image_deleted_at: datetime | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
