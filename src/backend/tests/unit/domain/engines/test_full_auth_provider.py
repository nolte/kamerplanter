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
        user = provider.resolve_user("Bearer valid-jwt-token", client_ip=None)
        assert user.key == active_user.key

    def test_missing_header_raises(self, provider):
        with pytest.raises(UnauthorizedError, match="Missing or invalid"):
            provider.resolve_user(None, client_ip=None)

    def test_empty_header_raises(self, provider):
        with pytest.raises(UnauthorizedError, match="Missing or invalid"):
            provider.resolve_user("", client_ip=None)

    def test_non_bearer_header_raises(self, provider):
        with pytest.raises(UnauthorizedError, match="Missing or invalid"):
            provider.resolve_user("Basic dXNlcjpwYXNz", client_ip=None)

    def test_invalid_jwt_raises(self, provider, token_engine):
        token_engine.decode_access_token.side_effect = ValueError("Token expired")
        with pytest.raises(UnauthorizedError, match="Token expired"):
            provider.resolve_user("Bearer expired-token", client_ip=None)

    def test_inactive_user_raises(self, provider, user_repo):
        inactive = User(
            _key="user-123",
            email="test@example.com",
            display_name="Test",
            is_active=False,
        )
        user_repo.get_by_key.return_value = inactive
        with pytest.raises(UnauthorizedError, match="not found or inactive"):
            provider.resolve_user("Bearer valid-token", client_ip=None)

    def test_api_key_delegates_to_auth_service(self, provider, auth_service, active_user):
        user = provider.resolve_user("Bearer kp_test-api-key-12345", client_ip=None)
        auth_service.authenticate_api_key.assert_called_once_with("kp_test-api-key-12345", client_ip=None)
        assert user.key == active_user.key

    def test_api_key_invalid_raises(self, provider, auth_service):
        auth_service.authenticate_api_key.return_value = None
        with pytest.raises(UnauthorizedError, match="Invalid or revoked API key"):
            provider.resolve_user("Bearer kp_invalid-key", client_ip=None)


class TestResolveUserOptional:
    def test_returns_none_without_header(self, provider):
        assert provider.resolve_user_optional(None, client_ip=None) is None

    def test_returns_none_with_empty_header(self, provider):
        assert provider.resolve_user_optional("", client_ip=None) is None

    def test_returns_user_with_valid_jwt(self, provider, active_user):
        user = provider.resolve_user_optional("Bearer valid-jwt", client_ip=None)
        assert user is not None
        assert user.key == active_user.key

    def test_returns_none_on_invalid_jwt(self, provider, token_engine):
        token_engine.decode_access_token.side_effect = ValueError("bad")
        assert provider.resolve_user_optional("Bearer bad-token", client_ip=None) is None

    def test_api_key_optional(self, provider, active_user):
        user = provider.resolve_user_optional("Bearer kp_test-key", client_ip=None)
        assert user is not None
        assert user.key == active_user.key


class TestIsAuthenticationRequired:
    def test_returns_true(self, provider):
        assert provider.is_authentication_required() is True


class TestRevokedAccessTokens:
    """#2116 (MT-019): an access token minted before a revocation stops resolving at once.

    Against the real ``TokenEngine``, so the ``gen`` claim is the one the minting
    path writes and the decoding path reads — not a hand-built payload.
    """

    @pytest.fixture
    def engine(self):
        from app.domain.engines.token_engine import TokenEngine

        return TokenEngine("s" * 64)

    def _provider(self, engine, user: User) -> FullAuthProvider:
        repo = MagicMock()
        repo.get_by_key.return_value = user
        return FullAuthProvider(engine, repo, MagicMock())

    def test_a_token_of_the_current_generation_resolves(self, engine, active_user):
        active_user.access_token_generation = 3
        token = engine.create_access_token("user-123", generation=3).access_token

        assert self._provider(engine, active_user).resolve_user(f"Bearer {token}", client_ip=None) is active_user

    def test_a_token_minted_before_the_last_revocation_is_refused(self, engine, active_user):
        token = engine.create_access_token("user-123", generation=3).access_token
        active_user.access_token_generation = 4  # logout everywhere / revoke / password change happened since

        provider = self._provider(engine, active_user)
        with pytest.raises(UnauthorizedError, match="revoked"):
            provider.resolve_user(f"Bearer {token}", client_ip=None)
        assert provider.resolve_user_optional(f"Bearer {token}", client_ip=None) is None

    def test_a_token_minted_before_the_claim_existed_counts_as_generation_zero(self, engine, active_user):
        """Tokens issued by the previous release carry no ``gen``: valid until a revocation, then refused."""
        import time

        from authlib.jose import JsonWebToken

        now = int(time.time())
        legacy = JsonWebToken(["HS256"]).encode(
            {"alg": "HS256"},
            {"sub": "user-123", "exp": now + 900, "iat": now, "jti": "j", "type": "access"},
            "s" * 64,
        )
        bearer = f"Bearer {legacy.decode()}"

        assert self._provider(engine, active_user).resolve_user(bearer, client_ip=None) is active_user
        active_user.access_token_generation = 1
        with pytest.raises(UnauthorizedError):
            self._provider(engine, active_user).resolve_user(bearer, client_ip=None)
