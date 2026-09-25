"""#1781 — what a log line may carry about a person: the shared helpers.

A log stream has no retention rule of its own (NFR-011): whatever it receives
outlives the account it names, the erasure that removed the account and the
erasure record proving it (R-06). ``app.common.log_privacy`` is the one home of
the helpers every log call uses instead of the raw value — the salted subject
reference, a redacted exception text and a truncated IP.

Every test calls the real helper, which reads ``settings`` at call time — the
same object the production call sites read.
"""

from __future__ import annotations

import pytest

from app.common.decoys import email_digest
from app.common.log_privacy import log_subject, loggable_error, loggable_ip
from app.config.settings import settings
from app.domain.engines.erasure_engine import UNAVAILABLE_LOG_SUBJECT, ErasureEngine

_SALT = "s" * 40


@pytest.fixture
def salted(monkeypatch: pytest.MonkeyPatch) -> str:
    monkeypatch.setattr(settings, "erasure_tombstone_salt", _SALT)
    return _SALT


# ── log_subject ─────────────────────────────────────────────────────────


def test_log_subject_is_the_erasure_engine_reference(salted: str) -> None:
    assert log_subject("12345") == ErasureEngine.log_subject("12345", salted)
    assert "12345" not in (log_subject("12345") or "")


@pytest.mark.parametrize("empty", [None, ""])
def test_log_subject_of_no_key_is_none(salted: str, empty: str | None) -> None:
    assert log_subject(empty) is None


def test_log_subject_without_salt_is_the_unavailable_constant(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "erasure_tombstone_salt", "")
    assert log_subject("12345") == UNAVAILABLE_LOG_SUBJECT


def test_log_subject_reads_the_salt_at_call_time(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "erasure_tombstone_salt", "a" * 32)
    first = log_subject("12345")
    monkeypatch.setattr(settings, "erasure_tombstone_salt", "b" * 32)
    assert log_subject("12345") != first


# ── loggable_error ──────────────────────────────────────────────────────


def test_loggable_error_replaces_the_subject_key(salted: str) -> None:
    text = loggable_error(LookupError("User 12345 not found"), user_key="12345")
    assert "12345" not in text
    assert ErasureEngine.log_subject("12345", salted) in text
    assert text.startswith("User ")


def test_loggable_error_masks_an_export_bundle_key_of_any_account(salted: str) -> None:
    text = loggable_error(OSError("No such file: '/data/privacy/exports/99999/abc.json'"))
    assert "99999" not in text
    assert "abc.json" in text


def test_loggable_error_masks_every_email_address(salted: str) -> None:
    exc = RuntimeError("recipients refused: {'Alice.Doe@Example.org': (550, b'no'), 'bob@x.io': (550, b'no')}")
    text = loggable_error(exc)
    assert "Alice.Doe@Example.org" not in text
    assert "bob@x.io" not in text
    assert f"<email:{email_digest('Alice.Doe@Example.org')}>" in text
    assert f"<email:{email_digest('bob@x.io')}>" in text
    assert "550" in text, "the rest of the text is what an operator needs"


def test_loggable_error_strips_url_query_strings(salted: str) -> None:
    exc = RuntimeError(
        "Client error '401 Unauthorized' for url "
        "'https://api.openweathermap.org/data/3.0/onecall?lat=52.52&lon=13.40&appid=SECRET'"
    )
    text = loggable_error(exc)
    assert "SECRET" not in text
    assert "52.52" not in text
    assert "https://api.openweathermap.org/data/3.0/onecall?<redacted>" in text
    assert "401 Unauthorized" in text


def test_loggable_error_keeps_a_url_without_query(salted: str) -> None:
    text = loggable_error("GET http://backend:8000/api/v1/health failed")
    assert text == "GET http://backend:8000/api/v1/health failed"


def test_loggable_error_accepts_a_plain_string(salted: str) -> None:
    assert loggable_error("disk full") == "disk full"


# ── loggable_ip ─────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("raw", "truncated"),
    [
        ("192.168.1.42", "192.168.1.0"),
        ("2001:0db8:85a3:1234:5678:8a2e:0370:7334", "2001:db8:85a3::"),
        ("::1", "::"),
        ("not-an-ip", "0.0.0.0"),
        ("", "0.0.0.0"),
    ],
)
def test_loggable_ip_is_the_r03_truncation(raw: str, truncated: str) -> None:
    assert loggable_ip(raw) == truncated


def test_loggable_ip_of_none_is_none() -> None:
    assert loggable_ip(None) is None


def test_the_ip_retention_task_uses_the_same_truncation() -> None:
    """One implementation: what the DB keeps after 7 days is what a log line carries."""
    from app.tasks.auth_tasks import _anonymize_ip

    assert _anonymize_ip is loggable_ip
    for raw in ("192.168.1.42", "2001:db8:85a3:1:2:3:4:5", "garbage"):
        assert _anonymize_ip(raw) == loggable_ip(raw)
