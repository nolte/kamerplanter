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


def _placeholder(slug: str, confidence: float, mode: PestFindingMode, box: BoundingBox | None = None) -> PestFinding:
    """A placeholder finding named and categorised by the taxonomy, like a real one."""
    taxon = get_taxon(slug)
    if taxon is None:  # a slug the taxonomy dropped: fail loudly, not with a nameless finding
        raise LookupError(f"demo pest adapter: unknown taxon {slug!r}")
    return PestFinding(
        label=slug,
        category=taxon.category,
        common_name=taxon.common_name_de,
        common_names_i18n=taxon.names_i18n(),
        confidence=confidence,
        mode=mode,
        bounding_box=box,
    )


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
        findings = [
            _placeholder(
                "spider_mite", 0.62, PestFindingMode.DIRECT, BoundingBox(x=0.30, y=0.28, width=0.22, height=0.20)
            ),
            _placeholder("aphid", 0.48, PestFindingMode.SYMPTOM),
        ]
        return PestDetectionResult(
            findings=findings,
            tiles_processed=len(tiles),
            adapter_key=self.adapter_key,
            source=PestDetectionSource.LOCAL_SYMPTOM.value,
        )
