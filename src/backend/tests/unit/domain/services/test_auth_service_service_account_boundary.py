"""A service account must not be able to hold or use an interactive credential — #1559.

REQ-023 defines ``account_type: 'service'`` as an M2M identity: API-key only, no
interactive login, with an IP allowlist and a per-account rate limit. Nothing
enforced that. ``POST /users/me/password`` depends on ``get_current_user`` alone,
and ``FullAuthProvider.resolve_user`` resolves a ``kp_``-prefixed bearer through
``authenticate_api_key``, so a service account reaches
``AuthService.change_password``. That method's SSO branch lets a caller with no
``password_hash`` set one *without* presenting ``current_password`` — and a
service account has no hash. It then writes the hash and creates a ``LOCAL``
auth provider. Afterwards the account satisfies every precondition of
``login_local``: active, local provider, password hash. The ``is_active``
backstop from #1528 does not catch it, because the account is active.

**The chain is reproduced here, not asserted about.** The first test drives the
real ``change_password`` and then the real ``login_local`` with the password it
just set, through a repository double that *writes the update back* into the
stored user — because a double that swallows the write would make the second
step fail for a reason that has nothing to do with the boundary, and the test
would pass while certifying nothing.

**Two surfaces, two gates.**

* granting the credential — ``change_password``, ``reset_password`` and the
  reset-token issuance that feeds it;
* minting the interactive session — ``_create_tokens``, which is the single
  method all four minting paths (local login, OAuth, refresh rotation,
  device-pairing redeem) pass through, next to the ``is_active`` backstop.

Either gate alone leaves something open: without the first, a service account
still accumulates a stored password hash and a LOCAL provider that only the
second gate makes inert; without the second, any future minting path inherits
nothing. The last test in this file is the one that shows the second gate holds
for a state the first one no longer permits to arise.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.common.exceptions import ForbiddenError, UnauthorizedError
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.models.user import User
from app.domain.services.auth_service import AuthService

SERVICE_EMAIL = "daily-bot@example.org"
USER_EMAIL = "person@example.org"
NEW_PASSWORD = "attacker-chosen-password-456"


def _account(*, account_type: str, email: str, password_hash: str | None = None) -> User:
    return User(
        _key="acc-1",
        email=email,
        display_name="Account",
        password_hash=password_hash,
        email_verified=True,
        is_active=True,
        account_type=account_type,  # type: ignore[arg-type]
    )


def _service(user: User) -> tuple[AuthService, MagicMock]:
    """Real engines, doubled repositories — and the user document really mutates.

    ``update_fields`` applies the written fields back onto the stored ``User``,
    the way ``ArangoUserRepository.update_fields`` does (read-modify-write, #1018).
    Without that, step 2 of the attack chain would read a user with no password
    hash and be refused for the wrong reason.
    """
    user_repo = MagicMock()
    user_repo.get_by_email.return_value = user
    user_repo.get_by_key.return_value = user
    user_repo.get_or_raise.return_value = user

    def _apply(key: str, fields: dict) -> User:  # noqa: ARG001
        for name, value in fields.items():
            setattr(user, name, value)
        return user

    user_repo.update_fields.side_effect = _apply

    refresh_token_repo = MagicMock()
    refresh_token_repo.create.side_effect = lambda token: token

    auth_provider_repo = MagicMock()
    auth_provider_repo.list_by_user.return_value = []

    service = AuthService(
        user_repo=user_repo,
        auth_provider_repo=auth_provider_repo,
        refresh_token_repo=refresh_token_repo,
        password_engine=PasswordEngine(),
        token_engine=TokenEngine("test-secret-key-for-unit-tests-32chars!", "HS256"),
        throttle_engine=LoginThrottleEngine(),
        email_service=MagicMock(),
        frontend_url="http://localhost:5173",
    )
    return service, user_repo


class TestTheReportedChain:
    def test_a_service_account_cannot_set_itself_a_password(self) -> None:
        """Step 1 of the chain: the credential is refused at the source."""
        account = _account(account_type="service", email=SERVICE_EMAIL)
        service, user_repo = _service(account)

        with pytest.raises(ForbiddenError):
            service.change_password("acc-1", None, NEW_PASSWORD)

        # Nothing was written: not the hash, and not the LOCAL provider that
        # would have made the account a login candidate on its own.
        assert user_repo.update_fields.call_count == 0
        assert account.password_hash is None

    def test_and_therefore_cannot_log_in_interactively(self) -> None:
        """Step 2: even if step 1 had succeeded, the login is refused.

        The password is planted directly here, which is a state the gate above
        no longer lets arise through the product. That is the point: this
        asserts the *second* gate, and it must hold for a hash that got there by
        any route — a migration, a fixture, an account converted from ``user``.
        """
        account = _account(
            account_type="service",
            email=SERVICE_EMAIL,
            password_hash=PasswordEngine().hash_password(NEW_PASSWORD),
        )
        service, _ = _service(account)

        with pytest.raises(UnauthorizedError):
            service.login_local(SERVICE_EMAIL, NEW_PASSWORD)


class TestTheInteractiveAccountIsUnaffected:
    """Positive controls — a gate one ``not`` away from locking everyone out fails here."""

    def test_an_sso_user_still_sets_an_initial_password(self) -> None:
        account = _account(account_type="user", email=USER_EMAIL)
        service, user_repo = _service(account)

        service.change_password("acc-1", None, NEW_PASSWORD)

        assert user_repo.update_fields.call_count == 1
        assert account.password_hash is not None

    def test_and_then_logs_in_with_it(self) -> None:
        account = _account(account_type="user", email=USER_EMAIL)
        service, _ = _service(account)

        service.change_password("acc-1", None, NEW_PASSWORD)
        pair, raw_refresh, _ = service.login_local(USER_EMAIL, NEW_PASSWORD)

        assert pair.access_token
        assert raw_refresh


class TestTheResetPathIsTheSameSurface:
    def test_no_reset_token_is_issued_for_a_service_account(self) -> None:
        """Silently, like the unknown-address branch — a distinct answer here
        would tell an anonymous caller which addresses are machine accounts."""
        account = _account(account_type="service", email=SERVICE_EMAIL)
        service, user_repo = _service(account)

        service.request_password_reset(SERVICE_EMAIL)

        assert user_repo.update_fields.call_count == 0
        assert service._email_service.send_password_reset_email.call_count == 0  # type: ignore[attr-defined]

    def test_an_interactive_account_still_gets_one(self) -> None:
        account = _account(account_type="user", email=USER_EMAIL)
        service, user_repo = _service(account)

        service.request_password_reset(USER_EMAIL)

        assert user_repo.update_fields.call_count == 1
        assert service._email_service.send_password_reset_email.call_count == 1  # type: ignore[attr-defined]

    def test_redeeming_a_reset_token_is_refused(self) -> None:
        """The token cannot be issued any more, but the redeem path is a second
        door into the same write and is gated on its own."""
        account = _account(account_type="service", email=SERVICE_EMAIL)
        account.password_reset_token = "planted-token"  # noqa: S105 — not a credential
        account.password_reset_expires = datetime.now(UTC) + timedelta(hours=1)
        service, user_repo = _service(account)

        user_repo.get_by_password_reset_token.return_value = account

        with pytest.raises(ForbiddenError):
            service.reset_password("planted-token", NEW_PASSWORD)

        assert user_repo.update_fields.call_count == 0


class TestTheMintingBackstop:
    """``_create_tokens`` is the one method every interactive session passes.

    ``login_local``, ``complete_oauth``, ``refresh_tokens`` and
    ``redeem_device_pairing`` all end in it, so the property holds for an entry
    point nobody has written yet — the same argument #1528 made for ``is_active``.
    """

    def test_minting_refuses_a_service_account_directly(self) -> None:
        account = _account(account_type="service", email=SERVICE_EMAIL)
        service, _ = _service(account)

        with pytest.raises(UnauthorizedError):
            service._create_tokens(account, None, None)

    def test_and_still_mints_for_an_interactive_account(self) -> None:
        account = _account(account_type="user", email=USER_EMAIL)
        service, _ = _service(account)

        pair, raw_refresh, _ = service._create_tokens(account, None, None)

        assert pair.access_token
        assert raw_refresh
