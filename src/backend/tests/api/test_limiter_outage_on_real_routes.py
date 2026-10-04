"""The shared limiter's outage path, driven through real routes (#2062, #2049).

``tests/conftest.py`` builds the limiter on ``memory://`` for the whole suite,
so until now no real route ran through ``FailoverStorage``: the "never open,
never 500" claim of #2045 was shown on toy routes only. Here the shared
limiter's storage is swapped for the one ``build_rate_limiter`` builds around a
primary that fails like a lost Valkey (``RedisError``), and real routes run
through it:

* the anonymous password-reset route with the limiter **and** the reset budget
  store down at once — still ``200``, still bounded by both;
* the signals of #2049: a storage that never answered since start logs
  ``rate_limit_storage_never_reached`` at error level; one that answered and
  then failed logs ``rate_limit_storage_unavailable``; every tenth failed probe
  logs ``rate_limit_storage_still_unavailable``.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import pytest
from fastapi.testclient import TestClient
from limits.storage import MemoryStorage
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import RedisError
from structlog.testing import capture_logs

from app.api.v1.auth.router import _rate_limit_key, limiter
from app.common import rate_limit
from app.config.settings import settings
from app.data_access.external.step_up_throttle import (
    PASSWORD_RESET_WINDOW_SECONDS,
    RedisStepUpThrottleStore,
    anonymous_budget_fallback,
)
from app.domain.services.auth_service import MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW
from tests.api import test_auth_password_reset_budget as reset_flow

_reset_client = contextmanager(reset_flow._client)


class _ValkeyDouble(MemoryStorage):
    """A ``limits`` storage that answers until ``down`` is set, then fails like a lost Valkey."""

    STORAGE_SCHEME = ["kp-outage-route-test"]
    down = False

    @property
    def base_exceptions(self) -> type[Exception]:
        return RedisError

    def _fail_if_down(self) -> None:
        if type(self).down:
            raise RedisConnectionError("Connection closed by server.")

    def incr(self, key: str, expiry: int, amount: int = 1) -> int:
        self._fail_if_down()
        return super().incr(key, expiry, amount)

    def get(self, key: str) -> int:
        self._fail_if_down()
        return super().get(key)

    def get_expiry(self, key: str) -> float:
        self._fail_if_down()
        return super().get_expiry(key)


@pytest.fixture
def failover(monkeypatch: pytest.MonkeyPatch) -> Iterator[rate_limit.FailoverStorage]:
    """The shared limiter, counting through ``FailoverStorage`` around the double."""
    _ValkeyDouble.down = False
    built = rate_limit.build_rate_limiter(_rate_limit_key, storage_url="kp-outage-route-test://")
    storage = built._storage
    assert isinstance(storage, rate_limit.FailoverStorage), "precondition: the production wrapper is in place"
    monkeypatch.setattr(limiter, "_storage", storage)
    monkeypatch.setattr(limiter, "_limiter", built._limiter)
    yield storage
    _ValkeyDouble.down = False


def _limit(budget: str) -> int:
    return int(budget.split("/")[0])


def test_the_reset_route_stays_bounded_with_the_limiter_and_the_budget_down(
    failover: rate_limit.FailoverStorage,
) -> None:
    _ValkeyDouble.down = True
    world = reset_flow._World(
        budget=RedisStepUpThrottleStore(
            reset_flow._BrokenRedis(),
            ttl_seconds=PASSWORD_RESET_WINDOW_SECONDS,
            fallback=anonymous_budget_fallback(PASSWORD_RESET_WINDOW_SECONDS),
        )
    )
    per_ip = _limit(settings.rate_limit_auth)

    with _reset_client(world) as client:
        statuses = [
            client.post(reset_flow._ROUTE, json={"email": reset_flow.OWNER}).status_code for _ in range(per_ip + 1)
        ]

    assert statuses[:per_ip] == [200] * per_ip, "an outage answered something other than 200 inside the IP limit"
    assert statuses[per_ip] == 429, "the per-process IP limit did not hold while the storage was down"
    assert world.mail.count(reset_flow.OWNER) == MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW


def _glossary_client() -> Iterator[TestClient]:
    from unittest.mock import MagicMock, patch

    from app.api.v1.glossar.deps import get_glossary_service

    with patch("app.main.get_connection"), patch("app.main.ensure_collections"):
        from app.main import app

    service = MagicMock()
    service.list_terms.return_value = []
    app.dependency_overrides[get_glossary_service] = lambda: service
    yield TestClient(app)


@pytest.fixture
def glossary() -> Iterator[TestClient]:
    yield from _glossary_client()


def _events(logs: list[dict[str, Any]], name: str) -> list[dict[str, Any]]:
    return [entry for entry in logs if entry["event"] == name]


def test_a_storage_never_reached_since_start_logs_an_error(
    failover: rate_limit.FailoverStorage, glossary: TestClient
) -> None:
    _ValkeyDouble.down = True

    with capture_logs() as logs:
        assert glossary.get("/api/v1/public/glossary/terms").status_code == 200

    errors = _events(logs, "rate_limit_storage_never_reached")
    assert [entry["log_level"] for entry in errors] == ["error"]
    assert _events(logs, "rate_limit_storage_unavailable") == []


def test_a_storage_that_answered_before_logs_the_outage_as_a_warning(
    failover: rate_limit.FailoverStorage, glossary: TestClient
) -> None:
    assert glossary.get("/api/v1/public/glossary/terms").status_code == 200
    _ValkeyDouble.down = True

    with capture_logs() as logs:
        assert glossary.get("/api/v1/public/glossary/terms").status_code == 200

    assert [entry["log_level"] for entry in _events(logs, "rate_limit_storage_unavailable")] == ["warning"]
    assert _events(logs, "rate_limit_storage_never_reached") == []


def test_a_storage_that_stays_down_is_reported_again(
    failover: rate_limit.FailoverStorage, glossary: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every failed probe is a candidate; every tenth one logs a reminder."""
    monkeypatch.setattr(rate_limit, "_PROBE_INITIAL_DELAY_S", 0.0)
    monkeypatch.setattr(rate_limit, "_PROBE_MAX_DELAY_S", 0.0)
    limiter.enabled = True
    _ValkeyDouble.down = True

    with capture_logs() as logs:
        # One request records the outage; each further one carries a probe (delay 0).
        for _ in range(1 + rate_limit._REMINDER_EVERY_FAILED_PROBES):
            glossary.get("/api/v1/public/glossary/terms")
            limiter.reset()  # keep the 10/minute route budget out of the way

    reminders = _events(logs, "rate_limit_storage_still_unavailable")
    assert len(reminders) == 1, reminders
    assert reminders[0]["never_answered"] is True
