from datetime import date, datetime
from unittest.mock import MagicMock

import pytest

from app.common.exceptions import NotFoundError, ValidationError
from app.domain.engines.token_engine import TokenEngine
from app.domain.models.calendar import CalendarFeed
from app.domain.services.calendar_service import CalendarService
from tests.conftest import wire_get_or_raise


@pytest.fixture
def mock_repo():
    return wire_get_or_raise(MagicMock(), "CalendarFeed")


@pytest.fixture
def mock_engine():
    return MagicMock()


@pytest.fixture
def service(mock_repo, mock_engine):
    return CalendarService(mock_repo, mock_engine, MagicMock())


class TestCreateFeed:
    def test_generates_token_and_stores_only_its_hash(self, service, mock_repo):
        feed = CalendarFeed(name="My Feed", tenant_key="t1", user_key="u1")
        mock_repo.save.return_value = feed

        issued = service.create_feed(feed)

        assert len(issued.token) > 10
        saved = mock_repo.save.call_args[0][0]
        assert saved.token_hash == TokenEngine.hash_token(issued.token)
        assert issued.token not in saved.model_dump_json()
        mock_repo.save.assert_called_once()


class TestGetFeed:
    def test_found(self, service, mock_repo):
        feed = CalendarFeed(
            name="Feed",
            tenant_key="t1",
            user_key="u1",
        )
        feed.key = "f1"
        mock_repo.get_by_key.return_value = feed

        result = service.get_feed("f1", tenant_key="t1")
        assert result.name == "Feed"

    def test_not_found(self, service, mock_repo):
        mock_repo.get_by_key.return_value = None

        with pytest.raises(NotFoundError):
            service.get_feed("missing", tenant_key="t1")


class TestUpdateFeed:
    def test_preserves_token_hash(self, service, mock_repo):
        existing = CalendarFeed(
            name="Old",
            tenant_key="t1",
            user_key="u1",
            token_hash="digest123",
        )
        existing.key = "f1"
        mock_repo.get_by_key.return_value = existing
        mock_repo.update.return_value = existing

        updated = CalendarFeed(name="New", tenant_key="t1", user_key="u1")
        service.update_feed("f1", updated, tenant_key="t1")

        call_args = mock_repo.update.call_args
        assert call_args[0][1].token_hash == "digest123"


class TestRegenerateToken:
    def test_new_token(self, service, mock_repo):
        feed = CalendarFeed(
            name="Feed",
            tenant_key="t1",
            user_key="u1",
            token_hash=TokenEngine.hash_token("old-token"),
        )
        feed.key = "f1"
        mock_repo.get_by_key.return_value = feed
        mock_repo.update.return_value = feed

        issued = service.regenerate_token("f1", tenant_key="t1")

        written = mock_repo.update.call_args[0][1]
        assert issued.token != "old-token"
        assert len(issued.token) > 10
        assert written.token_hash == TokenEngine.hash_token(issued.token)


class TestDeleteFeed:
    def test_delete(self, service, mock_repo):
        feed = CalendarFeed(name="Feed", tenant_key="t1", user_key="u1")
        feed.key = "f1"
        mock_repo.get_by_key.return_value = feed
        mock_repo.delete.return_value = True

        assert service.delete_feed("f1", tenant_key="t1") is True

    def test_delete_not_found(self, service, mock_repo):
        mock_repo.get_by_key.return_value = None

        with pytest.raises(NotFoundError):
            service.delete_feed("missing", tenant_key="t1")


