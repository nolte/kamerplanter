"""``POST /api/v1/auth/login`` may not answer differently for an unknown address (SEC-H-010).

The lockout counter used to live only on the ``User`` document. An address with
no document could never reach it, so five wrong passwords produced

* **423** ``Account temporarily locked. Try again in 15 minutes.`` for a
  registered address, and
* **401** ``Invalid email or password.`` for one that is not registered.

Unauthenticated, and no password guess ever had to succeed — the status code
alone answered "is this address registered?".

This module asserts the property where the vulnerability is observable: on the
wire. It drives both addresses through the identical sequence of wrong-password
attempts and requires the two responses to be indistinguishable in **status,
body and headers**, not merely "both are errors".
"""

from collections.abc import Iterator
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.common.dependencies import get_auth_service
from app.data_access.external.unknown_account_store import MemoryUnknownAccountStore
from app.domain.engines.login_throttle_engine import MAX_ATTEMPTS, LoginThrottleEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.models.user import User
from app.domain.services.auth_service import AuthService

REGISTERED_EMAIL = "victim@example.com"
UNREGISTERED_EMAIL = "ghost@example.com"
REAL_PASSWORD = "the-owners-real-password-2024"
WRONG_PASSWORD = "attacker-guess-password-2024"

#: Attempts needed before the lockout answers: ``calculate_lockout`` only starts
#: locking at the MAX_ATTEMPTS-th failure, which the next request then sees.
_ATTEMPTS_UNTIL_LOCKED = MAX_ATTEMPTS + 1

#: Response fields that differ between *any* two requests and therefore carry no
#: information about the account: a per-error UUID and a wall-clock stamp.
_VOLATILE_BODY_FIELDS = frozenset({"error_id", "timestamp"})

#: Likewise for headers — ``date`` ticks and ``x-request-id`` is a fresh UUID per
#: request. Everything else is compared, ``content-length`` included: the two
#: bodies are byte-identical apart from the volatile fields above, so a length
#: difference would mean a message difference.
_VOLATILE_HEADERS = frozenset({"date", "x-request-id"})


def _stateful_user_repo() -> MagicMock:
    """A user repo that actually persists the lockout counter across calls.

    A ``MagicMock`` returning a fresh ``User`` each time would never reach the
    lockout, and the test would pass against the unfixed code by accident.
    """
    stored = User(
        _key="8271634",
        email=REGISTERED_EMAIL,
        display_name="Victim Realname",
        password_hash=PasswordEngine().hash_password(REAL_PASSWORD),
        email_verified=True,
        is_active=True,
    )

    def _get_by_email(email: str) -> User | None:
        return stored.model_copy(deep=True) if email.lower() == REGISTERED_EMAIL else None

    def _update_fields(key: str, fields: dict) -> None:
        for name, value in fields.items():
            if name == "locked_until":
                setattr(stored, name, datetime.fromisoformat(value) if value else None)
            else:
                setattr(stored, name, value)

    repo = MagicMock()
    repo.get_by_email.side_effect = _get_by_email
    repo.update_fields.side_effect = _update_fields
    return repo


def _auth_service_factory():  # noqa: ANN202 - returns a FastAPI dependency override
    """Build one AuthService per request, all sharing one repo and one store.

    Mirrors production: ``get_auth_service()`` runs per request, so a store that
    only lived for the lifetime of a service instance would never count.
    """
    repo = _stateful_user_repo()
    store = MemoryUnknownAccountStore()

    def _factory() -> AuthService:
        return AuthService(
            user_repo=repo,
            auth_provider_repo=MagicMock(),
            refresh_token_repo=MagicMock(),
            password_engine=PasswordEngine(),
            token_engine=TokenEngine("test-secret-key-for-unit-tests-32chars!", "HS256"),
            throttle_engine=LoginThrottleEngine(),
            email_service=MagicMock(),
            frontend_url="http://localhost:5173",
            unknown_account_store=store,
        )

    return _factory


@pytest.fixture
def client() -> Iterator[TestClient]:
    # The per-IP window is process-global state shared with every other test
    # that touches an /auth route; ``tests/api/conftest.py`` clears it around
    # every test (#989). Each test here drives a full lockout sequence, so it
    # needs the whole budget and must not leave a spent one behind.
    with patch("app.main.get_connection"), patch("app.main.ensure_collections"):
        from app.main import app

        app.dependency_overrides[get_auth_service] = _auth_service_factory()
        try:
            yield TestClient(app, raise_server_exceptions=False)
        finally:
            app.dependency_overrides.pop(get_auth_service, None)


def _login(client: TestClient, email: str, password: str = WRONG_PASSWORD):  # noqa: ANN202 - httpx Response
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def _observable(response) -> tuple[int, dict, dict]:  # noqa: ANN001 - httpx Response
    """Everything about a response an attacker can actually read."""
    body = {k: v for k, v in response.json().items() if k not in _VOLATILE_BODY_FIELDS}
    headers = {k.lower(): v for k, v in response.headers.items() if k.lower() not in _VOLATILE_HEADERS}
    return response.status_code, body, headers


def _drive_to_lockout(client: TestClient, email: str) -> list[tuple[int, dict, dict]]:
    return [_observable(_login(client, email)) for _ in range(_ATTEMPTS_UNTIL_LOCKED)]


class TestLoginLockoutIsNotAnEnumerationOracle:
    def test_registered_and_unregistered_addresses_answer_identically(self, client: TestClient) -> None:
        """The whole point: status, body and headers must match, attempt for attempt."""
        registered = _drive_to_lockout(client, REGISTERED_EMAIL)
        unregistered = _drive_to_lockout(client, UNREGISTERED_EMAIL)

        # Pin the reference sequence first. "Both sides answered the same" is
        # also true when both sides are broken the same way (e.g. both 500), and
        # a test that accepts that proves nothing.
        assert [status for status, _, _ in registered] == [401] * MAX_ATTEMPTS + [423]

        for attempt, (from_registered, from_unregistered) in enumerate(zip(registered, unregistered, strict=True), 1):
            assert from_registered == from_unregistered, (
                f"attempt {attempt} distinguishes a registered address from an unregistered one: "
                f"{from_registered} vs {from_unregistered}"
            )

    def test_unregistered_address_reaches_the_same_423(self, client: TestClient) -> None:
        """Pins the concrete answer, so a regression to 'both are 401' also fails."""
        statuses = [status for status, _, _ in _drive_to_lockout(client, UNREGISTERED_EMAIL)]

        assert statuses == [401] * MAX_ATTEMPTS + [423]

        locked = _login(client, UNREGISTERED_EMAIL)
        assert locked.status_code == 423
        assert locked.json()["error_code"] == "ACCOUNT_LOCKED"
        assert "Try again in 15 minutes" in locked.json()["message"]

    def test_lockout_of_one_address_does_not_leak_onto_another(self, client: TestClient) -> None:
        """The counter is per address, as it is for real accounts — not per IP.

        A per-IP counter would answer 423 for the *next* address probed from the
        same client regardless of whether it exists, which is a different oracle
        wearing the same status code.
        """
        _drive_to_lockout(client, UNREGISTERED_EMAIL)

        other = _login(client, "second-ghost@example.com")
        assert other.status_code == 401

    def test_the_owner_can_still_log_in_before_the_threshold(self, client: TestClient) -> None:
        """The guard must not turn a wrong guess into a locked-out legitimate user."""
        _login(client, REGISTERED_EMAIL)

        ok = _login(client, REGISTERED_EMAIL, password=REAL_PASSWORD)
        assert ok.status_code == 200
        assert ok.json()["access_token"]
