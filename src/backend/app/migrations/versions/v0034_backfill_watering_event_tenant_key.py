"""v0034 — backfill tenant_key on confirm-produced watering/feeding rows and batch plants (#951).

Three write paths built their documents without a ``tenant_key`` although the
model carries the field and the caller's tenant was available:

* ``WateringService.confirm_watering`` — the ``WateringEvent`` and every derived
  ``FeedingEvent`` (``domain/services/watering_service.py``). This is a live UI
  path: ``WateringConfirmDialog`` and ``PlantingRunDetailPage`` both reach it.
* ``PlantingRunService.create_plants`` — every batch-created ``PlantInstance``,
  although ``run.tenant_key`` was right there.

All three persisted with the model default ``tenant_key == ""``. That stayed
invisible for as long as nothing filtered on the field; #947 added the predicate
to ``get_by_plant``/``get_by_location``/``get_stats_by_location``, at which point
the confirm-produced rows fall out of every one of those reads — a confirmation
made through the UI would stop appearing in the plant's watering history. The
batch plants were already invisible to every tenant-scoped plant read. The twin
``WateringLogService.confirm_watering`` was fixed under #580 with migration
``v0020``; this is the same repair for the rows that path's siblings left behind.

The code fix stamps the tenant at each construction site. This migration repairs
history, in dependency order because the later stages resolve *through* the
earlier ones:

1. ``plant_instances`` — bound to their run's tenant via the ``RUN_CONTAINS``
   edge (PlantingRun → PlantInstance).
2. ``watering_events`` — bound to their plant's tenant via the ``WATERED_PLANT``
   edge (WateringEvent → PlantInstance), with the embedded ``plant_keys`` array
   as a fallback when the edge is missing. Plants repaired in stage 1 count.
3. ``feeding_events`` — bound via their own ``plant_key``, falling back to the
   ``watering_event_key`` they were derived from (stage 2 counts).

Idempotent (M-3): after a run no resolvable row is left, so a re-run finds only
the unresolvable remainder and writes nothing (``changed == 0``). A row whose
references are all gone is left untouched and reported under ``unresolved``
rather than guessed at, so a later run retries it once the reference resolves.
Dry-run (M-5) computes the full plan — including what the earlier stages would
have made resolvable — and writes nothing. Irreversible (M-6): the pre-fix empty
``tenant_key`` is not recoverable, so there is no honest inverse.
"""

from __future__ import annotations

from typing import Any

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger()

#: ``{"key": …, "tenant_key": …}`` pairs ready for a batched UPDATE.
type UpdatePairs = list[dict[str, str]]


