"""v0107 — replace erased-account tombstones in ``care_events.performed_by_user_key`` with the marker (#2770).

**Why.** After an account erasure the domain events keep the account's tombstone hash (``anon_<16hex>``,
``ErasureEngine.compute_tombstone_hash``) in ``harvested_by_key`` / ``applied_by_key``. The M4 backfill (v0104) and
the daily consistency job copied that value as ``performed_by_user_key``, where GP-NFR-055 wants the fixed
``_anonymized`` marker. The copy stays linkable for the five-year care-log retention, and the care-log erasure rule
(which matches the real user key) never reaches it. The mapper no longer copies a tombstone
(``care_event_backfill_mapper.account_of``); this version corrects the lines an earlier run already wrote. v0104
itself is not edited (NFR-016 M-7).

**Scope.** Only ``performed_by_user_key`` values with the exact tombstone shape (``TOMBSTONE_FULLMATCH_REGEX``) are
replaced, whatever wrote the line; a real user key and the marker itself are never touched.

Idempotent (M-3): a corrected line no longer matches, a re-run changes nothing. Dry run (M-5) counts and writes
nothing. Irreversible (M-6): putting the pseudonym back would reintroduce the defect.
"""

from __future__ import annotations

from typing import Any, cast

import structlog
from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)

#: Frozen here (M-7): the marker and the tombstone shape as they were when this version was written
#: (``erasure_engine.ANONYMIZED_MARKER``, ``erasure_engine.TOMBSTONE_FULLMATCH_REGEX``).
_MARKER = "_anonymized"
_TOMBSTONE_REGEX = "^anon_[0-9a-f]{16}$"

_COUNT = """
FOR e IN @@events
  FILTER IS_STRING(e.performed_by_user_key) AND REGEX_TEST(e.performed_by_user_key, @pattern)
  COLLECT WITH COUNT INTO n
  RETURN n
"""

_REPLACE = """
FOR e IN @@events
  FILTER IS_STRING(e.performed_by_user_key) AND REGEX_TEST(e.performed_by_user_key, @pattern)
  UPDATE e WITH { performed_by_user_key: @marker } IN @@events
  RETURN 1
"""


class CareEventTombstonePerformerMigration(Migration):
    version = "0107"
    name = "care_event_tombstone_performer"
    description = (
        "Replace erased-account tombstone hashes in care_events.performed_by_user_key with the _anonymized marker "
        "(#2770, GP-NFR-055)."
    )
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        if not db.has_collection(col.CARE_EVENTS):
            return MigrationReport(
                version=self.version, name=self.name, scanned=0, changed=0, dry_run=dry_run, details={}
            )
        bind_vars: dict[str, Any] = {"@events": col.CARE_EVENTS, "pattern": _TOMBSTONE_REGEX}
        found = sum(cast(Cursor, db.aql.execute(_COUNT, bind_vars=bind_vars)))
        replaced = 0
        if not dry_run and found:
            cursor = cast(Cursor, db.aql.execute(_REPLACE, bind_vars=bind_vars | {"marker": _MARKER}))
            replaced = sum(1 for _ in cursor)
        details = {"will_replace" if dry_run else "replaced": found if dry_run else replaced}
        logger.info("care_event_tombstone_performer", dry_run=dry_run, **details)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=found,
            changed=0 if dry_run else replaced,
            dry_run=dry_run,
            details=details,
        )


migration = CareEventTombstonePerformerMigration()
