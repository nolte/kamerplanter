"""Unit tests for the dependency resolver engine."""

from datetime import datetime, timedelta

import pytest

from app.domain.engines.dependency_resolver import DependencyResolver


@pytest.fixture
def engine():
    return DependencyResolver()


def _make_task(key: str, status: str = "pending", priority: str = "medium", due_date: datetime | None = None) -> dict:
    """Helper to create a task dict."""
    task = {
        "key": key,
        "status": status,
        "priority": priority,
    }
    if due_date is not None:
        task["due_date"] = due_date
    return task


def _make_dep(from_key: str, to_key: str) -> dict:
    """Helper to create a dependency edge dict."""
    return {"from_key": from_key, "to_key": to_key}


class TestGetReadyTasks:
    """Tests for the get_ready_tasks method."""

    def test_no_dependencies_all_pending_ready(self, engine):
        """All pending tasks with no dependencies are ready."""
        tasks = [
            _make_task("t1"),
            _make_task("t2"),
            _make_task("t3"),
        ]
        result = engine.get_ready_tasks(tasks, [])
        assert len(result) == 3

    def test_blocked_tasks_excluded(self, engine):
        """Tasks blocked by incomplete dependencies are excluded."""
        tasks = [
            _make_task("t1"),
            _make_task("t2"),
        ]
        deps = [_make_dep("t1", "t2")]  # t2 depends on t1
        result = engine.get_ready_tasks(tasks, deps)
        assert len(result) == 1
        assert result[0]["key"] == "t1"

    def test_completed_deps_unblock(self, engine):
        """Tasks whose dependencies are completed become ready."""
        tasks = [
            _make_task("t1", status="completed"),
            _make_task("t2"),
        ]
        deps = [_make_dep("t1", "t2")]
        result = engine.get_ready_tasks(tasks, deps)
        assert len(result) == 1
        assert result[0]["key"] == "t2"

    def test_skipped_deps_unblock(self, engine):
        """Skipped dependencies also unblock downstream tasks."""
        tasks = [
            _make_task("t1", status="skipped"),
            _make_task("t2"),
        ]
        deps = [_make_dep("t1", "t2")]
        result = engine.get_ready_tasks(tasks, deps)
        assert len(result) == 1
        assert result[0]["key"] == "t2"

    def test_sorted_by_priority(self, engine):
        """Ready tasks are sorted by priority: critical > high > medium > low."""
        tasks = [
            _make_task("low", priority="low"),
            _make_task("critical", priority="critical"),
            _make_task("high", priority="high"),
            _make_task("medium", priority="medium"),
        ]
        result = engine.get_ready_tasks(tasks, [])
        assert result[0]["key"] == "critical"
        assert result[1]["key"] == "high"
        assert result[2]["key"] == "medium"
        assert result[3]["key"] == "low"

    def test_non_pending_tasks_excluded(self, engine):
        """Tasks that are not 'pending' are excluded from the ready list."""
        tasks = [
            _make_task("t1", status="completed"),
            _make_task("t2", status="in_progress"),
            _make_task("t3", status="pending"),
        ]
        result = engine.get_ready_tasks(tasks, [])
        assert len(result) == 1
        assert result[0]["key"] == "t3"

    def test_urgency_sorting_within_same_priority(self, engine):
        """Within the same priority, earlier due dates come first."""
        now = datetime.now()
        tasks = [
            _make_task("later", priority="medium", due_date=now + timedelta(days=10)),
            _make_task("sooner", priority="medium", due_date=now + timedelta(days=1)),
            _make_task("overdue", priority="medium", due_date=now - timedelta(days=2)),
        ]
        result = engine.get_ready_tasks(tasks, [])
        assert result[0]["key"] == "overdue"
        assert result[1]["key"] == "sooner"
        assert result[2]["key"] == "later"

    def test_no_internal_keys_in_output(self, engine):
        """Internal sorting keys are stripped from the output."""
        tasks = [_make_task("t1")]
        result = engine.get_ready_tasks(tasks, [])
        assert "_sort_priority" not in result[0]
        assert "_sort_urgency" not in result[0]

    def test_due_date_as_iso_string(self, engine):
        """Due dates can be provided as ISO format strings."""
        due = (datetime.now() + timedelta(days=5)).isoformat()
        tasks = [
            {"key": "t1", "status": "pending", "priority": "medium", "due_date": due},
        ]
        result = engine.get_ready_tasks(tasks, [])
        assert len(result) == 1

    def test_chain_dependency(self, engine):
        """In a chain t1 -> t2 -> t3, only t1 is ready when all are pending."""
        tasks = [
            _make_task("t1"),
            _make_task("t2"),
            _make_task("t3"),
        ]
        deps = [_make_dep("t1", "t2"), _make_dep("t2", "t3")]
        result = engine.get_ready_tasks(tasks, deps)
        assert len(result) == 1
        assert result[0]["key"] == "t1"


