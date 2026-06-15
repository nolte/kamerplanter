"""REQ-029-A §4 — License-compliant reference-image acquisition pipeline.

For a given species this service:

1. resolves the GBIF ``taxonKey`` from the scientific name,
2. lists candidate still-images with normalised licenses,
3. keeps only CC0 / CC-BY (rejects CC-BY-NC / CC-BY-SA / unknown),
4. downloads + curates each accepted candidate (resolution / aspect ratio),
5. strips EXIF, embeds it via the inference-service and upserts the embedding
   + provenance into the pgvector index — **no original image is persisted**,
6. records a per-species coverage report; species with fewer than the
   configured minimum usable references are marked "not recognizable".

Runs synchronously (invoked from a Celery task, WS-4).
"""

import io

import structlog
from PIL import Image, UnidentifiedImageError

from app.config.settings import settings
from app.domain.models.identification import ReferenceImageJob
from app.domain.models.reference_image import (
    AcquisitionResult,
    MediaCandidate,
)
from app.domain.services.image_processing import strip_exif
from app.domain.services.reference_image_license import is_acceptable

logger = structlog.get_logger()


class ReferenceImageService:
    """Acquires and indexes license-clean reference embeddings per species."""

    def __init__(self, gbif_adapter, media_client, inference_client, reference_repo) -> None:  # noqa: ANN001
        self._gbif = gbif_adapter
        self._media = media_client
        self._inference = inference_client
        self._repo = reference_repo

    def acquire_for_species(
        self,
        species_key: str,
        scientific_name: str,
    ) -> AcquisitionResult:
        """Acquire, filter, embed and index reference images for one species."""
        result = AcquisitionResult(species_key=species_key, scientific_name=scientific_name)

        match = self._gbif.match_species(scientific_name)
        if match is None:
            logger.info("reference_acquire_no_taxon", scientific_name=scientific_name)
            return self._persist(result)

        candidates = self._media.list_media(match.usage_key, limit=settings.reference_image_max_candidates)
        result.candidates_found = len(candidates)

        for candidate in candidates:
            self._process_candidate(candidate, species_key, scientific_name, result)

        result.usable_for_recognition = result.accepted >= settings.reference_image_min_usable
        return self._persist(result)

    # ── Internal ───────────────────────────────────────────────────────

    def _process_candidate(
        self,
        candidate: MediaCandidate,
        species_key: str,
        scientific_name: str,
        result: AcquisitionResult,
    ) -> None:
        if not is_acceptable(candidate.license):
            result.rejected_license += 1
            return

        try:
            image_data = self._media.download(candidate.url)
        except Exception as exc:  # noqa: BLE001 — one bad image must not abort the run
            logger.info("reference_download_failed", url=candidate.url, error=str(exc))
            result.rejected_error += 1
            return

        if not self._passes_quality(image_data):
            result.rejected_quality += 1
            return

        try:
            clean = strip_exif(image_data)
            embedding = self._inference.embed(clean)
            self._inference.upsert_reference(
                species_key=species_key,
                scientific_name=scientific_name,
                source=candidate.source,
                organ=candidate.organ,
                source_record_id=candidate.source_record_id,
                license=candidate.license.value,
                attribution=candidate.attribution,
                source_url=candidate.url,
                embedding=embedding,
            )
        except Exception as exc:  # noqa: BLE001 — keep acquiring the rest
            logger.info("reference_embed_failed", url=candidate.url, error=str(exc))
            result.rejected_error += 1
            return

        result.accepted += 1
        key = candidate.license.value
        result.license_breakdown[key] = result.license_breakdown.get(key, 0) + 1

    def _passes_quality(self, image_data: bytes) -> bool:
        """Reject images below the minimum resolution or with extreme aspect."""
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                width, height = img.size
        except (UnidentifiedImageError, OSError):  # fmt: skip
            return False
        if min(width, height) < settings.reference_image_min_dimension:
            return False
        if height == 0 or width == 0:
            return False
        aspect = max(width, height) / min(width, height)
        return aspect <= settings.reference_image_max_aspect_ratio

    def _persist(self, result: AcquisitionResult) -> AcquisitionResult:
        job = ReferenceImageJob(
            species_key=result.species_key,
            scientific_name=result.scientific_name,
            status="completed",
            candidates_found=result.candidates_found,
            accepted=result.accepted,
            rejected_license=result.rejected_license,
            rejected_quality=result.rejected_quality + result.rejected_error,
            license_breakdown=result.license_breakdown,
            usable_for_recognition=result.usable_for_recognition,
        )
        self._repo.upsert(job)
        logger.info(
            "reference_acquire_done",
            species_key=result.species_key,
            accepted=result.accepted,
            candidates=result.candidates_found,
            usable=result.usable_for_recognition,
        )
        return result
