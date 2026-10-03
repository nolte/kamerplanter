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
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from urllib.parse import unquote_plus, urlsplit

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
            logger.warning("server_side_url_rejected_ssrf", host=host, address=address.compressed, field=field)
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


#: Hosts that name this machine — the only ``http`` an OIDC endpoint may have, and
#: only while the application runs in ``settings.debug`` (#1987).
_LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


def https_endpoint_problem(url: object) -> str | None:
    """Why *url* is not an acceptable OIDC endpoint, or ``None`` when it is (#1987).

    A **pure predicate** — no DNS, no log — shared by the request schemas (which turn
    the answer into a 422) and by the login (which refuses to dial the URL). The rule is
    the scheme: an OIDC endpoint carries the discovery document, the authorization code
    and the client secret, or the signing keys, and over ``http`` whoever sits on the
    path answers it. ``http`` to a loopback host is accepted only when
    ``settings.debug`` is on — the existing development switch, not a new one.

    The host check is on the parsed hostname, never a prefix: ``http://localhost.evil``
    is not loopback.
    """
    if not isinstance(url, str) or not url or len(url) > _MAX_ENDPOINT_LENGTH:
        return "must be a non-empty URL of at most 2048 characters"
    try:
        parts = urlsplit(url)
        host = parts.hostname
        parts.port  # noqa: B018 — raises ValueError for a port outside 0-65535, which httpx would raise later
    except ValueError:
        return "is not a valid URL"
    if not host:
        return "has no host"
    if parts.username is not None or parts.password is not None:
        return "must not carry credentials"
    if parts.scheme == "https":
        return None
    if parts.scheme == "http" and settings.debug and host.lower() in _LOOPBACK_HOSTS:
        return None
    return "must use https"


def _unwrap_embedded_ipv4(address: ipaddress._BaseAddress) -> ipaddress._BaseAddress:
    """The IPv4 address an IPv6 one carries (mapped, NAT64, 6to4), else *address* itself."""
    if isinstance(address, ipaddress.IPv6Address):
        if address.ipv4_mapped is not None:
            return address.ipv4_mapped
        if address in _NAT64_PREFIX:
            return ipaddress.IPv4Address(int(address) & 0xFFFFFFFF)
        if address in _SIXTOFOUR_PREFIX:
            return ipaddress.IPv4Address((int(address) >> 80) & 0xFFFFFFFF)
    return address


