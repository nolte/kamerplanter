"""#2226 — the public iCal route ``GET /api/v1/calendar/feeds/{key}/feed.ics`` answers the issued URL.

Measured before the change: the route had been deleted in March 2026
(``a5345fbfb``) while the feed-management routes kept issuing subscription URLs
to it, so every URL a member copied into a calendar app answered ``404`` and the
path was absent from the OpenAPI document.

The routes run for real over the real ``CalendarService``; only the feed
repository and the event sources are doubled. The central test takes the URL the
create route hands out and fetches exactly that URL, so the issuer and the route
cannot drift apart again.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch
from urllib.parse import urlsplit

import pytest
from fastapi.testclient import TestClient

from app.common.auth import get_current_tenant
from app.common.dependencies import get_calendar_service
from app.common.enums import TenantRole
from app.config.settings import settings
from app.domain.engines.calendar_aggregation_engine import CalendarAggregationEngine
from app.domain.models.calendar import CalendarFeed
from app.domain.models.tenant_context import TenantContext
from app.domain.services.calendar_service import CalendarService

TENANT = "tenant-garden"
TENANT_SLUG = "garden"
FEED_ICS = "/api/v1/calendar/feeds/{key}/feed.ics"


class _FeedStore:
    """An in-memory feed repository: ``save`` assigns keys, ``get_by_token_hash`` finds by digest."""

    def __init__(self) -> None:
        self.feeds: dict[str, CalendarFeed] = {}

    def save(self, feed: CalendarFeed) -> CalendarFeed:
        stored = feed.model_copy(update={"key": f"feed-{len(self.feeds) + 1}"})
        self.feeds[stored.key or ""] = stored
        return stored

    def get_by_token_hash(self, token_hash: str) -> CalendarFeed | None:
        return next((f for f in self.feeds.values() if f.token_hash == token_hash), None)

    def get_or_raise(self, key: str) -> CalendarFeed:
        return self.feeds[key]

    def update_fields(self, key: str, fields: dict) -> CalendarFeed:
        updated = self.feeds[key].model_copy(update=fields)
        self.feeds[key] = updated
        return updated


@pytest.fixture
def store() -> _FeedStore:
    return _FeedStore()


@pytest.fixture
def sources() -> MagicMock:
    sources = MagicMock()
    sources.list_tasks_due.return_value = []
    sources.list_phase_timeline_rows.return_value = []
    sources.list_maintenance_logs.return_value = []
    sources.list_watering_logs.return_value = []
    sources.list_watering_forecast_rows.return_value = []
    return sources


@pytest.fixture
def client(store: _FeedStore, sources: MagicMock) -> Iterator[TestClient]:
    service = CalendarService(store, CalendarAggregationEngine(), sources)  # type: ignore[arg-type]
    ctx = TenantContext(tenant_key=TENANT, tenant_slug=TENANT_SLUG, user_key="owner", role=TenantRole.GROWER)
    with (
        patch("app.main.get_connection"),
        patch("app.main.ensure_collections"),
        patch("app.api.v1.calendar.tenant_router.get_calendar_service", lambda: service),
    ):
        from app.main import app

        app.dependency_overrides[get_current_tenant] = lambda: ctx
        app.dependency_overrides[get_calendar_service] = lambda: service
        try:
            yield TestClient(app, raise_server_exceptions=False)
        finally:
            app.dependency_overrides.pop(get_current_tenant, None)
            app.dependency_overrides.pop(get_calendar_service, None)


def _create_feed(client: TestClient) -> dict:
    response = client.post(f"/api/v1/t/{TENANT_SLUG}/calendar/feeds", json={"name": "Garden", "filters": {}})
    assert response.status_code == 201, response.text
    return response.json()


def _path_and_query(url: str) -> str:
    parts = urlsplit(url)
    return f"{parts.path}?{parts.query}"


class TestTheIssuedUrlIsServed:
    def test_the_url_from_create_answers_an_ical_document(self, client: TestClient) -> None:
        issued = _create_feed(client)

        response = client.get(_path_and_query(issued["ical_url"]))

        assert response.status_code == 200, response.text
        assert response.headers["content-type"] == "text/calendar; charset=utf-8"
        assert response.text.startswith("BEGIN:VCALENDAR")
        assert "X-WR-CALNAME:Garden" in response.text

    def test_the_url_from_a_rotation_answers_and_the_old_one_does_not(self, client: TestClient) -> None:
        issued = _create_feed(client)
        rotated = client.post(f"/api/v1/t/{TENANT_SLUG}/calendar/feeds/{issued['key']}/regenerate-token").json()

        assert client.get(_path_and_query(rotated["ical_url"])).status_code == 200
        assert client.get(_path_and_query(issued["ical_url"])).status_code == 404

    def test_the_issued_url_names_the_route_template(self, client: TestClient) -> None:
        issued = _create_feed(client)

        url = urlsplit(issued["ical_url"])

        assert url.path == FEED_ICS.format(key=issued["key"])
        assert url.query == f"token={issued['token']}"

    def test_the_route_is_in_the_openapi_document(self, client: TestClient) -> None:
        operation = client.app.openapi()["paths"][FEED_ICS]["get"]  # type: ignore[attr-defined]

        assert operation.get("security") == []  # no bearer, no API key: the token in the query authorises
        assert {"200", "404", "410", "429"} <= set(operation["responses"])

    def test_the_answer_is_not_cached(self, client: TestClient) -> None:
        issued = _create_feed(client)

        response = client.get(_path_and_query(issued["ical_url"]))

        assert response.headers["cache-control"] == "no-store"


class TestOnlyTheFeedsTenantIsRead:
    def test_every_event_source_is_read_with_the_feeds_tenant(self, client: TestClient, sources: MagicMock) -> None:
        issued = _create_feed(client)

        assert client.get(_path_and_query(issued["ical_url"])).status_code == 200

        for read in (
            sources.list_tasks_due,
            sources.list_phase_timeline_rows,
            sources.list_maintenance_logs,
            sources.list_watering_logs,
            sources.list_watering_forecast_rows,
        ):
            assert read.call_args.kwargs["tenant_key"] == TENANT, read


class TestEveryRefusalLooksTheSame:
    """No token, a wrong token, another feed's token and an inactive feed: one 404, one body shape."""

    def _refusals(self, client: TestClient, store: _FeedStore) -> dict[str, object]:
        first = _create_feed(client)
        second = _create_feed(client)
        inactive = _create_feed(client)
        store.update_fields(inactive["key"], {"is_active": False})
        key = first["key"]
        return {
            "no token": client.get(FEED_ICS.format(key=key)),
            "empty token": client.get(FEED_ICS.format(key=key) + "?token="),
            "unknown token": client.get(FEED_ICS.format(key=key) + "?token=not-a-feed-token"),
            "another feed's token": client.get(FEED_ICS.format(key=key) + f"?token={second['token']}"),
            "unknown key": client.get(FEED_ICS.format(key="feed-999") + f"?token={first['token']}"),
            "the stored digest": client.get(FEED_ICS.format(key=key) + f"?token={store.feeds[key].token_hash}"),
            "inactive feed": client.get(_path_and_query(inactive["ical_url"])),
        }

    def test_each_answers_404(self, client: TestClient, store: _FeedStore) -> None:
        refusals = self._refusals(client, store)

        assert {name: r.status_code for name, r in refusals.items()} == dict.fromkeys(refusals, 404)  # type: ignore[attr-defined]

    def test_each_body_has_the_same_code_and_message_shape(self, client: TestClient, store: _FeedStore) -> None:
        refusals = self._refusals(client, store)

        codes = {r.json()["error_code"] for r in refusals.values()}  # type: ignore[attr-defined]
        assert codes == {"ENTITY_NOT_FOUND"}
        for name, response in refusals.items():
            body = response.json()  # type: ignore[attr-defined]
            assert "token" not in body["message"].lower(), name
            assert "inactive" not in body["message"].lower(), name

    def test_an_expired_feed_answers_410_to_its_token_holder(self, client: TestClient, store: _FeedStore) -> None:
        issued = _create_feed(client)
        store.update_fields(issued["key"], {"expires_at": datetime.now(tz=UTC) - timedelta(minutes=1)})

        assert client.get(_path_and_query(issued["ical_url"])).status_code == 410

    def test_an_oversized_token_is_refused_before_any_lookup(self, client: TestClient, store: _FeedStore) -> None:
        issued = _create_feed(client)

        response = client.get(FEED_ICS.format(key=issued["key"]) + "?token=" + "a" * 257)

        assert response.status_code == 422


