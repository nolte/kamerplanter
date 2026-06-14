"""Unit tests for watering Celery tasks (Gießplan-Workflow).

Mocks ``app.common.dependencies`` and the ``WateringScheduleEngine`` before the
task runs so no ArangoDB / Redis connection is opened. Collaborators are
doubled with ``MagicMock``. Tests assert observable behaviour: the result dict
and which repo methods are invoked with which task payloads.
"""

import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _mock_dependencies(monkeypatch):
    """Install a mock ``app.common.dependencies`` module."""
    mock_deps = ModuleType("app.common.dependencies")
    mock_deps.get_planting_run_repo = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_task_repo = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_nutrient_plan_repo = MagicMock()  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "app.common.dependencies", mock_deps)

    yield mock_deps


def _legacy_run(**overrides):
    """A single-plan run row as returned by get_active_runs_with_schedule."""
    data = {
        "run_key": "run_1",
        "run_name": "Tomatoes",
        "tenant_key": "tenant_1",
        "watering_schedule": {
            "schedule_mode": "interval",
            "interval_days": 2,
            "preferred_time": "08:00",
        },
        "plan_key": None,
    }
    data.update(overrides)
    return data


class TestGenerateWateringTasks:
    def test_no_active_runs(self, _mock_dependencies):
        run_repo = MagicMock()
        run_repo.get_active_runs_with_schedule.return_value = []
        _mock_dependencies.get_planting_run_repo.return_value = run_repo
        _mock_dependencies.get_task_repo.return_value = MagicMock()
        _mock_dependencies.get_nutrient_plan_repo.return_value = MagicMock()

        from app.tasks.watering_tasks import generate_watering_tasks

        result = generate_watering_tasks()

        assert result == {"created": 0, "skipped": 0}

    def test_skips_run_with_invalid_schedule(self, _mock_dependencies):
        run_repo = MagicMock()
        run_repo.get_active_runs_with_schedule.return_value = [
            _legacy_run(watering_schedule={"interval_days": "not-a-number"})
        ]
        _mock_dependencies.get_planting_run_repo.return_value = run_repo
        _mock_dependencies.get_task_repo.return_value = MagicMock()
        _mock_dependencies.get_nutrient_plan_repo.return_value = MagicMock()

        from app.tasks.watering_tasks import generate_watering_tasks

        result = generate_watering_tasks()

        assert result == {"created": 0, "skipped": 0}

    def test_creates_legacy_task_when_due(self, _mock_dependencies):
        run_repo = MagicMock()
        run_repo.get_active_runs_with_schedule.return_value = [_legacy_run()]
        _mock_dependencies.get_planting_run_repo.return_value = run_repo

        task_repo = MagicMock()
        task_repo.find_by_field.return_value = []  # no completed history, no existing task
        _mock_dependencies.get_task_repo.return_value = task_repo

        _mock_dependencies.get_nutrient_plan_repo.return_value = MagicMock()

        with patch("app.domain.engines.watering_schedule_engine.WateringScheduleEngine") as engine_cls:
            engine_cls.return_value.is_watering_due.return_value = True

            from app.tasks.watering_tasks import generate_watering_tasks

            result = generate_watering_tasks()

        assert result == {"created": 1, "skipped": 0}
        task_repo.create.assert_called_once()
        created = task_repo.create.call_args.args[0]
        assert created.name.startswith("watering:run_1:")
        assert created.tenant_key == "tenant_1"
        assert created.instruction == "Scheduled watering for run Tomatoes"

    def test_not_due_creates_nothing(self, _mock_dependencies):
        run_repo = MagicMock()
        run_repo.get_active_runs_with_schedule.return_value = [_legacy_run()]
        _mock_dependencies.get_planting_run_repo.return_value = run_repo

        task_repo = MagicMock()
        task_repo.find_by_field.return_value = []
        _mock_dependencies.get_task_repo.return_value = task_repo
        _mock_dependencies.get_nutrient_plan_repo.return_value = MagicMock()

        with patch("app.domain.engines.watering_schedule_engine.WateringScheduleEngine") as engine_cls:
            engine_cls.return_value.is_watering_due.return_value = False

            from app.tasks.watering_tasks import generate_watering_tasks

            result = generate_watering_tasks()

        assert result == {"created": 0, "skipped": 0}
        task_repo.create.assert_not_called()

    def test_multi_channel_creates_per_channel_task(self, _mock_dependencies):
        from types import SimpleNamespace

        run_repo = MagicMock()
        run_repo.get_active_runs_with_schedule.return_value = [_legacy_run(plan_key="plan_1")]
        _mock_dependencies.get_planting_run_repo.return_value = run_repo

        task_repo = MagicMock()
        task_repo.find_by_field.return_value = []
        _mock_dependencies.get_task_repo.return_value = task_repo

        channel = SimpleNamespace(
            channel_id="root",
            enabled=True,
            label="Root zone",
            schedule=SimpleNamespace(preferred_time="07:30"),
            application_method=SimpleNamespace(value="fertigation"),
        )
        nutrient_plan_repo = MagicMock()
        nutrient_plan_repo.get_phase_entries.return_value = [SimpleNamespace(delivery_channels=[channel])]
        _mock_dependencies.get_nutrient_plan_repo.return_value = nutrient_plan_repo

        with patch("app.domain.engines.watering_schedule_engine.WateringScheduleEngine") as engine_cls:
            engine_cls.return_value.is_watering_due.return_value = True

            from app.tasks.watering_tasks import generate_watering_tasks

            result = generate_watering_tasks()

        assert result == {"created": 1, "skipped": 0}
        task_repo.create.assert_called_once()
        created = task_repo.create.call_args.args[0]
        assert created.name.startswith("watering:run_1:root:")
        assert "Root zone" in created.instruction

    def test_multi_channel_skips_disabled_channel(self, _mock_dependencies):
        from types import SimpleNamespace

        run_repo = MagicMock()
        run_repo.get_active_runs_with_schedule.return_value = [_legacy_run(plan_key="plan_1")]
        _mock_dependencies.get_planting_run_repo.return_value = run_repo

        task_repo = MagicMock()
        task_repo.find_by_field.return_value = []
        _mock_dependencies.get_task_repo.return_value = task_repo

        channel = SimpleNamespace(channel_id="root", enabled=False, schedule=None)
        nutrient_plan_repo = MagicMock()
        nutrient_plan_repo.get_phase_entries.return_value = [SimpleNamespace(delivery_channels=[channel])]
        _mock_dependencies.get_nutrient_plan_repo.return_value = nutrient_plan_repo

        with patch("app.domain.engines.watering_schedule_engine.WateringScheduleEngine") as engine_cls:
            engine_cls.return_value.is_watering_due.return_value = True

            from app.tasks.watering_tasks import generate_watering_tasks

            result = generate_watering_tasks()

        assert result == {"created": 0, "skipped": 0}
        task_repo.create.assert_not_called()

    def test_idempotent_skip_when_task_already_exists(self, _mock_dependencies):
        run_repo = MagicMock()
        run_repo.get_active_runs_with_schedule.return_value = [_legacy_run()]
        _mock_dependencies.get_planting_run_repo.return_value = run_repo

        task_repo = MagicMock()

        def _find_by_field(field, value):
            # No completed history for the date lookup; a duplicate for the name check.
            if field == "name":
                return [{"_key": "existing"}]
            return []

        task_repo.find_by_field.side_effect = _find_by_field
        _mock_dependencies.get_task_repo.return_value = task_repo
        _mock_dependencies.get_nutrient_plan_repo.return_value = MagicMock()

        with patch("app.domain.engines.watering_schedule_engine.WateringScheduleEngine") as engine_cls:
            engine_cls.return_value.is_watering_due.return_value = True

            from app.tasks.watering_tasks import generate_watering_tasks

            result = generate_watering_tasks()

        assert result == {"created": 0, "skipped": 1}
        task_repo.create.assert_not_called()


