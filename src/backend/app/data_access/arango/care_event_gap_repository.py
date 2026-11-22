"""ArangoDB read of the domain events that lack a care event (REQ-053 GP-FR-105; WP 8.2, #2645).

The scan itself is shared with the M4 backfill migration (:mod:`.care_event_backfill_scan`).
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

from arango.database import StandardDatabase

from app.data_access.arango.care_event_backfill_scan import scan_candidates
from app.domain.interfaces.care_event_gap_reader import ICareEventGapReader


class ArangoCareEventGapReader(ICareEventGapReader):
    def __init__(self, db: StandardDatabase) -> None:
        self._db = db

    def candidates(self, source: str, since: datetime) -> Iterator[dict[str, Any]]:
        cutoff_ms = int(since.astimezone(UTC).timestamp() * 1000)
        yield from scan_candidates(self._db, source, cutoff_ms)
