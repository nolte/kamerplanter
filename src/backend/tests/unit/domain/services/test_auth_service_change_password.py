"""Changing the password consumes an outstanding reset token (SEC-011).

``request_password_reset`` mints a token that stays valid for an hour. If the
owner reacts to a suspected compromise by *changing* the password instead of
following the mailed link, that token used to survive the change — so whoever
holds it can reset the password again and take the account over. The change path
therefore clears the token in the same partial update, exactly as
``reset_password`` already does.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.common.exceptions import UnauthorizedError
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.models.user import User
from app.domain.services.auth_service import AuthService

CURRENT_PASSWORD = "secure-password-123"
NEW_PASSWORD = "another-secure-password-456"


def _user(*, with_password: bool = True) -> User:
    return User(
        _key="u1",
        email="test@example.com",
        display_name="Test User",
        password_hash=PasswordEngine().hash_password(CURRENT_PASSWORD) if with_password else "",
        email_verified=True,
        is_active=True,
        password_reset_token="outstanding-reset-token",
        password_reset_expires=datetime.now(UTC) + timedelta(hours=1),
    )


@pytest.fixture
def user_repo() -> MagicMock:
    repo = MagicMock()
    repo.get_or_raise.return_value = _user()
    return repo


@pytest.fixture
def service(user_repo: MagicMock) -> AuthService:
    return AuthService(
        user_repo=user_repo,
        auth_provider_repo=MagicMock(),
        refresh_token_repo=MagicMock(),
        password_engine=PasswordEngine(),
        token_engine=TokenEngine("test-secret-key-for-unit-tests-32chars!", "HS256"),
        throttle_engine=LoginThrottleEngine(),
        email_service=MagicMock(),
        frontend_url="http://localhost:5173",
        access_token_expire_minutes=15,
        refresh_token_expire_days=30,
        session_token_expire_hours=24,
    )


def test_change_password_clears_the_outstanding_reset_token(service: AuthService, user_repo: MagicMock) -> None:
    service.change_password("u1", CURRENT_PASSWORD, NEW_PASSWORD)

    key, fields = user_repo.update_fields.call_args[0]
    assert key == "u1"
    # The token is cleared in the *same* update as the new hash — no window in
    # which the account carries a fresh password and a usable reset token.
    assert fields["password_reset_token"] is None
    assert fields["password_reset_expires"] is None
    assert fields["password_hash"] != _user().password_hash


def test_sso_user_setting_an_initial_password_also_clears_it(
    service: AuthService,
    user_repo: MagicMock,
) -> None:
    """An SSO-only account may set its first password without the current one."""
    user_repo.get_or_raise.return_value = _user(with_password=False)

    service.change_password("u1", None, NEW_PASSWORD)

    _, fields = user_repo.update_fields.call_args[0]
    assert fields["password_reset_token"] is None
    assert fields["password_reset_expires"] is None


def test_a_rejected_change_leaves_the_token_untouched(service: AuthService, user_repo: MagicMock) -> None:
    """A wrong current password must not touch the stored credentials at all."""
    with pytest.raises(UnauthorizedError):
        service.change_password("u1", "wrong-password", NEW_PASSWORD)

    user_repo.update_fields.assert_not_called()