class TestTheRouteIsRateLimitedPerAddress:
    def test_the_budget_is_granted_then_refused(self, client: TestClient) -> None:
        issued = _create_feed(client)
        budget = int(settings.rate_limit_calendar_feed.split("/")[0])
        url = _path_and_query(issued["ical_url"])

        granted = [client.get(url).status_code for _ in range(budget)]

        assert set(granted) == {200}
        assert client.get(url).status_code == 429

    def test_refused_guesses_spend_the_same_budget(self, client: TestClient) -> None:
        """Varying the key or the token does not open a fresh bucket (#2052)."""
        budget = int(settings.rate_limit_calendar_feed.split("/")[0])

        answers = [
            client.get(FEED_ICS.format(key=f"feed-{n}") + f"?token=guess-{n}").status_code for n in range(budget)
        ]

        assert set(answers) == {404}
        assert client.get(FEED_ICS.format(key="feed-x") + "?token=guess-x").status_code == 429


class TestTheTokenNeverReachesALogLine:
    def test_the_access_log_line_masks_key_and_token(self, client: TestClient) -> None:
        from app.config.logging import _AccessLogRedactionFilter

        issued = _create_feed(client)
        target = _path_and_query(issued["ical_url"])
        record = logging.LogRecord(
            "uvicorn.access",
            logging.INFO,
            __file__,
            0,
            '%s - "%s %s HTTP/%s" %d',
            ("203.0.113.7:51234", "GET", target, "1.1", 200),
            None,
        )

        assert _AccessLogRedactionFilter().filter(record)
        line = record.getMessage()

        assert issued["token"] not in line
        assert issued["key"] not in line
        assert "/api/v1/calendar/feeds/{}/feed.ics?<redacted>" in line
