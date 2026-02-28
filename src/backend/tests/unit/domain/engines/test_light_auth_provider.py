from unittest.mock import MagicMock

import pytest

from app.domain.engines.light_auth_provider import LightAuthProvider
from app.domain.models.user import User


@pytest.fixture
def system_user():
    return User(
        _key="system-user",
        email="system@kamerplanter.example",
        display_name="Gaertner",
        is_active=True,
    )


@pytest.fixture
def user_repo(system_user):
    repo = MagicMock()
    repo.get_by_key.return_value = system_user
    return repo


@pytest.fixture
def provider(user_repo):
    return LightAuthProvider(user_repo)


class TestResolveUser:
    def test_returns_system_user(self, provider, system_user):
        user = provider.resolve_user(None)
        assert user.key == system_user.key
        assert user.email == "system@kamerplanter.example"

    def test_ignores_authorization_header(self, provider, system_user):
        user = provider.resolve_user("Bearer some-jwt-token")
        assert user.key == system_user.key

    def test_caches_user_after_first_call(self, provider, user_repo):
        provider.resolve_user(None)
        provider.resolve_user(None)
        provider.resolve_user(None)
        user_repo.get_by_key.assert_called_once_with("system-user")

    def test_raises_if_system_user_missing(self):
        repo = MagicMock()
        repo.get_by_key.return_value = None
        p = LightAuthProvider(repo)
        with pytest.raises(RuntimeError, match="System user not found"):
            p.resolve_user(None)


class TestResolveUserOptional:
    def test_never_returns_none(self, provider, system_user):
        user = provider.resolve_user_optional(None)
        assert user is not None
        assert user.key == system_user.key

    def test_returns_same_as_resolve_user(self, provider):
        u1 = provider.resolve_user(None)
        u2 = provider.resolve_user_optional("Bearer anything")
        assert u1.key == u2.key


class TestIsAuthenticationRequired:
    def test_returns_false(self, provider):
        assert provider.is_authentication_required() is False
