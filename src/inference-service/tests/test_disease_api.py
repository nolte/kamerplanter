"""REQ-038 disease classifier endpoint tests (faked classifier, no ONNX model)."""

from app.main import DEFAULT_DISEASE_DISCLAIMER
from tests.conftest import make_image_bytes


def _image_part():
    return {"image": ("leaf.png", make_image_bytes(), "image/png")}


class TestDiseaseStatus:
    def test_status_disabled_when_classifier_absent(self, client):
        body = client.get("/disease/status").json()
        assert body["enabled"] is False
        assert body["ready"] is False
        assert body["class_count"] == 0
        # phenotype engine is patched-in and available in the fixture
        assert body["phenotype_available"] is True

    def test_status_ready_when_enabled(self, disease_client, fake_disease_classifier):
        fake_disease_classifier.class_count = 27
        body = disease_client.get("/disease/status").json()
        assert body["enabled"] is True
        assert body["ready"] is True
        assert body["class_count"] == 27


class TestDiseaseReady:
    def test_ready_503_when_disabled(self, client):
        assert client.get("/disease/ready").status_code == 503

    def test_ready_ok_when_enabled(self, disease_client):
        assert disease_client.get("/disease/ready").status_code == 200


class TestClassifyDisease:
    def test_returns_topk_above_floor_with_disclaimer(self, disease_client, fake_disease_classifier):
        fake_disease_classifier.results = [
            ("tomato_early_blight", "disease", "Alternaria solani", 0.82),
            ("nitrogen_deficiency", "deficiency", None, 0.11),
            ("healthy", "healthy", None, 0.04),  # below 0.10 floor -> dropped
        ]
        resp = disease_client.post("/classify/disease", files=_image_part())
        assert resp.status_code == 200
        body = resp.json()
        labels = [c["label"] for c in body["classifications"]]
        assert labels == ["tomato_early_blight", "nitrogen_deficiency"]
        # highlight flag only for the high-confidence class (>= 0.75)
        assert body["classifications"][0]["highlight"] is True
        assert body["classifications"][1]["highlight"] is False
        # deficiency category is carried through for backend null-key mapping
        assert body["classifications"][1]["category"] == "deficiency"
        # disclaimer is always present and non-empty (REQ-038 hard invariant)
        assert body["disclaimer"] == DEFAULT_DISEASE_DISCLAIMER
        assert body["disclaimer"].strip() != ""

    def test_model_meta_never_lists_plantvillage(self, disease_client, fake_disease_classifier):
        fake_disease_classifier.results = [("x", "disease", None, 0.9)]
        body = disease_client.post("/classify/disease", files=_image_part()).json()
        assert "PlantVillage" not in body["model_meta"]["fine_tuned_on"]
        assert body["model_meta"]["fine_tuned_on"] == ["PlantDoc"]

    def test_phenotype_included_when_requested(self, disease_client, fake_disease_classifier):
        fake_disease_classifier.results = [("x", "disease", None, 0.9)]
        body = disease_client.post(
            "/classify/disease", params={"phenotype": True}, files=_image_part()
        ).json()
        assert body["phenotype"] is not None
        assert body["phenotype"]["leaf_area_px"] == 1234
        assert body["phenotype"]["plantcv_version"] == "4.0-fake"

    def test_phenotype_omitted_by_default(self, disease_client, fake_disease_classifier):
        fake_disease_classifier.results = [("x", "disease", None, 0.9)]
        body = disease_client.post("/classify/disease", files=_image_part()).json()
        assert body["phenotype"] is None

    def test_classify_503_when_disabled(self, client):
        resp = client.post("/classify/disease", files=_image_part())
        assert resp.status_code == 503

    def test_classify_400_on_empty_upload(self, disease_client):
        resp = disease_client.post(
            "/classify/disease", files={"image": ("empty.png", b"", "image/png")}
        )
        assert resp.status_code == 400
