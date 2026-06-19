"""Unit tests for REQ-029-A §4 admin reference-image endpoints (WS-4 trigger).

The endpoint functions are exercised directly (the ``Depends(require_platform_admin)``
default is not evaluated on a direct call), with the Celery tasks and repos
patched out.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
import pytest

from app.api.v1.admin.reference_images import router as mod
from app.api.v1.admin.reference_images.schemas import SetImageActiveRequest
from app.common.exceptions import NotFoundError


def test_acquire_all_dispatches_task(monkeypatch):
    task = MagicMock()
    task.delay.return_value = SimpleNamespace(id="task-123")
    monkeypatch.setattr("app.tasks.reference_image_tasks.acquire_all_reference_images_task", task)

    resp = mod.acquire_all(_user=None)

    task.delay.assert_called_once_with()
    assert resp.status == "queued"
    assert resp.scope == "all"
    assert resp.task_id == "task-123"


def test_acquire_species_dispatches_with_scientific_name(monkeypatch):
    species_repo = MagicMock()
    species_repo.get_by_key.return_value = SimpleNamespace(key="species_monstera", scientific_name="Monstera deliciosa")
    monkeypatch.setattr(mod, "get_species_repo", lambda: species_repo)

    task = MagicMock()
    task.delay.return_value = SimpleNamespace(id="task-9")
    monkeypatch.setattr("app.tasks.reference_image_tasks.acquire_reference_images_task", task)

    resp = mod.acquire_species("species_monstera", _user=None)

    task.delay.assert_called_once_with("species_monstera", "Monstera deliciosa")
    assert resp.scope == "species"
    assert resp.species_key == "species_monstera"


def test_acquire_species_404_when_unknown(monkeypatch):
    species_repo = MagicMock()
    species_repo.get_by_key.return_value = None
    monkeypatch.setattr(mod, "get_species_repo", lambda: species_repo)

    with pytest.raises(NotFoundError):
        mod.acquire_species("nope", _user=None)


def test_coverage_aggregates(monkeypatch):
    repo = MagicMock()
    repo.coverage_report.return_value = [
        {"species_key": "a", "scientific_name": "A a", "accepted": 20, "usable_for_recognition": True},
        {"species_key": "b", "scientific_name": "B b", "accepted": 2, "usable_for_recognition": False},
    ]
    monkeypatch.setattr(mod, "get_reference_image_repo", lambda: repo)

    report = mod.get_coverage(_user=None)

    assert report.total_species == 2
    assert report.usable_species == 1
    assert report.entries[0].species_key == "a"


# -- curation (deselect / re-include) --------------------------------------


def _patch_species_exists(monkeypatch, exists: bool = True) -> None:
    species_repo = MagicMock()
    species_repo.get_by_key.return_value = SimpleNamespace(key="species_a") if exists else None
    monkeypatch.setattr(mod, "get_species_repo", lambda: species_repo)


def test_list_curation_images_includes_excluded(monkeypatch):
    _patch_species_exists(monkeypatch)
    client = MagicMock()
    client.list_references.return_value = [
        {"id": 1, "source_url": "http://x/1.jpg", "is_active": True, "source": "gbif"},
        {"id": 2, "source_url": "http://x/2.jpg", "is_active": False, "exclusion_reason": "blurry"},
        {"id": 3, "source_url": ""},  # no URL → dropped
    ]
    monkeypatch.setattr(mod, "InferenceServiceClient", lambda _url: client)

    result = mod.list_curation_images("species_a", _user=None)

    assert result.count == 2
    assert result.active_count == 1
    by_id = {img.id: img for img in result.images}
    assert by_id[2].is_active is False
    assert by_id[2].exclusion_reason == "blurry"
    # The admin view must request ALL images (not active_only).
    assert client.list_references.call_args.kwargs.get("active_only", False) is False


def test_list_curation_images_404_when_species_unknown(monkeypatch):
    _patch_species_exists(monkeypatch, exists=False)
    monkeypatch.setattr(mod, "InferenceServiceClient", lambda _url: MagicMock())

    with pytest.raises(NotFoundError):
        mod.list_curation_images("nope", _user=None)


def test_set_image_active_deselects(monkeypatch):
    client = MagicMock()
    monkeypatch.setattr(mod, "InferenceServiceClient", lambda _url: client)

    body = SetImageActiveRequest(is_active=False, reason="blurry")
    resp = mod.set_image_active("species_a", 7, body=body, _user=None)

    client.set_reference_active.assert_called_once_with("species_a", 7, is_active=False, reason="blurry")
    assert resp.is_active is False
    assert resp.id == 7
    assert resp.species_key == "species_a"


def test_set_image_active_404_when_image_unknown(monkeypatch):
    client = MagicMock()
    client.set_reference_active.side_effect = httpx.HTTPStatusError(
        "not found",
        request=httpx.Request("PATCH", "http://inference/reference/species_a/999"),
        response=httpx.Response(404),
    )
    monkeypatch.setattr(mod, "InferenceServiceClient", lambda _url: client)

    with pytest.raises(NotFoundError):
        mod.set_image_active("species_a", 999, body=SetImageActiveRequest(is_active=False), _user=None)
