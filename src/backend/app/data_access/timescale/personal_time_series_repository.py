"""TimescaleDB read side of the Art. 15 manifest: the personal garden's sensor readings (#2165)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from psycopg import sql
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.data_access.timescale.legacy_reading_store import LEGACY_TENANT_KEY
from app.data_access.timescale.observation_repository import AGGREGATE_VIEWS
from app.domain.interfaces.personal_data_repository import IPersonalTimeSeriesRepository
from app.domain.models.privacy import DataSourceDefinition, TimeSeriesSlice

#: The raw table (migration 001).
RAW_TABLE = "sensor_readings"
_RAW_COLUMNS = frozenset(
    {
        "time",
        "tenant_key",
        "sensor_key",
        "sensor_type",
        "value",
        "unit",
        "source",
        "quality_score",
        "raw_value",
        "metadata",
    }
)
_AGGREGATE_COLUMNS = frozenset(
    {"bucket", "tenant_key", "sensor_key", "sensor_type", "avg_value", "min_value", "max_value", "sample_count"}
)

#: The only tables and columns a manifest source may name. Every identifier of the query
#: below is checked against this map and composed with ``sql.Identifier``; nothing a
#: caller passes is spliced into the text.
TABLE_COLUMNS: dict[str, frozenset[str]] = {
    RAW_TABLE: _RAW_COLUMNS,
    **dict.fromkeys(AGGREGATE_VIEWS, _AGGREGATE_COLUMNS),
}

#: The longest a section query may run. An export runs in a Celery worker; a query that
#: hangs would hold the request in ``processing`` until the task's own limit. Raising here
#: ends the attempt, and the export task's retry policy applies (#1666).
STATEMENT_TIMEOUT = "120s"

#: Alias of the count column; not a table column, so it cannot clash.
_TOTAL = "export_total_rows"


class TimescalePersonalTimeSeriesRepository(IPersonalTimeSeriesRepository):
    """Reads a time-series manifest source for the subject's personal tenants."""

    def __init__(self, pool: ConnectionPool) -> None:
        self._pool = pool

    def collect_personal_tenant_series(
        self,
        source: DataSourceDefinition,
        tenant_keys: Sequence[str],
        series_keys: Sequence[str],
        *,
        max_rows: int,
    ) -> TimeSeriesSlice:
        scope = source.time_series
        if scope is None:
            msg = f"Manifest source '{source.collection}' is not a time-series source."
            raise ValueError(msg)
        columns = TABLE_COLUMNS.get(source.collection)
        if columns is None:
            msg = f"Manifest source '{source.collection}' names no known time-series table."
            raise ValueError(msg)
        unknown = sorted(set(source.fields) - columns)
        if unknown:
            msg = f"Manifest source '{source.collection}' declares columns the table does not have: {unknown}"
            raise ValueError(msg)
        if max_rows < 1:
            msg = "max_rows must be positive"
            raise ValueError(msg)
        owned = [key for key in tenant_keys if key]
        if not owned:
            # No personal tenant: nothing is the subject's here, and the legacy match
            # below must never run on its own (it would be unbounded by a tenant).
            return TimeSeriesSlice()

        # The subject's series: the owned tenants, or the empty pre-#2076 tenant key
        # together with a sensor of the garden. Shared by the page and the count.
        match = sql.SQL(
            "FROM {table} WHERE tenant_key = ANY(%(tenant_keys)s) "
            "OR (tenant_key = %(legacy)s AND sensor_key = ANY(%(series_keys)s))"
        ).format(table=sql.Identifier(source.collection))
        # No window function here: ``COUNT(*) OVER ()`` made the server read every match
        # before ``LIMIT`` could stop it (S-1, measured 1.3 M rows read for a 100 000 page).
        # Plain ``ORDER BY time DESC LIMIT`` lets the ordered chunk scan stop at the page.
        page = sql.SQL("SELECT {fields} {match} ORDER BY {time} DESC LIMIT %(limit)s").format(
            fields=sql.SQL(", ").join(sql.Identifier(field) for field in source.fields),
            match=match,
            time=sql.Identifier(scope.time_column),
        )
        count = sql.SQL("SELECT count(*) AS {total} {match}").format(total=sql.Identifier(_TOTAL), match=match)
        params: dict[str, Any] = {
            "tenant_keys": owned,
            "legacy": LEGACY_TENANT_KEY,
            "series_keys": [key for key in series_keys if key],
            "limit": max_rows,
        }
        with self._pool.connection() as conn, conn.transaction(), conn.cursor(row_factory=dict_row) as cur:
            # One snapshot for the page and the count: under REPEATABLE READ a reading that
            # arrives between the two statements is in neither, so ``total`` and the
            # delivered rows cannot disagree. Must be the transaction's first statement.
            cur.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            # ``is_local``: the timeout ends with this transaction and never leaks into the
            # pooled connection's next user.
            cur.execute("SELECT set_config('statement_timeout', %s, true)", (STATEMENT_TIMEOUT,))
            rows = cur.execute(page, params).fetchall()
            if len(rows) < max_rows:
                # The page holds every match; counting again would only repeat it.
                total = len(rows)
            else:
                counted = cur.execute(count, params).fetchone()
                total = int(counted[_TOTAL]) if counted else len(rows)
        records = [{field: row[field] for field in source.fields} for row in rows]
        return TimeSeriesSlice(records=records, total=total)


class NullPersonalTimeSeriesRepository(IPersonalTimeSeriesRepository):
    """A deployment without TimescaleDB stores no reading (``NullObservationRepository``).

    It therefore has none to disclose: an empty slice is the truth here, not a silence.
    """

    def collect_personal_tenant_series(
        self,
        source: DataSourceDefinition,
        tenant_keys: Sequence[str],
        series_keys: Sequence[str],
        *,
        max_rows: int,
    ) -> TimeSeriesSlice:
        if source.time_series is None:
            msg = f"Manifest source '{source.collection}' is not a time-series source."
            raise ValueError(msg)
        return TimeSeriesSlice()
