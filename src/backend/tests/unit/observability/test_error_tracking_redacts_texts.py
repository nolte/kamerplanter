"""The error-tracking event carries no unredacted exception text or log message (#1880).

``scrub_event`` scrubbed the event's *structure* — request, user, sensitive
names — and left its free text: ``exception.values[].value`` is ``str(exc)``
(``NotFoundError("User", <key>)`` names the account key, a connection error the
URL it dialled), ``logentry`` is a log record's format string and arguments, and
frame locals (``url``, ``html``, ``payload`` in the mail adapters) are values no
name-based rule can classify.

The measurement is a real subprocess: the API's process entry (``import
app.main`` with ``SENTRY_DSN`` set — so the real ``init_error_tracking`` call
with the real options and ``before_send`` hook), the real SDK, and a transport
stub that collects what would have been sent. No network: the DSN host is
``.invalid`` and the stub replaces the transport before anything is captured.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any

import pytest

from app.common.exceptions import NotFoundError
from app.common.log_privacy import redact_text_in_flight
from app.observability import error_tracking
from app.observability.error_tracking import scrub_breadcrumb, scrub_event
from tests.unit.guards.test_privacy_logs_carry_no_plaintext_subject import BACKEND_ROOT

# Assembled at run time: a literal shaped like a credential is reported by the
# repository's secret scanner (BACKEND.md §16.3).
SUBJECT_KEY = "-".join(("acct", "1880", "sentry"))
ADDRESS = "@".join(("mira-1880", "example.org"))
API_KEY = "-".join(("SECRET", "KEY", "1880"))
BOT_TOKEN = "AAH" + "k9Zq" * 8
RESET_LINK_TOKEN = "-".join(("reset", "link", "1880"))

_PROBE = r"""
import json, logging, os, sys
import app.main
import sentry_sdk
from app.common.exceptions import NotFoundError

events = []

class Stub(sentry_sdk.transport.Transport):
    def capture_envelope(self, envelope):
        for item in envelope.items:
            if item.headers.get("type") == "event":
                events.append(item.payload.json)

client = sentry_sdk.get_client()
assert client.is_active(), "the process entry did not enable error tracking"
client.transport = Stub(client.options)

subject, address, api_key = os.environ["PROBE_SUBJECT"], os.environ["PROBE_ADDRESS"], os.environ["PROBE_API_KEY"]
bot_path = "/bot18801880:" + os.environ["PROBE_BOT_TOKEN"] + "/sendMessage"

def send_mail(to_email, url, html, payload):
    raise NotFoundError("User", subject)

def lookup():
    try:
        raise ConnectionError("GET https://api.example.org/v1?appid=" + api_key + " and POST " + bot_path)
    except ConnectionError as cause:
        link = "https://app.example.org/password-reset/" + os.environ["PROBE_RESET"]
        headers = {"Authorization": "Bearer " + api_key}
        send_mail(address, link, "<a href='" + link + "'>reset</a>", {"headers": headers})

# 1. an exception captured directly
try:
    lookup()
except NotFoundError as exc:
    sentry_sdk.capture_exception(exc)
# 2. the same exception through a log record (LoggingIntegration)
try:
    lookup()
except NotFoundError:
    logging.getLogger("probe").exception("lookup failed")
# 3. a record without an exception whose ARGUMENTS carry the data
import httpx
with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200))) as http:
    http.get("https://api.openweathermap.org/data/2.5/forecast", params={"lat": "52.5", "appid": api_key})
