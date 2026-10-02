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
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
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
_resolver_pool = ThreadPoolExecutor(max_workers=8, thread_name_prefix="apprise-dns")


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


def _apprise_resolution_refusals(urls: list[str]) -> dict[int, str]:
    """Index -> reason for every URL whose host resolves to blocked space, or not at all.

    All distinct hosts are resolved concurrently under one shared deadline, so a
    list of ten slow names costs one timeout, not ten. Fail closed: NXDOMAIN
    (except for a possible ntfy topic), a resolver error and a timeout each refuse
    the URL. A DNS-rebinding window remains between this check and the connect
    Apprise performs itself.
    """
    targets = {i: t for i, u in enumerate(urls) if (t := _apprise_host_to_resolve(u)) is not None}
    if not targets:
        return {}
    resolve: Callable[[str], list[str]] = resolve_host_addresses
    futures = {h: _resolver_pool.submit(resolve, h) for h in {host for host, _ in targets.values()}}
    verdict: dict[str, str] = {}  # host -> "ok" | "blocked" | "unresolvable" | "timeout"
    started = time.monotonic()
    for host, future in futures.items():
        remaining = max(0.0, APPRISE_RESOLVE_TIMEOUT_SECONDS - (time.monotonic() - started))
        try:
            addresses = future.result(timeout=remaining)
        except FutureTimeoutError:
            future.cancel()
            verdict[host] = "timeout"
            continue
        except Exception:
            verdict[host] = "unresolvable"
            continue
        try:
            parsed = [ipaddress.ip_address(a.split("%", 1)[0]) for a in addresses]
        except ValueError:
            verdict[host] = "unresolvable"
            continue
        if not parsed:
            verdict[host] = "unresolvable"
        elif any(_is_apprise_blocked_address(a, resolved=True) for a in parsed):
            verdict[host] = "blocked"
        else:
            verdict[host] = "ok"
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


def partition_apprise_urls(urls: object) -> tuple[list[str], int]:
    """Split a stored ``urls`` value into ``(allowed, refused_count)``.

    Never raises: the send path uses it so a legacy row that predates the
    allow-list neither delivers to a refused target nor aborts the rest. Blocking
    (it resolves host targets, bounded by :data:`APPRISE_RESOLVE_TIMEOUT_SECONDS`);
    async callers run it in an executor.
    """
    if not isinstance(urls, list):
        return [], 1 if urls else 0
    literal_ok = [u for u in urls[:APPRISE_MAX_URLS] if _apprise_url_refusal(u) is None]
    refused_by_dns = _apprise_resolution_refusals(literal_ok)
    allowed = [u for i, u in enumerate(literal_ok) if i not in refused_by_dns]
    return allowed, len(urls) - len(allowed)


def validate_apprise_urls(urls: object) -> list[str]:
    """Validate the ``urls`` of an Apprise channel preference on save.

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
    for index, reason in sorted(_apprise_resolution_refusals(urls).items()):
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
