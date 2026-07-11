"""REQ-038 — request/response schemas for the CV disease-diagnosis endpoints."""

from pydantic import BaseModel, Field

from app.domain.interfaces.cv_diagnosis_adapter import (
    DiagnosisModelMeta,
    DiseaseClassification,
    PhenotypeMetrics,
)


class CvDiagnosisStatusResponse(BaseModel):
    """Availability of the CV diagnosis feature (drives the UI toggle)."""

    available: bool
    feature_enabled: bool
    adapter_key: str
    phenotype_available: bool
    class_count: int


class CvDiagnosisResponse(BaseModel):
    """One persisted diagnosis request and its mapped result.

    ``disclaimer`` is ALWAYS non-empty (REQ-038 §4.4). No original image is ever
    returned — only the ``image_hash`` provenance and ``image_deleted_at``.
    """

    key: str | None = None
    plant_instance_key: str | None = None
    inspection_key: str | None = None
    classifications: list[DiseaseClassification] = Field(default_factory=list)
    phenotype: PhenotypeMetrics | None = None
    model_meta: DiagnosisModelMeta = Field(default_factory=DiagnosisModelMeta)
    adapter_key: str = ""
    is_confident: bool = False
    disclaimer: str
    confirmed_labels: list[str] = Field(default_factory=list)
    image_hash: str
    image_deleted_at: str | None = None
    created_at: str | None = None


class ConfirmDiagnosisRequest(BaseModel):
    """Confirm a diagnosis into an IPM inspection suggestion (never a treatment)."""

    plant_key: str = Field(min_length=1, description="Plant instance the inspection belongs to")
    confirmed_labels: list[str] | None = Field(
        default=None,
        description="Class labels the user confirms; defaults to the highlighted classes.",
    )


class ConfirmDiagnosisResponse(BaseModel):
    """Result of confirming a diagnosis (an inspection suggestion, §0)."""

    inspection_key: str | None = None
    detected_disease_keys: list[str] = Field(default_factory=list)
    detected_pest_keys: list[str] = Field(default_factory=list)
    confirmed_labels: list[str] = Field(default_factory=list)
