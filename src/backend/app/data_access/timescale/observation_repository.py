from datetime import datetime

import structlog
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.domain.interfaces.observation_repository import IObservationRepository
from app.domain.models.observation import AggregatedReading, SensorReading

logger = structlog.get_logger(__name__)

_INSERT_SQL = """
INSERT INTO sensor_readings
    (time, tenant_key, sensor_key, sensor_type, value, unit, source,
     quality_score, raw_value, metadata)
VALUES
    (%(time)s, %(tenant_key)s, %(sensor_key)s, %(sensor_type)s, %(value)s,
     %(unit)s, %(source)s, %(quality_score)s, %(raw_value)s, %(metadata)s)
"""

_QUERY_RAW_SQL = """
SELECT time, tenant_key, sensor_key, sensor_type, value, unit,
       source, quality_score, raw_value, metadata
FROM sensor_readings
WHERE sensor_key = %(sensor_key)s
  AND tenant_key = %(tenant_key)s
  AND time >= %(start)s
  AND time < %(end)s
ORDER BY time DESC
LIMIT %(limit)s
"""

_QUERY_HOURLY_SQL = """
SELECT bucket, tenant_key, sensor_key, sensor_type,
       avg_value, min_value, max_value, sample_count
FROM sensor_hourly
WHERE sensor_key = %(sensor_key)s
  AND tenant_key = %(tenant_key)s
  AND bucket >= %(start)s
  AND bucket < %(end)s
ORDER BY bucket DESC
"""

_QUERY_DAILY_SQL = """
SELECT bucket, tenant_key, sensor_key, sensor_type,
       avg_value, min_value, max_value, sample_count
FROM sensor_daily
WHERE sensor_key = %(sensor_key)s
  AND tenant_key = %(tenant_key)s
  AND bucket >= %(start)s
  AND bucket < %(end)s
ORDER BY bucket DESC
"""

_LATEST_SQL = """
SELECT time, tenant_key, sensor_key, sensor_type, value, unit,
       source, quality_score, raw_value, metadata
FROM sensor_readings
WHERE sensor_key = %(sensor_key)s
  AND tenant_key = %(tenant_key)s
ORDER BY time DESC
LIMIT 1
"""

_DELETE_BY_SENSOR_SQL = """
DELETE FROM sensor_readings
WHERE sensor_key = %(sensor_key)s
  AND tenant_key = %(tenant_key)s
"""


def _prepare_params(reading: SensorReading) -> dict:
    params = reading.model_dump()
    if params.get("metadata") is not None:
        import psycopg.types.json

        params["metadata"] = psycopg.types.json.Jsonb(params["metadata"])
    return params


class TimescaleObservationRepository(IObservationRepository):
    def __init__(self, pool: ConnectionPool) -> None:
        self._pool = pool

    def insert(self, reading: SensorReading) -> None:
        params = _prepare_params(reading)
        with self._pool.connection() as conn:
            conn.execute(_INSERT_SQL, params)
            conn.commit()

    def insert_batch(self, readings: list[SensorReading]) -> int:
        if not readings:
            return 0

        params_list = [_prepare_params(r) for r in readings]
        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.executemany(_INSERT_SQL, params_list)
            conn.commit()

        return len(readings)

    def query_raw(
        self,
        sensor_key: str,
        start: datetime,
        end: datetime,
        tenant_key: str,
        limit: int = 1000,
    ) -> list[SensorReading]:
        params = {
            "sensor_key": sensor_key,
            "tenant_key": tenant_key,
            "start": start,
            "end": end,
            "limit": limit,
        }
        with self._pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            rows = cur.execute(_QUERY_RAW_SQL, params).fetchall()
        return [SensorReading(**row) for row in rows]

    def query_hourly(
        self,
        sensor_key: str,
        start: datetime,
        end: datetime,
        tenant_key: str,
    ) -> list[AggregatedReading]:
        params = {
            "sensor_key": sensor_key,
            "tenant_key": tenant_key,
            "start": start,
            "end": end,
        }
        with self._pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            rows = cur.execute(_QUERY_HOURLY_SQL, params).fetchall()
        return [AggregatedReading(**row) for row in rows]

    def query_daily(
        self,
        sensor_key: str,
        start: datetime,
        end: datetime,
        tenant_key: str,
    ) -> list[AggregatedReading]:
        params = {
            "sensor_key": sensor_key,
            "tenant_key": tenant_key,
            "start": start,
            "end": end,
        }
        with self._pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            rows = cur.execute(_QUERY_DAILY_SQL, params).fetchall()
        return [AggregatedReading(**row) for row in rows]

    def get_latest(
        self,
        sensor_key: str,
        tenant_key: str,
    ) -> SensorReading | None:
        params = {"sensor_key": sensor_key, "tenant_key": tenant_key}
        with self._pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            row = cur.execute(_LATEST_SQL, params).fetchone()
        if row is None:
            return None
        return SensorReading(**row)

    def delete_by_sensor(
        self,
        sensor_key: str,
        tenant_key: str,
    ) -> int:
        params = {"sensor_key": sensor_key, "tenant_key": tenant_key}
        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.execute(_DELETE_BY_SENSOR_SQL, params)
            count = cur.rowcount
            conn.commit()
        return count

    def is_available(self) -> bool:
        try:
            with self._pool.connection() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception:
            return False
