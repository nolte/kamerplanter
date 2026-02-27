from datetime import UTC, datetime, timedelta

from app.domain.models.calendar import CalendarEvent


class ICalGenerator:
    """Generate RFC 5545 iCalendar output from CalendarEvents."""

    def generate(
        self, events: list[CalendarEvent], feed_name: str = "Kamerplanter",
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
        return "\r\n".join(lines) + "\r\n"

    def _event_to_vevent(self, event: CalendarEvent) -> list[str]:
        lines = ["BEGIN:VEVENT"]
        lines.append(f"UID:{event.id}@kamerplanter")
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
        lines.append(f"X-APPLE-CALENDAR-COLOR:{event.color}")

        lines.append("END:VEVENT")
        return lines

    @staticmethod
    def _format_dt(dt: datetime) -> str:
        if dt.tzinfo is not None:
            dt = dt.astimezone(UTC)
        return dt.strftime("%Y%m%dT%H%M%SZ")

    @staticmethod
    def _escape(text: str) -> str:
        return (
            text.replace("\\", "\\\\")
            .replace(";", "\\;")
            .replace(",", "\\,")
            .replace("\n", "\\n")
        )
