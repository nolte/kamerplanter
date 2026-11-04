"""v0105 — REQ-053 WP 8.7 (#2650, U-002): a stored soil conductivity without a method gets ``ec_method = unknown``.

``SoilProfile.ec_method`` is new, and a conductivity is only readable with its extraction method: ``ec_ms_cm`` without
``ec_method`` is refused (422) from now on, and a stored profile that holds a value but no method would fail to load
against the new model. This version stamps ``soil_profile.ec_method = "unknown"`` on every bed whose profile has an
``ec_ms_cm`` and no ``ec_method``. ``unknown`` is comparable with nothing, not even with itself, so no salt assessment
or series can ever read the old value as if its method were known; nothing is guessed (E-10).

**Idempotent (M-3).** Only a profile with a value and without a method matches; after a run none does.
**Dry run (M-5).** ``--dry-run`` counts the beds it would stamp and writes nothing.
**Not reversible (M-6).** Which profiles carried no method before is not recorded, and ``unknown`` is the honest state
for the old values; clearing it again would make the stored profile invalid.
"""

from __future__ import annotations

from typing import cast

import structlog
from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)

#: Frozen here (M-7): the value of ``EcMethod.UNKNOWN``.
_UNKNOWN = "unknown"

_COUNT = """
FOR l IN @@locations
  FILTER IS_OBJECT(l.soil_profile) AND l.soil_profile.ec_ms_cm != null AND l.soil_profile.ec_method == null
  COLLECT WITH COUNT INTO n
  RETURN n
"""

_STAMP = """
FOR l IN @@locations
  FILTER IS_OBJECT(l.soil_profile) AND l.soil_profile.ec_ms_cm != null AND l.soil_profile.ec_method == null
  UPDATE l WITH { soil_profile: { ec_method: @unknown } } IN @@locations OPTIONS { mergeObjects: true }
  RETURN 1
"""


class SoilProfileEcMethodUnknownMigration(Migration):
    version = "0105"
    name = "soil_profile_ec_method_unknown"
    description = (
        "REQ-053 WP 8.7 (U-002): stamp ec_method = unknown on soil profiles that hold ec_ms_cm without a method."
    )
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        if not db.has_collection(col.LOCATIONS):
            return MigrationReport(
                version=self.version, name=self.name, scanned=0, changed=0, dry_run=dry_run, details={}
            )
        counted = sum(int(n) for n in cast(Cursor, db.aql.execute(_COUNT, bind_vars={"@locations": col.LOCATIONS})))
        stamped = 0
        if not dry_run and counted:
            written = cast(Cursor, db.aql.execute(_STAMP, bind_vars={"@locations": col.LOCATIONS, "unknown": _UNKNOWN}))
            stamped = sum(1 for _ in written)
        details = {"will_stamp" if dry_run else "stamped": counted if dry_run else stamped}
        logger.info("soil_profile_ec_method_unknown", dry_run=dry_run, **details)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=counted,
            changed=0 if dry_run else stamped,
            dry_run=dry_run,
            details=details,
        )


migration = SoilProfileEcMethodUnknownMigration()
