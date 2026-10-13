"""No credential carried in a URL *path* reaches a log line (#1879).

The redaction of #1795/#1796 masks URL userinfo, query strings and fragments.
Some services put the credential in the path instead: Telegram
(``/bot<id>:<token>/sendMessage``), Discord (``/api/webhooks/<id>/<token>``),
Slack (``/services/T…/B…/<token>``), a Web Push endpoint (the path is the
device's push token). Measured on the tree before the fix, through a real
``requests`` session over real urllib3 against a closed local port (no network):

* urllib3 logs ``Retrying (…) after connection broken by '…': /bot<id>:<token>/sendMessage``
  on ``urllib3.connectionpool`` at WARNING — above the WARNING floor
  ``setup_logging`` sets, and ``_UrlRedactionFilter`` left the path alone;
* the ``ConnectionError`` text is ``… Max retries exceeded with url:
  /bot<id>:<token>/sendMessage``, which ``loggable_error`` and the redacted
  traceback of ``exc_info=True`` kept — the two things the Apprise channel's
  ``except`` block logs.

Both processes (API, Celery worker) are configured the way they configure
themselves, and the assertion is on what a handler writes.

**What this does not measure:** the real ``apprise`` package is not a declared
dependency of the backend (the channel imports it lazily and reports "not
installed" otherwise), so the channel is driven with a stand-in module whose
``notify`` performs the real ``requests`` call. Real Apprise catches the
``requests`` exception itself and logs on its own ``apprise`` logger; that line
goes through the same record factory, which the stdlib case below exercises.
"""

from __future__ import annotations

import asyncio
import logging
import socket
import types
from collections.abc import Callable

import pytest
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.common.log_privacy import loggable_error, loggable_text, loggable_url_text
from app.data_access.external import apprise_notification_channel
from app.data_access.external.apprise_notification_channel import AppriseNotificationChannel
from app.domain.models.notification import Notification
from tests.unit.guards.test_logs_carry_no_secrets_runtime import (  # noqa: F401  (fixture, used via usefixtures)
    PROCESSES,
    _configure,
    isolated_logging,
)

pytestmark = pytest.mark.usefixtures("isolated_logging")

# Assembled at run time: a literal shaped like a credential is reported by the
# repository's secret scanner (BACKEND.md §16.3). None has ever authenticated anything.
_SECRET = "AAH" + "k9Zq" * 8
TELEGRAM_PATH = f"/bot{'1879' * 2}:{_SECRET}/sendMessage"
DISCORD_PATH = f"/api/webhooks/{'1879' * 4}/{_SECRET}-{_SECRET}"
SLACK_PATH = f"/services/T{'1879' * 2}/B{'1879' * 2}/{_SECRET[:24]}"
PUSH_PATH = f"/fcm/send/{_SECRET}:APA91b{_SECRET}"
CREDENTIAL_PATHS = {"telegram": TELEGRAM_PATH, "discord": DISCORD_PATH, "slack": SLACK_PATH, "push": PUSH_PATH}


def _closed_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _post(path: str) -> None:
    """A real ``requests`` POST with one retry to a port nothing listens on."""
    session = requests.Session()
    session.mount("http://", HTTPAdapter(max_retries=Retry(total=1, backoff_factor=0)))
    try:
        session.post(f"http://127.0.0.1:{_closed_port()}{path}", json={"text": "x"}, timeout=5)
    finally:
        session.close()


def _assert_no_credential(lines: list[str]) -> None:
    assert lines, "nothing was logged — the probe did not drive the path it claims to"
    leaked = [line for line in lines if _SECRET[:24] in line]
    assert not leaked, "a URL-path credential reached the log:\n  " + "\n  ".join(leaked)


@pytest.mark.parametrize("shape", sorted(CREDENTIAL_PATHS))
@pytest.mark.parametrize("process", sorted(PROCESSES))
def test_urllib3_retry_warning_names_no_path_credential(process: str, shape: str) -> None:
    capture = _configure(process)

    with pytest.raises(requests.ConnectionError):
        _post(CREDENTIAL_PATHS[shape])

    retry_lines = [line for line in capture.lines if "Retrying" in line]
    assert retry_lines, capture.lines
    _assert_no_credential(capture.lines)


