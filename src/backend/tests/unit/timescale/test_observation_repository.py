from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.data_access.timescale.observation_repository import TimescaleObservationRepository
from app.domain.models.observation import SensorReading


@pytest.fixture
def mock_pool():
    return MagicMock()


@pytest.fixture
def repo(mock_pool):
    return TimescaleObservationRepository(mock_pool)


def _make_reading(**kwargs) -> SensorReading:
    defaults = {
        "time": datetime(2026, 3, 28, 12, 0, 0, tzinfo=UTC),
        "tenant_key": "t1",
        "sensor_key": "s1",
        "sensor_type": "temperature",
        "value": 22.5,
        "unit": "°C",
        "source": "ha_auto",
    }
    defaults.update(kwargs)
    return SensorReading(**defaults)


class TestTimescaleInsert:
    def test_insert_executes_sql(self, repo, mock_pool):
        reading = _make_reading()
        mock_conn = MagicMock()
        mock_pool.connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_pool.connection.return_value.__exit__ = MagicMock(return_value=False)

        repo.insert(reading)

        mock_conn.execute.assert_called_once()
        mock_conn.commit.assert_called_once()

    def test_insert_batch_empty(self, repo):
        assert repo.insert_batch([]) == 0


class TestTimescaleQuery:
    def test_query_raw_returns_readings(self, repo, mock_pool):
        now = datetime.now(tz=UTC)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            {
                "time": now,
                "tenant_key": "t1",
                "sensor_key": "s1",
                "sensor_type": "temperature",
                "value": 22.5,
                "unit": "°C",
                "source": "ha_auto",
                "quality_score": 1.0,
                "raw_value": None,
                "metadata": None,
            }
        ]
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_pool.connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_pool.connection.return_value.__exit__ = MagicMock(return_value=False)

        result = repo.query_raw("s1", now, now, "t1")
        assert len(result) == 1
        assert result[0].value == 22.5

    def test_get_latest_returns_none_when_empty(self, repo, mock_pool):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_pool.connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_pool.connection.return_value.__exit__ = MagicMock(return_value=False)

        result = repo.get_latest("s1", "t1")
        assert result is None


class TestTimescaleAvailability:
    def test_is_available_true(self, repo, mock_pool):
        mock_conn = MagicMock()
        mock_pool.connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_pool.connection.return_value.__exit__ = MagicMock(return_value=False)

        assert repo.is_available() is True

    def test_is_available_false_on_error(self, repo, mock_pool):
        mock_pool.connection.return_value.__enter__ = MagicMock(side_effect=Exception("connection refused"))

        assert repo.is_available() is False
