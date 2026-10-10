import re
from datetime import UTC, datetime, timedelta

from app.domain.models.calendar import CalendarEvent

#: RFC 5545 §3.1: a content line SHOULD NOT exceed 75 octets, line break excluded.
_MAX_LINE_OCTETS = 75

#: Characters RFC 5545 allows in no value (§3.3.11 ``TEXT``, §3.1 ``VALUE-CHAR``):
#: every C0 control except HTAB, and DEL. CR and LF are normalised before this
#: applies to TEXT values; in every other value they are removed with the rest.
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0a-\x1f\x7f]")

#: Every line break a parser may honour: CRLF, CR, LF and the three Unicode ones -
#: NEL (U+0085), LINE SEPARATOR (U+2028) and PARAGRAPH SEPARATOR (U+2029). Python's
#: own ``str.splitlines`` and several calendar libraries end a line on each of the
#: Unicode three, so they could end a property like a CR would (#2226 re-review
#: SEC-S2). In a TEXT value each is one escaped ``\n``; elsewhere each is removed.
_LINE_BREAKS = re.compile(r"\r\n|[\r\n\u0085\u2028\u2029]")


class ICalGenerator:
    """Generate RFC 5545 iCalendar output from CalendarEvents."""

    def generate(
        self,
        events: list[CalendarEvent],
        feed_name: str = "Kamerplanter",
    ) -> str:
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Kamerplanter//Calendar//EN",
            f"X-WR-CALNAME:{self._escape(feed_name)}",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
        ]

        for event in events:
            lines.extend(self._event_to_vevent(event))

        lines.append("END:VCALENDAR")
        return "".join(f"{self._fold(line)}\r\n" for line in lines)

    def _event_to_vevent(self, event: CalendarEvent) -> list[str]:
        lines = ["BEGIN:VEVENT"]
        lines.append(f"UID:{self._plain(event.id)}@kamerplanter")
        lines.append(f"DTSTAMP:{self._format_dt(datetime.now(UTC))}")

        if event.start:
            if event.all_day:
                lines.append(
                    f"DTSTART;VALUE=DATE:{event.start.strftime('%Y%m%d')}",
                )
                if event.end:
                    lines.append(
                        f"DTEND;VALUE=DATE:{event.end.strftime('%Y%m%d')}",
                    )
                else:
                    # recurrence-owner-ok: RFC 5545 requires an all-day VEVENT's DTEND to be the
                    # exclusive next midnight; this is the end of ONE event, not the next occurrence
                    # of anything. A recurring calendar event carries its own RRULE property.
                    next_day = event.start + timedelta(days=1)
                    lines.append(
                        f"DTEND;VALUE=DATE:{next_day.strftime('%Y%m%d')}",
                    )
            else:
                lines.append(f"DTSTART:{self._format_dt(event.start)}")
                if event.end:
                    lines.append(f"DTEND:{self._format_dt(event.end)}")
                else:
                    end = event.start + timedelta(hours=1)
                    lines.append(f"DTEND:{self._format_dt(end)}")

        lines.append(f"SUMMARY:{self._escape(event.title)}")
        if event.description:
            lines.append(f"DESCRIPTION:{self._escape(event.description)}")

        lines.append(f"CATEGORIES:{event.category.value}")
        lines.append(f"X-APPLE-CALENDAR-COLOR:{self._plain(event.color)}")

        # REQ-015 v1.6 line 1938: PRIORITY + STATUS as RFC 5545 properties.
        if event.priority is not None:
            lines.append(f"PRIORITY:{event.priority}")
        if event.status:
            lines.append(f"STATUS:{self._plain(event.status).upper()}")

        # REQ-015 v1.6 line 1938: VALARM block when a reminder is requested.
        if event.alarm_minutes_before is not None:
            lines.extend(
                [
                    "BEGIN:VALARM",
                    "ACTION:DISPLAY",
                    f"DESCRIPTION:{self._escape(event.title)}",
                    f"TRIGGER:-PT{event.alarm_minutes_before}M",
                    "END:VALARM",
                ]
            )

        lines.append("END:VEVENT")
        return lines

    @staticmethod
    def _format_dt(dt: datetime) -> str:
        if dt.tzinfo is not None:
            dt = dt.astimezone(UTC)
        return dt.strftime("%Y%m%dT%H%M%SZ")

    @staticmethod
    def _escape(text: str) -> str:
        """``text`` as an RFC 5545 TEXT value (§3.3.11) that stays inside its one property.

        Event titles and descriptions are member-written (task names, plant names,
        notes). A bare CR ended the property for many parsers and let the rest of
        the value read as a new one - ``x\\rATTACH:...`` attached a URL to every
        subscriber's event (#2226 review SEC-002). CRLF, CR, LF, NEL, LINE SEPARATOR
        and PARAGRAPH SEPARATOR are all one line break (``_LINE_BREAKS``, re-review
        SEC-S2), written as the escaped ``\\n``; every other control character is
        dropped; backslash, semicolon and comma are escaped.
        """
        text = _LINE_BREAKS.sub("\n", text)
        text = text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
        text = text.replace("\n", "\\n")
        return _CONTROL_CHARS.sub("", text)

    @staticmethod
    def _plain(value: str) -> str:
        """A non-TEXT value (UID, colour, status): control characters and every line break removed."""
        return _CONTROL_CHARS.sub("", _LINE_BREAKS.sub("", value))

    @staticmethod
    def _fold(line: str) -> str:
        """Fold ``line`` into content lines of at most 75 octets (RFC 5545 §3.1).

        A continuation starts with one space, which counts towards its 75 octets.
        A line breaks only between characters, never inside a UTF-8 sequence.
        """
        if len(line.encode("utf-8")) <= _MAX_LINE_OCTETS:
            return line
        parts: list[str] = []
        current: list[str] = []
        used = 0
        limit = _MAX_LINE_OCTETS
        for char in line:
            size = len(char.encode("utf-8"))
            if used + size > limit:
                parts.append("".join(current))
                current, used, limit = [], 0, _MAX_LINE_OCTETS - 1
            current.append(char)
            used += size
        parts.append("".join(current))
        return "\r\n ".join(parts)
