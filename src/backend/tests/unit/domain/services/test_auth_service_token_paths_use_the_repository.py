"""#1556 — ``verify_email`` and ``reset_password`` drive through ``IUserRepository``.

Both used to execute AQL against ``self._user_repo._db``. #1556's second bullet
is the one this file answers: *the doubles cannot model it* — substituting
``IUserRepository`` got a ``MagicMock`` for ``_db`` too, so neither path could be
driven without also building an AQL cursor double.

**The fake here is a real subclass of ``IUserRepository``, not a ``MagicMock``,
and that is the point.** ``MagicMock`` answers every attribute, so a service test
written against one passes whether or not the repository ever grew the method —
it would certify the seam while the seam did not exist (the ``_FakeTenantRepo``
vacuum of #1155). Python's ABC refuses to instantiate a subclass that has not
implemented every abstract method, so this fake stops compiling the moment the
interface and the service disagree.

Red-first: against the pre-#1556 service both ``TestVerifyEmail`` and
``TestResetPassword`` fail — the service never calls the lookup, it reaches
``self._user_repo._db``, and ``_FakeUserRepository`` has no ``_db``.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.common.exceptions import InvalidTokenError
from app.common.types import UserKey
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.interfaces.user_repository import IUserRepository
from app.domain.models.user import User
from app.domain.services.auth_service import AuthService

VERIFY_TOKEN = "verify-token"  # noqa: S105 — a fixture value, not a credential
RESET_TOKEN = "reset-token"  # noqa: S105 — a fixture value, not a credential
NEW_PASSWORD = "a-sufficiently-long-new-password-1"


class _FakeUserRepository(IUserRepository):
    """Every abstract method implemented; the two lookups answer from one user.

    ``update_fields`` is read-modify-write, mirroring
    ``ArangoUserRepository.update_fields`` (#1018) — it applies the named fields
    onto the stored model and returns it. The concurrency window that shape
    carries is unchanged by #1556: the write path was already ``update_fields``
    before and after, and only the *read* moved behind the repository.
    """

    def __init__(self, user: User | None) -> None:
        self._user = user
        self.calls: list[tuple[str, str]] = []
        self.updates: list[dict] = []

    # -- the two lookups #1556 added ------------------------------------- #
    def get_by_email_verification_token(self, token: str) -> User | None:
        self.calls.append(("get_by_email_verification_token", token))
        if self._user is not None and self._user.email_verification_token == token:
            return self._user
        return None

    def get_by_password_reset_token(self, token: str) -> User | None:
        self.calls.append(("get_by_password_reset_token", token))
        if self._user is not None and self._user.password_reset_token == token:
            return self._user
        return None

    # -- the rest of the interface --------------------------------------- #
    def get_by_key(self, key: UserKey) -> User | None:
        return self._user

    def get_or_raise(self, key: UserKey) -> User:
        assert self._user is not None
        return self._user

    def get_by_email(self, email: str) -> User | None:
        return self._user

    def create(self, user: User) -> User:
        return user

    def update(self, key: UserKey, user: User) -> User:
        self._user = user
        return user

    def update_fields(self, key: UserKey, fields: dict) -> User | None:
        if self._user is None:
            return None
        self.updates.append(dict(fields))
        for name, value in fields.items():
            setattr(self._user, name, value)
        return self._user

    def delete(self, key: UserKey) -> bool:
        return True

    def list_all(self) -> list[User]:
        return [self._user] if self._user else []

    def count(self, *, active_only: bool = False) -> int:
        return 1 if self._user else 0

    def get_unverified_before(self, cutoff_iso: str) -> list[User]:
        return []


def _user(**overrides) -> User:
    fields = {
        "_key": "u-1",
        "email": "person@example.org",
        "display_name": "Person",
        "password_hash": "$2b$12$notarealhash",
        "is_active": True,
        "account_type": "user",
    }
    fields.update(overrides)
    return User(**fields)


def _service(repo: _FakeUserRepository) -> AuthService:
    refresh_token_repo = MagicMock()
    refresh_token_repo.create.side_effect = lambda token: token
    auth_provider_repo = MagicMock()
    auth_provider_repo.list_by_user.return_value = []
    return AuthService(
        user_repo=repo,
        auth_provider_repo=auth_provider_repo,
        refresh_token_repo=refresh_token_repo,
        password_engine=PasswordEngine(),
        token_engine=TokenEngine("test-secret-key-for-unit-tests-32chars!", "HS256"),
        throttle_engine=LoginThrottleEngine(),
        email_service=MagicMock(),
        frontend_url="http://localhost:5173",
    )


class TestTheFakeIsAdequate:
    def test_a_repository_missing_a_lookup_cannot_be_instantiated(self) -> None:
        """The ABC, not this file's discipline, is what keeps the fake honest."""

        class _Missing(IUserRepository):  # type: ignore[misc]
            """Implements nothing; the ABC must name the lookups among the gaps."""

        with pytest.raises(TypeError, match="get_by_password_reset_token"):
            _Missing()  # type: ignore[abstract]

    def test_the_fake_holds_no_database_handle(self) -> None:
        """If the service still reached ``_repo._db`` this would be an AttributeError."""
        assert not hasattr(_FakeUserRepository(None), "_db")


class TestVerifyEmail:
    def test_the_verification_token_is_looked_up_through_the_repository(self) -> None:
        user = _user(
            email_verified=False,
            email_verification_token=VERIFY_TOKEN,
            email_verification_expires=datetime.now(UTC) + timedelta(hours=1),
        )
        repo = _FakeUserRepository(user)

        profile = _service(repo).verify_email(VERIFY_TOKEN)

        assert repo.calls == [("get_by_email_verification_token", VERIFY_TOKEN)]
        assert profile.email_verified is True

    def test_the_token_is_burned_by_the_same_update_fields_write_as_before(self) -> None:
        """#1556 moved the READ. The write path is untouched (#1018/#1525)."""
        user = _user(email_verified=False, email_verification_token=VERIFY_TOKEN)
        repo = _FakeUserRepository(user)

        _service(repo).verify_email(VERIFY_TOKEN)

        assert repo.updates == [
            {
                "email_verified": True,
                "email_verification_token": None,
                "email_verification_expires": None,
            }
        ]

    def test_an_unknown_token_is_refused(self) -> None:
        repo = _FakeUserRepository(_user(email_verification_token="other"))
        with pytest.raises(InvalidTokenError):
            _service(repo).verify_email(VERIFY_TOKEN)
        assert repo.updates == []

    def test_an_expired_token_is_refused(self) -> None:
        user = _user(
            email_verified=False,
            email_verification_token=VERIFY_TOKEN,
            email_verification_expires=datetime.now(UTC) - timedelta(hours=1),
        )
        repo = _FakeUserRepository(user)
        with pytest.raises(InvalidTokenError):
            _service(repo).verify_email(VERIFY_TOKEN)
        assert repo.updates == []


class TestResetPassword:
    def test_the_reset_token_is_looked_up_through_the_repository(self) -> None:
        user = _user(
            password_reset_token=RESET_TOKEN,
            password_reset_expires=datetime.now(UTC) + timedelta(hours=1),
        )
        repo = _FakeUserRepository(user)

        _service(repo).reset_password(RESET_TOKEN, NEW_PASSWORD)

        assert ("get_by_password_reset_token", RESET_TOKEN) in repo.calls
        written = repo.updates[-1]
        assert written["password_reset_token"] is None
        assert written["password_reset_expires"] is None
        assert written["failed_login_attempts"] == 0
        assert written["locked_until"] is None
        assert written["password_hash"] != "$2b$12$notarealhash"

    def test_an_unknown_token_is_refused(self) -> None:
        repo = _FakeUserRepository(_user(password_reset_token="other"))
        with pytest.raises(InvalidTokenError):
            _service(repo).reset_password(RESET_TOKEN, NEW_PASSWORD)
        assert repo.updates == []

    def test_an_expired_token_is_refused(self) -> None:
        user = _user(
            password_reset_token=RESET_TOKEN,
            password_reset_expires=datetime.now(UTC) - timedelta(hours=1),
        )
        repo = _FakeUserRepository(user)
        with pytest.raises(InvalidTokenError):
            _service(repo).reset_password(RESET_TOKEN, NEW_PASSWORD)
        assert repo.updates == []
