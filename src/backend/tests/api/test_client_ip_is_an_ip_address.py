"""The client address every IP-keyed control uses is an IP address (#2053).

``resolve_client_ip`` returned the selected ``X-Forwarded-For`` entry as it
came. With ``TRUSTED_PROXY_HOPS=0`` — or on a path around our proxies — that
entry is the caller's, so any string became the key of the rate limits, the
pairing lockout, the service-account allowlist and, since #2059, the per-source
reset budget. Measured through ``GET /api/health`` before the fix: four headers
(``not-an-ip``, 200 × ``x``, ``2001:DB8::1``, ``2001:db8:0:0::1``) → four
limiter buckets. Now a non-address falls back to the socket peer and an address
is keyed in its canonical form: two buckets.
"""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.api.v1.auth.router import process_memory_limiter


@pytest.fixture
def client() -> Iterator[TestClient]:
    with patch("app.main.get_connection"), patch("app.main.ensure_collections"):
        from app.main import app

    yield TestClient(app)


def _buckets() -> set[str]:
    return {key.split("/")[1] for key in process_memory_limiter._storage.storage}


def test_a_header_that_is_no_address_counts_under_the_peer(client: TestClient) -> None:
    for header in ("not-an-ip", "x" * 200, "203.0.113.7:4444", "<script>"):
        assert client.get("/api/health", headers={"X-Forwarded-For": header}).status_code == 200

    assert _buckets() == {"testclient"}


def test_spellings_of_one_address_share_one_bucket(client: TestClient) -> None:
    for header in ("2001:DB8::1", "2001:db8:0:0::1", "2001:0db8::0001"):
        client.get("/api/health", headers={"X-Forwarded-For": header})
    client.get("/api/health", headers={"X-Forwarded-For": "203.0.113.7"})

    assert _buckets() == {"2001:db8::1", "203.0.113.7"}
