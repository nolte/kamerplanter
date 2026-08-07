"""``POST /api/v1/auth/register`` tells the existing address — after answering.

REQ-023 §3.2 wants the address that already owns an account to hear that
somebody tried to register with it. #957 deliberately did not build that,
because the obvious version reopens the oracle it had just closed:
``require_email_verification`` defaults to ``False``, so a genuine registration
sends **no mail at all**, and ``SmtpEmailAdapter._send`` re-raises. A synchronous
send on the duplicate branch alone would therefore be both slower *and* able to
answer 500 where a real registration answers 201.

This module asserts the two conditions that make the notice safe, on the wire:

* the request **does not wait** for it — the dispatch is a background task that
  runs after the response body has been written, asserted by observing the ASGI
  ``send`` events rather than by timing anything;
* a **broker outage changes nothing** a caller can see.

The per-recipient suppression window lives in the worker and is asserted in
``tests/unit/tasks/test_duplicate_registration_notice.py``.
"""

from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.common.dependencies import get_auth_service
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.models.user import User
from app.domain.services.auth_service import AuthService

TAKEN_EMAIL = "victim@example.com"
FREE_EMAIL = "newcomer@example.com"
PASSWORD = "Attacker-Guess-Password-2024!"
STORED_KEY = "8271634"
CREATED_KEY = "9137450"

#: Differ between any two registrations and therefore carry nothing about the
#: account: the synthesised key and the creation timestamp.
_VOLATILE_FIELDS = frozenset({"key", "created_at"})


def _auth_service() -> AuthService:
    repo = MagicMock()
    stored = User(
        _key=STORED_KEY,
        email=TAKEN_EMAIL,
        display_name="Victim Realname",
        password_hash=PasswordEngine().hash_password("The-Owners-Real-Password-2024!"),
        email_verified=True,
        created_at=datetime.now(UTC),
    )
    repo.get_by_email.side_effect = lambda email: stored if email.lower() == TAKEN_EMAIL else None

    def _create(user: User) -> User:
        created = user.model_copy(deep=True)
        created.key = CREATED_KEY
        created.created_at = datetime.now(UTC)
        return created

    repo.create.side_effect = _create
    return AuthService(
        user_repo=repo,
        auth_provider_repo=MagicMock(),
        refresh_token_repo=MagicMock(),
        password_engine=PasswordEngine(),
        token_engine=TokenEngine("test-secret-key-for-unit-tests-32chars!", "HS256"),
        throttle_engine=LoginThrottleEngine(),
        email_service=MagicMock(),
        frontend_url="http://localhost:5173",
        tenant_service=MagicMock(),
    )


class _OrderRecordingApp:
    """ASGI wrapper that notes the moment the response body leaves the app.

    The point of the feature is *when* the enqueue happens, and no assertion on
    a mock's call count can see that. Sharing one log between this wrapper and
    the patched dispatch makes the order observable without measuring a clock.
    """

    def __init__(self, app: Any, log: list[str]) -> None:
        self._app = app
        self._log = log

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        async def _send(message: dict) -> None:
            if message["type"] == "http.response.body" and not message.get("more_body", False):
                self._log.append("response-sent")
            await send(message)

        await self._app(scope, receive, _send)


