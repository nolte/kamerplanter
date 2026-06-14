"""Unit tests for sensor ingestion Celery task (REQ-005).

Mocks ``app.common.dependencies`` (imported lazily inside the task body) and
overrides ``settings.timescaledb_enabled`` on the task module directly. No real
TimescaleDB, ArangoDB or HA client is touched. Tests assert the result dict and
the early-return guard branches.
"""

import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest


@pytest.fixture(autouse=True)
def _task_module(monkeypatch):
    """Install mock dependencies and import the task module once.

    Returns ``(module, deps)``. ``settings`` is left in place; individual tests
    toggle ``settings.timescaledb_enabled`` via ``monkeypatch.setattr`` so each
    test controls the TimescaleDB guard without replacing the whole singleton.
    """
    mock_deps = ModuleType("app.common.dependencies")
    mock_deps.get_ha_client = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_observation_repo = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_sensor_repo = MagicMock()  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "app.common.dependencies", mock_deps)

    import app.tasks.sensor_ingestion_tasks as module

    yield module, mock_deps


def _enable_timescaledb(monkeypatch, module):
    monkeypatch.setattr(module.settings, "timescaledb_enabled", True, raising=False)


class TestIngestHaReadings:
    def test_skipped_when_timescaledb_disabled(self, _task_module, monkeypatch):
        module, _deps = _task_module
        monkeypatch.setattr(module.settings, "timescaledb_enabled", False, raising=False)

        result = module.ingest_ha_readings()

        assert result == {"status": "skipped", "reason": "timescaledb_disabled"}

    def test_skipped_when_ha_not_configured(self, _task_module, monkeypatch):
        module, deps = _task_module
        _enable_timescaledb(monkeypatch, module)
        deps.get_ha_client.return_value = None

        result = module.ingest_ha_readings()

        assert result == {"status": "skipped", "reason": "ha_not_configured"}

    def test_error_when_timescaledb_unavailable(self, _task_module, monkeypatch):
        module, deps = _task_module
        _enable_timescaledb(monkeypatch, module)
        deps.get_ha_client.return_value = MagicMock()
        obs_repo = MagicMock()
        obs_repo.is_available.return_value = False
        deps.get_observation_repo.return_value = obs_repo
        deps.get_sensor_repo.return_value = MagicMock()

        result = module.ingest_ha_readings()

        assert result == {"status": "error", "reason": "timescaledb_unavailable"}

    def test_inserts_readings_from_active_sensors(self, _task_module, monkeypatch):
        module, deps = _task_module
        _enable_timescaledb(monkeypatch, module)

        ha_client = MagicMock()
        ha_client.get_state.return_value = {"value": 21.5, "unit": "°C"}
        deps.get_ha_client.return_value = ha_client

        obs_repo = MagicMock()
        obs_repo.is_available.return_value = True
        obs_repo.insert_batch.return_value = 1
        deps.get_observation_repo.return_value = obs_repo

        sensor_repo = MagicMock()
        db = MagicMock()
        db.aql.execute.return_value = iter(
            [{"_key": "s1", "tenant_key": "t1", "metric_type": "temperature", "ha_entity_id": "sensor.temp"}]
        )
        sensor_repo._db = db
        deps.get_sensor_repo.return_value = sensor_repo

        result = module.ingest_ha_readings()

        assert result == {"status": "ok", "inserted": 1, "errors": 0}
        obs_repo.insert_batch.assert_called_once()
        readings = obs_repo.insert_batch.call_args.args[0]
        assert readings[0].value == 21.5
        assert readings[0].source == "ha_auto"

    def test_counts_ha_errors_without_crashing(self, _task_module, monkeypatch):
        module, deps = _task_module
        _enable_timescaledb(monkeypatch, module)

        ha_client = MagicMock()
        ha_client.get_state.side_effect = RuntimeError("ha down")
        deps.get_ha_client.return_value = ha_client

        obs_repo = MagicMock()
        obs_repo.is_available.return_value = True
        deps.get_observation_repo.return_value = obs_repo

        sensor_repo = MagicMock()
        db = MagicMock()
        db.aql.execute.return_value = iter(
            [{"_key": "s1", "tenant_key": "t1", "metric_type": "temperature", "ha_entity_id": "sensor.temp"}]
        )
        sensor_repo._db = db
        deps.get_sensor_repo.return_value = sensor_repo

        result = module.ingest_ha_readings()

        assert result == {"status": "ok", "inserted": 0, "errors": 1}
        obs_repo.insert_batch.assert_not_called()