class BackfillWateringEventTenantKeyMigration(Migration):
    version = "0034"
    name = "backfill_watering_event_tenant_key"
    description = "Bind empty-tenant batch plants, watering events and feeding events to their owning tenant (#951)."
    reversible = False

    # ── read helpers (no-op-safe on an empty/fresh database) ──────────────────

    def _tenantless(
        self,
        db: StandardDatabase,
        collection: str,
        projection: tuple[str, ...] = (),
    ) -> list[dict[str, Any]]:
        """Every document of ``collection`` still missing a tenant_key (read-only).

        ``projection`` names the extra document fields the caller needs to resolve
        the owner. They are code-level literals from this module, never caller
        input, so interpolating them into the ``RETURN`` clause is safe; the
        collection itself is bound as ``@@collection``.
        """
        if not db.has_collection(collection):
            return []
        extra = "".join(f", {field}: doc.{field}" for field in projection)
        return list(
            db.aql.execute(
                "FOR doc IN @@collection "
                "FILTER doc.tenant_key == null OR doc.tenant_key == '' "
                f"RETURN {{key: doc._key, id: doc._id{extra}}}",
                bind_vars={"@collection": collection},
            )
        )

    def _tenant_via_edge(
        self,
        db: StandardDatabase,
        edge_collection: str,
        *,
        doc_id: str,
        direction: str,
    ) -> str | None:
        """First non-empty ``tenant_key`` of the vertex on the other end of an edge.

        ``direction`` is ``"outbound"`` when ``doc_id`` is the edge's ``_from``
        (WateringEvent → PlantInstance) and ``"inbound"`` when it is the ``_to``
        (PlantingRun → PlantInstance).
        """
        if not db.has_collection(edge_collection):
            return None
        near, far = ("_from", "_to") if direction == "outbound" else ("_to", "_from")
        rows = db.aql.execute(
            f"FOR edge IN @@edges FILTER edge.{near} == @doc_id "
            f"LET other = DOCUMENT(edge.{far}) "
            "FILTER other != null AND other.tenant_key != null AND other.tenant_key != '' "
            "RETURN other.tenant_key",
            bind_vars={"@edges": edge_collection, "doc_id": doc_id},
        )
        for tenant_key in rows:
            return tenant_key
        return None

    def _plant_tenant(self, db: StandardDatabase, plant_key: str, planned: dict[str, str]) -> str | None:
        """A plant's tenant, counting what stage 1 has planned but not yet written."""
        if not plant_key:
            return None
        if plant_key in planned:
            return planned[plant_key]
        if not db.has_collection(col.PLANT_INSTANCES):
            return None
        plant = db.collection(col.PLANT_INSTANCES).get(plant_key)
        if plant and plant.get("tenant_key"):
            return plant["tenant_key"]
        return None

    # ── stage planning ────────────────────────────────────────────────────────

    def _plan_plants(self, db: StandardDatabase) -> tuple[UpdatePairs, int]:
        """Batch-created instances → their run's tenant, via ``RUN_CONTAINS``."""
        updates: UpdatePairs = []
        unresolved = 0
        for plant in self._tenantless(db, col.PLANT_INSTANCES):
            tenant_key = self._tenant_via_edge(db, col.RUN_CONTAINS, doc_id=plant["id"], direction="inbound")
            if tenant_key:
                updates.append({"key": plant["key"], "tenant_key": tenant_key})
            else:
                unresolved += 1
        return updates, unresolved

    def _plan_watering_events(self, db: StandardDatabase, plant_tenants: dict[str, str]) -> tuple[UpdatePairs, int]:
        """Confirm-produced events → their plant's tenant, via ``WATERED_PLANT``."""
        updates: UpdatePairs = []
        unresolved = 0
        for event in self._tenantless(db, col.WATERING_EVENTS, ("plant_keys",)):
            tenant_key = self._tenant_via_edge(db, col.WATERED_PLANT, doc_id=event["id"], direction="outbound")
            if tenant_key is None:
                # The edge may be missing (or point at a plant stage 1 is about to
                # repair); the embedded array carries the same references.
                for plant_key in event.get("plant_keys") or []:
                    tenant_key = self._plant_tenant(db, plant_key, plant_tenants)
                    if tenant_key:
                        break
            if tenant_key:
                updates.append({"key": event["key"], "tenant_key": tenant_key})
            else:
                unresolved += 1
        return updates, unresolved

    def _plan_feeding_events(
        self,
        db: StandardDatabase,
        plant_tenants: dict[str, str],
        event_tenants: dict[str, str],
    ) -> tuple[UpdatePairs, int]:
        """Derived feeding events → their plant's tenant, else their watering event's."""
        updates: UpdatePairs = []
        unresolved = 0
        for feeding in self._tenantless(db, col.FEEDING_EVENTS, ("plant_key", "watering_event_key")):
            tenant_key = self._plant_tenant(db, feeding.get("plant_key") or "", plant_tenants)
            if not tenant_key:
                event_key = feeding.get("watering_event_key") or ""
                if event_key in event_tenants:
                    tenant_key = event_tenants[event_key]
                elif event_key and db.has_collection(col.WATERING_EVENTS):
                    event = db.collection(col.WATERING_EVENTS).get(event_key)
                    tenant_key = event.get("tenant_key") if event else None
            if tenant_key:
                updates.append({"key": feeding["key"], "tenant_key": tenant_key})
            else:
                unresolved += 1
        return updates, unresolved

    # ── apply ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _apply(db: StandardDatabase, collection: str, updates: UpdatePairs) -> None:
        if not updates:
            return
        db.aql.execute(
            "FOR pair IN @pairs UPDATE {_key: pair.key, tenant_key: pair.tenant_key} IN @@collection",
            bind_vars={"pairs": updates, "@collection": collection},
        )

    # ── entry point ───────────────────────────────────────────────────────────

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        plant_updates, plants_unresolved = self._plan_plants(db)
        plant_tenants = {pair["key"]: pair["tenant_key"] for pair in plant_updates}
        if not dry_run:
            self._apply(db, col.PLANT_INSTANCES, plant_updates)

        event_updates, events_unresolved = self._plan_watering_events(db, plant_tenants)
        event_tenants = {pair["key"]: pair["tenant_key"] for pair in event_updates}
        if not dry_run:
            self._apply(db, col.WATERING_EVENTS, event_updates)

        feeding_updates, feedings_unresolved = self._plan_feeding_events(db, plant_tenants, event_tenants)
        if not dry_run:
            self._apply(db, col.FEEDING_EVENTS, feeding_updates)

        changed = len(plant_updates) + len(event_updates) + len(feeding_updates)
        unresolved = plants_unresolved + events_unresolved + feedings_unresolved
        details = {
            "plant_instances": len(plant_updates),
            "watering_events": len(event_updates),
            "feeding_events": len(feeding_updates),
            "unresolved": unresolved,
        }

        logger.info(
            "backfill_watering_event_tenant_key_dry_run" if dry_run else "backfill_watering_event_tenant_key_applied",
            scanned=changed + unresolved,
            changed=0 if dry_run else changed,
            to_update=changed,
            unresolved=unresolved,
        )
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=changed + unresolved,
            changed=0 if dry_run else changed,
            dry_run=dry_run,
            details={"to_update": changed, **details} if dry_run else details,
        )


migration = BackfillWateringEventTenantKeyMigration()
