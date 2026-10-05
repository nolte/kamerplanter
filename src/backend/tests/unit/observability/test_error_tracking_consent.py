"""The ``error_tracking`` consent decides whether an error event names anybody (#2136, MT-040).

Before #2136 the purpose was offered as an Art. 6 (1) a consent and read by
nothing: Sentry attached what it attached whatever the person had chosen, and a
revocation changed nothing (Art. 7 (3)). Decision (orchestrator, reversible):
the event's ``user`` block — the pseudonyms of account and tenant — is sent only
with a granted consent; the rest of the event (already scrubbed of bodies,
headers, raw paths and texts) is the operator's error tracking and does not
depend on it.

The end-to-end proof through the real SDK is in
``test_error_events_carry_pseudonyms.py``; these cases pin the decision path.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest

from app.common.request_context import bind_actor, bind_tenant, clear_request, start_request
from app.config.settings import settings
from app.domain.engines.consent_engine import ERROR_TRACKING
from app.domain.models.privacy import ConsentRecord
from app.observability import error_tracking, event_user
from app.observability.error_tracking import scrub_event

_SALT = "consent-probe-" * 4


@pytest.fixture(autouse=True)
def _request(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setattr(settings, "log_pseudonym_salt", _SALT)
    monkeypatch.setattr(error_tracking, "_user_context", event_user.error_event_user)
    start_request("0b6a1f9e-3c2d-4e5f-8a7b-9c0d1e2f3a4b")
    bind_actor("owner-2136")
    bind_tenant("tenant-2136")
    yield
    clear_request()


def _consents(answer: bool, calls: list[tuple[str, str]]) -> Any:
    def lookup(user_key: str, purpose: str) -> bool:
        calls.append((user_key, purpose))
        return answer

    return lookup


def test_a_granted_consent_sends_the_pseudonyms(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(event_user, "has_consent", _consents(True, calls))

    user = scrub_event({"message": "boom"})["user"]

    assert user["id"].startswith("sub_") and user["tenant"].startswith("ten_")
    assert calls == [("owner-2136", ERROR_TRACKING)]


def test_a_revoked_consent_sends_no_user_block(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(event_user, "has_consent", _consents(False, []))

    assert "user" not in scrub_event({"message": "boom", "user": {"id": "owner-2136"}})


def test_an_unreadable_consent_store_is_a_no(monkeypatch: pytest.MonkeyPatch) -> None:
    def failing(user_key: str, purpose: str) -> bool:
        raise ConnectionError("arangodb unreachable")

    monkeypatch.setattr(event_user, "has_consent", failing)

    assert "user" not in scrub_event({"message": "boom"})


def test_the_consent_is_read_once_per_request_however_many_events(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(event_user, "has_consent", _consents(True, calls))

    for _ in range(3):
        scrub_event({"message": "boom"})

    assert len(calls) == 1


def test_a_new_principal_on_the_request_is_asked_again(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(event_user, "has_consent", _consents(True, calls))

    scrub_event({"message": "boom"})
    bind_actor("someone-else")
    scrub_event({"message": "boom"})

    assert [user for user, _purpose in calls] == ["owner-2136", "someone-else"]


class _ConsentRepo:
    def __init__(self, record: ConsentRecord | None) -> None:
        self._record = record

    def get_by_user_and_purpose(self, user_key: str, purpose: str) -> ConsentRecord | None:
        return self._record if self._record and self._record.purpose == purpose else None


@pytest.mark.parametrize(
    ("record", "expected"),
    [
        (None, False),
        (ConsentRecord(user_key="owner-2136", purpose=ERROR_TRACKING, granted=True), True),
        (ConsentRecord(user_key="owner-2136", purpose=ERROR_TRACKING, granted=False), False),
    ],
)
def test_the_lookup_reads_the_consent_store(
    monkeypatch: pytest.MonkeyPatch, record: ConsentRecord | None, expected: bool
) -> None:
    """The real ``has_consent`` asks the REQ-025 store through ``ConsentGuard``: absent = no."""
    from app.common import dependencies

    monkeypatch.setattr(dependencies, "get_consent_repo", lambda: _ConsentRepo(record))

    assert event_user.has_consent("owner-2136", ERROR_TRACKING) is expected
