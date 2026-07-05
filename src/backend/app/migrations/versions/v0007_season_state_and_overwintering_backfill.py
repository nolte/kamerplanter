"""v0007 — REQ-047 overwintering-profile backfill.

Stamps the REQ-047 additive fields on existing ``overwintering_profiles``
(REQ-047 §2.3 / §5): ``user_overridden`` is set to ``auto_generated == false``
(manually curated profiles keep precedence), and ``derived_path`` is derived from
the stored ``hardiness_rating`` via the winter hardiness ampel where the rating
maps unambiguously.

The ``season_states`` collection and the ``has_season_state`` edge are created by
the idempotent startup ``ensure_collections`` (which the migration framework runs
before the seeds), so no structural step is needed here — this migration is a pure,
additive data backfill.

Only documents missing ``user_overridden`` are touched (``FILTER doc.user_overridden
== null``); re-running is a no-op (M-3). Purely additive — no data is lost or
overwritten (M-6, irreversible: the pre-migration state carried no such signal).
"""

from __future__ import annotations

import structlog
from arango.database import StandardDatabase

from app.common.enums import HardinessRating
from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger()

#: Ratings that map to the relocated winter path (D5 path B); everything else
#: (hardy / needs_protection) is the in-situ path A.
_PATH_B_RATINGS = {HardinessRating.FROST_FREE.value, HardinessRating.DIG_AND_STORE.value}


class SeasonStateAndOverwinteringBackfillMigration(Migration):
    version = "0007"
    name = "season_state_and_overwintering_backfill"
    description = "Backfill overwintering user_overridden/derived_path for REQ-047."
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        rows = list(
            db.aql.execute(
                f"FOR d IN {col.OVERWINTERING_PROFILES} "
                f"FILTER d.user_overridden == null "
                f"RETURN {{key: d._key, auto_generated: d.auto_generated, hardiness_rating: d.hardiness_rating}}"
            )
        )
        scanned = len(rows)

        updates: list[dict] = []
        for row in rows:
            rating = row.get("hardiness_rating")
            derived_path = None
            if rating is not None:
                derived_path = "B" if rating in _PATH_B_RATINGS else "A"
            updates.append(
                {
                    "_key": row["key"],
                    "user_overridden": not bool(row.get("auto_generated")),
                    "derived_path": derived_path,
                }
            )

        if dry_run:
            logger.info("season_backfill_dry_run", scanned=scanned)
            return MigrationReport(
                version=self.version,
                name=self.name,
                scanned=scanned,
                changed=0,
                dry_run=True,
            )

        changed = 0
        if updates:
            db.aql.execute(
                "FOR u IN @updates "
                "UPDATE {_key: u._key, user_overridden: u.user_overridden, derived_path: u.derived_path} "
                "IN @@collection",
                bind_vars={"updates": updates, "@collection": col.OVERWINTERING_PROFILES},
            )
            changed = len(updates)

        logger.info("season_backfill_applied", scanned=scanned, changed=changed)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=scanned,
            changed=changed,
            dry_run=False,
        )


migration = SeasonStateAndOverwinteringBackfillMigration()
