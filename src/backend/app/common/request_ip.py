"""Resolve the originating client IP behind the reverse proxy.

The backend runs behind a trusted reverse proxy (Traefik ingress), so
``request.client.host`` is the proxy's address, not the real caller. When the
proxy sets ``X-Forwarded-For`` we take the **left-most** entry (the original
client) so IP-based controls — e.g. the service-account ``ip_allowlist`` the MCP
authenticator enforces (SEC-004) — evaluate the actual caller, falling back to
the direct peer address when no forwarded header is present.
"""

from __future__ import annotations

from fastapi import Request


def resolve_client_ip(request: Request) -> str | None:
    """Return the originating client IP, honouring the trusted proxy header."""

    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # "client, proxy1, proxy2" — the first hop is the original client.
        first = forwarded_for.split(",")[0].strip()
        if first:
            return first
    return request.client.host if request.client else None
