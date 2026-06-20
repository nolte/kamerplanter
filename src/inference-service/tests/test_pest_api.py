"""REQ-044 pest few-shot endpoint tests (faked embedder + repo, no model/DB)."""

from app.vectordb.pest_repository import PestMatch
from tests.conftest import make_image_bytes


def _image_part():
    return {"image": ("tile.png", make_image_bytes(), "image/png")}


class TestPestReady:
    def test_ready_ok(self, client):
        assert client.get("/pest/ready").status_code == 200

    def test_ready_503_when_model_not_loaded(self, client, monkeypatch):
        from app import main

        class _NotReady:
            load_error = None

            def is_ready(self) -> bool:
                return False

        monkeypatch.setattr(main, "_embedder", _NotReady())
        assert client.get("/pest/ready").status_code == 503


class TestPestStatus:
    def test_status_reports_index_count(self, client, fake_pest_repo):
        fake_pest_repo.rows = [{"label": "spider_mite"}, {"label": "aphid"}]
        body = client.get("/pest/status").json()
        assert body["ready"] is True
        assert body["index_count"] == 2


class TestPestDetect:
    def test_detect_returns_findings_above_floor(self, client, fake_pest_repo):
        fake_pest_repo.matches = [
            PestMatch(label="spider_mite", category="pest", score=0.71),
            PestMatch(label="aphid", category="pest", score=0.05),  # below floor → dropped
        ]
        resp = client.post("/pest/detect", params={"mode": "symptom"}, files=_image_part())
        assert resp.status_code == 200
        body = resp.json()
        labels = [f["label"] for f in body["findings"]]
        assert labels == ["spider_mite"]
        assert body["findings"][0]["mode"] == "symptom"
        assert 0.0 <= body["findings"][0]["confidence"] <= 1.0

    def test_detect_503_when_model_not_ready(self, client, monkeypatch):
        from app import main

        class _NotReady:
            load_error = "boom"

            def is_ready(self) -> bool:
                return False

            def embed(self, data):
                from app.embedder import ModelNotReadyError

                raise ModelNotReadyError("not ready")

        monkeypatch.setattr(main, "_embedder", _NotReady())
        resp = client.post("/pest/detect", files=_image_part())
        assert resp.status_code == 503


class TestPestReference:
    def test_upsert_prototype_with_image(self, client, fake_pest_repo):
        resp = client.post(
            "/pest/reference",
            data={"label": "spider_mite", "category": "pest", "source": "gbif", "source_record_id": "r1"},
            files=_image_part(),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["label"] == "spider_mite"
        assert body["dim"] == 384
        assert len(fake_pest_repo.rows) == 1

    def test_upsert_requires_image_or_embedding(self, client):
        resp = client.post(
            "/pest/reference",
            data={"label": "aphid", "category": "pest", "source": "gbif"},
        )
        assert resp.status_code == 400

    def test_delete_by_label(self, client, fake_pest_repo):
        fake_pest_repo.rows = [{"label": "aphid"}, {"label": "aphid"}, {"label": "spider_mite"}]
        body = client.delete("/pest/reference/aphid").json()
        assert body["deleted"] == 2
