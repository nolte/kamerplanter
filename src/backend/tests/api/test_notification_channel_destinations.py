"""#1985 / #1986 — notification channel destinations stay inside the trust boundary.

Drives the real ``PUT /t/{slug}/notifications/preferences`` route and the real
channels:

* #1985 — ``HomeAssistantNotificationChannel`` against a recording HA client
  double (``call_service`` records ``(domain, service, data)``), so a preference
  value is observed reaching — or being kept from — the Home Assistant call.
* #1986 — ``AppriseNotificationChannel`` against a stub ``apprise`` module, with
  the DNS resolver seam ``url_safety.resolve_host_addresses`` replaced by a
  double that behaves like real resolution: unknown names raise ``OSError``
  (NXDOMAIN) and a slow resolver blocks past the timeout.
"""

import asyncio
import json
import threading
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
from app.data_access.external.apprise_notification_channel import AppriseNotificationChannel
from app.data_access.external.ha_notification_channel import HomeAssistantNotificationChannel
from app.domain.models.notification import Notification, NotificationPreferences
from app.domain.models.tenant_context import TenantContext
from app.domain.services.notification_service import NotificationService

SLUG = "anna"


class _Repo:
    def __init__(self) -> None:
        self.stored: NotificationPreferences | None = None
        self.upserts = 0

    def upsert(self, preferences):
        self.upserts += 1
        self.stored = preferences
        return preferences

    def get_by_user(self, user_key):
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


def _put(client, channel, config):
    return client.put(
        f"/api/v1/t/{SLUG}/notifications/preferences",
        json={"channels": {channel: {"enabled": True, "config": config}}},
    )


def _notification() -> Notification:
    return Notification(
        _key="n1", tenant_key="t1", user_key="u1", notification_type="care_watering", title="Water", body="Tomato"
    )


# ── #1985: Home Assistant destinations ──────────────────────────────


