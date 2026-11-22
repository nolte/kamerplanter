"""Unit tests for the REQ-046 ``fetch_weather_forecasts`` Celery task.

Mocks ``app.common.dependencies`` (imported lazily inside the task body) and
stubs the resolver so no real adapter / HTTP / DB is touched. The fetch service
is the real :class:`WeatherFetchService` over in-memory doubles, so the due-check,
the running lock and the recorded run are the production code (#2934).
"""

import sys
from datetime import UTC, datetime, timedelta
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.common.enums import WeatherFetchTrigger
from app.domain.models.weather import WeatherForecast
from app.domain.models.weather_fetch import WeatherFetchRun, WeatherFetchStatus
from app.domain.services.weather_fetch_service import WeatherFetchService
from tests.support.ha_entity_grants import grant_service
from tests.support.weather_fetch_doubles import FakeWeatherFetchGate, InMemoryWeatherFetchStatusRepo


@pytest.fixture
def task_module(monkeypatch):
    mock_deps = ModuleType("app.common.dependencies")
    mock_deps.get_weather_source_config_repo = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_weather_forecast_repo = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_encryption_engine = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_ha_client = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_ha_entity_grant_service = lambda: grant_service()  # type: ignore[attr-defined]
    mock_deps.get_site_repo = MagicMock()  # type: ignore[attr-defined]
    # REQ-056 §5.2: every tenant here is active (a MagicMock tenant reads ``is_active``).
    mock_deps.get_tenant_repo = MagicMock()  # type: ignore[attr-defined]
    mock_deps._effective_weather_settings = MagicMock()  # type: ignore[attr-defined]
    mock_deps.status_repo = InMemoryWeatherFetchStatusRepo()  # type: ignore[attr-defined]
    mock_deps.gate = FakeWeatherFetchGate()  # type: ignore[attr-defined]
    mock_deps.get_weather_fetch_service = lambda: WeatherFetchService(  # type: ignore[attr-defined]
        mock_deps.status_repo, mock_deps.gate, interval_hours=lambda: 6, weather_enabled=lambda: True
    )
    monkeypatch.setitem(sys.modules, "app.common.dependencies", mock_deps)

    import app.tasks.weather_tasks as module

    mock_deps.followups = MagicMock()  # type: ignore[attr-defined]
    monkeypatch.setattr(module, "_dispatch_followups", mock_deps.followups)

    yield module, mock_deps


def _stub_resolver(monkeypatch, forecasts):
    from app.domain.services import weather_source_resolver as mod

    class _StubResolver:
        def __init__(self, *args, **kwargs):
            pass

        async def resolve_daily(self, site, cfg):
            return forecasts

    monkeypatch.setattr(mod, "WeatherSourceResolver", _StubResolver)