bot_url = "https://api.telegram.org" + bot_path
sentry_sdk.add_breadcrumb(category="http", message="POST " + bot_url, data={"url": bot_url})
keyed_url = "https://api.example.org/v1?appid=" + api_key
logging.getLogger("probe").error("mail to %s failed at %s", address, keyed_url)
sentry_sdk.capture_message("no account for " + address)
sentry_sdk.flush()
print("EVENTS=" + json.dumps(events))
"""


@pytest.fixture(scope="module")
def captured() -> list[dict[str, Any]]:
    result = subprocess.run(
        [sys.executable, "-W", "ignore", "-c", _PROBE],
        cwd=BACKEND_ROOT,
        env={
            **os.environ,
            "PYTHONPATH": str(BACKEND_ROOT),
            "SENTRY_DSN": "https://public@tracker.invalid/1",
            "SENTRY_ENVIRONMENT": "e2e",
            "PROBE_SUBJECT": SUBJECT_KEY,
            "PROBE_ADDRESS": ADDRESS,
            "PROBE_API_KEY": API_KEY,
            "PROBE_BOT_TOKEN": BOT_TOKEN,
            "PROBE_RESET": RESET_LINK_TOKEN,
        },
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    lines = [line for line in result.stdout.splitlines() if line.startswith("EVENTS=")]
    assert lines, result.stdout + result.stderr
    events = json.loads(lines[-1].removeprefix("EVENTS="))
    assert len(events) == 4, [event.get("logentry") or event.get("message") for event in events]
    return events


@pytest.mark.parametrize("secret", [SUBJECT_KEY, ADDRESS, API_KEY, BOT_TOKEN, RESET_LINK_TOKEN])
def test_no_event_carries_the_probe_value(captured: list[dict[str, Any]], secret: str) -> None:
    for event in captured:
        text = json.dumps(event)
        position = text.find(secret)
        assert position < 0, f"{secret!r} left the process: …{text[max(0, position - 300) : position + 80]}…"


def test_the_events_keep_what_triage_needs(captured: list[dict[str, Any]]) -> None:
    direct, logged, record, message = captured

    for event in (direct, logged):
        values = event["exception"]["values"]
        assert [value["type"] for value in values] == ["ConnectionError", "NotFoundError"]
        assert values[1]["value"] == "[ENTITY_NOT_FOUND]"
        assert "https://api.example.org/v1?<redacted>" in values[0]["value"]
        assert "/bot<redacted>/sendMessage" in values[0]["value"]
        frames = values[1]["stacktrace"]["frames"]
        assert [frame["function"] for frame in frames][-2:] == ["lookup", "send_mail"]
        assert all("vars" not in frame for frame in frames)
    assert "mail to" in json.dumps(record["logentry"])
    assert "no account for <email:" in json.dumps(message)
    crumbs = [crumb for crumb in record["breadcrumbs"]["values"] if crumb.get("category") == "http"]
    assert crumbs and crumbs[0]["message"] == "POST https://api.telegram.org/bot<redacted>/sendMessage"


# ── the hook itself ───────────────────────────────────────────────────────────


@pytest.fixture
def backend_redactor(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(error_tracking, "_text_redactor", redact_text_in_flight)


@pytest.mark.usefixtures("backend_redactor")
def test_the_exception_text_is_replaced_for_the_hinted_exception() -> None:
    exc = NotFoundError("User", SUBJECT_KEY)
    event = {"exception": {"values": [{"type": "NotFoundError", "value": str(exc)}]}}

    scrubbed = scrub_event(event, {"exc_info": (type(exc), exc, None)})

    assert scrubbed["exception"]["values"][0]["value"] == "[ENTITY_NOT_FOUND]"


@pytest.mark.usefixtures("backend_redactor")
def test_logentry_message_params_and_formatted_are_redacted() -> None:
    event = {
        "logentry": {
            "message": "mail to %s failed (%s)",
            "params": [ADDRESS, {"url": f"https://api.example.org/v1?appid={API_KEY}"}],
            "formatted": f"mail to {ADDRESS} failed",
        }
    }

    text = json.dumps(scrub_event(event, None))

    assert ADDRESS not in text and API_KEY not in text, text
    assert "mail to %s failed (%s)" in text


@pytest.mark.usefixtures("backend_redactor")
def test_frame_locals_are_redacted_at_any_depth_when_an_event_carries_them() -> None:
    frame_vars = {
        "headers": {"Authorization": f"Bearer {API_KEY}", "Accept": "*/*"},
        "attempts": [{"password": "x", "url": f"https://api.example.org/v1?appid={API_KEY}"}],
        "html": f"'<a href=\"https://app.example.org/reset?token={RESET_LINK_TOKEN}\">{ADDRESS}</a>'",
    }
    event = {"exception": {"values": [{"stacktrace": {"frames": [{"vars": frame_vars}]}}]}}

    scrubbed = scrub_event(event, None)["exception"]["values"][0]["stacktrace"]["frames"][0]["vars"]

    assert scrubbed["headers"] == {"Authorization": "[redacted]", "Accept": "*/*"}
    assert scrubbed["attempts"][0]["password"] == "[redacted]"
    text = json.dumps(scrubbed)
    assert API_KEY not in text and RESET_LINK_TOKEN not in text and ADDRESS not in text, text


def test_a_failing_redactor_withholds_the_text(monkeypatch: pytest.MonkeyPatch) -> None:
    def broken(_text: str, _exceptions: object) -> str:
        raise RuntimeError("boom")

    monkeypatch.setattr(error_tracking, "_text_redactor", broken)
    event = {"exception": {"values": [{"type": "X", "value": SUBJECT_KEY}]}, "message": SUBJECT_KEY}

    scrubbed = scrub_event(event, None)

    assert SUBJECT_KEY not in json.dumps(scrubbed)
    assert scrub_breadcrumb({"message": SUBJECT_KEY}, None)["message"] == "[redacted]"


def test_without_a_redactor_the_structure_scrubbing_still_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(error_tracking, "_text_redactor", None)
    event = {"exception": {"values": [{"type": "X", "value": "kept"}]}, "extra": {"api_key": "x", "note": "kept"}}

    scrubbed = scrub_event(event, None)

    assert scrubbed["exception"]["values"][0]["value"] == "kept"
    assert scrubbed["extra"] == {"api_key": "[redacted]", "note": "kept"}


@pytest.mark.usefixtures("backend_redactor")
def test_the_request_url_goes_through_the_text_redaction() -> None:
    event = {"request": {"url": f"https://kp.example.org/hooks/{BOT_TOKEN}1Z/notify?x=1", "query_string": "x=1"}}

    url = scrub_event(event, None)["request"]["url"]

    assert BOT_TOKEN not in url, url
    assert url.startswith("https://kp.example.org/hooks/<redacted>/notify"), url
