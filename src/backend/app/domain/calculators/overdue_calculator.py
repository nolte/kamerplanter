"""The one definition of "overdue" (REQ-053 GP-FR-192, operator decision #2435 item 6 / #2455 item 4, #2461).

A task is overdue when its **due day lies before today**, both read as UTC calendar days. A task due today is not
overdue, whatever the time of day (00:00 and 23:59 alike). Pure: ``now`` is an argument.

Every surface uses this rule: the plant state marker, the bed counters (``overdue_task_count``), the bed list
"next due" column, the care tab and field mode. The TypeScript twins (``model/overdue.ts`` and the callers) run
against the same vectors (operation ``overdue`` of ``garden-plan-vectors.json``).
"""

from __future__ import annotations

from datetime import UTC, date, datetime


def _parse(value: str | datetime | date | None) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=UTC)
    else:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def utc_day(value: str | datetime | date | None) -> date | None:
    """The UTC calendar day of an ISO value (a naive value is read as UTC); ``None`` when absent or unreadable."""
    parsed = _parse(value)
    return None if parsed is None else parsed.astimezone(UTC).date()


def start_of_utc_day(now: datetime) -> datetime:
    """Midnight (UTC) of the day ``now`` falls on: tasks due before it are overdue."""
    moment = _parse(now)
    if moment is None:  # pragma: no cover - ``now`` is a datetime by contract
        raise ValueError("now must be a datetime")
    day = moment.astimezone(UTC).date()
    return datetime(day.year, day.month, day.day, tzinfo=UTC)


def is_overdue(due: str | datetime | date | None, now: datetime) -> bool:
    """Whether a task due at ``due`` is overdue at ``now`` (due UTC day < today's UTC day)."""
    day = utc_day(due)
    return day is not None and day < utc_day(now)  # type: ignore[operator]
