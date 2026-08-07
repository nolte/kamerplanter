"""Tests for task cleanup when a plant is removed (REQ-006 cascade).

When a plant is removed (soft delete), its still-open tasks must be deleted
from the queue so they no longer surface as orphaned work. Completed, skipped
and failed tasks are kept as history.
"""

from unittest.mock import MagicMock

import structlog.testing

from app.domain.models.task import Task
from app.domain.services.plant_instance_service import PlantInstanceService


def _make_task(key: str, status: str) -> Task:
    return Task(_key=key, name=f"task-{key}", status=status)


class TestRemovePlantTaskCleanup:
    def setup_method(self):
        self.plant_repo = MagicMock()
        self.site_repo = MagicMock()
        self.rotation = MagicMock()
        self.companion = MagicMock()
        self.task_repo = MagicMock()

        # The plant being removed has no slot, keeping the slot-release path
        # out of scope for these tests.
        self.plant = MagicMock()
        self.plant.slot_key = None
        # The task cascade is tenant-scoped since #927 and reads the tenant off
        # the plant being removed, so the double has to carry a real one.
        self.plant.tenant_key = "tenant-a"
        self.plant_repo.get_by_key.return_value = self.plant
        # ``remove_plant`` loads through ``get_or_raise``; the double has to
        # answer there too, or the tenant read off the plant is a MagicMock.
        self.plant_repo.get_or_raise.return_value = self.plant
        self.plant_repo.update.return_value = self.plant

    def _service(self, task_repo=None) -> PlantInstanceService:
        return PlantInstanceService(
            self.plant_repo,
            self.site_repo,
            self.rotation,
            self.companion,
            task_repo=task_repo,
        )

    def test_deletes_open_tasks(self):
        """Pending, in_progress and dormant tasks are deleted on removal."""
        self.task_repo.get_tasks_for_plant.return_value = [
            _make_task("t-pending", "pending"),
            _make_task("t-progress", "in_progress"),
            _make_task("t-dormant", "dormant"),
        ]
        service = self._service(task_repo=self.task_repo)

        service.remove_plant("plant-1")

        deleted_keys = {c.args[0] for c in self.task_repo.delete_task.call_args_list}
        assert deleted_keys == {"t-pending", "t-progress", "t-dormant"}

    def test_keeps_history_tasks(self):
        """Completed, skipped and failed tasks are retained as history."""
        self.task_repo.get_tasks_for_plant.return_value = [
            _make_task("t-done", "completed"),
            _make_task("t-skipped", "skipped"),
            _make_task("t-failed", "failed"),
            _make_task("t-open", "pending"),
        ]
        service = self._service(task_repo=self.task_repo)

        service.remove_plant("plant-1")

        deleted_keys = {c.args[0] for c in self.task_repo.delete_task.call_args_list}
        assert deleted_keys == {"t-open"}

    def test_no_task_repo_is_noop(self):
        """Without a task repository, removal still succeeds without error."""
        service = self._service(task_repo=None)

        result = service.remove_plant("plant-1")

        assert result is self.plant

    def test_returns_removed_plant(self):
        """remove_plant returns the updated plant after task cleanup."""
        self.task_repo.get_tasks_for_plant.return_value = []
        service = self._service(task_repo=self.task_repo)

        result = service.remove_plant("plant-1")

        assert result is self.plant
        self.task_repo.get_tasks_for_plant.assert_called_once_with("plant-1", tenant_key="tenant-a")


