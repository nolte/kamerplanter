"""REQ-044 §4.1/§4.3 — engine: mapping, abstention, suggested next step."""

from app.common.enums import (
    PestDetectionNextStep,
    PestFindingCategory,
    PestFindingMode,
)
from app.domain.engines.pest_detection_engine import PestDetectionEngine
from app.domain.interfaces.pest_detection_adapter import PestDetectionResult, PestFinding
from app.domain.models.beneficial import Beneficial
from app.domain.models.ipm import Pest
from app.domain.models.pest_detection import PestDetection


class _FakeIpmRepo:
    def get_pest_by_scientific_name(self, scientific_name: str) -> Pest | None:
        if scientific_name == "Tetranychus urticae":
            return Pest(_key="pest_spider_mite", scientific_name=scientific_name, common_name="Spider Mite")
        return None


class _FakePestRepo:
    def __init__(self) -> None:
        self.created: PestDetection | None = None

    def get_beneficial_by_slug(self, slug: str) -> Beneficial | None:
        if slug == "ladybird":
            return Beneficial(
                _key="beneficial_ladybird", slug=slug, common_name="Marienkäfer", scientific_name="Coccinellidae"
            )
        return None

    def create(self, detection: PestDetection) -> PestDetection:
        detection.key = "pestdet_1"
        self.created = detection
        return detection


def _finding(label: str, category: PestFindingCategory, confidence: float, mode=PestFindingMode.SYMPTOM) -> PestFinding:
    return PestFinding(label=label, category=category, common_name=label, confidence=confidence, mode=mode)


def _engine() -> tuple[PestDetectionEngine, _FakePestRepo]:
    repo = _FakePestRepo()
    return PestDetectionEngine(ipm_repo=_FakeIpmRepo(), pest_detection_repo=repo), repo


def _process(engine: PestDetectionEngine, findings: list[PestFinding]) -> PestDetection:
    result = PestDetectionResult(
        findings=findings, source="local_symptom", adapter_key="local_pest_symptom", tiles_processed=4
    )
    return engine.process_and_persist(
        result, tenant_key="t1", user_key="u1", plant_instance_key="plant1", image_hash="sha256:abc"
    )


class TestMapping:
    def test_pest_finding_mapped_to_stammdaten_key(self) -> None:
        engine, _ = _engine()
        det = _process(engine, [_finding("spider_mite", PestFindingCategory.SYMPTOM, 0.6)])
        assert det.findings[0].matched_pest_key == "pest_spider_mite"

    def test_beneficial_mapped_and_never_actionable(self) -> None:
        engine, _ = _engine()
        det = _process(engine, [_finding("ladybird", PestFindingCategory.BENEFICIAL, 0.95, PestFindingMode.DIRECT)])
        assert det.findings[0].matched_beneficial_key == "beneficial_ladybird"
        assert det.findings[0].matched_pest_key is None
        assert det.suggested_next_step == PestDetectionNextStep.NONE


class TestAbstention:
    def test_all_weak_findings_trigger_abstention(self) -> None:
        engine, _ = _engine()
        det = _process(engine, [_finding("spider_mite", PestFindingCategory.SYMPTOM, 0.30)])
        assert det.is_confident is False
        assert det.suggested_next_step == PestDetectionNextStep.NONE

    def test_confident_pest_suggests_inspection(self) -> None:
        engine, _ = _engine()
        det = _process(engine, [_finding("spider_mite", PestFindingCategory.SYMPTOM, 0.55)])
        assert det.is_confident is True
        assert det.suggested_next_step == PestDetectionNextStep.IPM_INSPECTION

    def test_empty_findings_is_confident_no_step(self) -> None:
        engine, _ = _engine()
        det = _process(engine, [])
        assert det.is_confident is True
        assert det.suggested_next_step == PestDetectionNextStep.NONE


class TestPersistence:
    def test_image_marked_deleted_and_not_stored(self) -> None:
        engine, repo = _engine()
        det = _process(engine, [_finding("spider_mite", PestFindingCategory.SYMPTOM, 0.6)])
        assert det.image_deleted_at is not None
        assert det.image_hash == "sha256:abc"
        # the persisted model has no field carrying raw image bytes
        assert "image_data" not in det.model_dump()
        assert repo.created is det
