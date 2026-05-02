"""REQ-015 v1.6 — VALARM, PRIORITY, STATUS in iCal output and HTTP 410 on expired feeds."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.common.exceptions import FeedExpiredError, ValidationError
from app.domain.models.calendar import CalendarEvent, CalendarFeed, CalendarFeedFilters
from app.domain.services.ical_generator import ICalGenerator


def _event(**overrides) -> CalendarEvent:
    base = {
        "id": "evt-1",
        "title": "Wässern",
        "start": datetime(2026, 5, 1, 9, 0),
    }
    base.update(overrides)
    return CalendarEvent(**base)


class TestICalV16Properties:
    def test_priority_is_emitted_when_set(self):
        ical = ICalGenerator().generate([_event(priority=5)])
        assert "PRIORITY:5" in ical

    def test_priority_is_omitted_when_none(self):
        ical = ICalGenerator().generate([_event()])
        assert "PRIORITY:" not in ical

    def test_status_is_emitted_uppercase(self):
        ical = ICalGenerator().generate([_event(status="confirmed")])
        assert "STATUS:CONFIRMED" in ical

    def test_valarm_block_emitted_when_alarm_minutes_set(self):
        ical = ICalGenerator().generate([_event(alarm_minutes_before=30)])
        assert "BEGIN:VALARM" in ical
        assert "ACTION:DISPLAY" in ical
        assert "TRIGGER:-PT30M" in ical
        assert "END:VALARM" in ical

    def test_no_valarm_when_no_alarm_minutes(self):
        ical = ICalGenerator().generate([_event()])
        assert "VALARM" not in ical


class TestFeedExpiry:
    def _feed(self, expires_at: datetime | None = None) -> CalendarFeed:
        return CalendarFeed(
            key="feed-1",
            tenant_key="t-1",
            name="My feed",
            token="tkn-abc",
            user_key="u-1",
            filters=CalendarFeedFilters(),
            is_active=True,
            expires_at=expires_at,
        )

    def test_generate_ical_raises_410_when_feed_expired(self):
        from app.domain.services.calendar_service import CalendarService

        feed = self._feed(expires_at=datetime.now() - timedelta(hours=1))
        feed_repo = MagicMock()
        feed_repo.get_by_token.return_value = feed

        svc = CalendarService(
            feed_repo=feed_repo,
            aggregation_engine=MagicMock(),
        )

        with pytest.raises(FeedExpiredError) as exc:
            svc.generate_ical_for_feed("feed-1", "tkn-abc")
        assert exc.value.status_code == 410

    def test_generate_ical_succeeds_when_feed_not_yet_expired(self):
        from app.domain.services.calendar_service import CalendarService

        feed = self._feed(expires_at=datetime.now() + timedelta(days=1))
        feed_repo = MagicMock()
        feed_repo.get_by_token.return_value = feed
        engine = MagicMock()
        engine.get_events.return_value = []

        svc = CalendarService(
            feed_repo=feed_repo,
            aggregation_engine=engine,
        )

        result = svc.generate_ical_for_feed("feed-1", "tkn-abc")
        assert result.startswith("BEGIN:VCALENDAR")

    def test_generate_ical_invalid_token_still_raises_validation(self):
        from app.domain.services.calendar_service import CalendarService

        feed_repo = MagicMock()
        feed_repo.get_by_token.return_value = None

        svc = CalendarService(
            feed_repo=feed_repo,
            aggregation_engine=MagicMock(),
        )

        with pytest.raises(ValidationError):
            svc.generate_ical_for_feed("feed-1", "wrong-token")
