"""#1885 — the e-mail channel mails the account's confirmed address, nothing else.

Every test drives the real dispatch path: the real ``NotificationEngine`` and
the real ``EmailNotificationChannel`` over a recording mail adapter, and asserts
on the recipient the adapter actually received. The fakes reject what the real
collaborators reject: the preference repo stores ``NotificationPreferences``
objects (so the model validator applies on write and read), and the user repo
returns real ``User`` models.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.api.v1.notifications.schemas import NotificationPreferencesRequest
from app.data_access.external.email_notification_channel import EmailNotificationChannel
from app.domain.engines.notification_channel_registry import NotificationChannelRegistry
from app.domain.engines.notification_engine import NotificationEngine
from app.domain.interfaces.email_service import IEmailService
from app.domain.models.notification import (
    ChannelPreference,
    Notification,
    NotificationPreferences,
    NotificationUrgency,
)
from app.domain.models.user import User
from app.domain.services.notification_service import NotificationService

ACCOUNT = "owner@example.org"
STRANGER = "victim@stranger.example"


class _RecordingMail(IEmailService):
    def __init__(self) -> None:
        self.recipients: list[str] = []

    def send_verification_email(self, to_email: str, token: str, frontend_url: str) -> None: ...
    def send_password_reset_email(self, to_email: str, token: str, frontend_url: str) -> None: ...

    def send_notification_email(self, to_email: str, subject: str, html_body: str) -> None:
        self.recipients.append(to_email)


class _PrefRepo:
    """Stores what the route builds, returns it through the model like a database round trip."""

    def __init__(self) -> None:
        self.stored: dict | None = None

    def get_by_user(self, user_key: str) -> NotificationPreferences | None:
        if self.stored is None:
            return None
        return NotificationPreferences(**self.stored)

    def upsert(self, preferences: NotificationPreferences) -> NotificationPreferences:
        self.stored = preferences.model_dump(by_alias=True)
        return NotificationPreferences(**self.stored)


class _UserRepo:
    def __init__(self, user: User | None) -> None:
        self._user = user

    def get_by_key(self, key: str) -> User | None:
        return self._user


def _user(**kw) -> User:
    base = {
        "_key": "u1",
        "email": ACCOUNT,
        "display_name": "Owner",
        "email_verified": True,
        "email_confirmed_at": datetime.now(UTC),
    }
    base.update(kw)
    return User(**base)


@pytest.fixture
def mail() -> _RecordingMail:
    return _RecordingMail()


@pytest.fixture(autouse=True)
def _registry(mail):
    NotificationChannelRegistry.register(EmailNotificationChannel(mail))
    yield
    NotificationChannelRegistry.unregister("email")


def _build(user: User | None, prefs_repo: _PrefRepo | None = None):
    prefs_repo = prefs_repo or _PrefRepo()
    notifications = MagicMock()
    notifications.create.side_effect = lambda n: n
    notifications.list_for_user_since.return_value = [_notification()]
    redis = MagicMock()
    redis.get.return_value = None
    engine = NotificationEngine(
        notification_repo=notifications,
        preference_repo=prefs_repo,
        channel_registry=NotificationChannelRegistry,
        redis_client=redis,
        user_repo=_UserRepo(user),
    )
    engine._is_quiet_hours = lambda prefs: False  # type: ignore[method-assign]
    service = NotificationService(engine=engine, notification_repo=notifications, preference_repo=prefs_repo)
    return engine, service, prefs_repo


def _notification() -> Notification:
    return Notification(
        notification_type="care.watering",
        title="Water the monstera",
        body="Due today",
        urgency=NotificationUrgency.NORMAL,
    )


def _put_preferences_as_the_route_does(service: NotificationService, config: dict) -> None:
    """The PUT /preferences body -> model -> service, exactly as ``update_preferences`` does."""
    body = NotificationPreferencesRequest(channels={"email": ChannelPreference(enabled=True, config=config)})
    prefs = NotificationPreferences(user_key="u1", channels=body.channels)
    service.update_preferences("u1", prefs, tenant_key="t1")


async def test_typed_in_recipient_is_not_mailed_the_account_address_is(mail):
    engine, service, _ = _build(_user())
    _put_preferences_as_the_route_does(service, {"email": STRANGER})

    result = await engine.notify("u1", "t1", _notification())

    assert result["channels_sent"] == ["email"]
    assert mail.recipients == [ACCOUNT]


async def test_unverified_account_gets_nothing_even_with_a_typed_in_recipient(mail):
    engine, service, _ = _build(_user(email_verified=False))
    _put_preferences_as_the_route_does(service, {"email": STRANGER})

    result = await engine.notify("u1", "t1", _notification())

    assert mail.recipients == []
    assert result["channels_failed"] == ["email"]


@pytest.mark.parametrize(
    "user",
    [
        None,
        _user(is_active=False),
        _user(account_type="service"),
    ],
    ids=["no-account", "inactive", "service-account"],
)
async def test_accounts_that_cannot_receive_mail_get_nothing(mail, user):
    engine, service, _ = _build(user)
    _put_preferences_as_the_route_does(service, {})

    await engine.notify("u1", "t1", _notification())

    assert mail.recipients == []


async def test_a_legacy_stored_row_with_a_free_text_address_is_not_mailed(mail):
    """A row written before #1885: the address sits in the database; it must not be dialled."""
    repo = _PrefRepo()
    repo.stored = {
        "user_key": "u1",
        "channels": {"email": {"enabled": True, "priority": 0, "config": {"email": STRANGER, "address": STRANGER}}},
    }
    engine, _, _ = _build(_user(email_verified=False), repo)

    await engine.notify("u1", "t1", _notification())

    assert mail.recipients == []