class TestFetchWeatherForecasts:
    def test_noop_when_disabled(self, task_module, monkeypatch):
        module, _deps = task_module
        monkeypatch.setattr(module.settings, "weather_enabled", False, raising=False)

        result = module.fetch_weather_forecasts()

        assert result == {"status": "skipped", "reason": "weather_disabled"}

    def test_writes_records_with_source_and_data_kind(self, task_module, monkeypatch):
        module, deps = task_module
        monkeypatch.setattr(module.settings, "weather_enabled", True, raising=False)

        config_repo = MagicMock()
        db = MagicMock()
        db.aql.execute.return_value = iter([{"site_key": "site1", "tenant_key": "t1"}])
        config_repo._db = db
        config_repo._from_doc.side_effect = lambda doc: doc
        deps.get_weather_source_config_repo.return_value = config_repo

        forecast_repo = MagicMock()
        deps.get_weather_forecast_repo.return_value = forecast_repo

        site_repo = MagicMock()
        site_repo.get_site_by_key.return_value = SimpleNamespace(gps_coordinates=(52.5, 13.4), tenant_key="t1")
        deps.get_site_repo.return_value = site_repo

        _stub_resolver(
            monkeypatch,
            [
                WeatherForecast(
                    site_key="",
                    forecast_date=datetime.now(tz=UTC).date(),
                    source="open-meteo",
                    fetched_at=datetime.now(tz=UTC),
                    data_kind="forecast",
                )
            ],
        )

        result = module.fetch_weather_forecasts()

        assert result["status"] == "ok"
        assert result["written"] == 1
        forecast_repo.upsert_daily.assert_called_once()
        written = forecast_repo.upsert_daily.call_args.args[0]
        assert written.site_key == "site1"
        assert written.tenant_key == "t1"
        assert written.source == "open-meteo"
        assert written.data_kind == "forecast"

    def test_skips_site_without_gps(self, task_module, monkeypatch):
        module, deps = task_module
        monkeypatch.setattr(module.settings, "weather_enabled", True, raising=False)

        config_repo = MagicMock()
        db = MagicMock()
        db.aql.execute.return_value = iter([{"site_key": "site1", "tenant_key": "t1"}])
        config_repo._db = db
        config_repo._from_doc.side_effect = lambda doc: doc
        deps.get_weather_source_config_repo.return_value = config_repo
        deps.get_weather_forecast_repo.return_value = MagicMock()

        site_repo = MagicMock()
        site_repo.get_site_by_key.return_value = SimpleNamespace(gps_coordinates=None)
        deps.get_site_repo.return_value = site_repo

        result = module.fetch_weather_forecasts()

        assert result == {"status": "ok", "written": 0, "skipped": 1, "errors": 0}

    def test_skips_config_with_mismatched_tenant(self, task_module, monkeypatch):
        # SEC-002: a config whose tenant_key differs from its site's is skipped —
        # never write forecasts under a tenant the site does not belong to.
        module, deps = task_module
        monkeypatch.setattr(module.settings, "weather_enabled", True, raising=False)

        config_repo = MagicMock()
        db = MagicMock()
        db.aql.execute.return_value = iter([{"site_key": "site1", "tenant_key": "t1"}])
        config_repo._db = db
        config_repo._from_doc.side_effect = lambda doc: doc
        deps.get_weather_source_config_repo.return_value = config_repo

        forecast_repo = MagicMock()
        deps.get_weather_forecast_repo.return_value = forecast_repo

        site_repo = MagicMock()
        site_repo.get_site_by_key.return_value = SimpleNamespace(gps_coordinates=(52.5, 13.4), tenant_key="t2")
        deps.get_site_repo.return_value = site_repo

        _stub_resolver(
            monkeypatch,
            [
                WeatherForecast(
                    site_key="",
                    forecast_date=datetime.now(tz=UTC).date(),
                    source="open-meteo",
                    fetched_at=datetime.now(tz=UTC),
                    data_kind="forecast",
                )
            ],
        )

        result = module.fetch_weather_forecasts()

        assert result == {"status": "ok", "written": 0, "skipped": 1, "errors": 0}
        forecast_repo.upsert_daily.assert_not_called()


def _forecast() -> WeatherForecast:
    return WeatherForecast(
        site_key="",
        forecast_date=datetime.now(tz=UTC).date(),
        source="open-meteo",
        fetched_at=datetime.now(tz=UTC),
        data_kind="forecast",
    )


def _two_sites(deps, monkeypatch, outcomes: dict[str, object]) -> MagicMock:
    """Two sites; ``outcomes[site_key]`` is a forecast list or an exception to raise."""
    from app.domain.services import weather_source_resolver as mod

    config_repo = MagicMock()
    config_repo._db.aql.execute.return_value = iter(
        [{"site_key": key, "tenant_key": "t1"} for key in ("site1", "site2")]
    )
    config_repo._from_doc.side_effect = lambda doc: doc
    deps.get_weather_source_config_repo.return_value = config_repo
    forecast_repo = MagicMock()
    deps.get_weather_forecast_repo.return_value = forecast_repo
    deps.get_site_repo.return_value.get_site_by_key.side_effect = lambda key: SimpleNamespace(
        key=key, gps_coordinates=(52.5, 13.4), tenant_key="t1"
    )

    class _Resolver:
        def __init__(self, *args, **kwargs):
            pass

        async def resolve_daily(self, site, cfg):
            outcome = outcomes[site.key]
            if isinstance(outcome, Exception):
                raise outcome
            return outcome

    monkeypatch.setattr(mod, "WeatherSourceResolver", _Resolver)
    return forecast_repo


def _succeeded(hours_ago: float) -> WeatherFetchRun:
    started = datetime.now(tz=UTC) - timedelta(hours=hours_ago)
    return WeatherFetchRun(
        trigger=WeatherFetchTrigger.SCHEDULED, started_at=started, finished_at=started, success=True, sites=1
    )


