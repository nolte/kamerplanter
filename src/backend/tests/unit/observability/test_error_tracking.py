"""Tests for the shared error-tracking wiring (#777).

These run against the *backend's* copy of the module. The copies in the two
microservices are byte-identical and a drift guard enforces that, so testing one
tests all three — that is the whole point of the sync pattern.

The two properties worth protecting are the optionality contract (no DSN => the
SDK is never touched) and the scrubbing rules (no credential or personal datum
leaves the process). Both are the kind of thing that only ever fails silently,
which is exactly why they are asserted rather than trusted.
"""

from __future__ import annotations

import sys
import types

import pytest

from app.observability.error_tracking import (
    ENVIRONMENTS,
    init_error_tracking,
    resolve_release,
    scrub_breadcrumb,
    scrub_event,
)


class _FakeSentry(types.ModuleType):
    """Stand-in for ``sentry_sdk`` that records what it was configured with."""

    def __init__(self) -> None:
        super().__init__("sentry_sdk")
        self.init_kwargs: dict | None = None
        self.tags: dict[str, str] = {}

    def init(self, **kwargs) -> None:
        self.init_kwargs = kwargs

    def set_tag(self, key: str, value: str) -> None:
        self.tags[key] = value


@pytest.fixture
def fake_sentry(monkeypatch: pytest.MonkeyPatch) -> _FakeSentry:
    module = _FakeSentry()
    monkeypatch.setitem(sys.modules, "sentry_sdk", module)
    return module


# ── Optionality contract ──────────────────────────────────────────────────


def test_no_dsn_means_the_sdk_is_never_touched(monkeypatch: pytest.MonkeyPatch, fake_sentry: _FakeSentry) -> None:
    monkeypatch.delenv("SENTRY_DSN", raising=False)

    assert init_error_tracking(component="backend", release="x@1") is False
    assert fake_sentry.init_kwargs is None


def test_blank_dsn_is_treated_as_absent(monkeypatch: pytest.MonkeyPatch, fake_sentry: _FakeSentry) -> None:
    # A Helm value or compose default of "" arrives as whitespace, not as unset.
    monkeypatch.setenv("SENTRY_DSN", "   ")

    assert init_error_tracking(component="backend", release="x@1") is False
    assert fake_sentry.init_kwargs is None


def test_dsn_enables_the_sdk_with_the_mandated_settings(
    monkeypatch: pytest.MonkeyPatch, fake_sentry: _FakeSentry
) -> None:
    monkeypatch.setenv("SENTRY_DSN", "https://key@tracker.example/1")
    monkeypatch.setenv("SENTRY_ENVIRONMENT", "staging")

    assert init_error_tracking(component="backend", release="kamerplanter-backend@1.0.0") is True

    kwargs = fake_sentry.init_kwargs
    assert kwargs is not None
    assert kwargs["dsn"] == "https://key@tracker.example/1"
    assert kwargs["environment"] == "staging"
    assert kwargs["release"] == "kamerplanter-backend@1.0.0"
    # The three non-negotiables of the integration contract.
    assert kwargs["send_default_pii"] is False
    assert kwargs["before_send"] is scrub_event
    assert kwargs["before_breadcrumb"] is scrub_breadcrumb
    assert fake_sentry.tags["component"] == "backend"


def test_unknown_environment_still_initialises(monkeypatch: pytest.MonkeyPatch, fake_sentry: _FakeSentry) -> None:
    monkeypatch.setenv("SENTRY_DSN", "https://key@tracker.example/1")
    monkeypatch.setenv("SENTRY_ENVIRONMENT", "producton")

    assert init_error_tracking(component="backend", release="x@1") is True
    # Passed through, not corrected: a stray value is visible in the tracker's
    # environment list, whereas a refusal looks like a healthy quiet service.
    assert fake_sentry.init_kwargs is not None
    assert fake_sentry.init_kwargs["environment"] == "producton"
    assert "producton" not in ENVIRONMENTS


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("1.0", 1.0), ("0.25", 0.25), ("0", 0.0), ("not-a-number", 1.0), ("2.5", 1.0), ("-1", 1.0)],
)
def test_sample_rate_falls_back_to_full_capture_on_nonsense(
    monkeypatch: pytest.MonkeyPatch, fake_sentry: _FakeSentry, raw: str, expected: float
) -> None:
    monkeypatch.setenv("SENTRY_DSN", "https://key@tracker.example/1")
    monkeypatch.setenv("SENTRY_SAMPLE_RATE", raw)

    init_error_tracking(component="backend", release="x@1")

    assert fake_sentry.init_kwargs is not None
    assert fake_sentry.init_kwargs["sample_rate"] == expected


