from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SensorReading(BaseModel):
    """A single time-series sensor reading stored in TimescaleDB."""

    time: datetime
    tenant_key: str
    sensor_key: str
    sensor_type: str
    value: float
    unit: str | None = None
    source: str = "manual"
    quality_score: float | None = Field(default=None, ge=0.0, le=1.0)
    raw_value: float | None = None
    metadata: dict[str, Any] | None = None


class AggregatedReading(BaseModel):
    """Aggregated sensor reading from continuous aggregates."""

    bucket: datetime
    tenant_key: str
    sensor_key: str
    sensor_type: str
    avg_value: float
    min_value: float
    max_value: float
    sample_count: int
