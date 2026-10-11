"""#2249 — a Web Push delivery never follows a redirect to a target nobody validated.

The subscriber supplies the push endpoint; it is validated (https, public address)
at subscribe time and again before every send. pywebpush then POSTs through
``requests``, which follows a 3xx to any ``Location`` — measured against develop:
an endpoint answering ``307 Location: http://127.0.0.1:<port>/internal`` had the
encrypted POST delivered to that loopback listener.

Real pywebpush and real sockets here; only the endpoint check is opened up for the
loopback listener (it would refuse ``http://127.0.0.1``, which is the point of it,
and is covered by its own tests). Both listeners are loopback because nothing else
exists in-process; "the Location target" stands for any internal address.
"""

from __future__ import annotations

import base64
import http.server
import os
import threading
from collections.abc import Iterator
from unittest.mock import patch

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from app.data_access.external.pwa_notification_channel import PwaNotificationChannel
from app.domain.models.notification import Notification, NotificationUrgency


class _Listener:
    """Loopback HTTP listener; answers ``status`` (with ``location`` for a 3xx) and records hits."""

    def __init__(self, status: int, location: str | None = None) -> None:
        self.hits: list[tuple[str, str]] = []
        listener = self

        class _Handler(http.server.BaseHTTPRequestHandler):
            def _handle(self) -> None:
                length = int(self.headers.get("content-length") or 0)
                if length:
                    self.rfile.read(length)
                listener.hits.append((self.command, self.path))
                self.send_response(status)
                if location is not None:
                    self.send_header("Location", location)
                self.send_header("content-length", "0")
                self.end_headers()

            do_GET = _handle  # noqa: N815 — BaseHTTPRequestHandler dispatches on do_<METHOD>
            do_POST = _handle  # noqa: N815 — BaseHTTPRequestHandler dispatches on do_<METHOD>

            def log_message(self, *args: object) -> None:
                return

        self._server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self.port = self._server.server_address[1]
        threading.Thread(target=self._server.serve_forever, daemon=True).start()

    def close(self) -> None:
        self._server.shutdown()
        self._server.server_close()


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _subscription(endpoint: str) -> dict[str, str]:
    """A subscription whose keys pywebpush can really encrypt to."""
    client_key = ec.generate_private_key(ec.SECP256R1())
    p256dh = client_key.public_key().public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
    )
    return {"endpoint": endpoint, "p256dh": _b64(p256dh), "auth": _b64(os.urandom(16))}


def _vapid_private_key() -> str:
    """The base64url raw private scalar — the form ``py_vapid.Vapid.from_string`` reads."""
    key = ec.generate_private_key(ec.SECP256R1())
    return _b64(key.private_numbers().private_value.to_bytes(32, "big"))


def _notification() -> Notification:
    return Notification(
        _key="notif_redirect",
        tenant_key="t1",
        user_key="u1",
        notification_type="care_watering",
        title="Water your plants",
        body="Tomato needs watering",
        urgency=NotificationUrgency.NORMAL,
        group_key="care:u1:watering",
    )


@pytest.fixture
def internal() -> Iterator[_Listener]:
    server = _Listener(201)
    yield server
    server.close()


@pytest.fixture(autouse=True)
def _endpoint_check_admits_the_loopback_listener() -> Iterator[None]:
    with patch("app.data_access.external.pwa_notification_channel.is_safe_push_endpoint", return_value=True):
        yield


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
async def test_redirect_target_is_never_dialed(internal: _Listener, status: int) -> None:
    endpoint_server = _Listener(status, location=f"http://127.0.0.1:{internal.port}/internal")
    try:
        channel = PwaNotificationChannel(_vapid_private_key(), "ops@kamerplanter.example")
        result = await channel.send(
            _notification(),
            {"subscriptions": [_subscription(f"http://127.0.0.1:{endpoint_server.port}/push/abc")]},
        )
    finally:
        endpoint_server.close()

    assert endpoint_server.hits == [("POST", "/push/abc")]
    assert internal.hits == [], f"a {status} from the push endpoint was followed to an unvalidated target"
    assert result.success is False
    assert f"WebPushException {status}" in (result.error or "")


@pytest.mark.asyncio
async def test_a_push_service_that_accepts_is_still_delivered_to() -> None:
    """The control: the no-redirect session does not break a normal 201 delivery."""
    push_service = _Listener(201)
    try:
        channel = PwaNotificationChannel(_vapid_private_key(), "ops@kamerplanter.example")
        result = await channel.send(
            _notification(),
            {"subscriptions": [_subscription(f"http://127.0.0.1:{push_service.port}/push/abc")]},
        )
    finally:
        push_service.close()

    assert push_service.hits == [("POST", "/push/abc")]
    assert result.success is True
