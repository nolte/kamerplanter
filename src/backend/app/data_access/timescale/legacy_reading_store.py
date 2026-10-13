"""TimescaleDB side of the pre-#2076 reading cleanup (#2077). Operator-run only."""

from __future__ import annotations

from datetime import datetime, timedelta

import structlog
from psycopg import sql
from psycopg_pool import ConnectionPool

from app.data_access.timescale.observation_repository import AGGREGATE_VIEWS, resolve_aggregate_tables
from app.domain.interfaces.legacy_reading_store import ILegacyReadingStore, LegacySeriesCounts

logger = structlog.get_logger(__name__)

#: What the Home Assistant poll stamped before #2076. Bound as a parameter, never spliced.
LEGACY_TENANT_KEY = ""

#: A raw delete covers this much time per transaction, so one sensor's history is never one huge delete.
WINDOW = timedelta(days=7)

_RAW_COUNTS_SQL = """
SELECT sensor_key, COUNT(*) FROM sensor_readings
WHERE tenant_key = %(tenant_key)s
GROUP BY sensor_key
"""

_RAW_SPAN_SQL = """
SELECT MIN(time), MAX(time) FROM sensor_readings
WHERE tenant_key = %(tenant_key)s AND sensor_key = %(sensor_key)s
"""

_RAW_DELETE_SQL = """
DELETE FROM sensor_readings
WHERE tenant_key = %(tenant_key)s AND sensor_key = %(sensor_key)s
  AND time >= %(start)s AND time < %(end)s
"""


class TimescaleLegacyReadingStore(ILegacyReadingStore):
    def __init__(self, pool: ConnectionPool) -> None:
        self._pool = pool

    def is_available(self) -> bool:
        try:
            with self._pool.connection() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception:  # noqa: BLE001 — any failure means "do not touch anything"
            return False

    def legacy_series(self) -> dict[str, LegacySeriesCounts]:
        params = {"tenant_key": LEGACY_TENANT_KEY}
        series: dict[str, dict[str, int]] = {}
        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.execute(_RAW_COUNTS_SQL, params)
            for key, count in cur.fetchall():
                series.setdefault(key, {})["raw"] = count
            tables = resolve_aggregate_tables(cur)
            for view, field_name in zip(AGGREGATE_VIEWS, ("hourly", "daily"), strict=True):
                schema, table = tables[view]
                query = sql.SQL(
                    "SELECT sensor_key, COUNT(*) FROM {} WHERE tenant_key = %(tenant_key)s GROUP BY sensor_key"
                )
                cur.execute(query.format(sql.Identifier(schema, table)), params)
                for key, count in cur.fetchall():
                    series.setdefault(key, {})[field_name] = count
        return {key: LegacySeriesCounts(**values) for key, values in series.items()}

    def purge_legacy_series(self, sensor_key: str) -> LegacySeriesCounts:
        if not sensor_key:
            msg = "purge_legacy_series needs a sensor key"
            raise ValueError(msg)
        raw = self._purge_raw(sensor_key)
        hourly = daily = 0
        with self._pool.connection() as conn, conn.cursor() as cur:
            tables = resolve_aggregate_tables(cur)
            counts = []
            for view in AGGREGATE_VIEWS:
                schema, table = tables[view]
                query = sql.SQL("DELETE FROM {} WHERE tenant_key = %(tenant_key)s AND sensor_key = %(sensor_key)s")
                cur.execute(
                    query.format(sql.Identifier(schema, table)),
                    {"tenant_key": LEGACY_TENANT_KEY, "sensor_key": sensor_key},
                )
                counts.append(cur.rowcount)
            conn.commit()
            hourly, daily = counts
        return LegacySeriesCounts(raw=raw, hourly=hourly, daily=daily)

    def _purge_raw(self, sensor_key: str) -> int:
        """Delete the raw rows window by window, one commit each; an interrupted run leaves a re-runnable remainder."""
        base = {"tenant_key": LEGACY_TENANT_KEY, "sensor_key": sensor_key}
        with self._pool.connection() as conn:
            first, last = conn.execute(_RAW_SPAN_SQL, base).fetchone() or (None, None)
        if first is None or last is None:
            return 0
        total = 0
        start: datetime = first
        while start <= last:
            end = start + WINDOW
            with self._pool.connection() as conn, conn.cursor() as cur:
                cur.execute(_RAW_DELETE_SQL, {**base, "start": start, "end": end})
                total += cur.rowcount
                conn.commit()
            start = end
        return total
