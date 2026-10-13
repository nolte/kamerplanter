"""#1753 (GDPR-001) — the backend and the celery-worker agree on the inference-service.

The backend writes user contributions to the recognition index only when
``INFERENCE_SERVICE_ENABLED`` is set in its environment; the celery-worker runs
the scheduled Art. 17 erasure that must delete them, and reads the same flag
from *its own* environment. ``values-dev.yaml`` had the flag on the backend
only, so the worker bound the no-op store and the erasure could not reach the
index. The application now refuses instead of skipping (the contribution
marker), but a chart that sets the two processes apart would hold every
erasure — so this pins the parity where the repository controls the values.

Production values are set in GitOps (``values.yaml`` says so next to the
inference-service controller); only the files in this repository are checked.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

_CHART = Path(__file__).resolve().parents[5] / "helm" / "kamerplanter"
_PAIR = ("backend", "celery-worker")
_KEYS = ("INFERENCE_SERVICE_ENABLED", "INFERENCE_SERVICE_URL")


def _env(values: dict[str, Any], controller: str) -> dict[str, Any]:
    containers = values.get("controllers", {}).get(controller, {}).get("containers", {})
    return dict(containers.get("main", {}).get("env", {}) or {})


def _values_files() -> list[Path]:
    files = sorted(_CHART.glob("values*.yaml"))
    assert files, f"no values files found under {_CHART}"
    return files


@pytest.mark.parametrize("path", _values_files(), ids=lambda p: p.name)
def test_backend_and_worker_set_the_inference_service_alike(path: Path) -> None:
    values = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    backend, worker = (_env(values, name) for name in _PAIR)
    for key in _KEYS:
        assert backend.get(key) == worker.get(key), (
            f"{path.name}: {key} differs between backend ({backend.get(key)!r}) and "
            f"celery-worker ({worker.get(key)!r}); the worker erases what the backend writes (#1753)"
        )


def test_the_dev_values_actually_enable_the_flag_on_both() -> None:
    """Positive control: the parity above must not hold vacuously over two absences."""
    values = yaml.safe_load((_CHART / "values-dev.yaml").read_text(encoding="utf-8"))
    for name in _PAIR:
        assert _env(values, name).get("INFERENCE_SERVICE_ENABLED") == "true", name
