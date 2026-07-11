"""REQ-029 §3.5 — identification engine.

Orchestrates a single identification: image validation, EXIF stripping and
normalization, the adapter call, matching suggestions against local species
master data, persisting the request (without the image), and resolving a
user's result selection (``select_result`` / ``confirm_identification``).

The engine programs against the ``PlantIdentificationAdapter`` interface only
(REQ-029-A §0.1.1 point 5), so Phase 2 needs no engine change.
"""

import hashlib
from datetime import UTC, datetime

import structlog

from app.common.exceptions import NotFoundError, PayloadTooLargeError, UnsupportedMediaTypeError, ValidationError
from app.config.settings import settings
from app.domain.calculators.image_preprocessor import strip_exif_and_normalize
from app.domain.interfaces.identification_repository import IIdentificationRepository
from app.domain.interfaces.plant_identification_adapter import (
    IdentificationResult,
    PlantIdentificationAdapter,
    PlantOrgan,
)
from app.domain.interfaces.species_repository import ISpeciesRepository
from app.domain.models.identification import IdentificationCandidate, IdentificationRequest

logger = structlog.get_logger()

_JPEG_MAGIC = b"\xff\xd8"
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


class IdentificationEngine:
    """Coordinates plant identification and mapping onto local master data."""

    def __init__(
        self,
        species_repo: ISpeciesRepository,
        identification_repo: IIdentificationRepository,
    ) -> None:
        self._species_repo = species_repo
        self._identification_repo = identification_repo

    # ── thresholds (config-driven) ──────────────────────────────────────

    @property
    def _max_image_size_bytes(self) -> int:
        return settings.identification_max_image_size_mb * 1024 * 1024

    @property
    def _confidence_auto_accept(self) -> float:
        return settings.identification_confidence_auto_accept

    @property
    def _confidence_min_show(self) -> float:
        return settings.identification_confidence_min_show

    @property
    def _max_image_dimension(self) -> int:
        return settings.identification_max_image_dimension

    # ── image handling ──────────────────────────────────────────────────

    def validate_image(self, image_data: bytes) -> None:
        """Validate raw image bytes before processing.

        Raises:
            PayloadTooLargeError: image exceeds the configured size limit.
            UnsupportedMediaTypeError: bytes are not JPEG or PNG.
        """
        if len(image_data) > self._max_image_size_bytes:
            raise PayloadTooLargeError(self._max_image_size_bytes)

        if not (image_data[:2] == _JPEG_MAGIC or image_data[:8] == _PNG_MAGIC):
            raise UnsupportedMediaTypeError("unknown", ["image/jpeg", "image/png"])

    def compute_image_hash(self, image_data: bytes) -> str:
        """SHA-256 hash (truncated) of the image — for audit/dedup, not storage."""
        return f"sha256:{hashlib.sha256(image_data).hexdigest()[:32]}"

    # ── identification ──────────────────────────────────────────────────

    def identify(
        self,
        adapter: PlantIdentificationAdapter,
        image_data: bytes,
        *,
        organ: PlantOrgan = PlantOrgan.AUTO,
        language: str = "de",
        tenant_key: str,
        user_key: str,
    ) -> dict:
        """Identify a plant, match against local species, and persist the request.

        The user image is EXIF-stripped and normalized before it ever reaches
        the adapter, and is discarded immediately afterwards — only the request
        metadata and (matched) suggestions are stored.
        """
        self.validate_image(image_data)

        try:
            clean_image = strip_exif_and_normalize(image_data, max_dimension=self._max_image_dimension)
        except ValueError as exc:
            raise UnsupportedMediaTypeError("unknown", ["image/jpeg", "image/png"]) from exc

        # Hash the sanitized image actually sent to the third party.
        image_hash = self.compute_image_hash(clean_image)

        result: IdentificationResult = adapter.identify(
            clean_image,
            organ=organ,
            language=language,
        )

        if not result.is_plant:
            self._persist(
                tenant_key=tenant_key,
                user_key=user_key,
                adapter_key=adapter.adapter_key,
                image_hash=image_hash,
                organ=organ,
                candidates=[],
                api_response_time_ms=result.api_response_time_ms,
            )
            return {
                "request_key": None,
                "is_plant": False,
                "suggestions": [],
                "message": "No plant material detected in image.",
            }

        candidates = self._match_candidates(result)

        saved = self._persist(
            tenant_key=tenant_key,
            user_key=user_key,
            adapter_key=adapter.adapter_key,
            image_hash=image_hash,
            organ=organ,
            candidates=candidates,
            api_response_time_ms=result.api_response_time_ms,
        )

        return {
            "request_key": saved.key,
            "is_plant": True,
            "suggestions": [c.model_dump() for c in candidates],
        }

    def identify_raw(
        self,
        adapter: PlantIdentificationAdapter,
        image_data: bytes,
        *,
        organ: PlantOrgan = PlantOrgan.AUTO,
        language: str = "de",
    ) -> IdentificationResult:
        """Run an identification and return the *raw* adapter result.

        REQ-034 §4a — used by the photo-quality assessment, which only needs the
        suggestions + ``is_plant`` flag to derive an Ampel verdict and does **not**
        create an identification-history record (the verdict is persisted on the
        attachment instead, §4a vs §4). The image is still validated, EXIF-stripped
        and normalized before it reaches the adapter, exactly like :meth:`identify`.
        """
        self.validate_image(image_data)
        try:
            clean_image = strip_exif_and_normalize(image_data, max_dimension=self._max_image_dimension)
        except ValueError as exc:
            raise UnsupportedMediaTypeError("unknown", ["image/jpeg", "image/png"]) from exc
        return adapter.identify(clean_image, organ=organ, language=language)

    def _match_candidates(self, result: IdentificationResult) -> list[IdentificationCandidate]:
        """Map adapter suggestions onto local species, filtering by min confidence."""
        candidates: list[IdentificationCandidate] = []
        for suggestion in result.suggestions:
            if suggestion.confidence < self._confidence_min_show:
                continue

            matched = None
            if suggestion.scientific_name:
                # Match on the canonical dedup key (REQ-048 Stufe 1) so a hybrid-
                # marker/casing/whitespace variant of an existing species
                # (Fragaria × ananassa vs Fragaria x ananassa) resolves to it and
                # reports species_in_database=True instead of looking un-catalogued.
                matched = self._species_repo.get_by_normalized_scientific_name(suggestion.scientific_name)

            candidates.append(
                IdentificationCandidate(
                    rank=suggestion.rank,
                    scientific_name=suggestion.scientific_name,
                    common_names=suggestion.common_names,
                    family=suggestion.family,
                    genus=suggestion.genus,
                    confidence=suggestion.confidence,
                    external_id=suggestion.external_id,
                    image_url=suggestion.image_url,
                    gbif_id=suggestion.gbif_id,
                    matched_species_key=matched.key if matched else None,
                    species_in_database=matched is not None,
                    auto_accept=suggestion.confidence >= self._confidence_auto_accept,
                )
            )
        return candidates

    def _persist(
        self,
        *,
        tenant_key: str,
        user_key: str,
        adapter_key: str,
        image_hash: str,
        organ: PlantOrgan,
        candidates: list[IdentificationCandidate],
        api_response_time_ms: int,
    ) -> IdentificationRequest:
        now = datetime.now(tz=UTC)
        request = IdentificationRequest(
            tenant_key=tenant_key,
            user_key=user_key,
            adapter_key=adapter_key,
            request_type="identification",
            image_hash=image_hash,
            image_organ=organ.value,
            status="completed",
            results=candidates,
            selected_result_rank=None,
            api_response_time_ms=api_response_time_ms,
            image_deleted_at=now,
        )
        return self._identification_repo.create(request)

    # ── selection ───────────────────────────────────────────────────────

    def select_result(
        self,
        request_key: str,
        selected_rank: int,
        *,
        tenant_key: str,
    ) -> dict:
        """Persist the user's chosen candidate (REQ-029-A §0.1.1 point 3).

        No silent auto-creation of the top-1 ever happens — the selection is
        an explicit user action. Returns the chosen candidate so the caller can
        create a PlantInstance / link a species.

        Raises:
            NotFoundError: request does not exist in this tenant.
            ValidationError: rank is out of range.
        """
        request = self._identification_repo.get(request_key, tenant_key)
        if request is None:
            raise NotFoundError("IdentificationRequest", request_key)

        if selected_rank < 1 or selected_rank > len(request.results):
            raise ValidationError(
                f"Invalid selected_rank {selected_rank} for {len(request.results)} result(s).",
                details=[
                    {
                        "field": "selected_rank",
                        "reason": "Rank out of range for this request.",
                        "code": "INVALID_RANK",
                    }
                ],
            )

        selected = request.results[selected_rank - 1]
        self._identification_repo.set_selected_rank(request_key, tenant_key, selected_rank)

        return {
            "request_key": request_key,
            "selected_rank": selected_rank,
            "matched_species_key": selected.matched_species_key,
            "scientific_name": selected.scientific_name,
            "common_names": selected.common_names,
            "family": selected.family,
            "genus": selected.genus,
            "gbif_id": selected.gbif_id,
            "confidence": selected.confidence,
            "species_in_database": selected.species_in_database,
        }
