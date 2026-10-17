from datetime import datetime
from typing import cast

import structlog
from dateutil.rrule import rrulestr

from app.common.exceptions import RecurrenceRuleRequiredError

logger = structlog.get_logger(__name__)


class RecurrenceEngine:
    """Single source of truth for turning a recurrence cadence into the next date.

    Pure domain logic (no I/O). Shared by the generic Task recurrence path
    (:meth:`TaskService._create_next_recurring_task`) and the fixed-interval care
    path (:meth:`CareReminderService.ensure_next_watering_task`) so the two no
    longer maintain separate next-occurrence implementations (#510). The care
    engine stays the *interval authority* (it computes the season/phase/adaptive
    interval); this engine only expresses that interval as a rule and advances it.

    The only recurrence format is an RFC 5545 RRULE (ADR-008, REQ-006 v3.5). The
    croniter fallback that once tolerated legacy cron strings is gone: migration M5
    (v0097, #2325) converted every stored cron rule, and the service boundary
    refuses a new one with ``recurrence.rrule_required`` (:meth:`require_rrule`).
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
    def parses_as_rrule(rule: str) -> bool:
        """Whether ``dateutil.rrule`` accepts ``rule`` as an RRULE (a cron string never does)."""
        try:
            rrulestr(rule, dtstart=datetime(2000, 1, 1))
        except (ValueError, TypeError) as exc:  # noqa: F841 — parens kept vs ruff-format tuple strip
            return False
        return True

    @classmethod
    def require_rrule(cls, rule: str | None) -> str | None:
        """Return ``rule`` when it is empty or a parseable RRULE; refuse anything else (GP-ACC-038).

        Raises :class:`RecurrenceRuleRequiredError` (422, ``recurrence.rrule_required``)
        for a cron expression or any other unparseable string. Called where a rule
        is persisted — the task create and update paths — so no new non-RRULE rule
        reaches storage after M5.
        """
        if not rule:
            return rule
        if not cls.parses_as_rrule(rule):
            raise RecurrenceRuleRequiredError(rule)
        return rule

    @staticmethod
    def next_occurrence(rule: str | None, after: datetime) -> datetime | None:
        """Return the next occurrence of a recurrence rule strictly after ``after``.

        The canonical recurrence format is an iCal RRULE string as emitted by the
        frontend (e.g. ``FREQ=DAILY``, ``FREQ=WEEKLY;INTERVAL=2``,
        ``FREQ=WEEKLY;BYDAY=MO,WE``), parsed via ``dateutil.rrule``. This aligns
        with the REQ-015 iCal token so a single format spans task recurrence and
        calendar export. An empty or unparseable rule yields ``None`` — a stored
        rule that is not an RRULE cannot exist after M5, and a reader never guesses.
        """
        if not rule:
            return None

        # dtstart=after makes the rule relative to "now"; inc=False returns the
        # first occurrence *after* it.
        try:
            rule_set = rrulestr(rule, dtstart=after)
        except (ValueError, TypeError) as exc:  # noqa: F841 — parens kept vs ruff-format tuple strip
            # A stored non-RRULE rule means M5 (v0097) refused or has not run; say so
            # instead of silently ending the recurrence.
            logger.warning("recurrence_rule_unparseable", rule=rule)
            return None
        return cast("datetime | None", rule_set.after(after, inc=False))