@pytest.mark.parametrize("shape", sorted(CREDENTIAL_PATHS))
@pytest.mark.parametrize("process", sorted(PROCESSES))
def test_a_logged_connection_error_names_no_path_credential(process: str, shape: str) -> None:
    capture = _configure(process)

    try:
        _post(CREDENTIAL_PATHS[shape])
    except requests.ConnectionError as exc:
        assert _SECRET[:24] in str(exc), "the probe exception does not carry the credential it should"
        logging.getLogger("apprise").warning("Socket Exception: %s", exc)
        logging.getLogger("somelib").exception("send failed")

    assert any("Socket Exception" in line for line in capture.lines), capture.lines
    _assert_no_credential(capture.lines)


def _fake_apprise(send: Callable[[], None]) -> types.ModuleType:
    module = types.ModuleType("apprise")

    class NotifyType:
        INFO = "info"
        WARNING = "warning"
        FAILURE = "failure"
        SUCCESS = "success"

    class Apprise:
        def add(self, _url: str, tag: object = None) -> bool:
            return True

        def notify(self, **_kwargs: object) -> bool:
            send()
            return True

    module.NotifyType = NotifyType  # type: ignore[attr-defined]
    module.Apprise = Apprise  # type: ignore[attr-defined]
    return module


@pytest.mark.parametrize("process", sorted(PROCESSES))
def test_the_apprise_channel_logs_a_failed_send_without_the_bot_token(
    process: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    capture = _configure(process)
    monkeypatch.setattr(
        apprise_notification_channel, "_import_apprise", lambda: _fake_apprise(lambda: _post(TELEGRAM_PATH))
    )
    notification = Notification(user_key="u-1879", notification_type="care.watering", title="t", body="b")

    result = asyncio.run(
        AppriseNotificationChannel().send(notification, {"urls": [f"tgram://{'1879' * 2}:{_SECRET}/42"]})
    )

    assert result.success is False
    assert any("apprise_notification_failed" in line for line in capture.lines), capture.lines
    _assert_no_credential(capture.lines)
    assert _SECRET[:24] not in (result.error or ""), result.error


@pytest.mark.parametrize("shape", sorted(CREDENTIAL_PATHS))
@pytest.mark.parametrize("redact", [loggable_error, loggable_text, loggable_url_text])
def test_every_text_redaction_masks_the_path_credential(redact: Callable[[str], str], shape: str) -> None:
    path = CREDENTIAL_PATHS[shape]
    for text in (
        f"HTTPSConnectionPool(host='api.example.org', port=443): Max retries exceeded with url: {path} (Caused by x)",
        f"POST https://api.example.org{path} failed",
        f'"POST {path} HTTP/1.1" 502',
        f"Retrying (Retry(total=0)) after connection broken by 'NewConnectionError()': {path}",
    ):
        assert _SECRET[:24] not in redact(text), redact(text)


def test_the_masking_keeps_what_an_operator_needs() -> None:
    text = f"POST https://api.telegram.org{TELEGRAM_PATH} failed"

    masked = loggable_error(text)

    assert "https://api.telegram.org/bot" in masked and masked.endswith("/sendMessage failed"), masked


@pytest.mark.parametrize(
    "text",
    [
        'File "/app/app/migrations/versions/v0056_backfill_user_key_on_three_models.py", line 12, in upgrade',
        "GET /api/v1/t/{}/plant-instances/{} 200",
        "http://arangodb:8529/_db/kamerplanter/_api/document/users/1234567",
        "migration v0020_backfill_watering_log_tenant_key applied in /app/app/migrations/versions",
    ],
)
def test_ordinary_paths_are_left_alone(text: str) -> None:
    assert loggable_text(text) == text
