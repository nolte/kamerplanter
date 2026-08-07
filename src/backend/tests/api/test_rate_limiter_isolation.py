"""The rate-limit budget does not cross a test boundary (#989).

``app.api.v1.auth.router.limiter`` is the single SlowAPI instance the whole app
decorates with, and SlowAPI counts against that decorating instance — not
against ``app.state.limiter``. Its counters are therefore process state shared by
every test in the session, and under ``TestClient`` every caller is the same IP
(``testclient``) on the same path, i.e. the same bucket. ``rate_limit_email_change``
is hourly, so a window opened in one module is still open at the end of the run:
whoever spends it makes a *later* module fail, and the test that fails is never
the one at fault.

``tests/api/conftest.py::reset_rate_limiter`` closes that structurally. This
module is the guard on the guard — the two tests below are written to fail if
that fixture is removed, weakened to module scope, or made non-autouse:

* the first deliberately exhausts the hourly budget, which is what a rate-limit
  test has to do and what an isolation mechanism must therefore tolerate;
* the second asserts the budget is full again, which is only true if the reset
  happens at the *test* boundary.

Their order is their meaning; keep the spender first.
"""

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.common.auth import get_current_user
from app.common.dependencies import get_privacy_service
from app.config.settings import settings
from app.domain.models.privacy import EmailChangeRequest
from app.domain.models.user import User

USER_KEY = "u-isolation-1"
ENDPOINT = "/api/v1/privacy/email-change"


def _budget() -> int:
    """Calls granted per hour, read from the setting rather than hard-coded."""
    return int(settings.rate_limit_email_change.split("/")[0])


@pytest.fixture
def client() -> Iterator[TestClient]:
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
    with patch("app.main.get_connection"), patch("app.main.ensure_collections"):
        from app.main import app

        app.dependency_overrides[get_privacy_service] = lambda: service
        app.dependency_overrides[get_current_user] = lambda: User(
            _key=USER_KEY,
            email="owner@example.com",
            display_name="Requesting User",
            is_active=True,
        )
        try:
            yield TestClient(app, raise_server_exceptions=False)
        finally:
            app.dependency_overrides.pop(get_privacy_service, None)
            app.dependency_overrides.pop(get_current_user, None)


def _spend(client: TestClient, count: int) -> list[int]:
    return [client.post(ENDPOINT, json={"new_email": f"target-{i}@example.com"}).status_code for i in range(count)]


class TestTheBudgetDoesNotCrossTheTestBoundary:
    def test_a_single_test_may_exhaust_the_hourly_budget(self, client: TestClient) -> None:
        """Also pins that the limiter is *enabled*: without the 429 this proves nothing."""
        statuses = _spend(client, _budget() + 1)

        assert statuses[:-1] == [201] * _budget()
        assert statuses[-1] == 429

    def test_the_next_test_still_gets_a_full_budget(self, client: TestClient) -> None:
        """Fails if the reset is per module instead of per test — the window is hourly."""
        statuses = _spend(client, _budget())

        assert statuses == [201] * _budget()
