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


# ─────────────────────────────────────────────────────────────────────
#  Per-worker E2E isolation (X-E2E-Worker-Id header)
# ─────────────────────────────────────────────────────────────────────


def _worker_user(worker_id: str) -> User:
    return User(
        _key=f"system-user-{worker_id}",
        email=f"system-user-{worker_id}@kamerplanter.example",
        display_name=f"E2E Worker {worker_id}",
        is_active=True,
    )


def _make_db_mock() -> MagicMock:
    """A MagicMock pretending to be StandardDatabase with empty collections."""
    db = MagicMock()
    coll = MagicMock()
    coll.has.return_value = False
    coll.insert.return_value = None
    db.collection.return_value = coll
    return db


class TestPerWorkerUser:
    def test_existing_worker_user_is_returned(self, system_user):
        repo = MagicMock()
        worker_user = _worker_user("gw3")
        # First lookup (system-user resolution path is not exercised here),
        # second lookup is for "system-user-gw3".  We side-effect both.
        repo.get_by_key.side_effect = lambda k: worker_user if k == "system-user-gw3" else system_user
        provider = LightAuthProvider(repo, db=_make_db_mock())

        user = provider.resolve_user(None, worker_id="gw3")
        assert user.key == "system-user-gw3"

    def test_missing_worker_user_is_auto_provisioned(self, system_user):
        # First get_by_key("system-user-gw0") → None (not yet created)
        # After provisioning a second get_by_key("system-user-gw0") → user
        repo = MagicMock()
        provisioned_user = _worker_user("gw0")
        lookups = {"calls": 0}

        def _get(key):
            if key == "system-user-gw0":
                lookups["calls"] += 1
                return None if lookups["calls"] == 1 else provisioned_user
            return system_user

        repo.get_by_key.side_effect = _get
        db = _make_db_mock()
        provider = LightAuthProvider(repo, db=db)

        user = provider.resolve_user(None, worker_id="gw0")

        assert user.key == "system-user-gw0"
        # Three collection.insert calls: user + tenant + membership
        assert db.collection.return_value.insert.call_count == 3

    def test_worker_user_is_cached(self, system_user):
        repo = MagicMock()
        wu = _worker_user("gw1")
        repo.get_by_key.side_effect = lambda k: wu if k == "system-user-gw1" else system_user
        provider = LightAuthProvider(repo, db=_make_db_mock())

        for _ in range(5):
            provider.resolve_user(None, worker_id="gw1")

        assert repo.get_by_key.call_count == 1

    def test_invalid_worker_id_falls_back_to_system_user(self, provider, system_user):
        # Header could be tampered with — only ``[a-zA-Z0-9_-]{1,32}`` is honored.
        user = provider.resolve_user(None, worker_id="../etc/passwd")
        assert user.key == system_user.key

    def test_empty_worker_id_falls_back_to_system_user(self, provider, system_user):
        user = provider.resolve_user(None, worker_id="")
        assert user.key == system_user.key

    def test_provisioning_without_db_raises(self, system_user):
        repo = MagicMock()
        repo.get_by_key.side_effect = lambda k: None if k == "system-user-gw9" else system_user
        provider = LightAuthProvider(repo)  # no db

        with pytest.raises(RuntimeError, match="not available"):
            provider.resolve_user(None, worker_id="gw9")