def test_release_prefers_the_deployment_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SENTRY_RELEASE", "sha-abc123")
    assert resolve_release("kamerplanter-backend", "1.0.0") == "sha-abc123"


def test_release_falls_back_to_component_and_version(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SENTRY_RELEASE", raising=False)
    assert resolve_release("kamerplanter-backend", "1.0.0") == "kamerplanter-backend@1.0.0"


# ── Scrubbing ─────────────────────────────────────────────────────────────


def test_request_body_and_cookies_never_leave_the_process() -> None:
    event = {
        "request": {
            "url": "https://kp.example/api/v1/auth/login",
            "data": {"email": "grower@example.org", "password": "hunter2"},
            "cookies": {"refresh_token": "eyJ..."},
        }
    }

    scrubbed = scrub_event(event)

    assert "data" not in scrubbed["request"]
    assert "cookies" not in scrubbed["request"]
    # The route survives: it is the most valuable grouping signal there is.
    assert scrubbed["request"]["url"] == "https://kp.example/api/v1/auth/login"


def test_headers_are_allow_listed_not_deny_listed() -> None:
    event = {
        "request": {
            "headers": {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0",
                "Authorization": "Bearer eyJhbGciOi...",
                "Cookie": "session=abc",
                "X-Some-Future-Proxy-Header": "whatever it carries",
            }
        }
    }

    headers = scrub_event(event)["request"]["headers"]

    assert set(headers) == {"Content-Type", "User-Agent"}
    # The point of the allow-list: a header nobody thought about is withheld by
    # default rather than leaking until someone remembers to blocklist it.
    assert "X-Some-Future-Proxy-Header" not in headers


def test_query_string_credentials_are_redacted_by_name() -> None:
    event = {"request": {"query_string": "page=2&api_key=s3cr3t&sort=name&session_id=abc"}}

    query = scrub_event(event)["request"]["query_string"]

    assert query == "page=2&api_key=[redacted]&sort=name&session_id=[redacted]"


def test_user_context_keeps_only_the_join_keys() -> None:
    event = {
        "user": {
            "id": "users/42",
            "tenant": "acme",
            "email": "grower@example.org",
            "username": "grower",
            "ip_address": "203.0.113.7",
        }
    }

    assert scrub_event(event)["user"] == {"id": "users/42", "tenant": "acme"}


def test_stack_frame_locals_are_redacted() -> None:
    # The frame that raised inside an authentication call is the one holding a
    # plaintext password — the single most likely PII leak in a Python trace.
    event = {
        "exception": {
            "values": [
                {
                    "stacktrace": {
                        "frames": [
                            {
                                "function": "authenticate",
                                "vars": {
                                    "email": "grower@example.org",
                                    "password": "hunter2",
                                    "attempt": "3",
                                },
                            }
                        ]
                    }
                }
            ]
        }
    }

    frame_vars = scrub_event(event)["exception"]["values"][0]["stacktrace"]["frames"][0]["vars"]

    assert frame_vars["password"] == "[redacted]"
    assert frame_vars["email"] == "[redacted]"
    # Non-sensitive locals survive — the trace has to stay useful.
    assert frame_vars["attempt"] == "3"


def test_extra_context_is_redacted_by_key_name() -> None:
    event = {"extra": {"tenant_slug": "acme", "internal_service_token": "abc123"}}

    extra = scrub_event(event)["extra"]

    assert extra["tenant_slug"] == "acme"
    assert extra["internal_service_token"] == "[redacted]"


def test_breadcrumb_data_is_redacted() -> None:
    crumb = {"category": "httplib", "data": {"url": "/api/v1/x", "access_token": "abc"}}

    assert scrub_breadcrumb(crumb)["data"]["access_token"] == "[redacted]"


def test_scrubbing_tolerates_a_minimal_event() -> None:
    # The hook runs on every event the SDK produces, including ones with none of
    # the sections above. A KeyError here would drop the event entirely.
    assert scrub_event({"message": "something broke"}) == {"message": "something broke"}
