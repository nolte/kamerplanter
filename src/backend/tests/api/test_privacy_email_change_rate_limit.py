"""``POST /api/v1/privacy/email-change`` must be rate-limited (#958 §2).

Every call to this endpoint sends mail to an address the caller names and does
not have to own: the verification link when the address is free, the "someone
tried to use your address" notice when it is taken. Authentication says *who*
may trigger that; until this limit existed nothing said *how often*, and unlike
every ``/auth/*`` route this router carried no ``@limiter.limit`` at all.

The budget is deliberately not ``rate_limit_auth``. See
``settings.rate_limit_email_change`` for why an interactive-retry figure is the
wrong shape for an endpoint whose every call leaves the system as an email.
"""

from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.common.auth import get_current_user
from app.common.dependencies import get_privacy_service
from app.config.settings import settings
from app.domain.models.privacy import EmailChangeRequest
from app.domain.models.user import User

USER_KEY = "u1"
OWN_EMAIL = "owner@example.com"


def _allowed_calls() -> int:
    """The configured budget, read from settings rather than hard-coded."""
    return int(settings.rate_limit_email_change.split("/")[0])


def _privacy_service() -> MagicMock:
    from datetime import UTC, datetime, timedelta

    service = MagicMock()
    now = datetime.now(UTC)
    service.request_email_change.side_effect = lambda _user_key, new_email: EmailChangeRequest(
        _key="ec-1",
        user_key=USER_KEY,
        new_email=new_email,
        verification_token_hash="",
        status="pending",
        requested_at=now,
        expires_at=now + timedelta(hours=24),
    )
    return service


@pytest.fixture
def service() -> MagicMock:
    """One instance for the whole test, so call counts across requests add up.

    A factory that mints a fresh mock per request would make every
    ``assert_not_called`` below trivially true — a test that measures nothing.
    """
    return _privacy_service()


@pytest.fixture
def client(service: MagicMock) -> Iterator[TestClient]:
    # The budget this module spends is process-global state shared with every
    # other test that posts here; the ``reset_rate_limiter`` autouse fixture in
    # ``tests/api/conftest.py`` clears it around every test (#989), so this
    # module neither inherits a spent counter nor leaves one behind.
    with patch("app.main.get_connection"), patch("app.main.ensure_collections"):
        from app.main import app

        app.dependency_overrides[get_privacy_service] = lambda: service
        app.dependency_overrides[get_current_user] = lambda: User(
            _key=USER_KEY,
            email=OWN_EMAIL,
            display_name="Requesting User",
            is_active=True,
        )
        try:
            yield TestClient(app, raise_server_exceptions=False)
        finally:
            app.dependency_overrides.pop(get_privacy_service, None)
            app.dependency_overrides.pop(get_current_user, None)


def _request_change(client: TestClient, new_email: str):  # noqa: ANN202 - httpx Response
    return client.post("/api/v1/privacy/email-change", json={"new_email": new_email})


class TestEmailChangeIsRateLimited:
    def test_the_budget_is_granted_then_refused(self, client: TestClient) -> None:
        allowed = [_request_change(client, f"target-{i}@example.com") for i in range(_allowed_calls())]
        refused = _request_change(client, "one-too-many@example.com")

        assert {response.status_code for response in allowed} == {201}
        assert refused.status_code == 429

    def test_a_refused_call_sends_no_mail(self, client: TestClient, service: MagicMock) -> None:
        """The point of the limit: the service is never reached, so nothing is sent."""
        for i in range(_allowed_calls()):
            _request_change(client, f"target-{i}@example.com")
        assert service.request_email_change.call_count == _allowed_calls()

        refused = _request_change(client, "one-too-many@example.com")

        assert refused.status_code == 429
        assert service.request_email_change.call_count == _allowed_calls()

    def test_the_budget_is_the_configured_one(self) -> None:
        """A hard-coded literal in the router would drift from the setting."""
        from app.api.v1.privacy import router as privacy_router

        assert privacy_router.settings.rate_limit_email_change == settings.rate_limit_email_change

    def test_it_is_stricter_than_the_interactive_auth_budget(self) -> None:
        """Guards the decision, not the number: this must never silently widen.

        ``rate_limit_auth`` is 20/minute = 1200/hour. If someone ever "unifies"
        the two, this endpoint would again allow four figures of mail an hour to
        addresses the caller does not own.
        """
        per_hour = {"minute": 60, "hour": 1, "day": 1 / 24}
        count, unit = settings.rate_limit_email_change.split("/")
        auth_count, auth_unit = settings.rate_limit_auth.split("/")

        assert int(count) * per_hour[unit] < int(auth_count) * per_hour[auth_unit]
