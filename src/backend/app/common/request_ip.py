"""Resolve the originating client IP behind the reverse proxies.

The backend never sees the caller's socket: a Traefik ingress and the frontend's
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
of reach, whether or not the outermost proxy sanitises inbound headers.

This matters beyond tidiness: the device-pairing lockout (#1118) and the
service-account ``ip_allowlist`` (SEC-004) both key on this value. A caller who
can choose it can walk around the lockout and can claim an allowlisted address.
"""

from __future__ import annotations

from fastapi import Request

from app.config.settings import settings


def resolve_client_ip(request: Request) -> str | None:
    """Return the originating client IP, honouring the configured proxy depth.

    Falls back to the socket peer whenever the header cannot answer: absent,
    empty, or shorter than the configured chain. That last case is deliberate —
    a header with fewer entries than expected means the request did not arrive
    the way the deployment is configured for, and reading it anyway would mean
    trusting a value no proxy of ours is known to have written. The peer is the
    one address nobody can fake.

    ``None`` only when there is no header *and* no peer, which is a "nothing to
    report" that callers keep distinct from an address.
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
    index = len(chain) - 1 - settings.trusted_proxy_hops
    if index < 0:
        return peer
    return chain[index]