class TestDueCheck:
    """acceptance-2 — the hourly beat fetches only when the interval has passed."""

    def test_not_due_returns_early_without_touching_a_source(self, task_module, monkeypatch):
        module, deps = task_module
        monkeypatch.setattr(module.settings, "weather_enabled", True, raising=False)
        deps.status_repo.status = WeatherFetchStatus(last_success=_succeeded(2))

        result = module.fetch_weather_forecasts()

        assert result == {"status": "skipped", "reason": "not_due"}
        deps.get_weather_source_config_repo.assert_not_called()
        assert deps.status_repo.recorded == []
        assert deps.gate.lock_ttls == []

    def test_due_after_the_interval(self, task_module, monkeypatch):
        module, deps = task_module
        monkeypatch.setattr(module.settings, "weather_enabled", True, raising=False)
        deps.status_repo.status = WeatherFetchStatus(last_success=_succeeded(6))
        _two_sites(deps, monkeypatch, {"site1": [_forecast()], "site2": [_forecast()]})

        result = module.fetch_weather_forecasts()

        assert result["status"] == "ok"
        assert deps.status_repo.recorded[-1].success

    def test_failed_last_run_is_retried_by_the_next_tick(self, task_module, monkeypatch):
        module, deps = task_module
        monkeypatch.setattr(module.settings, "weather_enabled", True, raising=False)
        _two_sites(deps, monkeypatch, {"site1": RuntimeError("down"), "site2": RuntimeError("down")})

        first = module.fetch_weather_forecasts()
        assert first["status"] == "failed"
        assert deps.status_repo.status.last_success is None

        _two_sites(deps, monkeypatch, {"site1": [_forecast()], "site2": RuntimeError("down")})
        second = module.fetch_weather_forecasts()

        assert second["status"] == "ok"
        assert deps.status_repo.status.last_success is not None

    def test_manual_run_skips_the_due_check(self, task_module, monkeypatch):
        module, deps = task_module
        monkeypatch.setattr(module.settings, "weather_enabled", True, raising=False)
        deps.status_repo.status = WeatherFetchStatus(last_success=_succeeded(1))
        _two_sites(deps, monkeypatch, {"site1": [_forecast()], "site2": [_forecast()]})

        result = module.fetch_weather_forecasts(trigger="manual")

        assert result["status"] == "ok"
        run = deps.status_repo.recorded[-1]
        assert run.trigger is WeatherFetchTrigger.MANUAL
        # acceptance-4: a successful manual run restarts the interval.
        assert deps.status_repo.status.last_success == run

    def test_a_held_lock_skips_the_run(self, task_module, monkeypatch):
        module, deps = task_module
        monkeypatch.setattr(module.settings, "weather_enabled", True, raising=False)
        deps.gate.holder = "someone-else"

        result = module.fetch_weather_forecasts(trigger="manual")

        assert result == {"status": "skipped", "reason": "already_running"}
        deps.get_weather_source_config_repo.assert_not_called()

    def test_the_run_holds_the_lock_and_releases_it(self, task_module, monkeypatch):
        module, deps = task_module
        monkeypatch.setattr(module.settings, "weather_enabled", True, raising=False)
        seen: list[bool] = []
        repo = _two_sites(deps, monkeypatch, {"site1": [_forecast()], "site2": [_forecast()]})
        repo.upsert_daily.side_effect = lambda _r: seen.append(deps.gate.running)

        module.fetch_weather_forecasts()

        assert seen and all(seen)
        assert deps.gate.running is False


