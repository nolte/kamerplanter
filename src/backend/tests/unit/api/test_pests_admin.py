"""REQ-044 — admin pest-recognition endpoints (coverage, acquire, gallery)."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from app.api.v1.admin.pests import router as mod
from app.api.v1.admin.pests.schemas import SetPestImageActiveRequest


def _client(monkeypatch, **methods):
    client = MagicMock()
    for name, value in methods.items():
        getattr(client, name).return_value = value
    monkeypatch.setattr(mod, "_client", lambda: client)
    return client


class TestStatus:
    def test_coverage_merges_taxonomy_with_index_counts(self, monkeypatch):
        monkeypatch.setattr(mod.settings, "pest_detection_enabled", True)
        monkeypatch.setattr(mod.settings, "pest_reference_min_usable", 30)
        _client(
            monkeypatch,
            is_ready=True,
            coverage=[
                {"label": "spider_mite", "category": "pest", "total": 35, "active": 32},
                {"label": "fungus_gnat", "category": "pest", "total": 8, "active": 8},
            ],
        )

        resp = mod.get_pest_recognition_status(_user=None)

        assert resp.feature_enabled is True
        assert resp.service_ready is True
        # every taxonomy class is represented (even those with 0 prototypes)
        by_label = {c.label: c for c in resp.classes}
        assert by_label["spider_mite"].total == 35
        assert by_label["spider_mite"].usable is True  # 32 >= 30
        assert by_label["fungus_gnat"].usable is False  # 8 < 30
        assert "ladybird" in by_label  # class with no prototypes still listed
        assert by_label["ladybird"].total == 0
        assert resp.index_count == 43

    def test_disabled_feature_reports_empty(self, monkeypatch):
        monkeypatch.setattr(mod.settings, "pest_detection_enabled", False)
        _client(monkeypatch, is_ready=False, coverage=[])
        resp = mod.get_pest_recognition_status(_user=None)
        assert resp.feature_enabled is False
        assert resp.index_count == 0


class TestAcquire:
    def test_dispatches_task(self, monkeypatch):
        task = MagicMock()
        task.delay.return_value = SimpleNamespace(id="pest-task-1")
        monkeypatch.setattr("app.tasks.pest_dataset_tasks.acquire_pest_dataset_task", task)

        resp = mod.start_pest_acquisition(_user=None)

        task.delay.assert_called_once_with()
        assert resp.status == "queued"
        assert resp.task_id == "pest-task-1"


class TestGallery:
    def test_list_images_returns_provenance(self, monkeypatch):
        _client(
            monkeypatch,
            list_prototypes={
                "label": "spider_mite",
                "count": 1,
                "active_count": 1,
                "images": [{"id": 1, "source_url": "u1", "license": "CC-BY", "attribution": "X", "is_active": True}],
            },
        )
        resp = mod.list_pest_images("spider_mite", _user=None)
        assert resp.count == 1
        assert resp.images[0].source_url == "u1"
        assert resp.images[0].attribution == "X"

    def test_set_active_curation(self, monkeypatch):
        client = _client(monkeypatch, set_prototype_active={"status": "ok"})
        resp = mod.set_pest_image_active(
            "aphid", 5, SetPestImageActiveRequest(is_active=False, reason="blurry"), _user=None
        )
        assert resp.is_active is False
        client.set_prototype_active.assert_called_once()