@pytest.fixture
def dispatched(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Record every enqueue, with the broker itself stubbed out."""
    from app.tasks import auth_tasks

    calls: list[str] = []
    monkeypatch.setattr(
        auth_tasks.send_duplicate_registration_notice,
        "delay",
        lambda user_key: calls.append(user_key),
    )
    return calls


@pytest.fixture
def order() -> list[str]:
    return []


@pytest.fixture
def client(order: list[str]) -> Iterator[TestClient]:
    # The per-IP window is process-global state shared with every other test
    # that touches an /auth route; ``tests/api/conftest.py`` clears it around
    # every test (#989).
    with patch("app.main.get_connection"), patch("app.main.ensure_collections"):
        from app.main import app

        app.dependency_overrides[get_auth_service] = _auth_service
        try:
            yield TestClient(_OrderRecordingApp(app, order), raise_server_exceptions=False)
        finally:
            app.dependency_overrides.pop(get_auth_service, None)


def _register(client: TestClient, email: str):  # noqa: ANN202 - httpx Response
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD, "display_name": "Attacker Chosen Name"},
    )


class TestTheNoticeIsDispatched:
    def test_duplicate_address_enqueues_exactly_one_notice(
        self,
        client: TestClient,
        dispatched: list[str],
    ) -> None:
        response = _register(client, TAKEN_EMAIL)

        assert response.status_code == 201
        assert dispatched == [STORED_KEY]

    def test_free_address_enqueues_nothing(self, client: TestClient, dispatched: list[str]) -> None:
        """Nobody to tell — and an enqueue here would be the oracle in reverse."""
        response = _register(client, FREE_EMAIL)

        assert response.status_code == 201
        assert dispatched == []

    def test_notified_key_never_appears_in_the_response(
        self,
        client: TestClient,
        dispatched: list[str],
    ) -> None:
        body = _register(client, TAKEN_EMAIL).json()

        assert dispatched == [STORED_KEY]
        assert STORED_KEY not in body.values()


class TestTheRequestDoesNotWaitForIt:
    def test_enqueue_happens_after_the_response_body_is_sent(
        self,
        client: TestClient,
        order: list[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The whole safety argument in one assertion.

        A caller with a stopwatch measures the interval that ends with
        ``http.response.body``. Everything the notice costs — the lazy import,
        the broker publish, a broker that hangs — happens after that event, so
        it cannot show up in the duplicate branch's response time and turn the
        branch back into an oracle.
        """
        from app.tasks import auth_tasks

        monkeypatch.setattr(
            auth_tasks.send_duplicate_registration_notice,
            "delay",
            lambda _user_key: order.append("dispatched"),
        )

        _register(client, TAKEN_EMAIL)

        assert order == ["response-sent", "dispatched"]

    def test_a_hanging_broker_is_not_inside_the_measured_window(
        self,
        client: TestClient,
        order: list[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Same ordering when the publish is the slowest thing in the process."""
        import time

        from app.tasks import auth_tasks

        def _slow(_user_key: str) -> None:
            time.sleep(0.25)
            order.append("dispatched")

        monkeypatch.setattr(auth_tasks.send_duplicate_registration_notice, "delay", _slow)

        _register(client, TAKEN_EMAIL)

        assert order == ["response-sent", "dispatched"]


class TestFailuresAreInvisible:
    def test_broker_outage_answers_exactly_like_a_genuine_registration(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """``.delay`` raising must not turn a 201 into a 500 (a sharper oracle)."""
        from app.tasks import auth_tasks

        def _broker_down(_user_key: str) -> None:
            raise ConnectionError("broker unreachable")

        monkeypatch.setattr(auth_tasks.send_duplicate_registration_notice, "delay", _broker_down)

        duplicate = _register(client, TAKEN_EMAIL)
        fresh = _register(client, FREE_EMAIL)

        assert duplicate.status_code == fresh.status_code == 201
        assert duplicate.json().keys() == fresh.json().keys()
        assert {k: v for k, v in duplicate.json().items() if k not in _VOLATILE_FIELDS | {"email"}} == {
            k: v for k, v in fresh.json().items() if k not in _VOLATILE_FIELDS | {"email"}
        }
        assert duplicate.json()["email"] == TAKEN_EMAIL

    def test_broker_outage_leaves_no_trace_in_headers_either(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from app.tasks import auth_tasks

        def _broker_down(_user_key: str) -> None:
            raise ConnectionError("broker unreachable")

        monkeypatch.setattr(auth_tasks.send_duplicate_registration_notice, "delay", _broker_down)

        duplicate = _register(client, TAKEN_EMAIL)
        fresh = _register(client, FREE_EMAIL)

        volatile = {"date", "x-request-id", "content-length"}
        assert {k.lower(): v for k, v in duplicate.headers.items() if k.lower() not in volatile} == {
            k.lower(): v for k, v in fresh.headers.items() if k.lower() not in volatile
        }