class TestGenerateIcalForFeed:
    def test_valid_token(self, service, mock_repo, mock_engine):
        feed = CalendarFeed(
            name="Feed",
            tenant_key="t1",
            user_key="u1",
            token_hash=TokenEngine.hash_token("tok123"),
        )
        feed.key = "f1"
        mock_repo.get_by_token_hash.return_value = feed
        mock_engine.aggregate.return_value = []

        result = service.generate_ical_for_feed("f1", "tok123")

        assert "BEGIN:VCALENDAR" in result
        assert "END:VCALENDAR" in result
        mock_repo.get_by_token_hash.assert_called_once_with(TokenEngine.hash_token("tok123"))

    def test_an_empty_token_never_reaches_the_lookup(self, service, mock_repo):
        with pytest.raises(ValidationError):
            service.generate_ical_for_feed("f1", "")
        mock_repo.get_by_token_hash.assert_not_called()

    def test_invalid_token(self, service, mock_repo):
        mock_repo.get_by_token_hash.return_value = None

        with pytest.raises(ValidationError):
            service.generate_ical_for_feed("f1", "wrong-token")

    def test_inactive_feed(self, service, mock_repo):
        feed = CalendarFeed(
            name="Feed",
            tenant_key="t1",
            user_key="u1",
            token_hash=TokenEngine.hash_token("tok123"),
            is_active=False,
        )
        feed.key = "f1"
        mock_repo.get_by_token_hash.return_value = feed

        with pytest.raises(ValidationError, match="inactive"):
            service.generate_ical_for_feed("f1", "tok123")

    def test_wrong_feed_key(self, service, mock_repo):
        feed = CalendarFeed(
            name="Feed",
            tenant_key="t1",
            user_key="u1",
            token_hash=TokenEngine.hash_token("tok123"),
        )
        feed.key = "f1"
        mock_repo.get_by_token_hash.return_value = feed

        with pytest.raises(ValidationError):
            service.generate_ical_for_feed("wrong-key", "tok123")


