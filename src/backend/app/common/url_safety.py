"""SSRF-hardening helpers for user-supplied URLs that are dialed server-side.

The Web Push (PWA) channel POSTs encrypted payloads to a push ``endpoint`` that
the *client* supplies at subscription time. Without validation an attacker could
register an endpoint pointing at an internal address (cloud metadata service,
loopback, RFC1918) and have the server make a request to it on every push —
a classic Server-Side Request Forgery (SSRF) vector.

``validate_push_endpoint`` enforces:

* an ``https://`` scheme (``http``/``file``/anything else is rejected),
* that *every* address the host resolves to is a public, routable IP — any
  private, loopback, link-local, reserved, multicast or unspecified address
  causes rejection (blocks ``169.254.169.254``, ``127.0.0.0/8``, RFC1918,
  ``::1``, ``fc00::/7`` …),
* an optional operator allowlist (host-suffix match) via settings.

The helper is reused both when a subscription is stored (raising
:class:`~app.common.exceptions.ValidationError`) and defensively at send time
(returning a boolean so the caller can skip + log invalid stored endpoints).
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlsplit

import structlog

from app.common.exceptions import ValidationError
from app.config.settings import settings

logger = structlog.get_logger(__name__)

# Maximum accepted endpoint length (mirrors the schema bound) — a cheap guard
# against absurdly long hostnames before any DNS resolution is attempted.
_MAX_ENDPOINT_LENGTH = 2048


def _resolved_addresses(host: str) -> list[ipaddress._BaseAddress]:
    """Resolve ``host`` to every A/AAAA address as ``ipaddress`` objects.

    Raises:
        OSError: if the hostname cannot be resolved.
    """
    infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    addresses: list[ipaddress._BaseAddress] = []
    for info in infos:
        sockaddr = info[4]
        ip_str = sockaddr[0]
        # IPv6 scoped addresses (fe80::1%eth0) — strip the zone id before parsing.
        ip_str = ip_str.split("%", 1)[0]
        addresses.append(ipaddress.ip_address(ip_str))
    return addresses


def _is_blocked_address(address: ipaddress._BaseAddress) -> bool:
    """True if ``address`` is in a non-routable / internal range."""
    return (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_reserved
        or address.is_multicast
        or address.is_unspecified
    )


def _allowed_hosts() -> list[str]:
    """Parse the operator allowlist from settings (comma-separated, lowercased)."""
    raw = settings.pwa_push_endpoint_allowed_hosts or ""
    return [h.strip().lower() for h in raw.split(",") if h.strip()]


def _host_matches_allowlist(host: str, allowed_hosts: list[str]) -> bool:
    """True if ``host`` equals or is a sub-domain of any allowlist entry."""
    host = host.lower()
    return any(host == entry or host.endswith(f".{entry}") for entry in allowed_hosts)


def is_safe_push_endpoint(endpoint: str) -> bool:
    """Return True if ``endpoint`` is a safe, dial-able Web Push endpoint.

    Pure predicate variant for the send loop — never raises, so a single bad
    stored subscription cannot abort a delivery batch. Resolution failures and
    malformed URLs are treated as unsafe.

    Args:
        endpoint: The push service endpoint URL to check.

    Returns:
        True if the endpoint is https and resolves only to public addresses
        (and, if an allowlist is configured, matches it); False otherwise.
    """
    try:
        validate_push_endpoint(endpoint)
    except ValidationError:
        return False
    return True


def validate_server_side_url(url: str, *, field: str = "url") -> str:
    """Validate any server-side-dialed URL against SSRF (generic variant).

    Enforces ``https`` and that every resolved address is public/routable —
    blocking loopback, RFC1918, link-local (incl. the cloud metadata endpoint
    ``169.254.169.254``), reserved, multicast and unspecified addresses. Unlike
    :func:`validate_push_endpoint` this carries no push-specific allowlist, so it
    suits internal integrations such as the virus-scan endpoint (SEC-006).

    Args:
        url: The URL the server will dial.
        field: Field name surfaced in the raised ``ValidationError`` details.

    Returns:
        The (unchanged) URL when it passes all checks.

    Raises:
        ValidationError: if the URL is empty/too long, not https, malformed,
            unresolvable, or resolves to an internal/non-routable address.
    """
    if not url or len(url) > _MAX_ENDPOINT_LENGTH:
        raise ValidationError(
            "Invalid URL.",
            details=[{"field": field, "reason": "URL is empty or too long.", "code": "INVALID_URL"}],
        )

    parts = urlsplit(url)
    if parts.scheme != "https":
        raise ValidationError(
            "URL must use https.",
            details=[{"field": field, "reason": "Only https URLs are accepted.", "code": "INVALID_URL_SCHEME"}],
        )

    host = parts.hostname
    if not host:
        raise ValidationError(
            "URL has no host.",
            details=[{"field": field, "reason": "URL has no host.", "code": "INVALID_URL"}],
        )

    try:
        addresses = _resolved_addresses(host)
    except OSError:
        raise ValidationError(
            "URL host could not be resolved.",
            details=[{"field": field, "reason": "Host does not resolve.", "code": "URL_UNRESOLVABLE"}],
        ) from None

    for address in addresses:
        if _is_blocked_address(address):
            logger.warning("server_side_url_rejected_ssrf", host=host, address=str(address), field=field)
            raise ValidationError(
                "URL resolves to a non-routable address.",
                details=[
                    {
                        "field": field,
                        "reason": "Host resolves to an internal or reserved IP range.",
                        "code": "URL_PRIVATE_ADDRESS",
                    }
                ],
            )

    return url


def _is_metadata_or_link_local(address: ipaddress._BaseAddress) -> bool:
    """True if ``address`` is link-local — covers the cloud metadata endpoint.

    ``169.254.169.254`` (and the IPv6 ``fe80::/10`` range, plus the AWS IMDS
    ``fd00:ec2::254`` reserved address) are all caught by ``is_link_local`` /
    ``is_reserved``; both are checked so metadata access can never be opted into.
    """
    return address.is_link_local or address.is_reserved or address.is_multicast or address.is_unspecified


def validate_storage_endpoint_url(url: str, *, field: str = "s3_endpoint_url", allow_private: bool = False) -> str:
    """Validate an admin-supplied S3 endpoint before the server probes it (SEC-002).

    The storage "test connection" probe dials a fully operator-controlled
    endpoint, so it must not become an SSRF primitive — especially in light mode
    where the anonymous system user is treated as the operator. Unlike
    :func:`validate_server_side_url` this is tailored to S3-compatible backends:

    * ``http`` **and** ``https`` are accepted — plain-HTTP MinIO / in-cluster S3
      is legitimate (the separate ``force_tls`` adapter guard governs TLS).
    * Link-local / cloud-metadata / reserved / multicast / unspecified addresses
      (incl. ``169.254.169.254`` IMDS) are **always** rejected — never opt-in-able.
    * Private (RFC1918) and loopback addresses are rejected **unless**
      ``allow_private`` is set (operator opt-in via
      ``STORAGE_S3_ALLOW_PRIVATE_ENDPOINT`` for in-cluster MinIO / localhost).

    Args:
        url: The S3 endpoint URL the server will dial.
        field: Field name surfaced in the raised ``ValidationError`` details.
        allow_private: When True, private / loopback addresses are permitted
            (still never link-local / metadata).

    Returns:
        The (unchanged) URL when it passes all checks.

    Raises:
        ValidationError: if the URL is empty/too long, not http(s), malformed,
            unresolvable, or resolves to a blocked address.
    """
    if not url or len(url) > _MAX_ENDPOINT_LENGTH:
        raise ValidationError(
            "Invalid storage endpoint URL.",
            details=[{"field": field, "reason": "URL is empty or too long.", "code": "INVALID_URL"}],
        )

    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        raise ValidationError(
            "Storage endpoint must use http or https.",
            details=[{"field": field, "reason": "Only http(s) URLs are accepted.", "code": "INVALID_URL_SCHEME"}],
        )

    host = parts.hostname
    if not host:
        raise ValidationError(
            "Storage endpoint has no host.",
            details=[{"field": field, "reason": "URL has no host.", "code": "INVALID_URL"}],
        )

    try:
        addresses = _resolved_addresses(host)
    except OSError:
        raise ValidationError(
            "Storage endpoint host could not be resolved.",
            details=[{"field": field, "reason": "Host does not resolve.", "code": "URL_UNRESOLVABLE"}],
        ) from None

    for address in addresses:
        # Link-local / metadata / reserved / multicast / unspecified — ALWAYS blocked.
        if _is_metadata_or_link_local(address):
            logger.warning("storage_endpoint_rejected_ssrf", host=host, address=str(address), field=field)
            raise ValidationError(
                "Storage endpoint resolves to a blocked address.",
                details=[
                    {
                        "field": field,
                        "reason": "Host resolves to a link-local / metadata address.",
                        "code": "URL_METADATA_ADDRESS",
                    }
                ],
            )
        # Private / loopback — blocked unless the operator opted in.
        if (address.is_private or address.is_loopback) and not allow_private:
            logger.warning("storage_endpoint_rejected_private", host=host, address=str(address), field=field)
            raise ValidationError(
                "Storage endpoint resolves to a private address.",
                details=[
                    {
                        "field": field,
                        "reason": (
                            "Host resolves to a private/loopback IP. Set "
                            "STORAGE_S3_ALLOW_PRIVATE_ENDPOINT=true to allow in-cluster/local S3."
                        ),
                        "code": "URL_PRIVATE_ADDRESS",
                    }
                ],
            )

    return url


def validate_push_endpoint(endpoint: str) -> str:
    """Validate a user-supplied Web Push endpoint against SSRF.

    Args:
        endpoint: The push service endpoint URL.

    Returns:
        The (unchanged) endpoint when it passes all checks.

    Raises:
        ValidationError: if the endpoint is not https, is malformed, cannot be
            resolved, resolves to an internal/non-routable address, or — when an
            allowlist is configured — does not match the allowlist.
    """
    if not endpoint or len(endpoint) > _MAX_ENDPOINT_LENGTH:
        raise ValidationError(
            "Invalid push endpoint URL.",
            details=[{"field": "endpoint", "reason": "Endpoint is empty or too long.", "code": "INVALID_ENDPOINT"}],
        )

    parts = urlsplit(endpoint)
    if parts.scheme != "https":
        raise ValidationError(
            "Push endpoint must use https.",
            details=[
                {"field": "endpoint", "reason": "Only https endpoints are accepted.", "code": "INVALID_ENDPOINT_SCHEME"}
            ],
        )

    host = parts.hostname
    if not host:
        raise ValidationError(
            "Push endpoint has no host.",
            details=[{"field": "endpoint", "reason": "Endpoint URL has no host.", "code": "INVALID_ENDPOINT"}],
        )

    allowed_hosts = _allowed_hosts()
    if allowed_hosts and not _host_matches_allowlist(host, allowed_hosts):
        raise ValidationError(
            "Push endpoint host is not allowed.",
            details=[
                {
                    "field": "endpoint",
                    "reason": "Host is not on the operator allowlist.",
                    "code": "ENDPOINT_NOT_ALLOWED",
                }
            ],
        )

    try:
        addresses = _resolved_addresses(host)
    except OSError:
        raise ValidationError(
            "Push endpoint host could not be resolved.",
            details=[{"field": "endpoint", "reason": "Host does not resolve.", "code": "ENDPOINT_UNRESOLVABLE"}],
        ) from None

    for address in addresses:
        if _is_blocked_address(address):
            logger.warning("pwa_endpoint_rejected_ssrf", host=host, address=str(address))
            raise ValidationError(
                "Push endpoint resolves to a non-routable address.",
                details=[
                    {
                        "field": "endpoint",
                        "reason": "Host resolves to an internal or reserved IP range.",
                        "code": "ENDPOINT_PRIVATE_ADDRESS",
                    }
                ],
            )

    return endpoint