async def test_legacy_row_for_a_verified_account_mails_the_account_not_the_stored_address(mail):
    repo = _PrefRepo()
    repo.stored = {
        "user_key": "u1",
        "channels": {"email": {"enabled": True, "priority": 0, "config": {"email": STRANGER}}},
    }
    engine, _, _ = _build(_user(), repo)

    await engine.notify("u1", "t1", _notification())

    assert mail.recipients == [ACCOUNT]


async def test_preferences_never_hold_a_typed_in_recipient(mail):
    _, service, repo = _build(_user())
    _put_preferences_as_the_route_does(
        service, {"email": STRANGER, "address": STRANGER, "Email": STRANGER, "to": STRANGER, "digest": True}
    )

    assert repo.stored is not None
    assert repo.stored["channels"]["email"]["config"] == {"digest": True}
    assert service.get_preferences("u1").channels["email"].config == {"digest": True}


async def test_digest_goes_to_the_account_address_only(mail):
    _, service, _ = _build(_user())
    _put_preferences_as_the_route_does(service, {"email": STRANGER, "digest": True})

    result = await service.send_email_digest("u1", datetime.now(UTC) - timedelta(hours=24))

    assert result["status"] == "sent"
    assert mail.recipients == [ACCOUNT]


async def test_digest_for_an_unverified_account_sends_nothing(mail):
    _, service, _ = _build(_user(email_verified=False))
    _put_preferences_as_the_route_does(service, {"email": STRANGER, "digest": True})

    result = await service.send_email_digest("u1", datetime.now(UTC) - timedelta(hours=24))

    assert result["status"] == "no_confirmed_address"
    assert mail.recipients == []


async def test_test_notification_goes_to_the_account_address_only(mail):
    _, service, _ = _build(_user())
    _put_preferences_as_the_route_does(service, {"email": STRANGER})

    result = await service.send_test("u1", "t1", "email")

    assert result["success"] is True
    assert mail.recipients == [ACCOUNT]


async def test_test_notification_for_an_unverified_account_sends_nothing(mail):
    _, service, _ = _build(_user(email_verified=False))
    _put_preferences_as_the_route_does(service, {"email": STRANGER})

    result = await service.send_test("u1", "t1", "email")

    assert result["success"] is False
    assert mail.recipients == []


async def test_a_failing_account_lookup_sends_no_mail_and_does_not_abort_other_channels(mail):
    class _Boom:
        def get_by_key(self, key: str):
            raise RuntimeError("database unavailable")

    engine, service, _ = _build(_user())
    engine._user_repo = _Boom()  # type: ignore[assignment]
    _put_preferences_as_the_route_does(service, {})

    result = await engine.notify("u1", "t1", _notification())

    assert mail.recipients == []
    assert result["channels_failed"] == ["email"]


async def test_verified_flag_without_the_proof_gets_nothing_even_with_a_typed_in_recipient(mail):
    """#1948 — ``email_verified`` is also stamped by a registration made with verification off."""
    engine, service, _ = _build(_user(email_confirmed_at=None))
    _put_preferences_as_the_route_does(service, {"email": STRANGER})

    result = await engine.notify("u1", "t1", _notification())

    assert result["channels_sent"] == []
    assert mail.recipients == []
    assert engine.resolve_email_recipient("u1") is None
