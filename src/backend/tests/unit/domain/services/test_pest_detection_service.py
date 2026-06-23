"""REQ-044 §6/§8 — service: dispatch, consent gate, disclaimer, IPM bridge."""

import io

import pytest
from PIL import Image

from app.common.enums import PestFindingCategory, PestFindingMode
from app.common.exceptions import ConsentRequiredError, FeatureNotConfiguredError
from app.config.settings import settings
from app.domain.engines.consent_engine import ConsentEngine
from app.domain.engines.pest_detection_engine import PestDetectionEngine
from app.domain.interfaces.pest_detection_adapter import (
    PestDetectionAdapter,
    PestDetectionResult,
    PestFinding,
)
from app.domain.models.beneficial import Beneficial
from app.domain.models.ipm import Inspection, Pest
from app.domain.models.privacy import ConsentRecord
from app.domain.services.pest_detection_service import PestDetectionService


def _jpeg() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (800, 600), color=(0, 120, 0)).save(buffer, format="JPEG")
    return buffer.getvalue()


class _StubAdapter(PestDetectionAdapter):
    def __init__(
        self, *, key="local_pest_symptom", findings=None, requires_consent=None, external=False, configured=True
    ):
        self.adapter_key = key
        self.requires_consent = requires_consent
        self.is_external = external
        self.supports_modes = [PestFindingMode.SYMPTOM.value]
        self._findings = findings or []
        self._configured = configured

    def is_configured(self) -> bool:
        return self._configured

    def detect(self, tiles, *, language="de") -> PestDetectionResult:
        return PestDetectionResult(
            findings=list(self._findings),
            tiles_processed=len(tiles),
            adapter_key=self.adapter_key,
            source="local_symptom" if not self.is_external else "cloud_kindwise",
        )


class _FakeRegistry:
    def __init__(self, adapter: _StubAdapter | None):
        self._adapter = adapter

    def get_preferred(self):
        return self._adapter

    def get(self, key):
        if self._adapter and self._adapter.adapter_key == key:
            return self._adapter
        raise KeyError(key)

    def all_keys(self):
        return [self._adapter.adapter_key] if self._adapter else []


class _FakeIpmRepo:
    def get_pest_by_scientific_name(self, scientific_name):
        if scientific_name == "Tetranychus urticae":
            return Pest(_key="pest_spider_mite", scientific_name=scientific_name, common_name="Spider Mite")
        return None


class _FakePestRepo:
    def __init__(self):
        self.created = []
        self.linked = []

    def get_beneficial_by_slug(self, slug):
        return Beneficial(_key="b1", slug=slug, common_name="x", scientific_name="y") if slug == "ladybird" else None

    def create(self, detection):
        detection.key = f"pestdet_{len(self.created) + 1}"
        self.created.append(detection)
        return detection

    def get(self, key, tenant_key):
        for d in self.created:
            if d.key == key and d.tenant_key == tenant_key:
                return d
        return None

    def list_for_plant(self, tenant_key, plant_instance_key, limit=20):
        return [d for d in self.created if d.tenant_key == tenant_key and d.plant_instance_key == plant_instance_key]

    def link_suggested_inspection(self, detection_key, inspection_key):
        self.linked.append((detection_key, inspection_key))

    def add_feedback(self, key, tenant_key, feedback):
        d = self.get(key, tenant_key)
        if d:
            d.feedback.append(feedback)
        return d


class _FakeIpmService:
    """Only ``create_inspection`` is allowed — never a treatment (§0)."""

    def __init__(self):
        self.inspections = []

    def create_inspection(self, plant_key, inspection: Inspection) -> Inspection:
        inspection.key = f"insp_{len(self.inspections) + 1}"
        self.inspections.append(inspection)
        return inspection


class _FakeConsentRepo:
    def __init__(self, granted):
        self._granted = granted

    def get_by_user_and_purpose(self, user_key, purpose):
        if self._granted is None:
            return None
        return ConsentRecord(user_key=user_key, purpose=purpose, granted=self._granted)


def _service(adapter, *, consent_granted=None, pest_repo=None, ipm_service=None) -> PestDetectionService:
    pest_repo = pest_repo or _FakePestRepo()
    engine = PestDetectionEngine(ipm_repo=_FakeIpmRepo(), pest_detection_repo=pest_repo)
    return PestDetectionService(
        engine=engine,
        repo=pest_repo,
        ipm_service=ipm_service or _FakeIpmService(),
        consent_repo=_FakeConsentRepo(consent_granted),
        consent_engine=ConsentEngine(),
        registry=_FakeRegistry(adapter),
    )


