"""REQ-038 §4 — contract for CV disease/deficiency diagnosis.

A CV diagnosis is a supervised classification of a plant photo against a fixed
set of disease / deficiency classes, optionally accompanied by objective PlantCV
phenotype measurements. It is CLEARLY distinct from REQ-044 (pest few-shot
prototype matching) and REQ-029 (species embedding matching): the result is
never an automatic treatment and always carries a non-empty ``disclaimer`` — the
strongest outcome is a *suggestion* the grower confirms manually (§0).
"""

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

from app.common.enums import DiagnosisCategory

# §4.4 — durchgaengiger Disclaimer; ein automatisierter Test prueft, dass dieses
# Feld in keiner API-Antwort/keinem Ergebnis leer ist. Eine CV-Diagnose ist immer
# nur ein Verdacht, nie eine akzeptierte Diagnose.
DEFAULT_DISEASE_DISCLAIMER = (
    "Nur eine Einschätzung der Bilderkennung — keine gesicherte Diagnose. "
    "Bitte den Verdacht fachlich prüfen, bevor du behandelst; bei Unsicherheit "
    "einen zweiten Blick einholen."
)


class DiseaseClassification(BaseModel):
    """One scored disease/deficiency class of a diagnosis result."""

    label: str
    category: DiagnosisCategory
    scientific_name: str | None = None
    probability: float = Field(ge=0.0, le=1.0)
    # True when the model is highly confident (probability >= highlight gate).
    # Highlighting is a UI hint only — it never implies auto-accept.
    highlight: bool = False
    # Mapping against REQ-010 stammdaten (set by the engine, not the adapter).
    # ``deficiency`` classes stay null and are matched via REQ-036 symptom slugs.
    matched_disease_key: str | None = None
    matched_pest_key: str | None = None
    matched_symptom_slug: str | None = None


class PhenotypeMetrics(BaseModel):
    """Objective PlantCV phenotype measurements (measurement, not diagnosis)."""

    leaf_area_px: int
    green_index: float
    discolored_area_ratio: float
    necrotic_area_ratio: float
    solidity: float
    hue_circular_mean_deg: float
    plantcv_version: str


class DiagnosisModelMeta(BaseModel):
    """Model card / provenance surfaced with the result.

    PlantVillage is deliberately never listed (unclear licence + lab->field gap).
    """

    model_name: str = ""
    training_base: str | None = None
    fine_tuned_on: list[str] = Field(default_factory=list)
    onnx_checksum: str | None = None
    model_version: str | None = None
    class_count: int = 0


class CvDiagnosisResult(BaseModel):
    """Unified diagnosis result (self-hosted classifier + optional phenotype)."""

    classifications: list[DiseaseClassification] = Field(default_factory=list)
    phenotype: PhenotypeMetrics | None = None
    model_meta: DiagnosisModelMeta = Field(default_factory=DiagnosisModelMeta)
    adapter_key: str = ""
    is_confident: bool = False
    # ALWAYS non-empty (§4.4). An automated test enforces this invariant.
    disclaimer: str = DEFAULT_DISEASE_DISCLAIMER


class CvDiagnosisAdapter(ABC):
    """Common contract for CV disease-diagnosis adapters (Phase 1: self-hosted)."""

    adapter_key: str = ""
    # Consent purpose that must be granted before use (REQ-025), or ``None`` for a
    # purely local path that performs no third-party egress.
    requires_consent: str | None = None
    # True when the adapter sends image data to a third party (data egress).
    is_external: bool = False

    @abstractmethod
    def is_configured(self) -> bool:
        """Whether the adapter has everything it needs to run (flag + model)."""

    @abstractmethod
    def classify(self, image: bytes, *, with_phenotype: bool = False) -> CvDiagnosisResult:
        """Classify one image; optionally attach phenotype measurements."""

    def status(self) -> dict:
        """Best-effort availability snapshot for a status card."""
        return {"ready": self.is_configured(), "adapter_key": self.adapter_key}

    def health_check(self) -> bool:
        return self.is_configured()