class _RecordingHA:
    """Doubles ``HomeAssistantClient``: records every service call it would make."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict]] = []

    async def fire_event(self, event_type, data):
        return {}

    async def create_persistent_notification(self, **kwargs):
        return {}

    async def call_service(self, domain, service, service_data):
        self.calls.append((domain, service, service_data))
        return {}


def _ha_send(config):
    ha = _RecordingHA()
    result = asyncio.run(HomeAssistantNotificationChannel(ha).send(_notification(), config))
    return ha, result


BAD_NOTIFY = [
    "../../states/sensor.x",
    "mobile_app_x/../../config",
    "notify.mobile_app_x/y",
    "switch.turn_off",
    "other.mobile_app_x",
    "Mobile_App",
    "mobile app",
    "mobile_app_x\n",
    "mobile_app_ä",
    "a" * 65,
    ".",
    "notify.",
    ["notify"],
    {"a": 1},
    7,
]
BAD_TTS_ENTITY = [
    "switch.garage_door",
    "light.kitchen",
    "media_player.kitchen/../../x",
    "media_player.",
    "media_player",
    "media_player.k\n",
    "MEDIA_PLAYER.k",
    "media_player.kä",
    ["media_player.k"],
    7,
]
BAD_TTS_SERVICE = ["../x", "speak/../../x", "tts.speak", "Speak", "a b", "speak\n", ["speak"], 7]


def test_ha_traversal_string_never_reaches_the_ha_call():
    """Measure: a traversal string in the preference is the service the HA call dials."""
    ha, _ = _ha_send({"mobile_push": True, "notify_service": "../../states/sensor.x"})
    assert [c for c in ha.calls if c[0] == "notify"] == []


@pytest.mark.parametrize("bad", BAD_NOTIFY)
def test_ha_send_drops_a_refused_notify_service(bad):
    ha, result = _ha_send({"mobile_push": True, "notify_service": bad})
    assert ha.calls == []
    assert result.success is False


@pytest.mark.parametrize("bad", BAD_TTS_ENTITY)
def test_ha_send_drops_a_refused_tts_entity(bad):
    ha, _ = _ha_send(
        {"mobile_push": False, "persistent_notification": False, "tts_enabled": True, "tts_entity_id": bad}
    )
    assert ha.calls == []


@pytest.mark.parametrize("bad", BAD_TTS_SERVICE)
def test_ha_send_drops_a_refused_tts_service(bad):
    ha, _ = _ha_send(
        {
            "mobile_push": False,
            "persistent_notification": False,
            "tts_enabled": True,
            "tts_entity_id": "media_player.kitchen",
            "tts_service": bad,
        }
    )
    assert ha.calls == []


@pytest.mark.parametrize(
    ("configured", "dialled"),
    [(None, "notify"), ("mobile_app_pixel", "mobile_app_pixel"), ("notify.mobile_app_pixel", "mobile_app_pixel")],
)
def test_ha_send_still_delivers_a_valid_notify_service(configured, dialled):
    config = {"mobile_push": True, "persistent_notification": False}
    if configured is not None:
        config["notify_service"] = configured
    ha, result = _ha_send(config)
    assert result.success is True
    assert [(d, s) for d, s, _ in ha.calls] == [("notify", dialled)]


def test_stored_empty_string_means_default_not_refusal():
    """The UI sends "" for a cleared field; that is "unset", so the default service is dialled."""
    ha, result = _ha_send({"mobile_push": True, "persistent_notification": False, "notify_service": ""})
    assert result.success is True
    assert [(d, s) for d, s, _ in ha.calls] == [("notify", "notify")]


def test_ha_send_still_delivers_valid_tts():
    ha, result = _ha_send(
        {
            "mobile_push": False,
            "persistent_notification": False,
            "tts_enabled": True,
            "tts_entity_id": "media_player.kitchen",
            "tts_service": "google_translate_say",
        }
    )
    assert result.success is True
    assert [(d, s, data["entity_id"]) for d, s, data in ha.calls] == [
        ("tts", "google_translate_say", "media_player.kitchen")
    ]


@pytest.mark.parametrize(
    ("key", "bad"),
    [("notify_service", b) for b in BAD_NOTIFY]
    + [("tts_entity_id", b) for b in BAD_TTS_ENTITY]
    + [("tts_service", b) for b in BAD_TTS_SERVICE],
)
def test_route_refuses_a_ha_destination_outside_the_shape_and_stores_nothing(key, bad):
    client, repo = _client()
    resp = _put(client, "home_assistant", {"mobile_push": True, key: bad})
    assert resp.status_code == 422, resp.text
    assert repo.upserts == 0
    assert "details" in resp.json()
    if isinstance(bad, str) and bad:
        # The reason text may quote a *shape* ("media_player.*"); never the submitted value.
        assert json.dumps(bad) not in resp.text


def test_route_accepts_valid_ha_destinations_and_unset_values():
    client, repo = _client()
    config = {
        "mobile_push": True,
        "notify_service": "notify.mobile_app_pixel",
        "tts_enabled": True,
        "tts_entity_id": "media_player.kitchen",
        "tts_service": "speak",
    }
    assert _put(client, "home_assistant", config).status_code == 200
    assert repo.stored.channels["home_assistant"].config == config
    # The settings UI sends an empty string for a cleared field: that means "unset".
    assert _put(client, "home_assistant", {"tts_entity_id": ""}).status_code == 200


# ── #1986: Apprise hosts are resolved ───────────────────────────────

PUBLIC = "93.184.216.34"
_ZONE = {
    "gotify.public.example": [PUBLIC],
    "gotify.lan.example": ["192.168.1.5"],
    "dual.example": [PUBLIC, "2001:db8::1"],
    "localtest.me": ["127.0.0.1"],
    "loop6.example": ["::1"],
    "mapped.example": ["::ffff:127.0.0.1"],
    "mapped-meta.example": ["::ffff:169.254.169.254"],
    "nat64.example": ["64:ff9b::7f00:1"],
    "meta.example": ["169.254.169.254"],
    "meta6.example": ["fd00:ec2::254"],
    "linklocal6.example": ["fe80::1%eth0"],
    "any.example": ["0.0.0.0"],
    "zeronet.example": ["0.1.2.3"],
    "reserved.example": ["240.0.0.1"],
    "multi.example": [PUBLIC, "127.0.0.1"],
}
RESOLVES_INTERNALLY = [h for h in _ZONE if h not in ("gotify.public.example", "gotify.lan.example", "dual.example")]


@pytest.fixture
def resolver(monkeypatch):
    calls: list[str] = []

    def _resolve(host: str) -> list[str]:
        calls.append(host)
        try:
            return list(_ZONE[host])
        except KeyError:
            raise OSError("Name or service not known") from None  # NXDOMAIN, like getaddrinfo

    monkeypatch.setattr(url_safety, "resolve_host_addresses", _resolve, raising=False)
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


def _urls_for(host):
    return [f"gotify://{host}/token", f"gotifys://{host}/token", f"matrix://u:p@{host}/room", f"ntfy://{host}/topic"]


@pytest.mark.parametrize("host", RESOLVES_INTERNALLY)
def test_route_refuses_a_host_that_resolves_to_a_blocked_address(resolver, host):
    client, repo = _client()
    for url in _urls_for(host):
        resp = _put(client, "apprise", {"urls": [url]})
        assert resp.status_code == 422, (url, resp.text)
        assert host not in resp.text
    assert repo.upserts == 0
    assert resolver, "the resolver seam was never consulted"


@pytest.mark.parametrize("host", RESOLVES_INTERNALLY)
def test_send_hands_nothing_to_apprise_for_a_host_that_resolves_internally(resolver, stub_apprise, host):
    result = asyncio.run(AppriseNotificationChannel().send(_notification(), {"urls": _urls_for(host)}))
    assert result.success is False
    assert stub_apprise == []
    assert resolver


def test_route_refuses_nxdomain_and_stores_nothing(resolver):
    client, repo = _client()
    assert _put(client, "apprise", {"urls": ["gotify://nope.invalid/t"]}).status_code == 422
    assert repo.upserts == 0


def test_send_drops_nxdomain_hosts_fail_closed(resolver, stub_apprise):
    result = asyncio.run(AppriseNotificationChannel().send(_notification(), {"urls": ["gotify://nope.invalid/t"]}))
    assert result.success is False
    assert stub_apprise == []


def test_resolver_timeout_fails_closed(monkeypatch, stub_apprise):
    release = threading.Event()
    monkeypatch.setattr(url_safety, "APPRISE_RESOLVE_TIMEOUT_SECONDS", 0.2, raising=False)
    monkeypatch.setattr(url_safety, "resolve_host_addresses", lambda host: release.wait(5) or [PUBLIC], raising=False)
    try:
        client, repo = _client()
        assert _put(client, "apprise", {"urls": ["gotify://slow.example/t"]}).status_code == 422
        assert repo.upserts == 0
        result = asyncio.run(AppriseNotificationChannel().send(_notification(), {"urls": ["gotify://slow.example/t"]}))
        assert result.success is False
        assert stub_apprise == []
    finally:
        release.set()


def test_rfc1918_and_public_hosts_stay_allowed(resolver, stub_apprise):
    client, repo = _client()
    urls = ["gotify://gotify.public.example/t", "gotify://gotify.lan.example/t", "gotify://dual.example/t"]
    assert _put(client, "apprise", {"urls": urls}).status_code == 200
    assert repo.stored.channels["apprise"].config["urls"] == urls
    result = asyncio.run(AppriseNotificationChannel().send(_notification(), {"urls": urls}))
    assert result.success is True
    assert stub_apprise == urls


def test_token_style_schemes_are_not_resolved(resolver, stub_apprise):
    urls = ["tgram://123:TOKEN/4711", "slack://a/b/c/#general", "discord://id/tok", "pover://user@tok"]
    client, _ = _client()
    assert _put(client, "apprise", {"urls": urls}).status_code == 200
    assert resolver == []


def test_ntfy_topic_without_path_is_tolerated_unless_it_resolves_internally(resolver):
    """``ntfy://mytopic`` is a topic on ntfy.sh: NXDOMAIN is fine, a blocked answer is not."""
    client, _ = _client()
    assert _put(client, "apprise", {"urls": ["ntfy://mytopic"]}).status_code == 200
    assert _put(client, "apprise", {"urls": ["ntfy://localtest.me"]}).status_code == 422
    assert _put(client, "apprise", {"urls": ["ntfy://localtest.me?to=x"]}).status_code == 422
    assert _put(client, "apprise", {"urls": ["ntfys://u:p@localtest.me?mode=private"]}).status_code == 422