class TestSuccessDefinition:
    """acceptance-3 — only a successful run queues frost and irrigation."""

    def test_every_site_failed_is_a_failure_without_followups(self, task_module, monkeypatch):
        module, deps = task_module
        monkeypatch.setattr(module.settings, "weather_enabled", True, raising=False)
        _two_sites(deps, monkeypatch, {"site1": RuntimeError("a"), "site2": RuntimeError("b")})

        result = module.fetch_weather_forecasts()

        assert result == {"status": "failed", "written": 0, "skipped": 0, "errors": 2}
        run = deps.status_repo.recorded[-1]
        assert (run.success, run.sites, run.sites_written, run.sites_failed) == (False, 2, 0, 2)
        deps.followups.assert_not_called()

    def test_one_written_site_is_a_success_that_queues_the_followups(self, task_module, monkeypatch):
        module, deps = task_module
        monkeypatch.setattr(module.settings, "weather_enabled", True, raising=False)
        _two_sites(deps, monkeypatch, {"site1": [_forecast(), _forecast()], "site2": RuntimeError("b")})

        result = module.fetch_weather_forecasts()

        assert result == {"status": "ok", "written": 2, "skipped": 0, "errors": 1}
        run = deps.status_repo.recorded[-1]
        assert (run.success, run.sites, run.sites_written, run.sites_failed, run.forecasts_written) == (
            True,
            2,
            1,
            1,
            2,
        )
        deps.followups.assert_called_once_with()

    def test_no_configured_site_is_a_success(self, task_module, monkeypatch):
        module, deps = task_module
        monkeypatch.setattr(module.settings, "weather_enabled", True, raising=False)
        deps.get_weather_source_config_repo.return_value._db.aql.execute.return_value = iter([])

        result = module.fetch_weather_forecasts()

        assert result["status"] == "ok"
        assert deps.status_repo.recorded[-1].success
        deps.followups.assert_called_once_with()

    def test_a_runtime_error_is_recorded_as_failure_and_releases_the_lock(self, task_module, monkeypatch):
        module, deps = task_module
        monkeypatch.setattr(module.settings, "weather_enabled", True, raising=False)
        deps.get_weather_source_config_repo.return_value._db.aql.execute.side_effect = OSError("db gone")

        with pytest.raises(OSError):
            module.fetch_weather_forecasts()

        run = deps.status_repo.recorded[-1]
        assert (run.success, run.error_type) == (False, "OSError")
        assert deps.gate.running is False
        deps.followups.assert_not_called()


def test_followups_queue_frost_and_irrigation(monkeypatch):
    """R4: the real dispatcher queues both tasks; irrigation respects its own kill-switch."""
    import app.tasks.weather_tasks as module
    from app.tasks import frost_forecast_tasks, irrigation_tasks

    frost = MagicMock()
    irrigation = MagicMock()
    monkeypatch.setattr(frost_forecast_tasks.evaluate_forecast_frost_warnings, "delay", frost)
    monkeypatch.setattr(irrigation_tasks.compute_irrigation_demand, "delay", irrigation)

    monkeypatch.setattr(module.settings, "irrigation_demand_enabled", True, raising=False)
    module._dispatch_followups()
    monkeypatch.setattr(module.settings, "irrigation_demand_enabled", False, raising=False)
    module._dispatch_followups()

    assert frost.call_count == 2
    assert irrigation.call_count == 1


