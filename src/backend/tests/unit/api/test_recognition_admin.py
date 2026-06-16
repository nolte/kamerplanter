"""Unit tests for REQ-029-A admin recognition status endpoint."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from app.api.v1.admin.recognition import router as mod


def _patch_common(monkeypatch, *, enabled, ready, model_info, coverage_rows, local_configured, total_species=0):
    monkeypatch.setattr(mod.settings, "inference_service_enabled", enabled)

    client = MagicMock()
    client.is_ready.return_value = ready
    client.modelinfo.return_value = model_info
    monkeypatch.setattr(mod, "InferenceServiceClient", lambda url: client)

    repo = MagicMock()
    repo.coverage_report.return_value = coverage_rows
    monkeypatch.setattr(mod, "get_reference_image_repo", lambda: repo)

    species_repo = MagicMock()
    species_repo.get_all.return_value = ([], total_species)
    monkeypatch.setattr(mod, "get_species_repo", lambda: species_repo)

    registry = MagicMock()
    registry.get.return_value = SimpleNamespace(is_configured=lambda: local_configured)
    monkeypatch.setattr(
        "app.domain.services.identification_registry.IdentificationAdapterRegistry",
        registry,
    )


def test_status_feature_enabled_service_ready(monkeypatch):
    _patch_common(
        monkeypatch,
        enabled=True,
        ready=True,
        model_info={"model": "dinov2_vits14", "dim": 384, "license": "Apache-2.0"},
        coverage_rows=[
            {"usable_for_recognition": True},
            {"usable_for_recognition": True},
            {"usable_for_recognition": False},
        ],
        local_configured=True,
        total_species=210,
    )

    resp = mod.get_recognition_status(_user=None)

    assert resp.feature_enabled is True
    assert resp.local_adapter_available is True
    assert resp.inference_service.ready is True
    assert resp.inference_service.model == "dinov2_vits14"
    assert resp.inference_service.dim == 384
    assert resp.coverage.total_species == 210  # all species, not just acquired ones
    assert resp.coverage.processed_species == 3  # species with an acquisition job
    assert resp.coverage.usable_species == 2
    assert resp.config.primary_adapter  # populated from settings


def test_start_acquisition_dispatches_task(monkeypatch):
    task = MagicMock()
    task.delay.return_value = SimpleNamespace(id="task-abc")
    monkeypatch.setattr("app.tasks.reference_image_tasks.acquire_all_reference_images_task", task)

    resp = mod.start_acquisition(_user=None)

    task.delay.assert_called_once_with()
    assert resp.status == "queued"
    assert resp.task_id == "task-abc"


def test_status_feature_disabled_skips_service_call(monkeypatch):
    _patch_common(
        monkeypatch,
        enabled=False,
        ready=True,  # would be ready, but disabled must short-circuit
        model_info={"model": "x"},
        coverage_rows=[],
        local_configured=False,
    )

    resp = mod.get_recognition_status(_user=None)

    assert resp.feature_enabled is False
    assert resp.inference_service.ready is False  # not queried when disabled
    assert resp.inference_service.model is None
    assert resp.coverage.total_species == 0
