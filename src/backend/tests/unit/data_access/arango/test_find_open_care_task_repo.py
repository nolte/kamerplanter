"""Repository-level contract for the single care-task dedup helper (#509).

``ArangoTaskRepository.find_open_care_task`` is THE tenant-aware idempotency
predicate for care reminders. These tests pin the query contract without a live
ArangoDB — following the capturing-fake-db style of ``test_dashboard_counts_repo``:

* the lookup is **tenant-scoped** — the AQL filters ``doc.tenant_key ==
  @tenant_key`` and the caller's tenant is passed as a bind var (never inlined),
  so a care task in another tenant can never be returned (the closed gap);
* it matches the reminder type by the ``"— {value}"`` name suffix and guards
  against ``null`` names;
* the recency rule ("completed today counts as satisfied") is expressed in the
  query and gated by the ``include_completed_today`` bind var; and
* the result document is wrapped into a ``Task`` (or ``None`` when empty).
"""

from __future__ import annotations

from typing import Any

from app.common.enums import ReminderType, TaskCategory, TaskStatus
from app.data_access.arango.task_repository import ArangoTaskRepository


class _CapturingAql:
    def __init__(self, result: list[Any]) -> None:
        self.query: str | None = None
        self.bind_vars: dict[str, Any] | None = None
        self._result = result

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        self.query = query
        self.bind_vars = bind_vars or {}
        return iter(self._result)


class _CapturingDb:
    def __init__(self, result: list[Any]) -> None:
        self.aql = _CapturingAql(result)


def _repo(result: list[Any]) -> ArangoTaskRepository:
    return ArangoTaskRepository(_CapturingDb(result))  # type: ignore[arg-type]


def test_lookup_is_tenant_scoped() -> None:
    repo = _repo([])
    repo.find_open_care_task("plant-1", ReminderType.WATERING, "tenant-A")

    aql = repo._db.aql  # type: ignore[attr-defined]
    # The tenant is filtered in the DB and passed through as a bind var — never
    # inlined into the query string (cross-tenant leak guard).
    assert "doc.tenant_key == @tenant_key" in aql.query
    assert aql.bind_vars["tenant_key"] == "tenant-A"
    assert "tenant-A" not in aql.query
    # Collection is bound via @@col, not string-interpolated (injection guard).
    assert "@@col" in aql.query
    assert aql.bind_vars["@col"] == repo._collection_name


def test_lookup_binds_entity_and_reminder_type_suffix() -> None:
    repo = _repo([])
    repo.find_open_care_task("plant-1", ReminderType.FERTILIZING, "tenant-A")

    aql = repo._db.aql  # type: ignore[attr-defined]
    assert aql.bind_vars["entity_key"] == "plant-1"
    assert aql.bind_vars["care_category"] == TaskCategory.CARE_REMINDER.value
    # Reminder type is matched via the name suffix (audit P5 — not a first-class field).
    assert aql.bind_vars["name_suffix"] == f"— {ReminderType.FERTILIZING.value}"
    assert "RIGHT(doc.name, LENGTH(@name_suffix)) == @name_suffix" in aql.query
    # Null-name guard so a task without a name never raises / matches.
    assert "doc.name != null" in aql.query


def test_recency_rule_gated_by_include_completed_today() -> None:
    repo = _repo([])
    repo.find_open_care_task("plant-1", ReminderType.WATERING, "tenant-A")

    aql = repo._db.aql  # type: ignore[attr-defined]
    assert aql.bind_vars["include_completed_today"] is True
    assert aql.bind_vars["open_statuses"] == [
        TaskStatus.PENDING.value,
        TaskStatus.IN_PROGRESS.value,
    ]
    assert aql.bind_vars["completed_status"] == TaskStatus.COMPLETED.value
    # The "completed today counts as satisfied" recency rule is in the query and
    # gated by the include-flag bind var.
    assert "@include_completed_today" in aql.query
    assert "LEFT(doc.completed_at, 10) >= @today" in aql.query
    # Newest-first so ties keep the latest task.
    assert "SORT doc.due_date DESC, doc.created_at DESC" in aql.query
    assert "LIMIT 1" in aql.query


def test_complete_flag_false_is_forwarded() -> None:
    repo = _repo([])
    repo.find_open_care_task(
        "plant-1",
        ReminderType.WATERING,
        "tenant-A",
        include_completed_today=False,
    )

    aql = repo._db.aql  # type: ignore[attr-defined]
    assert aql.bind_vars["include_completed_today"] is False


def test_returns_wrapped_task_when_document_found() -> None:
    doc = {
        "_key": "task-1",
        "name": "Monstera — watering",
        "instruction": "Water Monstera.",
        "category": TaskCategory.CARE_REMINDER.value,
        "entity_key": "plant-1",
        "entity_type": "plant_instance",
        "tenant_key": "tenant-A",
        "status": TaskStatus.PENDING.value,
    }
    repo = _repo([doc])

    task = repo.find_open_care_task("plant-1", ReminderType.WATERING, "tenant-A")

    assert task is not None
    assert task.key == "task-1"
    assert task.tenant_key == "tenant-A"
    assert task.name == "Monstera — watering"


def test_returns_none_when_no_document() -> None:
    repo = _repo([])

    assert repo.find_open_care_task("plant-1", ReminderType.WATERING, "tenant-A") is None
