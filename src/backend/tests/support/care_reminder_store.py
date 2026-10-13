"""In-memory care-reminder read side of ``ITaskRepository`` for the notification beats (MT-032, #2128).

The notification beats used to read the whole ``tasks`` collection of every tenant and
filter in Python. They now ask :meth:`ITaskRepository.list_open_care_reminders_due` once
per active tenant. ``CareReminderStore`` answers that question over a list of rows with
the semantics of the AQL in ``ArangoTaskRepository`` — tenant, ``care_reminder``
category, open status, inclusive due window, a due date without an offset read as UTC —
which ``tests/integration/test_care_reminders_due_query.py`` measures against the real
server. Its ``get_all`` refuses: a beat that falls back to loading the collection fails
the test instead of passing on a double that would have answered it.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from app.common.enums import TaskCategory, TaskStatus

_OPEN = {TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value}


def _field(row: Any, name: str) -> Any:
    if isinstance(row, dict):
        return row.get(name)
    return getattr(row, name, None)


def _due(row: Any) -> datetime | None:
    raw = _field(row, "due_date")
    if isinstance(raw, str):
        try:
            raw = datetime.fromisoformat(raw)
        except ValueError:
            return None
    if not isinstance(raw, datetime):
        return None
    return raw if raw.tzinfo is not None else raw.replace(tzinfo=UTC)


class CareReminderStore:
    """``list_open_care_reminders_due`` over in-memory rows (dicts or ``Task`` models)."""

    def __init__(self, rows: Iterable[Any] = ()) -> None:
        self.rows = list(rows)
        self.asked: list[tuple[str, datetime | None, datetime]] = []

    def get_all(self, *_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("a notification beat must not load the tasks collection (MT-032, #2128)")

    def list_open_care_reminders_due(
        self, *, tenant_key: str, due_until: datetime, due_from: datetime | None = None
    ) -> list[Any]:
        if not tenant_key:
            raise ValueError("list_open_care_reminders_due is tenant-scoped")
        self.asked.append((tenant_key, due_from, due_until))
        selected = []
        for row in self.rows:
            due = _due(row)
            if (
                _field(row, "tenant_key") == tenant_key
                and _field(row, "category") == TaskCategory.CARE_REMINDER.value
                and _field(row, "status") in _OPEN
                and due is not None
                and due <= due_until
                and (due_from is None or due >= due_from)
            ):
                selected.append(row)
        return selected

    def tenant_rows(self) -> list[dict[str, str]]:
        """One active tenant document per distinct non-empty ``tenant_key`` of the rows, in key order."""
        keys = sorted({_field(row, "tenant_key") for row in self.rows} - {None, ""})
        return [{"_key": key, "status": "active"} for key in keys]
