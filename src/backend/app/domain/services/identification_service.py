"""REQ-029 §3.6 — Service layer for AI-based plant identification.

Responsibilities:
- Consent gate (``plant_identification``, REQ-025 §5).
- EXIF stripping before any image leaves the system (REQ-029 §5.4).
- Adapter selection via the registry (``get_preferred``) with a
  confidence-based fallback chain (REQ-029-A §0.1 / Szenario A4).
- Request logging into ``identification_requests`` WITHOUT image persistence.
- Confirmation / result selection.

The service is async because adapters are async (httpx); the ArangoDB
repositories are synchronous (python-arango), matching the project's
established pattern of async endpoints calling sync repositories.
"""

import hashlib
from datetime import UTC, datetime
from typing import Any

import structlog

from app.common.exceptions import (
    ForbiddenError,
    PayloadTooLargeError,
    RateLimitError,
    UnsupportedMediaTypeError,
    ValidationError,
)
from app.config.settings import settings
from app.domain.engines.consent_engine import CONSENT_PURPOSE_PLANT_IDENTIFICATION, ConsentEngine
from app.domain.interfaces.consent_repository import IConsentRepository
from app.domain.interfaces.identification_repository import IIdentificationRepository
from app.domain.interfaces.plant_identification_adapter import PlantIdentificationAdapter
from app.domain.interfaces.species_repository import ISpeciesRepository
from app.domain.models.identification import (
    DiagnosisRequest,
    IdentificationRequest,
    IdentificationResult,
    PlantOrgan,
)
from app.domain.services.identification_adapter_registry import IdentificationAdapterRegistry
from app.domain.services.image_processing import is_supported_image, strip_exif

logger = structlog.get_logger()


