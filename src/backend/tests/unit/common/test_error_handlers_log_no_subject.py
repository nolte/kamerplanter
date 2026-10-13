"""The API's error handlers log no subject key, tenant slug or error message (#1796).

``app_error_handler`` logged ``message=exc.message`` — ``NotFoundError("User",
<key>)`` names the account key — and all three handlers logged the raw request
path, which carries the tenant slug (derived from a person's display name) and
entity keys. The handlers are driven directly with a real Starlette request.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

import pytest
import structlog.testing
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request

from app.common.error_handlers import app_error_handler, unhandled_error_handler, validation_error_handler
from app.common.exceptions import NotFoundError

SUBJECT_KEY = "user-key-1796"
SLUG = "max-mustermann-1796"
PATH = f"/api/v1/t/{SLUG}/memberships/{SUBJECT_KEY}"


def _request() -> Request:
    return Request({"type": "http", "method": "GET", "path": PATH, "query_string": b"", "headers": []})


HANDLERS: dict[str, Callable[[], Any]] = {
    "app_error": lambda: app_error_handler(_request(), NotFoundError("User", SUBJECT_KEY)),
    "validation_error": lambda: validation_error_handler(_request(), RequestValidationError([])),
    "unhandled_error": lambda: unhandled_error_handler(_request(), RuntimeError("boom")),
}


@pytest.mark.parametrize("event", sorted(HANDLERS))
def test_the_handler_logs_no_key_slug_or_message(event: str) -> None:
    with structlog.testing.capture_logs() as logs:
        asyncio.run(HANDLERS[event]())

    (entry,) = [e for e in logs if e["event"] == event]
    assert SUBJECT_KEY not in repr(logs)
    assert SLUG not in repr(logs)
    assert "message" not in entry
    assert entry["path"].startswith("/api/v1/"), entry
    assert entry["method"] == "GET"


def test_the_client_still_gets_the_message() -> None:
    """Only the log line loses it: the response body is the client's, unchanged."""
    response = asyncio.run(HANDLERS["app_error"]())
    assert SUBJECT_KEY.encode() in response.body
