"""#1948 — an account registered with verification off gets no notification mail until it confirms.

``REQUIRE_EMAIL_VERIFICATION=false`` makes ``POST /auth/register`` stamp
``email_verified`` without any confirmation. The e-mail notification channel
(#1885) mails only a *confirmed* address, so before this change the operator's
sender could be aimed at an address the registrant does not own. Flipping the
setting to ``true`` afterwards does not repair it: the stored flag stays set.

The test drives the real path end to end: the real route, the real
``AuthService`` over a stateful repository that behaves like the store (a write
is visible to the next read, ``update_fields`` merges), then the real
``NotificationEngine`` + ``EmailNotificationChannel`` over a recording mail
adapter. The assertion is on the recipient the adapter actually received.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.common.dependencies import get_auth_service
from app.data_access.external.email_notification_channel import EmailNotificationChannel
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.notification_channel_registry import NotificationChannelRegistry
from app.domain.engines.notification_engine import NotificationEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.interfaces.email_service import IEmailService
from app.domain.models.notification import (
    ChannelPreference,
    Notification,
    NotificationPreferences,
    NotificationUrgency,
)
from app.domain.models.user import User
from app.domain.services.auth_service import AuthService

ADDRESS = "newcomer@example.com"
PASSWORD = "Registrant-Chosen-Password-2024!"


class _StatefulUserRepo:
    """The slice of the user store registration, verification and the resend path use."""

    def __init__(self) -> None:
        self.rows: dict[str, User] = {}

    def get_by_key(self, key: str) -> User | None:
        return self.rows.get(key)

    def get_by_email(self, email: str) -> User | None:
        return next((u for u in self.rows.values() if u.email.lower() == email.lower()), None)

    def get_by_email_verification_token(self, token: str) -> User | None:
        return next((u for u in self.rows.values() if u.email_verification_token == token), None)

    def create(self, user: User) -> User:
        created = user.model_copy(deep=True)
        created.key = f"u{len(self.rows) + 1}"
        created.created_at = datetime.now(UTC)
        self.rows[created.key] = created
        return created

    def update_fields(self, key: str, fields: dict) -> User | None:
        # Like the real repository the merged model is validated, so a value the
        # model cannot hold is refused here too.
        merged = User.model_validate({**self.rows[key].model_dump(by_alias=True), **fields})
        self.rows[key] = merged
        return merged


class _RecordingMail(IEmailService):
    def __init__(self) -> None:
        self.recipients: list[str] = []
        self.verification: list[tuple[str, str]] = []

    def send_verification_email(self, to_email: str, token: str, frontend_url: str) -> None:
        self.verification.append((to_email, token))

    def send_password_reset_email(self, to_email: str, token: str, frontend_url: str) -> None: ...

    def send_notification_email(self, to_email: str, subject: str, html_body: str) -> None:
        self.recipients.append(to_email)


class _PrefRepo:
    def get_by_user(self, user_key: str) -> NotificationPreferences | None:
        return NotificationPreferences(user_key=user_key, channels={"email": ChannelPreference(enabled=True)})


def _service(repo: _StatefulUserRepo, mail: _RecordingMail, *, require: bool) -> AuthService:
    return AuthService(
        user_repo=repo,  # type: ignore[arg-type]
        auth_provider_repo=MagicMock(),
        refresh_token_repo=MagicMock(),
        password_engine=PasswordEngine(),
        token_engine=TokenEngine("test-secret-key-for-unit-tests-32chars!", "HS256"),
        throttle_engine=LoginThrottleEngine(),
        email_service=mail,
        frontend_url="http://localhost:5173",
        tenant_service=MagicMock(),
        require_email_verification=require,
    )


@pytest.fixture
def repo() -> _StatefulUserRepo:
    return _StatefulUserRepo()


@pytest.fixture
def mail() -> _RecordingMail:
    return _RecordingMail()


@pytest.fixture(autouse=True)
def _email_channel(mail: _RecordingMail) -> Iterator[None]:
    NotificationChannelRegistry.register(EmailNotificationChannel(mail))
    yield
    NotificationChannelRegistry.unregister("email")


def _client(service: AuthService) -> Iterator[TestClient]:
    with patch("app.main.get_connection"), patch("app.main.ensure_collections"):
        from app.main import app

        app.dependency_overrides[get_auth_service] = lambda: service
        try:
            yield TestClient(app, raise_server_exceptions=False)
        finally:
            app.dependency_overrides.pop(get_auth_service, None)


def _register(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": ADDRESS, "password": PASSWORD, "display_name": "Newcomer"},
    )
    assert response.status_code == 201


async def _dispatch(repo: _StatefulUserRepo, user_key: str) -> None:
    """Dispatch one notification through the real engine and e-mail channel."""
    notifications = MagicMock()
    notifications.create.side_effect = lambda n: n
    redis = MagicMock()
    redis.get.return_value = None
    engine = NotificationEngine(
        notification_repo=notifications,
        preference_repo=_PrefRepo(),
        channel_registry=NotificationChannelRegistry,
        redis_client=redis,
        user_repo=repo,
    )
    engine._is_quiet_hours = lambda prefs: False  # type: ignore[method-assign]
    await engine.notify(
        user_key,
        "t1",
        Notification(
            notification_type="care.watering",
            title="Water the monstera",
            body="Due today",
            urgency=NotificationUrgency.NORMAL,
        ),
    )


async def test_registered_with_verification_off_receives_no_notification_mail(
    repo: _StatefulUserRepo, mail: _RecordingMail
) -> None:
    for client in _client(_service(repo, mail, require=False)):
        _register(client)
    (key,) = repo.rows

    assert repo.rows[key].email_verified is True  # the setting stamps it: that is the premise
    await _dispatch(repo, key)

    assert mail.recipients == []


async def test_flipping_the_setting_to_true_does_not_confirm_the_address(
    repo: _StatefulUserRepo, mail: _RecordingMail
) -> None:
    for client in _client(_service(repo, mail, require=False)):
        _register(client)
    (key,) = repo.rows

    for client in _client(_service(repo, mail, require=True)):
        assert client.post("/api/v1/auth/resend-verification", json={"email": ADDRESS}).status_code == 202
        await _dispatch(repo, key)
        assert mail.recipients == []  # still unconfirmed: the stored flag proves nothing

        ((to_email, token),) = mail.verification  # the way to confirm is the link
        assert to_email == ADDRESS
        assert client.post("/api/v1/auth/verify-email", json={"token": token}).status_code == 200

    await _dispatch(repo, key)
    assert mail.recipients == [ADDRESS]


async def test_registered_with_verification_on_receives_mail_after_the_link(
    repo: _StatefulUserRepo, mail: _RecordingMail
) -> None:
    for client in _client(_service(repo, mail, require=True)):
        _register(client)
        (key,) = repo.rows
        await _dispatch(repo, key)
        assert mail.recipients == []  # unverified: nothing

        ((_, token),) = mail.verification
        assert client.post("/api/v1/auth/verify-email", json={"token": token}).status_code == 200

    await _dispatch(repo, key)
    assert mail.recipients == [ADDRESS]


async def test_the_two_origins_are_indistinguishable_by_the_flag_and_the_token_fields() -> None:
    """Why the v0080 backfill cannot tell a link-confirmed account from an unconfirmed one.

    Both end as ``email_verified`` with no token and no expiry; only
    ``email_confirmed_at`` (absent before #1948) separates them.
    """
    off_repo, on_repo = _StatefulUserRepo(), _StatefulUserRepo()
    off_mail, on_mail = _RecordingMail(), _RecordingMail()
    for client in _client(_service(off_repo, off_mail, require=False)):
        _register(client)
    for client in _client(_service(on_repo, on_mail, require=True)):
        _register(client)
        ((_, token),) = on_mail.verification
        assert client.post("/api/v1/auth/verify-email", json={"token": token}).status_code == 200

    def shape(user: User) -> tuple[bool, str | None, datetime | None]:
        return (user.email_verified, user.email_verification_token, user.email_verification_expires)

    (off,), (on,) = off_repo.rows.values(), on_repo.rows.values()
    assert shape(off) == shape(on) == (True, None, None)
    assert off.email_confirmed_at is None
    assert on.email_confirmed_at is not None
