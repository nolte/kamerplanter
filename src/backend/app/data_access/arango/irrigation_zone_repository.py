"""ArangoDB persistence of the irrigation zones (REQ-053 §14, §20.11; WP 7.1, #2467).

``irrigation_zones`` (migration v0093) carries ``tenant_key`` (E-01); every read filters the document on it
inside the query, and every write first re-reads the zone under the tenant **inside** its transaction, so a
zone deleted or taken over between the service's read and the write is a 404 and never a write on a stranger's
row.

**Coverage is kept in step.** Which beds a zone waters is held by the ``zone_covers`` edge (unique on ``_to``,
v0099: a bed is in at most one zone) *and* by ``Location.irrigation_zone_key``. The two writers here
(:meth:`replace_zone_locations`, :meth:`delete_zone`) change both in one stream transaction; the other two writers,
``PATCH /locations/{key}`` (``ArangoGardenPlanRepository.update_location_fields``) and the plan import
(``ArangoGardenPlanRepository._take_import_zones``), do the same. ``site_repository.delete_site`` removes a site's
zones with their edges, the legacy ``delete_location`` the bed's ``zone_covers`` edge.

**Every write takes the zone document first** (an ``UPDATE`` of ``updated_at``, under the tenant and — for the
plan writers — the bed's site), so two writers of one zone — two coverage replacements, a replacement and the
delete, a bed's PATCH or an import that assigns the zone and its delete — cannot both pass: the loser fails on the
write-write conflict (409 ``conflict.write``) instead of committing a coverage the winner never saw. A zone that
names a water source takes that garden object the same way (:data:`_TAKE_WATER_SOURCE`), so a plan batch deleting
it concurrently cannot leave a dead ``water_source_key``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

import structlog
from arango.cursor import Cursor
from arango.database import StandardDatabase
from pydantic import BaseModel

from app.common.exceptions import NotFoundError, PlanValidationError, WriteConflictError
from app.common.types import IrrigationZoneKey, LocationKey, SiteKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.data_access.arango.query_builder import aql_field
from app.data_access.arango.transactions import StreamTransaction, stream_transaction
from app.domain.engines.garden_plan_engine import ERROR_REFERENCE_NOT_FOUND
from app.domain.interfaces.irrigation_zone_repository import IIrrigationZoneRepository
from app.domain.models.garden_plan import PlanAuditRecord
from app.domain.models.irrigation_zone import IrrigationZone, ZoneCoverageChange

logger = structlog.get_logger()


def _edges_touching_zones() -> tuple[tuple[str, str], ...]:
    """``(edge collection, "_from" | "_to")`` of every named-graph edge that can end at a zone.

    Derived from ``GRAPH_EDGE_DEFINITIONS`` (the ``garden_plan_repository`` rule): a hand-written list misses
    the next relation added to the graph, which then dangles on a zone that is gone.
    """
    found: list[tuple[str, str]] = []
    for definition in col.GRAPH_EDGE_DEFINITIONS:
        edge = str(definition["edge_collection"])
        if col.IRRIGATION_ZONES in definition["from_vertex_collections"]:
            found.append((edge, "_from"))
        if col.IRRIGATION_ZONES in definition["to_vertex_collections"]:
            found.append((edge, "_to"))
    return tuple(found)


#: Every named-graph edge that can end at a zone; ``site_repository.delete_site`` cascades over the same set.
ZONE_EDGES = _edges_touching_zones()

#: What creating or editing a zone writes: the zone, its site edge, its water-source edge — and the water source
#: itself, which is taken inside the transaction so a plan batch deleting it concurrently conflicts.
ZONE_WRITE: tuple[str, ...] = (col.IRRIGATION_ZONES, col.HAS_IRRIGATION_ZONE, col.ZONE_SUPPLIED_BY, col.GARDEN_OBJECTS)
#: What a coverage replacement writes: the zone (taken first), the beds' field and the edges.
COVERAGE_WRITE: tuple[str, ...] = (col.IRRIGATION_ZONES, col.LOCATIONS, col.ZONE_COVERS)
#: What the delete writes: the zone, the beds it releases, every edge on the zone and the audit row.
DELETE_WRITE: tuple[str, ...] = tuple(
    dict.fromkeys((col.IRRIGATION_ZONES, col.LOCATIONS, col.GARDEN_PLAN_AUDIT, *(edge for edge, _ in ZONE_EDGES)))
)

_ZONE_BY_KEY = """
LET z = DOCUMENT(CONCAT(@zones, @key))
FILTER z != null AND z.tenant_key == @tenant_key
"""

#: Take the water source inside a transaction: a ``water_source`` object of ``@site_key`` whose site is the tenant's.
#: The ``UPDATE`` is the point — a plan batch that deletes the object at the same time loses on the write-write
#: conflict, or this statement finds it gone, so a zone never commits a ``water_source_key`` that is dead.
_TAKE_WATER_SOURCE = """
FOR o IN @@objects
    FILTER o._key == @key AND o.site_key == @site_key AND o.object_type == "water_source"
    LET site = DOCUMENT(CONCAT(@sites, o.site_key))
    FILTER site != null AND site.tenant_key == @tenant_key
    UPDATE o WITH { updated_at: @now } IN @@objects
    RETURN 1
