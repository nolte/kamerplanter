"""A deactivated account must not be able to authenticate — #1528.

``AuthService.login_local`` checked the lockout, the password hash and (when
required) ``email_verified``, and never read ``is_active``. A platform admin who
suspended an account through ``PATCH /admin/platform/users/{key}`` therefore did
not lock it out of the local login: the credential is deliberately left in place
because a suspension is reversible, and nothing else on that path looked at the
flag. The four other entry points — refresh, OAuth with an existing link, API key,
device-pairing redeem — all carried the check.

The class sweep found a second hole one branch over: ``complete_oauth`` gates the
*existing link* branch and not the *auto-link* branch, so a suspended account
whose address a provider asserts as verified could log in through OAuth **and**
acquire a fresh provider link on the way in.

**What is asserted here, and why each assertion is needed**

* the negative case — deactivated account, *correct* password, refused;
* the positive control — an active account still logs in, so a gate that is one
  ``not`` away from locking everyone out does not pass;
* the *enumeration* property — a deactivated account with a **wrong** password
  still gets the generic "Invalid email or password.", because the gate runs
  after the hash comparison and not before it. Placing it earlier (the shape the
  issue suggested) hands an anonymous caller, who needs nothing but an address,
  the answer "this address exists and is suspended" — the oracle SEC-H-010 closed
  for the not-registered case;
* the backstop in ``_create_tokens``, which is what makes the property hold for
  an entry point nobody has written yet.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.common.enums import AuthProviderType
from app.common.exceptions import UnauthorizedError
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.oauth_engine import OAuthEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.models.auth import OAuthUserInfo
from app.domain.models.oidc_config import OidcProviderConfig
from app.domain.models.user import User
from app.domain.services.auth_service import AuthService

EMAIL = "suspended@example.com"
PASSWORD = "secure-password-123"
WRONG_PASSWORD = "not-the-password-456"
INACTIVE_MESSAGE = "User account is inactive."
GENERIC_MESSAGE = "Invalid email or password."


def _user(*, is_active: bool) -> User:
    return User(
        _key="u1",
        email=EMAIL,
        display_name="Suspended User",
        password_hash=PasswordEngine().hash_password(PASSWORD),
        email_verified=True,
        is_active=is_active,
    )


def _service(user: User) -> tuple[AuthService, MagicMock]:
    """Real password/token/throttle engines; only the repositories are doubles.

    The engines are real on purpose: a doubled ``PasswordEngine`` would make the
    "wrong password" case indistinguishable from the "right password" case inside
    the test, and the ordering of the two checks is the point of this file.
    """
    user_repo = MagicMock()
    user_repo.get_by_email.return_value = user
    user_repo.get_by_key.return_value = user
    user_repo.update_fields.return_value = user

    refresh_token_repo = MagicMock()
    refresh_token_repo.create.side_effect = lambda token: token

    service = AuthService(
        user_repo=user_repo,
        auth_provider_repo=MagicMock(),
        refresh_token_repo=refresh_token_repo,
        password_engine=PasswordEngine(),
        token_engine=TokenEngine("test-secret-key-for-unit-tests-32chars!", "HS256"),
        throttle_engine=LoginThrottleEngine(),
        email_service=MagicMock(),
        frontend_url="http://localhost:5173",
    )
    return service, user_repo


class TestLocalLoginGatesTheDeactivatedAccount:
    def test_a_deactivated_account_with_the_correct_password_is_refused(self) -> None:
        """RED against the pre-#1528 service, which returned a token pair here."""
        service, _ = _service(_user(is_active=False))

        with pytest.raises(UnauthorizedError) as excinfo:
            service.login_local(EMAIL, PASSWORD)

        assert excinfo.value.status_code == 401
        assert excinfo.value.error_code == "UNAUTHORIZED"
        assert excinfo.value.message == INACTIVE_MESSAGE

    def test_an_active_account_still_logs_in(self) -> None:
        """The control. An inverted or misplaced gate locks everybody out and
        would pass the test above on its own."""
        service, _ = _service(_user(is_active=True))

        token_pair, raw_refresh, is_persistent = service.login_local(EMAIL, PASSWORD)

        assert token_pair.access_token
        assert raw_refresh
        assert is_persistent is False

    def test_a_refused_login_does_not_write_the_success_state_back(self) -> None:
        """The gate sits before the write-back, so a suspended account's
        ``last_login_at`` does not move and its lockout counter is not reset."""
        service, user_repo = _service(_user(is_active=False))

        with pytest.raises(UnauthorizedError):
            service.login_local(EMAIL, PASSWORD)

        written = [call.args[1] for call in user_repo.update_fields.call_args_list]
        assert not any("last_login_at" in fields for fields in written), (
            f"a refused login wrote success state back to the account: {written}"
        )


class TestTheGateDoesNotBecomeAnEnumerationOracle:
    """SEC-H-010: what an anonymous caller can learn from an address alone.

    ``_reject_unknown_account`` went to considerable lengths — a per-address
    counter for addresses with no account, a burnt bcrypt round — so that an
    unregistered address and a wrong password are one answer. A deactivated
    account must join that answer, not form a third one, for every caller who
    does not already hold the password.
    """

    def test_a_wrong_password_on_a_deactivated_account_answers_the_generic_message(self) -> None:
        """RED against the placement the issue proposed (gate after the lookup,
        before the hash comparison): that answers "inactive" to any password."""
        service, _ = _service(_user(is_active=False))

        with pytest.raises(UnauthorizedError) as excinfo:
            service.login_local(EMAIL, WRONG_PASSWORD)

        assert excinfo.value.message == GENERIC_MESSAGE, (
            "a caller who does not know the password learned that this address exists "
            "and is suspended — the gate is running ahead of the hash comparison"
        )

    def test_a_wrong_password_answers_identically_whether_or_not_the_account_is_active(self) -> None:
        """The comparison *between* the two, which is the property that matters.

        Asserting the message of one of them pins a literal; asserting that the
        two are equal pins the indistinguishability, and stays true if the
        literal is ever reworded.
        """
        active_service, _ = _service(_user(is_active=True))
        inactive_service, _ = _service(_user(is_active=False))

        with pytest.raises(UnauthorizedError) as active_error:
            active_service.login_local(EMAIL, WRONG_PASSWORD)
        with pytest.raises(UnauthorizedError) as inactive_error:
            inactive_service.login_local(EMAIL, WRONG_PASSWORD)

        assert active_error.value.status_code == inactive_error.value.status_code
        assert active_error.value.error_code == inactive_error.value.error_code
        assert active_error.value.message == inactive_error.value.message


