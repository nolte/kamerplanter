"""#2154 — a worker that reports readiness proves its database login first, then says it consumes.

The chart's worker had a liveness probe only. A worker whose ArangoDB login
failed after an upgrade started anyway (the connection is opened lazily, in the
first task), the Deployment counted it ready at container start and removed the
old, working worker; every task then failed in the new one.

With ``WORKER_READY_FILE`` set (the chart sets it):

* ``celeryd_init`` opens the database (``check_database_access``), retries for
  ``WORKER_DATABASE_START_BUDGET_SECONDS`` and then raises ``SystemExit`` — the
  container restarts, never becomes ready, the rollout keeps the old pod;
* ``worker_ready`` (consumer running) writes the file the startup and readiness
  probes test; ``worker_shutting_down`` removes it.

Without it nothing changes (compose, dev). The tests send the **real** signals, as
the sibling gates' tests do: Celery's ``Signal.send`` swallows an ``Exception``
from a receiver, so a receiver that raised the wrong type, or was never connected,
fails here. The behaviour against a real worker and a real ArangoDB is recorded in
the PR (wrong password -> exit, right password -> file).
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from celery.signals import celeryd_init, worker_ready, worker_shutting_down

import app.tasks  # noqa: F401  importing the package is what connects the receivers
from app.config.constants import WORKER_DATABASE_START_BUDGET_SECONDS, WORKER_DATABASE_START_RETRY_SECONDS
from app.config.settings import settings
from app.data_access.arango.connection import ArangoDatabaseAccessError

_SECRET = "the-password-must-not-appear"


@pytest.fixture(autouse=True)
def _sane_start(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the sibling receivers inert: valid salts and key, no DSN."""
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    monkeypatch.setattr(settings, "debug", True)
    monkeypatch.setattr(settings, "arangodb_password", _SECRET)


class _Clock:
    """``time.monotonic``/``time.sleep`` double: sleeping advances the clock."""

    def __init__(self) -> None:
        self.now = 1000.0
        self.slept: list[float] = []

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.now += seconds


def _start(clock: _Clock) -> None:
    with (
        patch("app.tasks.time.monotonic", clock.monotonic),
        patch("app.tasks.time.sleep", clock.sleep),
    ):
        celeryd_init.send(sender="worker@test", conf=None, instance=None)


def test_without_a_ready_file_the_start_does_not_touch_the_database(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "worker_ready_file", "")
    with patch("app.common.dependencies.check_database_access") as check:
        _start(_Clock())
    check.assert_not_called()


def test_a_reachable_database_lets_the_worker_start(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(settings, "worker_ready_file", str(tmp_path / "ready"))
    clock = _Clock()
    with patch("app.common.dependencies.check_database_access") as check:
        _start(clock)
    check.assert_called_once_with()
    assert clock.slept == []


def test_a_database_that_comes_up_within_the_budget_lets_the_worker_start(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(settings, "worker_ready_file", str(tmp_path / "ready"))
    clock = _Clock()
    failures = [ConnectionAbortedError("down"), ArangoDatabaseAccessError("account not provisioned yet")]
    with patch("app.common.dependencies.check_database_access", side_effect=[*failures, None]) as check:
        _start(clock)
    assert check.call_count == 3
    assert clock.slept == [WORKER_DATABASE_START_RETRY_SECONDS] * 2


@pytest.mark.parametrize(
    "error",
    [ArangoDatabaseAccessError(f"login refused for {_SECRET}"), ConnectionAbortedError("unreachable")],
    ids=["login-refused", "unreachable"],
)
def test_a_database_that_stays_closed_stops_the_worker(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, error: Exception
) -> None:
    monkeypatch.setattr(settings, "worker_ready_file", str(tmp_path / "ready"))
    clock = _Clock()
    with (
        patch("app.common.dependencies.check_database_access", side_effect=error) as check,
        pytest.raises(SystemExit) as excinfo,
    ):
        _start(clock)

    message = str(excinfo.value)
    assert "ARANGODB_USERNAME/ARANGODB_PASSWORD" in message
    assert type(error).__name__ in message
    assert _SECRET not in message
    # It kept trying for the whole budget, not one attempt and not forever.
    assert sum(clock.slept) < WORKER_DATABASE_START_BUDGET_SECONDS
    assert check.call_count == WORKER_DATABASE_START_BUDGET_SECONDS // WORKER_DATABASE_START_RETRY_SECONDS
    assert not (tmp_path / "ready").exists()


def test_the_ready_file_follows_the_consumer(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    ready = tmp_path / "run" / "worker-ready"
    monkeypatch.setattr(settings, "worker_ready_file", str(ready))

    worker_ready.send(sender=None)
    assert ready.is_file()

    worker_shutting_down.send(sender="worker@test", sig="TERM", how="Warm", exitcode=0)
    assert not ready.exists()
    worker_shutting_down.send(sender="worker@test", sig="TERM", how="Warm", exitcode=0)  # idempotent


def test_without_a_ready_file_nothing_is_written(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(settings, "worker_ready_file", "")
    monkeypatch.chdir(tmp_path)
    worker_ready.send(sender=None)
    assert list(tmp_path.iterdir()) == []


def test_check_database_access_closes_its_connection() -> None:
    from app.common import dependencies
    from app.data_access.arango.connection import ArangoConnection

    with (
        patch.object(ArangoConnection, "connect", autospec=True) as connect,
        patch.object(ArangoConnection, "close", autospec=True) as close,
    ):
        dependencies.check_database_access()
    connect.assert_called_once()
    close.assert_called_once()
    # the throwaway connection is not the process-wide one
    assert connect.call_args.args[0] is not dependencies._connection
