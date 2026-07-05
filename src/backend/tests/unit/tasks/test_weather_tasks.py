"""Unit tests for the REQ-046 ``fetch_weather_forecasts`` Celery task.

Mocks ``app.common.dependencies`` (imported lazily inside the task body) and
stubs the resolver so no real adapter / HTTP / DB is touched.
"""

import sys
from datetime import UTC, datetime
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.domain.models.weather import WeatherForecast


@pytest.fixture
def task_module(monkeypatch):
    mock_deps = ModuleType("app.common.dependencies")
    mock_deps.get_weather_source_config_repo = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_weather_forecast_repo = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_encryption_engine = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_ha_client = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_site_repo = MagicMock()  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "app.common.dependencies", mock_deps)

    import app.tasks.weather_tasks as module

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
