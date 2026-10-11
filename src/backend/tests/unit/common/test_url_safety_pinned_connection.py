"""#2249 — the address a request is sent to is the address the SSRF rule judged.

Every validator in ``app.common.url_safety`` resolves the host and judges the
answer; the HTTP client then resolves the name again when it connects. A name
whose answer changes in between (DNS rebinding: public to the check, private to
the connect) used to pass the check and be dialed at an address nobody judged —
measured against develop: ``validate_inventree_url`` passed on 93.184.216.34 and
``httpx`` then sent the request to a listener on 127.0.0.1.

These tests run real sockets against a listener on 127.0.0.1 and replace only the
resolver (``socket.getaddrinfo``, the one both the validator and the HTTP stack
use), so they exercise the production connection path, not a mock of it:

* a rebound answer is refused at connect time — the listener receives nothing;
* the connect-time answer is judged whole (mixed public/private is refused) by
  the same rule as the validator, for IPv4 and IPv6 private/loopback/link-local
  addresses and IPv4 carried in IPv6;
* a legitimate target still works: the request keeps its ``Host`` header, the
  bearer token, and over TLS its SNI name and certificate check.

Not testable in-process: a real authoritative nameserver with TTL 0 (the
resolver seam stands in for it), and a public address actually answering (only
loopback listeners exist here, so "accepted" paths use the private opt-in).
"""

from __future__ import annotations

import datetime
import http.server
import ipaddress
import os
import socket
import ssl
import threading
import time
from collections.abc import Iterator
from pathlib import Path

import anyio
import httpcore
import httpx
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

import app.api.v1.admin.settings.router as settings_router
import app.common.url_safety as url_safety
from app.common.url_safety import (
    PinnedConnectRefusedError,
    ha_address_policy,
    inventree_address_policy,
    pinned_async_transport,
    pinned_transport,
    validate_ha_url,
    validate_inventree_url,
)
from app.data_access.external.ha_client import HomeAssistantClient
from app.data_access.external.inventree_adapter import InvenTreeRestAdapter

PUBLIC = "93.184.216.34"
TEST_DOMAIN = ".kamerplanter.test"
_real_getaddrinfo = socket.getaddrinfo


class _Listener:
    """A threaded HTTP(S) listener on 127.0.0.1 that records what reaches it."""

    def __init__(self, ssl_context: ssl.SSLContext | None = None) -> None:
        self.hits: list[dict[str, str | None]] = []
        self.sni: list[str | None] = []
        listener = self

        class _Handler(http.server.BaseHTTPRequestHandler):
            def _handle(self) -> None:
                length = int(self.headers.get("content-length") or 0)
                if length:
                    self.rfile.read(length)
                listener.hits.append(
                    {
                        "method": self.command,
                        "path": self.path,
                        "host": self.headers.get("Host"),
                        "authorization": self.headers.get("Authorization"),
                    }
                )
                body = b'{"state": "21.5", "attributes": {}, "message": "API running."}'
                self.send_response(200)
                self.send_header("content-type", "application/json")
                self.send_header("content-length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            do_GET = _handle  # noqa: N815 — BaseHTTPRequestHandler dispatches on do_<METHOD>
            do_POST = _handle  # noqa: N815 — BaseHTTPRequestHandler dispatches on do_<METHOD>

            def log_message(self, *args: object) -> None:
                return

        self._server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        if ssl_context is not None:

            def _record_sni(_sock: ssl.SSLSocket, name: str | None, _ctx: ssl.SSLContext) -> None:
                listener.sni.append(name)

            ssl_context.sni_callback = _record_sni
            self._server.socket = ssl_context.wrap_socket(self._server.socket, server_side=True)
        self.port = self._server.server_address[1]
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def close(self) -> None:
        self._server.shutdown()
        self._server.server_close()


class _Resolver:
    """Answers for ``*.kamerplanter.test`` in sequence; every other name resolves for real.

    The last answer of a sequence repeats. ``calls`` counts lookups per name.
    """

    def __init__(self) -> None:
        self.answers: dict[str, list[list[str]]] = {}
        self.calls: dict[str, int] = {}

    def set(self, host: str, *answers: list[str]) -> None:
        self.answers[host] = list(answers)
        self.calls[host] = 0

    def __call__(self, host: object, port: object, *args: object, **kwargs: object) -> list:
        # anyio hands the name over IDNA-encoded (bytes); the stdlib and httpcore's sync path as str.
        if isinstance(host, bytes):
            host = host.decode("ascii")
        if isinstance(host, str) and host.endswith(TEST_DOMAIN):
            sequence = self.answers.get(host)
            if not sequence:
                raise socket.gaierror(socket.EAI_NONAME, "Name or service not known")
            index = min(self.calls[host], len(sequence) - 1)
            self.calls[host] += 1
            port_number = int(port) if isinstance(port, int | str) and str(port).isdigit() else 0
            result = []
            for address in sequence[index]:
                if ipaddress.ip_address(address).version == 6:
                    result.append((socket.AF_INET6, socket.SOCK_STREAM, 6, "", (address, port_number, 0, 0)))
                else:
                    result.append((socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, port_number)))
            return result
        return _real_getaddrinfo(host, port, *args, **kwargs)  # type: ignore[arg-type]


