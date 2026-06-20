"""REQ-044 WP-3 — cold-start dataset acquisition for few-shot pest detection.

Mirrors the REQ-029-A reference-image pipeline but targets the pest taxonomy:
for each class, query GBIF (public occurrence search — no credentials), keep
only CC0/CC-BY images (per-image license, §WP-3.1), download, quality-gate,
strip EXIF, and index the frozen-DINOv2 prototype in the inference service. No
image is persisted; an attribution manifest is returned for CC-BY compliance.

The trained object detector (Modus 1, D-FINE/RF-DETR) stays out of scope —
externally blocked on WP-1 (license sign-off) and WP-2 (benchmark). This builds
the license-safe symptom/on-leaf path only.
"""

import io

import structlog
from PIL import Image

from app.config.settings import settings
from app.data_access.external.gbif_media_client import GBIFMediaClient
from app.data_access.external.pest_inference_client import PestDetectionInferenceClient
from app.domain.calculators.image_preprocessor import strip_exif_and_normalize
from app.domain.models.pest_taxonomy import PEST_TAXONOMY, PestTaxon
from app.domain.models.reference_image import ReferenceLicense
from app.domain.services.reference_image_license import is_acceptable

logger = structlog.get_logger()


class PestDatasetAcquisitionService:
    """Build the few-shot prototype index from CC0/CC-BY GBIF images."""

    def __init__(
        self,
        media_client: GBIFMediaClient,
        inference: PestDetectionInferenceClient,
    ) -> None:
        self._media = media_client
        self._inference = inference

    def acquire_for_class(self, taxon: PestTaxon) -> dict:
        """Acquire and index prototypes for one taxonomy class. Returns a summary."""
        if not taxon.gbif_taxon_key:
            return self._summary(taxon, candidates=0, accepted=0, manifest=[])

        candidates = self._media.list_media(int(taxon.gbif_taxon_key), limit=settings.pest_reference_max_candidates)
        accepted = 0
        rejected_license = 0
        rejected_attribution = 0
        rejected_quality = 0
        rejected_error = 0
        manifest: list[dict] = []

        for candidate in candidates:
            if accepted >= settings.pest_reference_min_usable:
                break
            if not is_acceptable(candidate.license):
                rejected_license += 1
                continue
            # CC-BY requires attribution; without a recoverable creator/rightsHolder
            # we cannot reuse the image compliantly. CC0 needs no attribution.
            if candidate.license == ReferenceLicense.CC_BY and not (candidate.attribution or "").strip():
                rejected_attribution += 1
                continue
            try:
                raw = self._media.download(candidate.url)
            except Exception:
                rejected_error += 1
                continue
            if not self._passes_quality(raw):
                rejected_quality += 1
                continue
            try:
                clean = strip_exif_and_normalize(raw, max_dimension=settings.pest_detection_max_image_dimension)
                self._inference.upsert_prototype(
                    clean,
                    label=taxon.slug,
                    category=taxon.category.value,
                    source=candidate.source,
                    source_record_id=candidate.source_record_id,
                    license=candidate.license.value,
                    attribution=candidate.attribution,
                    source_url=candidate.url,
                )
            except Exception as exc:
                rejected_error += 1
                logger.info("pest_prototype_index_failed", label=taxon.slug, error=str(exc))
                continue
            accepted += 1
            manifest.append(
                {
                    "label": taxon.slug,
                    "category": taxon.category.value,
                    "source": candidate.source,
                    "source_record_id": candidate.source_record_id,
                    "source_url": candidate.url,
                    "license": candidate.license.value,
                    "attribution": candidate.attribution,
                }
            )

        summary = self._summary(taxon, candidates=len(candidates), accepted=accepted, manifest=manifest)
        summary.update(
            rejected_license=rejected_license,
            rejected_attribution=rejected_attribution,
            rejected_quality=rejected_quality,
            rejected_error=rejected_error,
        )
        logger.info("pest_dataset_class_acquired", **{k: v for k, v in summary.items() if k != "manifest"})
        return summary

    def acquire_all(self) -> dict:
        """Acquire prototypes for every class in the taxonomy. Returns results + manifest."""
        results = [self.acquire_for_class(t) for t in PEST_TAXONOMY]
        manifest = [entry for r in results for entry in r["manifest"]]
        return {
            "classes": len(results),
            "total_accepted": sum(r["accepted"] for r in results),
            "results": [{k: v for k, v in r.items() if k != "manifest"} for r in results],
            "manifest": manifest,
        }

    @staticmethod
    def _passes_quality(image_data: bytes) -> bool:
        """Reject too-small or extreme-aspect crops (insect images are tight)."""
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                width, height = img.size
        except Exception:
            return False
        if min(width, height) < settings.pest_reference_min_dimension:
            return False
        long_edge, short_edge = max(width, height), min(width, height)
        if short_edge == 0:
            return False
        return (long_edge / short_edge) <= settings.pest_reference_max_aspect_ratio

    @staticmethod
    def _summary(taxon: PestTaxon, *, candidates: int, accepted: int, manifest: list[dict]) -> dict:
        return {
            "label": taxon.slug,
            "category": taxon.category.value,
            "scientific_name": taxon.scientific_name,
            "candidates_found": candidates,
            "accepted": accepted,
            "usable": accepted >= settings.pest_reference_min_usable,
            "manifest": manifest,
        }