"""

#: Take the zone's document inside a transaction: the first write, so a concurrent writer of the zone conflicts.
_TAKE_ZONE = """
FOR z IN @@zones
    FILTER z._key == @key AND z.tenant_key == @tenant_key
    UPDATE z WITH { updated_at: @now } IN @@zones
    RETURN NEW
"""


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _dump(model: BaseModel, **options: Any) -> dict[str, Any]:
    """``model_dump`` through a receiver typed as the pydantic base (see the call-graph sweep's blind-spot ceiling)."""
    return model.model_dump(**options)


def _zone_id(key: str) -> str:
    return f"{col.IRRIGATION_ZONES}/{key}"


def _location_ids(keys: list[str]) -> list[str]:
    return [f"{col.LOCATIONS}/{key}" for key in keys]


class ArangoIrrigationZoneRepository(BaseArangoRepository[IrrigationZone], IIrrigationZoneRepository):
    """``irrigation_zones`` with ``has_irrigation_zone`` / ``zone_covers`` / ``zone_supplied_by`` (v0093)."""

    _model_cls = IrrigationZone
    is_tenant_scoped = True

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.IRRIGATION_ZONES)

    def _wrapped(self, doc: dict[str, Any]) -> IrrigationZone:
        return IrrigationZone(**self._from_doc(doc))

    # ── Reads ─────────────────────────────────────────────────────────────

    def list_zones_by_site(
        self, site_key: SiteKey, *, tenant_key: str, offset: int, limit: int
    ) -> list[IrrigationZone]:
        """A window of the site's zones by name (the v0099 ``(tenant_key, site_key)`` index)."""
        self._require_tenant_key(tenant_key, "list_zones_by_site")
        bind_vars: dict[str, Any] = {
            "@zones": col.IRRIGATION_ZONES,
            "tenant_key": tenant_key,
            "site_key": site_key,
            "offset": offset,
            "limit": limit,
        }
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                """
            FOR z IN @@zones
                FILTER z.tenant_key == @tenant_key AND z.site_key == @site_key
                SORT z.name ASC, z._key ASC
                LIMIT @offset, @limit
                RETURN z
            """,
                bind_vars=bind_vars,
            ),
        )
        return [self._wrapped(doc) for doc in cursor]

    def get_zone_by_key(self, key: IrrigationZoneKey, *, tenant_key: str) -> IrrigationZone | None:
        """The zone behind ``key`` when it is the tenant's; absent and foreign both give ``None``."""
        self._require_tenant_key(tenant_key, "get_zone_by_key")
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                f"{_ZONE_BY_KEY} RETURN z",
                bind_vars={"zones": f"{col.IRRIGATION_ZONES}/", "key": key, "tenant_key": tenant_key},
            ),
        )
        doc = next(cursor, None)
        return self._wrapped(doc) if doc is not None else None

    def get_zone_or_raise(self, key: IrrigationZoneKey, *, tenant_key: str) -> IrrigationZone:
        zone = self.get_zone_by_key(key, tenant_key=tenant_key)
        if zone is None:
            raise NotFoundError("IrrigationZone", key)
        return zone

    def covered_location_keys(
        self, zone_keys: list[IrrigationZoneKey], *, tenant_key: str
    ) -> dict[IrrigationZoneKey, list[LocationKey]]:
        self._require_tenant_key(tenant_key, "covered_location_keys")
        if not zone_keys:
            return {}
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                """
            FOR z IN @@zones
                FILTER z._key IN @keys AND z.tenant_key == @tenant_key
                LET covered = (
                    FOR e IN @@covers
                        FILTER e._from == z._id
                        LET key = PARSE_IDENTIFIER(e._to).key
                        SORT key ASC
                        RETURN key
                )
                RETURN { zone: z._key, covered: covered }
            """,
                bind_vars={
                    "@zones": col.IRRIGATION_ZONES,
                    "@covers": col.ZONE_COVERS,
                    "keys": zone_keys,
                    "tenant_key": tenant_key,
                },
            ),
        )
        found = {str(row["zone"]): [str(key) for key in row["covered"]] for row in cursor}
        return {key: found.get(key, []) for key in zone_keys}

    # ── Writes ────────────────────────────────────────────────────────────

    def create_zone(self, zone: IrrigationZone, *, tenant_key: str) -> IrrigationZone:
        self._require_tenant_key(tenant_key, "create_zone")
        if zone.tenant_key != tenant_key or not zone.site_key:
            raise ValueError("create_zone: the zone belongs to another tenant or names no site.")
        # Re-validated on the way (the #968 rule for hand-written writers): the caller may have mutated the model.
        doc = _dump(IrrigationZone(**_dump(zone, by_alias=True)), by_alias=True, mode="json")
        doc.pop("_key", None)
        now = _now()
        doc["created_at"] = doc["updated_at"] = now
        with stream_transaction(self._db, write=ZONE_WRITE, read=(col.SITES,), entity="irrigation_zone") as txn:
            created = txn.collection(col.IRRIGATION_ZONES).insert(doc, return_new=True)["new"]
            zone_id = str(created["_id"])
            txn.collection(col.HAS_IRRIGATION_ZONE).insert(
                {"_from": f"{col.SITES}/{zone.site_key}", "_to": zone_id, "created_at": now}
            )
            if zone.water_source_key:
                self._take_water_source(txn, zone.water_source_key, zone.site_key, tenant_key, now)
                self._link_water_source(txn, zone_id, zone.water_source_key, now)
        return self._wrapped(created)

    def update_zone(self, key: IrrigationZoneKey, fields: dict[str, Any], *, tenant_key: str) -> IrrigationZone:
        self._require_tenant_key(tenant_key, "update_zone")
        now = _now()
        with stream_transaction(self._db, write=ZONE_WRITE, read=(col.SITES,), entity="irrigation_zone") as txn:
            taken = self._take_zone(txn, key, tenant_key, now)
            if fields.get("water_source_key"):
                self._take_water_source(txn, str(fields["water_source_key"]), str(taken["site_key"]), tenant_key, now)
            updated = txn.collection(col.IRRIGATION_ZONES).update(
                {"_key": key, **fields, "updated_at": now}, merge=False, keep_none=False, return_new=True
            )["new"]
            if "water_source_key" in fields:
                zone_id = _zone_id(key)
                self._remove_edges(txn, col.ZONE_SUPPLIED_BY, "_from", [zone_id])
                if fields["water_source_key"]:
                    self._link_water_source(txn, zone_id, str(fields["water_source_key"]), now)
        return self._wrapped(updated)

    def delete_zone(self, key: IrrigationZoneKey, *, tenant_key: str, user_key: str) -> list[LocationKey]:
        self._require_tenant_key(tenant_key, "delete_zone")
        now = _now()
        zone_id = _zone_id(key)
        with stream_transaction(self._db, write=DELETE_WRITE, read=(col.SITES,), entity="irrigation_zone") as txn:
            zone = self._take_zone(txn, key, tenant_key, now)
            site_key = str(zone["site_key"])
            covered = self._covered_in(txn, zone_id)
            released = self._release_locations(txn, key, site_key, covered, keep=[], now=now)
            for edge, field_name in ZONE_EDGES:
                self._remove_edges(txn, edge, field_name, [zone_id])
            txn.collection(col.IRRIGATION_ZONES).delete(key)
            revision = next(
                iter(
                    txn.aql.execute(
                        "RETURN DOCUMENT(CONCAT(@sites, @site_key)).plan.plan_revision || 0",
                        bind_vars={"sites": f"{col.SITES}/", "site_key": site_key},
                    )
                ),
                0,
            )
            audit = PlanAuditRecord(
                tenant_key=tenant_key,
                site_key=site_key,
                revision=int(revision),
                user_key=user_key,
                op="delete",
                entity="irrigation_zone",
                key=key,
                summary=str(zone.get("name", ""))[:200],
                at=datetime.fromisoformat(now),
            )
            txn.collection(col.GARDEN_PLAN_AUDIT).insert(_dump(audit, mode="json"))
        return released

    def replace_zone_locations(
        self, key: IrrigationZoneKey, location_keys: list[LocationKey], *, tenant_key: str
    ) -> ZoneCoverageChange:
        self._require_tenant_key(tenant_key, "replace_zone_locations")
        wanted = sorted(set(location_keys))
        now = _now()
        zone_id = _zone_id(key)
        with stream_transaction(self._db, write=COVERAGE_WRITE, entity="irrigation_zone") as txn:
            zone = self._take_zone(txn, key, tenant_key, now)
            site_key = str(zone["site_key"])
            self._refuse_vanished_locations(txn, wanted, site_key)
            current = set(self._covered_in(txn, zone_id))
            added = [loc for loc in wanted if loc not in current]
            removed = sorted(current - set(wanted))
            moved_from = self._covering_zones(txn, added, exclude=zone_id)
            # One query removes the zone's dropped edges and the edges another zone held on the added beds.
            txn.aql.execute(
                """
            FOR e IN @@covers
                FILTER (e._from == @zone AND e._to IN @removed) OR e._to IN @added
                REMOVE e IN @@covers
            """,
                bind_vars={
                    "@covers": col.ZONE_COVERS,
                    "zone": zone_id,
                    "removed": _location_ids(removed),
                    "added": _location_ids(added),
                },
            )
            self._release_locations(txn, key, site_key, removed, keep=wanted, now=now)
            if wanted:
                txn.aql.execute(
                    """
                FOR l IN @@locations
                    FILTER l._key IN @keys AND l.irrigation_zone_key != @zone_key
                    UPDATE l WITH { irrigation_zone_key: @zone_key, updated_at: @now } IN @@locations
                """,
                    bind_vars={"@locations": col.LOCATIONS, "keys": wanted, "zone_key": key, "now": now},
                )
            if added:
                txn.collection(col.ZONE_COVERS).insert_many(
                    [{"_from": zone_id, "_to": location_id, "created_at": now} for location_id in _location_ids(added)]
                )
        return ZoneCoverageChange(added=tuple(added), removed=tuple(removed), moved_from=moved_from)

    # ── Transaction steps ─────────────────────────────────────────────────

    @staticmethod
    def _take_zone(txn: StreamTransaction, key: str, tenant_key: str, now: str) -> dict[str, Any]:
        rows = list(
            txn.aql.execute(
                _TAKE_ZONE,
                bind_vars={"@zones": col.IRRIGATION_ZONES, "key": key, "tenant_key": tenant_key, "now": now},
            )
        )
        if not rows:
            raise NotFoundError("IrrigationZone", key)
        return cast("dict[str, Any]", rows[0])

    @staticmethod
    def _covered_in(txn: StreamTransaction, zone_id: str) -> list[str]:
        return [
            str(key)
            for key in txn.aql.execute(
                "FOR e IN @@covers FILTER e._from == @zone RETURN PARSE_IDENTIFIER(e._to).key",
                bind_vars={"@covers": col.ZONE_COVERS, "zone": zone_id},
            )
        ]

    @staticmethod
    def _covering_zones(txn: StreamTransaction, location_keys: list[str], *, exclude: str) -> dict[str, str]:
        if not location_keys:
            return {}
        rows = txn.aql.execute(
            """
        FOR e IN @@covers
            FILTER e._to IN @ids AND e._from != @exclude
            RETURN { location: PARSE_IDENTIFIER(e._to).key, zone: PARSE_IDENTIFIER(e._from).key }
        """,
            bind_vars={"@covers": col.ZONE_COVERS, "ids": _location_ids(location_keys), "exclude": exclude},
        )
        return {str(row["location"]): str(row["zone"]) for row in rows}

    @staticmethod
    def _refuse_vanished_locations(txn: StreamTransaction, keys: list[str], site_key: str) -> None:
        """The beds the service resolved still exist on the zone's site — a bed deleted meanwhile is a 409."""
        if not keys:
            return
        found = list(
            txn.aql.execute(
                "FOR l IN @@locations FILTER l._key IN @keys AND l.site_key == @site_key RETURN 1",
                bind_vars={"@locations": col.LOCATIONS, "keys": keys, "site_key": site_key},
            )
        )
        if len(found) != len(keys):
            raise WriteConflictError("irrigation_zone", "a location of the zone was removed concurrently")

    @staticmethod
    def _release_locations(
        txn: StreamTransaction, zone_key: str, site_key: str, covered: list[str], *, keep: list[str], now: str
    ) -> list[str]:
        """Clear ``irrigation_zone_key`` on the beds that leave the zone; returns their keys.

        The beds are the ones the edges name **and** any bed of the site that still carries the key without
        an edge (a row written before the edge was maintained) — so the field never outlives the zone.
        ``site_key`` bounds the second half to the site's beds (the v0093 ``(site_key, bed_status)`` index).
        """
        rows = txn.aql.execute(
            """
        FOR l IN @@locations
            FILTER (l._key IN @covered OR l.site_key == @site_key) AND l.irrigation_zone_key == @zone_key
            FILTER l._key NOT IN @keep
            UPDATE l WITH { irrigation_zone_key: null, updated_at: @now } IN @@locations OPTIONS { keepNull: false }
            RETURN OLD._key
        """,
            bind_vars={
                "@locations": col.LOCATIONS,
                "covered": covered,
                "site_key": site_key,
                "zone_key": zone_key,
                "keep": keep,
                "now": now,
            },
        )
        return sorted(str(key) for key in rows)

    @staticmethod
    def _take_water_source(txn: StreamTransaction, object_key: str, site_key: str, tenant_key: str, now: str) -> None:
        """The water source still exists on the zone's site under the tenant — else 422 ``reference.not_found``."""
        taken = list(
            txn.aql.execute(
                _TAKE_WATER_SOURCE,
                bind_vars={
                    "@objects": col.GARDEN_OBJECTS,
                    "sites": f"{col.SITES}/",
                    "key": object_key,
                    "site_key": site_key,
                    "tenant_key": tenant_key,
                    "now": now,
                },
            )
        )
        if not taken:
            raise PlanValidationError([(None, "water_source_key", ERROR_REFERENCE_NOT_FOUND, {})])

    @staticmethod
    def _link_water_source(txn: StreamTransaction, zone_id: str, object_key: str, now: str) -> None:
        txn.collection(col.ZONE_SUPPLIED_BY).insert(
            {"_from": zone_id, "_to": f"{col.GARDEN_OBJECTS}/{object_key}", "created_at": now}
        )

    @staticmethod
    def _remove_edges(txn: StreamTransaction, edge_collection: str, field: str, ids: list[str]) -> None:
        # ``field`` is ``_from`` or ``_to`` from the edge derivation above — never a request value.
        txn.aql.execute(
            f"FOR e IN @@edges FILTER e.{aql_field(field)} IN @ids REMOVE e IN @@edges",
            bind_vars={"@edges": edge_collection, "ids": ids},
        )