class TestMintingIsTheBackstop:
    """``_create_tokens`` refuses an inactive account regardless of the caller.

    Every current path refuses earlier, so this is never reached in production —
    which is exactly why it is asserted directly. It is the difference between
    "the five known entry points are gated today" and "an entry point cannot
    mint a pair for a suspended account", and #1528 exists because the first
    property does not survive a sixth branch being written.
    """

    def test_it_refuses_an_inactive_user(self) -> None:
        service, _ = _service(_user(is_active=True))

        with pytest.raises(UnauthorizedError) as excinfo:
            service._create_tokens(_user(is_active=False), None, None)

        assert excinfo.value.message == INACTIVE_MESSAGE

    def test_it_still_mints_for_an_active_user(self) -> None:
        """The control: a backstop that refuses everything is not a backstop."""
        service, _ = _service(_user(is_active=True))

        token_pair, raw_refresh, _ = service._create_tokens(_user(is_active=True), None, None)

        assert token_pair.access_token
        assert raw_refresh


# ── The OAuth auto-link branch, found by the class sweep ────────────────────


def _oauth_service(existing_user: User | None) -> tuple[AuthService, MagicMock, MagicMock]:
    """``complete_oauth`` with doubled collaborators and a REAL ``OAuthEngine``.

    Mirrors the wiring of ``test_oauth_auto_link_claim`` — the engine is real so
    the auto-link decision under test is the production one, and only the
    transport around it is doubled.
    """
    oauth_user = OAuthUserInfo(
        provider=AuthProviderType.GOOGLE,
        provider_user_id="subject-1",
        email=EMAIL,
        display_name="Suspended User",
        email_verified=True,
    )

    user_repo = MagicMock()
    user_repo.get_by_email.return_value = existing_user
    user_repo.create.side_effect = lambda user: user

    auth_provider_repo = MagicMock()
    auth_provider_repo.get_by_provider.return_value = None  # no existing link

    oauth_engine = MagicMock(wraps=OAuthEngine())
    oauth_engine.exchange_code_for_tokens.return_value = {"access_token": "t", "id_token": ""}
    oauth_engine.extract_user_info.return_value = oauth_user

    state_store = MagicMock()
    state_store.get_and_delete.return_value = {"provider_slug": "acme", "code_verifier": "v"}

    config_repo = MagicMock()
    config_repo.get_by_slug.return_value = OidcProviderConfig(
        slug="acme",
        display_name="Acme",
        issuer_url="https://acme.example",
        client_id="cid",
        client_secret_encrypted="secret",
        enabled=True,
    )

    token_engine = MagicMock()
    token_engine.create_refresh_token.return_value = ("raw-refresh", "refresh-hash")

    service = AuthService(
        user_repo=user_repo,
        auth_provider_repo=auth_provider_repo,
        refresh_token_repo=MagicMock(),
        password_engine=MagicMock(),
        token_engine=token_engine,
        throttle_engine=MagicMock(),
        email_service=MagicMock(),
        frontend_url="https://kamerplanter.example",
        oauth_engine=oauth_engine,
        oauth_state_store=state_store,
        oidc_config_repo=config_repo,
        encryption_engine=None,
    )
    return service, auth_provider_repo, user_repo


class TestOAuthAutoLinkGatesTheDeactivatedAccount:
    def test_a_deactivated_account_is_not_auto_linked(self) -> None:
        """RED against the pre-#1528 branch, which logged the account in.

        The sibling branch (an account that already has a provider link) carried
        the check; this one did not, and nothing compared the two.
        """
        service, auth_provider_repo, _ = _oauth_service(_user(is_active=False))

        with pytest.raises(UnauthorizedError) as excinfo:
            service.complete_oauth("acme", "code", "state")

        assert excinfo.value.message == INACTIVE_MESSAGE
        assert auth_provider_repo.create.call_count == 0, (
            "a provider link was created for a suspended account; the refusal is "
            "running after _create_oauth_provider instead of before it"
        )

    def test_an_active_account_is_still_auto_linked(self) -> None:
        """The control, and the reason this gate is not simply `raise`."""
        service, auth_provider_repo, _ = _oauth_service(_user(is_active=True))

        token_pair, _, _ = service.complete_oauth("acme", "code", "state")

        assert token_pair is not None
        assert auth_provider_repo.create.call_count == 1

    def test_a_brand_new_oauth_account_is_unaffected(self) -> None:
        """No local account at all: the registration branch still runs, so the
        backstop in ``_create_tokens`` does not refuse a freshly created user."""
        service, auth_provider_repo, user_repo = _oauth_service(None)
        service._tenant_service = None

        token_pair, _, _ = service.complete_oauth("acme", "code", "state")

        assert token_pair is not None
        assert user_repo.create.call_count == 1
        assert auth_provider_repo.create.call_count == 1