class IdentificationService:
    """Orchestrates plant identification and master-data matching."""

    def __init__(
        self,
        identification_repo: IIdentificationRepository,
        species_repo: ISpeciesRepository,
        consent_repo: IConsentRepository,
        consent_engine: ConsentEngine,
        registry: type[IdentificationAdapterRegistry] = IdentificationAdapterRegistry,
    ) -> None:
        self._repo = identification_repo
        self._species_repo = species_repo
        self._consent_repo = consent_repo
        self._consent_engine = consent_engine
        self._registry = registry

    # ── Availability / status ──────────────────────────────────────────

    def is_available(self) -> bool:
        """True if at least one identification adapter is configured."""
        return self._registry.get_preferred() is not None

    async def get_status(self) -> dict[str, Any]:
        """Status of all registered adapters (for the frontend feature toggle)."""
        status: dict[str, Any] = {}
        for key in self._registry.all_keys():
            try:
                adapter = self._registry.get(key)
                healthy = await adapter.health_check()
                api_key = getattr(adapter, "_api_key", "configured")
                status[key] = {
                    "configured": bool(api_key),
                    "healthy": healthy,
                    "supports_health": adapter.supports_health_assessment,
                    "rate_limit_per_day": adapter.rate_limit_per_day,
                }
            except Exception:  # noqa: BLE001 — status must never raise
                status[key] = {"configured": False, "healthy": False}
        return status

    # ── Identification ─────────────────────────────────────────────────

    async def identify_plant(
        self,
        image_data: bytes,
        *,
        organ: PlantOrgan = PlantOrgan.AUTO,
        include_health: bool = False,
        language: str = "de",
        tenant_key: str,
        user_key: str,
        adapter_key: str | None = None,
    ) -> dict[str, Any]:
        """Identify a plant and match suggestions against local species data.

        Raises:
            ForbiddenError: Consent ``plant_identification`` not granted.
            ValidationError: Feature not configured / no usable result.
            UnsupportedMediaTypeError: Image is not JPEG/PNG.
            PayloadTooLargeError: Image exceeds the configured size limit.
        """
        self._require_consent(user_key)
        self._validate_image(image_data)
        clean_image = strip_exif(image_data)
        image_hash = self._compute_image_hash(clean_image)

        chain = self._resolve_chain(adapter_key)
        if not chain:
            raise ValidationError("Plant identification is not configured. Set an identification adapter API key.")

        result, used_adapter = await self._run_chain(
            chain,
            clean_image,
            organ=organ,
            include_health=include_health,
            language=language,
        )

        if not result.is_plant:
            return {
                "request_key": None,
                "is_plant": False,
                "adapter_key": used_adapter.adapter_key,
                "suggestions": [],
                "health_assessment": None,
                "message": "No plant material detected in image.",
            }

        enriched = self._enrich_suggestions(result)
        health = result.health_assessment.model_dump() if result.health_assessment else None

        request = IdentificationRequest(
            tenant_key=tenant_key,
            user_key=user_key,
            adapter_key=used_adapter.adapter_key,
            request_type="identification",
            image_hash=image_hash,
            image_organ=organ.value,
            status="completed",
            results=enriched,
            selected_result_rank=None,
            health_assessment=health,
            api_response_time_ms=result.api_response_time_ms,
            image_deleted_at=datetime.now(tz=UTC),
        )
        saved = self._repo.create(request)

        return {
            "request_key": saved.key,
            "is_plant": True,
            "adapter_key": used_adapter.adapter_key,
            "suggestions": enriched,
            "health_assessment": health,
        }

    async def diagnose_plant(
        self,
        image_data: bytes,
        *,
        plant_instance_key: str | None = None,
        language: str = "de",
        tenant_key: str,
        user_key: str,
    ) -> dict[str, Any]:
        """Diagnose diseases/pests from an image (requires a health-capable adapter)."""
        self._require_consent(user_key)
        self._validate_image(image_data)
        clean_image = strip_exif(image_data)
        image_hash = self._compute_image_hash(clean_image)

        adapter = self._registry.get_preferred()
        if adapter is None or not adapter.supports_health_assessment:
            raise ValidationError("Health assessment requires a diagnosis-capable adapter. None is configured.")

        health = await adapter.diagnose(clean_image, language=language)

        request = DiagnosisRequest(
            tenant_key=tenant_key,
            user_key=user_key,
            adapter_key=adapter.adapter_key,
            plant_instance_key=plant_instance_key,
            image_hash=image_hash,
            status="completed",
            health_assessment=health.model_dump(),
            image_deleted_at=datetime.now(tz=UTC),
        )
        saved = self._repo.create_diagnosis(request)

        return {
            "request_key": saved.key,
            "health_assessment": health.model_dump(),
            "plant_instance_key": plant_instance_key,
        }

    async def confirm_identification(
        self,
        request_key: str,
        selected_rank: int,
        *,
        tenant_key: str,
    ) -> dict[str, Any]:
        """Confirm a suggestion; returns the matched species for instance creation."""
        request = self._repo.get(request_key, tenant_key)
        if request is None:
            raise ValidationError(f"Identification request '{request_key}' not found.")
        if selected_rank < 1 or selected_rank > len(request.results):
            raise ValidationError(f"Invalid rank {selected_rank}.")

        selected = request.results[selected_rank - 1]
        self._repo.update_selected_rank(request_key, tenant_key, selected_rank)

        return {
            "request_key": request_key,
            "matched_species_key": selected.get("matched_species_key"),
            "scientific_name": selected.get("scientific_name"),
            "common_names": selected.get("common_names", []),
            "confidence": selected.get("confidence"),
            "species_in_database": selected.get("species_in_database", False),
        }

    def get_history(self, *, tenant_key: str, user_key: str, limit: int = 20) -> list[dict[str, Any]]:
        """Return the identification history for a user within a tenant."""
        return self._repo.list_history(tenant_key, user_key, limit)

    # ── Internal helpers ───────────────────────────────────────────────

    def _require_consent(self, user_key: str) -> None:
        consent = self._consent_repo.get_by_user_and_purpose(user_key, CONSENT_PURPOSE_PLANT_IDENTIFICATION)
        if not self._consent_engine.is_processing_allowed(CONSENT_PURPOSE_PLANT_IDENTIFICATION, consent):
            raise ForbiddenError("Consent 'plant_identification' is required to use photo identification.")

    def _validate_image(self, image_data: bytes) -> None:
        max_bytes = settings.identification_max_image_size_mb * 1024 * 1024
        if len(image_data) > max_bytes:
            raise PayloadTooLargeError(max_bytes)
        if not is_supported_image(image_data):
            raise UnsupportedMediaTypeError("unknown", ["image/jpeg", "image/png"])

    @staticmethod
    def _compute_image_hash(image_data: bytes) -> str:
        return f"sha256:{hashlib.sha256(image_data).hexdigest()[:32]}"

    def _resolve_chain(self, adapter_key: str | None) -> list[PlantIdentificationAdapter]:
        if adapter_key:
            try:
                adapter = self._registry.get(adapter_key)
            except KeyError:
                return []
            return [adapter]
        return self._registry.get_fallback_chain()

    async def _run_chain(
        self,
        chain: list[PlantIdentificationAdapter],
        image_data: bytes,
        *,
        organ: PlantOrgan,
        include_health: bool,
        language: str,
    ) -> tuple[IdentificationResult, PlantIdentificationAdapter]:
        """Run adapters in order, advancing to the next one on low confidence.

        Falls back to the next adapter when the top suggestion's confidence is
        below ``identification_confidence_auto_accept`` (REQ-029 Szenario A4).
        The last adapter's result is returned even if its confidence is low.
        """
        threshold = settings.identification_confidence_auto_accept
        last_result: IdentificationResult | None = None
        last_adapter: PlantIdentificationAdapter = chain[0]

        for index, adapter in enumerate(chain):
            result = await adapter.identify(
                image_data,
                organ=organ,
                include_health=include_health,
                language=language,
            )
            last_result = result
            last_adapter = adapter

            top_confidence = result.suggestions[0].confidence if result.suggestions else 0.0
            is_last = index == len(chain) - 1
            if not result.is_plant or top_confidence >= threshold or is_last:
                return result, adapter
            logger.info(
                "identification_fallback",
                from_adapter=adapter.adapter_key,
                top_confidence=top_confidence,
                threshold=threshold,
            )

        # chain is non-empty, so last_result is set
        assert last_result is not None  # noqa: S101 — invariant on non-empty chain
        return last_result, last_adapter

    def _enrich_suggestions(self, result: IdentificationResult) -> list[dict[str, Any]]:
        min_show = settings.identification_confidence_min_show
        auto_accept = settings.identification_confidence_auto_accept
        enriched: list[dict[str, Any]] = []
        for suggestion in result.suggestions:
            if suggestion.confidence < min_show:
                continue
            matched = self._species_repo.get_by_scientific_name(suggestion.scientific_name)
            # Adapters that only return a scientific name (e.g. the local
            # embedding adapter) get common names backfilled from master data.
            common_names = suggestion.common_names or (getattr(matched, "common_names", []) if matched else [])
            enriched.append(
                {
                    "rank": suggestion.rank,
                    "scientific_name": suggestion.scientific_name,
                    "common_names": common_names,
                    "family": suggestion.family,
                    "genus": suggestion.genus,
                    "confidence": suggestion.confidence,
                    "external_id": suggestion.external_id,
                    "image_url": suggestion.image_url,
                    "gbif_id": suggestion.gbif_id,
                    "matched_species_key": matched.key if matched else None,
                    "species_in_database": matched is not None,
                    "auto_accept": suggestion.confidence >= auto_accept,
                }
            )
        return enriched

    @staticmethod
    def raise_if_rate_limited(remaining: int, adapter_key: str) -> None:
        """Helper used by the API to convert exhausted quota into HTTP 429."""
        if remaining <= 0:
            raise RateLimitError(adapter_key, retry_after=86400)
