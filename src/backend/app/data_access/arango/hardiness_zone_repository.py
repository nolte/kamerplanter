"""REQ-039 — ArangoDB repository for the global ``hardiness_zones`` catalog.

Reference data (not tenant-scoped, analogous to
:class:`ArangoBotanicalFamilyRepository`): one document per USDA half-zone whose
``_key`` is the zone label itself (``"7a"``). Also manages the per-site
``located_in_zone`` assignment edge (exactly one per site).
"""

from __future__ import annotations

from datetime import UTC, datetime

from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.engines.hardiness_zone_resolver import index_for_zone_label
from app.domain.models.hardiness_zone import HardinessZone


class ArangoHardinessZoneRepository(BaseArangoRepository[HardinessZone]):
    _model_cls = HardinessZone

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.HARDINESS_ZONES)

    def get_all_zones(self) -> list[HardinessZone]:
        """All zones, ordered coldest → warmest (``1a`` … ``13b``)."""
        query = "FOR z IN @@collection RETURN z"
        cursor = self._db.aql.execute(query, bind_vars={"@collection": col.HARDINESS_ZONES})
        zones = [HardinessZone(**self._from_doc(doc)) for doc in cursor]
        return sorted(zones, key=lambda z: index_for_zone_label(z.zone))

    def get_by_zone(self, zone: str) -> HardinessZone | None:
        """Fetch a zone by its label (which is also the ``_key``)."""
        return self.get_by_key(zone)

    def upsert_zone(self, zone: HardinessZone) -> HardinessZone:
        """Idempotently persist a catalog entry keyed by its zone label.

        Used by the seed job: a re-run updates the existing document in place
        rather than duplicating it, so the catalog never grows on restart.
        """
        data = self._to_doc(zone)
        data["_key"] = zone.zone
        data["updated_at"] = datetime.now(UTC).isoformat()
        if self.collection.has(zone.zone):
            self.collection.update(data)
        else:
            data["created_at"] = data["updated_at"]
            self.collection.insert(data)
        result = self.get_by_key(zone.zone)
        assert result is not None  # noqa: S101 — just written
        return result

    def assign_site_to_zone(
        self,
        site_key: str,
        zone: str,
        *,
        source: str,
        resolved_at: datetime,
    ) -> None:
        """(Re)point the site's single ``located_in_zone`` edge at ``zone``.

        Removes any prior assignment edge for the site first, so a re-resolution
        never accumulates stale edges.
        """
        from_id = f"{col.SITES}/{site_key}"
        to_id = f"{col.HARDINESS_ZONES}/{zone}"
        self.delete_edges(col.LOCATED_IN_ZONE, from_id=from_id)
        self.create_edge(
            col.LOCATED_IN_ZONE,
            from_id,
            to_id,
            data={"source": source, "resolved_at": resolved_at.isoformat()},
        )
