"""The last mail an address receives carries the token that is stored, however the threadpool interleaves (#2062).

A verification link or a reset link is issued in two steps — write a fresh
single-use token over the stored one, then mail it — and both steps run after the
response, on a threadpool thread, once per request. Two requests for one account
at the same time (an anonymous resend and the refusal of a proven login; two
reset requests from two sources) interleave:

    A writes tokenA · B writes tokenB · B mails tokenB · A mails tokenA

The write of B killed tokenA, but A's mail arrives **last** — the newest mail in
the mailbox carries a dead link, and the working one sits above it. Reproduced
here deterministically with events instead of luck: the first issue is held
between its write and its mail until the second one has completed, or — when the
service serialises per account — for a bounded time.

The invariant asserted is the one a user relies on: **the newest mail carries the
stored token**.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.interfaces.email_service import IEmailService
from app.domain.models.user import User
from app.domain.services.auth_service import AuthService

ADDRESS = "owner@example.com"

#: How long the held issue waits for the other one to finish. Without serialisation the other one
#: finishes at once; with it the other one is blocked behind the held one and this is simply the delay.
_HOLD_S = 0.4


class _Repo:
    """One account; ``update_fields`` writes the tokens into it, like the real repository."""

    def __init__(self) -> None:
        self.user = User(_key="4000001", email=ADDRESS, display_name="Owner", password_hash="x", email_verified=False)
        self._lock = threading.Lock()
        self.after_write: Callable[[str], None] = lambda _field: None

    def get_by_email(self, email: str) -> User | None:
        return self.user.model_copy(deep=True) if email.lower() == ADDRESS else None

    def get_by_key(self, key: str) -> User | None:
        return self.user.model_copy(deep=True) if key == self.user.key else None

    def update_fields(self, key: str, fields: dict[str, Any]) -> User:
        with self._lock:
            self.user = self.user.model_validate({**self.user.model_dump(by_alias=True), **fields})
            written = self.user.model_copy(deep=True)
        self.after_write(next(iter(fields)))
        return written


class _Mailbox(IEmailService):
    """Records the token of every mail in arrival order."""

    def __init__(self) -> None:
        self.tokens: list[str] = []
        self.verification_tokens: list[str] = []
        self.reset_tokens: list[str] = []

    def send_verification_email(self, to_email: str, token: str, frontend_url: str) -> None:
        self.tokens.append(token)
        self.verification_tokens.append(token)

    def send_password_reset_email(self, to_email: str, token: str, frontend_url: str) -> None:
        self.tokens.append(token)
        self.reset_tokens.append(token)


def _service(repo: _Repo, mailbox: _Mailbox) -> AuthService:
    return AuthService(
        user_repo=repo,  # type: ignore[arg-type]
        auth_provider_repo=MagicMock(),
        refresh_token_repo=MagicMock(),
        password_engine=PasswordEngine(),
        token_engine=TokenEngine("test-secret-key-for-unit-tests-32chars!", "HS256"),
        throttle_engine=LoginThrottleEngine(),
        email_service=mailbox,
        frontend_url="http://localhost:5173",
        require_email_verification=True,
    )


def _collect(deferred: list[Callable[[], None]]) -> Callable[[Callable[[], None]], None]:
    return deferred.append


def _run_interleaved(repo: _Repo, first: Callable[[], None], second: Callable[[], None]) -> None:
    """Hold ``first`` between its token write and its mail until ``second`` is done (or ``_HOLD_S`` passed)."""
    first_written = threading.Event()
    second_done = threading.Event()
    held = {"armed": True}

    def after_write(_field: str) -> None:
        if threading.current_thread().name == "first" and held["armed"]:
            held["armed"] = False
            first_written.set()
            second_done.wait(timeout=_HOLD_S)

    repo.after_write = after_write

    def run_first() -> None:
        first()

    def run_second() -> None:
        first_written.wait(timeout=5)
        second()
        second_done.set()

    threads = [
        threading.Thread(target=run_first, name="first"),
        threading.Thread(target=run_second, name="second"),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)
    assert not any(thread.is_alive() for thread in threads)


def test_an_anonymous_resend_and_a_proven_link_leave_the_stored_token_in_the_newest_mail() -> None:
    repo, mailbox = _Repo(), _Mailbox()
    service = _service(repo, mailbox)
    started = time.monotonic()

    _run_interleaved(
        repo,
        lambda: service._send_fresh_verification_link(ADDRESS),
        lambda: service._send_proven_verification_link("4000001"),
    )

    stored = repo.user.email_verification_token_hash
    print(f"\nverification mails in arrival order: {len(mailbox.tokens)}, took {time.monotonic() - started:.2f}s")
    assert len(mailbox.tokens) == 2
    assert TokenEngine.hash_token(mailbox.tokens[-1]) == stored, (
        "the newest mail carries a token the other issue already overwrote"
    )


def test_two_reset_requests_leave_the_stored_token_in_the_newest_mail() -> None:
    repo, mailbox = _Repo(), _Mailbox()
    service = _service(repo, mailbox)
    deferred: list[Callable[[], None]] = []
    service.request_password_reset(ADDRESS, client_ip="203.0.113.1", defer_mail=_collect(deferred))
    service.request_password_reset(ADDRESS, client_ip="203.0.113.2", defer_mail=_collect(deferred))
    assert len(deferred) == 2

    _run_interleaved(repo, deferred[0], deferred[1])

    stored = repo.user.password_reset_token_hash
    assert len(mailbox.tokens) == 2
    assert TokenEngine.hash_token(mailbox.tokens[-1]) == stored, (
        "the newest reset mail carries a token the other request already overwrote"
    )


def test_issues_for_different_accounts_do_not_wait_for_each_other() -> None:
    """The serialisation is per account: a held issue for one account never holds another account's."""
    repo, mailbox = _Repo(), _Mailbox()
    other = User(_key="4000002", email="other@example.com", display_name="O", password_hash="x", email_verified=False)
    service = _service(repo, mailbox)
    held = threading.Event()
    release = threading.Event()

    def after_write(_field: str) -> None:
        if threading.current_thread().name == "slow":
            held.set()
            release.wait(timeout=5)

    repo.after_write = after_write
    slow = threading.Thread(target=lambda: service._issue_verification_link(repo.user), name="slow")
    slow.start()
    assert held.wait(timeout=5)
    started = time.monotonic()
    other_done = threading.Event()

    def issue_other() -> None:
        service._issue_verification_link(other)
        other_done.set()

    fast = threading.Thread(target=issue_other, name="fast")
    fast.start()
    finished = other_done.wait(timeout=2)
    elapsed = time.monotonic() - started
    release.set()
    slow.join(timeout=10)
    fast.join(timeout=10)

    assert finished, "an issue for another account waited behind a held one"
    assert elapsed < 1.0


