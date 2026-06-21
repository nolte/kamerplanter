"""REQ-044 §6 — pest-detection orchestration service.

Coordinates the detect flow: consent gate (cloud only) → EXIF strip (a second
time, server-side, §8) → mandatory tiling (§4.3) → adapter dispatch → mapping +
abstention + persistence (engine). Also exposes status, history, HITL feedback,
the IPM inspection bridge (never a treatment, §0) and the health signal that
REQ-043 will consume.
"""

import hashlib

import structlog

from app.common.enums import (
    PestFindingCategory,
    PestPressureLevel,
)
from app.common.exceptions import (
    ConsentRequiredError,
    FeatureNotConfiguredError,
    NotFoundError,
    ValidationError,
)
from app.config.settings import settings
from app.domain.calculators.image_preprocessor import strip_exif_and_normalize
from app.domain.calculators.image_tiler import ABSTAIN_CONFIDENCE, ImageTiler
from app.domain.engines.consent_engine import ConsentEngine
from app.domain.engines.pest_detection_engine import PestDetectionEngine
from app.domain.interfaces.consent_repository import IConsentRepository
from app.domain.interfaces.pest_detection_adapter import PestDetectionAdapter
from app.domain.interfaces.pest_detection_repository import IPestDetectionRepository
from app.domain.models.ipm import Inspection
from app.domain.models.pest_detection import PestDetection, PestFeedback
from app.domain.services.ipm_service import IpmService
from app.domain.services.pest_detection_registry import PestDetectionAdapterRegistry

logger = structlog.get_logger()


