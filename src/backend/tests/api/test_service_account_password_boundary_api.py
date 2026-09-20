"""``POST /users/me/password`` is reachable by an API key and must refuse one — #1559.

The unit tests next to ``AuthService`` prove the gate; this file proves the
*premise* they rest on, which is the part a service-layer double cannot show: a
``kp_``-prefixed bearer really does arrive at this route as an authenticated
principal. ``get_current_user`` resolves it through the real
``FullAuthProvider``, whose ``kp_`` branch goes to
``AuthService.authenticate_api_key`` — no account-type check anywhere on that
path, which is why the route was reachable at all.

Nothing here overrides ``get_current_user``. Overriding it would inject the
principal and assert the gate against a caller this test *declared* to exist;
what is asserted instead is that the real resolution chain produces one, from a
raw key string, and that the route then answers 403.
"""

from __future__ import annotations

import hashlib

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.users.router import router as users_router
from app.common.dependencies import get_auth_provider, get_auth_service
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError
from app.domain.engines.full_auth_provider import FullAuthProvider
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.models.auth import ApiKey
from app.domain.models.user import User
from app.domain.services.auth_service import AuthService

_RAW_KEY = "kp_" + "z" * 32
_KEY_HASH = hashlib.sha256(_RAW_KEY.encode()).hexdigest()
_NEW_PASSWORD = "attacker-chosen-password-456"


class _FakeApiKeyRepo:
    def get_by_hash(self, key_hash: str) -> ApiKey | None:
        if key_hash != _KEY_HASH:
            return None
        return ApiKey(key="ak-1", user_key="acc-1", label="ha", key_hash=_KEY_HASH, key_prefix=_RAW_KEY[:8])

    def update_last_used(self, key: str) -> None:
        return None


class _FakeUserRepo:
    """Returns the stored account and records every write.

    The account is returned by identity, so a write the service performs is
    visible to the assertions — a repo that discarded it would let a test pass
    while the hash was being persisted.
    """

    def __init__(self, user: User) -> None:
        self.user = user
        self.writes: list[dict] = []

    def get_by_key(self, key: str) -> User | None:
        return self.user if key == self.user.key else None

    def get_or_raise(self, key: str) -> User:
        assert key == self.user.key
        return self.user

    def update_fields(self, key: str, fields: dict) -> User:
        self.writes.append(fields)
        for name, value in fields.items():
            setattr(self.user, name, value)
        return self.user


def _client(account_type: str) -> tuple[TestClient, _FakeUserRepo]:
    user = User(
        _key="acc-1",
        email="daily-bot@example.org",
        display_name="Daily Bot",
        email_verified=True,
        is_active=True,
        account_type=account_type,  # type: ignore[arg-type]
    )
    user_repo = _FakeUserRepo(user)

    class _NoopRepo:
        def list_by_user(self, user_key: str) -> list:
            return []

        def create(self, model):  # noqa: ANN001, ANN202
            return model

        def revoke_all_for_user(self, user_key: str) -> int:
            return 0

    auth_service = AuthService(
        user_repo=user_repo,  # type: ignore[arg-type]
        auth_provider_repo=_NoopRepo(),  # type: ignore[arg-type]
        refresh_token_repo=_NoopRepo(),  # type: ignore[arg-type]
        password_engine=PasswordEngine(),
        token_engine=TokenEngine("test-secret-key-for-unit-tests-32chars!", "HS256"),
        throttle_engine=LoginThrottleEngine(),
        email_service=None,  # type: ignore[arg-type]
        frontend_url="http://localhost:5173",
        api_key_repo=_FakeApiKeyRepo(),  # type: ignore[arg-type]
    )

    app = FastAPI()
    app.include_router(users_router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_auth_provider] = lambda: FullAuthProvider(
        TokenEngine("test-secret-key-for-unit-tests-32chars!", "HS256"),
        user_repo,  # type: ignore[arg-type]
        auth_service,
    )
    return TestClient(app), user_repo


def test_an_api_key_reaches_the_route_and_is_refused() -> None:
    client, user_repo = _client("service")

    response = client.post(
        "/api/v1/users/me/password",
        json={"new_password": _NEW_PASSWORD},
        headers={"Authorization": f"Bearer {_RAW_KEY}"},
    )

    # 403, not 401: the key authenticated fine. A 401 here would mean the test
    # never got past resolution and would prove nothing about the gate.
    assert response.status_code == 403
    assert user_repo.writes == []
    assert user_repo.user.password_hash is None


def test_the_same_key_on_an_interactive_account_still_sets_the_password() -> None:
    """The control for the premise: resolution and the route work.

    Without this, the 403 above is equally consistent with a route that refuses
    every API-key caller for some unrelated reason.
    """
    client, user_repo = _client("user")

    response = client.post(
        "/api/v1/users/me/password",
        json={"new_password": _NEW_PASSWORD},
        headers={"Authorization": f"Bearer {_RAW_KEY}"},
    )

    assert response.status_code == 200
    assert user_repo.user.password_hash is not None
