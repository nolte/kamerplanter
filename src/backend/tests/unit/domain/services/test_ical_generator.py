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


def _unfold(ics: str) -> list[str]:
    """The logical content lines of ``ics`` (RFC 5545 §3.1: CRLF + one space continues a line)."""
    return ics.replace("\r\n ", "").split("\r\n")


def _property_names(ics: str) -> list[str]:
    return [line.split(":", 1)[0].split(";", 1)[0] for line in _unfold(ics) if line]


class TestMemberWrittenTextStaysInItsProperty:
    """#2226 review SEC-002 — a title or description cannot add a property to a subscriber's event.

    Measured before the change: ``_escape`` turned LF into ``\\n`` but left CR as
    it was, so ``x\\rATTACH:https://evil.example/a.exe`` produced a line break
    inside SUMMARY and many parsers read an ``ATTACH`` property of its own.
    """

    @pytest.mark.parametrize("breaker", ["\r", "\n", "\r\n"], ids=["CR", "LF", "CRLF"])
    def test_a_line_break_cannot_start_a_new_property(self, generator, breaker: str) -> None:
        event = CalendarEvent(
            id="task:1",
            title=f"Water{breaker}ATTACH:https://evil.example/a.exe",
            description=f"note{breaker}END:VEVENT{breaker}BEGIN:VEVENT",
            start=datetime(2026, 3, 15, tzinfo=UTC),
            all_day=True,
        )

        ics = generator.generate([event], f"Garden{breaker}X-INJECTED:1")

        assert "ATTACH" not in _property_names(ics)
        assert "X-INJECTED" not in _property_names(ics)
        assert _property_names(ics).count("BEGIN") == 2  # VCALENDAR + the one VEVENT
        assert "SUMMARY:Water\\nATTACH:https://evil.example/a.exe" in _unfold(ics)
        assert "\r" not in ics.replace("\r\n", "")
        assert "\n" not in ics.replace("\r\n", "")

    def test_other_control_characters_are_dropped(self, generator) -> None:
        event = CalendarEvent(
            id="task:\x001", title="A\x00B\x1bC\x7fD\tE", color="#fff\r\nX-BAD:1", status="tentative\n"
        )

        lines = _unfold(generator.generate([event]))

        assert "SUMMARY:ABCD\tE" in lines
        assert "UID:task:1@kamerplanter" in lines
        assert "X-APPLE-CALENDAR-COLOR:#fffX-BAD:1" in lines
        assert "STATUS:TENTATIVE" in lines

    def test_backslash_semicolon_and_comma_stay_escaped(self, generator) -> None:
        event = CalendarEvent(id="task:1", title="a\\b;c,d")

        assert r"SUMMARY:a\\b\;c\,d" in _unfold(generator.generate([event]))


_UNICODE_BREAKS = ["\u0085", " ", " "]


class TestUnicodeLineBreaksStayInTheirProperty:
    """#2226 re-review SEC-S2 — NEL, LINE SEPARATOR and PARAGRAPH SEPARATOR are line breaks too.

    Measured before the change: ``_escape`` and ``_plain`` handled CR and LF only,
    so the three Unicode breaks reached the document as they were - and a parser
    that splits lines the way ``str.splitlines`` does read the text after them as
    a property of its own.
    """

    @pytest.mark.parametrize("breaker", _UNICODE_BREAKS, ids=["NEL", "LS", "PS"])
    def test_in_a_text_value_it_is_an_escaped_line_break(self, generator, breaker: str) -> None:
        event = CalendarEvent(
            id="task:1",
            title=f"Water{breaker}ATTACH:https://evil.example/a.exe",
            description=f"note{breaker}END:VEVENT",
        )

        ics = generator.generate([event], f"Garden{breaker}X-INJECTED:1")
        split_like_python = [line.split(":", 1)[0] for line in ics.replace("\r\n ", "").splitlines()]

        assert breaker not in ics
        assert "ATTACH" not in split_like_python
        assert "X-INJECTED" not in split_like_python
        assert "SUMMARY:Water\\nATTACH:https://evil.example/a.exe" in _unfold(ics)
        assert "DESCRIPTION:note\\nEND:VEVENT" in _unfold(ics)
        assert "X-WR-CALNAME:Garden\\nX-INJECTED:1" in _unfold(ics)

    @pytest.mark.parametrize("breaker", _UNICODE_BREAKS, ids=["NEL", "LS", "PS"])
    def test_in_any_other_value_it_is_removed(self, generator, breaker: str) -> None:
        event = CalendarEvent(id=f"task:1{breaker}X", color=f"#fff{breaker}X-BAD:1", status=f"tentative{breaker}")

        ics = generator.generate([event])
        lines = _unfold(ics)

        assert breaker not in ics
        assert "UID:task:1X@kamerplanter" in lines
        assert "X-APPLE-CALENDAR-COLOR:#fffX-BAD:1" in lines
        assert "STATUS:TENTATIVE" in lines


class TestLongLinesAreFolded:
    """RFC 5545 §3.1 — no content line exceeds 75 octets; unfolding gives back the value."""

    def test_every_physical_line_is_at_most_75_octets(self, generator) -> None:
        title = "Tomaten gießen und düngen " * 12
        event = CalendarEvent(id="task:1", title=title, description="Ä" * 200)

        ics = generator.generate([event], "Gemüsegarten " * 10)

        assert ics.endswith("\r\n")
        for line in ics.split("\r\n"):
            assert len(line.encode("utf-8")) <= 75, line
        assert f"SUMMARY:{title}" in _unfold(ics)
        assert "DESCRIPTION:" + "Ä" * 200 in _unfold(ics)

    def test_a_fold_never_splits_a_multibyte_character(self, generator) -> None:
        ics = generator.generate([CalendarEvent(id="task:1", title="🌱" * 60)])

        for line in ics.split("\r\n"):
            line.encode("utf-8").decode("utf-8")  # a split sequence would have been replaced on decode
            assert "�" not in line

    def test_a_short_line_is_left_alone(self, generator) -> None:
        assert "SUMMARY:Water plants\r\n" in generator.generate([CalendarEvent(id="t", title="Water plants")])
