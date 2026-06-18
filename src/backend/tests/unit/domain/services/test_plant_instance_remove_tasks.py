"""Tests for task cleanup when a plant is removed (REQ-006 cascade).

When a plant is removed (soft delete), its still-open tasks must be deleted
from the queue so they no longer surface as orphaned work. Completed, skipped
and failed tasks are kept as history.
"""

from unittest.mock import MagicMock

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
        self.plant_repo.get_by_key.return_value = self.plant
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
        self.task_repo.get_tasks_for_plant.assert_called_once_with("plant-1")
