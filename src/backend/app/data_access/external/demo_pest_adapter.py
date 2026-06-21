"""REQ-044 — demo pest-detection adapter (no external service, no real model).

Lets operators preview the complete pest-detection UI flow — scan button, photo
upload, box overlay, findings, abstention/beneficial hints, HITL feedback and the
inspection CTA — while the trained self-hosted backend is externally blocked
(WP-1/2/3) and the cloud adapter is opt-in/off. Returns deterministic,
clearly-labelled PLACEHOLDER findings and must never inform a real decision; the
durchgängige Disclaimer (§8) already states this.

Enabled via ``PEST_DETECTION_DEMO_ENABLED`` (default off). When on, it becomes
the active adapter through the registry's graceful-degradation fallback because
the self-hosted symptom adapter is unreachable without the inference service.
"""

from app.common.enums import PestDetectionSource, PestFindingMode
from app.config.settings import settings
from app.domain.interfaces.pest_detection_adapter import (
    BoundingBox,
    PestDetectionAdapter,
    PestDetectionResult,
    PestFinding,
)
from app.domain.models.pest_taxonomy import get_taxon
from app.domain.services.pest_detection_registry import PestDetectionAdapterRegistry


@PestDetectionAdapterRegistry.register
class DemoPestAdapter(PestDetectionAdapter):
    """Placeholder adapter for previewing the UI without a real model."""

    adapter_key = "demo_pest"
    requires_consent = None
    is_external = False
    supports_modes = [PestFindingMode.DIRECT.value, PestFindingMode.SYMPTOM.value]

    def is_configured(self) -> bool:
        return settings.pest_detection_enabled and settings.pest_detection_demo_enabled

    def detect(self, tiles: list[bytes], *, language: str = "de") -> PestDetectionResult:
        # Two deterministic placeholder findings: one direct (with box, shows the
        # overlay) and one symptom (box-less), both above the abstention floor so
        # the inspection CTA appears. Categories/common names come from the
        # verified taxonomy so the mapping path is exercised too.
        spider = get_taxon("spider_mite")
        aphid = get_taxon("aphid")
        findings = [
            PestFinding(
                label="spider_mite",
                category=spider.category,
                common_name=spider.common_name_de,
                confidence=0.62,
                mode=PestFindingMode.DIRECT,
                bounding_box=BoundingBox(x=0.30, y=0.28, width=0.22, height=0.20),
            ),
            PestFinding(
                label="aphid",
                category=aphid.category,
                common_name=aphid.common_name_de,
                confidence=0.48,
                mode=PestFindingMode.SYMPTOM,
            ),
        ]
        return PestDetectionResult(
            findings=findings,
            tiles_processed=len(tiles),
            adapter_key=self.adapter_key,
            source=PestDetectionSource.LOCAL_SYMPTOM.value,
        )
