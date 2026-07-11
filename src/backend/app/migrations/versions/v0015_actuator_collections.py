"""v0015 — REQ-018 environment control: 6 collections + 9 edges.

Creates the document collections (``actuators``, ``control_schedules``,
``control_rules``, ``control_events``, ``manual_overrides``,
``phase_control_profiles``) and the nine edge collections that wire locations to
actuators and actuators to their schedules/rules/overrides/events, plus the
phase/location profile and rule->sensor edges. Adds a ``(tenant_key, name)``
index on ``actuators`` and wires every edge into the named graph
``kamerplanter_graph``.

Fresh databases already get all of this from the idempotent startup
``ensure_collections`` (``collections.py``). This migration brings existing
volumes — and the standalone ``python -m app.migrations`` path — to the same
shape. Purely additive and idempotent (M-3): every step checks for existence
first, so a re-run is a no-op (``changed == 0``). No data is read or rewritten.
Irreversible (M-6).
"""

from __future__ import annotations

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger()

_INDEX_FIELDS: list[str] = ["tenant_key", "name"]

_DOC_COLLECTIONS = [
    col.ACTUATORS,
    col.CONTROL_SCHEDULES,
    col.CONTROL_RULES,
    col.CONTROL_EVENTS,
    col.MANUAL_OVERRIDES,
    col.PHASE_CONTROL_PROFILES,
]

_EDGE_DEFINITIONS = [
    {
        "edge_collection": col.HAS_ACTUATOR,
        "from_vertex_collections": [col.LOCATIONS],
        "to_vertex_collections": [col.ACTUATORS],
    },
    {
        "edge_collection": col.ACTUATOR_CONTROLS_LOCATION,
        "from_vertex_collections": [col.ACTUATORS],
        "to_vertex_collections": [col.LOCATIONS],
    },
    {
        "edge_collection": col.ACTUATOR_HAS_SCHEDULE,
        "from_vertex_collections": [col.ACTUATORS],
        "to_vertex_collections": [col.CONTROL_SCHEDULES],
    },
    {
        "edge_collection": col.ACTUATOR_HAS_RULE,
        "from_vertex_collections": [col.ACTUATORS],
        "to_vertex_collections": [col.CONTROL_RULES],
    },
    {
        "edge_collection": col.ACTUATOR_HAS_OVERRIDE,
        "from_vertex_collections": [col.ACTUATORS],
        "to_vertex_collections": [col.MANUAL_OVERRIDES],
    },
    {
        "edge_collection": col.ACTUATOR_EVENT,
        "from_vertex_collections": [col.ACTUATORS],
        "to_vertex_collections": [col.CONTROL_EVENTS],
    },
    {
        "edge_collection": col.PHASE_PROFILE,
        "from_vertex_collections": [col.GROWTH_PHASES],
        "to_vertex_collections": [col.PHASE_CONTROL_PROFILES],
    },
    {
        "edge_collection": col.LOCATION_PROFILE,
        "from_vertex_collections": [col.LOCATIONS],
        "to_vertex_collections": [col.PHASE_CONTROL_PROFILES],
    },
    {
        "edge_collection": col.RULE_MONITORS,
        "from_vertex_collections": [col.CONTROL_RULES],
        "to_vertex_collections": [col.SENSORS],
    },
]

_EDGE_COLLECTIONS = [d["edge_collection"] for d in _EDGE_DEFINITIONS]


def _has_index(indexes: object, fields: list[str]) -> bool:
    if not isinstance(indexes, list):
        return False
    return any(
        isinstance(idx, dict) and idx.get("type") == "persistent" and idx.get("fields") == fields for idx in indexes
    )


class ActuatorCollectionsMigration(Migration):
    version = "0015"
    name = "actuator_collections"
    description = "Create the REQ-018 environment-control collections + 9 edges on existing volumes."
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        docs_missing = [name for name in _DOC_COLLECTIONS if not db.has_collection(name)]
        edges_missing = [name for name in _EDGE_COLLECTIONS if not db.has_collection(name)]
        index_missing = col.ACTUATORS in docs_missing or not _has_index(
            db.collection(col.ACTUATORS).indexes(), _INDEX_FIELDS
        )
        if db.has_graph(col.GRAPH_NAME):
            existing = {ed["edge_collection"] for ed in db.graph(col.GRAPH_NAME).edge_definitions()}
            graph_edges_missing = [
                d["edge_collection"] for d in _EDGE_DEFINITIONS if d["edge_collection"] not in existing
            ]
        else:
            graph_edges_missing = list(_EDGE_COLLECTIONS)

        pending = {
            "document_collections": docs_missing,
            "edge_collections": edges_missing,
            "index": index_missing,
            "graph_edges": graph_edges_missing,
        }
        changes = len(docs_missing) + len(edges_missing) + int(index_missing) + len(graph_edges_missing)
        scanned = len(_DOC_COLLECTIONS) + len(_EDGE_COLLECTIONS)

        if dry_run:
            logger.info("actuator_migration_dry_run", pending=pending)
            return MigrationReport(
                version=self.version, name=self.name, scanned=scanned, changed=0, dry_run=True, details=pending
            )

        for name in docs_missing:
            db.create_collection(name)
        for name in edges_missing:
            db.create_collection(name, edge=True)

        collection = db.collection(col.ACTUATORS)
        if not _has_index(collection.indexes(), _INDEX_FIELDS):
            collection.add_persistent_index(fields=_INDEX_FIELDS, unique=False)

        if db.has_graph(col.GRAPH_NAME):
            graph = db.graph(col.GRAPH_NAME)
            for definition in _EDGE_DEFINITIONS:
                if definition["edge_collection"] in graph_edges_missing:
                    graph.create_edge_definition(**definition)

        logger.info("actuator_migration_applied", changed=changes, pending=pending)
        return MigrationReport(
            version=self.version, name=self.name, scanned=scanned, changed=changes, dry_run=False, details=pending
        )


migration = ActuatorCollectionsMigration()
