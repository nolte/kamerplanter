"""#1947 — the Apprise channel only addresses allow-listed chat/push schemes.

Drives the real ``PUT /t/{slug}/notifications/preferences`` route and the real
``AppriseNotificationChannel`` against a stub ``apprise`` module that records
every URL it is handed. ``apprise`` is not a backend dependency, so the stub is
what the channel imports.
"""

import asyncio
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.v1.notifications.tenant_router import router
from app.common.auth import get_current_tenant, get_current_user, require_account_principal
from app.common.dependencies import get_notification_service
from app.common.enums import TenantRole
from app.common.exceptions import KamerplanterError
from app.data_access.external.apprise_notification_channel import AppriseNotificationChannel
from app.domain.models.notification import Notification, NotificationPreferences
from app.domain.models.tenant_context import TenantContext
from app.domain.services.notification_service import NotificationService

SLUG = "anna"
URLS_PATH = "channels.apprise.config.urls"
GOOD = "tgram://123456:SECRETTOKEN/4711"
REFUSED = [
    "mailto://victim:pw@mail.example.org",
    "json://internal.example.org/hook",
    "https://hooks.example.org/x",
    "xml://example.org",
    "form://example.org",
    "MAILTO://a@b.example.org",
    " tgram://a/b",
    "tgram://a/b,mailto://x@y.example.org",
    "tgram://a/b mailto://x@y.example.org",
    "tgram://a/b\nmailto://x@y.example.org",
    "tgram://a/b\u00a0json://internal.example.org/x",
    "tgram://a/b\u2028json://internal.example.org/x",
    "tgram://a/b\x85json://internal.example.org/x",
    "gotify://gotify.example.org/t?cto=600",
    "gotify://gotify.example.org/t?verify=no",
    "gotify://gotify.example.org/t?%63to=600",
    "gotify://gotify.example.org/t?%76erify=no",
    "gotify://127.0.0.1./token",
    "gotify://127.1/token",
    "gotify://2130706433/token",
    "gotify://127.0.0.1/token",
    "ntfy://localhost/topic",
    "gotify://169.254.169.254/token",
    "not a url",
    "",
]


class _Repo:
    """Doubles the preference repo: keeps what was upserted, like the real one."""

    def __init__(self) -> None:
        self.stored: NotificationPreferences | None = None
        self.upserts = 0

    def upsert(self, preferences: NotificationPreferences) -> NotificationPreferences:
        self.upserts += 1
        self.stored = preferences
        return preferences

    def get_by_user(self, user_key: str):
        return self.stored


def _client():
    repo = _Repo()
    service = NotificationService(engine=MagicMock(), notification_repo=MagicMock(), preference_repo=repo)
    app = FastAPI()
    app.include_router(router, prefix=f"/api/v1/t/{SLUG}")

    @app.exception_handler(KamerplanterError)
    def _handler(request: Request, exc: KamerplanterError):
        return JSONResponse(status_code=exc.status_code, content={"message": exc.message, "details": exc.details})

    ctx = TenantContext(tenant_key="t1", tenant_slug=SLUG, user_key="u1", role=TenantRole.GROWER)
    app.dependency_overrides[get_current_tenant] = lambda: ctx
    app.dependency_overrides[get_notification_service] = lambda: service
    app.dependency_overrides[require_account_principal] = lambda: SimpleNamespace(key="u1")
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(key="u1")
    return TestClient(app), repo


def _put(client, urls):
    return client.put(
        f"/api/v1/t/{SLUG}/notifications/preferences",
        json={"channels": {"apprise": {"enabled": True, "config": {"urls": urls}}}},
    )


@pytest.fixture(autouse=True)
def _public_dns(monkeypatch):
    """Every host name the allow-list cases use resolves to a public address (no network)."""
    from app.common import url_safety  # noqa: PLC0415

    monkeypatch.setattr(url_safety, "resolve_host_addresses", lambda host: ["93.184.216.34"])


@pytest.fixture
def stub_apprise(monkeypatch):
    seen: list[str] = []
    module = ModuleType("apprise")
    module.NotifyType = SimpleNamespace(INFO="info", WARNING="warning", FAILURE="failure")

    class _Apprise:
        def add(self, url, tag=None):
            seen.append(url)

        def notify(self, **kwargs):
            return True

    module.Apprise = _Apprise
    monkeypatch.setitem(__import__("sys").modules, "apprise", module)
    return seen


def _notification() -> Notification:
    return Notification(
        _key="n1",
        tenant_key="t1",
        user_key="u1",
        notification_type="care_watering",
        title="Water",
        body="Tomato",
    )


@pytest.mark.parametrize("bad", REFUSED)
def test_route_refuses_scheme_outside_allowlist_and_stores_nothing(bad):
    client, repo = _client()
    resp = _put(client, [GOOD, bad])
    assert resp.status_code == 422, resp.text
    assert repo.upserts == 0
    # Value-free: neither the refused URL nor the token of the good one comes back.
    assert "SECRETTOKEN" not in resp.text
    if bad.strip():
        assert bad.strip() not in resp.text


def test_route_accepts_documented_services():
    client, repo = _client()
    urls = [
        GOOD,
        "slack://a/b/c",
        "gotify://gotify.lan.example/token",
        "ntfys://ntfy.example.org/topic",
        "gotify://192.168.1.5/t",
    ]
    assert _put(client, urls).status_code == 200
    assert repo.stored.channels["apprise"].config["urls"] == urls


def test_route_refuses_non_list_and_too_many():
    client, _ = _client()
    assert _put(client, "tgram://a/b").status_code == 422
    assert _put(client, ["tgram://a/b"] * 11).status_code == 422


@pytest.mark.parametrize("bad", REFUSED)
def test_channel_send_hands_nothing_refused_to_apprise(stub_apprise, bad):
    result = asyncio.run(AppriseNotificationChannel().send(_notification(), {"urls": [bad]}))
    assert result.success is False
    assert stub_apprise == []


def test_channel_send_drops_only_the_refused_entries(stub_apprise):
    result = asyncio.run(
        AppriseNotificationChannel().send(_notification(), {"urls": ["mailto://x@y.example.org", GOOD]})
    )
    assert result.success is True
    assert stub_apprise == [GOOD]


def test_channel_send_batch_hands_nothing_refused_to_apprise(stub_apprise):
    result = asyncio.run(
        AppriseNotificationChannel().send_batch([_notification()], {"urls": ["json://internal.example.org/x"]})
    )
    assert result.success is False
    assert stub_apprise == []


def test_legacy_stored_row_is_not_sent_even_if_route_check_was_bypassed(stub_apprise):
    """A row stored before the allow-list: the send-time check stands alone."""
    prefs = NotificationPreferences(
        user_key="u1",
        channels={"apprise": {"enabled": True, "config": {"urls": ["mailto://x@y.example.org"]}}},
    )
    config = prefs.channels["apprise"].config
    result = asyncio.run(AppriseNotificationChannel().send(_notification(), config))
    assert result.success is False
    assert stub_apprise == []
