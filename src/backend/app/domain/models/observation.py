from datetime import datetime
from typing import Any, Literal

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


class ArchivedReading(BaseModel):
    """One row of a tenant archive's ``timeseries/readings.csv`` (REQ-056 §8.3, #2138).

    ``series`` names where the row comes from: ``raw`` (``sensor_readings``, 90 days), ``hourly``
    (``sensor_hourly``, 2 years) or ``daily`` (``sensor_daily``, 5 years) — what NFR-011 still keeps.
    ``time`` is the raw reading's instant or the aggregate's bucket start. Raw rows carry ``value``
    and the provenance columns, aggregate rows ``avg_value`` … ``sample_count``; the other columns are
    ``None``. The tenant is the archive's, not a column.
    """

    series: Literal["raw", "hourly", "daily"]
    time: datetime
    sensor_key: str
    sensor_type: str
    value: float | None = None
    unit: str | None = None
    source: str | None = None
    quality_score: float | None = None
    raw_value: float | None = None
    metadata: dict[str, Any] | None = None
    avg_value: float | None = None
    min_value: float | None = None
    max_value: float | None = None
    sample_count: int | None = None
