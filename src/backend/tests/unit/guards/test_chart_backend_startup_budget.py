"""#2125 — the backend container's start-up budget outlasts the migration barrier.

The FastAPI lifespan runs ``ensure_collections``, every pending migration and the
seed registry before uvicorn accepts a connection (``app/main.py``). A replica
that finds the migration lock held waits for it — bounded by
``BARRIER_TIMEOUT_SECONDS`` (``app/migrations/framework/runner.py``, twice the
300 s lock TTL) — and only then fails on its own with
``MigrationBarrierTimeoutError``.

Without a ``startupProbe`` the liveness probe guards that start: with the chart's
15 s initial delay, 10 s period and three failures the kubelet kills the
container about 35 s after it started. Measured on 2026-10-04 against an empty
ArangoDB 3.12.12 on a workstation: importing ``app.main`` takes 5.8 s, the
lifespan's database work 32.6 s (``ensure_collections`` 1.2 s, migrations 6.5 s,
seeds 24.7 s) — a first install is killed before it ever listens, on hardware
faster than the cluster's 1-CPU limit. A killed migrator also leaves its lock
fresh, so the next start waits on it and is killed again, until the lock goes
stale.

So every release that runs the backend gives its main container a startup probe
whose budget (``initialDelaySeconds + periodSeconds * failureThreshold``) is
LONGER than the barrier: the application's own bounded wait, not the kubelet,
decides that a start has failed. Read from the code constant, not from a copy of
the number, so a longer barrier cannot silently outgrow the chart.

Overlays are merged onto ``values.yaml`` the way Helm merges them (see
test_chart_trusted_proxy_hops.py for the helper's rationale).

**The documented maximum start-up time (operator decision on #2125, 2026-10-10).**
Migrations and seeds stay in the lifespan — no pre-upgrade job. The operator
contract is therefore the start-up budget itself, published as a table in
``docs/{de,en}/deployment/kubernetes.md`` (section "Startdauer des Backends" /
"Backend start-up time"): the maximum start-up time with its probe arithmetic,
the barrier wait and the lock TTL. Each row is compared with the chart and the
code constants, so a changed budget, barrier or TTL cannot leave the operator
page quoting the old number.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

from app.migrations.framework.runner import BARRIER_TIMEOUT_SECONDS
from app.migrations.framework.tracking import LOCK_TTL_SECONDS

_REPO = Path(__file__).resolve().parents[5]
_CHART = _REPO / "helm" / "kamerplanter"
_BASE = _CHART / "values.yaml"
_LIVENESS_PATH = "/api/v1/health/live"
_DEPLOYMENT_DOCS = [_REPO / "docs" / lang / "deployment" / "kubernetes.md" for lang in ("de", "en")]

#: One row of the start-up table: ``| <label naming `IDENT`> | <seconds> s [(<n> Minuten|minutes)] |``.
_LIMIT_ROW = re.compile(
    r"^\|(?P<label>[^|\n]*`(?P<ident>startupProbe|BARRIER_TIMEOUT_SECONDS|LOCK_TTL_SECONDS)`[^|\n]*)\|"
    r"\s*(?P<seconds>\d+)\s*s\b(?:\s*\((?P<minutes>\d+)\s+(?:Minuten|minutes)\))?[^|\n]*\|\s*$",
    re.MULTILINE,
)
#: The probe arithmetic inside the startupProbe label: ``<period> s × <failureThreshold>``.
_PROBE_ARITHMETIC = re.compile(r"(?P<period>\d+)\s*s\s*×\s*(?P<threshold>\d+)")


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


def _merged(path: Path) -> dict[str, Any]:
    return _load(_BASE) if path == _BASE else _helm_merge(_load(_BASE), _load(path))


def _backend(values: dict[str, Any]) -> dict[str, Any]:
    return dict((values.get("controllers") or {}).get("backend") or {})


def _releases_with_backend() -> list[Path]:
    files = sorted(_CHART.glob("values*.yaml"))
    assert _BASE in files, f"{_BASE} not found"
    return [path for path in files if _backend(_merged(path)).get("enabled") is not False]


def _probes(path: Path) -> dict[str, Any]:
    main = ((_backend(_merged(path)).get("containers") or {}).get("main")) or {}
    return dict(main.get("probes") or {})


def _budget_seconds(spec: dict[str, Any]) -> int:
    return int(spec.get("initialDelaySeconds", 0)) + int(spec.get("periodSeconds", 10)) * int(
        spec.get("failureThreshold", 3)
    )


@pytest.mark.parametrize("path", _releases_with_backend(), ids=lambda p: p.name)
def test_backend_has_a_startup_probe_on_the_liveness_endpoint(path: Path) -> None:
    startup = _probes(path).get("startup") or {}
    assert startup.get("enabled") is True and startup.get("custom") is True, (
        f"{path.name}: controllers.backend.containers.main.probes.startup is not an enabled custom probe — "
        "the liveness probe then kills the migrating lifespan after ~35 s (#2125)"
    )
    http_get = (startup.get("spec") or {}).get("httpGet") or {}
    assert http_get.get("path") == _LIVENESS_PATH, (
        f"{path.name}: the startup probe must ask the liveness endpoint {_LIVENESS_PATH} "
        f"(it answers once uvicorn listens, i.e. once the lifespan finished), got {http_get.get('path')!r}"
    )


@pytest.mark.parametrize("path", _releases_with_backend(), ids=lambda p: p.name)
def test_backend_startup_budget_outlasts_the_migration_barrier(path: Path) -> None:
    spec = (_probes(path).get("startup") or {}).get("spec") or {}
    budget = _budget_seconds(spec)
    assert budget > BARRIER_TIMEOUT_SECONDS, (
        f"{path.name}: backend startup budget {budget}s <= BARRIER_TIMEOUT_SECONDS={BARRIER_TIMEOUT_SECONDS}s — "
        "the kubelet would kill a replica that is still legitimately waiting for the migration lock (#2125)"
    )


def test_the_budget_formula_is_the_kubelets() -> None:
    """Positive control for the arithmetic: the chart's own liveness probe is the ~35-45 s window of the issue."""
    liveness = _probes(_BASE).get("liveness") or {}
    budget = _budget_seconds(liveness.get("spec") or {})
    assert 0 < budget < BARRIER_TIMEOUT_SECONDS, (
        f"liveness budget {budget}s: the control must stay a short window, or the formula above proves nothing"
    )