def _symptom(label, conf, category=PestFindingCategory.SYMPTOM):
    return PestFinding(label=label, category=category, common_name=label, confidence=conf, mode=PestFindingMode.SYMPTOM)


@pytest.fixture(autouse=True)
def _enable_feature(monkeypatch):
    monkeypatch.setattr(settings, "pest_detection_enabled", True)
    monkeypatch.setattr(settings, "kamerplanter_mode", "full")


class TestDetectDispatch:
    def test_symptom_detection_maps_pest_and_persists(self) -> None:
        adapter = _StubAdapter(findings=[_symptom("spider_mite", 0.6)])
        svc = _service(adapter)
        result = svc.detect_pests(_jpeg(), tenant_key="t1", user_key="u1", plant_instance_key="p1")
        assert result["findings"][0]["matched_pest_key"] == "pest_spider_mite"
        assert result["findings"][0]["mode"] == "symptom"
        assert result["suggested_next_step"] == "ipm_inspection"
        assert result["tiles_processed"] >= 1

    def test_beneficial_never_marked_as_pest(self) -> None:
        adapter = _StubAdapter(findings=[_symptom("ladybird", 0.95, PestFindingCategory.BENEFICIAL)])
        result = _service(adapter).detect_pests(_jpeg(), tenant_key="t1", user_key="u1", plant_instance_key="p1")
        assert result["findings"][0]["category"] == "beneficial"
        assert result["suggested_next_step"] == "none"

    def test_abstention_when_all_weak(self) -> None:
        adapter = _StubAdapter(findings=[_symptom("spider_mite", 0.25)])
        result = _service(adapter).detect_pests(_jpeg(), tenant_key="t1", user_key="u1", plant_instance_key="p1")
        assert result["is_confident"] is False


class TestGlobalDetect:
    """REQ-044 §7 — plant-agnostic detect (plant_instance_key=None)."""

    def test_global_detection_persists_without_plant(self) -> None:
        adapter = _StubAdapter(findings=[_symptom("spider_mite", 0.6)])
        pest_repo = _FakePestRepo()
        svc = _service(adapter, pest_repo=pest_repo)
        result = svc.detect_pests(_jpeg(), tenant_key="t1", user_key="u1", plant_instance_key=None)
        # The detection is persisted (so feedback has a key) but bound to no plant.
        assert result["key"]
        assert result["plant_instance_key"] is None
        assert len(pest_repo.created) == 1
        assert pest_repo.created[0].plant_instance_key is None
        # Same image-recognition path: pest mapping still happens.
        assert result["findings"][0]["matched_pest_key"] == "pest_spider_mite"

    def test_global_detection_still_carries_disclaimer(self) -> None:
        result = _service(_StubAdapter(findings=[])).detect_pests(
            _jpeg(), tenant_key="t1", user_key="u1", plant_instance_key=None
        )
        assert result["disclaimer"].strip()

    def test_feedback_on_global_detection(self) -> None:
        adapter = _StubAdapter(findings=[_symptom("spider_mite", 0.6)])
        pest_repo = _FakePestRepo()
        svc = _service(adapter, pest_repo=pest_repo)
        det = svc.detect_pests(_jpeg(), tenant_key="t1", user_key="u1", plant_instance_key=None)
        updated = svc.submit_feedback(det["key"], tenant_key="t1", finding_label="spider_mite", confirmed=True)
        assert updated["feedback"][0]["finding_label"] == "spider_mite"
        assert updated["feedback"][0]["confirmed"] is True

    def test_global_feature_disabled_raises(self, monkeypatch) -> None:
        monkeypatch.setattr(settings, "pest_detection_enabled", False)
        with pytest.raises(FeatureNotConfiguredError):
            _service(_StubAdapter()).detect_pests(_jpeg(), tenant_key="t1", user_key="u1", plant_instance_key=None)

    def test_global_cloud_adapter_without_consent_raises_403(self) -> None:
        adapter = _StubAdapter(key="kindwise_pest", requires_consent="pest_detection_cloud", external=True)
        svc = _service(adapter, consent_granted=None)
        with pytest.raises(ConsentRequiredError) as exc:
            svc.detect_pests(_jpeg(), tenant_key="t1", user_key="u1", plant_instance_key=None)
        assert exc.value.status_code == 403


