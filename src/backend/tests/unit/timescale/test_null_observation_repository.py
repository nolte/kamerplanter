from datetime import UTC, datetime

from app.data_access.timescale.null_observation_repository import NullObservationRepository
from app.domain.models.observation import SensorReading


class TestNullObservationRepository:
    def setup_method(self):
        self.repo = NullObservationRepository()

    def _make_reading(self, **kwargs) -> SensorReading:
        defaults = {
            "time": datetime.now(tz=UTC),
            "tenant_key": "t1",
            "sensor_key": "s1",
            "sensor_type": "temperature",
            "value": 22.5,
        }
        defaults.update(kwargs)
        return SensorReading(**defaults)

    def test_insert_is_noop(self):
        self.repo.insert(self._make_reading())

    def test_insert_batch_returns_zero(self):
        result = self.repo.insert_batch([self._make_reading(), self._make_reading()])
        assert result == 0

    def test_query_raw_returns_empty(self):
        now = datetime.now(tz=UTC)
        result = self.repo.query_raw("s1", now, now, "t1")
        assert result == []

    def test_query_hourly_returns_empty(self):
        now = datetime.now(tz=UTC)
        result = self.repo.query_hourly("s1", now, now, "t1")
        assert result == []

    def test_query_daily_returns_empty(self):
        now = datetime.now(tz=UTC)
        result = self.repo.query_daily("s1", now, now, "t1")
        assert result == []

    def test_get_latest_returns_none(self):
        result = self.repo.get_latest("s1", "t1")
        assert result is None

    def test_delete_by_sensor_returns_zero(self):
        result = self.repo.delete_by_sensor("s1", "t1")
        assert result == 0

    def test_is_available_returns_false(self):
        assert self.repo.is_available() is False
