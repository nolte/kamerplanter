"""REQ-038 §3 — LocalCvDiagnosisAdapter payload mapping + configuration gate."""

from app.common.enums import DiagnosisCategory
from app.data_access.external.local_cv_diagnosis_adapter import LocalCvDiagnosisAdapter
from app.domain.interfaces.cv_diagnosis_adapter import DEFAULT_DISEASE_DISCLAIMER


class _FakeClient:
    """In-memory stand-in for CvDiagnosisInferenceClient."""

    def __init__(self, *, ready: bool = True, payload: dict | None = None) -> None:
        self._ready = ready
        self.payload = payload or {}
        self.last_with_phenotype: bool | None = None

    def is_ready(self) -> bool:
        return self._ready

    def status(self) -> dict:
        return {"ready": self._ready, "enabled": True, "class_count": 3, "phenotype_available": True}

    def classify(self, image: bytes, *, k: int = 5, with_phenotype: bool = False) -> dict:
        self.last_with_phenotype = with_phenotype
        return self.payload


def _adapter(client: _FakeClient) -> LocalCvDiagnosisAdapter:
    return LocalCvDiagnosisAdapter(client=client)  # type: ignore[arg-type]


class TestConfiguration:
    def test_configured_requires_flag_and_ready(self, monkeypatch):
        from app.config.settings import settings

        monkeypatch.setattr(settings, "cv_diagnosis_enabled", True)
        assert _adapter(_FakeClient(ready=True)).is_configured() is True
        assert _adapter(_FakeClient(ready=False)).is_configured() is False

        monkeypatch.setattr(settings, "cv_diagnosis_enabled", False)
        assert _adapter(_FakeClient(ready=True)).is_configured() is False

    def test_requires_diagnosis_consent(self):
        assert LocalCvDiagnosisAdapter.requires_consent == "plant_diagnosis"
        assert LocalCvDiagnosisAdapter.is_external is False

    def test_status_includes_adapter_key(self, monkeypatch):
        from app.config.settings import settings

        monkeypatch.setattr(settings, "cv_diagnosis_enabled", True)
        snapshot = _adapter(_FakeClient(ready=True)).status()
        assert snapshot["adapter_key"] == "local_cv_diagnosis"
        assert snapshot["feature_enabled"] is True


class TestPayloadMapping:
    def test_maps_classifications_and_meta(self):
        payload = {
            "classifications": [
                {
                    "label": "tomato_early_blight",
                    "category": "disease",
                    "scientific_name": "Alternaria solani",
                    "probability": 0.82,
                    "highlight": True,
                },
                {"label": "nitrogen_deficiency", "category": "deficiency", "probability": 0.12, "highlight": False},
            ],
            "model_meta": {"model_name": "plantdoc_disease_v1", "fine_tuned_on": ["PlantDoc"], "class_count": 27},
            "phenotype": None,
            "disclaimer": "svc hint",
        }
        result = _adapter(_FakeClient(payload=payload)).classify(b"jpeg")
        assert [c.label for c in result.classifications] == ["tomato_early_blight", "nitrogen_deficiency"]
        assert result.classifications[0].category == DiagnosisCategory.DISEASE
        assert result.classifications[1].category == DiagnosisCategory.DEFICIENCY
        assert result.model_meta.class_count == 27
        assert "PlantVillage" not in result.model_meta.fine_tuned_on
        assert result.disclaimer == "svc hint"
        assert result.adapter_key == "local_cv_diagnosis"

    def test_unknown_category_falls_back_to_disease(self):
        payload = {"classifications": [{"label": "x", "category": "bogus", "probability": 0.5}]}
        result = _adapter(_FakeClient(payload=payload)).classify(b"jpeg")
        assert result.classifications[0].category == DiagnosisCategory.DISEASE

    def test_missing_disclaimer_falls_back_to_default(self):
        payload = {"classifications": [], "disclaimer": ""}
        result = _adapter(_FakeClient(payload=payload)).classify(b"jpeg")
        assert result.disclaimer == DEFAULT_DISEASE_DISCLAIMER

    def test_maps_phenotype_when_present(self):
        payload = {
            "classifications": [],
            "phenotype": {
                "leaf_area_px": 1000,
                "green_index": 0.5,
                "discolored_area_ratio": 0.1,
                "necrotic_area_ratio": 0.02,
                "solidity": 0.7,
                "hue_circular_mean_deg": 100.0,
                "plantcv_version": "4.0",
            },
        }
        result = _adapter(_FakeClient(payload=payload)).classify(b"jpeg", with_phenotype=True)
        assert result.phenotype is not None
        assert result.phenotype.leaf_area_px == 1000

    def test_phenotype_request_gated_by_setting(self, monkeypatch):
        from app.config.settings import settings

        monkeypatch.setattr(settings, "cv_phenotype_enabled", False)
        client = _FakeClient(payload={"classifications": []})
        _adapter(client).classify(b"jpeg", with_phenotype=True)
        # phenotype is suppressed at the client boundary when the setting is off
        assert client.last_with_phenotype is False