class PestDetectionService:
    def __init__(
        self,
        *,
        engine: PestDetectionEngine,
        repo: IPestDetectionRepository,
        ipm_service: IpmService,
        consent_repo: IConsentRepository,
        consent_engine: ConsentEngine,
        registry: type[PestDetectionAdapterRegistry] = PestDetectionAdapterRegistry,
        tiler: ImageTiler | None = None,
    ) -> None:
        self._engine = engine
        self._repo = repo
        self._ipm = ipm_service
        self._consent_repo = consent_repo
        self._consent_engine = consent_engine
        self._registry = registry
        self._tiler = tiler or ImageTiler()

    # ── Status (§6) ──

    def get_status(self) -> dict:
        """Availability payload used by the frontend to toggle the scan button."""
        preferred = self._registry.get_preferred()
        adapters: dict[str, dict] = {}
        for key in self._registry.all_keys():
            adapter = self._registry.get(key)
            adapters[key] = {
                "configured": adapter.is_configured(),
                "is_external": adapter.is_external,
                "requires_consent": adapter.requires_consent,
                "supports_modes": list(adapter.supports_modes),
            }
        return {
            "available": preferred is not None,
            "feature_enabled": settings.pest_detection_enabled,
            "primary_adapter": settings.pest_detection_primary_adapter,
            "active_adapter": preferred.adapter_key if preferred else None,
            "adapters": adapters,
        }

    # ── Detect (§6) ──

    def detect_pests(
        self,
        image_data: bytes,
        *,
        tenant_key: str,
        user_key: str,
        plant_instance_key: str | None,
        language: str = "de",
        adapter_key: str | None = None,
    ) -> dict:
        """Run pest detection over an uploaded photo. Never triggers a treatment."""
        self._validate_size(image_data)

        adapter = self._resolve_adapter(adapter_key)
        self._require_consent(adapter, user_key)

        # §8 — strip EXIF server-side (the second strip; the frontend does the
        # first) BEFORE tiling and before anything leaves the instance.
        try:
            clean = strip_exif_and_normalize(image_data, max_dimension=settings.pest_detection_max_image_dimension)
        except ValueError as exc:
            raise ValidationError("Image could not be decoded.") from exc

        image_hash = "sha256:" + hashlib.sha256(clean).hexdigest()
        tiles = self._tiler.tile(
            clean,
            tile=settings.pest_detection_tile_size,
            overlap=settings.pest_detection_tile_overlap,
        )

        result = adapter.detect(tiles, language=language)
        detection = self._engine.process_and_persist(
            result,
            tenant_key=tenant_key,
            user_key=user_key,
            plant_instance_key=plant_instance_key,
            image_hash=image_hash,
        )
        return self._to_response(detection)

    # ── History / feedback (§6) ──

    def get_history(self, *, tenant_key: str, plant_instance_key: str, limit: int = 20) -> list[dict]:
        return [self._to_response(d) for d in self._repo.list_for_plant(tenant_key, plant_instance_key, limit)]

    def submit_feedback(
        self,
        detection_key: str,
        *,
        tenant_key: str,
        finding_label: str,
        confirmed: bool,
        actual_label: str | None = None,
        was_beneficial: bool = False,
    ) -> dict:
        feedback = PestFeedback(
            finding_label=finding_label,
            confirmed=confirmed,
            actual_label=actual_label,
            was_beneficial=was_beneficial,
        )
        updated = self._repo.add_feedback(detection_key, tenant_key, feedback)
        if updated is None:
            raise NotFoundError("PestDetection", detection_key)
        return self._to_response(updated)

    # ── IPM bridge (§4.1 / REQ-010) — inspection only, never a treatment ──

    def create_inspection(self, detection_key: str, *, tenant_key: str, plant_key: str) -> dict:
        detection = self._repo.get(detection_key, tenant_key)
        if detection is None:
            raise NotFoundError("PestDetection", detection_key)

        pest_keys: list[str] = []
        symptoms: list[str] = []
        max_conf = 0.0
        for f in detection.findings:
            if f.category in {PestFindingCategory.PEST, PestFindingCategory.SYMPTOM}:
                symptoms.append(f.common_name)
                max_conf = max(max_conf, f.confidence)
                if f.matched_pest_key and f.matched_pest_key not in pest_keys:
                    pest_keys.append(f.matched_pest_key)

        inspection = Inspection(
            tenant_key=tenant_key,
            plant_key=plant_key,
            inspector="",
            pressure_level=self._pressure_from_confidence(max_conf),
            detected_pest_keys=pest_keys,
            symptoms_observed=symptoms,
            notes=f"Aus Schädlingserkennung {detection_key} (Bild-Signal, REQ-044).",
        )
        created = self._ipm.create_inspection(plant_key, inspection)
        if created.key:
            self._repo.link_suggested_inspection(detection_key, created.key)
        return {"inspection_key": created.key, "detected_pest_keys": pest_keys}

    # ── Health signal (§4.1 / REQ-043) ──

    def get_pest_signal_for_plant(self, *, tenant_key: str, plant_instance_key: str) -> dict:
        """Aggregate recent confident pest findings into a health signal.

        TODO(REQ-043): the ``HealthAssessmentEngine`` is not implemented yet
        (REQ-043 is spec-only in develop). This method already exposes the
        Schädlings-Bild-Signal in the shape the fusion will consume — a confirmed
        finding must strengthen the IPM/infestation signal (§9.1).
        """
        detections = self._repo.list_for_plant(tenant_key, plant_instance_key, limit=10)
        confirmed_pests: set[str] = set()
        max_conf = 0.0
        for d in detections:
            if not d.is_confident:
                continue
            for f in d.findings:
                if f.category in {PestFindingCategory.PEST, PestFindingCategory.SYMPTOM}:
                    max_conf = max(max_conf, f.confidence)
                    if f.matched_pest_key:
                        confirmed_pests.add(f.matched_pest_key)
        return {
            "has_pest_signal": bool(confirmed_pests) or max_conf >= ABSTAIN_CONFIDENCE,
            "pest_keys": sorted(confirmed_pests),
            "max_confidence": max_conf,
            "detections_considered": len(detections),
        }

    # ── internals ──

    def _resolve_adapter(self, adapter_key: str | None) -> PestDetectionAdapter:
        if not settings.pest_detection_enabled:
            raise FeatureNotConfiguredError("pest_detection", "Enable PEST_DETECTION_ENABLED.")
        adapter = self._registry.get(adapter_key) if adapter_key else self._registry.get_preferred()
        if adapter is None or not adapter.is_configured():
            raise FeatureNotConfiguredError(
                "pest_detection", "No pest-detection adapter is configured on this instance."
            )
        return adapter

    def _require_consent(self, adapter: PestDetectionAdapter, user_key: str) -> None:
        purpose = adapter.requires_consent
        if purpose is None:
            return
        if settings.kamerplanter_mode != "full":
            # Light mode has no consent subsystem and no cloud egress (§7).
            raise ConsentRequiredError(purpose)
        record = self._consent_repo.get_by_user_and_purpose(user_key, purpose)
        if not self._consent_engine.is_processing_allowed(purpose, record):
            raise ConsentRequiredError(purpose)

    @staticmethod
    def _validate_size(image_data: bytes) -> None:
        max_bytes = settings.pest_detection_max_image_size_mb * 1024 * 1024
        if len(image_data) > max_bytes:
            raise ValidationError(f"Image exceeds {settings.pest_detection_max_image_size_mb} MB limit.")
        if not image_data:
            raise ValidationError("Empty image upload.")

    @staticmethod
    def _pressure_from_confidence(confidence: float) -> PestPressureLevel:
        if confidence >= 0.7:
            return PestPressureLevel.HIGH
        if confidence >= 0.5:
            return PestPressureLevel.MEDIUM
        if confidence > 0.0:
            return PestPressureLevel.LOW
        return PestPressureLevel.NONE

    @staticmethod
    def _to_response(detection: PestDetection) -> dict:
        data = detection.model_dump(mode="json")
        data["key"] = detection.key
        # §8 — the disclaimer is never empty in any response (Szenario 6).
        if not data.get("disclaimer"):
            from app.domain.interfaces.pest_detection_adapter import DEFAULT_PEST_DISCLAIMER

            data["disclaimer"] = DEFAULT_PEST_DISCLAIMER
        return data