# Spellings urlsplit and Apprise read differently: the host judged must be the host dialled.
PARSER_DIFFERENTIAL = [
    "gotify://x@127.0.0.1@gotify.public.example/token",
    "gotify://x@169.254.169.254@gotify.public.example/token",
    "gotify://gotify.public.example\\@127.0.0.1/token",
    "gotify://gotify.public.example/token#?verify=no",
    "gotify://gotify.public.example/token#?cto=600",
    "slack://a/b/c#?verify=no",
    "ntfy://localtest.me#/topic",
    "gotify://::1/token",
    "gotify:///token",
    "gotify://1/token",
    "gotify://[::1]/token",
]


@pytest.mark.parametrize("bad", PARSER_DIFFERENTIAL)
def test_parser_differential_spellings_are_refused(resolver, stub_apprise, bad):
    client, repo = _client()
    assert _put(client, "apprise", {"urls": [bad]}).status_code == 422
    assert repo.upserts == 0
    result = asyncio.run(AppriseNotificationChannel().send(_notification(), {"urls": [bad]}))
    assert result.success is False
    assert stub_apprise == []


@pytest.mark.parametrize("bad", ["64:ff9b:1::7f00:1", "2001:0:4136:e378:8000:63bf:3fff:fdd2", "100.100.100.200"])
def test_transition_and_metadata_addresses_are_refused(monkeypatch, bad):
    monkeypatch.setattr(url_safety, "resolve_host_addresses", lambda host: [bad], raising=False)
    client, _ = _client()
    assert _put(client, "apprise", {"urls": ["gotify://x.example/t"]}).status_code == 422


def test_only_the_bad_entry_is_dropped_at_send(resolver, stub_apprise):
    good = "gotify://gotify.public.example/t"
    result = asyncio.run(
        AppriseNotificationChannel().send(_notification(), {"urls": ["gotify://localtest.me/t", good]})
    )
    assert result.success is True
    assert stub_apprise == [good]
