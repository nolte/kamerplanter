"""Which `X-Forwarded-For` entry is the caller, and which one is their claim (#1151).

`resolve_client_ip` feeds three controls that are only worth anything if the
address is the caller's and not the caller's *choice*: the device-pairing
lockout (#1118), the service-account `ip_allowlist` (SEC-004), and — proposed in
#1144 — the rate limiter.

It took the **left-most** entry, which is only the real client if every proxy in
front replaces the header. Nothing in this repository makes that true:

* `src/frontend/nginx.conf:18` sets `X-Forwarded-For $proxy_add_x_forwarded_for`,
  which **appends** the peer to whatever arrived. A caller who sends
  `X-Forwarded-For: 203.0.113.1` is handed back `203.0.113.1, <their real peer>`
  — and the left-most entry is their invention.
* No `forwardedHeaders` / `trustedIPs` is pinned anywhere in `helm/`
  (`ingress: {}`), so the ingress behaviour that would sanitise inbound headers
  is an assumption, not a configured fact.

## Why counting from the right

Every proxy in the chain *appends*, so the trustworthy entries are at the right
end and anything a caller invents is pushed left. Counting `trusted_proxy_hops`
entries in from the right therefore ignores a prepended claim **whether or not**
the outermost proxy sanitises — which is the property the old reading lacked.

The deployments differ in depth, which is why this is configuration and not a
constant:

* e2e / dev — client → nginx → backend: nginx appends nothing before the peer,
  so the caller is the **last** entry (`trusted_proxy_hops = 0`).
* production — client → ingress → nginx → backend: nginx appends the ingress's
  address, so the caller is the **second to last** (`trusted_proxy_hops = 1`).

The default is the *shallow* one on purpose. Configured too low, the resolved
address collapses towards the nearest proxy — controls then bind more coarsely
than intended (the shared-bucket problem #1130 describes), which is a
degradation. Configured too high, the resolver would start reading entries a
caller can write — which is a bypass. Degrading beats bypassing.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.common.request_ip import resolve_client_ip

_PEER = "10.0.0.5"
_CLIENT = "198.51.100.7"
_SPOOF = "203.0.113.1"
_INGRESS = "10.0.0.9"


def _request(xff: str | None, peer: str | None = _PEER) -> SimpleNamespace:
    """A request stub carrying only what the resolver reads."""
    headers = {"x-forwarded-for": xff} if xff is not None else {}
    return SimpleNamespace(
        headers=headers,
        client=SimpleNamespace(host=peer) if peer is not None else None,
    )


@pytest.fixture
def hops(monkeypatch: pytest.MonkeyPatch):
    """Set `trusted_proxy_hops` for one test."""

    def _set(value: int) -> None:
        from app.config.settings import settings

        monkeypatch.setattr(settings, "trusted_proxy_hops", value)

    return _set


class TestASpoofedClaimIsIgnored:
    """The finding: a caller could name their own bucket."""

    def test_a_prepended_claim_does_not_win_in_the_single_proxy_chain(self, hops) -> None:
        """nginx appended the real peer; the claim sits to its left."""
        hops(0)

        assert resolve_client_ip(_request(f"{_SPOOF}, {_CLIENT}")) == _CLIENT

    def test_a_prepended_claim_does_not_win_in_the_two_proxy_chain(self, hops) -> None:
        """The ingress saw the client, nginx appended the ingress — the claim is two to the left."""
        hops(1)

        assert resolve_client_ip(_request(f"{_SPOOF}, {_CLIENT}, {_INGRESS}")) == _CLIENT

    def test_many_prepended_claims_change_nothing(self, hops) -> None:
        """Padding the header cannot walk the index off the trusted tail."""
        hops(1)
        claims = ", ".join([_SPOOF] * 12)

        assert resolve_client_ip(_request(f"{claims}, {_CLIENT}, {_INGRESS}")) == _CLIENT


class TestTheHonestChains:
    """What the resolver must still answer when nobody is lying."""

    def test_single_proxy_reads_the_last_entry(self, hops) -> None:
        hops(0)

        assert resolve_client_ip(_request(_CLIENT)) == _CLIENT

    def test_two_proxies_read_the_second_to_last(self, hops) -> None:
        hops(1)

        assert resolve_client_ip(_request(f"{_CLIENT}, {_INGRESS}")) == _CLIENT

    def test_no_header_falls_back_to_the_socket_peer(self, hops) -> None:
        hops(1)

        assert resolve_client_ip(_request(None)) == _PEER

    def test_entries_are_trimmed(self, hops) -> None:
        hops(1)

        assert resolve_client_ip(_request(f"  {_CLIENT} ,  {_INGRESS}  ")) == _CLIENT


class TestAShortChainFallsBackRatherThanGuessing:
    """A header shorter than the configured depth is not evidence about anyone."""

    def test_fewer_entries_than_configured_hops_uses_the_peer(self, hops) -> None:
        """Two hops configured, one entry present: the chain is not the one configured.

        Reading the only entry would mean trusting a value that, in this
        configuration, no trusted proxy is known to have written. The socket
        peer is the one address nobody can fake.
        """
        hops(2)

        assert resolve_client_ip(_request(_SPOOF)) == _PEER

    def test_an_empty_header_uses_the_peer(self, hops) -> None:
        hops(0)

        assert resolve_client_ip(_request("   ")) == _PEER

    def test_no_header_and_no_peer_answers_none(self, hops) -> None:
        """The only case with nothing to report — kept distinct from a wrong guess."""
        hops(0)

        assert resolve_client_ip(_request(None, peer=None)) is None
