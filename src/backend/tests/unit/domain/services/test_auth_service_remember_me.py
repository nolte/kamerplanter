"""Tests for remember_me / session persistence in AuthService."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.models.auth import RefreshToken
from app.domain.models.user import User
from app.domain.services.auth_service import AuthService


@pytest.fixture
def user():
    return User(
        _key="u1",
        email="test@example.com",
        display_name="Test User",
        password_hash=PasswordEngine().hash_password("secure-password-123"),
        email_verified=True,
        is_active=True,
    )


@pytest.fixture
def user_repo(user):
    repo = MagicMock()
    repo.get_by_email.return_value = user
    repo.get_by_key.return_value = user
    repo.update.return_value = user
    return repo


@pytest.fixture
def refresh_token_repo():
    repo = MagicMock()
    repo.create.side_effect = lambda t: t
    return repo


@pytest.fixture
def auth_provider_repo():
    return MagicMock()


@pytest.fixture
def email_service():
    return MagicMock()


@pytest.fixture
def service(user_repo, auth_provider_repo, refresh_token_repo, email_service):
    return AuthService(
        user_repo=user_repo,
        auth_provider_repo=auth_provider_repo,
        refresh_token_repo=refresh_token_repo,
        password_engine=PasswordEngine(),
        token_engine=TokenEngine("test-secret-key-for-unit-tests-32chars!", "HS256"),
        throttle_engine=LoginThrottleEngine(),
        email_service=email_service,
        frontend_url="http://localhost:5173",
        access_token_expire_minutes=15,
        refresh_token_expire_days=30,
        session_token_expire_hours=24,
    )


class TestLoginRememberMe:
    def test_remember_me_true_returns_persistent(self, service):
        token_pair, raw_refresh, is_persistent = service.login_local(
            "test@example.com",
            "secure-password-123",
            remember_me=True,
        )
        assert is_persistent is True
        assert token_pair.access_token
        assert raw_refresh

    def test_remember_me_false_returns_not_persistent(self, service):
        token_pair, raw_refresh, is_persistent = service.login_local(
            "test@example.com",
            "secure-password-123",
            remember_me=False,
        )
        assert is_persistent is False

    def test_remember_me_default_is_false(self, service):
        _, _, is_persistent = service.login_local(
            "test@example.com",
            "secure-password-123",
        )
        assert is_persistent is False

    def test_persistent_token_expires_in_30_days(self, service, refresh_token_repo):
        service.login_local(
            "test@example.com",
            "secure-password-123",
            remember_me=True,
        )
        created_token = refresh_token_repo.create.call_args[0][0]
        assert created_token.is_persistent is True
        # Expiry should be ~30 days from now
        expected = datetime.now(UTC) + timedelta(days=30)
        assert abs((created_token.expires_at - expected).total_seconds()) < 5

    def test_session_token_expires_in_24_hours(self, service, refresh_token_repo):
        service.login_local(
            "test@example.com",
            "secure-password-123",
            remember_me=False,
        )
        created_token = refresh_token_repo.create.call_args[0][0]
        assert created_token.is_persistent is False
        # Expiry should be ~24 hours from now
        expected = datetime.now(UTC) + timedelta(hours=24)
        assert abs((created_token.expires_at - expected).total_seconds()) < 5


class TestRefreshPreservesPersistence:
    def _make_stored_token(self, is_persistent: bool, token_engine: TokenEngine) -> tuple[str, RefreshToken]:
        raw, token_hash = token_engine.create_refresh_token()
        return raw, RefreshToken(
            _key="rt1",
            user_key="u1",
            token_hash=token_hash,
            is_persistent=is_persistent,
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )

    def test_refresh_preserves_persistent_flag(self, service, refresh_token_repo):
        token_engine = TokenEngine("test-secret-key-for-unit-tests-32chars!", "HS256")
        raw, stored = self._make_stored_token(True, token_engine)
        refresh_token_repo.get_by_hash.return_value = stored

        _, _, is_persistent = service.refresh_tokens(raw)
        assert is_persistent is True

        created_token = refresh_token_repo.create.call_args[0][0]
        assert created_token.is_persistent is True

    def test_refresh_preserves_session_flag(self, service, refresh_token_repo):
        token_engine = TokenEngine("test-secret-key-for-unit-tests-32chars!", "HS256")
        raw, stored = self._make_stored_token(False, token_engine)
        refresh_token_repo.get_by_hash.return_value = stored

        _, _, is_persistent = service.refresh_tokens(raw)
        assert is_persistent is False

        created_token = refresh_token_repo.create.call_args[0][0]
        assert created_token.is_persistent is False
