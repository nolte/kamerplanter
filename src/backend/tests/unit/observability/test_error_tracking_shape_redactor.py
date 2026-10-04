"""The shared shape-based redactor, its key/tags/contexts walk and its uncaught hooks (#1926).

Run against the backend's copy of ``kp_errortracking.error_tracking`` — the copies in the
two microservices are byte-identical (``kp_errortracking copies in sync``), so this tests
all three. The services' own wiring (their ``app.main`` passes this redactor and installs
the hooks) is measured through a real subprocess in each service's own test suite
(``test_error_tracking_redacts_texts.py``).
"""

from __future__ import annotations

import sys
import threading
import time

import pytest

from app.observability import error_tracking
from app.observability.error_tracking import (
    install_uncaught_exception_redaction,
    scrub_event,
    shape_text_redactor,
)

# Assembled at run time: a literal shaped like a credential is reported by the secret scanner.
PASSWORD = "-".join(("PW", "1926", "unit"))
API_KEY = "-".join(("KEY", "1926", "unit"))
ADDRESS = "@".join(("mira-1926", "example.org"))
BOT = "AAH" + "k9Zq" * 8
BODY = "eyJvcCI6ImRvd25sb2FkIiwia2V5IjoiYWJjMTIzIiwiZXhwIjoxNzkwMDAwMDAwfQ"
SIG = "x9Yz" * 10 + "abc"


@pytest.mark.parametrize(
    ("text", "secrets"),
    [
        (f"redis://:{PASSWORD}@valkey:6379/0 refused", (PASSWORD,)),
        (f"https://svc:{PASSWORD}@llm.internal/v1", (PASSWORD,)),
        (f"GET https://api.example.org/v1/forecast?lat=1&appid={API_KEY} failed", (API_KEY,)),
        (f"redirect https://app.example.org/cb#access_token={API_KEY}", (API_KEY,)),
        (f"Max retries exceeded with url: /v1/send?key={API_KEY} (Caused by …)", (API_KEY,)),
        (f"POST /v1/send?key={API_KEY} HTTP/1.1", (API_KEY,)),
        (f"refused for {ADDRESS}", (ADDRESS,)),
        (f"retry /bot18801880:{BOT}/sendMessage", (BOT,)),
        (f"POST /api/webhooks/{'1880' * 4}/{BOT}-{BOT}", (BOT,)),
        (f"GET /api/v1/attachments/token/{BODY}.{SIG}", (BODY, SIG)),
        ("x" * 100 + f".{ADDRESS}", (ADDRESS,)),
    ],
)
def test_a_shape_is_masked(text: str, secrets: tuple[str, ...]) -> None:
    masked = shape_text_redactor(text, ())
    for secret in secrets:
        assert secret not in masked, masked


def test_what_triage_needs_stays() -> None:
    masked = shape_text_redactor(
        f"Client error '401' for url 'https://svc:{PASSWORD}@llm.internal/v1/chat?k={API_KEY}'"
    )
    assert "llm.internal/v1/chat" in masked
    assert "Client error '401'" in masked


@pytest.mark.parametrize(
    "text",
    [
        "x if y else None  # why?",
        "/data/migrations/v0056_backfill_user_key_on_three_models.py",
        "/static/" + "abcdefghijklmnopqrstuvwxyz" * 2,
        "version 3.14.0.1 of the library",
        "see https://example.org/docs/page for details",
        "a@b is not an address",
    ],
)
def test_ordinary_text_is_left_alone(text: str) -> None:
    assert shape_text_redactor(text, ()) == text


def test_masking_is_idempotent() -> None:
    text = f"https://svc:{PASSWORD}@llm.internal/v1?k={API_KEY} for {ADDRESS} /bot18801880:{BOT}/x /t/{BODY}.{SIG}"
    once = shape_text_redactor(text, ())
    assert shape_text_redactor(once, ()) == once


@pytest.mark.parametrize(
    "unit",
    [
        "a",
        "a.",
        "a@",
        "http://a",
        "http://",
        "a://",
        "@a.",
        "x" * 70 + "@",
        "/bot1:",
        "/" + "A1" * 16,
        "GET /a?",
        "with url: /a?",
    ],
)
def test_the_redactor_is_linear(unit: str) -> None:
    text = unit * (200_000 // len(unit))
    started = time.perf_counter()
    shape_text_redactor(text, ())
    assert time.perf_counter() - started < 1.0


def test_dict_keys_tags_and_contexts_go_through_the_text_redactor(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(error_tracking, "_text_redactor", shape_text_redactor)
    event = {
        "extra": {ADDRESS: f"https://x:{PASSWORD}@h/p"},
        "tags": {"who": ADDRESS},
        "contexts": {"call": {ADDRESS: f"https://h/p?k={API_KEY}"}},
    }

    scrubbed = scrub_event(event, None)

    blob = str(scrubbed)
    for secret in (ADDRESS, PASSWORD, API_KEY):
        assert secret not in blob, blob


@pytest.fixture
def restore_hooks():
    saved = (sys.excepthook, threading.excepthook, sys.unraisablehook)
    yield
    sys.excepthook, threading.excepthook, sys.unraisablehook = saved


def test_the_hooks_are_installed_once(restore_hooks) -> None:  # type: ignore[no-untyped-def]
    install_uncaught_exception_redaction()
    first = (sys.excepthook, threading.excepthook, sys.unraisablehook)
    install_uncaught_exception_redaction()

    assert (sys.excepthook, threading.excepthook, sys.unraisablehook) == first
    assert all(getattr(hook, "_kp_redacting", False) for hook in first)


def test_a_hook_that_cannot_render_fails_closed(restore_hooks, monkeypatch: pytest.MonkeyPatch, capsys) -> None:  # type: ignore[no-untyped-def]
    install_uncaught_exception_redaction()

    def explode(*_args: object) -> str:
        raise RuntimeError("renderer broke")

    monkeypatch.setattr(error_tracking.traceback, "format_exception", explode)
    try:
        raise ValueError(f"secret {ADDRESS}")
    except ValueError:
        sys.excepthook(*sys.exc_info())  # type: ignore[arg-type]

    err = capsys.readouterr().err
    assert ADDRESS not in err
    assert "ValueError" in err
