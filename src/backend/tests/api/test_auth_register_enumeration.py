"""``POST /api/v1/auth/register`` may not answer differently for a taken email (SEC-H-009).

The service-level guarantee is covered in
``tests/unit/domain/services/test_auth_service_registration_enumeration.py``.
This module asserts it where the vulnerability was actually observed: on the
wire, through the real ``UserProfileResponse`` serialisation — including
``is_platform_admin``, which the response schema carries but ``UserProfile``
does not, and which would let an attacker rank targets by privilege.

It also pins the per-IP rate limit on ``/register``. Without it an enumeration
sweep is unbounded, and a decorator that is present but not wired to the app
would look identical to one that works.
"""

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.v1.auth.router import limiter
from app.common.dependencies import get_auth_service
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.models.user import User
from app.domain.services.auth_service import AuthService

TAKEN_EMAIL = "victim@example.com"
FREE_EMAIL = "newcomer@example.com"
WRONG_PASSWORD = "attacker-guess-password-2024"
STORED_KEY = "8271634"
CREATED_KEY = "9137450"

#: Mirrors ``settings.rate_limit_auth`` ("20/minute"); the 21st call must fail.
_AUTH_LIMIT_PER_MINUTE = 20


def _stored_user() -> User:
    return User(
        _key=STORED_KEY,
        email=TAKEN_EMAIL,
        display_name="Victim Realname",
        password_hash=PasswordEngine().hash_password("the-owners-real-password-2024"),
        email_verified=True,
        is_active=False,
        avatar_url="https://cdn.example.com/avatars/victim.png",
        locale="en",
        timezone="America/New_York",
        last_login_at=datetime.now(UTC) - timedelta(days=3),
        created_at=datetime.now(UTC) - timedelta(days=900),
    )


def _auth_service() -> AuthService:
    repo = MagicMock()
    repo.get_by_email.side_effect = lambda email: _stored_user() if email.lower() == TAKEN_EMAIL else None

    def _create(user: User) -> User:
        created = user.model_copy(deep=True)
        created.key = CREATED_KEY
        created.created_at = datetime.now(UTC)
        return created

    repo.create.side_effect = _create
    return AuthService(
        user_repo=repo,
        auth_provider_repo=MagicMock(),
        refresh_token_repo=MagicMock(),
        password_engine=PasswordEngine(),
        token_engine=TokenEngine("test-secret-key-for-unit-tests-32chars!", "HS256"),
        throttle_engine=LoginThrottleEngine(),
        email_service=MagicMock(),
        frontend_url="http://localhost:5173",
    )


@pytest.fixture
def client() -> Iterator[TestClient]:
    # The per-IP window is module-level state shared with every other test that
    # touches an /auth route — reset it so neither this module nor its
    # neighbours inherit a poisoned counter.
    limiter.reset()
    with patch("app.main.get_connection"), patch("app.main.ensure_collections"):
        from app.main import app

        app.dependency_overrides[get_auth_service] = _auth_service
        try:
            yield TestClient(app, raise_server_exceptions=False)
        finally:
            app.dependency_overrides.pop(get_auth_service, None)
            limiter.reset()


def _register(client: TestClient, email: str, display_name: str) -> tuple[int, dict]:
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": WRONG_PASSWORD, "display_name": display_name},
    )
    return resp.status_code, resp.json()


def test_taken_email_answers_exactly_like_a_fresh_registration(client: TestClient) -> None:
    taken_status, taken_body = _register(client, TAKEN_EMAIL, "Attacker Chosen Name")
    fresh_status, fresh_body = _register(client, FREE_EMAIL, "Attacker Chosen Name")

    assert taken_status == fresh_status == 201
    assert taken_body.keys() == fresh_body.keys()

    # ``key``/``created_at`` differ between any two registrations and ``email``
    # echoes what was submitted; everything else must be identical.
    volatile = {"key", "email", "created_at"}
    assert {k: v for k, v in taken_body.items() if k not in volatile} == {
        k: v for k, v in fresh_body.items() if k not in volatile
    }
    assert taken_body["email"] == TAKEN_EMAIL


def test_taken_email_response_carries_nothing_from_the_stored_account(client: TestClient) -> None:
    stored = _stored_user()
    _, body = _register(client, TAKEN_EMAIL, "Attacker Chosen Name")

    assert body["key"] != stored.key
    assert body["display_name"] == "Attacker Chosen Name"
    assert body["avatar_url"] is None
    assert body["locale"] != stored.locale
    assert body["timezone"] != stored.timezone
    assert body["is_active"] is True and stored.is_active is False
    assert body["last_login_at"] is None
    # Present in the schema, never true here: the endpoint must not tell an
    # anonymous caller which addresses belong to platform admins.
    assert body["is_platform_admin"] is False


def test_register_is_rate_limited_per_ip(client: TestClient) -> None:
    """A limiter that is declared but not wired would leave the sweep unbounded."""
    statuses = [_register(client, f"probe-{i}@example.com", "Probe")[0] for i in range(_AUTH_LIMIT_PER_MINUTE + 1)]

    assert statuses[:_AUTH_LIMIT_PER_MINUTE] == [201] * _AUTH_LIMIT_PER_MINUTE
    assert statuses[-1] == 429
