"""#1995 — one user's never-answering Apprise host names do not starve another user.

Drives the real ``PUT /t/{slug}/notifications/preferences`` route (save) and the
real ``AppriseNotificationChannel`` (send), with the DNS seam
``url_safety.resolve_host_addresses`` replaced by a double: ``stuck*`` names
block like a nameserver that never answers, every other name answers at once.

Before #1995 one save of ten stuck names held all eight threads of the one
module-wide resolver pool, so the next user's fast name waited behind them and
was refused at the deadline, on save and on send alike.

The timed windows hold only the victim's request and run with the cyclic
garbage collector paused (:func:`_timed`). In the ``tests/api`` process the
collector tracks some 2.6 million objects; one incremental old-generation
collection measured up to 0.70 s locally and ~1 s on the CI runner — a pause the
victim's request merely happened to allocate into, not a wait for a resolver
thread. Starvation is a wait on threads and the deadline, which the paused
collector does not shorten.
"""

import asyncio
import gc
import threading
import time
from collections.abc import Callable
from types import ModuleType, SimpleNamespace
from typing import Any
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
from app.domain.models.notification import Notification
from app.domain.models.tenant_context import TenantContext
from app.domain.services.notification_service import NotificationService

SLUG = "garden"
PUBLIC = "93.184.216.34"
#: Short deadline for the test; the starvation does not depend on its length.
DEADLINE = 0.5


class _Repo:
    def __init__(self) -> None:
        self.stored = None

    def upsert(self, preferences):
        self.stored = preferences
        return preferences

    def get_by_user(self, user_key):
        return self.stored


def _client(user_key: str) -> TestClient:
    service = NotificationService(engine=MagicMock(), notification_repo=MagicMock(), preference_repo=_Repo())
    app = FastAPI()
    app.include_router(router, prefix=f"/api/v1/t/{SLUG}")

    @app.exception_handler(KamerplanterError)
    def _handler(request: Request, exc: KamerplanterError):
        return JSONResponse(status_code=exc.status_code, content={"message": exc.message, "details": exc.details})

    ctx = TenantContext(tenant_key="t1", tenant_slug=SLUG, user_key=user_key, role=TenantRole.GROWER)
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


class _NeverAnswering:
    """Resolver double: ``stuck*`` blocks until released, anything else answers at once."""

    def __init__(self) -> None:
        self.release = threading.Event()
        self._lock = threading.Lock()
        self.inside = 0

    def __call__(self, host: str) -> list[str]:
        if not host.startswith("stuck"):
            return [PUBLIC]
        with self._lock:
            self.inside += 1
        try:
            self.release.wait(30)
            raise OSError("Temporary failure in name resolution")
        finally:
            with self._lock:
                self.inside -= 1

    def drain(self) -> None:
        self.release.set()
        end = time.monotonic() + 10
        while self.inside and time.monotonic() < end:
            time.sleep(0.01)


@pytest.fixture
def never_answering(monkeypatch):
    double = _NeverAnswering()
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


def _timed(call: Callable[[], Any]) -> tuple[Any, float]:
    """``(result, seconds)`` of ``call()``, with the cyclic garbage collector paused meanwhile.

    Only the collector's automatic runs pause; threads, locks and waits behave as
    always, so a request that waits for a resolver thread takes just as long.
    """
    was_enabled = gc.isenabled()
    gc.disable()
    try:
        started = time.monotonic()
        result = call()
        return result, time.monotonic() - started
    finally:
        if was_enabled:
            gc.enable()


def test_a_never_answering_user_does_not_delay_another_users_save_or_send(never_answering, stub_apprise):
    attacker = _client("attacker")
    for round_ in range(3):  # ten names per save (the list maximum), three saves
        resp = _save(attacker, [f"gotify://stuck{round_}-{i}.example/t" for i in range(10)])
        assert resp.status_code == 422, resp.text
    assert never_answering.inside > 0, "the double never held a resolver thread"

    victim = _client("victim")  # building the test app is not part of the save
    resp, save_seconds = _timed(lambda: _save(victim, ["gotify://fast.example/t"]))
    assert resp.status_code == 200, (resp.text, round(save_seconds, 2))
    assert save_seconds < DEADLINE, save_seconds

    notification = Notification(
        _key="n1", tenant_key="t1", user_key="victim", notification_type="care_watering", title="Water", body="Tomato"
    )
    channel = AppriseNotificationChannel()
    result, send_seconds = _timed(
        lambda: asyncio.run(channel.send(notification, {"urls": ["gotify://fast2.example/t"]}))
    )
    assert result.success is True, (result.error, round(send_seconds, 2))
    assert stub_apprise == ["gotify://fast2.example/t"]
    assert send_seconds < DEADLINE, send_seconds
