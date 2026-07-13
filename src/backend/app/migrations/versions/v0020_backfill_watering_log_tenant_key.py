"""v0020 — backfill tenant_key on care/task-produced watering logs (#580).

Bug #580 (bug/security): watering logs created from the care-reminder and
task-completion paths were constructed WITHOUT a ``tenant_key`` and therefore
persisted with the model default ``tenant_key == ""``. The global
``GET /watering-logs`` view filters strictly on ``tenant_key`` and silently
dropped these empty-tenant orphans, so a watering logged via a Pflege-/Task-flow
never appeared in the tenant's global Gießprotokoll (while the per-plant view,
which did not filter, still showed them — a confusing divergence).

The code fix stamps ``tenant_key`` at every construction site. This migration
repairs the historical rows: every ``watering_logs`` document still carrying an
empty/absent ``tenant_key`` is bound to its plant's tenant, resolved through the
``LOG_PLANT`` edge (WateringLog -> PlantInstance) with the embedded
``plant_keys`` array as a fallback. The first plant that resolves to a non-empty
``tenant_key`` wins — care/task logs reference exactly one plant, so this is
unambiguous in practice.

Idempotent (M-3): after the first run no empty-tenant log remains, so a re-run
finds nothing and is a no-op (``changed == 0``). A log whose plants are all
gone/unresolvable is left untouched (reported under ``unresolved``) rather than
guessed — a later run retries it once the reference resolves. Dry-run (M-5)
computes the full plan and writes nothing. Irreversible (M-6): the pre-fix empty
tenant_key is not recoverable, so there is no honest inverse.
"""

from __future__ import annotations

from typing import Any

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger()


class BackfillWateringLogTenantKeyMigration(Migration):
    version = "0020"
    name = "backfill_watering_log_tenant_key"
    description = "Bind empty-tenant watering logs to their plant's tenant via LOG_PLANT (#580)."
    reversible = False

    # ── read helpers (no-op-safe on an empty/fresh database) ──────────────────

    def _orphaned_logs(self, db: StandardDatabase) -> list[dict[str, Any]]:
        """Every watering log still missing a tenant_key (read-only, M-5-safe)."""
        if not db.has_collection(col.WATERING_LOGS):
            return []
        return list(
            db.aql.execute(
                "FOR log IN @@collection "
                "FILTER log.tenant_key == null OR log.tenant_key == '' "
                "RETURN {key: log._key, id: log._id, plant_keys: log.plant_keys}",
                bind_vars={"@collection": col.WATERING_LOGS},
            )
        )

    def _resolve_tenant_key(self, db: StandardDatabase, log: dict[str, Any]) -> str | None:
        """Resolve a log's owning tenant from its plant references.

        Primary: the ``LOG_PLANT`` edge (WateringLog -> PlantInstance). Fallback:
        the embedded ``plant_keys`` array (present even if an edge is missing).
        Returns the first non-empty plant ``tenant_key``, or ``None`` when no
        referenced plant resolves to a tenant (the log is then left untouched).
        """
        if db.has_collection(col.LOG_PLANT):
            rows = db.aql.execute(
                "FOR edge IN @@log_plant "
                "FILTER edge._from == @log_id "
                "LET plant = DOCUMENT(edge._to) "
                "FILTER plant != null AND plant.tenant_key != null AND plant.tenant_key != '' "
                "RETURN plant.tenant_key",
                bind_vars={"@log_plant": col.LOG_PLANT, "log_id": log["id"]},
            )
            for tenant_key in rows:
                return tenant_key

        if db.has_collection(col.PLANT_INSTANCES):
            plants = db.collection(col.PLANT_INSTANCES)
            for plant_key in log.get("plant_keys") or []:
                plant = plants.get(plant_key)
                if plant and plant.get("tenant_key"):
                    return plant["tenant_key"]
        return None

    def _plan(self, db: StandardDatabase) -> tuple[list[dict[str, str]], int]:
        """Return (updates, unresolved_count) for the orphaned logs.

        ``updates`` are ``{"key", "tenant_key"}`` pairs ready for a batched UPDATE;
        ``unresolved_count`` counts orphaned logs whose plants yield no tenant.
        """
        updates: list[dict[str, str]] = []
        unresolved = 0
        for log in self._orphaned_logs(db):
            tenant_key = self._resolve_tenant_key(db, log)
            if tenant_key:
                updates.append({"key": log["key"], "tenant_key": tenant_key})
            else:
                unresolved += 1
        return updates, unresolved

    # ── entry point ───────────────────────────────────────────────────────────

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        updates, unresolved = self._plan(db)
        scanned = len(updates) + unresolved

        if dry_run:
            logger.info(
                "backfill_watering_log_tenant_key_dry_run",
                scanned=scanned,
                to_update=len(updates),
                unresolved=unresolved,
            )
            return MigrationReport(
                version=self.version,
                name=self.name,
                scanned=scanned,
                changed=0,
                dry_run=True,
                details={"to_update": len(updates), "unresolved": unresolved},
            )

        if updates:
            db.aql.execute(
                "FOR pair IN @pairs UPDATE {_key: pair.key, tenant_key: pair.tenant_key} IN @@collection",
                bind_vars={"pairs": updates, "@collection": col.WATERING_LOGS},
            )

        logger.info(
            "backfill_watering_log_tenant_key_applied",
            scanned=scanned,
            changed=len(updates),
            unresolved=unresolved,
        )
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=scanned,
            changed=len(updates),
            dry_run=False,
            details={"updated": len(updates), "unresolved": unresolved},
        )


migration = BackfillWateringLogTenantKeyMigration()
