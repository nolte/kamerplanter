"""Behavioural regression for the #508 care/task double-count fix (REQ-009).

Issue #508: care reminders are persisted as ``Task`` rows with
``category == "care_reminder"`` and are already surfaced by the dedicated
``care_reminders_due`` tile (``ArangoCareReminderRepository.count_due_on``). The
generic task counters (``count_open_due_on`` / ``count_overdue``) used to apply
no category filter, so a care reminder due today/overdue was counted in two
tiles at once. This test proves — behaviourally, over a shared in-memory task
set — that:

* generic open/overdue counts and the upcoming list EXCLUDE care reminders,
* the ``care_reminders_due`` count still counts exactly those care reminders,
* the two surfaces are disjoint (no task is double-counted),
* the exclusion is applied per tenant.

Rather than a live ArangoDB, a tiny in-memory AQL interpreter replays the three
generic queries and the care query against the same documents, applying the same
FILTER predicates (tenant, category, open-status, due-date banding, orphan
guard). It is intentionally scoped to the exact query shapes these two
repositories emit — its job is to prove the *filter semantics*, not to be a
general AQL engine.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from app.data_access.arango.care_reminder_repository import ArangoCareReminderRepository
from app.data_access.arango.task_repository import ArangoTaskRepository

TODAY = date(2026, 4, 29)


class _InMemoryAql:
    """Replays the dashboard count/list queries against in-memory task docs."""

    def __init__(self, docs: list[dict[str, Any]]) -> None:
        self._docs = docs

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        bv = bind_vars or {}
        rows = [d for d in self._docs if d.get("tenant_key") == bv["tenant_key"]]

        if "doc.category != @care_category" in query:
            rows = [d for d in rows if d.get("category") != bv["care_category"]]
        if "doc.category == @care_category" in query:
            rows = [d for d in rows if d.get("category") == bv["care_category"]]

        rows = [d for d in rows if d.get("status") in bv["open_statuses"]]
        rows = [d for d in rows if d.get("due_date")]

        today = bv.get("today")
        if "@window_end" in query:
            window_end = bv["window_end"]
            rows = [d for d in rows if today <= d["due_date"][:10] <= window_end]
        elif "LEFT(doc.due_date, 10) == @today" in query:
            rows = [d for d in rows if d["due_date"][:10] == today]
        elif "LEFT(doc.due_date, 10) < @today" in query:
            rows = [d for d in rows if d["due_date"][:10] < today]
        elif "LEFT(doc.due_date, 10) <= @today" in query:
            rows = [d for d in rows if d["due_date"][:10] <= today]

        # Orphan guard: non-plant tasks always pass; the fixtures carry no
        # plant_instance entity, so nothing is dropped here.
        rows = [d for d in rows if d.get("entity_type") != "plant_instance"]

        if query.lstrip().startswith("RETURN LENGTH"):
            return iter([len(rows)])

        rows = sorted(rows, key=lambda d: d["due_date"])
        limit = bv.get("limit")
        if limit is not None:
            rows = rows[:limit]
        return iter(rows)


class _InMemoryDb:
    def __init__(self, docs: list[dict[str, Any]]) -> None:
        self.aql = _InMemoryAql(docs)


def _task(
    key: str,
    *,
    tenant_key: str,
    category: str,
    due: str,
    status: str = "pending",
) -> dict[str, Any]:
    return {
        "_key": key,
        "tenant_key": tenant_key,
        "category": category,
        "due_date": f"{due}T09:00:00+00:00",
        "status": status,
        "entity_type": "generic",
    }


def _fixtures() -> list[dict[str, Any]]:
    """A tenant with mixed generic + care tasks, plus a second tenant."""
    return [
        # tenant-A — due today
        _task("g-today", tenant_key="tenant-A", category="watering", due="2026-04-29"),
        _task("c-today", tenant_key="tenant-A", category="care_reminder", due="2026-04-29"),
        # tenant-A — overdue
        _task("g-over", tenant_key="tenant-A", category="feeding", due="2026-04-25"),
        _task("c-over", tenant_key="tenant-A", category="care_reminder", due="2026-04-20"),
        # tenant-A — upcoming (within the 7-day window, not today)
        _task("g-up", tenant_key="tenant-A", category="watering", due="2026-05-02"),
        _task("c-up", tenant_key="tenant-A", category="care_reminder", due="2026-05-03"),
        # tenant-A — a completed care task must never count anywhere
        _task("c-done", tenant_key="tenant-A", category="care_reminder", due="2026-04-29", status="completed"),
        # tenant-B — isolation guard: its care reminder must not leak into tenant-A
        _task("c-b", tenant_key="tenant-B", category="care_reminder", due="2026-04-29"),
        _task("g-b", tenant_key="tenant-B", category="watering", due="2026-04-29"),
    ]


def test_generic_counts_exclude_care_while_care_count_keeps_them() -> None:
    db = _InMemoryDb(_fixtures())
    task_repo = ArangoTaskRepository(db)  # type: ignore[arg-type]
    care_repo = ArangoCareReminderRepository(db)  # type: ignore[arg-type]

    open_today = task_repo.count_open_due_on("tenant-A", TODAY)
    overdue = task_repo.count_overdue("tenant-A", TODAY)
    care_due = care_repo.count_due_on("tenant-A", TODAY)

    # Generic tiles: only the non-care work (g-today / g-over).
    assert open_today == 1  # g-today only, NOT c-today
    assert overdue == 1  # g-over only, NOT c-over
    # Care tile: today + overdue care reminders (c-today, c-over), never the
    # completed one (c-done) and never tenant-B's leak (c-b).
    assert care_due == 2


def test_no_task_is_counted_in_both_generic_and_care() -> None:
    docs = _fixtures()
    db = _InMemoryDb(docs)
    task_repo = ArangoTaskRepository(db)  # type: ignore[arg-type]
    care_repo = ArangoCareReminderRepository(db)  # type: ignore[arg-type]

    # Reconstruct the *sets* each surface would count for tenant-A today.
    open_today_keys = {
        d["_key"]
        for d in docs
        if d["tenant_key"] == "tenant-A"
        and d["category"] != "care_reminder"
        and d["status"] in ("pending", "in_progress")
        and d["due_date"][:10] == TODAY.isoformat()
    }
    overdue_keys = {
        d["_key"]
        for d in docs
        if d["tenant_key"] == "tenant-A"
        and d["category"] != "care_reminder"
        and d["status"] in ("pending", "in_progress")
        and d["due_date"][:10] < TODAY.isoformat()
    }
    care_keys = {
        d["_key"]
        for d in docs
        if d["tenant_key"] == "tenant-A"
        and d["category"] == "care_reminder"
        and d["status"] in ("pending", "in_progress")
        and d["due_date"][:10] <= TODAY.isoformat()
    }

    # The generic slice and the care slice must be disjoint (no double-count).
    assert open_today_keys.isdisjoint(care_keys)
    assert overdue_keys.isdisjoint(care_keys)

    # And the repositories agree with those disjoint sets.
    assert task_repo.count_open_due_on("tenant-A", TODAY) == len(open_today_keys)
    assert task_repo.count_overdue("tenant-A", TODAY) == len(overdue_keys)
    assert care_repo.count_due_on("tenant-A", TODAY) == len(care_keys)


def test_upcoming_list_excludes_care_reminders() -> None:
    db = _InMemoryDb(_fixtures())
    task_repo = ArangoTaskRepository(db)  # type: ignore[arg-type]

    upcoming = task_repo.list_upcoming("tenant-A", TODAY, date(2026, 5, 6), 10)
    keys = {row["_key"] for row in upcoming}

    # Generic tasks in the window (today g-today + future g-up), no care tasks.
    assert "g-today" in keys
    assert "g-up" in keys
    assert not any(k.startswith("c-") for k in keys)


def test_exclusion_is_per_tenant() -> None:
    db = _InMemoryDb(_fixtures())
    task_repo = ArangoTaskRepository(db)  # type: ignore[arg-type]
    care_repo = ArangoCareReminderRepository(db)  # type: ignore[arg-type]

    # tenant-B sees only its own docs: one generic due today, one care due today.
    assert task_repo.count_open_due_on("tenant-B", TODAY) == 1  # g-b
    assert care_repo.count_due_on("tenant-B", TODAY) == 1  # c-b
    # tenant-A's care reminders never bleed into tenant-B and vice versa.
    assert task_repo.count_overdue("tenant-B", TODAY) == 0
