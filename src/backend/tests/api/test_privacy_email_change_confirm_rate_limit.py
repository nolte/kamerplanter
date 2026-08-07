"""``POST /api/v1/privacy/email-change/confirm`` must be rate-limited (#990).

The endpoint is unauthenticated and state-changing. The argument for leaving it
alone — the token is 32 random bytes compared by hash, so guessing it is not a
realistic attack — is true today and is a property of *code*, which can change
without anyone re-deriving this decision. A limit is cheap insurance that does
not depend on that property holding.

What it bounds is **not** what its sibling bounds, and that is the point of the
separate setting. ``rate_limit_email_change`` bounds outbound mail to a
caller-chosen address, so its budget is cumulative and its window is an hour.
Confirm sends no mail; it bounds token attempts, whose natural unit is a burst
from one source. See ``settings.rate_limit_email_change_confirm`` for the number
and its derivation.
"""

from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.common.dependencies import get_privacy_service
from app.config.settings import settings

#: Converts a slowapi budget to calls per hour, so two limits written in
#: different units can be compared at all.
_PER_HOUR = {"minute": 60, "hour": 1, "day": 1 / 24}


def _per_hour(budget: str) -> float:
    count, unit = budget.split("/")
    return int(count) * _PER_HOUR[unit]


def _allowed_calls() -> int:
    """The configured budget, read from settings rather than hard-coded."""
    return int(settings.rate_limit_email_change_confirm.split("/")[0])


@pytest.fixture
def service() -> MagicMock:
    """One instance for the whole test, so call counts across requests add up.

    A factory that mints a fresh mock per request would make the
    "a refused call is never served" assertion trivially true.
    """
    service = MagicMock()
    service.confirm_email_change.return_value = None
    return service


@pytest.fixture
def client(service: MagicMock) -> Iterator[TestClient]:
    # ``limiter`` is process-global for the whole API test session, but the
    # ``reset_rate_limiter`` autouse fixture in ``tests/api/conftest.py`` now
    # clears it around every test (#989), so this module no longer resets it
    # by hand — that is exactly the second mechanism #989 removed.
    with patch("app.main.get_connection"), patch("app.main.ensure_collections"):
        from app.main import app

        app.dependency_overrides[get_privacy_service] = lambda: service
        try:
            yield TestClient(app, raise_server_exceptions=False)
        finally:
            app.dependency_overrides.pop(get_privacy_service, None)


def _confirm(client: TestClient, token: str):  # noqa: ANN202 - httpx Response
    return client.post("/api/v1/privacy/email-change/confirm", json={"token": token})


class TestEmailChangeConfirmIsRateLimited:
    def test_the_budget_is_granted_then_refused(self, client: TestClient) -> None:
        allowed = [_confirm(client, f"token-{i}") for i in range(_allowed_calls())]
        refused = _confirm(client, "one-too-many")

        assert {response.status_code for response in allowed} == {200}
        assert refused.status_code == 429

    def test_a_refused_call_never_reaches_the_token_check(self, client: TestClient, service: MagicMock) -> None:
        """The point of the limit: a refused attempt costs no token comparison."""
        for i in range(_allowed_calls()):
            _confirm(client, f"token-{i}")
        assert service.confirm_email_change.call_count == _allowed_calls()

        refused = _confirm(client, "one-too-many")

        assert refused.status_code == 429
        assert service.confirm_email_change.call_count == _allowed_calls()

    def test_the_budget_is_the_configured_one(self) -> None:
        """A hard-coded literal in the router would drift from the setting."""
        from app.api.v1.privacy import router as privacy_router

        assert privacy_router.settings.rate_limit_email_change_confirm == settings.rate_limit_email_change_confirm

    def test_it_is_sized_between_the_mail_budget_and_the_interactive_one(self) -> None:
        """Guards the *decision*, not the number: neither "unification" may pass.

        Both bounds are strict, and each fails a different wrong refactor:

        * **More permissive than ``rate_limit_email_change``.** That setting
          bounds outbound mail to third parties, which is why it is a handful an
          hour. Reusing it here would make the endpoint that *completes* a change
          tighter than the one that *starts* it — the system would hand out more
          change requests than it accepts confirmations, and a legitimate user
          who was allowed to request would be refused the click. A limit that
          strict on a click is a limit copied rather than sized.
        * **Stricter than ``rate_limit_auth``.** ``/auth/*`` is an interactive
          retry surface budgeted for a human mistyping a password several times a
          minute. Confirming is one request, plus a refresh or a retry. Reaching
          the auth figure would mean this endpoint is no longer sized for what it
          bounds.
        """
        confirm = _per_hour(settings.rate_limit_email_change_confirm)

        assert confirm > _per_hour(settings.rate_limit_email_change)
        assert confirm < _per_hour(settings.rate_limit_auth)