def test_the_base_release_runs_the_backend() -> None:
    """Positive control: the parametrised checks must not pass by selecting no release."""
    assert _BASE in _releases_with_backend()


def _documented_limits(doc: Path) -> dict[str, re.Match[str]]:
    """Every start-up limit row of *doc*, by the identifier it names; a duplicate is an error."""
    # The operator page IS the contract under test (#2125): the number a reader
    # is told, not code, so reading the published table is the intent.
    text = doc.read_text(encoding="utf-8")
    rows: dict[str, re.Match[str]] = {}
    for match in _LIMIT_ROW.finditer(text):
        ident = match.group("ident")
        assert ident not in rows, f"{doc.relative_to(_REPO)}: two start-up table rows name `{ident}`"
        rows[ident] = match
    return rows


@pytest.mark.parametrize("doc", _DEPLOYMENT_DOCS, ids=lambda p: p.parts[-3])
def test_documented_maximum_start_up_time_is_the_charts_budget(doc: Path) -> None:
    spec = (_probes(_BASE).get("startup") or {}).get("spec") or {}
    row = _documented_limits(doc).get("startupProbe")
    assert row is not None, f"{doc.relative_to(_REPO)}: no start-up table row naming `startupProbe` (#2125)"
    budget = _budget_seconds(spec)
    assert int(row.group("seconds")) == budget, (
        f"{doc.relative_to(_REPO)}: documents a maximum start-up time of {row.group('seconds')} s, "
        f"the chart's startupProbe budget is {budget} s"
    )
    if row.group("minutes") is not None:
        assert int(row.group("minutes")) * 60 == budget, (
            f"{doc.relative_to(_REPO)}: {row.group('minutes')} minutes is not {budget} s"
        )
    arithmetic = _PROBE_ARITHMETIC.search(row.group("label"))
    assert arithmetic is not None, f"{doc.relative_to(_REPO)}: the startupProbe row names no `<period> s × <failures>`"
    documented = (int(arithmetic.group("period")), int(arithmetic.group("threshold")))
    assert documented == (int(spec.get("periodSeconds", 10)), int(spec.get("failureThreshold", 3))), (
        f"{doc.relative_to(_REPO)}: documents {documented[0]} s × {documented[1]}, "
        f"the chart probes every {spec.get('periodSeconds')} s with failureThreshold {spec.get('failureThreshold')}"
    )


@pytest.mark.parametrize("doc", _DEPLOYMENT_DOCS, ids=lambda p: p.parts[-3])
@pytest.mark.parametrize(
    ("ident", "seconds"),
    [("BARRIER_TIMEOUT_SECONDS", BARRIER_TIMEOUT_SECONDS), ("LOCK_TTL_SECONDS", LOCK_TTL_SECONDS)],
)
def test_documented_migration_waits_are_the_code_constants(doc: Path, ident: str, seconds: int) -> None:
    row = _documented_limits(doc).get(ident)
    assert row is not None, f"{doc.relative_to(_REPO)}: no start-up table row naming `{ident}` (#2125)"
    assert int(row.group("seconds")) == seconds, (
        f"{doc.relative_to(_REPO)}: documents `{ident}` as {row.group('seconds')} s, the code says {seconds} s"
    )
