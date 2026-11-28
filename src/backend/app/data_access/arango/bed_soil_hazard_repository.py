"""ArangoDB writes of a bed's soil hazards (REQ-054 §5.2, #2888 F-20), see the interface module of the same name."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from arango.database import StandardDatabase
from pydantic import BaseModel

from app.common.enums import SoilHazard
from app.data_access.arango import collections as col
from app.data_access.arango.transactions import StreamTransaction, stream_transaction
from app.domain.interfaces.bed_soil_hazard_repository import (
    IBedSoilHazardRepository,
    SoilHazardChange,
    SoilHazardRemoval,
    SoilHazardWrite,
)
from app.domain.models.bed_soil_hazard import AUDIT_ENTITY_SOIL_HAZARD, BedSoilHazard, removal_audit_summary
from app.domain.models.garden_plan import PlanAuditRecord

#: The bed **through its site's tenant** (a location carries no ``tenant_key``, #2107): a key of another tenant's
#: bed finds no row, exactly like an absent one.
_OWNED_LOCATION = """
FOR l IN @@locations
    FILTER l._key == @location_key
    FOR s IN @@sites
        FILTER s._key == l.site_key AND s.tenant_key == @tenant_key
        LIMIT 1
        RETURN {soil_hazards: l.soil_hazards || [], site_key: s._key, revision: s.plan.plan_revision || 0}
"""

#: ``UPDATE <key> WITH`` rather than ``UPDATE { _key: … } WITH``: the same statement, in the shape the write-route
#: detector (``tests/unit/api/_write_call_graph.py``) recognises as a write.
_WRITE_SOIL_HAZARDS = """
UPDATE @location_key
    WITH { soil_hazards: @soil_hazards, updated_at: @now }
    IN @@locations
"""


def _dump(model: BaseModel, **options: Any) -> dict[str, Any]:
    """``model_dump`` through a receiver typed as the pydantic base (see the call-graph sweep's blind-spot ceiling)."""
    return model.model_dump(**options)


class ArangoBedSoilHazardRepository(IBedSoilHazardRepository):
    def __init__(self, db: StandardDatabase) -> None:
        self._db = db

    @staticmethod
    def _read(txn: StreamTransaction, location_key: str, tenant_key: str) -> tuple[BedSoilHazard, ...] | None:
        row = ArangoBedSoilHazardRepository._read_row(txn, location_key, tenant_key)
        if row is None:
            return None
        return tuple(BedSoilHazard.model_validate(entry) for entry in row.get("soil_hazards") or [])

    @staticmethod
    def _read_row(txn: StreamTransaction, location_key: str, tenant_key: str) -> dict[str, Any] | None:
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
        return rows[0] if rows else None

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

    def remove_soil_hazard(
        self, location_key: str, hazard: SoilHazard, *, tenant_key: str, user_key: str, at: datetime
    ) -> SoilHazardRemoval:
        if not tenant_key:
            raise ValueError("remove_soil_hazard needs a tenant_key (an empty tenant is no tenant, #2107).")
        with stream_transaction(
            self._db, write=(col.LOCATIONS, col.GARDEN_PLAN_AUDIT), read=(col.SITES,), entity="location"
        ) as txn:
            row = self._read_row(txn, location_key, tenant_key)
            if row is None:
                return SoilHazardRemoval("location_not_found")
            stored = tuple(BedSoilHazard.model_validate(entry) for entry in row.get("soil_hazards") or [])
            removed = next((entry for entry in stored if entry.hazard is hazard), None)
            if removed is None:
                return SoilHazardRemoval("not_held")
            txn.aql.execute(
                _WRITE_SOIL_HAZARDS,
                bind_vars={
                    "@locations": col.LOCATIONS,
                    "location_key": location_key,
                    "soil_hazards": [_dump(entry, mode="json") for entry in stored if entry.hazard is not hazard],
                    "now": at.astimezone(UTC).isoformat(),
                },
            )
            audit = PlanAuditRecord(
                tenant_key=tenant_key,
                site_key=str(row["site_key"]),
                revision=int(row.get("revision") or 0),
                user_key=user_key,
                op="delete",
                entity=AUDIT_ENTITY_SOIL_HAZARD,
                key=location_key,
                summary=removal_audit_summary(removed),
                at=at,
            )
            txn.collection(col.GARDEN_PLAN_AUDIT).insert(_dump(audit, mode="json"))
            return SoilHazardRemoval("removed", removed)
