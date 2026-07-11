"""REQ-038 §4/§6 — CV disease-diagnosis orchestration service.

Coordinates the diagnose flow: consent gate (``plant_diagnosis``) → server-side
EXIF strip (§4.4) → adapter dispatch → engine gating/IPM-mapping → persistence
WITHOUT retaining the image (``image_deleted_at``). Also exposes status, history
and the confirm bridge — which creates an IPM inspection *suggestion* only, never
a treatment (§0), so the REQ-010 Karenz gate stays untouched by construction.
"""

import hashlib
from datetime import UTC, datetime

import structlog

from app.common.enums import PestPressureLevel
from app.common.exceptions import (
    ConsentRequiredError,
    FeatureNotConfiguredError,
    NotFoundError,
    ValidationError,
)
from app.config.settings import settings
from app.domain.calculators.image_preprocessor import strip_exif_and_normalize
from app.domain.engines.consent_engine import ConsentEngine
from app.domain.engines.cv_diagnosis_engine import CvDiagnosisEngine
from app.domain.interfaces.consent_repository import IConsentRepository
from app.domain.interfaces.cv_diagnosis_adapter import (
    DEFAULT_DISEASE_DISCLAIMER,
    CvDiagnosisAdapter,
)
from app.domain.interfaces.plant_diagnosis_repository import IPlantDiagnosisRepository
from app.domain.models.ipm import Inspection
from app.domain.models.plant_diagnosis_request import PlantDiagnosisRequest
from app.domain.services.ipm_service import IpmService

logger = structlog.get_logger()

_CONSENT_PURPOSE = "plant_diagnosis"


