from datetime import datetime

import psycopg
import structlog
from psycopg import sql
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.common.log_privacy import log_tenant
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

_DELETE_BY_TENANT_SQL = """
DELETE FROM sensor_readings
WHERE tenant_key = %(tenant_key)s
"""

#: The continuous aggregates (migration 002) that hold a derived copy of every
#: raw reading, and the only two names resolved to materialisation tables below.
AGGREGATE_VIEWS = ("sensor_hourly", "sensor_daily")

#: Where each aggregate keeps its buckets. A continuous aggregate is a read-only
#: view: ``DELETE FROM sensor_hourly`` is refused, the rows live in an internal
#: materialisation hypertable that TimescaleDB names itself.
_MATERIALIZATION_SQL = """
SELECT view_name, materialization_hypertable_schema, materialization_hypertable_name
FROM timescaledb_information.continuous_aggregates
WHERE view_name = ANY(%(views)s)
  AND view_schema = current_schema()
"""


def resolve_aggregate_tables(cur: psycopg.Cursor) -> dict[str, tuple[str, str]]:
    """The materialisation table of each continuous aggregate, ``{view: (schema, table)}``.

    Raises when one is missing: skipping would report an erasure that left the
    aggregated copy of the data behind (the failure #1793 is about).
    """
    cur.execute(_MATERIALIZATION_SQL, {"views": list(AGGREGATE_VIEWS)})
    found = {row[0]: (row[1], row[2]) for row in cur.fetchall()}  # one row per view: the schema is fixed above
    missing = set(AGGREGATE_VIEWS) - found.keys()
    if missing:
        msg = f"continuous aggregate(s) not found, cannot erase their buckets: {sorted(missing)}"
        raise RuntimeError(msg)
    return found


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

    def _purge_aggregates(self, cur: psycopg.Cursor, tenant_key: str, sensor_key: str | None = None) -> int:
        """Delete the tenant's (or one sensor's) buckets from the continuous aggregates (#1793).

        Deleting raw rows does not reach them: a bucket is only recomputed when a
        refresh covers its range, and the policies cover the last 3 hours /
        3 days. Buckets older than the raw retention (90 days) cannot be
        recomputed at all — the raw rows they were built from are gone — which is
        also why *refreshing* the deleted window is not the fix: it would leave
        those buckets behind, and a wider refresh would wipe other tenants'
        history for the same reason. The buckets are therefore deleted
        explicitly from the materialisation tables, by the grouping columns
        (``tenant_key``, ``sensor_key``) the aggregates carry.

        Runs on the caller's cursor, so the raw delete and this one commit or
        roll back together. A policy refresh that is already running on a
        snapshot from before the raw delete can still re-materialise a bucket of
        the hot window (last 3 hours / 3 days) after this commit; the raw delete
        has logged an invalidation for that range, so the next policy run removes
        it again, and the erasure record's retry repeats this idempotent delete.
        A pending invalidation of the deleted raw range is
        harmless: the next refresh recomputes from raw rows that no longer exist
        and materialises nothing for the deleted tenant.
        """
        found = resolve_aggregate_tables(cur)
        total = 0
        for view in AGGREGATE_VIEWS:
            schema, table = found[view]
            query = sql.SQL("DELETE FROM {} WHERE tenant_key = %(tenant_key)s").format(sql.Identifier(schema, table))
            params = {"tenant_key": tenant_key}
            if sensor_key is not None:
                query += sql.SQL(" AND sensor_key = %(sensor_key)s")
                params["sensor_key"] = sensor_key
            cur.execute(query, params)
            total += cur.rowcount
        return total

    def delete_by_sensor(
        self,
        sensor_key: str,
        tenant_key: str,
    ) -> int:
        """Delete one sensor's raw readings **and its hourly/daily buckets** (#1793).

        Both keys are required: ``_purge_aggregates`` reads a missing sensor key
        as "every sensor of the tenant", which must never be reachable from here.
        """
        if not sensor_key or not tenant_key:
            msg = "delete_by_sensor needs a sensor key and a tenant key"
            raise ValueError(msg)
        params = {"sensor_key": sensor_key, "tenant_key": tenant_key}
        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.execute(_DELETE_BY_SENSOR_SQL, params)
            count = cur.rowcount
            aggregates = self._purge_aggregates(cur, tenant_key, sensor_key)
            conn.commit()
        logger.info("sensor_aggregates_deleted", sensor_key=sensor_key, buckets=aggregates)
        return count

    def delete_by_tenant(self, tenant_key: str) -> int:
        """#1769 — every raw reading of a deleted tenant, and (#1793) its aggregate buckets.

        An empty key would match nothing here (``tenant_key`` is ``NOT NULL`` and
        stamped from the tenant context), but the caller validates it anyway.
        Returns the raw rows removed; the aggregate buckets are removed in the
        same transaction whether or not any raw row was left (a tenant whose raw
        data all aged out still has up to 5 years of daily buckets).
        """
        if not tenant_key:
            msg = "delete_by_tenant needs a tenant key"
            raise ValueError(msg)
        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.execute(_DELETE_BY_TENANT_SQL, {"tenant_key": tenant_key})
            count = cur.rowcount
            aggregates = self._purge_aggregates(cur, tenant_key)
            conn.commit()
        logger.info("tenant_aggregates_deleted", tenant=log_tenant(tenant_key), buckets=aggregates)
        return count

    def is_available(self) -> bool:
        try:
            with self._pool.connection() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception:
            return False
