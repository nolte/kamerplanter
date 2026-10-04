"""#2126 — the database pod gets its own credentials, the application its own account.

Until #2126 the ArangoDB container pulled the WHOLE ``kamerplanter-secrets`` by
``envFrom`` — ``JWT_SECRET_KEY``, ``FERNET_KEY``, ``INTERNAL_SERVICE_TOKEN``, mail
and API keys landed in a pod that needs one value, its root password — while the
backend, worker and beat connected as ``root``. The vectordb controller already
showed the scoped shape (one ``secretKeyRef``).

Held here, for every release that runs the database (overlays merged the way Helm
merges them, see test_chart_trusted_proxy_hops.py):

* no container of the ``arangodb`` controller has an ``envFrom``;
* every secret it reads is a named key, and the main container reads exactly
  ``ARANGO_ROOT_PASSWORD``;
* the base release's backend, worker and beat do not connect as ``root``.

The rendered form — and that the ``app-user`` container provisions exactly the
account the backend uses — is asserted by ``scripts/ci/assert_chart_contracts.sh``,
because those values are templates that only a render resolves.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

_CHART = Path(__file__).resolve().parents[5] / "helm" / "kamerplanter"
_BASE = _CHART / "values.yaml"


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


def _controller(values: dict[str, Any], name: str) -> dict[str, Any]:
    return dict((values.get("controllers") or {}).get(name) or {})


def _releases_with_the_database() -> list[Path]:
    files = sorted(_CHART.glob("values*.yaml"))
    assert _BASE in files, f"{_BASE} not found"
    return [path for path in files if _controller(_merged(path), "arangodb").get("enabled") is not False]


def _secret_keys(container: dict[str, Any]) -> list[str]:
    keys = []
    for value in (container.get("env") or {}).values():
        if isinstance(value, dict) and "secretKeyRef" in (value.get("valueFrom") or {}):
            keys.append(value["valueFrom"]["secretKeyRef"]["key"])
    return sorted(keys)


@pytest.mark.parametrize("path", _releases_with_the_database(), ids=lambda p: p.name)
def test_no_database_container_receives_a_whole_secret(path: Path) -> None:
    containers = _controller(_merged(path), "arangodb").get("containers") or {}
    assert containers, f"{path.name}: the arangodb controller has no containers"
    for name, container in containers.items():
        assert not container.get("envFrom"), (
            f"{path.name}: controllers.arangodb.containers.{name} has envFrom {container.get('envFrom')!r} — "
            "the database pod would receive every application secret (#2126); use one secretKeyRef per key"
        )


@pytest.mark.parametrize("path", _releases_with_the_database(), ids=lambda p: p.name)
def test_the_database_reads_exactly_its_root_password(path: Path) -> None:
    main = (_controller(_merged(path), "arangodb").get("containers") or {}).get("main") or {}
    assert _secret_keys(main) == ["ARANGO_ROOT_PASSWORD"], (
        f"{path.name}: the arangodb main container reads secret keys {_secret_keys(main)}, "
        "expected exactly ARANGO_ROOT_PASSWORD (#2126)"
    )


@pytest.mark.parametrize("controller", ["backend", "celery-worker", "celery-beat"])
def test_the_base_release_does_not_connect_as_root(controller: str) -> None:
    env = ((_controller(_load(_BASE), controller).get("containers") or {}).get("main") or {}).get("env") or {}
    assert "ARANGODB_USERNAME" in env, f"{controller}: no ARANGODB_USERNAME — the application default is root"
    assert str(env["ARANGODB_USERNAME"]).strip() != "root", (
        f"{controller}: connects to ArangoDB as root (#2126); use the application account"
    )


def test_the_base_release_runs_the_database() -> None:
    """Positive control: the parametrised checks must not pass by selecting no release."""
    assert _BASE in _releases_with_the_database()