class TestRemovePlantRunTaskCleanup:
    """Watering/feeding tasks hang off the planting run, not the instance.

    They are cleaned up only once the run has no active instances left, since a
    run may contain several plants and keeps needing those tasks while any
    sibling is still growing.
    """

    def setup_method(self):
        self.plant_repo = MagicMock()
        self.site_repo = MagicMock()
        self.rotation = MagicMock()
        self.companion = MagicMock()
        self.task_repo = MagicMock()
        self.run_repo = MagicMock()

        self.plant = MagicMock()
        self.plant.slot_key = None
        self.plant.tenant_key = "tenant-a"
        self.plant_repo.get_by_key.return_value = self.plant
        self.plant_repo.get_or_raise.return_value = self.plant
        self.plant_repo.update.return_value = self.plant
        # Isolate the run-scoped path: the plant-scoped cascade finds nothing.
        self.task_repo.get_tasks_for_plant.return_value = []

    def _service(self) -> PlantInstanceService:
        return PlantInstanceService(
            self.plant_repo,
            self.site_repo,
            self.rotation,
            self.companion,
            task_repo=self.task_repo,
            planting_run_repo=self.run_repo,
        )

    @staticmethod
    def _run(key: str = "run-1") -> MagicMock:
        run = MagicMock()
        run.key = key
        return run

    def test_deletes_open_run_tasks_when_no_active_siblings(self):
        self.run_repo.get_runs_for_plant.return_value = [self._run("run-1")]
        # Every instance of the run is removed (the just-removed plant carries
        # removed_on); only open run tasks should be deleted, history kept.
        self.run_repo.get_run_plants.return_value = [
            {"_key": "plant-1", "removed_on": "2026-06-30"},
        ]
        self.task_repo.get_tasks_for_run.return_value = [
            _make_task("w-open", "pending"),
            _make_task("w-done", "completed"),
        ]
        service = self._service()

        service.remove_plant("plant-1")

        deleted = {c.args[0] for c in self.task_repo.delete_task.call_args_list}
        assert deleted == {"w-open"}

    def test_keeps_run_tasks_while_active_sibling_remains(self):
        self.run_repo.get_runs_for_plant.return_value = [self._run("run-1")]
        self.run_repo.get_run_plants.return_value = [
            {"_key": "plant-1", "removed_on": "2026-06-30"},
            {"_key": "plant-2", "removed_on": None},  # still active
        ]
        service = self._service()

        service.remove_plant("plant-1")

        self.task_repo.get_tasks_for_run.assert_not_called()
        self.task_repo.delete_task.assert_not_called()

    def test_without_run_repo_run_cleanup_is_noop(self):
        service = PlantInstanceService(
            self.plant_repo,
            self.site_repo,
            self.rotation,
            self.companion,
            task_repo=self.task_repo,
        )

        result = service.remove_plant("plant-1")

        assert result is self.plant

    def test_the_run_task_lookup_carries_the_plants_tenant(self):
        """#952 — ``get_tasks_for_run`` was the last unscoped scan over ``tasks``."""
        self.run_repo.get_runs_for_plant.return_value = [self._run("run-1")]
        self.run_repo.get_run_plants.return_value = [{"_key": "plant-1", "removed_on": "2026-06-30"}]
        self.task_repo.get_tasks_for_run.return_value = []
        service = self._service()

        service.remove_plant("plant-1")

        self.task_repo.get_tasks_for_run.assert_called_once_with("run-1", tenant_key="tenant-a")


class TestATenantlessPlantSaysSoInsteadOfSkippingSilently:
    """#952 — fail-closed here **omits work that must happen**, so it must be loud.

    Both cleanups are skipped for a plant with no tenant, because the task reads
    behind them are tenant-scoped since #927/#952 and a tenantless read would be
    the cross-tenant scan those fixes remove. But skipping means the removed
    plant's open tasks — including its REQ-022 care reminders — stay in the queue
    forever. Previously that happened with no signal at all; the Celery sweep's
    ``runoff_trend_check_skipped_tenantless_plant`` is the pattern followed here.
    """

    def setup_method(self):
        self.plant_repo = MagicMock()
        self.task_repo = MagicMock()
        self.run_repo = MagicMock()

        self.plant = MagicMock()
        self.plant.slot_key = None
        self.plant.tenant_key = ""  # a legacy, un-backfilled instance
        self.plant_repo.get_by_key.return_value = self.plant
        self.plant_repo.get_or_raise.return_value = self.plant
        self.plant_repo.update.return_value = self.plant

    def _service(self) -> PlantInstanceService:
        return PlantInstanceService(
            self.plant_repo,
            MagicMock(),
            MagicMock(),
            MagicMock(),
            task_repo=self.task_repo,
            planting_run_repo=self.run_repo,
        )

    def test_neither_cleanup_runs_an_unscoped_read(self):
        self._service().remove_plant("plant-1")

        self.task_repo.get_tasks_for_plant.assert_not_called()
        self.task_repo.get_tasks_for_run.assert_not_called()

    def test_both_skips_are_logged_rather_than_silent(self):
        with structlog.testing.capture_logs() as logs:
            self._service().remove_plant("plant-1")

        events = {entry["event"] for entry in logs if entry.get("log_level") == "warning"}
        assert "open_task_cleanup_skipped_tenantless_plant" in events
        assert "orphaned_run_task_cleanup_skipped_tenantless_plant" in events
        assert all(entry.get("plant_key") == "plant-1" for entry in logs if entry["event"] in events)
