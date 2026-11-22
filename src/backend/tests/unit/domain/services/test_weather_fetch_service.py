"""REQ-046 §3.6a (#2934) — due-check, manual-fetch admission and status of the weather fetch.

acceptance-1 (a changed interval applies on the next tick), acceptance-2 (due after
the interval, a failed run does not restart it), acceptance-5 (409 while running,
429 + seconds within the cooldown) and acceptance-6 (next scheduled run).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.common.enums import WeatherFetchTrigger
from app.common.exceptions import (
    WeatherFetchCooldownError,
    WeatherFetchDisabledError,
    WeatherFetchRunningError,
    WeatherFetchUnavailableError,
)
from app.domain.models.weather_fetch import (
    MANUAL_FETCH_COOLDOWN_SECONDS,
    WeatherFetchRun,
    WeatherFetchStatus,
    is_successful_run,
)
from app.domain.services.weather_fetch_service import (
    LOCK_UNAVAILABLE,
    RUN_LOCK_TTL_SECONDS,
    RUN_SOFT_TIME_LIMIT_SECONDS,
    RUN_TIME_LIMIT_SECONDS,
    WeatherFetchService,
)
from tests.support.weather_fetch_doubles import FakeWeatherFetchGate as _Gate
from tests.support.weather_fetch_doubles import InMemoryWeatherFetchStatusRepo as _StatusRepo

NOW = datetime(2026, 11, 22, 12, 0, 3, tzinfo=UTC)


def _run(started_at: datetime, *, success: bool = True) -> WeatherFetchRun:
    return WeatherFetchRun(
        trigger=WeatherFetchTrigger.SCHEDULED,
        started_at=started_at,
        finished_at=started_at + timedelta(seconds=40),
        success=success,
        sites=2,
        sites_written=2 if success else 0,
        sites_failed=0 if success else 2,
    )


def _service(
    status: WeatherFetchStatus | None = None,
    gate: _Gate | None = None,
    interval: list[int] | None = None,
    *,
    enabled: bool = True,
) -> tuple[WeatherFetchService, _StatusRepo, _Gate]:
    repo, gate = _StatusRepo(status), gate or _Gate()
    hours = interval if interval is not None else [6]
    service = WeatherFetchService(
        repo, gate, interval_hours=lambda: hours[0], weather_enabled=lambda: enabled, clock=lambda: NOW
    )
    return service, repo, gate


# ── acceptance-2: due-check ──────────────────────────────────────────────


def test_due_when_no_fetch_ever_succeeded() -> None:
    service, _, _ = _service()

    assert service.is_due()


def test_not_due_before_the_interval_has_passed() -> None:
    service, _, _ = _service(WeatherFetchStatus(last_success=_run(NOW - timedelta(hours=3))))

    assert not service.is_due()


def test_due_at_the_tick_one_interval_after_the_last_success() -> None:
    """A run started at 06:00:05 is due again at the 12:00:03 tick, not one hour later."""
    started = NOW - timedelta(hours=6) + timedelta(seconds=2)
    service, _, _ = _service(WeatherFetchStatus(last_success=_run(started)))

    assert service.is_due()


def test_a_failed_run_does_not_restart_the_interval() -> None:
    """The last *success* counts: a failed run one hour ago leaves the fetch due."""
    status = WeatherFetchStatus(
        last_run=_run(NOW - timedelta(hours=1), success=False),
        last_success=_run(NOW - timedelta(hours=7)),
    )
    service, _, _ = _service(status)

    assert service.is_due()


# ── acceptance-1: a changed interval applies without restart ─────────────


def test_a_changed_interval_applies_on_the_next_check() -> None:
    hours = [6]
    service, _, _ = _service(WeatherFetchStatus(last_success=_run(NOW - timedelta(hours=7))), interval=hours)
    assert service.is_due()

    hours[0] = 12

    assert not service.is_due()


# ── acceptance-6: next scheduled fetch ───────────────────────────────────


def test_next_scheduled_is_the_first_tick_after_the_interval() -> None:
    last = _run(datetime(2026, 11, 22, 9, 17, tzinfo=UTC))
    service, repo, _ = _service(WeatherFetchStatus(last_success=last))

    assert service.next_scheduled_at(repo.status, 6) == datetime(2026, 11, 22, 16, 0, tzinfo=UTC)


def test_next_scheduled_is_the_next_tick_when_overdue_or_never_run() -> None:
    service, repo, _ = _service()

    assert service.next_scheduled_at(repo.status, 6) == datetime(2026, 11, 22, 13, 0, tzinfo=UTC)


def test_overview_reports_both_runs_the_interval_and_the_gate_state() -> None:
    failed = _run(NOW - timedelta(hours=1), success=False)
    succeeded = _run(NOW - timedelta(hours=2))
    service, _, _ = _service(
        WeatherFetchStatus(last_run=failed, last_success=succeeded), gate=_Gate(running=True, cooldown=120)
    )

    overview = service.get_overview()

    assert overview.interval_hours == 6
    assert overview.last_run == failed
    assert overview.last_success == succeeded
    assert overview.running is True
    assert overview.manual_fetch_available_in_s == 120
    assert overview.next_scheduled_at == datetime(2026, 11, 22, 16, 0, tzinfo=UTC)


def test_overview_survives_an_unreachable_gate() -> None:
    service, _, _ = _service(gate=_Gate(down=True))

    overview = service.get_overview()

    assert overview.running is None
    assert overview.manual_fetch_available_in_s is None


# ── acceptance-5: manual-fetch admission ─────────────────────────────────


def test_manual_fetch_claims_the_ten_minute_cooldown() -> None:
    service, _, gate = _service()

    service.reserve_manual_fetch()

    assert gate.claimed == [MANUAL_FETCH_COOLDOWN_SECONDS] == [600]


def test_manual_fetch_is_refused_while_a_run_holds_the_lock() -> None:
    service, _, gate = _service(gate=_Gate(running=True))

    with pytest.raises(WeatherFetchRunningError) as info:
        service.reserve_manual_fetch()

    assert info.value.status_code == 409
    assert gate.claimed == []  # a refused fetch does not consume the cooldown


def test_manual_fetch_is_refused_within_the_cooldown_with_the_seconds_left() -> None:
    service, _, _ = _service(gate=_Gate(cooldown=420))

    with pytest.raises(WeatherFetchCooldownError) as info:
        service.reserve_manual_fetch()

    assert info.value.status_code == 429
    assert info.value.retry_after == 420


def test_manual_fetch_fails_closed_when_the_gate_is_unreachable() -> None:
    service, _, _ = _service(gate=_Gate(down=True))

    with pytest.raises(WeatherFetchUnavailableError) as info:
        service.reserve_manual_fetch()

    assert info.value.status_code == 503


def test_cancel_gives_the_cooldown_back() -> None:
    service, _, gate = _service()
    service.reserve_manual_fetch()

    service.cancel_manual_fetch()

    assert gate.released_cooldown
    service.reserve_manual_fetch()  # a second attempt is admitted again


# ── Running lock (fetch task side) ───────────────────────────────────────


def test_run_lock_is_taken_with_a_ttl_below_the_next_tick() -> None:
    service, _, gate = _service()

    token = service.acquire_run_lock()

    assert token == "token-1"
    assert gate.lock_ttls == [RUN_LOCK_TTL_SECONDS]
    assert RUN_LOCK_TTL_SECONDS < 3600
    assert service.acquire_run_lock() is None


def test_the_task_time_limits_end_a_run_before_its_lock_expires() -> None:
    """S1: the lock must never lapse under a run that is still going."""
    from app.tasks.weather_tasks import fetch_weather_forecasts

    assert RUN_SOFT_TIME_LIMIT_SECONDS < RUN_TIME_LIMIT_SECONDS < RUN_LOCK_TTL_SECONDS
    # The production task carries them — not just the constants.
    assert fetch_weather_forecasts.soft_time_limit == RUN_SOFT_TIME_LIMIT_SECONDS
    assert fetch_weather_forecasts.time_limit == RUN_TIME_LIMIT_SECONDS


def test_the_soft_to_hard_gap_outlasts_the_longest_site_chain() -> None:
    """K2: after the soft limit the task still waits for the current site; the hard limit must not cut that wait.

    Derived from the request schema's ``fetch_timeout_s`` ceiling, not restated: a
    larger admin maximum or a longer chain would turn this red.
    """
    from app.api.v1.admin.weather_providers.schemas import WeatherProvidersUpdate
    from app.domain.models.weather_fetch import (
        MAX_FETCH_TIMEOUT_S,
        SITE_FETCH_BUDGET_SECONDS,
        SITE_FETCH_MAX_SLOW_SOURCES,
    )

    schema_ceiling = WeatherProvidersUpdate.model_json_schema()["properties"]["fetch_timeout_s"]["anyOf"][0]["maximum"]

    assert schema_ceiling == MAX_FETCH_TIMEOUT_S
    assert SITE_FETCH_BUDGET_SECONDS >= MAX_FETCH_TIMEOUT_S * SITE_FETCH_MAX_SLOW_SOURCES
    assert RUN_TIME_LIMIT_SECONDS - RUN_SOFT_TIME_LIMIT_SECONDS > SITE_FETCH_BUDGET_SECONDS
    assert RUN_TIME_LIMIT_SECONDS < RUN_LOCK_TTL_SECONDS < 3600


def test_manual_fetch_is_refused_while_weather_is_disabled_without_taking_the_cooldown() -> None:
    service, _, gate = _service(enabled=False)

    with pytest.raises(WeatherFetchDisabledError) as info:
        service.reserve_manual_fetch()

    assert (info.value.status_code, info.value.error_code) == (409, "WEATHER_FETCH_DISABLED")
    assert gate.claimed == []


def test_overview_names_no_next_fetch_while_weather_is_disabled() -> None:
    service, _, _ = _service(enabled=False)

    assert service.get_overview().next_scheduled_at is None


def test_unreachable_lock_store_yields_the_unlocked_sentinel_and_release_skips_it() -> None:
    service, _, gate = _service(gate=_Gate(down=True))

    token = service.acquire_run_lock()
    service.release_run_lock(token)  # type: ignore[arg-type]

    assert token == LOCK_UNAVAILABLE
    assert gate.released_tokens == []


# ── acceptance-3: success rule ───────────────────────────────────────────


@pytest.mark.parametrize(
    ("aborted", "sites", "written", "expected"),
    [
        (False, 0, 0, True),  # nothing configured is not a failure
        (False, 3, 1, True),  # at least one site written
        (False, 3, 0, False),  # every site failed
        (True, 3, 3, False),  # a runtime error aborted the run
        (True, 0, 0, False),
    ],
)
def test_success_rule(aborted: bool, sites: int, written: int, expected: bool) -> None:
    assert is_successful_run(aborted=aborted, sites=sites, sites_written=written) is expected
