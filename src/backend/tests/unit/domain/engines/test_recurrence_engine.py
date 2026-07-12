"""Tests for the shared RecurrenceEngine (#510).

Locks the single next-occurrence implementation now reused by both the generic
Task recurrence path (``TaskService._create_next_recurring_task``) and the
fixed-interval care path (``CareReminderService.ensure_next_watering_task``).
"""

from datetime import UTC, datetime

from app.domain.engines.recurrence_engine import RecurrenceEngine


class TestFixedIntervalRule:
    def test_positive_interval_becomes_daily_rrule(self) -> None:
        assert RecurrenceEngine.fixed_interval_rule(7) == "FREQ=DAILY;INTERVAL=7"

    def test_none_interval_yields_no_rule(self) -> None:
        assert RecurrenceEngine.fixed_interval_rule(None) is None

    def test_non_positive_interval_yields_no_rule(self) -> None:
        assert RecurrenceEngine.fixed_interval_rule(0) is None
        assert RecurrenceEngine.fixed_interval_rule(-3) is None


class TestNextOccurrence:
    # Monday, 2026-01-05 at 12:00 UTC — reference point.
    _AFTER = datetime(2026, 1, 5, 12, 0, tzinfo=UTC)

    def test_rrule_daily_advances_one_day(self) -> None:
        assert RecurrenceEngine.next_occurrence("FREQ=DAILY", self._AFTER) == datetime(2026, 1, 6, 12, 0, tzinfo=UTC)

    def test_fixed_interval_rule_advances_by_interval(self) -> None:
        rule = RecurrenceEngine.fixed_interval_rule(7)
        base = datetime(2026, 3, 5, 0, 0, tzinfo=UTC)

        assert RecurrenceEngine.next_occurrence(rule, base) == datetime(2026, 3, 12, 0, 0, tzinfo=UTC)

    def test_rrule_weekly_advances_seven_days(self) -> None:
        assert RecurrenceEngine.next_occurrence("FREQ=WEEKLY", self._AFTER) == datetime(2026, 1, 12, 12, 0, tzinfo=UTC)

    def test_rrule_byday_picks_next_matching_weekday(self) -> None:
        next_dt = RecurrenceEngine.next_occurrence("FREQ=WEEKLY;BYDAY=MO,WE", self._AFTER)

        assert next_dt == datetime(2026, 1, 7, 12, 0, tzinfo=UTC)

    def test_legacy_cron_string_falls_back_to_croniter(self) -> None:
        assert RecurrenceEngine.next_occurrence("0 9 * * *", self._AFTER) == datetime(2026, 1, 6, 9, 0, tzinfo=UTC)

    def test_empty_rule_returns_none(self) -> None:
        assert RecurrenceEngine.next_occurrence("", self._AFTER) is None

    def test_none_rule_returns_none(self) -> None:
        assert RecurrenceEngine.next_occurrence(None, self._AFTER) is None

    def test_garbage_rule_returns_none(self) -> None:
        assert RecurrenceEngine.next_occurrence("not-a-rule", self._AFTER) is None
