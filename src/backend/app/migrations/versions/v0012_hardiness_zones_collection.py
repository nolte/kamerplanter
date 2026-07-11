"""v0012 — REQ-039 hardiness zones: ``hardiness_zones`` collection + edge.

Creates the reference document collection ``hardiness_zones`` and the edge
collection ``located_in_zone`` (sites → hardiness_zones) on *existing* volumes,
adds the unique ``[zone]`` index and wires the edge into the named graph
``kamerplanter_graph``. It additionally back-fills ``Site.hardiness_zone`` from a
legacy ``climate_zone`` value **only** when that value already has a valid zone
format (``<number><a|b>``) — free-text climate zones are left untouched.

Fresh databases already get the collections/index/graph edge from the idempotent
startup ``ensure_collections`` (``collections.py``); this migration brings
existing volumes — and the standalone ``python -m app.migrations`` path, which
does not call ``ensure_collections`` — to the same shape.

Purely additive and idempotent (M-3): every step checks first, so a re-run is a
no-op (``changed == 0``). Irreversible (M-6): dropping a collection the bootstrap
also creates would not honestly restore the pre-migration state.
"""

from __future__ import annotations

import re

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger()

_INDEX_FIELDS: list[str] = ["zone"]
_ZONE_PATTERN = re.compile(r"^\d{1,2}[ab]$")

_EDGE_DEFINITION = {
    "edge_collection": col.LOCATED_IN_ZONE,
    "from_vertex_collections": [col.SITES],
    "to_vertex_collections": [col.HARDINESS_ZONES],
}


def _has_index(indexes: object, fields: list[str]) -> bool:
    if not isinstance(indexes, list):
        return False
    return any(
        isinstance(idx, dict) and idx.get("type") == "persistent" and idx.get("fields") == fields for idx in indexes
    )


class HardinessZonesCollectionMigration(Migration):
    version = "0012"
    name = "hardiness_zones_collection"
    description = "Create the REQ-039 hardiness_zones collection + located_in_zone edge and backfill valid zones."
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        doc_missing = not db.has_collection(col.HARDINESS_ZONES)
        edge_missing = not db.has_collection(col.LOCATED_IN_ZONE)
        index_missing = doc_missing or not _has_index(db.collection(col.HARDINESS_ZONES).indexes(), _INDEX_FIELDS)
        graph_edge_missing = True
        if db.has_graph(col.GRAPH_NAME):
            existing = {ed["edge_collection"] for ed in db.graph(col.GRAPH_NAME).edge_definitions()}
            graph_edge_missing = col.LOCATED_IN_ZONE not in existing

        backfill_keys = self._sites_needing_backfill(db)

        pending = {
            "document_collection": doc_missing,
            "edge_collection": edge_missing,
            "index": index_missing,
            "graph_edge": graph_edge_missing,
            "site_backfill": len(backfill_keys),
        }
        changes = sum(1 for key, is_pending in pending.items() if key != "site_backfill" and is_pending)
        changes += len(backfill_keys)

        if dry_run:
            logger.info("hardiness_zones_migration_dry_run", pending=pending)
            return MigrationReport(
                version=self.version,
                name=self.name,
                scanned=len(pending),
                changed=0,
                dry_run=True,
                details=pending,
            )

        if doc_missing:
            db.create_collection(col.HARDINESS_ZONES)
        if edge_missing:
            db.create_collection(col.LOCATED_IN_ZONE, edge=True)

        collection = db.collection(col.HARDINESS_ZONES)
        if not _has_index(collection.indexes(), _INDEX_FIELDS):
            collection.add_persistent_index(fields=_INDEX_FIELDS, unique=True)

        if db.has_graph(col.GRAPH_NAME) and graph_edge_missing:
            db.graph(col.GRAPH_NAME).create_edge_definition(**_EDGE_DEFINITION)

        self._apply_backfill(db, backfill_keys)

        logger.info("hardiness_zones_migration_applied", changed=changes, pending=pending)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=len(pending),
            changed=changes,
            dry_run=False,
            details=pending,
        )

    @staticmethod
    def _sites_needing_backfill(db: StandardDatabase) -> list[str]:
        """Keys of sites with a valid-format ``climate_zone`` and no ``hardiness_zone``."""
        if not db.has_collection(col.SITES):
            return []
        cursor = db.aql.execute(
            "FOR s IN @@col FILTER s.hardiness_zone == null AND s.climate_zone != null "
            "AND s.climate_zone != '' RETURN {key: s._key, climate_zone: s.climate_zone}",
            bind_vars={"@col": col.SITES},
        )
        return [doc["key"] for doc in cursor if _ZONE_PATTERN.match(str(doc["climate_zone"]))]

    @staticmethod
    def _apply_backfill(db: StandardDatabase, keys: list[str]) -> None:
        if not keys:
            return
        db.aql.execute(
            "FOR s IN @@col FILTER s._key IN @keys "
            "UPDATE s WITH {hardiness_zone: s.climate_zone, hardiness_zone_source: 'manual'} IN @@col",
            bind_vars={"@col": col.SITES, "keys": keys},
        )


migration = HardinessZonesCollectionMigration()