class CvDiagnosisService:
    """Service layer for CV disease diagnosis (Phase 1, self-hosted)."""

    def __init__(
        self,
        *,
        adapter: CvDiagnosisAdapter,
        engine: CvDiagnosisEngine,
        repo: IPlantDiagnosisRepository,
        ipm_service: IpmService,
        consent_repo: IConsentRepository,
        consent_engine: ConsentEngine,
    ) -> None:
        self._adapter = adapter
        self._engine = engine
        self._repo = repo
        self._ipm = ipm_service
        self._consent_repo = consent_repo
        self._consent_engine = consent_engine

    # ── status ──────────────────────────────────────────────────────────

    def get_status(self) -> dict:
        """Availability payload used by the frontend to toggle the diagnose UI."""
        snapshot = self._adapter.status()
        return {
            "available": bool(snapshot.get("ready", False)) and settings.cv_diagnosis_enabled,
            "feature_enabled": settings.cv_diagnosis_enabled,
            "adapter_key": snapshot.get("adapter_key", self._adapter.adapter_key),
            "phenotype_available": bool(snapshot.get("phenotype_available", False)),
            "class_count": int(snapshot.get("class_count", 0)),
        }

    # ── diagnose ────────────────────────────────────────────────────────

    def diagnose(
        self,
        image_data: bytes,
        *,
        tenant_key: str,
        user_key: str,
        plant_instance_key: str | None = None,
        with_phenotype: bool = False,
    ) -> dict:
        """Run a CV disease diagnosis over an uploaded photo.

        Raises:
            FeatureNotConfiguredError: the diagnosis feature/adapter is disabled.
            ConsentRequiredError: the user has not granted ``plant_diagnosis``.
            ValidationError: the image is empty/oversized/undecodable.
        """
        self._validate_size(image_data)
        self._require_consent(user_key)

        if not self._adapter.is_configured():
            raise FeatureNotConfiguredError(
                "plant_diagnosis",
                hint="The self-hosted disease classifier is disabled or unreachable.",
            )

        # §4.4 — strip EXIF server-side BEFORE anything else; the original bytes
        # are discarded and never persisted (only the hash of the clean image is
        # kept for dedup/audit).
        try:
            clean = strip_exif_and_normalize(
                image_data,
                max_dimension=settings.identification_max_image_dimension,
            )
        except ValueError as exc:
            raise ValidationError("Image could not be decoded.") from exc

        image_hash = "sha256:" + hashlib.sha256(clean).hexdigest()
        result = self._adapter.classify(clean, with_phenotype=with_phenotype)
        processed = self._engine.process(result)

        now = datetime.now(tz=UTC)
        request = PlantDiagnosisRequest(
            tenant_key=tenant_key,
            user_key=user_key,
            plant_instance_key=plant_instance_key,
            classifications=processed.classifications,
            phenotype=processed.phenotype,
            model_meta=processed.model_meta,
            adapter_key=processed.adapter_key or self._adapter.adapter_key,
            is_confident=processed.is_confident,
            disclaimer=processed.disclaimer or DEFAULT_DISEASE_DISCLAIMER,
            image_hash=image_hash,
            image_deleted_at=now,  # the image is never persisted (§4.4)
        )
        created = self._repo.create(request)
        return self._to_response(created)

    # ── confirm (IPM inspection suggestion only — never a treatment, §0) ─

    def confirm(
        self,
        key: str,
        *,
        tenant_key: str,
        plant_key: str,
        confirmed_labels: list[str] | None = None,
    ) -> dict:
        """Confirm a diagnosis into an IPM inspection suggestion.

        Cross-tenant fail-closed: an unknown/foreign request raises
        :class:`NotFoundError` (no information-leak oracle). Never creates a
        treatment, so the REQ-010 Karenz gate is not engaged here.
        """
        request = self._repo.get(key, tenant_key)
        if request is None:
            raise NotFoundError("PlantDiagnosisRequest", key)

        labels = confirmed_labels or [c.label for c in request.classifications if c.highlight]
        confirmed = [c for c in request.classifications if c.label in labels]

        disease_keys: list[str] = []
        pest_keys: list[str] = []
        symptoms: list[str] = []
        max_conf = 0.0
        for c in confirmed:
            symptoms.append(c.label)
            max_conf = max(max_conf, c.probability)
            if c.matched_disease_key and c.matched_disease_key not in disease_keys:
                disease_keys.append(c.matched_disease_key)
            if c.matched_pest_key and c.matched_pest_key not in pest_keys:
                pest_keys.append(c.matched_pest_key)

        inspection = Inspection(
            tenant_key=tenant_key,
            plant_key=plant_key,
            inspector="",
            pressure_level=self._pressure_from_confidence(max_conf),
            detected_pest_keys=pest_keys,
            detected_disease_keys=disease_keys,
            symptoms_observed=symptoms,
            notes=f"Aus CV-Krankheitsdiagnose {key} (Bild-Verdacht, REQ-038).",
        )
        created = self._ipm.create_inspection(plant_key, inspection)
        self._repo.mark_confirmed(
            key,
            tenant_key,
            confirmed_labels=labels,
            inspection_key=created.key,
        )
        return {
            "inspection_key": created.key,
            "detected_disease_keys": disease_keys,
            "detected_pest_keys": pest_keys,
            "confirmed_labels": labels,
        }

    # ── history ─────────────────────────────────────────────────────────

    def get_history(self, *, tenant_key: str, user_key: str, limit: int = 20) -> list[dict]:
        """Return the user's recent diagnosis requests (no images retained)."""
        return [self._to_response(r) for r in self._repo.list_for_user(tenant_key, user_key, limit)]

    # ── internals ───────────────────────────────────────────────────────

    def _require_consent(self, user_key: str) -> None:
        """Block diagnosis unless the user granted ``plant_diagnosis``.

        Mode-aware: the hard backend gate applies only in ``full`` mode. In Light
        mode (REQ-027) there is no consent subsystem — the transparency/opt-in is
        handled client-side and no consent record could exist — so the backend
        gate is skipped there (mirrors the identification service).
        """
        if settings.kamerplanter_mode != "full":
            return
        record = self._consent_repo.get_by_user_and_purpose(user_key, _CONSENT_PURPOSE)
        if not self._consent_engine.is_processing_allowed(_CONSENT_PURPOSE, record):
            raise ConsentRequiredError(_CONSENT_PURPOSE)

    @staticmethod
    def _validate_size(image_data: bytes) -> None:
        if not image_data:
            raise ValidationError("Empty image upload.")
        max_bytes = settings.cv_diagnosis_max_image_size_mb * 1024 * 1024
        if len(image_data) > max_bytes:
            raise ValidationError(f"Image exceeds {settings.cv_diagnosis_max_image_size_mb} MB limit.")

    @staticmethod
    def _pressure_from_confidence(confidence: float) -> PestPressureLevel:
        if confidence >= 0.75:
            return PestPressureLevel.HIGH
        if confidence >= 0.5:
            return PestPressureLevel.MEDIUM
        if confidence > 0.0:
            return PestPressureLevel.LOW
        return PestPressureLevel.NONE

    @staticmethod
    def _to_response(request: PlantDiagnosisRequest) -> dict:
        data = request.model_dump(mode="json", by_alias=False)
        data["key"] = request.key
        # §4.4 — the disclaimer is never empty in any response.
        if not data.get("disclaimer"):
            data["disclaimer"] = DEFAULT_DISEASE_DISCLAIMER
        # Defense in depth: never leak a raw image field even if one sneaks in.
        data.pop("image_data", None)
        return data