class TestDisclaimerInvariant:
    @pytest.mark.parametrize("findings", [[], [_symptom("spider_mite", 0.6)], [_symptom("x", 0.1)]])
    def test_disclaimer_never_empty(self, findings) -> None:
        result = _service(_StubAdapter(findings=findings)).detect_pests(
            _jpeg(), tenant_key="t1", user_key="u1", plant_instance_key="p1"
        )
        assert result["disclaimer"].strip()


class TestConsentGate:
    def test_cloud_adapter_without_consent_raises_403(self) -> None:
        adapter = _StubAdapter(key="kindwise_pest", requires_consent="pest_detection_cloud", external=True)
        svc = _service(adapter, consent_granted=None)
        with pytest.raises(ConsentRequiredError) as exc:
            svc.detect_pests(_jpeg(), tenant_key="t1", user_key="u1", plant_instance_key="p1")
        assert exc.value.status_code == 403

    def test_cloud_adapter_with_consent_runs(self) -> None:
        adapter = _StubAdapter(
            key="kindwise_pest",
            requires_consent="pest_detection_cloud",
            external=True,
            findings=[_symptom("spider_mite", 0.6)],
        )
        result = _service(adapter, consent_granted=True).detect_pests(
            _jpeg(), tenant_key="t1", user_key="u1", plant_instance_key="p1"
        )
        assert result["source"] == "cloud_kindwise"

    def test_self_hosted_needs_no_consent(self) -> None:
        adapter = _StubAdapter(findings=[_symptom("spider_mite", 0.6)])
        result = _service(adapter, consent_granted=None).detect_pests(
            _jpeg(), tenant_key="t1", user_key="u1", plant_instance_key="p1"
        )
        assert result["adapter_key"] == "local_pest_symptom"


class TestFeatureGate:
    def test_feature_disabled_raises(self, monkeypatch) -> None:
        monkeypatch.setattr(settings, "pest_detection_enabled", False)
        with pytest.raises(FeatureNotConfiguredError):
            _service(_StubAdapter()).detect_pests(_jpeg(), tenant_key="t1", user_key="u1", plant_instance_key="p1")

    def test_no_adapter_configured_raises(self) -> None:
        with pytest.raises(FeatureNotConfiguredError):
            _service(None).detect_pests(_jpeg(), tenant_key="t1", user_key="u1", plant_instance_key="p1")

    def test_status_reports_no_active_adapter_when_none(self) -> None:
        status = _service(None).get_status()
        assert status["available"] is False
        assert status["active_adapter"] is None


class TestIpmBridgeNoTreatment:
    def test_create_inspection_no_treatment(self) -> None:
        adapter = _StubAdapter(findings=[_symptom("spider_mite", 0.7)])
        pest_repo = _FakePestRepo()
        ipm = _FakeIpmService()
        svc = _service(adapter, pest_repo=pest_repo, ipm_service=ipm)
        det = svc.detect_pests(_jpeg(), tenant_key="t1", user_key="u1", plant_instance_key="p1")

        out = svc.create_inspection(det["key"], tenant_key="t1", plant_key="p1")
        assert out["inspection_key"] == "insp_1"
        assert "pest_spider_mite" in out["detected_pest_keys"]
        # exactly one inspection, and the fake service exposes no treatment path
        assert len(ipm.inspections) == 1
        assert not hasattr(ipm, "create_treatment_application")
        assert pest_repo.linked == [(det["key"], "insp_1")]


class TestHealthSignal:
    def test_health_signal_reflects_confident_pest(self) -> None:
        adapter = _StubAdapter(findings=[_symptom("spider_mite", 0.7)])
        pest_repo = _FakePestRepo()
        svc = _service(adapter, pest_repo=pest_repo)
        svc.detect_pests(_jpeg(), tenant_key="t1", user_key="u1", plant_instance_key="p1")
        signal = svc.get_pest_signal_for_plant(tenant_key="t1", plant_instance_key="p1")
        assert signal["has_pest_signal"] is True
        assert "pest_spider_mite" in signal["pest_keys"]
