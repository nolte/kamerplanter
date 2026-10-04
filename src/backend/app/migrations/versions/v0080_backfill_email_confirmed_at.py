"""v0080 — grandfather the already verified accounts into ``email_confirmed_at`` (#1948).

``email_confirmed_at`` is the proof that the owner of a login address followed a
link (or that an OIDC provider asserted it). The e-mail notification channel
(REQ-030 §3.4) mails only an address carrying it, because ``email_verified`` alone
is also stamped by a registration made with ``REQUIRE_EMAIL_VERIFICATION=false``.

**Backfill rule.** Every account with ``email_verified == true`` and no
``email_confirmed_at`` gets the migration time. The migration cannot tell the two
origins apart: ``verify_email`` clears the token fields and a registration made
with verification off leaves them empty, so both end as ``verified, no token``
(asserted in ``tests/api/test_registration_without_verification_gets_no_notification_mail.py``).
Leaving the unprovable accounts unstamped would silently stop every existing notification mail on first deploy;
stamping them keeps today's behaviour and applies the proof requirement to every
account registered *after* this migration. An operator who ran with verification
off can lower ``email_verified`` on those accounts (admin step-up) to make them
confirm again; the dry run reports how many accounts are grandfathered.

Accounts with ``email_verified == false`` are never touched: they confirm through the
link and ``verify_email`` writes the proof then.

**Idempotent (M-3).** A stamped account no longer matches; a second run changes nothing.

**Dry run (M-5).** Counts the accounts that would be stamped and writes nothing.

**Not reversible (M-6).** The pre-migration state of the field (absent) is the
defect being repaired; there is no value to restore.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any, cast

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)

_MATCH = "FILTER doc.email_verified == true AND (doc.email_confirmed_at == null)"

_COUNT_QUERY = f"FOR doc IN @@collection {_MATCH} COLLECT WITH COUNT INTO n RETURN n"
_STAMP_QUERY = (
    f"FOR doc IN @@collection {_MATCH} "
    "UPDATE doc WITH {email_confirmed_at: @stamp} IN @@collection "
    "COLLECT WITH COUNT INTO n RETURN n"
)


class BackfillEmailConfirmedAtMigration(Migration):
    version = "0080"
    name = "backfill_email_confirmed_at"
    description = (
        "Stamp email_confirmed_at on every already verified account so the e-mail notification channel "
        "keeps mailing them; accounts registered afterwards must prove the address (#1948)."
    )
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        if not db.has_collection(col.USERS):
            return MigrationReport(version=self.version, name=self.name, scanned=0, changed=0, dry_run=dry_run)
        binds: dict[str, Any] = {"@collection": col.USERS}
        if not dry_run:
            binds["stamp"] = datetime.now(UTC).isoformat()
        cursor = db.aql.execute(_COUNT_QUERY if dry_run else _STAMP_QUERY, bind_vars=binds)
        rows = next(iter(cast(Iterable[int], cursor)), 0)
        logger.info("backfill_email_confirmed_at", dry_run=dry_run, accounts=rows)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=rows,
            changed=0 if dry_run else rows,
            dry_run=dry_run,
            details={"grandfathered_accounts": rows},
        )


migration = BackfillEmailConfirmedAtMigration()
