"""REQ-046 §3.6a (#2934) — the weather fetch status document.

A document of its own in the platform collection ``system_settings`` (key
``weather_fetch_status``), next to — never inside — the ``default`` settings
singleton: the admin settings PUT rewrites the singleton whole, and a run recorded
between its read and its write would be lost (operator decision 2026-11-17). Only
the fetch task writes here, in one ``UPSERT`` statement.
"""

from datetime import UTC, datetime

from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.document_reads import get_document
from app.domain.interfaces.weather_fetch import IWeatherFetchStatusRepository
from app.domain.models.weather_fetch import WeatherFetchRun, WeatherFetchStatus

STATUS_KEY = "weather_fetch_status"

_RECORD_RUN_QUERY = """
UPSERT { _key: @key }
INSERT { _key: @key, last_run: @run, last_success: @success ? @run : null, created_at: @now, updated_at: @now }
UPDATE { last_run: @run, last_success: @success ? @run : OLD.last_success, updated_at: @now }
IN @@collection
OPTIONS { mergeObjects: false }
"""


class ArangoWeatherFetchStatusRepository(IWeatherFetchStatusRepository):
    def __init__(self, db: StandardDatabase) -> None:
        self._db = db

    def get_status(self) -> WeatherFetchStatus:
        doc = get_document(self._db.collection(col.SYSTEM_SETTINGS), STATUS_KEY)
        if doc is None:
            return WeatherFetchStatus()
        return WeatherFetchStatus(last_run=doc.get("last_run"), last_success=doc.get("last_success"))

    def record_run(self, run: WeatherFetchRun) -> None:
        self._db.aql.execute(
            _RECORD_RUN_QUERY,
            bind_vars={
                "@collection": col.SYSTEM_SETTINGS,
                "key": STATUS_KEY,
                "run": run.model_dump(mode="json"),
                "success": run.success,
                "now": datetime.now(UTC).isoformat(),
            },
        )