class TestRescheduleDependents:
    """Tests for the reschedule_dependents method."""

    def test_on_time_completion_no_reschedule(self, engine):
        """If a task completes on time, no rescheduling occurs."""
        due = datetime(2026, 3, 10, 12, 0, 0)
        completed_at = datetime(2026, 3, 10, 10, 0, 0)
        tasks = [
            _make_task("t1", status="completed"),
            _make_task("t2", due_date=datetime(2026, 3, 12, 12, 0, 0)),
        ]
        deps = [_make_dep("t1", "t2")]
        result = engine.reschedule_dependents("t1", completed_at, due, tasks, deps)
        assert result == []

    def test_late_completion_propagates_delay(self, engine):
        """A task that completes 3 days late shifts its dependent by 3 days."""
        original_due = datetime(2026, 3, 10, 12, 0, 0)
        completed_at = datetime(2026, 3, 13, 12, 0, 0)
        dep_due = datetime(2026, 3, 15, 12, 0, 0)

        tasks = [
            _make_task("t1", status="completed"),
            _make_task("t2", due_date=dep_due),
        ]
        deps = [_make_dep("t1", "t2")]
        result = engine.reschedule_dependents("t1", completed_at, original_due, tasks, deps)
        assert len(result) == 1
        assert result[0]["task_key"] == "t2"
        new_due = datetime.fromisoformat(result[0]["new_due_date"])
        assert new_due == datetime(2026, 3, 18, 12, 0, 0)

    def test_no_dependents_empty_result(self, engine):
        """A task with no dependents produces no rescheduling."""
        tasks = [_make_task("t1", status="completed")]
        result = engine.reschedule_dependents(
            "t1",
            datetime(2026, 3, 15, 12, 0, 0),
            datetime(2026, 3, 10, 12, 0, 0),
            tasks,
            [],
        )
        assert result == []

    def test_cascading_reschedule(self, engine):
        """Delay propagates through a chain: t1 -> t2 -> t3."""
        original_due = datetime(2026, 3, 10, 12, 0, 0)
        completed_at = datetime(2026, 3, 12, 12, 0, 0)

        tasks = [
            _make_task("t1", status="completed"),
            _make_task("t2", due_date=datetime(2026, 3, 14, 12, 0, 0)),
            _make_task("t3", due_date=datetime(2026, 3, 18, 12, 0, 0)),
        ]
        deps = [_make_dep("t1", "t2"), _make_dep("t2", "t3")]
        result = engine.reschedule_dependents("t1", completed_at, original_due, tasks, deps)
        assert len(result) == 2
        keys = {r["task_key"] for r in result}
        assert keys == {"t2", "t3"}
        # Both should be shifted by 2 days
        for r in result:
            if r["task_key"] == "t2":
                new_due = datetime.fromisoformat(r["new_due_date"])
                assert new_due == datetime(2026, 3, 16, 12, 0, 0)
            elif r["task_key"] == "t3":
                new_due = datetime.fromisoformat(r["new_due_date"])
                assert new_due == datetime(2026, 3, 20, 12, 0, 0)

    def test_completed_dependents_not_rescheduled(self, engine):
        """Already completed dependents are not rescheduled."""
        original_due = datetime(2026, 3, 10, 12, 0, 0)
        completed_at = datetime(2026, 3, 13, 12, 0, 0)
        tasks = [
            _make_task("t1", status="completed"),
            _make_task("t2", status="completed", due_date=datetime(2026, 3, 15, 12, 0, 0)),
        ]
        deps = [_make_dep("t1", "t2")]
        result = engine.reschedule_dependents("t1", completed_at, original_due, tasks, deps)
        assert result == []

    def test_no_original_due_no_reschedule(self, engine):
        """If the completed task had no original due date, nothing is rescheduled."""
        tasks = [
            _make_task("t1", status="completed"),
            _make_task("t2", due_date=datetime(2026, 3, 15, 12, 0, 0)),
        ]
        deps = [_make_dep("t1", "t2")]
        result = engine.reschedule_dependents("t1", datetime(2026, 3, 13, 12, 0, 0), None, tasks, deps)
        assert result == []

    def test_dependent_without_due_date_skipped(self, engine):
        """Dependents without a due_date are not included in reschedule results."""
        original_due = datetime(2026, 3, 10, 12, 0, 0)
        completed_at = datetime(2026, 3, 13, 12, 0, 0)
        tasks = [
            _make_task("t1", status="completed"),
            _make_task("t2"),  # No due_date
        ]
        deps = [_make_dep("t1", "t2")]
        result = engine.reschedule_dependents("t1", completed_at, original_due, tasks, deps)
        assert result == []