@pytest.mark.parametrize("kind", ["verification", "reset"])
def test_a_failing_mail_releases_the_account_for_the_next_issue(kind: str) -> None:
    """A send that raises must not leave the per-account serialisation held."""
    repo, mailbox = _Repo(), _Mailbox()
    service = _service(repo, mailbox)
    real = mailbox.send_verification_email if kind == "verification" else mailbox.send_password_reset_email
    failures = {"left": 1}

    def flaky(to_email: str, token: str, frontend_url: str) -> None:
        if failures["left"]:
            failures["left"] -= 1
            raise RuntimeError("smtp down")
        real(to_email, token, frontend_url)

    if kind == "verification":
        mailbox.send_verification_email = flaky  # type: ignore[method-assign]
        issue = lambda: service._issue_verification_link(repo.user)  # noqa: E731
    else:
        mailbox.send_password_reset_email = flaky  # type: ignore[method-assign]
        deferred: list[Callable[[], None]] = []
        service.request_password_reset(ADDRESS, client_ip="203.0.113.1", defer_mail=_collect(deferred))
        service.request_password_reset(ADDRESS, client_ip="203.0.113.2", defer_mail=_collect(deferred))
        queue = list(deferred)
        issue = lambda: queue.pop(0)()  # noqa: E731

    first = threading.Thread(target=lambda: _swallow(issue))
    first.start()
    first.join(timeout=5)
    second_done = threading.Event()
    second = threading.Thread(target=lambda: (issue(), second_done.set()))
    second.start()

    assert second_done.wait(timeout=3), "the account stayed locked after a failed send"
    assert len(mailbox.tokens) == 1


def _swallow(call: Callable[[], None]) -> None:
    try:
        call()
    except Exception:  # noqa: BLE001 - the failure is the point of the test
        return
