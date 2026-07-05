"""REQ-009 DashboardService unit tests."""

from datetime import UTC, date, datetime
from unittest.mock import MagicMock

import pytest

from app.domain.services.dashboard_service import (
    DashboardCounts,
    DashboardService,
    DashboardSummary,
)


def _frozen_clock(at: datetime):
    return lambda: at


def _service(**overrides) -> DashboardService:
    deps = {
        "plant_repo": MagicMock(),
        "task_repo": MagicMock(),
        "tank_repo": MagicMock(),
        "care_repo": MagicMock(),
        "activity_repo": MagicMock(),
        "clock": _frozen_clock(datetime(2026, 4, 29, 9, 0, tzinfo=UTC)),
    }
    deps.update(overrides)
    return DashboardService(**deps)


class TestDashboardSummary:
    def test_returns_summary_shape_with_zero_counts_when_repos_empty(self):
        plant_repo = MagicMock()
        plant_repo.count_for_tenant.return_value = 0
        plant_repo.count_active_for_tenant.return_value = 0
        task_repo = MagicMock()
        task_repo.count_open_due_on.return_value = 0
        task_repo.count_overdue.return_value = 0
        task_repo.list_upcoming.return_value = []
        tank_repo = MagicMock()
        tank_repo.count_below_threshold.return_value = 0
        care_repo = MagicMock()
        care_repo.count_due_on.return_value = 0
        activity_repo = MagicMock()
        activity_repo.list_recent.return_value = []

        svc = _service(
            plant_repo=plant_repo,
            task_repo=task_repo,
            tank_repo=tank_repo,
            care_repo=care_repo,
            activity_repo=activity_repo,
        )

        result = svc.get_summary("t-1")

        assert isinstance(result, DashboardSummary)
        assert result.tenant_key == "t-1"
        assert result.counts == DashboardCounts(
            plants_total=0,
            plants_active=0,
            open_tasks_today=0,
            overdue_tasks=0,
            tanks_low=0,
            care_reminders_due=0,
        )
        assert result.upcoming_tasks == []
        assert result.recent_activities == []

    def test_aggregates_repo_values_into_counts(self):
        plant_repo = MagicMock()
        plant_repo.count_for_tenant.return_value = 42
        plant_repo.count_active_for_tenant.return_value = 30
        task_repo = MagicMock()
        task_repo.count_open_due_on.return_value = 5
        task_repo.count_overdue.return_value = 2
        task_repo.list_upcoming.return_value = [{"key": "task-1"}]
        tank_repo = MagicMock()
        tank_repo.count_below_threshold.return_value = 1
        care_repo = MagicMock()
        care_repo.count_due_on.return_value = 7
        activity_repo = MagicMock()
        activity_repo.list_recent.return_value = [{"key": "act-1"}]

        svc = _service(
            plant_repo=plant_repo,
            task_repo=task_repo,
            tank_repo=tank_repo,
            care_repo=care_repo,
            activity_repo=activity_repo,
        )

        result = svc.get_summary("t-1")

        assert result.counts.plants_total == 42
        assert result.counts.plants_active == 30
        assert result.counts.open_tasks_today == 5
        assert result.counts.overdue_tasks == 2
        assert result.counts.tanks_low == 1
        assert result.counts.care_reminders_due == 7
        assert result.upcoming_tasks == [{"key": "task-1"}]
        assert result.recent_activities == [{"key": "act-1"}]

    def test_optional_repos_none_degrade_to_empty(self):
        # Absent OPTIONAL repos (tank/care/activity) are a legit configuration,
        # not an error: their tiles degrade to 0/[] via a plain presence check.
        plant_repo = MagicMock()
        plant_repo.count_for_tenant.return_value = 4
        plant_repo.count_active_for_tenant.return_value = 4
        task_repo = MagicMock()
        task_repo.count_open_due_on.return_value = 1
        task_repo.count_overdue.return_value = 0
        task_repo.list_upcoming.return_value = []

        svc = _service(
            plant_repo=plant_repo,
            task_repo=task_repo,
            tank_repo=None,
            care_repo=None,
            activity_repo=None,
        )

        result = svc.get_summary("t-1")

        assert result.counts.plants_total == 4
        assert result.counts.tanks_low == 0
        assert result.counts.care_reminders_due == 0
        assert result.recent_activities == []

    def test_missing_required_method_raises_loudly(self):
        # REQ-009 R7/R8 regression: a missing REQUIRED repository method is a
        # programming/wiring error and MUST surface loudly, never collapse to a
        # legit-looking 0 (the exact masking that caused the hard-zero dashboard).
        plant_repo = MagicMock(spec=[])  # lacks count_for_tenant
        task_repo = MagicMock()
        task_repo.count_open_due_on.return_value = 0
        task_repo.count_overdue.return_value = 0
        task_repo.list_upcoming.return_value = []

        svc = _service(plant_repo=plant_repo, task_repo=task_repo, tank_repo=None, care_repo=None, activity_repo=None)

        with pytest.raises(AttributeError):
            svc.get_summary("t-1")

    def test_active_plants_present_yield_nonzero_count(self):
        # REQ-009 R8(a): with active plants present the tile reports a real count,
        # not a hard 0.
        plant_repo = MagicMock()
        plant_repo.count_for_tenant.return_value = 12
        plant_repo.count_active_for_tenant.return_value = 9
        task_repo = MagicMock()
        task_repo.count_open_due_on.return_value = 0
        task_repo.count_overdue.return_value = 0
        task_repo.list_upcoming.return_value = []

        svc = _service(plant_repo=plant_repo, task_repo=task_repo, tank_repo=None, care_repo=None, activity_repo=None)

        result = svc.get_summary("t-1")

        assert result.counts.plants_total == 12
        assert result.counts.plants_active == 9
        assert result.counts.plants_active > 0

    def test_swallows_repo_exceptions_per_section(self):
        plant_repo = MagicMock()
        plant_repo.count_for_tenant.side_effect = RuntimeError("db down")
        plant_repo.count_active_for_tenant.return_value = 0
        task_repo = MagicMock()
        task_repo.count_open_due_on.return_value = 3
        task_repo.count_overdue.return_value = 0
        task_repo.list_upcoming.return_value = []

        svc = _service(plant_repo=plant_repo, task_repo=task_repo, tank_repo=None, care_repo=None)

        result = svc.get_summary("t-1")
        assert result.counts.plants_total == 0  # exception swallowed
        assert result.counts.open_tasks_today == 3  # other section still works

    def test_passes_today_to_task_repo(self):
        task_repo = MagicMock()
        task_repo.count_open_due_on.return_value = 0
        task_repo.count_overdue.return_value = 0
        task_repo.list_upcoming.return_value = []

        svc = _service(task_repo=task_repo)
        svc.get_summary("t-1")

        assert task_repo.count_open_due_on.call_args.args[1] == date(2026, 4, 29)
