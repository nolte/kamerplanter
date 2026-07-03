"""Unit tests for the datetime normalization helpers."""

from datetime import UTC, datetime, timedelta, timezone

from app.common.datetimes import ensure_aware_utc, now_utc


class TestNowUtc:
    def test_returns_aware_utc(self):
        """now_utc() returns a timezone-aware datetime in UTC."""
        value = now_utc()
        assert value.tzinfo is not None
        assert value.utcoffset() == timedelta(0)


class TestEnsureAwareUtc:
    def test_none_returns_none(self):
        """None passes through unchanged."""
        assert ensure_aware_utc(None) is None

    def test_naive_datetime_interpreted_as_utc(self):
        """A naive datetime (legacy data) is interpreted as UTC."""
        naive = datetime(2026, 7, 3, 12, 0, 0)
        result = ensure_aware_utc(naive)
        assert result == datetime(2026, 7, 3, 12, 0, 0, tzinfo=UTC)
        assert result.tzinfo == UTC

    def test_aware_non_utc_converted_to_utc(self):
        """An aware non-UTC datetime is converted to UTC (same instant)."""
        berlin = timezone(timedelta(hours=2))
        aware = datetime(2026, 7, 3, 14, 0, 0, tzinfo=berlin)
        result = ensure_aware_utc(aware)
        assert result == datetime(2026, 7, 3, 12, 0, 0, tzinfo=UTC)
        assert result.utcoffset() == timedelta(0)

    def test_aware_utc_unchanged(self):
        """An already-UTC datetime is returned equivalently in UTC."""
        aware = datetime(2026, 7, 3, 12, 0, 0, tzinfo=UTC)
        result = ensure_aware_utc(aware)
        assert result == aware
        assert result.utcoffset() == timedelta(0)

    def test_iso_string_with_offset(self):
        """An ISO string carrying an offset is parsed and normalized to UTC."""
        result = ensure_aware_utc("2026-07-03T14:00:00+02:00")
        assert result == datetime(2026, 7, 3, 12, 0, 0, tzinfo=UTC)

    def test_iso_string_without_offset_interpreted_as_utc(self):
        """An ISO string without offset (naive) is interpreted as UTC."""
        result = ensure_aware_utc("2026-07-03T12:00:00")
        assert result == datetime(2026, 7, 3, 12, 0, 0, tzinfo=UTC)
        assert result.tzinfo == UTC