class TestTimelineToBars:
    """Tests for CalendarService._timeline_to_bars static method."""

    def test_converts_completed_phase(self):
        timelines = [
            {
                "species_key": "sp1",
                "phases": [
                    {
                        "phase_name": "germination",
                        "display_name": "Germination",
                        "status": "completed",
                        "actual_entered_at": datetime(2026, 2, 1, 8, 0),
                        "actual_exited_at": datetime(2026, 2, 14, 8, 0),
                        "projected_start": None,
                        "projected_end": None,
                    }
                ],
            }
        ]
        bars = CalendarService._timeline_to_bars(timelines, 2026)
        assert len(bars) == 1
        assert bars[0].phase == "germination"
        assert bars[0].start_date == date(2026, 2, 1)
        assert bars[0].end_date == date(2026, 2, 14)
        assert bars[0].color == "#FDD835"

    def test_converts_projected_phase(self):
        timelines = [
            {
                "species_key": "sp1",
                "phases": [
                    {
                        "phase_name": "flowering",
                        "display_name": "Flowering",
                        "status": "projected",
                        "actual_entered_at": None,
                        "actual_exited_at": None,
                        "projected_start": datetime(2026, 6, 1),
                        "projected_end": datetime(2026, 7, 31),
                    }
                ],
            }
        ]
        bars = CalendarService._timeline_to_bars(timelines, 2026)
        assert len(bars) == 1
        assert bars[0].phase == "flowering"
        assert bars[0].color == "#EC407A"

    def test_current_phase_uses_entered_and_projected_end(self):
        timelines = [
            {
                "species_key": "sp1",
                "phases": [
                    {
                        "phase_name": "vegetative",
                        "display_name": "Vegetative",
                        "status": "current",
                        "actual_entered_at": datetime(2026, 3, 15),
                        "actual_exited_at": None,
                        "projected_start": None,
                        "projected_end": datetime(2026, 5, 31),
                    }
                ],
            }
        ]
        bars = CalendarService._timeline_to_bars(timelines, 2026)
        assert len(bars) == 1
        assert bars[0].start_date == date(2026, 3, 15)
        assert bars[0].end_date == date(2026, 5, 31)

    def test_skips_phase_outside_year(self):
        timelines = [
            {
                "species_key": "sp1",
                "phases": [
                    {
                        "phase_name": "harvest",
                        "display_name": "Harvest",
                        "status": "completed",
                        "actual_entered_at": datetime(2025, 8, 1),
                        "actual_exited_at": datetime(2025, 9, 30),
                        "projected_start": None,
                        "projected_end": None,
                    }
                ],
            }
        ]
        bars = CalendarService._timeline_to_bars(timelines, 2026)
        assert len(bars) == 0

    def test_clamps_to_year_boundaries(self):
        timelines = [
            {
                "species_key": "sp1",
                "phases": [
                    {
                        "phase_name": "vegetative",
                        "display_name": "Vegetative",
                        "status": "completed",
                        "actual_entered_at": datetime(2025, 11, 1),
                        "actual_exited_at": datetime(2026, 3, 31),
                        "projected_start": None,
                        "projected_end": None,
                    }
                ],
            }
        ]
        bars = CalendarService._timeline_to_bars(timelines, 2026)
        assert len(bars) == 1
        assert bars[0].start_date == date(2026, 1, 1)
        assert bars[0].end_date == date(2026, 3, 31)

    def test_skips_phase_without_dates(self):
        timelines = [
            {
                "species_key": "sp1",
                "phases": [
                    {
                        "phase_name": "harvest",
                        "display_name": "Harvest",
                        "status": "projected",
                        "actual_entered_at": None,
                        "actual_exited_at": None,
                        "projected_start": None,
                        "projected_end": None,
                    }
                ],
            }
        ]
        bars = CalendarService._timeline_to_bars(timelines, 2026)
        assert len(bars) == 0

    def test_multiple_phases(self):
        timelines = [
            {
                "species_key": "sp1",
                "phases": [
                    {
                        "phase_name": "germination",
                        "display_name": "Germination",
                        "status": "completed",
                        "actual_entered_at": datetime(2026, 2, 1),
                        "actual_exited_at": datetime(2026, 2, 14),
                        "projected_start": None,
                        "projected_end": None,
                    },
                    {
                        "phase_name": "seedling",
                        "display_name": "Seedling",
                        "status": "completed",
                        "actual_entered_at": datetime(2026, 2, 15),
                        "actual_exited_at": datetime(2026, 3, 15),
                        "projected_start": None,
                        "projected_end": None,
                    },
                    {
                        "phase_name": "vegetative",
                        "display_name": "Vegetative",
                        "status": "current",
                        "actual_entered_at": datetime(2026, 3, 16),
                        "actual_exited_at": None,
                        "projected_start": None,
                        "projected_end": datetime(2026, 5, 31),
                    },
                ],
            }
        ]
        bars = CalendarService._timeline_to_bars(timelines, 2026)
        assert len(bars) == 3
        assert [b.phase for b in bars] == ["germination", "seedling", "vegetative"]

    def test_handles_iso_string_dates(self):
        timelines = [
            {
                "species_key": "sp1",
                "phases": [
                    {
                        "phase_name": "harvest",
                        "display_name": "Harvest",
                        "status": "completed",
                        "actual_entered_at": "2026-08-01T00:00:00",
                        "actual_exited_at": "2026-09-30T00:00:00",
                        "projected_start": None,
                        "projected_end": None,
                    }
                ],
            }
        ]
        bars = CalendarService._timeline_to_bars(timelines, 2026)
        assert len(bars) == 1
        assert bars[0].start_date == date(2026, 8, 1)

    def test_unknown_phase_gets_grey_color(self):
        timelines = [
            {
                "species_key": "sp1",
                "phases": [
                    {
                        "phase_name": "custom_phase",
                        "display_name": "Custom",
                        "status": "completed",
                        "actual_entered_at": datetime(2026, 5, 1),
                        "actual_exited_at": datetime(2026, 5, 31),
                        "projected_start": None,
                        "projected_end": None,
                    }
                ],
            }
        ]
        bars = CalendarService._timeline_to_bars(timelines, 2026)
        assert len(bars) == 1
        assert bars[0].color == "#9E9E9E"
