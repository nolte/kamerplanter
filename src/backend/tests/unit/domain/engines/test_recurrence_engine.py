"""Tests for the shared RecurrenceEngine (#510).

Locks the single next-occurrence implementation now reused by both the generic
Task recurrence path (``TaskService._create_next_recurring_task``) and the
fixed-interval care path (``CareReminderService.ensure_next_watering_task``).
"""

from datetime import UTC, datetime

import pytest

from app.common.exceptions import RecurrenceRuleRequiredError, ValidationError
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

    def test_a_cron_string_is_no_longer_advanced(self) -> None:
        """M5 (#2325): the croniter fallback is gone — a stored cron rule cannot exist after v0097."""
        assert RecurrenceEngine.next_occurrence("0 9 * * *", self._AFTER) is None

    def test_empty_rule_returns_none(self) -> None:
        assert RecurrenceEngine.next_occurrence("", self._AFTER) is None

    def test_none_rule_returns_none(self) -> None:
        assert RecurrenceEngine.next_occurrence(None, self._AFTER) is None

    def test_garbage_rule_returns_none(self) -> None:
        assert RecurrenceEngine.next_occurrence("not-a-rule", self._AFTER) is None


class TestRequireRrule:
    """GP-ACC-038: the service boundary refuses anything that is not an RRULE with ``recurrence.rrule_required``."""

    @pytest.mark.parametrize(
        "rule", [None, "", "FREQ=DAILY", "FREQ=WEEKLY;BYDAY=MO;BYHOUR=8;BYMINUTE=0", "FREQ=DAILY;INTERVAL=3"]
    )
    def test_empty_or_rrule_passes_through(self, rule: str | None) -> None:
        assert RecurrenceEngine.require_rrule(rule) == rule

    @pytest.mark.parametrize("rule", ["0 8 * * 1", "*/15 * * * *", "weekly", "not-a-rule"])
    def test_cron_or_garbage_is_refused_with_the_code(self, rule: str) -> None:
        with pytest.raises(RecurrenceRuleRequiredError) as excinfo:
            RecurrenceEngine.require_rrule(rule)

        assert excinfo.value.status_code == 422
        assert excinfo.value.error_code == "recurrence.rrule_required"
        assert isinstance(excinfo.value, ValidationError), "existing handlers keep catching it"
