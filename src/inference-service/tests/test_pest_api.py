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


class TestPestGalleryAndCoverage:
    def test_list_references_returns_provenance(self, client, fake_pest_repo):
        fake_pest_repo.rows = [
            {"id": 1, "label": "spider_mite", "source_url": "u1", "license": "CC0", "is_active": True},
            {
                "id": 2,
                "label": "spider_mite",
                "source_url": "u2",
                "license": "CC-BY",
                "attribution": "X",
                "is_active": False,
            },
        ]
        body = client.get("/pest/reference/spider_mite").json()
        assert body["count"] == 2
        assert body["active_count"] == 1
        assert {img["source_url"] for img in body["images"]} == {"u1", "u2"}

    def test_coverage_counts_per_class(self, client, fake_pest_repo):
        fake_pest_repo.rows = [
            {"id": 1, "label": "spider_mite", "category": "pest", "source_url": "u1", "is_active": True},
            {"id": 2, "label": "spider_mite", "category": "pest", "source_url": "u2", "is_active": False},
            {"id": 3, "label": "ladybird", "category": "beneficial", "source_url": "u3", "is_active": True},
        ]
        body = client.get("/pest/coverage").json()
        by_label = {c["label"]: c for c in body["classes"]}
        assert by_label["spider_mite"]["total"] == 2
        assert by_label["spider_mite"]["active"] == 1
        assert by_label["ladybird"]["category"] == "beneficial"

    def test_set_active_curation(self, client, fake_pest_repo):
        fake_pest_repo.rows = [{"id": 7, "label": "aphid", "source_url": "u", "is_active": True}]
        resp = client.patch("/pest/reference/aphid/7", json={"is_active": False, "reason": "blurry"})
        assert resp.status_code == 200
        assert fake_pest_repo.rows[0]["is_active"] is False

    def test_set_active_404_for_unknown(self, client, fake_pest_repo):
        resp = client.patch("/pest/reference/aphid/999", json={"is_active": False})
        assert resp.status_code == 404


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
