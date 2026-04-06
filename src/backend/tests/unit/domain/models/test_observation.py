from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.domain.models.observation import AggregatedReading, SensorReading


class TestSensorReading:
    def test_valid_reading(self):
        reading = SensorReading(
            time=datetime.now(tz=UTC),
            tenant_key="t1",
            sensor_key="s1",
            sensor_type="temperature",
            value=22.5,
            unit="°C",
            source="ha_auto",
        )
        assert reading.value == 22.5
        assert reading.source == "ha_auto"

    def test_default_source(self):
        reading = SensorReading(
            time=datetime.now(tz=UTC),
            tenant_key="t1",
            sensor_key="s1",
            sensor_type="ph",
            value=6.2,
        )
        assert reading.source == "manual"

    def test_quality_score_range(self):
        reading = SensorReading(
            time=datetime.now(tz=UTC),
            tenant_key="t1",
            sensor_key="s1",
            sensor_type="ec",
            value=1.2,
            quality_score=0.95,
        )
        assert reading.quality_score == 0.95

    def test_quality_score_out_of_range(self):
        with pytest.raises(ValidationError):
            SensorReading(
                time=datetime.now(tz=UTC),
                tenant_key="t1",
                sensor_key="s1",
                sensor_type="ec",
                value=1.2,
                quality_score=1.5,
            )

    def test_metadata_optional(self):
        reading = SensorReading(
            time=datetime.now(tz=UTC),
            tenant_key="t1",
            sensor_key="s1",
            sensor_type="temperature",
            value=20.0,
        )
        assert reading.metadata is None

    def test_metadata_dict(self):
        reading = SensorReading(
            time=datetime.now(tz=UTC),
            tenant_key="t1",
            sensor_key="s1",
            sensor_type="temperature",
            value=20.0,
            metadata={"location": "indoor", "calibrated": True},
        )
        assert reading.metadata["location"] == "indoor"


class TestAggregatedReading:
    def test_valid_aggregated(self):
        agg = AggregatedReading(
            bucket=datetime.now(tz=UTC),
            tenant_key="t1",
            sensor_key="s1",
            sensor_type="temperature",
            avg_value=22.0,
            min_value=20.0,
            max_value=24.0,
            sample_count=60,
        )
        assert agg.avg_value == 22.0
        assert agg.sample_count == 60