@pytest.fixture
def resolver(monkeypatch: pytest.MonkeyPatch) -> _Resolver:
    fake = _Resolver()
    monkeypatch.setattr(socket, "getaddrinfo", fake)
    return fake


@pytest.fixture
def listener() -> Iterator[_Listener]:
    server = _Listener()
    yield server
    server.close()


@pytest.fixture
def tcp_connects(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Every address the sync and async httpcore backends open a TCP connection to."""
    opened: list[str] = []
    sync_connect = httpcore.SyncBackend.connect_tcp
    async_connect = httpcore.AnyIOBackend.connect_tcp

    def _sync(self: httpcore.SyncBackend, host: str, port: int, *args: object, **kwargs: object):  # noqa: ANN202
        opened.append(host)
        return sync_connect(self, host, port, *args, **kwargs)  # type: ignore[arg-type]

    async def _async(self: httpcore.AnyIOBackend, host: str, port: int, *args: object, **kwargs: object):  # noqa: ANN202
        opened.append(host)
        return await async_connect(self, host, port, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(httpcore.SyncBackend, "connect_tcp", _sync)
    monkeypatch.setattr(httpcore.AnyIOBackend, "connect_tcp", _async)
    return opened


def _refused_by_pin(exc: BaseException) -> bool:
    """True if *exc* (an ``httpx.ConnectError``) came from the connect-time SSRF rule."""
    cause: BaseException | None = exc
    while cause is not None:
        if isinstance(cause, PinnedConnectRefusedError):
            return True
        cause = cause.__cause__ or cause.__context__
    return False


# ── DNS rebinding: public to the check, private to the connect ──────────────


class TestReboundAnswerIsRefusedAtConnect:
    def test_ha_client_sync_read_never_reaches_the_rebound_address(self, resolver, listener) -> None:
        host = "ha-rebind.kamerplanter.test"
        resolver.set(host, [PUBLIC], ["127.0.0.1"])
        client = HomeAssistantClient(f"http://{host}:{listener.port}", "llat-secret", timeout=5)

        with pytest.raises(httpx.ConnectError) as caught:
            client.get_state("sensor.tank_ec")

        assert _refused_by_pin(caught.value)
        assert listener.hits == [], "the bearer token reached an address the SSRF rule never judged"

    @pytest.mark.asyncio
    async def test_ha_client_async_call_never_reaches_the_rebound_address(self, resolver, listener) -> None:
        host = "ha-rebind-async.kamerplanter.test"
        resolver.set(host, [PUBLIC], ["127.0.0.1"])
        client = HomeAssistantClient(f"http://{host}:{listener.port}", "llat-secret", timeout=5)

        with pytest.raises(httpx.ConnectError) as caught:
            await client.fire_event("kamerplanter_care", {"plant": "tomato"})

        assert _refused_by_pin(caught.value)
        assert listener.hits == []

    @pytest.mark.asyncio
    async def test_inventree_adapter_never_reaches_the_rebound_address(self, resolver, listener) -> None:
        """The tenant-supplied URL: re-validated before every request, and still rebindable without the pin."""
        host = "inventree-rebind.kamerplanter.test"
        # Construction-free check, the adapter's per-request guard, then the connection.
        resolver.set(host, [PUBLIC], [PUBLIC], ["127.0.0.1"])
        url = f"http://{host}:{listener.port}"
        validate_inventree_url(url, allow_private=False)
        adapter = InvenTreeRestAdapter(url, "inventree-token", allow_private=False)

        with pytest.raises(httpx.ConnectError) as caught:
            await adapter.get_part(42)

        assert _refused_by_pin(caught.value)
        assert listener.hits == []

    def test_admin_ha_probe_never_reaches_the_rebound_address(self, monkeypatch, resolver, listener) -> None:
        monkeypatch.setattr(settings_router.settings, "ha_allow_private_endpoint", False)
        host = "ha-probe-rebind.kamerplanter.test"
        resolver.set(host, [PUBLIC], ["127.0.0.1"])
        url = f"http://{host}:{listener.port}"
        validate_ha_url(url, allow_private=False)

        with pytest.raises(httpx.ConnectError) as caught:
            settings_router._ha_get(f"{url}/api/", headers={"Authorization": "Bearer llat"}, timeout=5)

        assert _refused_by_pin(caught.value)
        assert listener.hits == []


# ── The connect-time answer is judged whole, by the validator's rule ────────


BLOCKED_WITHOUT_OPT_IN = [
    "127.0.0.1",
    "10.0.0.5",
    "172.16.4.4",
    "192.168.1.50",
    "169.254.169.254",
    "0.0.0.0",
    "::1",
    "fe80::1",
    "fc00::5",
    "::ffff:127.0.0.1",
    "::ffff:169.254.169.254",
    # Not global, not "private" to the stdlib: CGNAT (pod networks in some clusters) and
    # deprecated IPv6 site-local — the opt-in class, as in the OIDC rule (review SEC-001).
    "100.64.0.1",
    "fec0::1",
    # IPv4 carried in 6to4 / NAT64, judged as the IPv4 address it carries (review SEC-004).
    "2002:c0a8:0101::",
    "64:ff9b::a00:5",
]


class TestConnectTimeAnswerIsJudged:
    @pytest.mark.parametrize("address", BLOCKED_WITHOUT_OPT_IN)
    def test_private_loopback_and_link_local_answers_open_no_socket(self, resolver, tcp_connects, address) -> None:
        host = "judged.kamerplanter.test"
        resolver.set(host, [address])
        transport = pinned_transport(ha_address_policy(allow_private=False))

        with httpx.Client(transport=transport, timeout=5) as client, pytest.raises(httpx.ConnectError) as caught:
            client.get(f"http://{host}:8123/api/")

        assert _refused_by_pin(caught.value)
        assert tcp_connects == []

    @pytest.mark.asyncio
    @pytest.mark.parametrize("address", BLOCKED_WITHOUT_OPT_IN)
    async def test_async_transport_judges_the_same_answers(self, resolver, tcp_connects, address) -> None:
        host = "judged-async.kamerplanter.test"
        resolver.set(host, [address])
        transport = pinned_async_transport(inventree_address_policy(allow_private=False))

        async with httpx.AsyncClient(transport=transport, timeout=5) as client:
            with pytest.raises(httpx.ConnectError) as caught:
                await client.get(f"http://{host}:8000/api/")

        assert _refused_by_pin(caught.value)
        assert tcp_connects == []

    def test_mixed_public_and_private_answer_is_refused_whole(self, resolver, tcp_connects) -> None:
        """Not "the public half": the validators refuse a mixed answer, so the connection does too."""
        host = "mixed.kamerplanter.test"
        resolver.set(host, [PUBLIC, "127.0.0.1"])
        transport = pinned_transport(ha_address_policy(allow_private=False))

        with httpx.Client(transport=transport, timeout=5) as client, pytest.raises(httpx.ConnectError) as caught:
            client.get(f"http://{host}:8123/api/")

        assert _refused_by_pin(caught.value)
        assert tcp_connects == []

    @pytest.mark.parametrize(
        "address",
        [
            "169.254.169.254",
            "fe80::1",
            "::ffff:169.254.169.254",
            "224.0.0.1",
            # 6to4 / NAT64 carrying 169.254.169.254 — metadata, never opt-in-able (review SEC-004).
            "2002:a9fe:a9fe::",
            "64:ff9b::a9fe:a9fe",
            # AWS IMDS over IPv6 and Alibaba's metadata address (the OIDC rule's extra list).
            "fd00:ec2::254",
            "100.100.100.200",
        ],
    )
    def test_metadata_and_link_local_stay_refused_with_the_private_opt_in(self, resolver, tcp_connects, address):
        host = "metadata.kamerplanter.test"
        resolver.set(host, [address])
        transport = pinned_transport(ha_address_policy(allow_private=True))

        with httpx.Client(transport=transport, timeout=5) as client, pytest.raises(httpx.ConnectError) as caught:
            client.get(f"http://{host}/latest/meta-data/")

        assert _refused_by_pin(caught.value)
        assert tcp_connects == []

    def test_literal_private_address_in_the_url_is_judged_too(self, tcp_connects) -> None:
        transport = pinned_transport(ha_address_policy(allow_private=False))

        with httpx.Client(transport=transport, timeout=5) as client, pytest.raises(httpx.ConnectError) as caught:
            client.get("http://127.0.0.1:9/api/")

        assert _refused_by_pin(caught.value)
        assert tcp_connects == []

    def test_unresolvable_name_is_a_connect_error(self, resolver, tcp_connects) -> None:
        transport = pinned_transport(ha_address_policy(allow_private=True))

        with httpx.Client(transport=transport, timeout=5) as client, pytest.raises(httpx.ConnectError):
            client.get("http://nxdomain.kamerplanter.test/api/")

        assert tcp_connects == []


# ── Legitimate targets keep working ─────────────────────────────────────────


class TestAcceptedTargetsKeepTheirName:
    def test_ha_client_with_lan_opt_in_reaches_the_judged_address(self, resolver, listener, tcp_connects) -> None:
        host = "ha-lan.kamerplanter.test"
        resolver.set(host, ["127.0.0.1"])
        client = HomeAssistantClient(f"http://{host}:{listener.port}", "llat-secret", timeout=5, allow_private=True)

        state = client.get_state("sensor.tank_ec")

        assert state is not None
        assert state["value"] == 21.5
        assert tcp_connects == ["127.0.0.1"], "the connection must go to the address that was judged"
        assert listener.hits == [
            {
                "method": "GET",
                "path": "/api/states/sensor.tank_ec",
                "host": f"{host}:{listener.port}",
                "authorization": "Bearer llat-secret",
            }
        ]

    @pytest.mark.asyncio
    async def test_inventree_adapter_with_opt_in_reaches_the_judged_address(self, resolver, listener) -> None:
        host = "inventree-lan.kamerplanter.test"
        resolver.set(host, ["127.0.0.1"])
        adapter = InvenTreeRestAdapter(f"http://{host}:{listener.port}", "inventree-token", allow_private=True)

        assert await adapter.health_check() is True

        assert listener.hits[0]["host"] == f"{host}:{listener.port}"
        assert listener.hits[0]["authorization"] == "Token inventree-token"

    def test_the_name_is_resolved_once_per_connection(self, resolver, listener) -> None:
        """Pinning means one lookup feeds both the judgement and the connect."""
        host = "once.kamerplanter.test"
        resolver.set(host, ["127.0.0.1"])
        transport = pinned_transport(ha_address_policy(allow_private=True))

        with httpx.Client(transport=transport, timeout=5) as client:
            assert client.get(f"http://{host}:{listener.port}/api/").status_code == 200

        assert resolver.calls[host] == 1


# ── TLS: SNI and certificate verification stay on the host name ─────────────


def _ca_and_leaf(tmp_path: Path, leaf_name: str) -> tuple[ssl.SSLContext, ssl.SSLContext]:
    """A throwaway CA, a leaf certificate for *leaf_name*; (server context, client context)."""
    now = datetime.datetime.now(datetime.UTC)
    ca_key = ec.generate_private_key(ec.SECP256R1())
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "kamerplanter test CA")])
    ca_cert = (
        x509.CertificateBuilder()
        .subject_name(ca_name)
        .issuer_name(ca_name)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(minutes=5))
        .not_valid_after(now + datetime.timedelta(hours=1))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(x509.SubjectKeyIdentifier.from_public_key(ca_key.public_key()), critical=False)
        .sign(ca_key, hashes.SHA256())
    )
    leaf_key = ec.generate_private_key(ec.SECP256R1())
    leaf_cert = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, leaf_name)]))
        .issuer_name(ca_name)
        .public_key(leaf_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(minutes=5))
        .not_valid_after(now + datetime.timedelta(hours=1))
        .add_extension(x509.SubjectAlternativeName([x509.DNSName(leaf_name)]), critical=False)
        .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()), critical=False)
        .add_extension(x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
        .sign(ca_key, hashes.SHA256())
    )
    cert_file = tmp_path / "leaf.pem"
    key_file = tmp_path / "leaf.key"
    cert_file.write_bytes(leaf_cert.public_bytes(serialization.Encoding.PEM))
    key_file.write_bytes(
        leaf_key.private_bytes(
            serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
        )
    )
    server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    server_context.load_cert_chain(cert_file, key_file)
    client_context = ssl.create_default_context(cadata=ca_cert.public_bytes(serialization.Encoding.PEM).decode())
    return server_context, client_context


class TestTlsVerifiesTheName:
    def test_sni_and_certificate_are_the_host_name_not_the_pinned_address(self, tmp_path, resolver) -> None:
        host = "tls.kamerplanter.test"
        server_context, client_context = _ca_and_leaf(tmp_path, host)
        server = _Listener(server_context)
        try:
            resolver.set(host, ["127.0.0.1"])
            transport = pinned_transport(ha_address_policy(allow_private=True), verify=client_context)
            with httpx.Client(transport=transport, timeout=5) as client:
                response = client.get(f"https://{host}:{server.port}/api/")
        finally:
            server.close()

        assert response.status_code == 200
        assert server.sni == [host]
        assert server.hits[0]["host"] == f"{host}:{server.port}"

    def test_a_certificate_for_another_name_is_refused(self, tmp_path, resolver) -> None:
        """Verification is against the URL's name — a pinned IP does not relax it."""
        host = "tls-mismatch.kamerplanter.test"
        server_context, client_context = _ca_and_leaf(tmp_path, "someone-else.kamerplanter.test")
        server = _Listener(server_context)
        try:
            resolver.set(host, ["127.0.0.1"])
            transport = pinned_transport(ha_address_policy(allow_private=True), verify=client_context)
            with httpx.Client(transport=transport, timeout=5) as client, pytest.raises(httpx.ConnectError) as caught:
                client.get(f"https://{host}:{server.port}/api/")
        finally:
            server.close()

        assert "Hostname mismatch" in str(caught.value), str(caught.value)
        assert server.hits == []


# ── Review follow-ups (#2249 SEC-003, SEC-005) ──────────────────────────────


class TestAddressFallbackAndTimeouts:
    def test_a_refused_first_address_falls_back_to_the_next_judged_one(self, resolver, listener, tcp_connects):
        """127.0.0.2 has no listener on this port (the listener binds 127.0.0.1 only)."""
        host = "fallback.kamerplanter.test"
        resolver.set(host, ["127.0.0.2", "127.0.0.1"])
        transport = pinned_transport(ha_address_policy(allow_private=True))

        with httpx.Client(transport=transport, timeout=5) as client:
            assert client.get(f"http://{host}:{listener.port}/api/").status_code == 200

        assert tcp_connects == ["127.0.0.2", "127.0.0.1"]
        assert len(listener.hits) == 1

    @pytest.mark.asyncio
    async def test_async_fallback_across_judged_addresses(self, resolver, listener, tcp_connects):
        host = "fallback-async.kamerplanter.test"
        resolver.set(host, ["127.0.0.2", "127.0.0.1"])
        transport = pinned_async_transport(inventree_address_policy(allow_private=True))

        async with httpx.AsyncClient(transport=transport, timeout=5) as client:
            assert (await client.get(f"http://{host}:{listener.port}/api/")).status_code == 200

        assert tcp_connects == ["127.0.0.2", "127.0.0.1"]

    def test_a_connect_timeout_does_not_fall_through_to_the_next_address(self, monkeypatch, resolver):
        """A timeout already spent the caller's connect budget; trying the next address would double it."""
        attempts: list[str] = []

        def _timeout(self, host, port, *args, **kwargs):  # noqa: ANN001, ANN202, ARG001
            attempts.append(host)
            raise httpcore.ConnectTimeout("timed out")

        monkeypatch.setattr(httpcore.SyncBackend, "connect_tcp", _timeout)
        host = "slow.kamerplanter.test"
        resolver.set(host, ["127.0.0.2", "127.0.0.1"])
        transport = pinned_transport(ha_address_policy(allow_private=True))

        with httpx.Client(transport=transport, timeout=5) as client, pytest.raises(httpx.ConnectTimeout):
            client.get(f"http://{host}:8123/api/")

        assert attempts == ["127.0.0.2"]


class TestConnectTimeResolutionIsBounded:
    @pytest.mark.asyncio
    async def test_a_hanging_resolver_times_out_without_borrowing_the_shared_thread_limiter(self, monkeypatch):
        release = threading.Event()

        def _hang(host: str) -> list:
            release.wait(10)
            raise OSError("released")

        monkeypatch.setattr(url_safety, "_resolved_addresses", _hang)
        transport = pinned_async_transport(ha_address_policy(allow_private=True))
        try:
            started = time.monotonic()
            async with httpx.AsyncClient(transport=transport, timeout=0.3) as client:
                with pytest.raises(httpx.ConnectTimeout):
                    await client.get("http://hang.kamerplanter.test/api/")
            elapsed = time.monotonic() - started

            assert elapsed < 3, f"the lookup was not bounded by the connect timeout ({elapsed:.1f} s)"
            assert anyio.to_thread.current_default_thread_limiter().borrowed_tokens == 0
        finally:
            release.set()

    @pytest.mark.asyncio
    async def test_a_full_lane_refuses_instead_of_queueing(self, monkeypatch):
        lane = url_safety._ResolverLane("test-connect", workers=1, per_owner=1, trusts_cache=False)
        monkeypatch.setattr(url_safety, "_connect_lane", lane)
        release = threading.Event()

        def _hang(host: str) -> list:
            release.wait(10)
            raise OSError("released")

        monkeypatch.setattr(url_safety, "_resolved_addresses", _hang)
        transport = pinned_async_transport(ha_address_policy(allow_private=True))
        try:
            async with httpx.AsyncClient(transport=transport, timeout=0.3) as client:
                with pytest.raises(httpx.ConnectTimeout):
                    await client.get("http://hang-a.kamerplanter.test/api/")
                # The first lookup still holds the only thread: the next is refused at once.
                started = time.monotonic()
                with pytest.raises(httpx.ConnectError) as caught:
                    await client.get("http://hang-b.kamerplanter.test/api/")

            assert "resolver busy" in str(caught.value)
            assert time.monotonic() - started < 0.3
        finally:
            release.set()


class TestTransportSettingsCannotBypassThePin:
    @pytest.mark.asyncio
    async def test_inventree_verify_ssl_false_still_goes_through_the_pin(self, tmp_path, resolver):
        host = "inventree-selfsigned.kamerplanter.test"
        server_context, _client_context = _ca_and_leaf(tmp_path, host)
        server = _Listener(server_context)
        try:
            resolver.set(host, ["127.0.0.1"])
            url = f"https://{host}:{server.port}"
            unverified = InvenTreeRestAdapter(url, "tok", allow_private=True, verify_ssl=False)
            verified = InvenTreeRestAdapter(url, "tok", allow_private=True, verify_ssl=True)

            assert await unverified.health_check() is True
            assert await verified.health_check() is False, "an unknown CA must fail when verification is on"

            # And with verification off, the connect-time rule still applies.
            resolver.set(host, [PUBLIC], [PUBLIC], ["127.0.0.1"])
            blocked = InvenTreeRestAdapter(url, "tok", allow_private=False, verify_ssl=False)
            hits_before = len(server.hits)
            assert await blocked.health_check() is False
            assert len(server.hits) == hits_before
        finally:
            server.close()

    def test_proxy_environment_does_not_bypass_the_pin(self, monkeypatch, resolver, listener):
        """A proxy would resolve the name itself; with the pinned transport the env proxy is not used."""
        proxy = _Listener()
        try:
            for name in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
                monkeypatch.setenv(name, f"http://127.0.0.1:{proxy.port}")
            monkeypatch.delenv("NO_PROXY", raising=False)
            monkeypatch.delenv("no_proxy", raising=False)
            assert os.environ["HTTP_PROXY"].endswith(str(proxy.port))

            host = "ha-proxy.kamerplanter.test"
            resolver.set(host, [PUBLIC], ["127.0.0.1"])
            client = HomeAssistantClient(f"http://{host}:{listener.port}", "llat-secret", timeout=5)
            with pytest.raises(httpx.ConnectError) as caught:
                client.get_state("sensor.tank_ec")

            assert _refused_by_pin(caught.value)
            assert proxy.hits == [], "the request went to the environment proxy, around the pin"
            assert listener.hits == []
        finally:
            proxy.close()
