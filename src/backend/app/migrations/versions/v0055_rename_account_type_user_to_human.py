"""v0055 — store ``account_type`` under the value REQ-023 declares (#1620).

REQ-023 §Datenmodell specifies the discriminator as ``Literal['human', 'service']``
with default ``human``, in three places. The model shipped in April 2026 with
``Literal["user", "service"]`` and default ``"user"``, and every account created
since — through registration, SSO, the demo seed and the E2E platform-admin seed —
was stored with ``account_type: "user"``. Nothing read the *human* side of the
value until #1616 (``allows_interactive_auth``, the ``_create_tokens`` backstop),
which is what turned the divergence from cosmetic into a security-relevant one: a
predicate written from the spec, ``account_type == 'human'``, is false for every
stored account, and a check phrased "is this a human?" therefore fails in the
permissive direction. The operator decided on 2026-09-23 that the code follows the
spec. #1620's model change makes ``"user"`` an invalid value; this migration deals
with the rows that already carry it.

**Population.** Two shapes are rewritten, both of which mean "not a service
account":

* ``account_type == "user"`` — every row the old default wrote;
* no ``account_type`` attribute at all — rows persisted before the field existed
  (April 2026), which the model has always read as its default. They are stamped
  too, so that after this migration the collection holds exactly one spelling and an
  AQL filter on the value sees every human account rather than only the ones that
  happened to be written after the field was added.

``"service"`` rows are never touched: the filter names the two shapes explicitly
rather than "everything that is not service", so an unknown third value — which
cannot exist under the model but would be the sign of a hand edit — is reported by
the scan, not silently absorbed.

**Idempotent (M-3).** The scan matches only rows still in one of the two shapes; a
second run finds none and reports ``changed == 0``.

**Not reversible (M-6).** The inverse would write a value the current model
refuses, so a ``down`` that "restores" ``"user"`` would break every read that
follows it. ``reversible = False`` rather than a faked inverse.

**Measured before writing.** Against the kind installation on 2026-09-23
(``schema_migrations`` at ``0043``, one account):
``users: 1 · account_type == "user": 0 · without the attribute: 1 · service: 0``.
The only shape that exists there is the *absent* one — which is why the ``HAS``
clause is load-bearing and not a precaution: a scan on ``== "user"`` alone would
report ``changed == 0`` on that installation and leave its one account in a shape
no writer produces any more. Installations whose accounts were created after the
field landed carry ``"user"`` (the model default wrote it; ``_to_doc`` excludes
``None``, not defaults), so both shapes are real.

**On the version number.** ``0055`` was the next free number on ``develop`` when
this was written. #1669 (PR #1674) had taken ``0055`` in parallel; the order was
settled by coordination on 2026-09-23 rather than by merge order: this module keeps
``0055`` and #1674 renumbers to ``0056``. Should the sequence still collide at merge
time, ``app/migrations/README.md`` §"Zwei Migrationen gleichzeitig im Review"
applies — safe while the migration has been applied nowhere (M-7).
"""

from __future__ import annotations

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)

#: The value the model stored until #1620.
OLD_VALUE = "user"
#: The value REQ-023 declares, and the model's default since #1620.
NEW_VALUE = "human"


class RenameAccountTypeUserToHumanMigration(Migration):
    version = "0055"
    name = "rename_account_type_user_to_human"
    description = "Rewrite account_type 'user' (and a missing attribute) to 'human' on every account (REQ-023, #1620)."
    reversible = False

    #: Both shapes that mean "not a service account". ``HAS`` is what makes the
    #: pre-field rows visible: ``u.account_type == null`` would also match an
    #: explicit ``null``, which no writer produces, but naming the absence is the
    #: honest predicate for "written before the field existed".
    _SCAN_QUERY = f"""
    FOR u IN {col.USERS}
      FILTER u.account_type == @old OR !HAS(u, "account_type")
      RETURN u._key
    """

    _TOTAL_QUERY = f"RETURN LENGTH({col.USERS})"

    def _plan(self, db: StandardDatabase) -> tuple[int, list[str]]:
        """Return ``(scanned, keys to rewrite)`` without writing (M-5)."""
        if not db.has_collection(col.USERS):
            return (0, [])
        scanned = int(next(iter(db.aql.execute(self._TOTAL_QUERY)), 0))
        keys = [str(k) for k in db.aql.execute(self._SCAN_QUERY, bind_vars={"old": OLD_VALUE})]
        return (scanned, keys)

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        scanned, keys = self._plan(db)

        if not dry_run and keys:
            users = db.collection(col.USERS)
            for key in keys:
                users.update({"_key": key, "account_type": NEW_VALUE}, silent=True)

        logger.info(
            "rename_account_type_user_to_human",
            scanned=scanned,
            rewritten=len(keys),
            dry_run=dry_run,
        )
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=scanned,
            changed=0 if dry_run else len(keys),
            dry_run=dry_run,
            details={"rewritten": len(keys), "keys": keys},
        )


migration = RenameAccountTypeUserToHumanMigration()
