"""#2045 — every chart release that runs the backend keeps ``TRUSTED_PROXY_HOPS >= 1``.

The reference request path is ingress -> frontend nginx -> backend, so the
caller sits one entry in from the right of ``X-Forwarded-For``. The application
default is ``0``; a chart that drops the key or sets it to ``0`` resolves every
caller to the ingress address, and every IP-keyed control — the slowapi limits
(now counted in shared Valkey, so one bucket for the whole deployment), the
device-pairing lockout and the service-account ``ip_allowlist`` — binds to a
single shared bucket. ``values.yaml`` explains the value next to the key; this
pins it.

Helm applies the chart's ``values.yaml`` under every ``-f`` overlay, so each
overlay is checked as Helm would see it: ``values.yaml`` deep-merged with the
overlay (maps merge, everything else is replaced, ``null`` deletes). Releases
that disable the backend controller (the ki / recognition overlays) are
skipped — they serve no rate-limited route.

A deployment that deliberately routes ``/api`` straight to the backend has one
proxy fewer and must set ``0`` in its own GitOps values; that is outside this
repository and outside this check.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

_CHART = Path(__file__).resolve().parents[5] / "helm" / "kamerplanter"
_BASE = _CHART / "values.yaml"
_KEY = "TRUSTED_PROXY_HOPS"


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


def _backend(values: dict[str, Any]) -> dict[str, Any]:
    return dict((values.get("controllers") or {}).get("backend") or {})


def _merged(path: Path) -> dict[str, Any]:
    return _load(_BASE) if path == _BASE else _helm_merge(_load(_BASE), _load(path))


def _all_releases() -> list[Path]:
    files = sorted(_CHART.glob("values*.yaml"))
    assert _BASE in files, f"{_BASE} not found"
    return files


def _backend_disabled(path: Path) -> bool:
    return _backend(_merged(path)).get("enabled") is False


#: Releases that switch the backend off (``backend.enabled: false``): they serve no
#: rate-limited route, so the hop count means nothing there. Named instead of
#: skipped at run time: the backend tier declares ``--max-skipped 0`` (#1434), and a
#: new release that drops the backend should be a visible decision in this list.
_WITHOUT_BACKEND = frozenset({"values-dev-ki.yaml", "values-dev-recognition.yaml"})


def _releases() -> list[Path]:
    return [path for path in _all_releases() if not _backend_disabled(path)]


@pytest.mark.parametrize("path", _releases(), ids=lambda p: p.name)
def test_backend_trusts_at_least_one_proxy_hop(path: Path) -> None:
    backend = _backend(_merged(path))

    env = ((backend.get("containers") or {}).get("main") or {}).get("env") or {}
    assert _KEY in env, (
        f"{path.name}: backend env has no {_KEY}; the application default 0 resolves every "
        "caller behind ingress + nginx to one address (#2045)"
    )
    raw = env[_KEY]
    try:
        hops = int(str(raw))
    except ValueError:
        pytest.fail(f"{path.name}: backend {_KEY}={raw!r} is not an integer")
    assert hops >= 1, (
        f"{path.name}: backend {_KEY}={raw!r}; behind ingress + nginx it must be >= 1, "
        "or every IP-keyed limit shares one bucket (#2045)"
    )


def test_the_base_release_runs_the_backend() -> None:
    """Positive control: the check above must not pass by skipping every file."""
    assert _backend(_load(_BASE)).get("enabled") is not False


def test_the_releases_without_a_backend_are_exactly_the_named_ones() -> None:
    """A release that drops the backend, or gains it back, must be a decision made here."""
    disabled = {path.name for path in _all_releases() if _backend_disabled(path)}
    assert disabled == _WITHOUT_BACKEND, (
        f"releases with the backend switched off changed: {sorted(disabled)} (named: {sorted(_WITHOUT_BACKEND)}). "
        "Add or remove the release in _WITHOUT_BACKEND once you have checked it serves no rate-limited route."
    )
