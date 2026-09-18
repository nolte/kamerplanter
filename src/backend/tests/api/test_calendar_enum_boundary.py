"""Calendar category filters are validated at the boundary, not converted in the handler (#1520).

Three routes of ``calendar/tenant_router.py`` built ``CalendarEventCategory``
out of request input themselves — twice in a list comprehension over
``body.filters.categories`` (``categories: list[str]`` on the schema) and once
in a ``for`` loop over the comma-separated ``category`` query parameter. A
misspelt member raised a bare ``ValueError``, which is neither a
``KamerplanterError`` nor a ``RequestValidationError``, so it reached the
``Exception`` handler: ``500 INTERNAL_ERROR`` for input the application itself
rejects.

They are the #1520 class in a different router, and they survived the first
version of that issue's guard because it followed assignments only. The
independent review of PR #1527 named all three (SCR-001); the guard now follows
``for`` and comprehension targets too, and these tests pin the behaviour the
guard can only describe.

Every rejection is paired with the canonical spelling on the same request, so
the control shows the status is caused by the spelling and not by the fixture.
"""

from datetime import date
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.common.auth import get_current_tenant
from app.common.enums import CalendarEventCategory, TenantRole
from app.domain.models.calendar import CalendarFeed, CalendarFeedFilters
from app.domain.models.tenant_context import TenantContext

BASE = "/api/v1/t/personal/calendar"


class _FakeCalendarService:
    """Records what the handler asked for; the routes under test never persist."""

    def __init__(self) -> None:
        self.last_query = None

    def get_events(self, query):
        self.last_query = query
        return []

    def create_feed(self, feed: CalendarFeed) -> CalendarFeed:
        feed.key = "feed-1"
        feed.token = "tok"
        return feed

    def get_feed(self, key: str, tenant_key: str = "") -> CalendarFeed:
        return CalendarFeed(
            _key=key,
            tenant_key="personal",
            name="Feed",
            token="tok",
            filters=CalendarFeedFilters(categories=[CalendarEventCategory.HARVEST]),
        )

    def update_feed(self, key: str, feed: CalendarFeed) -> CalendarFeed:
        feed.key = key
        feed.token = "tok"
        return feed


def _ctx() -> TenantContext:
    return TenantContext(tenant_key="personal", tenant_slug="personal", user_key="u1", role=TenantRole.LEAD)


@pytest.fixture
def service() -> _FakeCalendarService:
    return _FakeCalendarService()


@pytest.fixture
def client(service):
    with (
        patch("app.main.get_connection"),
        patch("app.main.ensure_collections"),
        patch("app.api.v1.calendar.tenant_router.get_calendar_service", lambda: service),
    ):
        from app.main import app

        app.dependency_overrides[get_current_tenant] = _ctx
        yield TestClient(app, raise_server_exceptions=False)
        app.dependency_overrides.pop(get_current_tenant, None)


def _assert_boundary_rejection(response, field: str) -> None:
    """422 naming the offending field, per NFR-006.

    The field is compared after stripping the *location* prefix FastAPI puts in
    front of it (``body``/``query``/``path``), which is what the frontend's own
    error mapper does (``src/utils/errors.ts``). Taking the last dotted segment
    instead would accept ``some.other.substrate_type`` and quietly pass a test
    whose subject had moved (review SCR-007).
    """
    assert response.status_code == 422, response.json()
    payload = response.json()
    assert payload["error_code"] == "VALIDATION_ERROR"
    locations = {d["field"].split(".", 1)[1] if "." in d["field"] else d["field"] for d in payload["details"]}
    assert any(loc == field or loc.startswith(f"{field}.") for loc in locations), payload["details"]


class TestEventQueryCategories:
    """``GET /calendar/events?category=…`` — the loop-over-a-split-string spelling."""

    PARAMS = {"start": "2026-01-01", "end": "2026-01-31"}

    def test_misspelt_category_is_rejected(self, client):
        response = client.get(f"{BASE}/events", params={**self.PARAMS, "category": "Harvest"})
        _assert_boundary_rejection(response, "category")

    def test_canonical_category_is_accepted(self, client, service):
        response = client.get(f"{BASE}/events", params={**self.PARAMS, "category": "harvest"})
        assert response.status_code == 200, response.json()
        assert service.last_query.categories == [CalendarEventCategory.HARVEST]

    def test_the_comma_separated_form_still_works(self, client, service):
        """The wire format is unchanged: one parameter, members separated by commas."""
        response = client.get(f"{BASE}/events", params={**self.PARAMS, "category": "harvest, feeding"})
        assert response.status_code == 200, response.json()
        assert service.last_query.categories == [CalendarEventCategory.HARVEST, CalendarEventCategory.FEEDING]

    def test_one_bad_member_in_a_list_rejects_the_request(self, client):
        response = client.get(f"{BASE}/events", params={**self.PARAMS, "category": "harvest,Feeding"})
        _assert_boundary_rejection(response, "category")

    def test_no_category_filter_is_still_all_categories(self, client, service):
        response = client.get(f"{BASE}/events", params=self.PARAMS)
        assert response.status_code == 200, response.json()
        assert service.last_query.categories == []
        assert service.last_query.start_date == date(2026, 1, 1)


class TestFeedFilterCategories:
    """``POST``/``PUT /calendar/feeds`` — the comprehension spelling."""

    def _body(self, category: str) -> dict:
        return {"name": "My feed", "filters": {"categories": [category], "site_key": None}}

    def test_create_rejects_a_misspelt_category(self, client):
        _assert_boundary_rejection(client.post(f"{BASE}/feeds", json=self._body("Harvest")), "filters.categories.0")

    def test_create_accepts_a_canonical_category(self, client):
        response = client.post(f"{BASE}/feeds", json=self._body("harvest"))
        assert response.status_code == 201, response.json()
        assert response.json()["filters"]["categories"] == ["harvest"]

    def test_update_rejects_a_misspelt_category(self, client):
        _assert_boundary_rejection(
            client.put(f"{BASE}/feeds/feed-1", json=self._body("Harvest")), "filters.categories.0"
        )

    def test_update_accepts_a_canonical_category(self, client):
        response = client.put(f"{BASE}/feeds/feed-1", json=self._body("feeding"))
        assert response.status_code == 200, response.json()
        assert response.json()["filters"]["categories"] == ["feeding"]

    def test_a_feed_read_back_still_serialises_categories_as_strings(self, client):
        """The response schema shares the filter model — it must not start emitting objects."""
        response = client.get(f"{BASE}/feeds/feed-1")
        assert response.status_code == 200, response.json()
        assert response.json()["filters"]["categories"] == ["harvest"]
