"""#2171: the iCal feed token leaves the server once - in the create / rotate response.

Measured before the change: ``CalendarFeedResponse`` carried ``token`` and an
``ical_url`` with the token in its query string, and every route built it - so
``GET /calendar/feeds`` and ``GET /calendar/feeds/{key}`` handed the live
subscription credential to any member on every read.

The routes run for real; only the service is doubled, and it returns a feed that
still carries every secret-shaped value the stored document could hold (a legacy
plaintext ``token`` attribute and the ``token_hash``), so a response that echoed
either is caught whichever attribute it read.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.common.auth import get_current_tenant
from app.common.enums import TenantRole
from app.domain.models.calendar import CalendarFeed, CalendarFeedIssued
from app.domain.models.tenant_context import TenantContext

BASE = "/api/v1/t/personal/calendar"
LEGACY_TOKEN = "legacy-plaintext-token-value"
STORED_HASH = "f" * 64
ISSUED_TOKEN = "freshly-issued-token-value"


def _stored_feed(key: str = "feed-1") -> CalendarFeed:
    # ``model_validate`` with the legacy attribute: whatever the model keeps of it,
    # the response must not show it.
    return CalendarFeed.model_validate(
        {
            "_key": key,
            "tenant_key": "personal",
            "user_key": "u1",
            "name": "Feed",
            "token": LEGACY_TOKEN,
            "token_hash": STORED_HASH,
        }
    )


class _FakeCalendarService:
    def list_feeds(self, user_key: str, tenant_key: str) -> list[CalendarFeed]:
        return [_stored_feed("feed-1"), _stored_feed("feed-2")]

    def get_feed(self, key: str, *, tenant_key: str) -> CalendarFeed:
        return _stored_feed(key)

    def update_feed(self, key: str, feed: CalendarFeed, *, tenant_key: str) -> CalendarFeed:
        return _stored_feed(key)

    def create_feed(self, feed: CalendarFeed) -> CalendarFeedIssued:
        return CalendarFeedIssued(feed=_stored_feed("feed-new"), token=ISSUED_TOKEN)

    def regenerate_token(self, key: str, *, tenant_key: str) -> CalendarFeedIssued:
        return CalendarFeedIssued(feed=_stored_feed(key), token=ISSUED_TOKEN)


def _ctx() -> TenantContext:
    return TenantContext(tenant_key="personal", tenant_slug="personal", user_key="u1", role=TenantRole.LEAD)


@pytest.fixture
def client():
    service = _FakeCalendarService()
    with (
        patch("app.main.get_connection"),
        patch("app.main.ensure_collections"),
        patch("app.api.v1.calendar.tenant_router.get_calendar_service", lambda: service),
    ):
        from app.main import app

        app.dependency_overrides[get_current_tenant] = _ctx
        yield TestClient(app, raise_server_exceptions=False)
        app.dependency_overrides.pop(get_current_tenant, None)


def _assert_no_secret(response) -> None:
    assert response.status_code == 200, response.text
    for secret in (LEGACY_TOKEN, STORED_HASH, ISSUED_TOKEN):
        assert secret not in response.text


def test_the_feed_list_returns_neither_token_nor_url(client) -> None:
    response = client.get(f"{BASE}/feeds")

    _assert_no_secret(response)
    for item in response.json():
        assert {"token", "token_hash", "ical_url"}.isdisjoint(item)
    assert [item["key"] for item in response.json()] == ["feed-1", "feed-2"]  # the control: feeds are listed


def test_a_single_feed_read_returns_neither_token_nor_url(client) -> None:
    response = client.get(f"{BASE}/feeds/feed-1")

    _assert_no_secret(response)
    assert {"token", "token_hash", "ical_url"}.isdisjoint(response.json())
    assert response.json()["name"] == "Feed"


def test_an_update_returns_neither_token_nor_url(client) -> None:
    response = client.put(f"{BASE}/feeds/feed-1", json={"name": "Feed", "filters": {}, "is_active": True})

    _assert_no_secret(response)
    assert {"token", "token_hash", "ical_url"}.isdisjoint(response.json())


def test_the_create_response_carries_the_new_token_and_url_once(client) -> None:
    response = client.post(f"{BASE}/feeds", json={"name": "Feed", "filters": {}})

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["token"] == ISSUED_TOKEN
    assert body["ical_url"].endswith(f"/api/v1/calendar/feeds/feed-new/feed.ics?token={ISSUED_TOKEN}")
    assert LEGACY_TOKEN not in response.text and STORED_HASH not in response.text


def test_the_rotation_response_carries_the_new_token_and_url_once(client) -> None:
    response = client.post(f"{BASE}/feeds/feed-1/regenerate-token")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["token"] == ISSUED_TOKEN
    assert body["ical_url"].endswith(f"/api/v1/calendar/feeds/feed-1/feed.ics?token={ISSUED_TOKEN}")
    assert LEGACY_TOKEN not in response.text and STORED_HASH not in response.text
