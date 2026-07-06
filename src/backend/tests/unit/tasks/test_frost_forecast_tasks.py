"""Unit tests for the Issue #392 ``evaluate_forecast_frost_warnings`` task.

Mocks ``app.common.dependencies`` (imported lazily inside the task body) and
uses the real pure engine (``evaluate_forecast_frost_warning``) plus a real
``NotificationService`` whose channel engine is stubbed — so the R9 dedup logic
(``group_key`` + ``find_by_group_key``) is exercised end-to-end without touching
Redis, channels or the database. Mirrors ``test_weather_tasks.py``.
"""

import asyncio
import sys
from datetime import UTC, datetime, timedelta
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domain.models.weather import WeatherForecast
from app.domain.services.notification_service import NotificationService


def _sync_run(coro):
    """Drive a coroutine to completion on a throwaway loop.

    Replaces ``asyncio.run`` inside the task so the real async service method is
    exercised without ``asyncio.run`` nulling the thread's current event loop
    (which pollutes later tests in the same session — the reason
    ``test_notification_tasks`` mocks ``asyncio.run`` outright).
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@pytest.fixture
def task_module(monkeypatch):
    mock_deps = ModuleType("app.common.dependencies")
    mock_deps.get_weather_source_config_repo = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_weather_forecast_repo = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_site_repo = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_membership_repo = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_notification_service = MagicMock()  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "app.common.dependencies", mock_deps)
    monkeypatch.setattr("asyncio.run", _sync_run)

    import app.tasks.frost_forecast_tasks as module

    yield module, mock_deps


def _make_service(notification_repo: MagicMock) -> NotificationService:
    """Real service with a stubbed channel engine (no Redis/channels/DB)."""
    engine = MagicMock()
    engine.notify = AsyncMock(return_value={"status": "delivered"})
    service = NotificationService(
        engine=engine,
        notification_repo=notification_repo,
        preference_repo=MagicMock(),
    )
    return service


def _wire_config_cursor(deps, *, site_key: str = "site1", tenant_key: str = "t1") -> MagicMock:
    config_repo = MagicMock()
    db = MagicMock()
    db.aql.execute.return_value = iter([{"site_key": site_key, "tenant_key": tenant_key}])
    config_repo._db = db
    config_repo._from_doc.side_effect = lambda doc: doc
    deps.get_weather_source_config_repo.return_value = config_repo
    return config_repo


def _site(*, tenant_key: str = "t1", name: str = "Balcony", gps=(52.5, 13.4)) -> SimpleNamespace:
    return SimpleNamespace(tenant_key=tenant_key, name=name, gps_coordinates=gps)


def _forecast(days_ahead: int, temp_min: float | None, *, source: str = "open-meteo") -> WeatherForecast:
    return WeatherForecast(
        site_key="site1",
        tenant_key="t1",
        forecast_date=datetime.now(UTC).date() + timedelta(days=days_ahead),
        temp_min_c=temp_min,
        source=source,
        fetched_at=datetime.now(UTC),
        data_kind="forecast",
    )


class TestEvaluateForecastFrostWarnings:
    def test_noop_when_disabled(self, task_module, monkeypatch):
        module, _deps = task_module
        monkeypatch.setattr(module.settings, "weather_enabled", False, raising=False)

        result = module.evaluate_forecast_frost_warnings()

        assert result == {"status": "skipped", "reason": "weather_disabled"}

    def test_emits_one_notification_on_in_horizon_frost(self, task_module, monkeypatch):
        module, deps = task_module
        monkeypatch.setattr(module.settings, "weather_enabled", True, raising=False)

        _wire_config_cursor(deps)
        deps.get_site_repo.return_value.get_site_by_key.return_value = _site()
        deps.get_weather_forecast_repo.return_value.find_by_site.return_value = [_forecast(0, -2.0)]
        deps.get_membership_repo.return_value.list_by_tenant.return_value = [
            SimpleNamespace(user_key="u1", is_active=True),
        ]

        notification_repo = MagicMock()
        notification_repo.find_by_group_key.return_value = []  # nothing sent yet
        service = _make_service(notification_repo)
        deps.get_notification_service.return_value = service

        result = module.evaluate_forecast_frost_warnings()

        assert result["status"] == "ok"
        assert result["notified"] == 1
        service._engine.notify.assert_awaited_once()
        _user, _tenant, notification = service._engine.notify.await_args.args
        assert _tenant == "t1"
        today = datetime.now(UTC).date()
        assert notification.group_key == f"frost-forecast:site1:{today.isoformat()}"
        assert notification.notification_type == "frost_forecast_warning"

    def test_second_run_same_frost_does_not_renotify(self, task_module, monkeypatch):
        module, deps = task_module
        monkeypatch.setattr(module.settings, "weather_enabled", True, raising=False)

        deps.get_site_repo.return_value.get_site_by_key.return_value = _site()
        deps.get_weather_forecast_repo.return_value.find_by_site.return_value = [_forecast(0, -2.0)]
        deps.get_membership_repo.return_value.list_by_tenant.return_value = [
            SimpleNamespace(user_key="u1", is_active=True),
        ]

        notification_repo = MagicMock()
        # First run: no prior notification; second run: one already exists.
        notification_repo.find_by_group_key.side_effect = [[], [MagicMock()]]
        service = _make_service(notification_repo)
        deps.get_notification_service.return_value = service

        _wire_config_cursor(deps)
        first = module.evaluate_forecast_frost_warnings()
        _wire_config_cursor(deps)  # fresh cursor iterator for the second run
        second = module.evaluate_forecast_frost_warnings()

        assert first["notified"] == 1
        assert second["notified"] == 0
        # Only the first run reached the channel engine.
        assert service._engine.notify.await_count == 1

    def test_new_earlier_frost_date_emits_new_notification(self, task_module, monkeypatch):
        module, deps = task_module
        monkeypatch.setattr(module.settings, "weather_enabled", True, raising=False)

        deps.get_site_repo.return_value.get_site_by_key.return_value = _site()
        deps.get_membership_repo.return_value.list_by_tenant.return_value = [
            SimpleNamespace(user_key="u1", is_active=True),
        ]

        notification_repo = MagicMock()
        notification_repo.find_by_group_key.return_value = []  # distinct keys, never seen before
        service = _make_service(notification_repo)
        deps.get_notification_service.return_value = service

        # First run: frost tomorrow (today + 1).
        deps.get_weather_forecast_repo.return_value.find_by_site.return_value = [_forecast(1, -1.0)]
        _wire_config_cursor(deps)
        module.evaluate_forecast_frost_warnings()

        # Second run: an earlier frost appears (today) -> new group_key.
        deps.get_weather_forecast_repo.return_value.find_by_site.return_value = [_forecast(0, -3.0)]
        _wire_config_cursor(deps)
        module.evaluate_forecast_frost_warnings()

        assert service._engine.notify.await_count == 2
        today = datetime.now(UTC).date()
        group_keys = {call.args[2].group_key for call in service._engine.notify.await_args_list}
        assert f"frost-forecast:site1:{(today + timedelta(days=1)).isoformat()}" in group_keys
        assert f"frost-forecast:site1:{today.isoformat()}" in group_keys

    def test_no_frost_emits_nothing(self, task_module, monkeypatch):
        module, deps = task_module
        monkeypatch.setattr(module.settings, "weather_enabled", True, raising=False)

        _wire_config_cursor(deps)
        deps.get_site_repo.return_value.get_site_by_key.return_value = _site()
        deps.get_weather_forecast_repo.return_value.find_by_site.return_value = [_forecast(0, 8.0)]
        deps.get_membership_repo.return_value.list_by_tenant.return_value = [
            SimpleNamespace(user_key="u1", is_active=True),
        ]

        notification_repo = MagicMock()
        notification_repo.find_by_group_key.return_value = []
        service = _make_service(notification_repo)
        deps.get_notification_service.return_value = service

        result = module.evaluate_forecast_frost_warnings()

        assert result["notified"] == 0
        service._engine.notify.assert_not_awaited()
        notification_repo.find_by_group_key.assert_not_called()

    def test_empty_forecast_emits_nothing(self, task_module, monkeypatch):
        module, deps = task_module
        monkeypatch.setattr(module.settings, "weather_enabled", True, raising=False)

        _wire_config_cursor(deps)
        deps.get_site_repo.return_value.get_site_by_key.return_value = _site()
        deps.get_weather_forecast_repo.return_value.find_by_site.return_value = []
        deps.get_membership_repo.return_value.list_by_tenant.return_value = [
            SimpleNamespace(user_key="u1", is_active=True),
        ]

        notification_repo = MagicMock()
        service = _make_service(notification_repo)
        deps.get_notification_service.return_value = service

        result = module.evaluate_forecast_frost_warnings()

        assert result["notified"] == 0
        service._engine.notify.assert_not_awaited()

    def test_skips_site_without_gps(self, task_module, monkeypatch):
        module, deps = task_module
        monkeypatch.setattr(module.settings, "weather_enabled", True, raising=False)

        _wire_config_cursor(deps)
        deps.get_site_repo.return_value.get_site_by_key.return_value = _site(gps=None)
        forecast_repo = MagicMock()
        deps.get_weather_forecast_repo.return_value = forecast_repo
        service = _make_service(MagicMock())
        deps.get_notification_service.return_value = service

        result = module.evaluate_forecast_frost_warnings()

        assert result == {"status": "ok", "notified": 0, "skipped": 1, "errors": 0}
        forecast_repo.find_by_site.assert_not_called()
        service._engine.notify.assert_not_awaited()

    def test_skips_foreign_tenant_site(self, task_module, monkeypatch):
        module, deps = task_module
        monkeypatch.setattr(module.settings, "weather_enabled", True, raising=False)

        # config.tenant_key == "t1" but the site belongs to "t2" -> skip, no read.
        _wire_config_cursor(deps, tenant_key="t1")
        deps.get_site_repo.return_value.get_site_by_key.return_value = _site(tenant_key="t2")
        forecast_repo = MagicMock()
        deps.get_weather_forecast_repo.return_value = forecast_repo
        service = _make_service(MagicMock())
        deps.get_notification_service.return_value = service

        result = module.evaluate_forecast_frost_warnings()

        assert result == {"status": "ok", "notified": 0, "skipped": 1, "errors": 0}
        forecast_repo.find_by_site.assert_not_called()
        service._engine.notify.assert_not_awaited()

    def test_tenant_scoped_forecast_read(self, task_module, monkeypatch):
        module, deps = task_module
        monkeypatch.setattr(module.settings, "weather_enabled", True, raising=False)

        _wire_config_cursor(deps, site_key="site1", tenant_key="t1")
        deps.get_site_repo.return_value.get_site_by_key.return_value = _site(tenant_key="t1")
        forecast_repo = MagicMock()
        forecast_repo.find_by_site.return_value = [_forecast(0, 10.0)]
        deps.get_weather_forecast_repo.return_value = forecast_repo
        deps.get_membership_repo.return_value.list_by_tenant.return_value = []
        service = _make_service(MagicMock())
        deps.get_notification_service.return_value = service

        module.evaluate_forecast_frost_warnings()

        forecast_repo.find_by_site.assert_called_once_with("site1", "t1")

    def test_one_bad_site_does_not_abort_run(self, task_module, monkeypatch):
        module, deps = task_module
        monkeypatch.setattr(module.settings, "weather_enabled", True, raising=False)

        _wire_config_cursor(deps)
        deps.get_site_repo.return_value.get_site_by_key.side_effect = RuntimeError("boom")
        deps.get_weather_forecast_repo.return_value = MagicMock()
        deps.get_membership_repo.return_value = MagicMock()
        deps.get_notification_service.return_value = _make_service(MagicMock())

        result = module.evaluate_forecast_frost_warnings()

        assert result["status"] == "ok"
        assert result["errors"] == 1
        assert result["notified"] == 0
