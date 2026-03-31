from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SensorReadingCreate(BaseModel):
    value: float
    sensor_type: str = Field(min_length=1, max_length=50)
    unit: str | None = Field(default=None, max_length=20)
    source: str = Field(default="manual", max_length=50)
    quality_score: float | None = Field(default=None, ge=0.0, le=1.0)
    raw_value: float | None = None
    metadata: dict[str, Any] | None = None


class SensorReadingBatchCreate(BaseModel):
    readings: list[SensorReadingCreate] = Field(..., min_length=1, max_length=1000)


class SensorReadingResponse(BaseModel):
    time: datetime
    sensor_key: str
    sensor_type: str
    value: float
    unit: str | None = None
    source: str
    quality_score: float | None = None
    raw_value: float | None = None
    metadata: dict[str, Any] | None = None


class AggregatedReadingResponse(BaseModel):
    bucket: datetime
    sensor_key: str
    sensor_type: str
    avg_value: float
    min_value: float
    max_value: float
    sample_count: int


class ReadingsListResponse(BaseModel):
    items: list[SensorReadingResponse] | list[AggregatedReadingResponse]
    total: int
    resolution: str


class BatchInsertResponse(BaseModel):
    inserted: int


class TimeseriesStatusResponse(BaseModel):
    available: bool
