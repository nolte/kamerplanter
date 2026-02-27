import secrets

from app.common.exceptions import NotFoundError, ValidationError
from app.domain.engines.calendar_aggregation_engine import CalendarAggregationEngine
from app.domain.interfaces.calendar_feed_repository import ICalendarFeedRepository
from app.domain.models.calendar import (
    CalendarEvent,
    CalendarEventsQuery,
    CalendarFeed,
)
from app.domain.services.ical_generator import ICalGenerator


class CalendarService:
    def __init__(
        self,
        feed_repo: ICalendarFeedRepository,
        aggregation_engine: CalendarAggregationEngine,
    ) -> None:
        self._feed_repo = feed_repo
        self._engine = aggregation_engine
        self._ical = ICalGenerator()

    def get_events(self, query: CalendarEventsQuery) -> list[CalendarEvent]:
        return self._engine.get_events(query)

    # ── Feed CRUD ────────────────────────────────────────────────────

    def create_feed(self, feed: CalendarFeed) -> CalendarFeed:
        feed.token = secrets.token_urlsafe(32)
        return self._feed_repo.save(feed)

    def get_feed(self, key: str) -> CalendarFeed:
        feed = self._feed_repo.get_by_key(key)
        if feed is None:
            raise NotFoundError("CalendarFeed", key)
        return feed

    def list_feeds(self, user_key: str, tenant_key: str) -> list[CalendarFeed]:
        return self._feed_repo.list_by_user(user_key, tenant_key)

    def update_feed(self, key: str, feed: CalendarFeed) -> CalendarFeed:
        existing = self.get_feed(key)
        feed.token = existing.token
        return self._feed_repo.update(key, feed)

    def delete_feed(self, key: str) -> bool:
        self.get_feed(key)
        return self._feed_repo.delete(key)

    def regenerate_token(self, key: str) -> CalendarFeed:
        feed = self.get_feed(key)
        feed.token = secrets.token_urlsafe(32)
        return self._feed_repo.update(key, feed)

    # ── iCal generation ──────────────────────────────────────────────

    def generate_ical_for_feed(self, feed_key: str, token: str) -> str:
        feed = self._feed_repo.get_by_token(token)
        if feed is None or feed.key != feed_key:
            raise ValidationError("Invalid feed token")
        if not feed.is_active:
            raise ValidationError("Feed is inactive")

        from datetime import date, timedelta

        query = CalendarEventsQuery(
            start_date=date.today() - timedelta(days=30),
            end_date=date.today() + timedelta(days=90),
            categories=feed.filters.categories,
            site_key=feed.filters.site_key,
            tenant_key=feed.tenant_key,
        )
        events = self._engine.get_events(query)
        return self._ical.generate(events, feed.name)
