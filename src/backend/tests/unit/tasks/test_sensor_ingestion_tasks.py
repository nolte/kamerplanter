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
    mock_deps.get_observation_service = MagicMock()  # type: ignore[attr-defined]
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
        deps.get_observation_repo.return_value = obs_repo
        service = MagicMock()
        service.owning_tenant_key.return_value = "t1"
        service.record_readings_batch.return_value = 1
        deps.get_observation_service.return_value = service

        sensor_repo = MagicMock()
        db = MagicMock()
        # A sensor document carries no tenant_key: its owner is its parent's (#1944).
        db.aql.execute.return_value = iter(
            [{"_key": "s1", "metric_type": "temperature", "ha_entity_id": "sensor.temp", "site_key": "site-1"}]
        )
        sensor_repo._db = db
        deps.get_sensor_repo.return_value = sensor_repo

        result = module.ingest_ha_readings()

        assert result == {"status": "ok", "inserted": 1, "errors": 0, "skipped": 0}
        service.record_readings_batch.assert_called_once()
        (sensor_key, readings), kwargs = service.record_readings_batch.call_args
        assert (sensor_key, kwargs) == ("s1", {"tenant_key": "t1"})
        assert readings[0].value == 21.5
        assert readings[0].source == "ha_auto"
        assert readings[0].tenant_key == "t1", "the reading must carry the tenant the sensor's parent belongs to"

    def test_the_poll_skips_what_the_service_refuses_and_counts_it(self, _task_module, monkeypatch):
        """No owner (no parent, or a delete began) and a sensor erased during the wait are skipped, not errors."""
        from app.common.exceptions import NotFoundError

        module, deps = _task_module
        _enable_timescaledb(monkeypatch, module)
        ha_client = MagicMock()
        ha_client.get_state.return_value = {"value": 1.0, "unit": None}
        deps.get_ha_client.return_value = ha_client
        obs_repo = MagicMock()
        obs_repo.is_available.return_value = True
        deps.get_observation_repo.return_value = obs_repo
        service = MagicMock()
        service.owning_tenant_key.side_effect = [None, "t1", "t1"]
        service.record_readings_batch.side_effect = [NotFoundError("Sensor", "s2"), 1]
        deps.get_observation_service.return_value = service
        sensor_repo = MagicMock()
        sensor_repo._db.aql.execute.return_value = iter(
            [{"_key": key, "ha_entity_id": f"sensor.{key}", "metric_type": "t"} for key in ("s1", "s2", "s3")]
        )
        deps.get_sensor_repo.return_value = sensor_repo

        result = module.ingest_ha_readings()

        assert result == {"status": "ok", "inserted": 1, "errors": 0, "skipped": 2}

    def test_the_poll_does_not_select_a_sensor_whose_delete_began(self, _task_module, monkeypatch):
        module, deps = _task_module
        _enable_timescaledb(monkeypatch, module)
        deps.get_ha_client.return_value = MagicMock()
        obs_repo = MagicMock()
        obs_repo.is_available.return_value = True
        deps.get_observation_repo.return_value = obs_repo
        sensor_repo = MagicMock()
        sensor_repo._db.aql.execute.return_value = iter([])
        deps.get_sensor_repo.return_value = sensor_repo

        module.ingest_ha_readings()

        query = sensor_repo._db.aql.execute.call_args.args[0]
        assert "deletion_pending != true" in query

    def test_counts_ha_errors_without_crashing(self, _task_module, monkeypatch):
        module, deps = _task_module
        _enable_timescaledb(monkeypatch, module)

        ha_client = MagicMock()
        ha_client.get_state.side_effect = RuntimeError("ha down")
        deps.get_ha_client.return_value = ha_client

        obs_repo = MagicMock()
        obs_repo.is_available.return_value = True
        deps.get_observation_repo.return_value = obs_repo
        service = MagicMock()
        service.owning_tenant_key.return_value = "t1"
        deps.get_observation_service.return_value = service

        sensor_repo = MagicMock()
        db = MagicMock()
        db.aql.execute.return_value = iter(
            [{"_key": "s1", "metric_type": "temperature", "ha_entity_id": "sensor.temp"}]
        )
        sensor_repo._db = db
        deps.get_sensor_repo.return_value = sensor_repo

        result = module.ingest_ha_readings()

        assert result == {"status": "ok", "inserted": 0, "errors": 1, "skipped": 0}
        service.record_readings_batch.assert_not_called()
