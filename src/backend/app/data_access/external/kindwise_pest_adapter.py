"""REQ-044 §3.1 — Kindwise cloud pest-detection adapter (opt-in).

Optional, consent-gated cloud path (Kindwise ``plant.health`` for indoor
ornamentals, Prep §5). **Default disabled.** Consent ``pest_detection_cloud`` is
enforced by the service *before* any image leaves the instance; EXIF is stripped
beforehand (§8). Both modes (direct + symptom) are reported by the API.

TODO(REQ-044 WP-7): the Kindwise contract/DSGVO questions (training opt-out, EU
residency, indoor-class coverage) are externally open. Keep this adapter
disabled by default and behind a prominent consent until WP-7 is answered; the
response parsing below must be reconciled with the real plant.health schema.
"""

from typing import Any

import httpx
import structlog

from app.common.enums import PestDetectionSource, PestFindingCategory, PestFindingMode
from app.config.settings import settings
from app.domain.interfaces.pest_detection_adapter import (
    PestDetectionAdapter,
    PestDetectionResult,
    PestFinding,
)
from app.domain.models.pest_taxonomy import get_taxon
from app.domain.services.pest_detection_registry import PestDetectionAdapterRegistry

logger = structlog.get_logger()

_CLOUD_TIMEOUT_SECONDS = 30.0


@PestDetectionAdapterRegistry.register
class KindwisePestAdapter(PestDetectionAdapter):
    """Cloud pest detection via Kindwise plant.health (opt-in, consent-gated)."""

    adapter_key = "kindwise_pest"
    requires_consent = "pest_detection_cloud"
    is_external = True
    supports_modes = [PestFindingMode.DIRECT.value, PestFindingMode.SYMPTOM.value]

    def is_configured(self) -> bool:
        return settings.pest_detection_cloud_enabled and bool(settings.pest_detection_cloud_api_key)

    def detect(self, tiles: list[bytes], *, language: str = "de") -> PestDetectionResult:
        # Cloud detection runs on the full (first) tile; the cloud model does its
        # own internal small-object handling. Sending every tile would multiply
        # per-call cost and data egress.
        primary = tiles[0] if tiles else b""
        response = httpx.post(
            f"{settings.pest_detection_cloud_base_url.rstrip('/')}/health_assessment",
            headers={"Api-Key": settings.pest_detection_cloud_api_key},
            params={"language": language},
            files={"images": ("photo.jpg", primary, "image/jpeg")},
            timeout=_CLOUD_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        findings = self._parse(response.json())
        return PestDetectionResult(
            findings=findings,
            tiles_processed=len(tiles),
            adapter_key=self.adapter_key,
            source=PestDetectionSource.CLOUD_KINDWISE.value,
        )

    @staticmethod
    def _parse(payload: dict[str, Any]) -> list[PestFinding]:
        # TODO(REQ-044 WP-7): align with the real plant.health response schema.
        suggestions = (payload.get("result", {}).get("disease", {}) or {}).get("suggestions", [])
        findings: list[PestFinding] = []
        for raw in suggestions:
            label = raw.get("name", "unknown")
            taxon = get_taxon(label)
            category = taxon.category if taxon else PestFindingCategory.SYMPTOM
            common_name = taxon.common_name_de if taxon else label
            findings.append(
                PestFinding(
                    label=label,
                    category=category,
                    common_name=common_name,
                    confidence=float(raw.get("probability", 0.0)),
                    mode=PestFindingMode.SYMPTOM,
                )
            )
        return findings
