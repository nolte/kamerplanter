"""REQ-038 — CvDiagnosisService: consent gate, non-persistence, confirm bridge."""

import io
from unittest.mock import MagicMock

import pytest
from PIL import Image

from app.common.enums import DiagnosisCategory
from app.common.exceptions import ConsentRequiredError, FeatureNotConfiguredError, NotFoundError, ValidationError
from app.domain.interfaces.cv_diagnosis_adapter import CvDiagnosisResult, DiseaseClassification
from app.domain.models.ipm import Inspection
from app.domain.models.plant_diagnosis_request import PlantDiagnosisRequest
from app.domain.services.cv_diagnosis_service import CvDiagnosisService


def _real_jpeg() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), (0, 120, 0)).save(buf, format="JPEG")
    return buf.getvalue()


class _FakeEngine:
    """Passes the adapter result through unchanged (engine gating is unit-tested separately)."""

    def process(self, result: CvDiagnosisResult) -> CvDiagnosisResult:
        return result


def _build_service(
    *,
    consent_granted: bool = True,
    configured: bool = True,
    classify_result: CvDiagnosisResult | None = None,
    mode: str = "full",
    monkeypatch=None,
):
    from app.config.settings import settings

    if monkeypatch is not None:
        monkeypatch.setattr(settings, "kamerplanter_mode", mode)
        monkeypatch.setattr(settings, "cv_diagnosis_enabled", True)

    adapter = MagicMock()
    adapter.adapter_key = "local_cv_diagnosis"
    adapter.is_configured.return_value = configured
    adapter.classify.return_value = classify_result or CvDiagnosisResult(
        classifications=[
            DiseaseClassification(
                label="tomato_early_blight",
                category=DiagnosisCategory.DISEASE,
                probability=0.9,
                highlight=True,
                matched_disease_key="disease_early_blight",
            )
        ],
        adapter_key="local_cv_diagnosis",
        is_confident=True,
    )

    repo = MagicMock()
    repo.create.side_effect = lambda req: req.model_copy(update={"key": "diag_1"})

    ipm_service = MagicMock()
    ipm_service.create_inspection.return_value = Inspection(
        _key="insp_1", tenant_key="tenant_anna", plant_key="plant_1"
    )

    consent_repo = MagicMock()
    consent_engine = MagicMock()
    consent_engine.is_processing_allowed.return_value = consent_granted

    service = CvDiagnosisService(
        adapter=adapter,
        engine=_FakeEngine(),
        repo=repo,
        ipm_service=ipm_service,
        consent_repo=consent_repo,
        consent_engine=consent_engine,
    )
    return service, adapter, repo, ipm_service


class TestConsentGate:
    def test_diagnose_without_consent_raises(self, monkeypatch):
        service, adapter, _, _ = _build_service(consent_granted=False, monkeypatch=monkeypatch)
        with pytest.raises(ConsentRequiredError):
            service.diagnose(_real_jpeg(), tenant_key="tenant_anna", user_key="user_anna")
        adapter.classify.assert_not_called()

    def test_light_mode_skips_backend_consent(self, monkeypatch):
        service, adapter, _, _ = _build_service(consent_granted=False, mode="light", monkeypatch=monkeypatch)
        service.diagnose(_real_jpeg(), tenant_key="tenant_anna", user_key="user_anna")
        adapter.classify.assert_called_once()


class TestFeatureGate:
    def test_unconfigured_adapter_raises(self, monkeypatch):
        service, _, _, _ = _build_service(configured=False, monkeypatch=monkeypatch)
        with pytest.raises(FeatureNotConfiguredError):
            service.diagnose(_real_jpeg(), tenant_key="tenant_anna", user_key="user_anna")


class TestValidation:
    def test_empty_image_rejected(self, monkeypatch):
        service, _, _, _ = _build_service(monkeypatch=monkeypatch)
        with pytest.raises(ValidationError):
            service.diagnose(b"", tenant_key="tenant_anna", user_key="user_anna")

    def test_undecodable_image_rejected(self, monkeypatch):
        service, _, _, _ = _build_service(monkeypatch=monkeypatch)
        with pytest.raises(ValidationError):
            service.diagnose(b"not-an-image", tenant_key="tenant_anna", user_key="user_anna")


class TestImageNonPersistence:
    def test_image_not_persisted_hash_and_deleted_marker_set(self, monkeypatch):
        service, _, repo, _ = _build_service(monkeypatch=monkeypatch)
        result = service.diagnose(_real_jpeg(), tenant_key="tenant_anna", user_key="user_anna")
        persisted: PlantDiagnosisRequest = repo.create.call_args.args[0]
        assert persisted.image_deleted_at is not None
        assert persisted.image_hash.startswith("sha256:")
        # The persisted model carries no raw image field at all.
        assert "image_data" not in persisted.model_dump()
        assert result["disclaimer"].strip() != ""


class TestConfirmBridge:
    def test_confirm_creates_inspection_never_treatment(self, monkeypatch):
        service, _, repo, ipm_service = _build_service(monkeypatch=monkeypatch)
        repo.get.return_value = PlantDiagnosisRequest(
            _key="diag_1",
            tenant_key="tenant_anna",
            user_key="user_anna",
            image_hash="sha256:x",
            classifications=[
                DiseaseClassification(
                    label="tomato_early_blight",
                    category=DiagnosisCategory.DISEASE,
                    probability=0.9,
                    highlight=True,
                    matched_disease_key="disease_early_blight",
                )
            ],
        )
        result = service.confirm("diag_1", tenant_key="tenant_anna", plant_key="plant_1")
        assert result["inspection_key"] == "insp_1"
        assert result["detected_disease_keys"] == ["disease_early_blight"]
        ipm_service.create_inspection.assert_called_once()
        # never a treatment application
        assert not hasattr(ipm_service, "apply_treatment") or not ipm_service.apply_treatment.called

    def test_confirm_foreign_request_is_404(self, monkeypatch):
        service, _, repo, _ = _build_service(monkeypatch=monkeypatch)
        repo.get.return_value = None  # tenant-filtered miss
        with pytest.raises(NotFoundError):
            service.confirm("diag_x", tenant_key="tenant_anna", plant_key="plant_1")
