"""``login_local`` must not answer differently for an address with no account (SEC-H-010).

The HTTP-level proof lives in ``tests/api/test_auth_login_lockout_enumeration.py``.
This module pins the pieces that make it work and that a refactor could quietly
remove without turning that test red on a single-process run:

* the guard runs the **same** ``LoginThrottleEngine`` decision on both paths,
* it is **not inert** when nobody injects a store (``get_auth_service()`` builds
  one ``AuthService`` per request, so a per-instance store would count nothing),
* the address is **pseudonymised** in the log line, because the caller is
  anonymous and the address may belong to a third party (NFR-011),
* the branch still burns a bcrypt round, so the stopwatch cannot answer the
  question the status code no longer does.
"""

from unittest.mock import MagicMock

import pytest
import structlog

from app.common.exceptions import AccountLockedError, UnauthorizedError
from app.data_access.external.unknown_account_store import MemoryUnknownAccountStore
from app.domain.engines.login_throttle_engine import MAX_ATTEMPTS, LoginThrottleEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.services import auth_service as auth_service_module
from app.domain.services.auth_service import AuthService

UNKNOWN_EMAIL = "ghost@example.com"
SOME_PASSWORD = "attacker-guess-password-2024"


def _make_service(
    store: MemoryUnknownAccountStore | None = None,
    password_engine: PasswordEngine | None = None,
) -> AuthService:
    repo = MagicMock()
    repo.get_by_email.return_value = None
    return AuthService(
        user_repo=repo,
        auth_provider_repo=MagicMock(),
        refresh_token_repo=MagicMock(),
        password_engine=password_engine or PasswordEngine(),
        token_engine=TokenEngine("test-secret-key-for-unit-tests-32chars!", "HS256"),
        throttle_engine=LoginThrottleEngine(),
        email_service=MagicMock(),
        frontend_url="http://localhost:5173",
        unknown_account_store=store,
    )


def _fail_n_times(service: AuthService, times: int, email: str = UNKNOWN_EMAIL) -> None:
    for _ in range(times):
        with pytest.raises(UnauthorizedError):
            service.login_local(email, SOME_PASSWORD)


class TestUnknownAccountReachesTheSameLockout:
    def test_below_the_threshold_answers_401(self) -> None:
        service = _make_service(MemoryUnknownAccountStore())
        _fail_n_times(service, MAX_ATTEMPTS - 1)

        with pytest.raises(UnauthorizedError):
            service.login_local(UNKNOWN_EMAIL, SOME_PASSWORD)

    def test_at_the_threshold_answers_423_with_the_same_message(self) -> None:
        service = _make_service(MemoryUnknownAccountStore())
        _fail_n_times(service, MAX_ATTEMPTS)

        with pytest.raises(AccountLockedError) as excinfo:
            service.login_local(UNKNOWN_EMAIL, SOME_PASSWORD)

        assert excinfo.value.status_code == 423
        assert excinfo.value.error_code == "ACCOUNT_LOCKED"
        assert excinfo.value.message == "Account temporarily locked. Try again in 15 minutes."

    def test_counter_is_per_address(self) -> None:
        """A shared counter would answer 423 for a fresh address, which is its own oracle."""
        service = _make_service(MemoryUnknownAccountStore())
        _fail_n_times(service, MAX_ATTEMPTS)

        with pytest.raises(UnauthorizedError):
            service.login_local("another-ghost@example.com", SOME_PASSWORD)


class TestGuardIsNotInert:
    def test_store_defaults_to_the_process_wide_instance(self) -> None:
        """Not ``None``, or the guard would be a no-op wherever nobody wires it."""
        default_store = auth_service_module.DEFAULT_UNKNOWN_ACCOUNT_STORE
        assert _make_service(store=None)._unknown_account_store is default_store

    def test_counter_survives_across_service_instances(self) -> None:
        """Production rebuilds AuthService per request; the count must not restart."""
        store = MemoryUnknownAccountStore()
        _fail_n_times(_make_service(store), 1)
        _fail_n_times(_make_service(store), MAX_ATTEMPTS - 1)

        with pytest.raises(AccountLockedError):
            _make_service(store).login_local(UNKNOWN_EMAIL, SOME_PASSWORD)


class TestSideChannelsOnTheUnknownPath:
    def test_log_line_carries_a_digest_not_the_address(self) -> None:
        service = _make_service(MemoryUnknownAccountStore())

        with structlog.testing.capture_logs() as logs, pytest.raises(UnauthorizedError):
            service.login_local(UNKNOWN_EMAIL, SOME_PASSWORD)

        events = [entry for entry in logs if entry["event"] == "login_unknown_account_attempt"]
        assert len(events) == 1
        assert UNKNOWN_EMAIL not in str(events[0])
        assert events[0]["email_sha256"]

    def test_bcrypt_round_is_burned_so_the_branch_is_not_faster(self) -> None:
        """Without this the response is identical and the clock still answers."""
        password_engine = MagicMock(wraps=PasswordEngine())
        service = _make_service(MemoryUnknownAccountStore(), password_engine=password_engine)

        with pytest.raises(UnauthorizedError):
            service.login_local(UNKNOWN_EMAIL, SOME_PASSWORD)

        assert password_engine.verify_password.call_count == 1
        submitted, decoy_hash = password_engine.verify_password.call_args[0]
        assert submitted == SOME_PASSWORD
        assert decoy_hash.startswith("$2b$")
        assert password_engine.verify_password.return_value is not True

    def test_locked_out_unknown_address_skips_bcrypt_exactly_like_a_real_one(self) -> None:
        """The real path returns 423 *before* verifying; the decoy must match that."""
        store = MemoryUnknownAccountStore()
        _fail_n_times(_make_service(store), MAX_ATTEMPTS)

        password_engine = MagicMock(wraps=PasswordEngine())
        with pytest.raises(AccountLockedError):
            _make_service(store, password_engine=password_engine).login_local(UNKNOWN_EMAIL, SOME_PASSWORD)

        assert password_engine.verify_password.call_count == 0
