from datetime import UTC, datetime

import pytest

from app.common.enums import CalendarEventCategory, CalendarEventSource
from app.domain.models.calendar import CalendarEvent
from app.domain.services.ical_generator import ICalGenerator


@pytest.fixture
def generator():
    return ICalGenerator()


class TestGenerate:
    def test_empty_events(self, generator):
        result = generator.generate([], "Test Feed")
        assert "BEGIN:VCALENDAR" in result
        assert "END:VCALENDAR" in result
        assert "X-WR-CALNAME:Test Feed" in result
        assert "BEGIN:VEVENT" not in result

    def test_single_all_day_event(self, generator):
        event = CalendarEvent(
            id="task:1",
            title="Water plants",
            description="Morning watering",
            category=CalendarEventCategory.FEEDING,
            source=CalendarEventSource.TASK,
            color="#2196F3",
            start=datetime(2026, 3, 15, tzinfo=UTC),
            all_day=True,
        )
        result = generator.generate([event])

        assert "BEGIN:VEVENT" in result
        assert "END:VEVENT" in result
        assert "UID:task:1@kamerplanter" in result
        assert "SUMMARY:Water plants" in result
        assert "DESCRIPTION:Morning watering" in result
        assert "DTSTART;VALUE=DATE:20260315" in result
        assert "DTEND;VALUE=DATE:20260316" in result
        assert "CATEGORIES:feeding" in result

    def test_timed_event(self, generator):
        event = CalendarEvent(
            id="water:1",
            title="Watering",
            category=CalendarEventCategory.FEEDING,
            source=CalendarEventSource.WATERING,
            color="#2196F3",
            start=datetime(2026, 3, 15, 10, 0, 0, tzinfo=UTC),
            end=datetime(2026, 3, 15, 11, 0, 0, tzinfo=UTC),
            all_day=False,
        )
        result = generator.generate([event])

        assert "DTSTART:20260315T100000Z" in result
        assert "DTEND:20260315T110000Z" in result

    def test_timed_event_default_end(self, generator):
        event = CalendarEvent(
            id="water:2",
            title="Quick water",
            category=CalendarEventCategory.FEEDING,
            source=CalendarEventSource.WATERING,
            color="#2196F3",
            start=datetime(2026, 3, 15, 10, 0, 0, tzinfo=UTC),
            all_day=False,
        )
        result = generator.generate([event])

        assert "DTSTART:20260315T100000Z" in result
        assert "DTEND:20260315T110000Z" in result

    def test_multiple_events(self, generator):
        events = [
            CalendarEvent(
                id="task:1",
                title="Task 1",
                category=CalendarEventCategory.TRAINING,
                source=CalendarEventSource.TASK,
                color="#4CAF50",
                start=datetime(2026, 3, 10, tzinfo=UTC),
                all_day=True,
            ),
            CalendarEvent(
                id="task:2",
                title="Task 2",
                category=CalendarEventCategory.PRUNING,
                source=CalendarEventSource.TASK,
                color="#8BC34A",
                start=datetime(2026, 3, 11, tzinfo=UTC),
                all_day=True,
            ),
        ]
        result = generator.generate(events)

        assert result.count("BEGIN:VEVENT") == 2
        assert result.count("END:VEVENT") == 2

    def test_escaping(self, generator):
        event = CalendarEvent(
            id="task:1",
            title="Water; feed, plants",
            description="Line1\nLine2",
            category=CalendarEventCategory.FEEDING,
            source=CalendarEventSource.TASK,
            color="#2196F3",
            start=datetime(2026, 3, 15, tzinfo=UTC),
            all_day=True,
        )
        result = generator.generate([event])

        assert "SUMMARY:Water\\; feed\\, plants" in result
        assert "DESCRIPTION:Line1\\nLine2" in result

    def test_rfc5545_line_endings(self, generator):
        result = generator.generate([])
        # RFC 5545 requires CRLF
        assert "\r\n" in result
