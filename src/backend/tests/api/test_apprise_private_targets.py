"""#1996 — Apprise host targets in private address space need the operator's switch.

Drives the real routes: ``PUT /t/{slug}/notifications/preferences`` (save) and
``POST /t/{slug}/notifications/test`` (send, through ``NotificationService.send_test``
and the real ``AppriseNotificationChannel``), with the DNS seam
``url_safety.resolve_host_addresses`` replaced by a zone double.

In a Kubernetes deployment a private address is the cluster: the API server
(``10.96.0.1:443``), ArangoDB (``:8529``) and Valkey (``:6379``) on pod IPs. The
send-side test stores the URL directly (a row saved before the rule, or while the
switch was on), so the send-time check is measured on its own.
"""

from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.v1.notifications.tenant_router import router
from app.common import url_safety
from app.common.auth import get_current_tenant, get_current_user, require_account_principal
from app.common.dependencies import get_notification_service
from app.common.enums import TenantRole
from app.common.exceptions import KamerplanterError
from app.config.settings import settings
from app.data_access.external.apprise_notification_channel import AppriseNotificationChannel
from app.domain.engines.notification_engine import NotificationEngine
from app.domain.models.notification import ChannelPreference, NotificationPreferences
from app.domain.models.tenant_context import TenantContext
from app.domain.services.notification_service import NotificationService

SLUG = "garden"
PUBLIC = "93.184.216.34"
_ZONE = {
    "arangodb.internal.example": ["10.244.1.7"],
    "gotify.public.example": [PUBLIC],
    "ula.internal.example": ["fd12:3456::1"],
    "mapped.internal.example": ["::ffff:10.0.0.1"],
    "cgnat.internal.example": ["100.64.0.10"],
}

#: Targets in private space: (label, url). Each must be refused with the switch off.
PRIVATE_TARGETS = [
    ("k8s-api-literal", "gotify://10.96.0.1:443/x/token"),
    ("pod-ip-arangodb", "gotify://10.244.1.7:8529/x/token"),
    ("pod-ip-valkey", "matrix://u:p@10.244.1.8:6379/room"),
    ("name-resolving-10", "gotify://arangodb.internal.example/t"),
    # IPv6 literals need brackets, which the allow-list refuses outright (``[]``),
    # so an IPv6 private target can only arrive as a name: AAAA answers.
    ("ula-literal-bracketed", "gotify://[fd12:3456::1]/t"),
    ("ula-resolved", "gotify://ula.internal.example/t"),
    ("mapped-10-resolved", "gotify://mapped.internal.example/t"),
    ("cgnat-resolved", "gotify://cgnat.internal.example/t"),
    ("rfc1918-172-edge", "gotify://172.31.255.254/t"),
    ("rfc1918-192", "gotify://192.168.1.5/t"),
    ("cgnat", "gotify://100.64.1.1/t"),
    ("ntfy-host", "ntfy://10.1.2.3/topic"),
]
PUBLIC_TARGETS = [
    "gotify://172.32.0.1/t",
    "gotify://gotify.public.example/t",
    "tgram://167772161:TOKEN/4711",  # a bot id whose number spells 10.0.0.1 is not a host
    "ntfy://mytopic",
]


class _Repo:
    def __init__(self) -> None:
        self.stored = None

    def upsert(self, preferences):
        self.stored = preferences
        return preferences

    def get_by_user(self, user_key):
        return self.stored


class _Registry:
    def __init__(self, channel) -> None:
        self._channel = channel

    def get(self, key):
        return self._channel if key == self._channel.channel_key else None


def _client() -> tuple[TestClient, _Repo]:
    repo = _Repo()
    engine = NotificationEngine(
        notification_repo=MagicMock(),
        preference_repo=repo,
        channel_registry=_Registry(AppriseNotificationChannel()),
        redis_client=MagicMock(),
        user_repo=MagicMock(),
    )
    service = NotificationService(engine=engine, notification_repo=MagicMock(), preference_repo=repo)
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


def _save(client: TestClient, urls: list[str]):
    return client.put(
        f"/api/v1/t/{SLUG}/notifications/preferences",
        json={"channels": {"apprise": {"enabled": True, "config": {"urls": urls}}}},
    )


def _store(repo: _Repo, urls: list[str]) -> None:
    repo.stored = NotificationPreferences(
        user_key="u1", channels={"apprise": ChannelPreference(enabled=True, config={"urls": urls})}
    )


def _test_send(client: TestClient):
    return client.post(f"/api/v1/t/{SLUG}/notifications/test", json={"channel_key": "apprise"})


@pytest.fixture
def zone(monkeypatch):
    calls: list[str] = []

    def _resolve(host: str) -> list[str]:
        calls.append(host)
        try:
            return list(_ZONE[host])
        except KeyError:
            raise OSError("Name or service not known") from None

    monkeypatch.setattr(url_safety, "resolve_host_addresses", _resolve)
    return calls


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


@pytest.fixture
def full_mode_default(monkeypatch):
    """The chart's deployment: full mode, the switch not set (its default applies)."""
    monkeypatch.setattr(settings, "kamerplanter_mode", "full")
    monkeypatch.setattr(settings, "apprise_allow_private_targets", None)


@pytest.mark.parametrize(("label", "url"), PRIVATE_TARGETS, ids=[t[0] for t in PRIVATE_TARGETS])
def test_a_private_target_is_refused_on_save_in_full_mode_by_default(full_mode_default, zone, label, url):
    client, repo = _client()
    resp = _save(client, [url])
    assert resp.status_code == 422, (label, resp.status_code, resp.text)
    assert repo.stored is None
    assert "10." not in resp.text and "fd12" not in resp.text  # value-free refusal


@pytest.mark.parametrize(("label", "url"), PRIVATE_TARGETS, ids=[t[0] for t in PRIVATE_TARGETS])
def test_a_stored_private_target_is_not_sent_in_full_mode_by_default(full_mode_default, zone, stub_apprise, label, url):
    client, repo = _client()
    _store(repo, [url])
    resp = _test_send(client)
    assert resp.status_code == 200, resp.text
    assert resp.json()["success"] is False, (label, resp.json())
    assert stub_apprise == []


def test_public_targets_stay_allowed_on_save_and_send(full_mode_default, zone, stub_apprise):
    client, repo = _client()
    assert _save(client, PUBLIC_TARGETS).status_code == 200
    assert _test_send(client).json()["success"] is True
    assert stub_apprise == PUBLIC_TARGETS


@pytest.mark.parametrize("url", ["gotify://127.0.0.1/t", "gotify://169.254.169.254/t", "gotify://[::1]/t"])
@pytest.mark.parametrize("mode", ["full", "light"])
def test_loopback_and_link_local_stay_refused_in_every_mode(monkeypatch, zone, stub_apprise, url, mode):
    monkeypatch.setattr(settings, "kamerplanter_mode", mode)
    monkeypatch.setattr(settings, "apprise_allow_private_targets", None)
    client, repo = _client()
    assert _save(client, [url]).status_code == 422
    _store(repo, [url])
    assert _test_send(client).json()["success"] is False
    assert stub_apprise == []
