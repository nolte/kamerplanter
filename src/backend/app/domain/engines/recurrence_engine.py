from datetime import datetime

from dateutil.rrule import rrulestr


class RecurrenceEngine:
    """Single source of truth for turning a recurrence cadence into the next date.

    Pure domain logic (no I/O). Shared by the generic Task recurrence path
    (:meth:`TaskService._create_next_recurring_task`) and the fixed-interval care
    path (:meth:`CareReminderService.ensure_next_watering_task`) so the two no
    longer maintain separate next-occurrence implementations (#510). The care
    engine stays the *interval authority* (it computes the season/phase/adaptive
    interval); this engine only expresses that interval as a rule and advances it.
    """

    @staticmethod
    def fixed_interval_rule(interval_days: int | None) -> str | None:
        """Express a fixed day interval as the canonical iCal RRULE.

        ``FREQ=DAILY;INTERVAL=n`` is the same token the generic recurrence path
        consumes, so a care reminder that recurs "every n days" is advanced by the
        exact same machinery as a hand-authored recurring task. Returns ``None``
        for a missing or non-positive interval (no meaningful recurrence).
        """
        if interval_days is None or interval_days <= 0:
            return None
        return f"FREQ=DAILY;INTERVAL={interval_days}"

    @staticmethod
    def next_occurrence(rule: str | None, after: datetime) -> datetime | None:
        """Return the next occurrence of a recurrence rule strictly after ``after``.

        The canonical recurrence format is an iCal RRULE string as emitted by the
        frontend (e.g. ``FREQ=DAILY``, ``FREQ=WEEKLY;INTERVAL=2``,
        ``FREQ=WEEKLY;BYDAY=MO,WE``), parsed via ``dateutil.rrule``. This aligns
        with the REQ-015 iCal token so a single format spans task recurrence and
        calendar export.

        Legacy cron expressions are tolerated as a fallback: if the rule does not
        parse as an RRULE, it is retried with ``croniter``. No cron strings are
        known to be persisted today, but the fallback keeps any historically
        created rule working. An empty or unparseable rule yields ``None``.
        """
        if not rule:
            return None

        # Canonical path: iCal RRULE via dateutil. dtstart=after makes the rule
        # relative to "now"; inc=False returns the first occurrence *after* it.
        try:
            rule_set = rrulestr(rule, dtstart=after)
        except (ValueError, TypeError) as exc:  # noqa: F841 — parens kept vs ruff-format tuple strip
            rule_set = None
        if rule_set is not None:
            return rule_set.after(after, inc=False)

        # Legacy fallback: cron syntax via croniter.
        try:
            from croniter import croniter

            return croniter(rule, after).get_next(datetime)
        except (ValueError, KeyError, TypeError) as exc:  # noqa: F841 — parens kept vs ruff-format tuple strip
            return None
