"""Unit tests for the FLUX model pass-through in ``scripts/kami/render.py`` (#1576).

``render.py`` is a standalone operator script outside the backend package, so it is
loaded by path. ``subprocess.run`` is replaced to capture the argv that would be
handed to nolte-media's ``image_generate.py``; no network call is made.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

_RENDER_PY = Path(__file__).resolve().parents[4] / "scripts" / "kami" / "render.py"


def _load_render() -> ModuleType:
    spec = importlib.util.spec_from_file_location("kami_render", _RENDER_PY)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["kami_render"] = module
    spec.loader.exec_module(module)
    return module


render = _load_render()


def _run_generate(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, provider: str, model: str | None) -> list[str]:
    captured: list[list[str]] = []

    def fake_run(cmd: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        captured.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(render.subprocess, "run", fake_run)
    render.generate_one(
        tmp_path / "image_generate.py",
        {"id": "empty-state-plants"},
        "a prompt",
        tmp_path / "out.png",
        provider,
        4200,
        1024,
        768,
        False,
        model=model,
    )
    assert len(captured) == 1
    return captured[0]


def test_cloudflare_with_model_passes_model_flag(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    argv = _run_generate(monkeypatch, tmp_path, "cloudflare", "flux-2-klein-4b")

    idx = argv.index("--model")
    assert argv[idx + 1] == "flux-2-klein-4b"


def test_no_model_leaves_tool_default(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    argv = _run_generate(monkeypatch, tmp_path, "cloudflare", None)

    assert "--model" not in argv


def test_non_cloudflare_provider_never_gets_model_flag(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    argv = _run_generate(monkeypatch, tmp_path, "gemini", "flux-2-klein-4b")

    assert "--model" not in argv
    assert argv[argv.index("--provider") + 1] == "gemini"


@pytest.mark.parametrize(
    ("cli", "defaults", "job", "expected"),
    [
        (None, {}, {}, None),
        (None, {"model": "flux-2-klein-4b"}, {}, "flux-2-klein-4b"),
        ("flux-2-klein-4b", {"model": "flux-1-schnell"}, {}, "flux-2-klein-4b"),
        ("flux-1-schnell", {"model": "flux-1-schnell"}, {"model": "flux-2-klein-4b"}, "flux-2-klein-4b"),
    ],
)
def test_resolve_model_precedence(
    cli: str | None, defaults: dict[str, str], job: dict[str, str], expected: str | None
) -> None:
    assert render.resolve_model(cli, defaults, job) == expected
