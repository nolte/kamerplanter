"""#1995 review F1/F2 — the send-time Apprise check resolves fresh; the test send has an owner.

Drives the real routes: ``PUT /t/{slug}/notifications/preferences`` (save) and
``POST /t/{slug}/notifications/test`` (``NotificationService.send_test`` → the
real ``AppriseNotificationChannel``), with one ``NotificationEngine`` and one
preference store behind both, and the DNS seam ``url_safety.resolve_host_addresses``
replaced by a zone the test edits between the two calls — an attacker re-pointing
its own authoritative DNS.

The host cache is **not** cleared between save and send in these tests: the
autouse clear in ``tests/conftest.py`` runs between tests only, and a clear here
would hide exactly the class under test (a save-time answer reused at send).
"""

import threading
import time
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
from app.data_access.external import apprise_notification_channel
from app.data_access.external.apprise_notification_channel import AppriseNotificationChannel
from app.domain.engines.notification_engine import NotificationEngine
from app.domain.models.tenant_context import TenantContext
from app.domain.services.notification_service import NotificationService

SLUG = "garden"
PUBLIC = "93.184.216.34"
DEADLINE = 0.3


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


def _client(user_key: str = "u1", tenant_key: str = "t1") -> TestClient:
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

    ctx = TenantContext(tenant_key=tenant_key, tenant_slug=SLUG, user_key=user_key, role=TenantRole.GROWER)
    app.dependency_overrides[get_current_tenant] = lambda: ctx
    app.dependency_overrides[get_notification_service] = lambda: service
    app.dependency_overrides[require_account_principal] = lambda: SimpleNamespace(key=user_key)
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(key=user_key)
    return TestClient(app)


def _save(client: TestClient, urls: list[str]):
    return client.put(
        f"/api/v1/t/{SLUG}/notifications/preferences",
        json={"channels": {"apprise": {"enabled": True, "config": {"urls": urls}}}},
    )


def _test_send(client: TestClient):
    return client.post(f"/api/v1/t/{SLUG}/notifications/test", json={"channel_key": "apprise"})


class _Zone:
    """Resolver double the test edits: a list answers, ``None`` is NXDOMAIN, ``"hang"`` blocks."""

    def __init__(self) -> None:
        self.records: dict[str, object] = {}
        self.calls: list[str] = []
        self.release = threading.Event()
        self.inside = 0
        self._lock = threading.Lock()

    def __call__(self, host: str) -> list[str]:
        self.calls.append(host)
        record = self.records.get(host)
        if record == "hang":
            with self._lock:
                self.inside += 1
            try:
                self.release.wait(30)
                raise OSError("Temporary failure in name resolution")  # ends late, with an error
            finally:
                with self._lock:
                    self.inside -= 1
        if record is None:
            raise OSError("Name or service not known")
        return list(record)  # type: ignore[call-overload]

    def drain(self) -> None:
        self.release.set()
        end = time.monotonic() + 10
        while self.inside and time.monotonic() < end:
            time.sleep(0.01)


@pytest.fixture
def zone(monkeypatch):
    double = _Zone()
    monkeypatch.setattr(url_safety, "APPRISE_RESOLVE_TIMEOUT_SECONDS", DEADLINE)
    monkeypatch.setattr(url_safety, "resolve_host_addresses", double)
    yield double
    double.drain()


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


@pytest.mark.parametrize("internal", ["127.0.0.1", "169.254.169.254"])
def test_a_host_repointed_after_save_is_refused_at_send(zone, stub_apprise, internal):
    """F1: the save-time answer must not stand in for the send-time check."""
    client = _client()
    zone.records["flip.example"] = [PUBLIC]
    assert _save(client, ["gotify://flip.example/t"]).status_code == 200

    zone.records["flip.example"] = [internal]  # the attacker re-points its DNS, well inside the cache TTL
    resp = _test_send(client)
    assert resp.status_code == 200, resp.text
    assert resp.json()["success"] is False, resp.json()
    assert stub_apprise == []
    assert zone.calls == ["flip.example", "flip.example"], "the send did not resolve again"


def test_a_late_failure_after_a_timeout_is_not_tolerated_at_send(zone, stub_apprise):
    """F1, negative half: a refused timeout must not turn into a tolerated 'unresolvable'.

    ``ntfy://name`` without a path tolerates NXDOMAIN (a ntfy.sh topic). A lookup
    that hangs is refused as a timeout; when it later ends with an error, that
    error must not be reused by the next send as if the name were NXDOMAIN.
    """
    client = _client()
    assert _save(client, ["ntfy://slowtopic"]).status_code == 200  # NXDOMAIN at save: a topic, tolerated

    zone.records["slowtopic"] = "hang"
    first = _test_send(client)
    assert first.json()["success"] is False, first.json()
    zone.release.set()  # the hanging lookup ends late, with an error
    assert _wait_until(lambda: zone.inside == 0)
    zone.release.clear()

    second = _test_send(client)
    assert second.json()["success"] is False, second.json()
    assert stub_apprise == []


def test_a_blocked_answer_from_save_is_still_honoured_at_send(zone, stub_apprise, monkeypatch):
    """The send path may take a cached *blocked* verdict — it only ever refuses."""
    client = _client()
    zone.records["flip.example"] = [PUBLIC]
    assert _save(client, ["gotify://flip.example/t"]).status_code == 200
    url_safety._resolution_cache.store("flip.example", ("127.0.0.1",))
    resp = _test_send(client)
    assert resp.json()["success"] is False, resp.json()
    assert zone.calls == ["flip.example"], "a cached blocked verdict was resolved again"


def test_the_test_send_attributes_its_resolution_to_the_caller(zone, stub_apprise, monkeypatch):
    """F2: ``send_test`` builds its own notification; it must carry the caller as owner."""
    seen: list[str] = []
    real = apprise_notification_channel.partition_apprise_urls

    def _spy(urls, *, owner_key):
        seen.append(owner_key)
        return real(urls, owner_key=owner_key)

    monkeypatch.setattr(apprise_notification_channel, "partition_apprise_urls", _spy)
    client = _client(user_key="anna", tenant_key="t-anna")
    zone.records["gotify.example"] = [PUBLIC]
    assert _save(client, ["gotify://gotify.example/t"]).status_code == 200
    assert _test_send(client).json()["success"] is True
    assert seen == ["anna"]


def _wait_until(predicate, seconds: float = 5.0) -> bool:
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if predicate():
            return True
        time.sleep(0.005)
    return predicate()
