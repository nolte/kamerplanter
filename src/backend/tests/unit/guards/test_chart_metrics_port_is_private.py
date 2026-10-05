"""#2129 — the backend's metrics port is reachable by the configured Prometheus and by nothing else.

``/metrics`` is served on a listener of its own (``METRICS_PORT``), never as a
route of the API, so the public path (ingress -> frontend nginx -> backend
:8000) cannot reach it. What keeps a pod inside the cluster from reading it is
the NetworkPolicy: the backend's own policy admits the frontend on 8000 only,
and ``backend-metrics`` admits the Prometheus pods (namespace *and* pod label)
on the metrics port only. Both are pinned here for every release overlay, as
Helm merges it over ``values.yaml``.

The port is a literal in three places (``values.yaml`` explains why); they must
agree, or Prometheus scrapes a port nothing listens on — or the backend listens
on one the policy does not admit.

Measured with ``helm template`` while writing this (every overlay, monitoring
off and on): off renders no ServiceMonitor, no ``metrics`` Service port, no
``backend-metrics`` policy and ``METRICS_PORT=0``; on renders all four with 9464.
This test reads the values instead of shelling out to ``helm``, which the unit
tier does not install.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from tests.unit.guards.test_chart_trusted_proxy_hops import _BASE, _all_releases, _helm_merge, _load

_PORT = 9464
_API_PORT = 8000
_ENABLED_BY_MONITORING = "{{ if .Values.monitoring.enabled }}true{{ end }}"


def _merged(path: Path) -> dict[str, Any]:
    return _load(_BASE) if path == _BASE else _helm_merge(_load(_BASE), _load(path))


def _ports_admitted(policy: dict[str, Any]) -> set[int]:
    ports: set[int] = set()
    for rule in (policy.get("rules") or {}).get("ingress") or []:
        for port in rule.get("ports") or []:
            ports.add(int(port["port"]))
    return ports


def test_monitoring_is_off_by_default() -> None:
    values = _load(_BASE)

    assert values["monitoring"]["enabled"] is False
    env = values["controllers"]["backend"]["containers"]["main"]["env"]
    assert env["METRICS_PORT"] == "{{ if .Values.monitoring.enabled }}" + str(_PORT) + "{{ else }}0{{ end }}"


def test_the_three_literals_of_the_metrics_port_agree() -> None:
    values = _load(_BASE)

    service_port = values["service"]["backend"]["ports"]["metrics"]
    policy = values["networkpolicies"]["backend-metrics"]
    monitor = values["serviceMonitor"]["backend"]

    assert service_port["port"] == _PORT
    assert service_port["enabled"] == _ENABLED_BY_MONITORING
    assert _ports_admitted(policy) == {_PORT}
    assert policy["enabled"] == _ENABLED_BY_MONITORING
    assert monitor["enabled"] == _ENABLED_BY_MONITORING
    assert [endpoint["port"] for endpoint in monitor["endpoints"]] == ["metrics"]
    assert monitor["service"]["identifier"] == "backend"


@pytest.mark.parametrize("release", _all_releases(), ids=lambda path: path.name)
def test_only_the_prometheus_policy_admits_the_metrics_port(release: Path) -> None:
    policies = _merged(release).get("networkpolicies") or {}

    for name, policy in policies.items():
        if not isinstance(policy, dict) or name == "backend-metrics":
            continue
        assert _PORT not in _ports_admitted(policy), f"{release.name}: networkpolicies.{name} admits {_PORT}"
    backend = policies.get("backend") or {}
    if backend.get("enabled") is not False:
        assert _ports_admitted(backend) == {_API_PORT}, f"{release.name}: the backend policy admits more than 8000"


@pytest.mark.parametrize("release", _all_releases(), ids=lambda path: path.name)
def test_every_scraper_is_named_by_namespace_and_pod(release: Path) -> None:
    policy = (_merged(release).get("networkpolicies") or {}).get("backend-metrics") or {}
    if policy.get("enabled") is False:
        return
    rules = (policy.get("rules") or {}).get("ingress") or []

    assert rules, f"{release.name}: backend-metrics has no ingress rule"
    for rule in rules:
        peers = rule.get("from") or []
        assert peers, f"{release.name}: a rule without `from` admits every source"
        for peer in peers:
            assert peer.get("namespaceSelector", {}).get("matchLabels"), peer
            assert peer.get("podSelector", {}).get("matchLabels"), peer


def test_no_ingress_or_route_names_the_metrics_port() -> None:
    values = _load(_BASE)
    text = repr({key: values.get(key) for key in ("ingress", "route", "rawResources")})

    assert str(_PORT) not in text
    assert "metrics" not in text
