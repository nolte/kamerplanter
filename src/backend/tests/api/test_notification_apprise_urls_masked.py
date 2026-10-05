"""#2113 — the preferences API never returns a stored Apprise URL; a masked line written back keeps it.

An Apprise URL carries the bot token / webhook secret in the URL itself
(``tgram://<bot token>/<chat>``). Since #2113 it is Fernet-encrypted at rest and
the API answers with a masked placeholder per URL (``tgram://****#1``) — the
scheme, so the user can tell the services apart, and the position, so a line the
client sends back unchanged is resolved to the stored URL it stands for. A new
line replaces or adds; a placeholder that names no stored URL is refused (422)
rather than stored as if it were a URL.

Drives the real ``GET``/``PUT /t/{slug}/notifications/preferences`` routes and the
real ``NotificationService``; the repository double keeps what was upserted.
Credential-shaped values are assembled at runtime (BACKEND.md §16.3).
"""

from __future__ import annotations

from types import SimpleNamespace
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
from app.domain.models.notification import NotificationPreferences
from app.domain.models.tenant_context import TenantContext
from app.domain.services.notification_service import NotificationService

SLUG = "anna"
TGRAM = "tgram://" + "123456789:" + "AAbot2113" + "Secret/4711"
GOTIFY = "gotifys://" + "gotify.example.org/" + "Atoken2113"
NTFY = "ntfys://" + "ntfy.example.org/" + "topic2113"


class _Repo:
    def __init__(self) -> None:
        self.stored: NotificationPreferences | None = None

    def upsert(self, preferences: NotificationPreferences) -> NotificationPreferences:
        self.stored = preferences.model_copy(deep=True)
        return preferences.model_copy(deep=True)

    def get_by_user(self, user_key: str) -> NotificationPreferences | None:  # noqa: ARG002
        return self.stored.model_copy(deep=True) if self.stored is not None else None


@pytest.fixture(autouse=True)
def _public_dns(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.common import url_safety  # noqa: PLC0415

    monkeypatch.setattr(url_safety, "resolve_host_addresses", lambda host: ["93.184.216.34"])


@pytest.fixture
def client_and_repo() -> tuple[TestClient, _Repo]:
    repo = _Repo()
    service = NotificationService(engine=MagicMock(), notification_repo=MagicMock(), preference_repo=repo)
    app = FastAPI()
    app.include_router(router, prefix=f"/api/v1/t/{SLUG}")

    @app.exception_handler(KamerplanterError)
    def _handler(request: Request, exc: KamerplanterError) -> JSONResponse:  # noqa: ARG001
        return JSONResponse(status_code=exc.status_code, content={"message": exc.message, "details": exc.details})

    ctx = TenantContext(tenant_key="t1", tenant_slug=SLUG, user_key="u1", role=TenantRole.GROWER)
    app.dependency_overrides[get_current_tenant] = lambda: ctx
    app.dependency_overrides[get_notification_service] = lambda: service
    app.dependency_overrides[require_account_principal] = lambda: SimpleNamespace(key="u1")
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(key="u1")
    return TestClient(app), repo


def _put(client: TestClient, urls: list[str]):
    return client.put(
        f"/api/v1/t/{SLUG}/notifications/preferences",
        json={"channels": {"apprise": {"enabled": True, "config": {"urls": urls}}}},
    )


def _urls(response) -> list[str]:
    return response.json()["channels"]["apprise"]["config"]["urls"]


def test_get_and_put_answer_with_masked_urls_only(client_and_repo: tuple[TestClient, _Repo]) -> None:
    client, _repo = client_and_repo

    put = _put(client, [TGRAM, GOTIFY])
    got = client.get(f"/api/v1/t/{SLUG}/notifications/preferences")

    assert put.status_code == 200, put.text
    assert got.status_code == 200
    for body in (put.text, got.text):
        assert TGRAM not in body
        assert GOTIFY not in body
        assert "AAbot2113" not in body
    assert _urls(got) == ["tgram://****#1", "gotifys://****#2"]


def test_masked_lines_written_back_keep_the_stored_urls(client_and_repo: tuple[TestClient, _Repo]) -> None:
    client, repo = client_and_repo
    _put(client, [TGRAM, GOTIFY])

    response = _put(client, ["tgram://****#1", "gotifys://****#2"])

    assert response.status_code == 200, response.text
    assert repo.stored is not None
    assert repo.stored.channels["apprise"].config["urls"] == [TGRAM, GOTIFY]


def test_a_removed_masked_line_drops_that_url_and_a_new_line_is_added(
    client_and_repo: tuple[TestClient, _Repo],
) -> None:
    client, repo = client_and_repo
    _put(client, [TGRAM, GOTIFY])

    response = _put(client, ["gotifys://****#2", NTFY])

    assert response.status_code == 200, response.text
    assert repo.stored is not None
    assert repo.stored.channels["apprise"].config["urls"] == [GOTIFY, NTFY]
    assert _urls(response) == ["gotifys://****#1", "ntfys://****#2"]


@pytest.mark.parametrize("placeholder", ["tgram://****#3", "gotifys://****#1", "tgram://****#0"])
def test_a_placeholder_that_names_no_stored_url_is_refused(
    client_and_repo: tuple[TestClient, _Repo], placeholder: str
) -> None:
    client, repo = client_and_repo
    _put(client, [TGRAM, GOTIFY])

    response = _put(client, [placeholder])

    assert response.status_code == 422, response.text
    assert repo.stored is not None
    assert repo.stored.channels["apprise"].config["urls"] == [TGRAM, GOTIFY]
    assert TGRAM not in response.text


def test_a_client_supplied_ciphertext_key_is_not_stored(client_and_repo: tuple[TestClient, _Repo]) -> None:
    """``urls_encrypted`` is derived from ``urls`` by the store; a client cannot set it and skip validation."""
    client, repo = client_and_repo

    response = client.put(
        f"/api/v1/t/{SLUG}/notifications/preferences",
        json={"channels": {"apprise": {"enabled": True, "config": {"urls_encrypted": ["json://internal/x"]}}}},
    )

    assert response.status_code == 200, response.text
    assert repo.stored is not None
    assert "urls_encrypted" not in repo.stored.channels["apprise"].config
