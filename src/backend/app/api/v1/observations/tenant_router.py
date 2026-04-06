from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query

from app.api.v1.observations.schemas import (
    AggregatedReadingResponse,
    BatchInsertResponse,
    ReadingsListResponse,
    SensorReadingBatchCreate,
    SensorReadingCreate,
    SensorReadingResponse,
)
from app.common.auth import get_current_tenant
from app.common.dependencies import get_observation_service
from app.domain.models.observation import AggregatedReading, SensorReading
from app.domain.models.tenant_context import TenantContext
from app.domain.services.observation_service import ObservationService

router = APIRouter(prefix="/observations", tags=["observations"])


@router.post(
    "/sensors/{sensor_key}/readings",
    response_model=SensorReadingResponse,
    status_code=201,
)
def record_sensor_reading(
    sensor_key: str,
    body: SensorReadingCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: ObservationService = Depends(get_observation_service),
) -> SensorReadingResponse:
    reading = SensorReading(
        time=datetime.now(tz=UTC),
        tenant_key=ctx.tenant_key,
        sensor_key=sensor_key,
        sensor_type=body.sensor_type,
        value=body.value,
        unit=body.unit,
        source=body.source,
        quality_score=body.quality_score,
        raw_value=body.raw_value,
        metadata=body.metadata,
    )
    service.record_reading(reading)
    return SensorReadingResponse(
        time=reading.time,
        sensor_key=reading.sensor_key,
        sensor_type=reading.sensor_type,
        value=reading.value,
        unit=reading.unit,
        source=reading.source,
        quality_score=reading.quality_score,
        raw_value=reading.raw_value,
        metadata=reading.metadata,
    )


@router.post(
    "/sensors/{sensor_key}/readings/batch",
    response_model=BatchInsertResponse,
    status_code=201,
)
def record_sensor_readings_batch(
    sensor_key: str,
    body: SensorReadingBatchCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: ObservationService = Depends(get_observation_service),
) -> BatchInsertResponse:
    now = datetime.now(tz=UTC)
    readings = [
        SensorReading(
            time=now,
            tenant_key=ctx.tenant_key,
            sensor_key=sensor_key,
            sensor_type=r.sensor_type,
            value=r.value,
            unit=r.unit,
            source=r.source,
            quality_score=r.quality_score,
            raw_value=r.raw_value,
            metadata=r.metadata,
        )
        for r in body.readings
    ]
    inserted = service.record_readings_batch(readings)
    return BatchInsertResponse(inserted=inserted)


@router.get(
    "/sensors/{sensor_key}/readings",
    response_model=ReadingsListResponse,
)
def get_sensor_readings(
    sensor_key: str,
    start: datetime = Query(...),
    end: datetime = Query(...),
    resolution: str = Query("raw", pattern="^(raw|hourly|daily)$"),
    ctx: TenantContext = Depends(get_current_tenant),
    service: ObservationService = Depends(get_observation_service),
) -> ReadingsListResponse:
    raw_items = service.get_readings(sensor_key, start, end, ctx.tenant_key, resolution)
    if raw_items and isinstance(raw_items[0], AggregatedReading):
        items: list[SensorReadingResponse] | list[AggregatedReadingResponse] = [
            AggregatedReadingResponse(
                bucket=r.bucket,
                sensor_key=r.sensor_key,
                sensor_type=r.sensor_type,
                avg_value=r.avg_value,
                min_value=r.min_value,
                max_value=r.max_value,
                sample_count=r.sample_count,
            )
            for r in raw_items  # type: ignore[union-attr]
        ]
    else:
        items = [
            SensorReadingResponse(
                time=r.time,
                sensor_key=r.sensor_key,
                sensor_type=r.sensor_type,
                value=r.value,
                unit=r.unit,
                source=r.source,
                quality_score=r.quality_score,
                raw_value=r.raw_value,
                metadata=r.metadata,
            )
            for r in raw_items  # type: ignore[union-attr]
        ]
    return ReadingsListResponse(items=items, total=len(items), resolution=resolution)


@router.get(
    "/sensors/{sensor_key}/readings/latest",
    response_model=SensorReadingResponse | None,
)
def get_latest_sensor_reading(
    sensor_key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: ObservationService = Depends(get_observation_service),
) -> SensorReadingResponse | None:
    reading = service.get_latest_reading(sensor_key, ctx.tenant_key)
    if reading is None:
        return None
    return SensorReadingResponse(
        time=reading.time,
        sensor_key=reading.sensor_key,
        sensor_type=reading.sensor_type,
        value=reading.value,
        unit=reading.unit,
        source=reading.source,
        quality_score=reading.quality_score,
        raw_value=reading.raw_value,
        metadata=reading.metadata,
    )
