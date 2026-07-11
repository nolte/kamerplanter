"""REQ-038 §3 — self-hosted CV disease-diagnosis adapter (no data egress).

Wraps the inference-service ``/classify/disease`` endpoint and maps its raw
payload onto the typed :class:`CvDiagnosisResult`. The trained model artifact is
externally provided (mounted at runtime); until the service exposes an enabled,
loaded classifier ``is_configured()`` returns False and the feature degrades
gracefully (the diagnosis flow reports "not available", the app keeps working).
"""

from typing import Any

from app.common.enums import DiagnosisCategory
from app.config.settings import settings
from app.data_access.external.cv_diagnosis_inference_client import CvDiagnosisInferenceClient
from app.domain.interfaces.cv_diagnosis_adapter import (
    DEFAULT_DISEASE_DISCLAIMER,
    CvDiagnosisAdapter,
    CvDiagnosisResult,
    DiagnosisModelMeta,
    DiseaseClassification,
    PhenotypeMetrics,
)


def _classification_from_raw(raw: dict[str, Any]) -> DiseaseClassification:
    """Map one raw classification dict onto the typed model (category-guarded)."""
    category_value = raw.get("category", DiagnosisCategory.DISEASE.value)
    try:
        category = DiagnosisCategory(category_value)
    except ValueError:
        category = DiagnosisCategory.DISEASE
    return DiseaseClassification(
        label=raw["label"],
        category=category,
        scientific_name=raw.get("scientific_name"),
        probability=float(raw["probability"]),
        highlight=bool(raw.get("highlight", False)),
    )


def _phenotype_from_raw(raw: dict[str, Any] | None) -> PhenotypeMetrics | None:
    if not raw:
        return None
    return PhenotypeMetrics(**raw)


def _model_meta_from_raw(raw: dict[str, Any] | None) -> DiagnosisModelMeta:
    if not raw:
        return DiagnosisModelMeta()
    return DiagnosisModelMeta(
        model_name=raw.get("model_name", ""),
        training_base=raw.get("training_base"),
        fine_tuned_on=raw.get("fine_tuned_on", []),
        onnx_checksum=raw.get("onnx_checksum"),
        model_version=raw.get("model_version"),
        class_count=int(raw.get("class_count", 0)),
    )


class LocalCvDiagnosisAdapter(CvDiagnosisAdapter):
    """Self-hosted disease classifier (Phase-1 default). No third-party egress."""

    adapter_key = "local_cv_diagnosis"
    is_external = False
    # The self-hosted path performs no external egress, but the user photo is
    # still processed, so the diagnosis consent purpose gates it (REQ-025/§4.4).
    requires_consent = "plant_diagnosis"

    def __init__(self, client: CvDiagnosisInferenceClient | None = None) -> None:
        self._client = client or CvDiagnosisInferenceClient(settings.inference_service_url)

    def is_configured(self) -> bool:
        return bool(settings.cv_diagnosis_enabled) and self._client.is_ready()

    def status(self) -> dict:
        snapshot = self._client.status()
        snapshot["adapter_key"] = self.adapter_key
        snapshot["feature_enabled"] = bool(settings.cv_diagnosis_enabled)
        return snapshot

    def classify(self, image: bytes, *, with_phenotype: bool = False) -> CvDiagnosisResult:
        payload = self._client.classify(
            image,
            k=5,
            with_phenotype=with_phenotype and settings.cv_phenotype_enabled,
        )
        classifications = [_classification_from_raw(raw) for raw in payload.get("classifications", [])]
        # The service always sends a disclaimer; fall back defensively so the
        # invariant (§4.4) holds even against a malformed payload.
        disclaimer = payload.get("disclaimer") or DEFAULT_DISEASE_DISCLAIMER
        return CvDiagnosisResult(
            classifications=classifications,
            phenotype=_phenotype_from_raw(payload.get("phenotype")),
            model_meta=_model_meta_from_raw(payload.get("model_meta")),
            adapter_key=self.adapter_key,
            disclaimer=disclaimer,
        )
