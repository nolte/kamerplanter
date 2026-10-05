"""MT-015 (#2112): a Home Assistant notification destination must be granted to the tenant.

The ``notify`` service and the TTS entity name devices of the operator's one Home
Assistant instance. Saving a *changed* destination checks the tenant the
preferences are saved in (422); every send checks the notification's own tenant,
because a preference is per user and the user may belong to several tenants.
Drives the real route, the real :class:`NotificationService` and the real
:class:`HomeAssistantNotificationChannel` against a recording Home Assistant double.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.notifications.tenant_router import router
from app.common.auth import get_current_tenant, get_current_user, require_account_principal
from app.common.dependencies import get_notification_service
from app.common.enums import TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError
from app.data_access.external.ha_notification_channel import HomeAssistantNotificationChannel
from app.domain.models.notification import ChannelPreference, Notification, NotificationPreferences
from app.domain.models.tenant_context import TenantContext
from app.domain.services.notification_service import NotificationService
from tests.support.ha_entity_grants import grant_service

SLUG = "garten-a"
GRANTS = {"t1": {"notify.mobile_app_own", "media_player.tent"}, "t2": {"notify.mobile_app_other"}}


class _Repo:
    def __init__(self, stored: NotificationPreferences | None = None) -> None:
        self.stored = stored

    def upsert(self, preferences):
        self.stored = preferences
        return preferences

    def get_by_user(self, user_key):
        return self.stored


def _client(stored: NotificationPreferences | None = None, grants=None) -> tuple[TestClient, _Repo]:
    repo = _Repo(stored)
    service = NotificationService(
        engine=MagicMock(),
        notification_repo=MagicMock(),
        preference_repo=repo,
        ha_entity_grants=grants if grants is not None else grant_service(GRANTS),
    )
    app = FastAPI()
    app.include_router(router, prefix=f"/api/v1/t/{SLUG}")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    ctx = TenantContext(tenant_key="t1", tenant_slug=SLUG, user_key="u1", role=TenantRole.GROWER)
    app.dependency_overrides[get_current_tenant] = lambda: ctx
    app.dependency_overrides[get_notification_service] = lambda: service
    app.dependency_overrides[require_account_principal] = lambda: SimpleNamespace(key="u1")
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(key="u1")
    return TestClient(app), repo


def _put(client: TestClient, config: dict):
    return client.put(
        f"/api/v1/t/{SLUG}/notifications/preferences",
        json={"channels": {"home_assistant": {"enabled": True, "config": config}}},
    )


class TestSavingADestination:
    @pytest.mark.parametrize(
        "config",
        [
            {"notify_service": "notify.mobile_app_operator"},
            {"notify_service": "mobile_app_other"},  # granted, but to another tenant
            {"tts_enabled": True, "tts_entity_id": "media_player.living_room"},
        ],
    )
    def test_an_ungranted_destination_is_422_and_nothing_is_stored(self, config: dict) -> None:
        client, repo = _client()

        response = _put(client, config)

        assert response.status_code == 422
        assert [d["code"] for d in response.json()["details"]] == ["HA_ENTITY_NOT_GRANTED"]
        assert repo.stored is None

    @pytest.mark.parametrize("notify", ["mobile_app_own", "notify.mobile_app_own"])
    def test_a_granted_destination_is_stored(self, notify: str) -> None:
        client, repo = _client()

        response = _put(client, {"notify_service": notify, "tts_enabled": True, "tts_entity_id": "media_player.tent"})

        assert response.status_code == 200, response.text
        assert repo.stored is not None

    def test_an_unchanged_legacy_destination_does_not_block_an_unrelated_edit(self) -> None:
        legacy = NotificationPreferences(
            user_key="u1",
            channels={
                "home_assistant": ChannelPreference(enabled=True, config={"notify_service": "mobile_app_legacy"})
            },
        )
        client, _repo = _client(stored=legacy)

        response = _put(client, {"notify_service": "mobile_app_legacy", "persistent_notification": False})

        assert response.status_code == 200, response.text

    def test_an_unset_service_needs_no_grant_on_save(self) -> None:
        client, _ = _client()

        assert _put(client, {"mobile_push": True}).status_code == 200


class TestLightMode:
    def test_saving_the_channel_grants_what_a_send_will_dial(self) -> None:
        """Light mode: the operator is the only user; the default broadcast service is granted on save."""
        grants = grant_service(grant_on_use=True)
        client, _ = _client(grants=grants)

        response = _put(client, {"mobile_push": True, "tts_enabled": True, "tts_entity_id": "media_player.tent"})

        assert response.status_code == 200, response.text
        assert grants.granted_entity_ids("t1") == frozenset({"notify.notify", "media_player.tent"})


class _RecordingHA:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict]] = []

    async def fire_event(self, event_type, data):
        return {}

    async def create_persistent_notification(self, **kwargs):
        return {}

    async def call_service(self, domain, service, service_data):
        self.calls.append((domain, service, service_data))
        return {}


def _send(tenant_key: str, config: dict):
    ha = _RecordingHA()
    channel = HomeAssistantNotificationChannel(ha, ha_entity_grants=grant_service(GRANTS))
    notification = Notification(
        _key="n1", tenant_key=tenant_key, user_key="u1", notification_type="care_watering", title="Water", body="x"
    )
    result = asyncio.run(channel.send(notification, {"persistent_notification": False, **config}))
    return ha.calls, result


class TestSendingToADestination:
    def test_a_granted_notify_service_is_dialled(self) -> None:
        calls, result = _send("t1", {"notify_service": "mobile_app_own"})

        assert result.success is True
        assert [(d, s) for d, s, _ in calls] == [("notify", "mobile_app_own")]

    def test_the_notifications_own_tenant_decides_not_the_one_it_was_saved_in(self) -> None:
        """The destination is t1's; a notification of t2 is not pushed to it."""
        calls, result = _send("t2", {"notify_service": "mobile_app_own"})

        assert calls == []
        assert result.success is False

    def test_the_default_broadcast_service_needs_its_own_grant(self) -> None:
        calls, _ = _send("t1", {"mobile_push": True})

        assert calls == []

    def test_an_ungranted_tts_entity_is_not_announced_on(self) -> None:
        calls, _ = _send("t1", {"mobile_push": False, "tts_enabled": True, "tts_entity_id": "media_player.kitchen"})

        assert calls == []

    def test_a_granted_tts_entity_is_announced_on(self) -> None:
        calls, _ = _send("t1", {"mobile_push": False, "tts_enabled": True, "tts_entity_id": "media_player.tent"})

        assert [(d, data["entity_id"]) for d, _s, data in calls] == [("tts", "media_player.tent")]

    def test_a_notification_without_a_tenant_reaches_no_destination(self) -> None:
        calls, _ = _send("", {"notify_service": "mobile_app_own"})

        assert calls == []
