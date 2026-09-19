"""#1533 — the two tank beat tasks decide idempotency inside one tenant, in the query.

Both bodies used to ask::

    existing, _ = task_repo.get_all_tasks(0, 200, {"category": MAINTENANCE})
    already_exists = any(t.name == task_name and t.status in OPEN for t in existing)

``ArangoTaskRepository.get_all_tasks`` adds its tenant predicate only when it is
given one (``if tenant_key:``), and neither call site gave it one. Two defects
followed, and this module measures both against a repository double that mirrors
the *old* signature and semantics — so the red run proves the behaviour, not a
``TypeError`` from a changed signature:

1. **Cross-tenant read.** The page was drawn from every tenant's maintenance
   tasks, so a foreign tenant's row could answer one tenant's idempotency
   question.
2. **Cap-then-filter (#1503, one layer down).** The narrowing by ``name`` and
   ``status`` happened in Python over a **200-row cap**. Past 200 maintenance
   tasks the matching one sorts past the cut, ``already_exists`` is ``False`` and
   every beat run creates another duplicate.

The repair moves the whole predicate — tenant, name, open status — into
``find_open_task_by_name``, which has no cap to fall off.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.common.enums import TaskCategory, TaskStatus
from app.domain.models.task import Task

#: The open statuses the production predicate treats as "already there".
_OPEN = (TaskStatus.PENDING, TaskStatus.IN_PROGRESS)


class _TaskRepoDouble:
    """In-memory stand-in mirroring the two lookups this class is about.

    ``get_all_tasks`` reproduces the **old** contract deliberately: tenant filter
    only when a non-empty ``tenant_key`` arrives, equality on every ``filters``
    entry, ``due_date`` ascending, then ``offset``/``limit``. That is what makes
    the pre-repair run red for the reason the issue names instead of for a
    signature mismatch.

    ``find_open_task_by_name`` mirrors the AQL of the real method — tenant, exact
    name, open status, no cap. Its fidelity is not taken on trust: the same
    predicate is measured against a real ArangoDB in
    ``tests/integration/test_open_task_by_name_lookup.py``.
    """

    def __init__(self, tasks: list[Task]) -> None:
        self.tasks = list(tasks)
        self.created: list[Task] = []

    def get_all_tasks(
        self,
        offset: int = 0,
        limit: int = 50,
        filters: dict | None = None,
        tenant_key: str | None = None,
        *,
        origins=None,
    ) -> tuple[list[Task], int]:
        rows = self.tasks
        if tenant_key:
            rows = [t for t in rows if t.tenant_key == tenant_key]
        for field, value in (filters or {}).items():
            rows = [t for t in rows if getattr(t, field, None) == value]
        rows = sorted(rows, key=lambda t: t.due_date or datetime.min.replace(tzinfo=UTC))
        return rows[offset : offset + limit], len(rows)

    def find_open_task_by_name(self, name: str, *, tenant_key: str) -> Task | None:
        for task in self.tasks:
            if task.tenant_key == tenant_key and task.name == name and task.status in _OPEN:
                return task
        return None

    def create_task(self, task: Task) -> Task:
        self.created.append(task)
        self.tasks.append(task)
        return task


def _task(name: str, tenant: str, *, due_days: int = 0, status: TaskStatus = TaskStatus.PENDING) -> Task:
    return Task(
        name=name,
        instruction="seeded",
        category=TaskCategory.MAINTENANCE,
        tenant_key=tenant,
        due_date=datetime.now(UTC) + timedelta(days=due_days),
        status=status,
    )


@pytest.fixture(autouse=True)
def _mock_dependencies(monkeypatch):
    mock_deps = ModuleType("app.common.dependencies")
    for getter in (
        "get_tank_repo",
        "get_task_repo",
        "get_ha_client",
        "get_sensor_repo",
        "get_feeding_repo",
        "get_plant_repo",
        "get_db",
    ):
        setattr(mock_deps, getter, MagicMock())
    monkeypatch.setitem(sys.modules, "app.common.dependencies", mock_deps)
    yield mock_deps


def _tank_repo(tenant: str) -> MagicMock:
    repo = MagicMock()
    repo.get_active_auto_create_schedules.return_value = [
        SimpleNamespace(
            tank_key="tank_1",
            maintenance_type="water_change",
            interval_days=7,
            reminder_days_before=0,
            instructions=None,
            priority=SimpleNamespace(value="medium"),
        )
    ]
    repo.get_last_maintenance_by_type.return_value = None
    repo.get_by_key.return_value = SimpleNamespace(name="Res 1", tenant_key=tenant)
    return repo


class TestMaintenanceScheduleIdempotency:
    def test_a_foreign_tenants_task_does_not_suppress_creation(self, _mock_dependencies):
        """The idempotency question belongs to one tenant."""
        _mock_dependencies.get_tank_repo.return_value = _tank_repo("tenant_1")
        task_repo = _TaskRepoDouble([_task("maintenance:water_change:tank_1", "tenant_2")])
        _mock_dependencies.get_task_repo.return_value = task_repo

        from app.tasks.tank_maintenance_tasks import generate_tank_maintenance_tasks

        assert generate_tank_maintenance_tasks() == {"created": 1, "skipped": 0}
        assert [t.tenant_key for t in task_repo.created] == ["tenant_1"]

    def test_the_tenants_own_open_task_still_suppresses_creation(self, _mock_dependencies):
        _mock_dependencies.get_tank_repo.return_value = _tank_repo("tenant_1")
        task_repo = _TaskRepoDouble([_task("maintenance:water_change:tank_1", "tenant_1")])
        _mock_dependencies.get_task_repo.return_value = task_repo

        from app.tasks.tank_maintenance_tasks import generate_tank_maintenance_tasks

        assert generate_tank_maintenance_tasks() == {"created": 0, "skipped": 1}
        assert task_repo.created == []

    def test_a_match_past_the_old_200_row_cap_still_suppresses_creation(self, _mock_dependencies):
        """The #1503 class: the answer must not depend on a page size."""
        _mock_dependencies.get_tank_repo.return_value = _tank_repo("tenant_1")
        filler = [_task(f"maintenance:other:{i}", "tenant_1", due_days=i) for i in range(250)]
        # Sorts last by due_date, i.e. beyond any 200-row page.
        match = _task("maintenance:water_change:tank_1", "tenant_1", due_days=999)
        task_repo = _TaskRepoDouble([*filler, match])
        _mock_dependencies.get_task_repo.return_value = task_repo

        from app.tasks.tank_maintenance_tasks import generate_tank_maintenance_tasks

        assert generate_tank_maintenance_tasks() == {"created": 0, "skipped": 1}
        assert task_repo.created == []

    def test_a_tenantless_tank_is_skipped_instead_of_read_unscoped(self, _mock_dependencies):
        """Fail closed, exactly as the runoff sweep does for a tenantless plant."""
        tank_repo = _tank_repo("")
        _mock_dependencies.get_tank_repo.return_value = tank_repo
        task_repo = _TaskRepoDouble([])
        _mock_dependencies.get_task_repo.return_value = task_repo

        from app.tasks.tank_maintenance_tasks import generate_tank_maintenance_tasks

        assert generate_tank_maintenance_tasks() == {"created": 0, "skipped": 1}
        assert task_repo.created == []


