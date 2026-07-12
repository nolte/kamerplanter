"""Repository-level contract for the REQ-009 dashboard counts/lists.

Every dashboard count/list is strictly tenant-scoped (SEC-001 / SEC-B4). These
unit tests pin, per method, that the AQL:

* binds the collection via ``@@…`` (never interpolates it — injection guard),
* filters every row on ``… .tenant_key == @tenant_key``,
* passes the caller's ``tenant_key`` through as a bind var and never inlines a
  foreign tenant value into the query string (cross-tenant leak guard), and
* rejects the empty-tenant sentinel with a ``ValueError`` **before** issuing any
  query (so a foreign-/absent-tenant read can never run).

They follow the capturing-fake-db style of
``test_plant_instance_survival_stats_repo.py`` — a live ArangoDB is not required
to prove the scoping contract.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import pytest

from app.data_access.arango.care_reminder_repository import ArangoCareReminderRepository
from app.data_access.arango.plant_instance_repository import ArangoPlantInstanceRepository
from app.data_access.arango.tank_repository import ArangoTankRepository
from app.data_access.arango.task_repository import ArangoTaskRepository

TODAY = date(2026, 4, 29)


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

    def collection(self, _name: str):  # pragma: no cover - must not be reached
        raise AssertionError("dashboard counts must run through AQL, not raw collections")


# ── PlantInstanceRepository ───────────────────────────────────────────


def test_count_for_tenant_is_tenant_scoped() -> None:
    db = _CapturingDb([7])
    repo = ArangoPlantInstanceRepository(db)  # type: ignore[arg-type]

    assert repo.count_for_tenant("tenant-A") == 7

    q = db.aql.query or ""
    assert "@@col" in q
    assert "p.tenant_key == @tenant_key" in q
    assert db.aql.bind_vars is not None
    assert db.aql.bind_vars["@col"] == "plant_instances"
    assert db.aql.bind_vars["tenant_key"] == "tenant-A"
    assert "tenant-A" not in q  # never interpolated


def test_count_active_for_tenant_filters_removed_on_null() -> None:
    db = _CapturingDb([3])
    repo = ArangoPlantInstanceRepository(db)  # type: ignore[arg-type]

    assert repo.count_active_for_tenant("tenant-A") == 3

    q = db.aql.query or ""
    assert "p.tenant_key == @tenant_key" in q
    # Alive marker is codebase-consistent: removed_on == null.
    assert "p.removed_on == null" in q
    assert db.aql.bind_vars["tenant_key"] == "tenant-A"


def test_list_active_for_tenant_is_scoped_sorted_and_capped() -> None:
    rows = [
        {
            "_key": "p-1",
            "plant_name": "Basil",
            "species_key": "ocimum-basilicum",
            "cultivar_key": None,
            "cultivar_name": None,
            "phase_key": "veg",
            "phase_name": "Vegetative",
            "location_key": "loc-1",
            "location_name": "Balcony",
            "has_open_task": True,
            "next_due_date": "2026-05-01T00:00:00+00:00",
        }
    ]
    db = _CapturingDb(rows)
    repo = ArangoPlantInstanceRepository(db)  # type: ignore[arg-type]

    result = repo.list_active_for_tenant("tenant-A", 8)

    assert result == rows
    q = db.aql.query or ""
    assert "@@col" in q
    assert "p.tenant_key == @tenant_key" in q
    assert "p.removed_on == null" in q  # only alive plants
    assert "SORT p.planted_on DESC" in q  # newest first
    assert "LIMIT @limit" in q
    # #488 — enriched per-card status fields are projected (no full document).
    assert "cultivar_name:" in q
    assert "phase_name:" in q
    assert "location_name:" in q
    assert "has_open_task:" in q
    assert "next_due_date:" in q
    # #548 — the open-task alarm is due-date-aware: only tasks due today-or-earlier
    # (or undated) count, so a merely future-scheduled task does not raise it.
    assert "due_now_task_count" in q
    assert "LEFT(d, 10) <= @today" in q
    # Open-task marker must be tenant-scoped too (no cross-tenant task leak, SEC-B4).
    assert "@@task_col" in q
    assert "tsk.tenant_key == @tenant_key" in q
    assert "tsk.entity_key == p._key" in q
    # location name is surfaced only for the caller's own-tenant location
    # (defence-in-depth: a foreign location_key never leaks another tenant's name).
    assert "location.tenant_key == @tenant_key" in q
    bv = db.aql.bind_vars or {}
    assert bv["@col"] == "plant_instances"
    assert bv["@task_col"] == "tasks"
    assert bv["tenant_key"] == "tenant-A"
    assert bv["limit"] == 8
    assert bv["cultivar_col"] == "cultivars"
    assert bv["phase_col"] == "growth_phases"
    assert bv["location_col"] == "locations"
    assert bv["plant_entity_type"] == "plant_instance"
    assert bv["open_statuses"] == ["pending", "in_progress"]
    assert bv["today"] == date.today().isoformat()  # #548 due-date-aware alarm
    assert "tenant-A" not in q  # never interpolated


def test_plant_counts_reject_empty_tenant_key() -> None:
    db = _CapturingDb([0])
    repo = ArangoPlantInstanceRepository(db)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="tenant"):
        repo.count_for_tenant("")
    with pytest.raises(ValueError, match="tenant"):
        repo.count_active_for_tenant("")
    with pytest.raises(ValueError, match="tenant"):
        repo.list_active_for_tenant("", 8)
    # Guard fires before any query runs.
    assert db.aql.query is None


# ── TaskRepository ────────────────────────────────────────────────────


def test_count_open_due_on_scoped_and_open_and_dated() -> None:
    db = _CapturingDb([5])
    repo = ArangoTaskRepository(db)  # type: ignore[arg-type]

    assert repo.count_open_due_on("tenant-A", TODAY) == 5

    q = db.aql.query or ""
    assert "@@col" in q
    assert "doc.tenant_key == @tenant_key" in q
    assert "doc.status IN @open_statuses" in q
    assert "LEFT(doc.due_date, 10) == @today" in q
    # #508: generic task counts exclude care reminders (they own the dedicated
    # care_reminders_due tile), so a care reminder is never double-counted.
    assert "doc.category != @care_category" in q
    # Orphaned plant tasks excluded (mirrors get_all_tasks user-facing queue).
    assert "_plant.removed_on == null" in q
    bv = db.aql.bind_vars or {}
    assert bv["@col"] == "tasks"
    assert bv["tenant_key"] == "tenant-A"
    assert bv["care_category"] == "care_reminder"
    assert bv["open_statuses"] == ["pending", "in_progress"]
    assert bv["today"] == "2026-04-29"
    assert bv["plant_col"] == "plant_instances"
    assert "tenant-A" not in q


def test_count_overdue_uses_strictly_before_today() -> None:
    db = _CapturingDb([2])
    repo = ArangoTaskRepository(db)  # type: ignore[arg-type]

    assert repo.count_overdue("tenant-A", TODAY) == 2

    q = db.aql.query or ""
    assert "LEFT(doc.due_date, 10) < @today" in q
    assert "doc.status IN @open_statuses" in q
    # #508: overdue generic count excludes care reminders too.
    assert "doc.category != @care_category" in q
    bv = db.aql.bind_vars or {}
    assert bv["today"] == "2026-04-29"
    assert bv["care_category"] == "care_reminder"


def test_list_upcoming_is_windowed_sorted_and_capped() -> None:
    db = _CapturingDb([{"_key": "t1", "name": "Water"}])
    repo = ArangoTaskRepository(db)  # type: ignore[arg-type]

    result = repo.list_upcoming("tenant-A", TODAY, date(2026, 5, 6), 5)

    assert result == [{"_key": "t1", "name": "Water"}]
    q = db.aql.query or ""
    assert "doc.tenant_key == @tenant_key" in q
    assert "LEFT(doc.due_date, 10) >= @today" in q
    assert "LEFT(doc.due_date, 10) <= @window_end" in q
    # #508: the generic upcoming-tasks list is disjoint from the care section.
    assert "doc.category != @care_category" in q
    assert "SORT doc.due_date ASC" in q
    assert "LIMIT @limit" in q
    bv = db.aql.bind_vars or {}
    assert bv["today"] == "2026-04-29"
    assert bv["window_end"] == "2026-05-06"
    assert bv["limit"] == 5
    assert bv["care_category"] == "care_reminder"


def test_task_dashboard_methods_reject_empty_tenant_key() -> None:
    db = _CapturingDb([0])
    repo = ArangoTaskRepository(db)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="tenant"):
        repo.count_open_due_on("", TODAY)
    with pytest.raises(ValueError, match="tenant"):
        repo.count_overdue("", TODAY)
    with pytest.raises(ValueError, match="tenant"):
        repo.list_upcoming("", TODAY, date(2026, 5, 6), 5)
    assert db.aql.query is None


# ── CareReminderRepository ────────────────────────────────────────────


def test_count_due_on_scopes_care_tasks_incl_overdue() -> None:
    db = _CapturingDb([4])
    repo = ArangoCareReminderRepository(db)  # type: ignore[arg-type]

    assert repo.count_due_on("tenant-A", TODAY) == 4

    q = db.aql.query or ""
    # Care reminders materialise as care_reminder tasks (tenant-scoped, due-dated).
    assert "@@tasks" in q
    assert "doc.tenant_key == @tenant_key" in q
    assert "doc.category == @care_category" in q
    assert "doc.status IN @open_statuses" in q
    # Today PLUS overdue — a single care count, so overdue is included (R3).
    assert "LEFT(doc.due_date, 10) <= @today" in q
    bv = db.aql.bind_vars or {}
    assert bv["@tasks"] == "tasks"
    assert bv["care_category"] == "care_reminder"
    assert bv["tenant_key"] == "tenant-A"
    assert bv["today"] == "2026-04-29"
    assert "tenant-A" not in q


def test_count_due_on_rejects_empty_tenant_key() -> None:
    db = _CapturingDb([0])
    repo = ArangoCareReminderRepository(db)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="tenant"):
        repo.count_due_on("", TODAY)
    assert db.aql.query is None


# ── TankRepository ────────────────────────────────────────────────────


def test_count_below_threshold_resolves_latest_state_per_tank() -> None:
    db = _CapturingDb([1])
    repo = ArangoTankRepository(db)  # type: ignore[arg-type]

    assert repo.count_below_threshold("tenant-A") == 1

    q = db.aql.query or ""
    assert "@@tanks" in q
    assert "@@states" in q
    assert "tank.tenant_key == @tenant_key" in q
    # Newest-per-tank resolution + per-tank threshold with the 20 % fallback.
    assert "SORT s.recorded_at DESC" in q
    assert "s.fill_level_percent != null" in q
    assert "latest_fill < threshold" in q
    bv = db.aql.bind_vars or {}
    assert bv["@tanks"] == "tanks"
    assert bv["@states"] == "tank_states"
    assert bv["tenant_key"] == "tenant-A"
    assert bv["default_threshold"] == 20.0
    assert "tenant-A" not in q


def test_count_below_threshold_rejects_empty_tenant_key() -> None:
    db = _CapturingDb([0])
    repo = ArangoTankRepository(db)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="tenant"):
        repo.count_below_threshold("")
    assert db.aql.query is None
