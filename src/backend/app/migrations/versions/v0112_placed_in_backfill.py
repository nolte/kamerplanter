"""v0112 — #2952: the ``placed_in`` edge of every plant moved onto its slot before #2948.

**Why.** Before #2948 ``ArangoPlantInstanceRepository.update`` changed ``plant.slot_key`` without writing a
``placed_in`` edge to the new slot. Every *current-occupancy* reader selects by ``slot_key`` since #2951 and sees
those plants; the crop-rotation history (``get_history_by_slot``) still reads the edges and misses them, so a
rotation check on the slot a plant was moved onto knows nothing of that plant.

**What.** For every plant whose ``slot_key`` names a slot it has no ``placed_in`` edge to, one edge
``plant_instances/<plant> -> slots/<slot_key>`` is inserted. That is exactly what a move writes since #2948:
the new slot gets an edge, the edge to a slot the plant left stays (it is that slot's history) and no edge is closed
or changed - an edge carries no time window, only ``created_at``. A removed plant (``removed_on`` set) is included:
it stood on its last slot, and the history is what this repairs.

**When it was placed.** No move time is recorded anywhere (the plant has no move field, the move wrote no edge), so
the edge's ``created_at`` is the best known lower bound: the plant's own ``created_at``, else its ``planted_on`` at
midnight UTC, else the run's time. No reader orders by it (the history filters on the plant's ``planted_on``).

**Never across tenants (#706).** ``Location`` and ``Slot`` carry no ``tenant_key`` (v0087); the tenant of a slot is
its anchoring site's (``slot.location_key -> location.site_key -> site.tenant_key``). An edge is only inserted when
that chain resolves and the site belongs to the plant's own tenant. Everything else is counted and listed (first
:attr:`PlacedInBackfillMigration.LISTED` plant keys) under its reason and left alone: ``slot_missing``,
``slot_without_location``, ``location_missing``, ``location_without_site``, ``site_missing``,
``site_without_tenant`` (legacy data: a site without its tenant stamp) and ``cross_tenant`` (the plant has no
tenant, or the site is another tenant's).

**Consistent against a live writer.** The insert re-reads the plant and the edges: a plant whose ``slot_key``
or tenant changed since the scan, or that meanwhile got the edge (a move through ``update``), is skipped.
``inserted`` (and the report's ``changed``) counts the edges actually written, ``skipped_changed_since_scan``
the planned ones a writer touched in between.

**Idempotent (M-3).** The scan only matches plants without an edge to their slot; after a run the repaired ones no
longer match, a second run finds the unresolvable remainder and inserts nothing.

**Dry run (M-5).** Counts only: ``will_insert`` plus the unresolved plants per reason, nothing written.

**Reversible (M-6).** Every inserted edge carries ``backfilled_by = "v0112"``; ``down`` removes exactly those and
no edge a writer made. A downgrade puts the affected plants back into the pre-#2948 state.

**Frozen (M-7).** Collection names, marker and queries are literals on the class, so the checksum covers them and a
later rename of a ``collections`` constant does not change what this version did.
"""

from __future__ import annotations

from datetime import UTC, datetime
from numbers import Number
from typing import Any, cast

import structlog
from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)


