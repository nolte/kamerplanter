"""REQ-044 §3 — Self-Hosted pest-detection adapters (no data egress).

``LocalPestSymptomAdapter`` (Modus 2, Phase-1 default) and
``LocalPestDetectorAdapter`` (Modus 1, Phase 2). Both run per-tile against the
self-hosted inference-service and merge boxes back into the full image. The
trained weights / few-shot index are externally blocked (WP-1/2/3); until the
service exposes ``/pest/*`` both adapters report themselves as unconfigured and
the feature degrades gracefully.
"""

from typing import Any

from app.common.enums import PestDetectionSource, PestFindingCategory, PestFindingMode
from app.config.settings import settings
from app.data_access.external.pest_inference_client import PestDetectionInferenceClient
from app.domain.calculators.image_tiler import ImageTiler
from app.domain.interfaces.pest_detection_adapter import (
    BoundingBox,
    PestDetectionAdapter,
    PestDetectionResult,
    PestFinding,
)
from app.domain.models.pest_taxonomy import get_taxon
from app.domain.services.pest_detection_registry import PestDetectionAdapterRegistry


def _finding_from_raw(raw: dict[str, Any], *, default_mode: PestFindingMode) -> PestFinding:
    """Map a raw inference dict onto a typed finding, enriched from the taxonomy.

    Category and common name are taken from the verified taxonomy (WP-4) when the
    label is known, so a beneficial is never relabelled as a pest (§9.1).
    """
    label = raw["label"]
    taxon = get_taxon(label)
    if taxon is not None:
        category = taxon.category
        common_name = taxon.common_name_de
    else:
        category = PestFindingCategory(raw.get("category", PestFindingCategory.UNKNOWN.value))
        common_name = raw.get("common_name", label)

    bbox = None
    raw_box = raw.get("bounding_box")
    if raw_box:
        bbox = BoundingBox(**raw_box)

    return PestFinding(
        label=label,
        category=category,
        common_name=common_name,
        confidence=float(raw["confidence"]),
        mode=PestFindingMode(raw.get("mode", default_mode.value)),
        bounding_box=bbox,
    )


class _LocalPestInferenceAdapter(PestDetectionAdapter):
    """Shared per-tile inference + box-merge logic for the self-hosted adapters."""

    _source: PestDetectionSource
    _mode: PestFindingMode
    _enabled_flag: str  # settings attribute name gating this adapter

    def __init__(self) -> None:
        self._client = PestDetectionInferenceClient(settings.inference_service_url)
        self._tiler = ImageTiler()

    is_external = False
    requires_consent = None

    def is_configured(self) -> bool:
        return bool(getattr(settings, self._enabled_flag)) and self._client.is_ready()

    def detect(self, tiles: list[bytes], *, language: str = "de") -> PestDetectionResult:
        per_tile: list[list[PestFinding]] = []
        for tile in tiles:
            raw_findings = self._client.detect(tile, mode=self._mode.value, language=language)
            per_tile.append([_finding_from_raw(r, default_mode=self._mode) for r in raw_findings])

        merged = self._tiler.merge_boxes(per_tile)
        return PestDetectionResult(
            findings=merged,
            tiles_processed=len(tiles),
            adapter_key=self.adapter_key,
            source=self._source.value,
        )


@PestDetectionAdapterRegistry.register
class LocalPestSymptomAdapter(_LocalPestInferenceAdapter):
    """Modus 2 (Schadbild), Phase-1 default — few-shot DINOv2 classification."""

    adapter_key = "local_pest_symptom"
    supports_modes = [PestFindingMode.SYMPTOM.value]
    _source = PestDetectionSource.LOCAL_SYMPTOM
    _mode = PestFindingMode.SYMPTOM
    _enabled_flag = "pest_detection_symptom_enabled"


@PestDetectionAdapterRegistry.register
class LocalPestDetectorAdapter(_LocalPestInferenceAdapter):
    """Modus 1 (Direkt-Detektion), Phase 2 — quantized ONNX detector + SAHI.

    TODO(REQ-044 WP-1/WP-2/WP-3): final model choice (D-FINE-S vs RF-DETR-S) and
    trained weights are externally blocked; disabled by default until then.
    """

    adapter_key = "local_pest_detector"
    supports_modes = [PestFindingMode.DIRECT.value, PestFindingMode.SYMPTOM.value]
    _source = PestDetectionSource.LOCAL_DETECTOR
    _mode = PestFindingMode.DIRECT
    _enabled_flag = "pest_detection_detector_enabled"
