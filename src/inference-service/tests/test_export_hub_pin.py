"""The DINOv2 export loads a pinned hub commit without GitHub-API validation (#2991)."""

import importlib.util
import re
import sys
import types
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "export_dinov2_onnx.py"


class _LoadCalled(Exception):
    """Raised by the fake hub to stop the export right after the load call."""


def _load_script():
    spec = importlib.util.spec_from_file_location("export_dinov2_onnx", _SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_export_loads_a_pinned_commit_without_api_validation(monkeypatch, tmp_path):
    calls = []

    def fake_load(repo, model, **kwargs):
        calls.append((repo, model, kwargs))
        raise _LoadCalled

    fake_torch = types.ModuleType("torch")
    fake_torch.hub = types.SimpleNamespace(load=fake_load)
    monkeypatch.setitem(sys.modules, "torch", fake_torch)

    script = _load_script()
    with pytest.raises(_LoadCalled):
        script.export("dinov2_vits14", 224, tmp_path, opset=17)

    [(repo, model, kwargs)] = calls
    assert re.fullmatch(r"facebookresearch/dinov2:[0-9a-f]{40}", repo)
    assert model == "dinov2_vits14"
    # skip_validation=False makes torch.hub call api.github.com unauthenticated,
    # which failed the image build with HTTP 403 on a shared runner.
    assert kwargs.get("skip_validation") is True
    assert kwargs.get("trust_repo") is True
