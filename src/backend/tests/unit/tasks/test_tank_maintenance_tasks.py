"""Unit tests for tank maintenance Celery tasks (REQ-014, REQ-004-A).

Mocks ``app.common.dependencies`` (and ``TankEngine``) before importing the
task functions so the ArangoDB import chain is never triggered. Collaborators
are doubled with ``MagicMock`` — no real database, broker or HA client is
touched. Tests assert observable behaviour: the result dict and which repo /
engine methods are invoked.
"""

import sys
from datetime import UTC, datetime, timedelta
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _mock_dependencies(monkeypatch):
    """Install a mock ``app.common.dependencies`` module.

    The task module imports its dependency getters lazily inside the function
    body, so installing the mock module before the task runs is sufficient.
    """
    mock_deps = ModuleType("app.common.dependencies")
    mock_deps.get_tank_repo = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_task_repo = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_ha_client = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_sensor_repo = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_feeding_repo = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_plant_repo = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_db = MagicMock()  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "app.common.dependencies", mock_deps)

    yield mock_deps


def _schedule(**overrides):
    """Build a MaintenanceSchedule double with sensible defaults."""
    defaults = {
        "tank_key": "tank_1",
        "maintenance_type": "water_change",
        "interval_days": 7,
        "reminder_days_before": 0,
        "instructions": None,
        "priority": SimpleNamespace(value="medium"),
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class TestGenerateTankMaintenanceTasks:
    def test_no_schedules_creates_nothing(self, _mock_dependencies):
        tank_repo = MagicMock()
        tank_repo.get_active_auto_create_schedules.return_value = []
        _mock_dependencies.get_tank_repo.return_value = tank_repo
        _mock_dependencies.get_task_repo.return_value = MagicMock()

        from app.tasks.tank_maintenance_tasks import generate_tank_maintenance_tasks

        result = generate_tank_maintenance_tasks()

        assert result == {"created": 0, "skipped": 0}

    def test_creates_task_when_never_performed(self, _mock_dependencies):
        tank_repo = MagicMock()
        tank_repo.get_active_auto_create_schedules.return_value = [_schedule()]
        tank_repo.get_last_maintenance_by_type.return_value = None
        tank_repo.get_by_key.return_value = SimpleNamespace(name="Res 1", tenant_key="tenant_1")
        _mock_dependencies.get_tank_repo.return_value = tank_repo

        task_repo = MagicMock()
        task_repo.get_all_tasks.return_value = ([], 0)
        _mock_dependencies.get_task_repo.return_value = task_repo

        from app.tasks.tank_maintenance_tasks import generate_tank_maintenance_tasks

        result = generate_tank_maintenance_tasks()

        assert result == {"created": 1, "skipped": 0}
        task_repo.create_task.assert_called_once()
        created = task_repo.create_task.call_args.args[0]
        assert created.name == "maintenance:water_change:tank_1"
        assert created.tenant_key == "tenant_1"

    def test_skips_schedule_without_tank_key(self, _mock_dependencies):
        tank_repo = MagicMock()
        tank_repo.get_active_auto_create_schedules.return_value = [_schedule(tank_key=None)]
        _mock_dependencies.get_tank_repo.return_value = tank_repo
        _mock_dependencies.get_task_repo.return_value = MagicMock()

        from app.tasks.tank_maintenance_tasks import generate_tank_maintenance_tasks

        result = generate_tank_maintenance_tasks()

        assert result == {"created": 0, "skipped": 0}
        tank_repo.get_last_maintenance_by_type.assert_not_called()

    def test_skips_when_not_yet_due(self, _mock_dependencies):
        last_log = SimpleNamespace(performed_at=datetime.now(UTC) - timedelta(days=1))
        tank_repo = MagicMock()
        tank_repo.get_active_auto_create_schedules.return_value = [_schedule(interval_days=7)]
        tank_repo.get_last_maintenance_by_type.return_value = last_log
        _mock_dependencies.get_tank_repo.return_value = tank_repo
        _mock_dependencies.get_task_repo.return_value = MagicMock()

        from app.tasks.tank_maintenance_tasks import generate_tank_maintenance_tasks

        result = generate_tank_maintenance_tasks()

        assert result == {"created": 0, "skipped": 0}

    def test_idempotent_skip_when_task_exists(self, _mock_dependencies):
        from app.common.enums import TaskCategory, TaskStatus

        existing_task = SimpleNamespace(
            name="maintenance:water_change:tank_1",
            status=TaskStatus.PENDING,
        )
        tank_repo = MagicMock()
        tank_repo.get_active_auto_create_schedules.return_value = [_schedule()]
        tank_repo.get_last_maintenance_by_type.return_value = None
        _mock_dependencies.get_tank_repo.return_value = tank_repo

        task_repo = MagicMock()
        task_repo.get_all_tasks.return_value = ([existing_task], 1)
        _mock_dependencies.get_task_repo.return_value = task_repo

        from app.tasks.tank_maintenance_tasks import generate_tank_maintenance_tasks

        result = generate_tank_maintenance_tasks()

        assert result == {"created": 0, "skipped": 1}
        task_repo.create_task.assert_not_called()
        # The existing-task lookup must be scoped to the MAINTENANCE category,
        # otherwise unrelated tasks could suppress maintenance creation.
        assert task_repo.get_all_tasks.call_args.args[2]["category"] == TaskCategory.MAINTENANCE.value


class TestSyncTankStatesFromHa:
    def test_skips_when_ha_not_configured(self, _mock_dependencies):
        _mock_dependencies.get_ha_client.return_value = None

        from app.tasks.tank_maintenance_tasks import sync_tank_states_from_ha

        result = sync_tank_states_from_ha()

        assert result == {"status": "skipped", "reason": "ha_not_configured"}

    def test_skips_tank_without_ha_sensors(self, _mock_dependencies):
        _mock_dependencies.get_ha_client.return_value = MagicMock()
        sensor_repo = MagicMock()
        sensor_repo.find_by_tank.return_value = [SimpleNamespace(ha_entity_id=None, metric_type="ph")]
        _mock_dependencies.get_sensor_repo.return_value = sensor_repo

        tank_repo = MagicMock()
        tank_repo.get_all.return_value = ([SimpleNamespace(key="tank_1")], 1)
        _mock_dependencies.get_tank_repo.return_value = tank_repo

        from app.tasks.tank_maintenance_tasks import sync_tank_states_from_ha

        result = sync_tank_states_from_ha()

        assert result == {"updated": 0, "skipped": 1, "errors": 0}
        tank_repo.create_state.assert_not_called()

    def test_persists_state_from_ha_values(self, _mock_dependencies):
        ha_client = MagicMock()
        ha_client.get_state.return_value = {"value": 6.2}
        _mock_dependencies.get_ha_client.return_value = ha_client

        sensor_repo = MagicMock()
        sensor_repo.find_by_tank.return_value = [SimpleNamespace(ha_entity_id="sensor.ph", metric_type="ph")]
        _mock_dependencies.get_sensor_repo.return_value = sensor_repo

        tank_repo = MagicMock()
        tank_repo.get_all.return_value = ([SimpleNamespace(key="tank_1")], 1)
        _mock_dependencies.get_tank_repo.return_value = tank_repo

        from app.tasks.tank_maintenance_tasks import sync_tank_states_from_ha

        result = sync_tank_states_from_ha()

        assert result == {"updated": 1, "skipped": 0, "errors": 0}
        tank_repo.create_state.assert_called_once()
        state = tank_repo.create_state.call_args.args[0]
        assert state.ph == 6.2
        assert state.source == "ha_auto"

    def test_counts_ha_error_without_crashing(self, _mock_dependencies):
        ha_client = MagicMock()
        ha_client.get_state.side_effect = RuntimeError("ha down")
        _mock_dependencies.get_ha_client.return_value = ha_client

        sensor_repo = MagicMock()
        sensor_repo.find_by_tank.return_value = [SimpleNamespace(ha_entity_id="sensor.ph", metric_type="ph")]
        _mock_dependencies.get_sensor_repo.return_value = sensor_repo

        tank_repo = MagicMock()
        tank_repo.get_all.return_value = ([SimpleNamespace(key="tank_1")], 1)
        _mock_dependencies.get_tank_repo.return_value = tank_repo

        from app.tasks.tank_maintenance_tasks import sync_tank_states_from_ha

        result = sync_tank_states_from_ha()

        assert result["errors"] == 1
        assert result["updated"] == 0
        tank_repo.create_state.assert_not_called()


class TestCheckTankAlerts:
    def test_skips_tank_without_state(self, _mock_dependencies):
        tank_repo = MagicMock()
        tank_repo.get_all.return_value = ([SimpleNamespace(key="tank_1", name="Res")], 1)
        tank_repo.get_latest_state.return_value = None
        _mock_dependencies.get_tank_repo.return_value = tank_repo

        with patch("app.domain.engines.tank_engine.TankEngine") as engine_cls:
            from app.tasks.tank_maintenance_tasks import check_tank_alerts

            result = check_tank_alerts()

            engine_cls.return_value.check_alerts.assert_not_called()

        assert result == {"tanks_checked": 0, "total_alerts": 0, "critical_count": 0}

    def test_counts_alerts_and_criticals(self, _mock_dependencies):
        tank_repo = MagicMock()
        tank_repo.get_all.return_value = ([SimpleNamespace(key="tank_1", name="Res")], 1)
        tank_repo.get_latest_state.return_value = SimpleNamespace()
        tank_repo.get_latest_full_change.return_value = None
        _mock_dependencies.get_tank_repo.return_value = tank_repo

        with patch("app.domain.engines.tank_engine.TankEngine") as engine_cls:
            engine_cls.return_value.check_alerts.return_value = [
                {"type": "ph_low", "severity": "critical"},
                {"type": "ec_high", "severity": "warning"},
            ]

            from app.tasks.tank_maintenance_tasks import check_tank_alerts

            result = check_tank_alerts()

        assert result == {"tanks_checked": 1, "total_alerts": 2, "critical_count": 1}


class TestCheckRunoffTrends:
    def _feeding_repo_with_high_runoff(self, count_high):
        events = []
        for i in range(5):
            ratio_high = i < count_high
            events.append(
                SimpleNamespace(
                    runoff_ec=1.4 if ratio_high else 1.0,
                    measured_ec_before=1.0,
                )
            )
        repo = MagicMock()
        repo.get_recent_runoff_events.return_value = events
        return repo

    def test_no_active_plants(self, _mock_dependencies):
        db = MagicMock()
        db.aql.execute.return_value = iter([])
        _mock_dependencies.get_db.return_value = db
        _mock_dependencies.get_feeding_repo.return_value = MagicMock()
        _mock_dependencies.get_task_repo.return_value = MagicMock()

        from app.tasks.tank_maintenance_tasks import check_runoff_trends

        result = check_runoff_trends()

        assert result == {"plants_checked": 0, "created": 0, "skipped": 0}

    def test_query_excludes_removed_plants(self, _mock_dependencies):
        """The plant lookup must filter out removed plants in AQL."""
        db = MagicMock()
        db.aql.execute.return_value = iter([])
        _mock_dependencies.get_db.return_value = db
        _mock_dependencies.get_feeding_repo.return_value = MagicMock()
        _mock_dependencies.get_task_repo.return_value = MagicMock()

        from app.tasks.tank_maintenance_tasks import check_runoff_trends

        check_runoff_trends()

        query = db.aql.execute.call_args.args[0]
        assert "removed_on == null" in query

    def test_creates_flush_task_when_trend_detected(self, _mock_dependencies):
        db = MagicMock()
        # The plant sweep projects the owning tenant alongside the key since
        # #927 — the feeding lookup below is tenant-scoped.
        db.aql.execute.return_value = iter([{"key": "plant_1", "tenant_key": "tenant_1"}])
        _mock_dependencies.get_db.return_value = db

        _mock_dependencies.get_feeding_repo.return_value = self._feeding_repo_with_high_runoff(3)

        task_repo = MagicMock()
        task_repo.get_all_tasks.return_value = ([], 0)
        _mock_dependencies.get_task_repo.return_value = task_repo

        from app.tasks.tank_maintenance_tasks import check_runoff_trends

        result = check_runoff_trends()

        assert result == {"plants_checked": 1, "created": 1, "skipped": 0}
        task_repo.create_task.assert_called_once()
        created = task_repo.create_task.call_args.args[0]
        assert created.name == "flush:runoff_trend:plant_1"
        # The tenant comes off the same row that selected the plant (#927) and is
        # both stamped on the task and used to scope the feeding lookup.
        assert created.tenant_key == "tenant_1"
        feeding_repo = _mock_dependencies.get_feeding_repo.return_value
        assert feeding_repo.get_recent_runoff_events.call_args.kwargs["tenant_key"] == "tenant_1"

    def test_no_task_when_trend_below_threshold(self, _mock_dependencies):
        db = MagicMock()
        # The plant sweep projects the owning tenant alongside the key since
        # #927 — the feeding lookup below is tenant-scoped.
        db.aql.execute.return_value = iter([{"key": "plant_1", "tenant_key": "tenant_1"}])
        _mock_dependencies.get_db.return_value = db

        _mock_dependencies.get_feeding_repo.return_value = self._feeding_repo_with_high_runoff(2)
        _mock_dependencies.get_task_repo.return_value = MagicMock()
        _mock_dependencies.get_plant_repo.return_value = MagicMock()

        from app.tasks.tank_maintenance_tasks import check_runoff_trends

        result = check_runoff_trends()

        assert result == {"plants_checked": 1, "created": 0, "skipped": 0}

    def test_tenantless_plant_is_skipped_instead_of_read_unscoped(self, _mock_dependencies):
        """Fail closed on a plant without a tenant (#927).

        The feeding lookup rejects the empty ``tenant_key`` sentinel, so the sweep
        skips such a plant and counts it as skipped rather than widening the query
        back to every tenant's feeding events.
        """
        db = MagicMock()
        db.aql.execute.return_value = iter([{"key": "plant_orphan", "tenant_key": ""}])
        _mock_dependencies.get_db.return_value = db

        feeding_repo = MagicMock()
        _mock_dependencies.get_feeding_repo.return_value = feeding_repo
        _mock_dependencies.get_task_repo.return_value = MagicMock()

        from app.tasks.tank_maintenance_tasks import check_runoff_trends

        result = check_runoff_trends()

        assert result == {"plants_checked": 1, "created": 0, "skipped": 1}
        feeding_repo.get_recent_runoff_events.assert_not_called()

    def test_skips_plant_with_too_few_events(self, _mock_dependencies):
        db = MagicMock()
        # The plant sweep projects the owning tenant alongside the key since
        # #927 — the feeding lookup below is tenant-scoped.
        db.aql.execute.return_value = iter([{"key": "plant_1", "tenant_key": "tenant_1"}])
        _mock_dependencies.get_db.return_value = db

        feeding_repo = MagicMock()
        feeding_repo.get_recent_runoff_events.return_value = [SimpleNamespace(runoff_ec=1.4, measured_ec_before=1.0)]
        _mock_dependencies.get_feeding_repo.return_value = feeding_repo
        _mock_dependencies.get_task_repo.return_value = MagicMock()
        _mock_dependencies.get_plant_repo.return_value = MagicMock()

        from app.tasks.tank_maintenance_tasks import check_runoff_trends

        result = check_runoff_trends()

        assert result == {"plants_checked": 1, "created": 0, "skipped": 0}
