from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.common.exceptions import NotFoundError, ValidationError
from app.domain.models.calendar import CalendarFeed, CalendarFeedFilters
from app.domain.services.calendar_service import CalendarService


@pytest.fixture
def mock_repo():
    return MagicMock()


@pytest.fixture
def mock_engine():
    return MagicMock()


@pytest.fixture
def service(mock_repo, mock_engine):
    return CalendarService(mock_repo, mock_engine)


class TestCreateFeed:
    def test_generates_token(self, service, mock_repo):
        feed = CalendarFeed(name="My Feed", tenant_key="t1", user_key="u1")
        mock_repo.save.return_value = feed

        result = service.create_feed(feed)

        assert feed.token != ""
        mock_repo.save.assert_called_once()


class TestGetFeed:
    def test_found(self, service, mock_repo):
        feed = CalendarFeed(
            name="Feed", tenant_key="t1", user_key="u1",
        )
        feed.key = "f1"
        mock_repo.get_by_key.return_value = feed

        result = service.get_feed("f1")
        assert result.name == "Feed"

    def test_not_found(self, service, mock_repo):
        mock_repo.get_by_key.return_value = None

        with pytest.raises(NotFoundError):
            service.get_feed("missing")


class TestUpdateFeed:
    def test_preserves_token(self, service, mock_repo):
        existing = CalendarFeed(
            name="Old", tenant_key="t1", user_key="u1", token="secret123",
        )
        existing.key = "f1"
        mock_repo.get_by_key.return_value = existing
        mock_repo.update.return_value = existing

        updated = CalendarFeed(name="New", tenant_key="t1", user_key="u1")
        service.update_feed("f1", updated)

        call_args = mock_repo.update.call_args
        assert call_args[0][1].token == "secret123"


class TestRegenerateToken:
    def test_new_token(self, service, mock_repo):
        feed = CalendarFeed(
            name="Feed", tenant_key="t1", user_key="u1", token="old-token",
        )
        feed.key = "f1"
        mock_repo.get_by_key.return_value = feed
        mock_repo.update.return_value = feed

        service.regenerate_token("f1")

        call_args = mock_repo.update.call_args
        new_token = call_args[0][1].token
        assert new_token != "old-token"
        assert len(new_token) > 10


class TestDeleteFeed:
    def test_delete(self, service, mock_repo):
        feed = CalendarFeed(name="Feed", tenant_key="t1", user_key="u1")
        feed.key = "f1"
        mock_repo.get_by_key.return_value = feed
        mock_repo.delete.return_value = True

        assert service.delete_feed("f1") is True

    def test_delete_not_found(self, service, mock_repo):
        mock_repo.get_by_key.return_value = None

        with pytest.raises(NotFoundError):
            service.delete_feed("missing")


class TestGenerateIcalForFeed:
    def test_valid_token(self, service, mock_repo, mock_engine):
        feed = CalendarFeed(
            name="Feed", tenant_key="t1", user_key="u1", token="tok123",
        )
        feed.key = "f1"
        mock_repo.get_by_token.return_value = feed
        mock_engine.get_events.return_value = []

        result = service.generate_ical_for_feed("f1", "tok123")

        assert "BEGIN:VCALENDAR" in result
        assert "END:VCALENDAR" in result

    def test_invalid_token(self, service, mock_repo):
        mock_repo.get_by_token.return_value = None

        with pytest.raises(ValidationError):
            service.generate_ical_for_feed("f1", "wrong-token")

    def test_inactive_feed(self, service, mock_repo):
        feed = CalendarFeed(
            name="Feed", tenant_key="t1", user_key="u1",
            token="tok123", is_active=False,
        )
        feed.key = "f1"
        mock_repo.get_by_token.return_value = feed

        with pytest.raises(ValidationError, match="inactive"):
            service.generate_ical_for_feed("f1", "tok123")

    def test_wrong_feed_key(self, service, mock_repo):
        feed = CalendarFeed(
            name="Feed", tenant_key="t1", user_key="u1", token="tok123",
        )
        feed.key = "f1"
        mock_repo.get_by_token.return_value = feed

        with pytest.raises(ValidationError):
            service.generate_ical_for_feed("wrong-key", "tok123")
