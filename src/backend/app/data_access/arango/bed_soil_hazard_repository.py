"""ArangoDB writes of a bed's soil hazards (REQ-054 §5.2, #2888 F-20), see the interface module of the same name."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.transactions import StreamTransaction, stream_transaction
from app.domain.interfaces.bed_soil_hazard_repository import (
    IBedSoilHazardRepository,
    SoilHazardChange,
    SoilHazardWrite,
)
from app.domain.models.bed_soil_hazard import BedSoilHazard

#: The bed **through its site's tenant** (a location carries no ``tenant_key``, #2107): a key of another tenant's
#: bed finds no row, exactly like an absent one.
_OWNED_LOCATION = """
FOR l IN @@locations
    FILTER l._key == @location_key
    FOR s IN @@sites
        FILTER s._key == l.site_key AND s.tenant_key == @tenant_key
        LIMIT 1
        RETURN {soil_hazards: l.soil_hazards || []}
"""

#: ``UPDATE <key> WITH`` rather than ``UPDATE { _key: … } WITH``: the same statement, in the shape the write-route
#: detector (``tests/unit/api/_write_call_graph.py``) recognises as a write.
_WRITE_SOIL_HAZARDS = """
UPDATE @location_key
    WITH { soil_hazards: @soil_hazards, updated_at: @now }
    IN @@locations
"""


class ArangoBedSoilHazardRepository(IBedSoilHazardRepository):
    def __init__(self, db: StandardDatabase) -> None:
        self._db = db

    @staticmethod
    def _read(txn: StreamTransaction, location_key: str, tenant_key: str) -> tuple[BedSoilHazard, ...] | None:
        rows: list[dict[str, Any]] = list(
            txn.aql.execute(
                _OWNED_LOCATION,
                bind_vars={
                    "@locations": col.LOCATIONS,
                    "@sites": col.SITES,
                    "location_key": location_key,
                    "tenant_key": tenant_key,
                },
            )
        )
        if not rows:
            return None
        return tuple(BedSoilHazard.model_validate(entry) for entry in rows[0].get("soil_hazards") or [])

    def change_soil_hazards(self, location_key: str, *, tenant_key: str, change: SoilHazardChange) -> SoilHazardWrite:
        if not tenant_key:
            raise ValueError("change_soil_hazards needs a tenant_key (an empty tenant is no tenant, #2107).")
        with stream_transaction(self._db, write=(col.LOCATIONS,), read=(col.SITES,), entity="location") as txn:
            stored = self._read(txn, location_key, tenant_key)
            if stored is None:
                return SoilHazardWrite("location_not_found")
            changed = change(stored)
            if changed == stored:
                return SoilHazardWrite("unchanged", stored)
            txn.aql.execute(
                _WRITE_SOIL_HAZARDS,
                bind_vars={
                    "@locations": col.LOCATIONS,
                    "location_key": location_key,
                    "soil_hazards": [entry.model_dump(mode="json") for entry in changed],
                    "now": datetime.now(UTC).isoformat(),
                },
            )
            return SoilHazardWrite("written", changed)