class PlacedInBackfillMigration(Migration):
    version = "0112"
    name = "placed_in_backfill"
    description = (
        "#2952: insert the missing placed_in edge of every plant whose slot_key names a slot it has no edge to "
        "(moved before #2948); same-tenant only, marked backfilled_by=v0112 so down removes exactly those."
    )
    reversible = True

    #: Frozen collection names (M-7) - the ``collections`` constants at this version.
    PLANTS = "plant_instances"
    SLOTS = "slots"
    LOCATIONS = "locations"
    SITES = "sites"
    EDGES = "placed_in"

    #: The marker on every edge this version inserts; ``down`` removes by it.
    MARKER = "v0112"

    #: Plant keys a report lists per reason before it only counts.
    LISTED = 25
    #: Edges per insert statement, and scan rows per cursor batch.
    BATCH_SIZE = 500
    #: Seconds the server keeps the scan cursor between two fetches (an insert batch runs in between).
    CURSOR_TTL_SECONDS = 600

    #: Plants with a slot and no edge to it, with what the tenant check needs. Non-streaming: the server fixes the
    #: result before the first batch, so the inserts applied while reading never change which rows it yields.
    SCAN = """
    FOR p IN @@plants
      FILTER p.slot_key != null AND p.slot_key != ""
      LET slot_id = CONCAT(@slots, "/", p.slot_key)
      FILTER LENGTH(FOR e IN @@edges FILTER e._from == p._id AND e._to == slot_id LIMIT 1 RETURN 1) == 0
      SORT p._key
      LET slot = DOCUMENT(@slots, p.slot_key)
      LET location_key = slot == null ? null : slot.location_key
      LET location = location_key == null OR location_key == "" ? null : DOCUMENT(@locations, location_key)
      LET site_key = location == null ? null : location.site_key
      LET site = site_key == null OR site_key == "" ? null : DOCUMENT(@sites, site_key)
      RETURN {
        key: p._key,
        tenant_key: p.tenant_key,
        slot_key: p.slot_key,
        created_at: p.created_at,
        planted_on: p.planted_on,
        slot_found: slot != null,
        location_key: location_key,
        location_found: location != null,
        site_key: site_key,
        site_found: site != null,
        site_tenant_key: site == null ? null : site.tenant_key
      }
    """

    #: Re-reads plant and edges per planned row; inserts only while the plant still names the slot, still belongs
    #: to the tenant the check passed for and has no edge to it. Returns the number of edges written.
    APPLY = """
    FOR u IN @rows
      LET plant = DOCUMENT(@plants_name, u.plant_key)
      FILTER plant != null AND plant.slot_key == u.slot_key AND plant.tenant_key == u.tenant_key
      FILTER LENGTH(FOR e IN @@edges FILTER e._from == u.from_id AND e._to == u.to_id LIMIT 1 RETURN 1) == 0
      INSERT { _from: u.from_id, _to: u.to_id, created_at: u.created_at, backfilled_by: @marker } INTO @@edges
      COLLECT WITH COUNT INTO inserted
      RETURN inserted
    """

    COUNT_MARKED = """
    FOR e IN @@edges
      FILTER e.backfilled_by == @marker
      COLLECT WITH COUNT INTO marked
      RETURN marked
    """

    REMOVE_MARKED = """
    FOR e IN @@edges
      FILTER e.backfilled_by == @marker
      REMOVE e IN @@edges
      COLLECT WITH COUNT INTO removed
      RETURN removed
    """

    @staticmethod
    def reason(row: dict[str, Any]) -> str | None:
        """Why no edge may be inserted for the scanned plant (``None`` = it may)."""
        if not row.get("slot_found"):
            return "slot_missing"
        if not row.get("location_key"):
            return "slot_without_location"
        if not row.get("location_found"):
            return "location_missing"
        if not row.get("site_key"):
            return "location_without_site"
        if not row.get("site_found"):
            return "site_missing"
        plant_tenant = row.get("tenant_key")
        if not plant_tenant:
            return "cross_tenant"
        site_tenant = row.get("site_tenant_key")
        if not site_tenant:
            return "site_without_tenant"
        if site_tenant != plant_tenant:
            return "cross_tenant"
        return None

    @staticmethod
    def placed_at(row: dict[str, Any], now: datetime) -> str:
        """The best known placement time: the plant's ``created_at``, else ``planted_on`` at midnight UTC, else now."""
        created_at = row.get("created_at")
        if isinstance(created_at, str) and created_at:
            return created_at
        planted_on = row.get("planted_on")
        if isinstance(planted_on, str) and len(planted_on) >= 10:
            try:
                day = datetime.fromisoformat(planted_on[:10])
            except ValueError:
                pass
            else:
                return day.replace(tzinfo=UTC).isoformat()
        return now.isoformat()

    @classmethod
    def plan(cls, row: dict[str, Any], now: datetime) -> dict[str, Any]:
        """The insert for a scanned plant :meth:`reason` cleared."""
        return {
            "plant_key": str(row["key"]),
            "slot_key": row["slot_key"],
            "tenant_key": row["tenant_key"],
            "from_id": f"{cls.PLANTS}/{row['key']}",
            "to_id": f"{cls.SLOTS}/{row['slot_key']}",
            "created_at": cls.placed_at(row, now),
        }

    def _scan(self, db: StandardDatabase) -> Cursor:
        return cast(
            Cursor,
            db.aql.execute(
                self.SCAN,
                bind_vars={
                    "@plants": self.PLANTS,
                    "@edges": self.EDGES,
                    "slots": self.SLOTS,
                    "locations": self.LOCATIONS,
                    "sites": self.SITES,
                },
                batch_size=self.BATCH_SIZE,
                # python-arango annotates ``ttl`` as ``numbers.Number``, which ``int`` is only at runtime
                ttl=cast(Number, self.CURSOR_TTL_SECONDS),
                stream=False,
            ),
        )

    def _apply(self, db: StandardDatabase, batch: list[dict[str, Any]]) -> int:
        cursor = cast(
            Cursor,
            db.aql.execute(
                self.APPLY,
                bind_vars={
                    "@edges": self.EDGES,
                    "plants_name": self.PLANTS,
                    "rows": batch,
                    "marker": self.MARKER,
                },
            ),
        )
        return sum(int(inserted) for inserted in cursor)

    def _count(self, db: StandardDatabase, query: str) -> int:
        cursor = cast(Cursor, db.aql.execute(query, bind_vars={"@edges": self.EDGES, "marker": self.MARKER}))
        return sum(int(count) for count in cursor)

    def _ready(self, db: StandardDatabase) -> bool:
        return bool(db.has_collection(self.PLANTS) and db.has_collection(self.EDGES))

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        if not self._ready(db):
            return MigrationReport(
                version=self.version, name=self.name, scanned=0, changed=0, dry_run=dry_run, details={}
            )
        now = datetime.now(UTC)
        scanned = planned = inserted = 0
        listed_keys: list[str] = []
        unresolved: dict[str, dict[str, Any]] = {}
        batch: list[dict[str, Any]] = []
        for row in self._scan(db):
            scanned += 1
            why = self.reason(row)
            if why is not None:
                bucket = unresolved.setdefault(why, {"count": 0, "listed": []})
                bucket["count"] += 1
                if len(bucket["listed"]) < self.LISTED:
                    bucket["listed"].append(str(row["key"]))
                continue
            planned += 1
            if len(listed_keys) < self.LISTED:
                listed_keys.append(str(row["key"]))
            if not dry_run:
                batch.append(self.plan(row, now))
                if len(batch) >= self.BATCH_SIZE:
                    inserted += self._apply(db, batch)
                    batch = []
        if batch:
            inserted += self._apply(db, batch)
        details: dict[str, Any] = {
            "scanned_without_edge_to_slot": scanned,
            "listed_keys": listed_keys,
            "unresolved": unresolved,
            "unresolved_count": sum(b["count"] for b in unresolved.values()),
        }
        if dry_run:
            details["will_insert"] = planned
            logger.info("placed_in_backfill_dry_run", scanned=scanned, will_insert=planned)
            return MigrationReport(
                version=self.version, name=self.name, scanned=scanned, changed=0, dry_run=True, details=details
            )
        details["inserted"] = inserted
        details["skipped_changed_since_scan"] = planned - inserted
        logger.info("placed_in_backfill_applied", scanned=scanned, inserted=inserted)
        return MigrationReport(
            version=self.version, name=self.name, scanned=scanned, changed=inserted, dry_run=False, details=details
        )

    def down(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        """Remove exactly the edges :meth:`up` inserted (``backfilled_by == "v0112"``)."""
        if not self._ready(db):
            return MigrationReport(
                version=self.version, name=self.name, scanned=0, changed=0, dry_run=dry_run, details={}
            )
        if dry_run:
            marked = self._count(db, self.COUNT_MARKED)
            return MigrationReport(
                version=self.version,
                name=self.name,
                scanned=marked,
                changed=0,
                dry_run=True,
                details={"will_remove": marked},
            )
        removed = self._count(db, self.REMOVE_MARKED)
        logger.info("placed_in_backfill_reverted", removed=removed)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=removed,
            changed=removed,
            dry_run=False,
            details={"removed": removed},
        )


migration = PlacedInBackfillMigration()
