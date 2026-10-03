"""A runtime signal when the forwarded chain is deeper than ``trusted_proxy_hops`` explains (#2045).

The app cannot know its proxy topology at start-up, so a misconfigured depth was
silent: with ``trusted_proxy_hops = 0`` behind ingress + nginx the resolver reads
the entry nginx appended — the ingress address — and every IP-keyed control
(rate limits, pairing lockout, ``ip_allowlist``) collapses into one bucket.

The signal is a warning logged **once per process**, raised when a request with
``trusted_proxy_hops == 0`` carries a chain of more than one entry. One entry is
the correct shape of a run without ingress (client → nginx → backend, nginx writes the caller),
so it stays silent there. The warning never carries the header or an address.
"""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import MagicMock

import pytest
from structlog.testing import capture_logs

from app.common import request_ip
from app.common.request_ip import resolve_client_ip
from app.config.settings import settings

_EVENT = "forwarded_chain_deeper_than_trusted_proxy_hops"
_CLIENT = "198.51.100.23"
_INGRESS = "10.42.0.17"
_PEER = "10.42.1.5"


def _make_request(forwarded_for: str | None) -> MagicMock:
    request = MagicMock()
    request.client.host = _PEER
    request.headers = {"x-forwarded-for": forwarded_for} if forwarded_for is not None else {}
    return request


@pytest.fixture(autouse=True)
def _fresh_process(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    # Each test starts as a process that has not warned yet.
    monkeypatch.setattr(request_ip, "_zero_hops_warning_emitted", False, raising=False)
    monkeypatch.setattr(settings, "trusted_proxy_hops", 0)
    yield


def _warnings(logs: list[dict[str, object]]) -> list[dict[str, object]]:
    return [entry for entry in logs if entry.get("event") == _EVENT]


class TestZeroHopsWarning:
    def test_chain_deeper_than_zero_hops_warns(self) -> None:
        with capture_logs() as logs:
            resolve_client_ip(_make_request(f"{_CLIENT}, {_INGRESS}"))

        [warning] = _warnings(logs)
        assert warning["log_level"] == "warning"
        assert warning["trusted_proxy_hops"] == 0
        assert warning["forwarded_entries"] == 2

    def test_warns_only_once_per_process(self) -> None:
        with capture_logs() as logs:
            for _ in range(3):
                resolve_client_ip(_make_request(f"{_CLIENT}, {_INGRESS}"))

        assert len(_warnings(logs)) == 1

    def test_warning_carries_no_address_or_header(self) -> None:
        with capture_logs() as logs:
            resolve_client_ip(_make_request(f"{_CLIENT}, {_INGRESS}"))

        [warning] = _warnings(logs)
        rendered = repr(warning)
        for address in (_CLIENT, _INGRESS, _PEER):
            assert address not in rendered

    def test_single_entry_chain_is_the_correct_zero_hops_shape(self) -> None:
        """client → nginx → backend: nginx wrote the caller, nothing is wrong."""
        with capture_logs() as logs:
            assert resolve_client_ip(_make_request(_CLIENT)) == _CLIENT

        assert _warnings(logs) == []

    def test_no_header_is_silent(self) -> None:
        with capture_logs() as logs:
            assert resolve_client_ip(_make_request(None)) == _PEER

        assert _warnings(logs) == []

    def test_configured_depth_is_silent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(settings, "trusted_proxy_hops", 1)

        with capture_logs() as logs:
            assert resolve_client_ip(_make_request(f"{_CLIENT}, {_INGRESS}")) == _CLIENT

        assert _warnings(logs) == []

    def test_resolution_is_unchanged_by_the_warning(self) -> None:
        """The signal only observes: hops 0 still reads the last entry."""
        assert resolve_client_ip(_make_request(f"{_CLIENT}, {_INGRESS}")) == _INGRESS