class TestLockAndCooldown:
    """Security review 2026-11-22: own-token release, fail-open, soft time limit, cooldown give-back."""

    def test_only_the_own_lock_is_released(self, task_module, monkeypatch):
        """The lock expired mid-run and another run took it: our release must not free theirs."""
        module, deps = task_module
        monkeypatch.setattr(module.settings, "weather_enabled", True, raising=False)
        repo = _two_sites(deps, monkeypatch, {"site1": [_forecast()], "site2": [_forecast()]})

        def _taken_over(_record):
            deps.gate.holder = "other-run"

        repo.upsert_daily.side_effect = _taken_over

        module.fetch_weather_forecasts()

        assert deps.gate.released_tokens == ["token-1"]
        assert deps.gate.holder == "other-run"

    def test_an_unreachable_gate_runs_unlocked_and_releases_nothing(self, task_module, monkeypatch):
        module, deps = task_module
        monkeypatch.setattr(module.settings, "weather_enabled", True, raising=False)
        deps.gate.down = True
        _two_sites(deps, monkeypatch, {"site1": [_forecast()], "site2": [_forecast()]})

        result = module.fetch_weather_forecasts()

        assert result["status"] == "ok"
        assert deps.status_repo.recorded[-1].success
        assert deps.gate.released_tokens == []
        deps.followups.assert_called_once_with()

    def test_the_soft_time_limit_aborts_the_run_records_it_and_frees_the_lock(self, task_module, monkeypatch):
        from celery.exceptions import SoftTimeLimitExceeded

        module, deps = task_module
        monkeypatch.setattr(module.settings, "weather_enabled", True, raising=False)
        forecast_repo = _two_sites(deps, monkeypatch, {"site1": SoftTimeLimitExceeded(), "site2": [_forecast()]})

        with pytest.raises(SoftTimeLimitExceeded):
            module.fetch_weather_forecasts()

        run = deps.status_repo.recorded[-1]
        assert (run.success, run.error_type) == (False, "SoftTimeLimitExceeded")
        forecast_repo.upsert_daily.assert_not_called()  # site2 was not fetched after the limit
        assert deps.gate.holder is None
        deps.followups.assert_not_called()

    def test_a_manual_run_that_finds_the_lock_held_gives_its_cooldown_back(self, task_module, monkeypatch):
        module, deps = task_module
        monkeypatch.setattr(module.settings, "weather_enabled", True, raising=False)
        deps.gate.holder = "scheduled-run"
        deps.gate.cooldown = 600  # claimed by the API when it admitted this manual fetch

        result = module.fetch_weather_forecasts(trigger="manual")

        assert result == {"status": "skipped", "reason": "already_running"}
        assert deps.gate.released_cooldown
        assert deps.gate.cooldown == 0

    def test_a_scheduled_run_that_finds_the_lock_held_leaves_the_cooldown(self, task_module, monkeypatch):
        module, deps = task_module
        monkeypatch.setattr(module.settings, "weather_enabled", True, raising=False)
        deps.gate.holder = "manual-run"
        deps.gate.cooldown = 600

        module.fetch_weather_forecasts()

        assert not deps.gate.released_cooldown
        assert deps.gate.cooldown == 600


class TestSiteBudget:
    """K2: one site's source chain is cut at ``SITE_FETCH_BUDGET_SECONDS`` and counts as a failed site."""

    def test_a_site_over_its_budget_is_cut_and_the_next_site_still_runs(self, task_module, monkeypatch):
        import asyncio

        from app.domain.services import weather_source_resolver as mod

        module, deps = task_module
        monkeypatch.setattr(module.settings, "weather_enabled", True, raising=False)
        monkeypatch.setattr(module, "SITE_FETCH_BUDGET_SECONDS", 0.05)
        forecast_repo = _two_sites(deps, monkeypatch, {"site1": [], "site2": [_forecast()]})

        class _SlowFirst:
            def __init__(self, *args, **kwargs):
                pass

            async def resolve_daily(self, site, cfg):
                if site.key == "site1":
                    await asyncio.sleep(5)
                return [_forecast()]

        monkeypatch.setattr(mod, "WeatherSourceResolver", _SlowFirst)

        result = module.fetch_weather_forecasts()

        assert result == {"status": "ok", "written": 1, "skipped": 0, "errors": 1}
        assert forecast_repo.upsert_daily.call_count == 1
        assert deps.status_repo.recorded[-1].sites_failed == 1


class TestOutageAlert:
    """Item 1: three failed runs in a row are an outage, logged at ``error`` level."""

    def test_the_third_failed_run_in_a_row_logs_the_outage(self, task_module, monkeypatch):
        from structlog.testing import capture_logs

        module, deps = task_module
        monkeypatch.setattr(module.settings, "weather_enabled", True, raising=False)

        events: list[list[str]] = []
        for _ in range(3):
            _two_sites(deps, monkeypatch, {"site1": RuntimeError("a"), "site2": RuntimeError("b")})
            with capture_logs() as logs:
                module.fetch_weather_forecasts(trigger="manual")
            events.append([e["event"] for e in logs if e["log_level"] == "error"])

        assert events[0] == [] and events[1] == []
        assert events[2] == ["weather_fetch_outage"]
        assert deps.status_repo.status.consecutive_failures == 3

    def test_a_success_resets_the_count(self, task_module, monkeypatch):
        module, deps = task_module
        monkeypatch.setattr(module.settings, "weather_enabled", True, raising=False)
        deps.status_repo.status = WeatherFetchStatus(consecutive_failures=5)
        _two_sites(deps, monkeypatch, {"site1": [_forecast()], "site2": RuntimeError("b")})

        module.fetch_weather_forecasts(trigger="manual")

        assert deps.status_repo.status.consecutive_failures == 0
