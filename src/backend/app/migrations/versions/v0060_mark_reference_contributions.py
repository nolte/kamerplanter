"""v0060 — record that user contributions may already exist in the recognition index.

#1753 introduced ``system_settings.reference_contributions_since``: the
contribution path (``ReferenceImageService.contribute_user_reference``) sets it
before every write, and the no-op reference-index store refuses to report
"nothing to delete" while it is set — so a process without
``INFERENCE_SERVICE_ENABLED`` (typically the celery-worker running the
scheduled Art. 17 erasure) holds the erasure instead of skipping the vectors.
Deployments that accepted contributions *before* #1753 have no marker; this
migration backfills it.

**This is a heuristic.** The migration cannot ask the inference-service whether
contributed rows exist. It uses the one fact available in the migrating
process: migrations run in the backend's lifespan, and the backend has accepted
contributions exactly while ``inference_service_enabled`` was set — the
contribution route (``POST /t/{slug}/identification/reference``, live since
#447) refuses otherwise. So:

* flag set here → the marker is set (when absent). A false positive — the flag
  was on but nobody contributed — only makes a flagless worker hold erasures
  loudly with an operator hint; it never deletes or keeps anything wrongly.
* flag unset here → nothing is marked. A deployment that had the flag on, took
  contributions and switched it off before upgrading is **not** caught; the
  marker appears with the next contribution after the flag is re-enabled.

* **Atomic, only when absent:** one ``UPSERT`` that writes only
  ``reference_contributions_since`` and only while it is ``null``; the other
  settings on the singleton are untouched (same statement semantics as
  ``ArangoSystemSettingsRepository.record_reference_contributions``, copied so
  this applied migration stays frozen).
* **Idempotent (M-3):** a present marker is left alone; a re-run changes nothing.
* **Not reversible (M-6):** after the run, a marker set here and one set by a
  contribution are indistinguishable; removing it could drop a real one.
* **Dry run (M-5):** reports whether it would mark, writes nothing.
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
_FIELD = "reference_contributions_since"


class MarkReferenceContributionsMigration(Migration):
    version = "0060"
    name = "mark_reference_contributions"
    description = (
        "Record that user reference contributions may exist when the backend runs with the "
        "inference-service enabled, so a flagless worker holds erasures instead of skipping them (#1753)."
    )
    reversible = False

    _MARK_QUERY = """
    UPSERT { _key: @key }
    INSERT { _key: @key, reference_contributions_since: @now, created_at: @now, updated_at: @now }
    UPDATE {
      reference_contributions_since: OLD.reference_contributions_since == null
        ? @now : OLD.reference_contributions_since
    }
    IN @@collection
    """

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        from app.config.settings import settings

        reason: str | None = None
        if not settings.inference_service_enabled:
            reason = "inference_service_disabled"
        elif db.has_collection(col.SYSTEM_SETTINGS):
            doc = db.collection(col.SYSTEM_SETTINGS).get(_SINGLETON_KEY)
            if doc is not None and doc.get(_FIELD) is not None:
                reason = "marker_present"

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

        logger.info("mark_reference_contributions", marked=marked, reason=reason, dry_run=dry_run)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=1,
            changed=1 if marked and not dry_run else 0,
            dry_run=dry_run,
            details={"marked": marked, "reason": reason},
        )


migration = MarkReferenceContributionsMigration()
