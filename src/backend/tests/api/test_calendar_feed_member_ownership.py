"""#2171 review W-1: a grower manages their own calendar feeds, a lead every feed of the tenant.

Measured before the change: ``PUT /feeds/{key}`` and ``POST /feeds/{key}/regenerate-token``
checked only the tenant - any grower could rename, deactivate or rotate a colleague's
feed and so break (or, with the rotation response, take over) that colleague's calendar
subscription. The routes run for real over the real ``CalendarService``; only the
repository is doubled, holding one feed owned by ``owner``. What is pinned here is the
wiring: the router hands the caller's member key and role to the service, which decides.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.common.auth import get_current_tenant
from app.common.enums import TenantRole
from app.common.exceptions import NotFoundError
from app.domain.models.calendar import CalendarFeed
from app.domain.models.tenant_context import TenantContext
from app.domain.services.calendar_service import CalendarService

BASE = "/api/v1/t/garden/calendar"
TENANT = "tenant-garden"
FEED_KEY = "feed-1"


def _stored_feed() -> CalendarFeed:
    return CalendarFeed(_key=FEED_KEY, name="Owner's feed", tenant_key=TENANT, user_key="owner", token_hash="d" * 64)


@pytest.fixture
def repo() -> MagicMock:
    repo = MagicMock()

    def get_or_raise(key: str) -> CalendarFeed:
        if key != FEED_KEY:
            raise NotFoundError("CalendarFeed", key)
        return _stored_feed()

    repo.get_or_raise.side_effect = get_or_raise
    repo.update_fields.side_effect = lambda key, fields: CalendarFeed.model_validate(
        {**_stored_feed().model_dump(by_alias=True), **fields}
    )
    repo.delete.return_value = True
    return repo


def _service_and_ctx(repo: MagicMock, *, user_key: str, role: TenantRole):
    service = CalendarService(feed_repo=repo, aggregation_engine=MagicMock(), source_repo=MagicMock())
    ctx = TenantContext(tenant_key=TENANT, tenant_slug="garden", user_key=user_key, role=role)
    return service, ctx


@pytest.fixture
def call(repo: MagicMock):
    """Issue one request as ``(user_key, role)`` against the real routes."""

    def _call(method: str, path: str, *, user_key: str, role: TenantRole, json: dict | None = None):
        service, ctx = _service_and_ctx(repo, user_key=user_key, role=role)
        with (
            patch("app.main.get_connection"),
            patch("app.main.ensure_collections"),
            patch("app.api.v1.calendar.tenant_router.get_calendar_service", lambda: service),
        ):
            from app.main import app

            app.dependency_overrides[get_current_tenant] = lambda: ctx
            try:
                return TestClient(app, raise_server_exceptions=False).request(method, f"{BASE}{path}", json=json)
            finally:
                app.dependency_overrides.pop(get_current_tenant, None)

    return _call


_UPDATE_BODY = {"name": "Renamed", "filters": {}, "is_active": False}


class TestAGrowerCannotTouchAColleaguesFeed:
    def test_update_answers_404(self, call, repo) -> None:
        response = call("PUT", f"/feeds/{FEED_KEY}", user_key="colleague", role=TenantRole.GROWER, json=_UPDATE_BODY)

        assert response.status_code == 404, response.text
        repo.update_fields.assert_not_called()

    def test_rotation_answers_404_and_issues_no_token(self, call, repo) -> None:
        response = call("POST", f"/feeds/{FEED_KEY}/regenerate-token", user_key="colleague", role=TenantRole.GROWER)

        assert response.status_code == 404, response.text
        assert "token" not in response.json()
        repo.update_fields.assert_not_called()


class TestTheOwnerAndTheLeadAreServed:
    def test_the_owner_updates(self, call, repo) -> None:
        response = call("PUT", f"/feeds/{FEED_KEY}", user_key="owner", role=TenantRole.GROWER, json=_UPDATE_BODY)

        assert response.status_code == 200, response.text
        assert response.json()["name"] == "Renamed"

    def test_the_owner_rotates(self, call) -> None:
        response = call("POST", f"/feeds/{FEED_KEY}/regenerate-token", user_key="owner", role=TenantRole.GROWER)

        assert response.status_code == 200, response.text
        assert response.json()["token"]

    def test_a_lead_rotates_a_members_feed(self, call) -> None:
        response = call("POST", f"/feeds/{FEED_KEY}/regenerate-token", user_key="lead", role=TenantRole.LEAD)

        assert response.status_code == 200, response.text

    def test_a_lead_deletes_a_members_feed(self, call, repo) -> None:
        response = call("DELETE", f"/feeds/{FEED_KEY}", user_key="lead", role=TenantRole.LEAD)

        assert response.status_code == 204, response.text
        repo.delete.assert_called_once_with(FEED_KEY)
