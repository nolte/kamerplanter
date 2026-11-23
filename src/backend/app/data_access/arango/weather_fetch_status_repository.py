"""REQ-046 §3.6a (#2934) — the weather fetch status document.

A document of its own in the platform collection ``system_settings`` (key
``weather_fetch_status``), next to — never inside — the ``default`` settings
singleton: the admin settings PUT rewrites the singleton whole, and a run recorded
between its read and its write would be lost (operator decision 2026-11-17). Only
the fetch task writes here, in one ``UPSERT`` statement.

The read is tolerant: a document that does not validate (hand edit, older shape)
reads as "no status" — logged — so the hourly due-check treats the fetch as due
and the next run overwrites it, instead of raising on every tick.
"""

from datetime import UTC, datetime

import structlog
from arango.database import StandardDatabase
from pydantic import ValidationError as PydanticValidationError
from pydantic_core import to_jsonable_python

from app.data_access.arango import collections as col
from app.data_access.arango.document_reads import get_document, invalid_fields
from app.domain.interfaces.weather_fetch import IWeatherFetchStatusRepository
from app.domain.models.weather_fetch import WeatherFetchRun, WeatherFetchStatus

logger = structlog.get_logger(__name__)

STATUS_KEY = "weather_fetch_status"

_RECORD_RUN_QUERY = """
UPSERT { _key: @key }
INSERT {
  _key: @key, last_run: @run, last_success: @success ? @run : null,
  consecutive_failures: @success ? 0 : 1, created_at: @now, updated_at: @now
}
UPDATE {
  last_run: @run, last_success: @success ? @run : OLD.last_success,
  consecutive_failures: @success ? 0 : TO_NUMBER(OLD.consecutive_failures) + 1, updated_at: @now
}
IN @@collection
OPTIONS { mergeObjects: false }
RETURN NEW.consecutive_failures
"""


class ArangoWeatherFetchStatusRepository(IWeatherFetchStatusRepository):
    def __init__(self, db: StandardDatabase) -> None:
        self._db = db

    def get_status(self) -> WeatherFetchStatus:
        doc = get_document(self._db.collection(col.SYSTEM_SETTINGS), STATUS_KEY)
        if doc is None:
            return WeatherFetchStatus()
        try:
            return WeatherFetchStatus(
                last_run=doc.get("last_run"),
                last_success=doc.get("last_success"),
                consecutive_failures=doc.get("consecutive_failures") or 0,
            )
        except PydanticValidationError as exc:
            logger.warning("weather_fetch_status_unreadable", fields=invalid_fields(exc))
            return WeatherFetchStatus()

    def record_run(self, run: WeatherFetchRun) -> int:
        cursor = self._db.aql.execute(
            _RECORD_RUN_QUERY,
            bind_vars={
                "@collection": col.SYSTEM_SETTINGS,
                "key": STATUS_KEY,
                # JSON mode (ISO datetimes, enum values), as a plain function call (#2934).
                "run": to_jsonable_python(run),
                "success": run.success,
                "now": datetime.now(UTC).isoformat(),
            },
        )
        rows = list(cursor)  # type: ignore[arg-type]
        return int(rows[0] or 0) if rows else 0
