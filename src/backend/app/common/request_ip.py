"""Resolve the originating client IP behind the reverse proxies.

The backend never sees the caller's socket: an ingress proxy and the frontend's
nginx sit in front, so ``request.client.host`` is a proxy address. The caller has
to be read out of ``X-Forwarded-For`` — and *which* entry that is, is the whole
question.

**Read from the right, not from the left (#1151).** Every proxy in the chain
*appends*: ``nginx.conf`` uses ``$proxy_add_x_forwarded_for``, which adds its
peer to whatever arrived. So a caller who sends ``X-Forwarded-For: 203.0.113.1``
is handed back ``203.0.113.1, <their real address>`` — the left-most entry, which
this module used to return, is the caller's own invention. Taking the entry
:data:`~app.config.settings.Settings.trusted_proxy_hops` in from the right reads
what a proxy we run wrote, and pushes anything the caller prepends harmlessly out
of reach.

**The bound of that claim**, because it is easy to overstate: it holds for a
request that actually traversed ``hops + 1`` of our proxies. The chart's own
NetworkPolicy admits a second path — a rule with no ``from`` selector on port
8000, i.e. direct access to the backend — and a request arriving that way carries
whatever header its sender chose, with no proxy entry appended after it. Reading
from the right is what makes the *proxied* path unforgeable; keeping the direct
path off the network is what makes the other one safe, and that is a
NetworkPolicy question rather than something this function can decide.

This matters beyond tidiness: the device-pairing lockout (#1118) and the
service-account ``ip_allowlist`` (SEC-004) both key on this value. A caller who
can choose it can walk around the lockout and can claim an allowlisted address.
"""

from __future__ import annotations

import structlog
from fastapi import Request

from app.config.settings import settings

logger = structlog.get_logger()

#: Whether this process has already reported a forwarded chain deeper than
#: ``trusted_proxy_hops = 0`` explains (#2045). Once per process: the condition
#: is a property of the deployment, not of a request, and one line per request
#: would bury it. An unsynchronised flag is enough — a race costs a second line.
_zero_hops_warning_emitted = False


def _warn_once_on_unexplained_chain(chain_length: int) -> None:
    """Report, once, a chain that ``trusted_proxy_hops = 0`` cannot account for.

    The app cannot see its proxy topology, so a depth left at the default behind
    ingress + nginx was silent: the resolver read the ingress address nginx
    appended, and every IP-keyed control — the rate limits, the pairing lockout,
    the ``ip_allowlist`` — bound to one shared bucket (#2045). Behind exactly one
    proxy the chain has one entry and hops 0 is right, so only a longer chain is
    reported: either a proxy the setting does not count, or a caller who
    prepended entries. Both are worth a look; neither is decided here.

    A one-entry chain is the shape of a local run without ingress (nginx only).
    The chart's releases, the dev release included, inherit ``TRUSTED_PROXY_HOPS: "1"``
    from ``values.yaml`` and so never reach this branch.

    Logs the entry *count* only — never the header or an address (NFR-011).
    """
    global _zero_hops_warning_emitted
    if _zero_hops_warning_emitted or chain_length <= 1:
        return
    _zero_hops_warning_emitted = True
    logger.warning(
        "forwarded_chain_deeper_than_trusted_proxy_hops",
        trusted_proxy_hops=0,
        forwarded_entries=chain_length,
        hint=(
            "Either a proxy TRUSTED_PROXY_HOPS does not count, or a caller sent X-Forwarded-For itself "
            "(then 0 is correct). Raise TRUSTED_PROXY_HOPS to the number of proxies after the first only "
            "if more than one proxy really sits in front; set too high, every IP-based control becomes forgeable."
        ),
    )


def resolve_client_ip(request: Request) -> str | None:
    """Return the originating client IP, honouring the configured proxy depth.

    Falls back to the socket peer whenever the header cannot answer: absent,
    empty, or shorter than the configured chain. That last case is deliberate —
    a header with fewer entries than expected means the request did not arrive
    the way the deployment is configured for, and reading it anyway would mean
    trusting a value no proxy of ours is known to have written. The peer is the
    one address nobody can fake.

    ``None`` means the peer could not be read either — no header *or* a header
    this configuration cannot interpret, and no ``request.client``. It is
    emphatically **not** "no forwarded header was sent": a header shorter than
    the configured depth also lands here. A caller reading ``None`` may conclude
    only "no address could be established", which is why
    ``McpAuthenticator._enforce_ip_allowlist`` fails closed on it.
    """
    peer = request.client.host if request.client else None

    forwarded_for = request.headers.get("x-forwarded-for")
    if not forwarded_for:
        return peer

    chain = [entry.strip() for entry in forwarded_for.split(",")]
    chain = [entry for entry in chain if entry]

    # `hops` entries were appended *after* the caller's, so the caller sits that
    # far in from the right. A chain too short for the configured depth is not
    # evidence about anyone.
    hops = settings.trusted_proxy_hops
    if hops == 0:
        _warn_once_on_unexplained_chain(len(chain))
    index = len(chain) - 1 - hops
    if index < 0:
        return peer
    return chain[index]
