"""The error-tracking event carries the route pattern, never the raw request path (#1925).

``event.request.url`` is set by the SDK's ASGI integration from the raw request
target. The path carries the attachment download token (which *is* the
authorisation) and the tenant slug derived from a person's display name — what
``loggable_path`` already removes from the access log. The measurement drives
the real stack: the API's process entry with ``SENTRY_DSN`` set (the real
``init_error_tracking`` call and ``before_send`` hook), the real SDK ASGI
integration, a request that raises, and a transport stub that collects what
would have been sent.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any

import pytest

from app.common.log_privacy import loggable_path
from app.observability import error_tracking
from app.observability.error_tracking import scrub_event
from tests.unit.guards.test_privacy_logs_carry_no_plaintext_subject import BACKEND_ROOT

# Assembled at run time: a literal shaped like a credential is reported by the
# repository's secret scanner (BACKEND.md §16.3).
SLUG = "-".join(("max", "mustermann", "1925"))
DOWNLOAD_TOKEN = "-".join(("dl", "token", "1925", "x" * 24))

_PROBE = r"""
import json, os
import app.main
import sentry_sdk
from fastapi import APIRouter
from starlette.testclient import TestClient

events = []

class Stub(sentry_sdk.transport.Transport):
    def capture_envelope(self, envelope):
        for item in envelope.items:
            if item.headers.get("type") == "event":
                events.append(item.payload.json)

client = sentry_sdk.get_client()
assert client.is_active(), "the process entry did not enable error tracking"
client.transport = Stub(client.options)

router = APIRouter()

@router.get("/api/v1/t/{tenant_slug}/attachments/{key}/download")
def download(tenant_slug: str, key: str):
    raise RuntimeError("download failed")

@router.get("/api/v1/attachments/token/{token}")
def by_token(token: str):
    raise RuntimeError("token download failed")

app.main.app.include_router(router)
http = TestClient(app.main.app, raise_server_exceptions=False)
http.get("/api/v1/t/" + os.environ["PROBE_SLUG"] + "/attachments/k-1/download?x=1")
http.get("/api/v1/attachments/token/" + os.environ["PROBE_TOKEN"])
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
            "PROBE_SLUG": SLUG,
            "PROBE_TOKEN": DOWNLOAD_TOKEN,
        },
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    lines = [line for line in result.stdout.splitlines() if line.startswith("EVENTS=")]
    assert lines, result.stdout + result.stderr
    events = json.loads(lines[-1].removeprefix("EVENTS="))
    # The SDK reports both the unhandled exception and the error-handler's log
    # record for each request; every one of them carries the request.
    assert len(events) >= 2 and all(event.get("request") for event in events), events
    return events


@pytest.mark.parametrize("secret", [SLUG, DOWNLOAD_TOKEN])
def test_no_event_carries_a_raw_path_segment(captured: list[dict[str, Any]], secret: str) -> None:
    for event in captured:
        text = json.dumps(event)
        position = text.find(secret)
        assert position < 0, f"{secret!r} left the process: …{text[max(0, position - 200) : position + 80]}…"


def test_the_request_url_is_the_route_pattern_with_method_kept(captured: list[dict[str, Any]]) -> None:
    urls = {event["request"]["url"].removeprefix("http://testserver") for event in captured}

    assert urls == {"/api/v1/t/{tenant_slug}/attachments/{key}/download", "/api/v1/attachments/token/{token}"}
    assert {event["request"]["method"] for event in captured} == {"GET"}
    assert {event["transaction"] for event in captured} == urls


@pytest.fixture
def backend_path_redactor(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(error_tracking, "_path_redactor", loggable_path)


@pytest.mark.usefixtures("backend_path_redactor")
def test_an_unmatched_request_falls_back_to_the_service_path_redactor() -> None:
    # No route matched (a 404 path, an error in a middleware before routing): the
    # SDK has no pattern, the transaction name *is* the raw path.
    raw = f"/api/v1/attachments/token/{DOWNLOAD_TOKEN}"
    event = {
        "transaction": raw,
        "transaction_info": {"source": "url"},
        "request": {"method": "GET", "url": f"https://kp.example.org{raw}?x=1", "query_string": "x=1"},
    }

    scrubbed = scrub_event(event, None)

    assert DOWNLOAD_TOKEN not in json.dumps(scrubbed)
    assert scrubbed["request"]["url"].startswith("https://kp.example.org/api/v1/"), scrubbed["request"]
    assert scrubbed["request"]["method"] == "GET"
    assert "?" not in scrubbed["request"]["url"]


def test_without_a_path_redactor_only_api_and_version_segments_survive(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(error_tracking, "_path_redactor", None)
    event = {
        "transaction": f"/api/v1/t/{SLUG}/plants",
        "transaction_info": {"source": "url"},
        "request": {"url": f"http://svc.local/api/v1/t/{SLUG}/plants#frag"},
    }

    scrubbed = scrub_event(event, None)

    assert SLUG not in json.dumps(scrubbed)
    assert scrubbed["request"]["url"] == "http://svc.local/api/v1/{}/{}/{}"


@pytest.mark.usefixtures("backend_path_redactor")
@pytest.mark.parametrize(
    "transaction",
    [
        f"http://10.0.0.1:8000/api/v1/attachments/token/{DOWNLOAD_TOKEN}",  # uvicorn sets ``server``: absolute URL
        f"/api/v1/attachments/token/{DOWNLOAD_TOKEN}",
        f"//{SLUG}/x",
    ],
)
def test_an_unmatched_transaction_name_is_reduced_whatever_its_shape(transaction: str) -> None:
    event = {
        "transaction": transaction,
        "transaction_info": {"source": "url"},
        "request": {"url": transaction},
    }

    text = json.dumps(scrub_event(event, None))

    assert DOWNLOAD_TOKEN not in text and SLUG not in text, text


@pytest.mark.usefixtures("backend_path_redactor")
def test_a_scheme_less_request_url_is_only_a_path_and_userinfo_is_dropped() -> None:
    bare = scrub_event({"request": {"url": f"//{SLUG}/x"}}, None)["request"]["url"]
    userinfo = scrub_event({"request": {"url": f"https://u:p@[::1]:8000/api/v1/{SLUG}"}}, None)["request"]["url"]

    assert SLUG not in bare and not bare.startswith("://")
    assert userinfo == "https://[::1]:8000/api/v1/{}"


@pytest.mark.usefixtures("backend_path_redactor")
def test_a_worker_task_name_is_not_a_request_path() -> None:
    event = {"transaction": "app.tasks.care_tasks.generate", "transaction_info": {"source": "task"}}

    scrubbed = scrub_event(event, None)

    assert scrubbed["transaction"] == "app.tasks.care_tasks.generate"
    assert scrubbed["transaction_info"] == {"source": "task"}