class TestFindLastCompletedDate:
    def test_returns_none_when_no_completed_tasks(self, _mock_dependencies):
        from app.tasks.watering_tasks import _find_last_completed_date

        task_repo = MagicMock()
        task_repo.find_by_field.return_value = []

        result = _find_last_completed_date(task_repo, "run_1", "watering:run_1:")

        assert result is None

    def test_returns_date_of_latest_completed_task(self, _mock_dependencies):
        from datetime import date

        from app.common.enums import TaskCategory, TaskStatus
        from app.tasks.watering_tasks import _find_last_completed_date

        task_repo = MagicMock()
        task_repo.find_by_field.return_value = [
            {
                "category": TaskCategory.FEEDING.value,
                "name": "watering:run_1:2026-06-10",
                "status": TaskStatus.COMPLETED.value,
                "completed_at": "2026-06-10T08:00:00+00:00",
            },
        ]

        result = _find_last_completed_date(task_repo, "run_1", "watering:run_1:")

        assert result == date(2026, 6, 10)

    def test_ignores_non_matching_prefix(self, _mock_dependencies):
        from app.common.enums import TaskCategory, TaskStatus
        from app.tasks.watering_tasks import _find_last_completed_date

        task_repo = MagicMock()
        task_repo.find_by_field.return_value = [
            {
                "category": TaskCategory.FEEDING.value,
                "name": "watering:run_1:ch_a:2026-06-10",
                "status": TaskStatus.COMPLETED.value,
                "completed_at": "2026-06-10T08:00:00+00:00",
            },
        ]

        result = _find_last_completed_date(task_repo, "run_1", "watering:run_1:ch_b:")

        assert result is None
        # The history lookup must query by planting_run_key — a changed field
        # would silently match the wrong tasks.
        task_repo.find_by_field.assert_called_once_with("planting_run_key", "run_1")
