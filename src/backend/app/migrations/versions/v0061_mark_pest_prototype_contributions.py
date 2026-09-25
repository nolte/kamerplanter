"""v0061 — record that contributed pest prototypes may already be in the recognition index.

#1759 introduced ``system_settings.pest_prototype_contributions_since``: the
promotion index task (``app/tasks/pest_image_tasks.py``) sets it before every
upsert into the inference-service's ``pest_embeddings``, and the no-op
pest-prototype store refuses to report "nothing to delete" while it is set — so
a process that reaches no inference-service holds the erasure instead of
leaving the prototypes behind. Deployments that indexed promotions *before*
#1759 have no marker; this migration backfills it.

**A heuristic, like v0060.** The migration cannot ask the inference-service.
It marks when both facts available here hold:

* the migrating process (the backend) has ``pest_detection_enabled`` or
  ``inference_service_enabled`` set — without either no process of this
  deployment is expected to have reached the index; and
* at least one ``pest_image_contributions`` document carries ``promoted_at`` —
  only a promotion triggers the index task.

A false positive only makes a process without the flags hold erasures loudly
with an operator hint. A deployment that switched both flags off before
upgrading is not caught; the marker appears with the next indexed promotion.

* **Atomic, only when absent:** one ``UPSERT`` writing only this field, only
  while it is ``null`` (the statement of
  ``ArangoSystemSettingsRepository.record_pest_prototype_contributions``,
  copied so this applied migration stays frozen).
* **Idempotent (M-3), not reversible (M-6), dry run (M-5)** — as v0060.
"""

from __future__ import annotations

from datetime import UTC, datetime

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)

_SINGLETON_KEY = "default"
_FIELD = "pest_prototype_contributions_since"


class MarkPestPrototypeContributionsMigration(Migration):
    version = "0061"
    name = "mark_pest_prototype_contributions"
    description = (
        "Record that promoted pest-image contributions may have been indexed as recognition prototypes, "
        "so a process without the inference-service holds erasures instead of skipping them (#1759)."
    )
    reversible = False

    _ANY_PROMOTED_QUERY = """
    RETURN LENGTH(FOR c IN @@collection FILTER c.promoted_at != null LIMIT 1 RETURN 1) > 0
    """

    _MARK_QUERY = """
    UPSERT { _key: @key }
    INSERT { _key: @key, pest_prototype_contributions_since: @now, created_at: @now, updated_at: @now }
    UPDATE {
      pest_prototype_contributions_since: OLD.pest_prototype_contributions_since == null
        ? @now : OLD.pest_prototype_contributions_since
    }
    IN @@collection
    """

    def _any_promoted(self, db: StandardDatabase) -> bool:
        if not db.has_collection(col.PEST_IMAGE_CONTRIBUTIONS):
            return False
        cursor = db.aql.execute(self._ANY_PROMOTED_QUERY, bind_vars={"@collection": col.PEST_IMAGE_CONTRIBUTIONS})
        return bool(next(iter(cursor), False))

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        from app.config.settings import settings

        reason: str | None = None
        if not (settings.pest_detection_enabled or settings.inference_service_enabled):
            reason = "inference_service_unreachable_from_backend"
        elif db.has_collection(col.SYSTEM_SETTINGS) and (
            (doc := db.collection(col.SYSTEM_SETTINGS).get(_SINGLETON_KEY)) is not None and doc.get(_FIELD) is not None
        ):
            reason = "marker_present"
        elif not self._any_promoted(db):
            reason = "no_promoted_contribution"

        marked = reason is None
        if marked and not dry_run:
            if not db.has_collection(col.SYSTEM_SETTINGS):
                db.create_collection(col.SYSTEM_SETTINGS)
            db.aql.execute(
                self._MARK_QUERY,
                bind_vars={
                    "@collection": col.SYSTEM_SETTINGS,
                    "key": _SINGLETON_KEY,
                    "now": datetime.now(UTC).isoformat(),
                },
            )

        logger.info("mark_pest_prototype_contributions", marked=marked, reason=reason, dry_run=dry_run)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=1,
            changed=1 if marked and not dry_run else 0,
            dry_run=dry_run,
            details={"marked": marked, "reason": reason},
        )


migration = MarkPestPrototypeContributionsMigration()
