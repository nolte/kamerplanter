from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.common.exceptions import NotFoundError
from app.data_access.timescale.null_observation_repository import NullObservationRepository
from app.domain.models.observation import SensorReading
from app.domain.models.sensor import Sensor
from app.domain.services.observation_service import ObservationService


@pytest.fixture
def mock_obs_repo():
    return MagicMock()


@pytest.fixture
def mock_sensor_repo():
    return MagicMock()


@pytest.fixture
def service(mock_obs_repo, mock_sensor_repo):
    return ObservationService(mock_obs_repo, mock_sensor_repo)


def _make_reading(**kwargs) -> SensorReading:
    defaults = {
        "time": datetime(2026, 3, 28, 12, 0, 0, tzinfo=UTC),
        "tenant_key": "t1",
        "sensor_key": "s1",
        "sensor_type": "temperature",
        "value": 22.5,
    }
    defaults.update(kwargs)
    return SensorReading(**defaults)


def _make_sensor(**kwargs) -> Sensor:
    defaults = {
        "_key": "s1",
        "name": "Test Sensor",
        "metric_type": "temperature",
    }
    defaults.update(kwargs)
    return Sensor(**defaults)


class TestRecordReading:
    def test_record_reading_delegates_to_repo(self, service, mock_obs_repo, mock_sensor_repo):
        mock_sensor_repo.get.return_value = _make_sensor()
        reading = _make_reading()
        service.record_reading(reading)
        mock_obs_repo.insert.assert_called_once_with(reading)

    def test_record_reading_raises_if_sensor_not_found(self, service, mock_sensor_repo):
        mock_sensor_repo.get.return_value = None
        with pytest.raises(NotFoundError):
            service.record_reading(_make_reading())

    def test_record_batch_delegates(self, service, mock_obs_repo):
        readings = [_make_reading(), _make_reading(value=23.0)]
        mock_obs_repo.insert_batch.return_value = 2
        result = service.record_readings_batch(readings)
        assert result == 2


class TestGetReadings:
    def test_get_raw_readings(self, service, mock_obs_repo):
        now = datetime.now(tz=UTC)
        mock_obs_repo.query_raw.return_value = [_make_reading()]
        result = service.get_readings("s1", now, now, "t1", "raw")
        assert len(result) == 1
        mock_obs_repo.query_raw.assert_called_once()

    def test_get_hourly_readings(self, service, mock_obs_repo):
        now = datetime.now(tz=UTC)
        mock_obs_repo.query_hourly.return_value = []
        result = service.get_readings("s1", now, now, "t1", "hourly")
        assert result == []
        mock_obs_repo.query_hourly.assert_called_once()

    def test_get_daily_readings(self, service, mock_obs_repo):
        now = datetime.now(tz=UTC)
        mock_obs_repo.query_daily.return_value = []
        result = service.get_readings("s1", now, now, "t1", "daily")
        assert result == []
        mock_obs_repo.query_daily.assert_called_once()


class TestGetLatest:
    def test_returns_reading(self, service, mock_obs_repo):
        reading = _make_reading()
        mock_obs_repo.get_latest.return_value = reading
        result = service.get_latest_reading("s1", "t1")
        assert result == reading

    def test_returns_none(self, service, mock_obs_repo):
        mock_obs_repo.get_latest.return_value = None
        result = service.get_latest_reading("s1", "t1")
        assert result is None


class TestAvailability:
    def test_delegates_to_repo(self, service, mock_obs_repo):
        mock_obs_repo.is_available.return_value = True
        assert service.is_available() is True


class TestWithNullRepo:
    def test_service_works_with_null_repo(self, mock_sensor_repo):
        null_repo = NullObservationRepository()
        svc = ObservationService(null_repo, mock_sensor_repo)
        assert svc.is_available() is False

    def test_get_readings_returns_empty(self, mock_sensor_repo):
        null_repo = NullObservationRepository()
        svc = ObservationService(null_repo, mock_sensor_repo)
        now = datetime.now(tz=UTC)
        assert svc.get_readings("s1", now, now, "t1") == []

    def test_get_latest_returns_none(self, mock_sensor_repo):
        null_repo = NullObservationRepository()
        svc = ObservationService(null_repo, mock_sensor_repo)
        assert svc.get_latest_reading("s1", "t1") is None
