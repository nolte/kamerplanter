"""REQ-044 §4.1/§4.3 — pest-detection result processing.

Maps findings against REQ-010 ``pests`` (Befund-Brücke) and WP-8 ``beneficials``,
finalises abstention (§4.3) and derives the ``suggested_next_step``. It NEVER
triggers a treatment (§0) — the strongest outcome is an inspection suggestion.
Persists the request without retaining the image (§8).
"""

from datetime import UTC, datetime

from app.common.enums import (
    PestDetectionNextStep,
    PestDetectionSource,
    PestDetectionTrigger,
    PestFindingCategory,
)
from app.domain.calculators.image_tiler import ABSTAIN_CONFIDENCE
from app.domain.interfaces.ipm_repository import IIpmRepository
from app.domain.interfaces.pest_detection_adapter import PestDetectionResult, PestFinding
from app.domain.interfaces.pest_detection_repository import IPestDetectionRepository
from app.domain.models.pest_detection import PestDetection
from app.domain.models.pest_taxonomy import get_taxon

# Categories that can warrant an IPM inspection. Beneficials/unknown never do.
_ACTIONABLE = {PestFindingCategory.PEST, PestFindingCategory.SYMPTOM}


class PestDetectionEngine:
    def __init__(
        self,
        ipm_repo: IIpmRepository,
        pest_detection_repo: IPestDetectionRepository,
    ) -> None:
        self._ipm_repo = ipm_repo
        self._repo = pest_detection_repo

    def process_and_persist(
        self,
        result: PestDetectionResult,
        *,
        tenant_key: str,
        user_key: str,
        plant_instance_key: str | None,
        image_hash: str,
        trigger: PestDetectionTrigger = PestDetectionTrigger.USER_PHOTO,
    ) -> PestDetection:
        for finding in result.findings:
            self._map_finding(finding)

        is_confident = self._is_confident(result.findings)
        next_step = self._suggested_next_step(result.findings, is_confident=is_confident)
        now = datetime.now(tz=UTC)

        detection = PestDetection(
            tenant_key=tenant_key,
            user_key=user_key,
            plant_instance_key=plant_instance_key,
            source=PestDetectionSource(result.source) if result.source else PestDetectionSource.LOCAL_SYMPTOM,
            adapter_key=result.adapter_key,
            is_confident=is_confident,
            trigger=trigger,
            findings=result.findings,
            tiles_processed=result.tiles_processed,
            suggested_next_step=next_step,
            image_hash=image_hash,
            image_deleted_at=now,  # the image is never persisted (§8)
            disclaimer=result.disclaimer,
        )
        return self._repo.create(detection)

    def _map_finding(self, finding: PestFinding) -> None:
        """Resolve a finding against REQ-010 pests / WP-8 beneficials stammdaten."""
        if finding.category == PestFindingCategory.BENEFICIAL:
            beneficial = self._repo.get_beneficial_by_slug(finding.label)
            finding.matched_beneficial_key = beneficial.key if beneficial else None
            return
        if finding.category in _ACTIONABLE:
            taxon = get_taxon(finding.label)
            if taxon is not None and taxon.scientific_name:
                pest = self._ipm_repo.get_pest_by_scientific_name(taxon.scientific_name)
                finding.matched_pest_key = pest.key if pest else None

    @staticmethod
    def _is_confident(findings: list[PestFinding]) -> bool:
        """Abstention (§4.3): non-empty but all-weak findings → not confident."""
        if not findings:
            return True  # "nothing found" is not abstention
        return any(f.confidence >= ABSTAIN_CONFIDENCE for f in findings)

    @staticmethod
    def _suggested_next_step(findings: list[PestFinding], *, is_confident: bool) -> PestDetectionNextStep:
        if not is_confident:
            return PestDetectionNextStep.NONE
        actionable = any(f.category in _ACTIONABLE and f.confidence >= ABSTAIN_CONFIDENCE for f in findings)
        return PestDetectionNextStep.IPM_INSPECTION if actionable else PestDetectionNextStep.NONE