class TestRunoffFlushIdempotency:
    @staticmethod
    def _feeding_repo() -> MagicMock:
        repo = MagicMock()
        repo.get_recent_runoff_events.return_value = [
            SimpleNamespace(runoff_ec=2.0, measured_ec_before=1.0) for _ in range(5)
        ]
        return repo

    @staticmethod
    def _db(tenant: str) -> MagicMock:
        db = MagicMock()
        db.aql.execute.return_value = iter([{"key": "plant_1", "tenant_key": tenant}])
        return db

    def test_a_foreign_tenants_flush_task_does_not_suppress_creation(self, _mock_dependencies):
        _mock_dependencies.get_db.return_value = self._db("tenant_1")
        _mock_dependencies.get_feeding_repo.return_value = self._feeding_repo()
        task_repo = _TaskRepoDouble([_task("flush:runoff_trend:plant_1", "tenant_2")])
        _mock_dependencies.get_task_repo.return_value = task_repo

        from app.tasks.tank_maintenance_tasks import check_runoff_trends

        assert check_runoff_trends() == {"plants_checked": 1, "created": 1, "skipped": 0}
        assert [t.tenant_key for t in task_repo.created] == ["tenant_1"]

    def test_a_match_past_the_old_200_row_cap_still_suppresses_creation(self, _mock_dependencies):
        _mock_dependencies.get_db.return_value = self._db("tenant_1")
        _mock_dependencies.get_feeding_repo.return_value = self._feeding_repo()
        filler = [_task(f"maintenance:other:{i}", "tenant_1", due_days=i) for i in range(250)]
        match = _task("flush:runoff_trend:plant_1", "tenant_1", due_days=999)
        task_repo = _TaskRepoDouble([*filler, match])
        _mock_dependencies.get_task_repo.return_value = task_repo

        from app.tasks.tank_maintenance_tasks import check_runoff_trends

        assert check_runoff_trends() == {"plants_checked": 1, "created": 0, "skipped": 1}
        assert task_repo.created == []
