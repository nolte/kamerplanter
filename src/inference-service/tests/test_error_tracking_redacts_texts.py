"""This service's error-tracking events and uncaught tracebacks carry no URL userinfo, query or address (#1926).

``init_error_tracking`` declared ``redact_text=None`` here, so the event's exception
text, log entry, message and breadcrumbs left the process as the SDK built them, and the
interpreter's three uncaught-exception hooks printed raw tracebacks. Measured before the
fix, with the real SDK and a transport stub (no network): an httpx-style error text
``https://svc:<pw>@llm.internal/v1/chat?api_key=<key>`` for an address reached the event
verbatim, in all three of exception value, log entry and message, and a thread's
traceback printed it to stderr.

The probe is a real subprocess that imports this service's own ``app.main`` (so the real
``init_error_tracking`` call with the real options) with ``SENTRY_DSN`` set. What a shape
cannot hide — the free text of a question a person typed — is not claimed here.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

import pytest

SERVICE_ROOT = pathlib.Path(__file__).resolve().parents[1]

# Assembled at run time: a literal shaped like a credential is reported by the secret scanner.
PASSWORD = "-".join(("PW", "1926", "probe"))
API_KEY = "-".join(("KEY", "1926", "probe"))
ADDRESS = "@".join(("mira-1926", "example.org"))
BOT_TOKEN = "AAH" + "k9Zq" * 8

_PROBE = r"""
import json, logging, os, sys, threading
import app.main
import sentry_sdk

# The service's own log lines are not what is measured here (a bare process prints a
# WARNING+ record through logging's last resort handler): only the event and the hooks.
logging.getLogger().addHandler(logging.NullHandler())
events = []

class Stub(sentry_sdk.transport.Transport):
    def capture_envelope(self, envelope):
        for item in envelope.items:
            if item.headers.get("type") == "event":
                events.append(item.payload.json)

client = sentry_sdk.get_client()
assert client.is_active(), "the process entry did not enable error tracking"
client.transport = Stub(client.options)

pw, key, address, bot = (os.environ[n] for n in ("P_PW", "P_KEY", "P_ADDRESS", "P_BOT"))
url = "https://svc:" + pw + "@llm.internal/v1/chat?api_key=" + key
text = "Client error '401' for url '" + url + "' for " + address + " via /bot18801880:" + bot + "/sendMessage"

def failing():
    raise RuntimeError(text)

try:
    failing()
except RuntimeError:
    logging.getLogger("probe").exception("call failed for %s", address)
sentry_sdk.capture_message("no account for " + address + " at " + url)
sentry_sdk.set_tag("who", address)
sentry_sdk.set_context("call", {address: url})
try:
    failing()
except RuntimeError as exc:
    sentry_sdk.capture_exception(exc)
sentry_sdk.flush()
print("EVENTS=" + json.dumps(events))

if os.environ.get("P_MODE") == "uncaught":
    t = threading.Thread(target=failing, name="probe-thread")
    t.start()
    t.join()
    class Probe:
        def __del__(self):
            failing()
    p = Probe()
    del p
    failing()
"""


def _run(mode: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-W", "ignore", "-c", _PROBE],
        cwd=SERVICE_ROOT,
        env={
            **os.environ,
            "PYTHONPATH": str(SERVICE_ROOT),
            "SENTRY_DSN": "https://public@tracker.invalid/1",
            "SENTRY_ENVIRONMENT": "e2e",
            "P_PW": PASSWORD,
            "P_KEY": API_KEY,
            "P_ADDRESS": ADDRESS,
            "P_BOT": BOT_TOKEN,
            "P_MODE": mode,
        },
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )


@pytest.fixture(scope="module")
def probe() -> tuple[str, list[dict]]:
    result = _run("uncaught")
    lines = [line for line in result.stdout.splitlines() if line.startswith("EVENTS=")]
    assert lines, result.stdout + result.stderr
    return result.stderr, json.loads(lines[-1].removeprefix("EVENTS="))


SECRETS = (PASSWORD, API_KEY, ADDRESS, BOT_TOKEN)


@pytest.mark.parametrize("secret", SECRETS)
def test_the_event_carries_no_secret_in_any_text_field(probe: tuple[str, list[dict]], secret: str) -> None:
    _stderr, events = probe
    assert events, "the SDK sent no event"
    assert secret not in json.dumps(events)


def test_the_event_keeps_what_triage_needs(probe: tuple[str, list[dict]]) -> None:
    _stderr, events = probe
    blob = json.dumps(events)
    assert "llm.internal" in blob
    assert "Client error '401'" in blob
    assert "<email>" in blob


@pytest.mark.parametrize("secret", SECRETS)
def test_an_uncaught_exception_prints_no_secret_to_stderr(probe: tuple[str, list[dict]], secret: str) -> None:
    stderr, _events = probe
    assert "RuntimeError" in stderr, stderr
    assert secret not in stderr, stderr


def test_every_uncaught_hook_printed_the_redacted_form(probe: tuple[str, list[dict]]) -> None:
    stderr, _events = probe
    assert "Exception in thread probe-thread" in stderr, stderr
    assert "Exception ignored" in stderr, stderr
    assert stderr.count("Client error '401'") >= 3, stderr
