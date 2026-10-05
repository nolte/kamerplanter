"""#2154 — the chart's Celery worker reports ready only once it consumes, and its budget fits the gate.

The worker had a liveness probe only, so Kubernetes counted it ready the moment
its container started and a rollout removed the old worker at once — also when
the new one could not log in to ArangoDB and failed every task. Now
(``app/tasks/__init__.py``):

* with ``WORKER_READY_FILE`` set, ``celeryd_init`` proves the database login,
  retrying for ``WORKER_DATABASE_START_BUDGET_SECONDS``, and exits when it cannot;
* ``worker_ready`` writes that file once the consumer runs.

For that to hold in a release, in every values profile that runs the worker:

1. the worker sets ``WORKER_READY_FILE`` and its startup and readiness probes test
   exactly that path (a probe on another path never succeeds, or succeeds for the
   wrong reason);
2. the startup budget (``initialDelaySeconds + periodSeconds * failureThreshold``)
   outlasts the database gate plus one slow attempt plus the import — read from the
   code constant, so a longer gate cannot silently outgrow the chart;
3. liveness asks this pod's own worker (``-d celery@$HOSTNAME``): a broadcast
   ``inspect ping`` passes when *any* worker answers (measured: exit 0 with this
   pod's worker gone and another alive).

Overlays are merged the way Helm merges them (see test_chart_backend_startup_budget.py).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from app.config.constants import WORKER_DATABASE_START_BUDGET_SECONDS

_CHART = Path(__file__).resolve().parents[5] / "helm" / "kamerplanter"
_BASE = _CHART / "values.yaml"

#: One attempt against an unreachable ArangoDB takes ~18 s (python-arango's own
#: retries, measured 2026-10-05); the gate may start one just before its deadline.
_SLOWEST_ATTEMPT_SECONDS = 18
#: Importing ``app.tasks`` (~6 s measured on a workstation; the pod has 0.5 CPU)
#: plus the broker connection, generously.
_IMPORT_AND_BROKER_SECONDS = 60


def _load(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _helm_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in overlay.items():
        if value is None:
            merged.pop(key, None)
        elif isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _helm_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _worker_main(path: Path) -> dict[str, Any] | None:
    values = _load(_BASE) if path == _BASE else _helm_merge(_load(_BASE), _load(path))
    worker = (values.get("controllers") or {}).get("celery-worker") or {}
    if worker.get("enabled") is False:
        return None
    return dict(((worker.get("containers") or {}).get("main")) or {})


def _profiles() -> list[Path]:
    files = sorted(_CHART.glob("values*.yaml"))
    assert _BASE in files
    running = [path for path in files if _worker_main(path) is not None]
    assert _BASE in running, "the base chart runs no worker"
    return running


def _probe(main: dict[str, Any], kind: str) -> dict[str, Any]:
    probe = (main.get("probes") or {}).get(kind) or {}
    assert probe.get("enabled") is True and probe.get("custom") is True, f"{kind} probe is not an enabled custom probe"
    return dict(probe.get("spec") or {})


def _budget_seconds(spec: dict[str, Any]) -> int:
    return int(spec.get("initialDelaySeconds", 0)) + int(spec.get("periodSeconds", 10)) * int(
        spec.get("failureThreshold", 3)
    )


@pytest.mark.parametrize("profile", _profiles(), ids=lambda path: path.name)
def test_startup_and_readiness_test_the_file_the_worker_writes(profile: Path) -> None:
    main = _worker_main(profile)
    assert main is not None
    ready_file = (main.get("env") or {}).get("WORKER_READY_FILE")
    assert isinstance(ready_file, str) and ready_file.startswith("/tmp/"), (  # noqa: S108 — the pod's writable emptyDir
        f"{profile.name}: WORKER_READY_FILE must be set on the writable /tmp volume, got {ready_file!r}"
    )
    for kind in ("startup", "readiness"):
        assert _probe(main, kind).get("exec", {}).get("command") == ["test", "-f", ready_file], (
            f"{profile.name}: the {kind} probe does not test {ready_file}"
        )


@pytest.mark.parametrize("profile", _profiles(), ids=lambda path: path.name)
def test_the_startup_budget_outlasts_the_database_gate(profile: Path) -> None:
    main = _worker_main(profile)
    assert main is not None
    needed = WORKER_DATABASE_START_BUDGET_SECONDS + _SLOWEST_ATTEMPT_SECONDS + _IMPORT_AND_BROKER_SECONDS
    budget = _budget_seconds(_probe(main, "startup"))
    assert budget > needed, (
        f"{profile.name}: worker startup budget {budget}s <= {needed}s (database gate "
        f"{WORKER_DATABASE_START_BUDGET_SECONDS}s + one slow attempt + import): the kubelet would kill a worker "
        "that is still allowed to wait for its database"
    )


@pytest.mark.parametrize("profile", _profiles(), ids=lambda path: path.name)
def test_liveness_asks_this_pods_own_worker(profile: Path) -> None:
    main = _worker_main(profile)
    assert main is not None
    command = " ".join(_probe(main, "liveness").get("exec", {}).get("command") or [])
    assert "inspect ping" in command
    assert '-d "celery@${HOSTNAME}"' in command, (
        f"{profile.name}: liveness pings every worker; it passes while any worker answers: {command!r}"
    )
