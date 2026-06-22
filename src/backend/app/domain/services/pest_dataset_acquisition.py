"""REQ-044 WP-3 — cold-start dataset acquisition for few-shot pest detection.

Mirrors the REQ-029-A reference-image pipeline but targets the pest taxonomy and
runs over a CONFIGURED LIST of media sources (GBIF + iNaturalist + iDigBio). For
each class it collects candidates from every active source in priority order,
de-duplicates them (by source record id, falling back to a URL hash), then keeps
only license-acceptable images (CC0/CC-BY always; CC-BY-NC only when the
application runs non-commercially, see ``pest_reference_allow_noncommercial``),
downloads, quality-gates, strips EXIF and indexes the frozen-DINOv2 prototype in
the inference service — until ``pest_reference_min_usable`` is reached. No image
is persisted; an attribution manifest is returned for CC-BY(-NC) compliance.

The trained object detector (Modus 1, D-FINE/RF-DETR) stays out of scope —
externally blocked on WP-1 (license sign-off) and WP-2 (benchmark). This builds
the license-safe symptom/on-leaf path only.
"""

import hashlib
import io
from collections.abc import Sequence

import structlog
from PIL import Image

from app.config.settings import settings
from app.domain.calculators.image_preprocessor import strip_exif_and_normalize
from app.domain.interfaces.pest_media_source import PestMediaSource
from app.domain.models.pest_taxonomy import PEST_TAXONOMY, PestTaxon
from app.domain.models.reference_image import MediaCandidate, ReferenceLicense
from app.domain.services.reference_image_license import is_acceptable

logger = structlog.get_logger()


class PestDatasetAcquisitionService:
    """Build the few-shot prototype index from multiple CC-licensed sources."""

    def __init__(
        self,
        sources: Sequence[PestMediaSource],
        inference,
        *,
        allow_noncommercial: bool | None = None,
    ) -> None:
        if not sources:
            raise ValueError("PestDatasetAcquisitionService needs at least one media source")
        # Keep the configured priority order: earlier sources are preferred and
        # fill the per-class quota first.
        self._sources: list[PestMediaSource] = list(sources)
        self._inference = inference
        self._allow_noncommercial = (
            settings.pest_reference_allow_noncommercial if allow_noncommercial is None else allow_noncommercial
        )

    def acquire_for_class(self, taxon: PestTaxon) -> dict:
        """Acquire and index prototypes for one taxonomy class. Returns a summary."""
        candidates = self._collect_candidates(taxon)

        accepted = 0
        rejected_license = 0
        rejected_attribution = 0
        rejected_quality = 0
        rejected_error = 0
        manifest: list[dict] = []

        for candidate, source in candidates:
            if accepted >= settings.pest_reference_min_usable:
                break
            if not is_acceptable(candidate.license, allow_noncommercial=self._allow_noncommercial):
                rejected_license += 1
                continue
            # CC-BY and CC-BY-NC both require attribution; without a recoverable
            # creator/rightsHolder we cannot reuse the image compliantly. CC0
            # needs no attribution.
            if self._requires_attribution(candidate.license) and not (candidate.attribution or "").strip():
                rejected_attribution += 1
                continue
            try:
                raw = source.download(candidate.url)
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

    # ── internals ──────────────────────────────────────────────────────

    def _collect_candidates(self, taxon: PestTaxon) -> list[tuple[MediaCandidate, PestMediaSource]]:
        """Gather de-duplicated candidates from all sources in priority order.

        Per-source failures are logged and skipped so one dead source never
        blocks the rest. De-duplication is keyed on ``source|source_record_id``
        (stable across sources for the same upstream record) with a URL hash
        fallback when no record id is present.
        """
        seen: set[str] = set()
        collected: list[tuple[MediaCandidate, PestMediaSource]] = []
        per_source_limit = settings.pest_reference_max_candidates
        for source in self._sources:
            try:
                candidates = source.list_media(taxon, limit=per_source_limit)
            except Exception as exc:
                logger.info(
                    "pest_source_list_failed",
                    label=taxon.slug,
                    source=getattr(source, "source_key", type(source).__name__),
                    error=str(exc),
                )
                continue
            for candidate in candidates:
                key = self._dedup_key(candidate)
                if key in seen:
                    continue
                seen.add(key)
                collected.append((candidate, source))
        return collected

    @staticmethod
    def _dedup_key(candidate: MediaCandidate) -> str:
        if candidate.source_record_id:
            return f"{candidate.source}:{candidate.source_record_id}"
        return "url:" + hashlib.sha256(candidate.url.encode("utf-8")).hexdigest()

    @staticmethod
    def _requires_attribution(license_value: ReferenceLicense) -> bool:
        """CC-BY and CC-BY-NC require attribution; CC0 does not."""
        return license_value in {ReferenceLicense.CC_BY, ReferenceLicense.CC_BY_NC}

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