def validate_oidc_fetch_url(
    url: str, *, field: str = "url", trusted_host: str | None = None, allow_private: bool = False
) -> str:
    """Validate a URL the server is about to fetch for an OIDC provider (#1987).

    The scheme rule of :func:`https_endpoint_problem`, plus the address rule of the
    other server-side validators here: a host that resolves to a link-local /
    cloud-metadata / reserved / multicast / unspecified address is **always** refused
    (:func:`_is_metadata_or_link_local` plus the extra metadata addresses of the Apprise
    validator, an IPv4 address carried in IPv6 judged as itself — never opt-in-able). A private
    or loopback address is refused too unless one of three things holds:

    * ``allow_private`` — the URL was typed by the platform admin behind a step-up
      (an explicitly configured ``jwks_url``), which is the same trust the admin already
      has over ``issuer_url``;
    * *trusted_host* — the host the provider itself is configured at (the name is compared; the
      address is not pinned, so a name that changes its answer between this check and the
      connection is the residual DNS-rebinding risk every validator in this module has — TLS
      with a valid certificate for that name is what bounds it). A self-hosted IdP
      on the LAN publishes a key set on its own host, and that is the one case where the
      provider-supplied ``jwks_uri`` of a discovery document is allowed a private address;
      a key endpoint on *another* private host is exactly the SSRF this exists to stop;
    * ``settings.debug`` — development against a local provider.

    Raises:
        ValidationError: not acceptable; the ``code`` in the details says which rule.
    """
    problem = https_endpoint_problem(url)
    if problem is not None:
        raise ValidationError(
            f"{field} {problem}.",
            details=[{"field": field, "reason": f"The URL {problem}.", "code": "INVALID_URL_SCHEME"}],
        )
    host = urlsplit(url).hostname or ""
    try:
        addresses = _resolved_addresses(host)
    except OSError:
        raise ValidationError(
            f"{field} host could not be resolved.",
            details=[{"field": field, "reason": "Host does not resolve.", "code": "URL_UNRESOLVABLE"}],
        ) from None
    private_ok = allow_private or settings.debug or (trusted_host is not None and host.lower() == trusted_host.lower())
    for resolved in addresses:
        # Judged by the IPv4 address an IPv6 one carries (mapped, NAT64, 6to4), and against the
        # metadata addresses the stdlib files under "private" or "global" (Alibaba's
        # 100.100.100.200, AWS IMDS over IPv6 fd00:ec2::254) — the Apprise validator's list, so the
        # two cannot drift (#1987 security review).
        address = _unwrap_embedded_ipv4(resolved)
        # ``::1`` is "reserved" to the stdlib as well as loopback; loopback is the opt-in's to give.
        always_blocked = (not address.is_loopback and _is_metadata_or_link_local(address)) or any(
            address in network for network in _APPRISE_EXTRA_BLOCKED_NETWORKS
        )
        internal = _is_blocked_address(address) or not address.is_global
        if always_blocked or (internal and not private_ok):
            logger.warning("oidc_url_rejected_ssrf", host=host, address=resolved.compressed, field=field)
            raise ValidationError(
                f"{field} resolves to a blocked address.",
                details=[
                    {
                        "field": field,
                        "reason": "Host resolves to an internal, link-local or reserved address.",
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
            logger.warning("storage_endpoint_rejected_ssrf", host=host, address=address.compressed, field=field)
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
            logger.warning("storage_endpoint_rejected_private", host=host, address=address.compressed, field=field)
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


def validate_ha_url(url: str, *, allow_private: bool = False, field: str = "ha_url") -> str:
    """Validate a tenant/admin-supplied Home Assistant base URL against SSRF (SEC-B3).

    The HA ``base_url`` is dialed server-side with the long-lived bearer token
    attached, so an attacker who can set it (admin, or a mis-scoped lower-privilege
    user) could otherwise point it at ``169.254.169.254`` or internal cluster
    addresses to leak the token and exfiltrate internal responses. Unlike
    :func:`validate_server_side_url` this is tailored to Home Assistant, which in
    many setups runs in the LAN over plain http:

    * ``http`` **and** ``https`` are accepted — LAN HA (``homeassistant.local``,
      ``192.168.x.x:8123``) legitimately speaks http.
    * Link-local / cloud-metadata / reserved / multicast / unspecified addresses
      (incl. ``169.254.169.254`` IMDS) are **always** rejected — never opt-in-able.
    * Private (RFC1918) and loopback addresses are rejected **unless**
      ``allow_private`` is set (operator opt-in via ``HA_ALLOW_PRIVATE_ENDPOINT``
      for LAN Home Assistant).

    Args:
        url: The HA base URL the server will dial.
        allow_private: When True, private / loopback addresses are permitted
            (still never link-local / metadata).
        field: Field name surfaced in the raised ``ValidationError`` details.

    Returns:
        The (unchanged) URL when it passes all checks.

    Raises:
        ValidationError: if the URL is empty/too long, not http(s), malformed,
            unresolvable, or resolves to a blocked address.
    """
    if not url or len(url) > _MAX_ENDPOINT_LENGTH:
        raise ValidationError(
            "Invalid Home Assistant URL.",
            details=[{"field": field, "reason": "URL is empty or too long.", "code": "INVALID_URL"}],
        )

    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        raise ValidationError(
            "Home Assistant URL must use http or https.",
            details=[{"field": field, "reason": "Only http(s) URLs are accepted.", "code": "INVALID_URL_SCHEME"}],
        )

    host = parts.hostname
    if not host:
        raise ValidationError(
            "Home Assistant URL has no host.",
            details=[{"field": field, "reason": "URL has no host.", "code": "INVALID_URL"}],
        )

    try:
        addresses = _resolved_addresses(host)
    except OSError:
        raise ValidationError(
            "Home Assistant URL host could not be resolved.",
            details=[{"field": field, "reason": "Host does not resolve.", "code": "URL_UNRESOLVABLE"}],
        ) from None

    for address in addresses:
        # Link-local / metadata / reserved / multicast / unspecified — ALWAYS blocked.
        if _is_metadata_or_link_local(address):
            logger.warning("ha_url_rejected_ssrf", host=host, address=address.compressed, field=field)
            raise ValidationError(
                "Home Assistant URL resolves to a blocked address.",
                details=[
                    {
                        "field": field,
                        "reason": "Host resolves to a link-local / metadata address.",
                        "code": "URL_METADATA_ADDRESS",
                    }
                ],
            )
        # Private / loopback — blocked unless the operator opted in.
        if _is_blocked_address(address) and not allow_private:
            logger.warning("ha_url_rejected_private", host=host, address=address.compressed, field=field)
            raise ValidationError(
                "Home Assistant URL resolves to a private address.",
                details=[
                    {
                        "field": field,
                        "reason": (
                            "Host resolves to a private/loopback IP. Set "
                            "HA_ALLOW_PRIVATE_ENDPOINT=true to allow LAN Home Assistant."
                        ),
                        "code": "URL_PRIVATE_ADDRESS",
                    }
                ],
            )

    return url


def validate_inventree_url(url: str, *, allow_private: bool = False, field: str = "base_url") -> str:
    """Validate a tenant/admin-supplied InvenTree base URL against SSRF (REQ-016 IT).

    The InvenTree ``base_url`` is dialed server-side with the API token attached,
    so an actor who can set it could otherwise point it at ``169.254.169.254`` or
    internal cluster addresses to leak the token or exfiltrate internal responses.
    Tailored to InvenTree, which frequently runs on the LAN / in-cluster over
    plain http:

    * ``http`` **and** ``https`` are accepted — LAN InvenTree
      (``inventree.local``, ``10.x.x.x``) legitimately speaks http.
    * Link-local / cloud-metadata / reserved / multicast / unspecified addresses
      (incl. ``169.254.169.254`` IMDS) are **always** rejected — never opt-in-able.
    * Private (RFC1918) and loopback addresses are rejected **unless**
      ``allow_private`` is set (operator opt-in via
      ``INVENTREE_ALLOW_PRIVATE_ENDPOINT`` for LAN / in-cluster InvenTree).

    Args:
        url: The InvenTree base URL the server will dial.
        allow_private: When True, private / loopback addresses are permitted
            (still never link-local / metadata).
        field: Field name surfaced in the raised ``ValidationError`` details.

    Returns:
        The (unchanged) URL when it passes all checks.

    Raises:
        ValidationError: if the URL is empty/too long, not http(s), malformed,
            unresolvable, or resolves to a blocked address.
    """
    if not url or len(url) > _MAX_ENDPOINT_LENGTH:
        raise ValidationError(
            "Invalid InvenTree URL.",
            details=[{"field": field, "reason": "URL is empty or too long.", "code": "INVALID_URL"}],
        )

    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        raise ValidationError(
            "InvenTree URL must use http or https.",
            details=[{"field": field, "reason": "Only http(s) URLs are accepted.", "code": "INVALID_URL_SCHEME"}],
        )

    host = parts.hostname
    if not host:
        raise ValidationError(
            "InvenTree URL has no host.",
            details=[{"field": field, "reason": "URL has no host.", "code": "INVALID_URL"}],
        )

    try:
        addresses = _resolved_addresses(host)
    except OSError:
        raise ValidationError(
            "InvenTree URL host could not be resolved.",
            details=[{"field": field, "reason": "Host does not resolve.", "code": "URL_UNRESOLVABLE"}],
        ) from None

    for address in addresses:
        # Link-local / metadata / reserved / multicast / unspecified — ALWAYS blocked.
        if _is_metadata_or_link_local(address):
            logger.warning("inventree_url_rejected_ssrf", host=host, address=address.compressed, field=field)
            raise ValidationError(
                "InvenTree URL resolves to a blocked address.",
                details=[
                    {
                        "field": field,
                        "reason": "Host resolves to a link-local / metadata address.",
                        "code": "URL_METADATA_ADDRESS",
                    }
                ],
            )
        # Private / loopback — blocked unless the operator opted in.
        if _is_blocked_address(address) and not allow_private:
            logger.warning("inventree_url_rejected_private", host=host, address=address.compressed, field=field)
            raise ValidationError(
                "InvenTree URL resolves to a private address.",
                details=[
                    {
                        "field": field,
                        "reason": (
                            "Host resolves to a private/loopback IP. Set "
                            "INVENTREE_ALLOW_PRIVATE_ENDPOINT=true to allow LAN / in-cluster InvenTree."
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
            logger.warning("pwa_endpoint_rejected_ssrf", host=host, address=address.compressed)
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


# ── Apprise notification URLs (#1947) ───────────────────────────────

#: The Apprise schemes a user may address, and nothing else. The documented chat
#: and push services only (``docs/*/user-guide/notifications.md``, REQ-030 §3.6):
#: Telegram, Slack, Discord, ntfy, Gotify, Pushover, Matrix. Apprise itself speaks
#: ~100 more, among them ``mailto://`` (mail through a server the user names),
#: ``json://`` / ``xml://`` / ``form://`` and plain ``http(s)://`` (an arbitrary
#: request, with title and body of the sender's choosing, from the operator's
#: backend). A positive list, so a scheme nobody thought of is refused too.
APPRISE_ALLOWED_SCHEMES: frozenset[str] = frozenset(
    {
        "tgram",
        "telegram",
        "slack",
        "discord",
        "ntfy",
        "ntfys",
        "gotify",
        "gotifys",
        "pover",
        "pushover",
        "matrix",
        "matrixs",
    }
)
#: At most this many URLs per channel and this many characters per URL.
APPRISE_MAX_URLS = 10
_APPRISE_MAX_URL_LENGTH = 512
#: Apprise splits one string on whitespace and commas into several URLs
#: (``tgram://a/b mailto://x`` is two), so a single list entry could carry a
#: second, un-vetted scheme. Control characters are refused with them.
_APPRISE_FORBIDDEN_CHARS = frozenset(",;[]")
#: Query parameters that change how Apprise talks to the target: connect/read
#: timeouts (a slow target would hold an executor thread) and TLS verification.
_APPRISE_FORBIDDEN_QUERY_KEYS = frozenset({"cto", "rto", "verify"})


#: Beyond the stdlib flags: the two metadata addresses the stdlib calls plain
#: private/global (Alibaba's ``100.100.100.200``, AWS IMDS over IPv6
#: ``fd00:ec2::254``) and the two IPv6 transition prefixes that embed an IPv4
#: address in a position this module does not unpack: local-use NAT64
#: ``64:ff9b:1::/48`` (RFC 8215) and Teredo ``2001::/32``.
_APPRISE_EXTRA_BLOCKED_NETWORKS = tuple(
    ipaddress.ip_network(n) for n in ("100.100.100.200/32", "fd00:ec2::/32", "64:ff9b:1::/48", "2001::/32")
)
#: ``0.0.0.0/8`` ("this network") — the stdlib files it under ``is_private``, so it
#: cannot be refused by flag with RFC1918 left allowed. Judged for *resolved*
#: addresses only: a literal host check also sees the leading digits of a
#: Telegram bot token (``tgram://123456:TOKEN/chat`` parses as the host ``123456``).
_THIS_NETWORK = ipaddress.ip_network("0.0.0.0/8")
_NAT64_PREFIX = ipaddress.ip_network("64:ff9b::/96")
_SIXTOFOUR_PREFIX = ipaddress.ip_network("2002::/16")

#: Seconds the whole resolution of one URL list may take (save and send alike).
#: A resolver that does not answer in time counts as a refusal (fail closed).
APPRISE_RESOLVE_TIMEOUT_SECONDS = 3.0
#: Schemes whose host part is a server the backend (through Apprise) connects to.
#: ``tgram``/``slack``/``discord``/``pover`` carry tokens there and talk to a fixed
#: vendor host; ``ntfy`` is host-addressed only when a topic path follows
#: (``ntfy://host/topic``; ``ntfy://topic`` is the public ntfy.sh).
_APPRISE_HOST_SCHEMES = frozenset({"gotify", "gotifys", "matrix", "matrixs"})
_APPRISE_NTFY_SCHEMES = frozenset({"ntfy", "ntfys"})
#: Schemes whose syntax has no use for ``#``; elsewhere it names a channel or room.
_APPRISE_NO_FRAGMENT_SCHEMES = frozenset({"gotify", "gotifys", "ntfy", "ntfys"})

#: Threads per resolver lane. A ``getaddrinfo`` against a nameserver that never
#: answers holds its thread for the system resolver's own timeout (10-30 s);
#: ``Future.cancel`` cannot stop it (#1995).
APPRISE_RESOLVER_WORKERS = 8
#: Resolutions one owner (the user whose URL list it is) may have running in one
#: lane at a time. A running resolution keeps its slot until its thread returns —
#: past the request's deadline — so never-answering names hold at most this many
#: threads per owner. Beyond it a host is refused at once (as a timeout), never
#: queued (#1995).
APPRISE_RESOLUTIONS_PER_OWNER = 3
#: Seconds a save-time resolver answer is reused by the next save: an address
#: list (``ok`` or ``blocked``), and a failure (NXDOMAIN, resolver error). A
#: *timeout* is never cached: it says nothing about the name. A stuck save-time
#: lookup that ends after the deadline caches what it ended with, under these TTLs.
#: The send path reads only a cached ``blocked`` verdict and writes nothing (see
#: :class:`_HostCache`).
APPRISE_RESOLVE_CACHE_TTL_SECONDS = 60.0
APPRISE_RESOLVE_NEGATIVE_CACHE_TTL_SECONDS = 10.0
#: Host names the cache holds at most; the oldest entry goes first.
APPRISE_RESOLVE_CACHE_MAX_ENTRIES = 1024


class _HostCache:
    """Recent save-time resolver answers per host name: address tuple, or ``None`` for a failure.

    Bounded, thread-safe, clock injectable. Only the **save** lane writes it and
    only the save lane takes every answer from it: a save is followed by no
    connect, so a reused answer opens no window there.

    The **send** lane takes from it a ``blocked`` verdict only — reusing that can
    only refuse — and resolves ``ok`` and every failure fresh, writing nothing
    back. A reused ``ok`` at send would leave the TTL between the check and
    Apprise's own resolution at connect: a host re-pointed to ``127.0.0.1`` after
    the save would pass (#1995 review F1). A reused failure would let a lookup
    that timed out (refused) and later ended with an error read as NXDOMAIN, which
    ``ntfy://topic`` tolerates.
    """

    def __init__(
        self,
        *,
        ttl: float = APPRISE_RESOLVE_CACHE_TTL_SECONDS,
        negative_ttl: float = APPRISE_RESOLVE_NEGATIVE_CACHE_TTL_SECONDS,
        max_entries: int = APPRISE_RESOLVE_CACHE_MAX_ENTRIES,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._ttl = ttl
        self._negative_ttl = negative_ttl
        self._max_entries = max_entries
        self._clock = clock
        self._lock = threading.Lock()
        self._entries: OrderedDict[str, tuple[float, tuple[str, ...] | None]] = OrderedDict()

    def lookup(self, host: str) -> tuple[bool, tuple[str, ...] | None]:
        """``(hit, addresses)``; ``addresses`` is ``None`` for a cached failure."""
        key = host.lower()
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return False, None
            expires, addresses = entry
            if self._clock() >= expires:
                del self._entries[key]
                return False, None
            return True, addresses

    def store(self, host: str, addresses: tuple[str, ...] | None) -> None:
        """Remember an answer (``None`` = the name failed to resolve)."""
        key = host.lower()
        ttl = self._ttl if addresses else self._negative_ttl
        with self._lock:
            self._entries.pop(key, None)
            self._entries[key] = (self._clock() + ttl, addresses or None)
            while len(self._entries) > self._max_entries:
                self._entries.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)


class _ResolverLane:
    """A resolver thread pool that never queues and caps each owner (#1995).

    At most ``workers`` resolutions run at once, so a submitted one always has a
    thread and never waits behind a stuck lookup; at most ``per_owner`` of them
    belong to one owner. A slot is held until the resolution *ends* (returns,
    raises or is cancelled), not until the caller stops waiting.
    """

    def __init__(
        self,
        name: str,
        *,
        workers: int = APPRISE_RESOLVER_WORKERS,
        per_owner: int = APPRISE_RESOLUTIONS_PER_OWNER,
        trusts_cache: bool,
    ) -> None:
        self.name = name
        #: Whether this lane reads every cached answer and writes its own (save),
        #: or reads only cached ``blocked`` verdicts and writes nothing (send).
        self.trusts_cache = trusts_cache
        self._workers = workers
        self._per_owner = per_owner
        self._pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix=f"apprise-dns-{name}")
        self._lock = threading.Lock()
        self._by_owner: dict[str, int] = {}
        self._running = 0

    def try_submit(self, owner_key: str, fn: Callable[[str], list[str]], host: str) -> Future[list[str]] | None:
        """Start ``fn(host)`` for ``owner_key``; ``None`` when the owner or the lane is full."""
        with self._lock:
            if self._running >= self._workers or self._by_owner.get(owner_key, 0) >= self._per_owner:
                return None
            self._by_owner[owner_key] = self._by_owner.get(owner_key, 0) + 1
            self._running += 1
        try:
            future = self._pool.submit(fn, host)
        except BaseException:
            self._release(owner_key)
            raise
        future.add_done_callback(lambda _done: self._release(owner_key))
        return future

    def outstanding(self, owner_key: str | None = None) -> int:
        """Resolutions still running — of ``owner_key``, or of the whole lane."""
        with self._lock:
            return self._running if owner_key is None else self._by_owner.get(owner_key, 0)

    def _release(self, owner_key: str) -> None:
        with self._lock:
            self._running -= 1
            left = self._by_owner.get(owner_key, 0) - 1
            if left > 0:
                self._by_owner[owner_key] = left
            else:
                self._by_owner.pop(owner_key, None)


_resolution_cache = _HostCache()
#: Save (a user's PUT) and send (delivery) resolve in separate lanes, so a burst
#: of saves cannot hold the threads delivery needs, nor the other way round.
_save_lane = _ResolverLane("save", trusts_cache=True)
_send_lane = _ResolverLane("send", trusts_cache=False)


def resolve_host_addresses(host: str) -> list[str]:
    """Resolve ``host`` to its address strings. The seam tests replace.

    Raises:
        OSError: the name does not resolve (NXDOMAIN, no A/AAAA record).
    """
    infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    return [str(info[4][0]) for info in infos]


def _apprise_literal_address(host: str) -> ipaddress._BaseAddress | None:
    """The address ``host`` spells, or ``None`` for a name.

    Also numeric spellings ``ip_address`` rejects but ``getaddrinfo`` resolves
    (``127.1``, ``0x7f.1``, ``2130706433``).
    """
    try:
        return ipaddress.ip_address(host)
    except ValueError:
        try:
            return ipaddress.ip_address(socket.inet_aton(host))
        except OSError, ValueError:
            return None


def _is_apprise_blocked_address(address: ipaddress._BaseAddress, *, resolved: bool = False) -> bool:
    """True for loopback / link-local / reserved / unspecified / multicast space.

    RFC1918 and unique-local stay allowed (REQ-030 §3.6: a LAN Gotify/ntfy is the
    documented use). IPv4 carried inside IPv6 (``::ffff:127.0.0.1``, NAT64,
    6to4) is judged by the IPv4 address it carries.
    """
    if isinstance(address, ipaddress.IPv6Address):
        if address.ipv4_mapped is not None:
            return _is_apprise_blocked_address(address.ipv4_mapped, resolved=resolved)
        if address in _NAT64_PREFIX:
            return _is_apprise_blocked_address(ipaddress.IPv4Address(int(address) & 0xFFFFFFFF), resolved=resolved)
        if address in _SIXTOFOUR_PREFIX:
            return _is_apprise_blocked_address(
                ipaddress.IPv4Address((int(address) >> 80) & 0xFFFFFFFF), resolved=resolved
            )
    return (
        (resolved and address.version == 4 and address in _THIS_NETWORK)
        or address.is_loopback
        or address.is_link_local
        or address.is_unspecified
        or address.is_reserved
        or address.is_multicast
        or any(address in net for net in _APPRISE_EXTRA_BLOCKED_NETWORKS if net.version == address.version)
    )


def _apprise_host_to_resolve(url: str) -> tuple[str, bool] | None:
    """``(host, unresolvable_ok)`` Apprise may connect to by name for ``url``, else ``None``.

    ``unresolvable_ok`` marks ``ntfy://name`` without a topic path: Apprise reads
    that as a *topic* on the public ntfy.sh unless a query (``?to=``, ``?mode=``)
    makes it a host, so a name that does not resolve is tolerated there, while a
    name that resolves into blocked space is refused either way.
    """
    parts = urlsplit(url)
    scheme = parts.scheme.lower()
    host = (parts.hostname or "").rstrip(".")
    if not host or _apprise_literal_address(host) is not None or host.lower() == "localhost":
        return None  # a literal is judged by ``_apprise_url_refusal`` without DNS
    if scheme in _APPRISE_HOST_SCHEMES:
        return host, False
    if scheme in _APPRISE_NTFY_SCHEMES:
        return host, not parts.path.strip("/")
    return None


def _apprise_resolved_verdict(addresses: tuple[str, ...] | None) -> str:
    """``ok`` / ``blocked`` / ``unresolvable`` for a resolver answer (``None`` = failed)."""
    if not addresses:
        return "unresolvable"
    try:
        parsed = [ipaddress.ip_address(a.split("%", 1)[0]) for a in addresses]
    except ValueError:
        return "unresolvable"
    if any(_is_apprise_blocked_address(a, resolved=True) for a in parsed):
        return "blocked"
    return "ok"


def _apprise_answer(future: Future[list[str]]) -> tuple[str, ...] | None:
    """The address tuple a finished resolution returned; ``None`` when it raised."""
    try:
        return tuple(str(a) for a in future.result(timeout=0))
    except Exception:
        return None


def _apprise_cache_on_end(host: str) -> Callable[[Future[list[str]]], None]:
    """Done-callback: cache what a resolution ended with — also after the deadline."""

    def _store(future: Future[list[str]]) -> None:
        if not future.cancelled():
            _resolution_cache.store(host, _apprise_answer(future))

    return _store


def _apprise_resolve_hosts(hosts: list[str], *, owner_key: str, lane: _ResolverLane) -> dict[str, str]:
    """Host -> ``ok`` / ``blocked`` / ``unresolvable`` / ``timeout``, within one deadline.

    Cached answers first — every one on a lane that trusts the cache, only a
    ``blocked`` verdict otherwise (see :class:`_HostCache`). The rest runs in ``lane`` under ``owner_key``'s slots:
    when no slot is free and nothing of this call is running, the remaining hosts
    are refused at once; otherwise they take the slot the next finished lookup of
    this call frees, until the deadline.
    """
    verdict: dict[str, str] = {}
    pending: list[str] = []
    for host in hosts:
        hit, addresses = _resolution_cache.lookup(host)
        cached = _apprise_resolved_verdict(addresses) if hit else None
        if cached is not None and (lane.trusts_cache or cached == "blocked"):
            verdict[host] = cached
        else:
            pending.append(host)
    resolve: Callable[[str], list[str]] = resolve_host_addresses
    deadline = time.monotonic() + APPRISE_RESOLVE_TIMEOUT_SECONDS
    running: dict[Future[list[str]], str] = {}
    capped = 0
    while pending:
        while pending and (future := lane.try_submit(owner_key, resolve, pending[0])) is not None:
            if lane.trusts_cache:
                future.add_done_callback(_apprise_cache_on_end(pending[0]))
            running[future] = pending.pop(0)
        if not pending:
            break
        if not running:  # the owner's share (or the lane) is held by earlier calls
            capped = len(pending)
            break
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        done, _ = wait(running, timeout=remaining, return_when=FIRST_COMPLETED)
        if not done:
            break
        for future in done:
            verdict[running.pop(future)] = _apprise_resolved_verdict(_apprise_answer(future))
    if running:
        finished, _ = wait(running, timeout=max(0.0, deadline - time.monotonic()))
        for future, host in running.items():
            verdict[host] = _apprise_resolved_verdict(_apprise_answer(future)) if future in finished else "timeout"
    for host in pending:
        verdict[host] = "timeout"
    if capped:
        logger.warning("apprise_resolution_capped", lane=lane.name, refused_hosts=capped)
    return verdict


def _apprise_resolution_refusals(urls: list[str], *, owner_key: str, lane: _ResolverLane) -> dict[int, str]:
    """Index -> reason for every URL whose host resolves to blocked space, or not at all.

    All distinct hosts are resolved concurrently under one shared deadline, so a
    list of ten slow names costs one timeout, not ten — within ``owner_key``'s
    share of ``lane`` (#1995). Fail closed: NXDOMAIN (except for a possible ntfy
    topic), a resolver error, a timeout and a host over the owner's share each
    refuse the URL; the last two read alike. A DNS-rebinding window remains
    between this check and the connect Apprise performs itself.
    """
    targets = {i: t for i, u in enumerate(urls) if (t := _apprise_host_to_resolve(u)) is not None}
    if not targets:
        return {}
    hosts = list(dict.fromkeys(host for host, _ in targets.values()))
    verdict = _apprise_resolve_hosts(hosts, owner_key=owner_key, lane=lane)
    reasons = {
        "blocked": "An Apprise URL host resolves to a loopback, link-local or reserved address.",
        "unresolvable": "An Apprise URL host could not be resolved.",
        "timeout": "An Apprise URL host did not resolve in time.",
    }
    refusals: dict[int, str] = {}
    for index, (host, unresolvable_ok) in targets.items():
        state = verdict[host]
        if state == "ok" or (state == "unresolvable" and unresolvable_ok):
            continue
        refusals[index] = reasons[state]
    return refusals


def _apprise_url_refusal(url: object) -> str | None:
    """Why ``url`` may not be handed to Apprise; ``None`` when it may.

    The reason names the rule, never the value: a URL carries its credential in
    the path (``tgram://<bot-token>/<chat>``) and must not travel into an error
    body or a log line (#1879, #1930).
    """
    if not isinstance(url, str) or not url.strip():
        return "Each Apprise URL must be a non-empty string."
    if len(url) > _APPRISE_MAX_URL_LENGTH:
        return "An Apprise URL is too long."
    # Printable ASCII only, and no whitespace of any kind: Apprise splits a string
    # with a Unicode-aware ``\\s`` (NEL, NBSP, U+2028 ...), so an ASCII-only
    # blacklist let ``tgram://a/b<NBSP>json://internal/x`` through.
    if not url.isascii() or not url.isprintable() or any(ch.isspace() or ch in _APPRISE_FORBIDDEN_CHARS for ch in url):
        return "An Apprise URL must contain only printable ASCII without whitespace, commas or brackets."
    scheme, separator, rest = url.partition("://")
    scheme = scheme.lower()
    if not separator or scheme not in APPRISE_ALLOWED_SCHEMES:
        return "An Apprise URL uses a scheme that is not allowed."
    # Spellings ``urlsplit`` and Apprise's own parser read differently, so the host
    # judged here is not the host dialled: a second ``@`` in the userinfo
    # (``a@127.0.0.1@public.example``), a backslash, and a ``#`` that Apprise does not
    # treat as a fragment (it hides ``?verify=no`` from the query check).
    authority = rest.split("/", 1)[0].split("?", 1)[0]
    if authority.count("@") > 1 or "\\" in url:
        return "An Apprise URL is malformed."
    fragment_start = url.find("#")
    if fragment_start != -1 and (
        scheme in _APPRISE_NO_FRAGMENT_SCHEMES or "?" in url[fragment_start:]
    ):  # ``slack://.../#channel`` and ``matrix://.../#room`` stay valid
        return "An Apprise URL is malformed."
    try:
        parts = urlsplit(url)
        host = (parts.hostname or "").rstrip(".")
        query_keys = {unquote_plus(pair.split("=", 1)[0]).lower() for pair in parts.query.split("&") if pair}
    except ValueError:
        return "An Apprise URL is malformed."
    if query_keys & _APPRISE_FORBIDDEN_QUERY_KEYS:
        return "An Apprise URL must not set timeouts or TLS verification."
    # ``ntfy://1234`` is a topic, ``ntfy://0.1.2.3/topic`` a host: only the latter is dialled.
    host_addressed = scheme in _APPRISE_HOST_SCHEMES or (
        scheme in _APPRISE_NTFY_SCHEMES and bool(parts.path.strip("/"))
    )
    if not host and scheme in _APPRISE_HOST_SCHEMES:
        return "An Apprise URL is malformed."
    if host:
        address = _apprise_literal_address(host)
        if host.lower().rstrip(".") == "localhost" or (
            address is not None and _is_apprise_blocked_address(address, resolved=host_addressed)
        ):
            return "An Apprise URL points at a loopback, link-local or reserved address."
    return None


def partition_apprise_urls(urls: object, *, owner_key: str) -> tuple[list[str], int]:
    """Split a stored ``urls`` value into ``(allowed, refused_count)``.

    Never raises: the send path uses it so a legacy row that predates the
    allow-list neither delivers to a refused target nor aborts the rest. Blocking
    (it resolves host targets, bounded by :data:`APPRISE_RESOLVE_TIMEOUT_SECONDS`);
    async callers run it in an executor. ``owner_key`` (the recipient's user key)
    picks the share of the send lane the resolution may use (#1995).
    """
    if not isinstance(urls, list):
        return [], 1 if urls else 0
    literal_ok = [u for u in urls[:APPRISE_MAX_URLS] if _apprise_url_refusal(u) is None]
    refused_by_dns = _apprise_resolution_refusals(literal_ok, owner_key=owner_key, lane=_send_lane)
    allowed = [u for i, u in enumerate(literal_ok) if i not in refused_by_dns]
    return allowed, len(urls) - len(allowed)


def validate_apprise_urls(urls: object, *, owner_key: str) -> list[str]:
    """Validate the ``urls`` of an Apprise channel preference on save.

    ``owner_key`` (the saving user's key) picks the share of the save lane the
    host resolution may use (#1995); it never reaches a log line.

    Raises:
        ValidationError: a value-free message when the list is not a list of at
            most :data:`APPRISE_MAX_URLS` strings, or an entry is outside the
            scheme allow-list, carries a second URL, or addresses loopback /
            link-local / reserved space, or a host name of a host-addressed
            scheme resolves to such space (or not at all, or not in time).
            Private (RFC1918) hosts stay allowed: a self-hosted Gotify or ntfy
            on the LAN is the documented use.
    """
    if not isinstance(urls, list) or len(urls) > APPRISE_MAX_URLS:
        raise ValidationError(
            f"Apprise URLs must be a list of at most {APPRISE_MAX_URLS} entries.",
            details=[
                {
                    "field": "channels.apprise.config.urls",
                    "reason": "Not a list or too long.",
                    "code": "INVALID_APPRISE_URLS",
                }
            ],
        )
    for index, url in enumerate(urls):
        reason = _apprise_url_refusal(url)
        if reason is not None:
            logger.warning("apprise_url_rejected", index=index, reason=reason)
            raise ValidationError(
                "An Apprise URL is not allowed.",
                details=[
                    {
                        "field": f"channels.apprise.config.urls[{index}]",
                        "reason": reason,
                        "code": "APPRISE_URL_NOT_ALLOWED",
                    }
                ],
            )
    for index, reason in sorted(_apprise_resolution_refusals(urls, owner_key=owner_key, lane=_save_lane).items()):
        logger.warning("apprise_url_rejected", index=index, reason=reason)
        raise ValidationError(
            "An Apprise URL is not allowed.",
            details=[
                {
                    "field": f"channels.apprise.config.urls[{index}]",
                    "reason": reason,
                    "code": "APPRISE_URL_NOT_ALLOWED",
                }
            ],
        )
    return urls
