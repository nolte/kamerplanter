"""Prometheus exposition for the NFR-007 SLOs, on its own port, without personal labels (#2129, MT-033).

Before #2129 there was no ``/metrics`` at all: the request-latency and error-rate
SLOs of NFR-007 could not be measured. Three properties are asserted here:

1. **The reach probe.** The metrics listener serves ``http_request_duration_seconds``
   for a request that went through the real API app (``app.main.app``, every
   middleware in place).
2. **No tenant, no person, no raw path in a label.** ``handler`` is the route
   *pattern* (``/api/v1/t/{tenant_slug}/…``), never the requested path — that holds
   the tenant slug derived from a person's display name and, on the attachment
   route, the download token. A path no route matched is ``unmatched``, so a
   scanner cannot grow the series set without bound. Tenant is deliberately *not*
   a label (cardinality, and it would publish the tenant set to whoever scrapes).
3. **Not on the API port.** The API app serves no metrics route: the public
   ingress reaches the API through the frontend's nginx, and the listener runs on
   ``METRICS_PORT``, which the Service exposes only to the scraper the
   NetworkPolicy admits (``helm/kamerplanter/values.yaml``, ``monitoring``).
"""

from __future__ import annotations

import urllib.request
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from prometheus_client.parser import text_string_to_metric_families

from app.observability.metrics import UNMATCHED_HANDLER, start_metrics_server

_SLUG = "-".join(("erika", "musterfrau", "2129"))


@pytest.fixture(scope="module")
def api() -> TestClient:
    from app.main import app

    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def scrape() -> Iterator[str]:
    server = start_metrics_server(0, "127.0.0.1")
    assert server is not None
    url = f"http://127.0.0.1:{server.server_port}/metrics"
    try:
        yield url
    finally:
        server.shutdown()
        server.server_close()


def _samples(url: str, name: str) -> list[dict[str, str]]:
    with urllib.request.urlopen(url, timeout=5) as response:  # noqa: S310 — loopback test listener
        body = response.read().decode()
    return [
        dict(sample.labels)
        for family in text_string_to_metric_families(body)
        for sample in family.samples
        if sample.name == name
    ]


def _body(url: str) -> str:
    with urllib.request.urlopen(url, timeout=5) as response:  # noqa: S310 — loopback test listener
        return response.read().decode()


def test_the_metrics_port_serves_the_request_duration_of_an_api_request(api: TestClient, scrape: str) -> None:
    api.get("/api/v1/health/live")

    samples = _samples(scrape, "http_request_duration_seconds_count")

    assert {"method": "GET", "handler": "/api/v1/health/live", "status": "200"} in samples
    # NFR-007 §2.1 reads error rate and throughput from the counter.
    assert {"method": "GET", "handler": "/api/v1/health/live", "status": "200"} in _samples(
        scrape, "http_requests_total"
    )


def test_the_handler_label_is_the_route_pattern_never_the_requested_path(api: TestClient, scrape: str) -> None:
    # The route matches whatever it answers (here without credentials or database).
    response = api.get(f"/api/v1/t/{_SLUG}/actuators")
    api.get(f"/no-such-route/{_SLUG}")

    body = _body(scrape)
    samples = _samples(scrape, "http_request_duration_seconds_count")
    handlers = {s["handler"] for s in samples}

    assert _SLUG not in body
    # The full template, inclusion prefixes and all — not the route's path relative to its router.
    assert {
        "method": "GET",
        "handler": "/api/v1/t/{tenant_slug}/actuators",
        "status": str(response.status_code),
    } in samples
    assert UNMATCHED_HANDLER in handlers


def test_no_series_is_labelled_by_tenant_person_or_request(api: TestClient, scrape: str) -> None:
    api.get("/api/v1/health/live")

    body = _body(scrape)
    families = list(text_string_to_metric_families(body))
    label_names = {name for family in families for sample in family.samples for name in sample.labels}

    assert label_names <= {
        "method",
        "handler",
        "status",
        "le",
        "generation",
        "implementation",
        "major",
        "minor",
        "patchlevel",
        "version",
    }
    for forbidden in ("tenant", "user", "subject", "actor", "request_id", "ip"):
        assert forbidden not in label_names


@pytest.mark.parametrize("path", ["/metrics", "/api/v1/metrics", "/api/metrics"])
def test_the_api_app_serves_no_metrics(api: TestClient, path: str) -> None:
    response = api.get(path)

    assert response.status_code == 404
    assert "http_request_duration_seconds" not in response.text


def test_a_port_of_zero_in_the_settings_starts_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config.settings import settings
    from app.observability.metrics import start_configured_metrics_server

    monkeypatch.setattr(settings, "metrics_port", 0)

    assert start_configured_metrics_server() is None
