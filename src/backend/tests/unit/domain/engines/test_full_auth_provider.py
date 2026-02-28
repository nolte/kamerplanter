from unittest.mock import MagicMock

import pytest

from app.common.exceptions import UnauthorizedError
from app.domain.engines.full_auth_provider import FullAuthProvider
from app.domain.models.auth import TokenPayload
from app.domain.models.user import User


@pytest.fixture
def active_user():
    return User(
        _key="user-123",
        email="test@example.com",
        display_name="Test User",
        is_active=True,
    )


@pytest.fixture
def token_engine():
    engine = MagicMock()
    engine.decode_access_token.return_value = TokenPayload(
        sub="user-123",
        email="test@example.com",
        display_name="Test User",
        jti="test-jti",
        exp=9999999999,
        iat=1000000000,
    )
    return engine


@pytest.fixture
def user_repo(active_user):
    repo = MagicMock()
    repo.get_by_key.return_value = active_user
    return repo


@pytest.fixture
def auth_service(active_user):
    svc = MagicMock()
    svc.authenticate_api_key.return_value = active_user
    return svc


@pytest.fixture
def provider(token_engine, user_repo, auth_service):
    return FullAuthProvider(token_engine, user_repo, auth_service)


class TestResolveUser:
    def test_valid_jwt_returns_user(self, provider, active_user):
        user = provider.resolve_user("Bearer valid-jwt-token")
        assert user.key == active_user.key

    def test_missing_header_raises(self, provider):
        with pytest.raises(UnauthorizedError, match="Missing or invalid"):
            provider.resolve_user(None)

    def test_empty_header_raises(self, provider):
        with pytest.raises(UnauthorizedError, match="Missing or invalid"):
            provider.resolve_user("")

    def test_non_bearer_header_raises(self, provider):
        with pytest.raises(UnauthorizedError, match="Missing or invalid"):
            provider.resolve_user("Basic dXNlcjpwYXNz")

    def test_invalid_jwt_raises(self, provider, token_engine):
        token_engine.decode_access_token.side_effect = ValueError("Token expired")
        with pytest.raises(UnauthorizedError, match="Token expired"):
            provider.resolve_user("Bearer expired-token")

    def test_inactive_user_raises(self, provider, user_repo):
        inactive = User(
            _key="user-123",
            email="test@example.com",
            display_name="Test",
            is_active=False,
        )
        user_repo.get_by_key.return_value = inactive
        with pytest.raises(UnauthorizedError, match="not found or inactive"):
            provider.resolve_user("Bearer valid-token")

    def test_api_key_delegates_to_auth_service(self, provider, auth_service, active_user):
        user = provider.resolve_user("Bearer kp_test-api-key-12345")
        auth_service.authenticate_api_key.assert_called_once_with("kp_test-api-key-12345")
        assert user.key == active_user.key

    def test_api_key_invalid_raises(self, provider, auth_service):
        auth_service.authenticate_api_key.return_value = None
        with pytest.raises(UnauthorizedError, match="Invalid or revoked API key"):
            provider.resolve_user("Bearer kp_invalid-key")


class TestResolveUserOptional:
    def test_returns_none_without_header(self, provider):
        assert provider.resolve_user_optional(None) is None

    def test_returns_none_with_empty_header(self, provider):
        assert provider.resolve_user_optional("") is None

    def test_returns_user_with_valid_jwt(self, provider, active_user):
        user = provider.resolve_user_optional("Bearer valid-jwt")
        assert user is not None
        assert user.key == active_user.key

    def test_returns_none_on_invalid_jwt(self, provider, token_engine):
        token_engine.decode_access_token.side_effect = ValueError("bad")
        assert provider.resolve_user_optional("Bearer bad-token") is None

    def test_api_key_optional(self, provider, active_user):
        user = provider.resolve_user_optional("Bearer kp_test-key")
        assert user is not None
        assert user.key == active_user.key


class TestIsAuthenticationRequired:
    def test_returns_true(self, provider):
        assert provider.is_authentication_required() is True
