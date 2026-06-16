"""Unit tests for REQ-029-A §4 admin reference-image endpoints (WS-4 trigger).

The endpoint functions are exercised directly (the ``Depends(require_platform_admin)``
default is not evaluated on a direct call), with the Celery tasks and repos
patched out.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.api.v1.admin.reference_images import router as mod
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
