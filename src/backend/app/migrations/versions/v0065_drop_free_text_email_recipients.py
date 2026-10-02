"""v0065 — drop the free-text recipient from every stored e-mail channel preference (#1885).

Until #1885 ``notification_preferences.channels.email.config.email`` held an
address the user had typed, and the e-mail channel mailed it without any
confirmation, so a preference could aim the operator's sender reputation at a
stranger's inbox. The channel now mails the account's confirmed address only and
the preference model drops ``email`` / ``address`` on every read and write, so the
stored value is already inert at dispatch. This migration removes the data itself
(it is personal data of a third party, REQ-025 data minimisation) from the rows
that still carry it.

Everything else in ``channels.email.config`` (``digest``, and whatever else a
client stored) and every other channel is left alone.

**Idempotent (M-3).** A row without the keys is not touched; a second run changes
nothing.

**Dry run (M-5).** Counts the affected rows and writes nothing.

**Not reversible (M-6).** The typed addresses are deleted on purpose; the model
would drop them again on the next read.
"""

from __future__ import annotations

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.domain.models.notification import EMAIL_RECIPIENT_KEYS
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)


class DropFreeTextEmailRecipientsMigration(Migration):
    version = "0065"
    name = "drop_free_text_email_recipients"
    description = (
        "Remove the typed-in recipient from channels.email.config of every stored notification "
        "preference; the e-mail channel mails the account's confirmed address only (#1885)."
    )
    reversible = False

    _SCAN_QUERY = f"""
    FOR p IN {col.NOTIFICATION_PREFERENCES}
      FILTER IS_OBJECT(p.channels.email.config)
      FILTER LENGTH(INTERSECTION(ATTRIBUTES(p.channels.email.config), @keys)) > 0
      RETURN p._key
    """
    _STRIP_QUERY = f"""
    FOR p IN {col.NOTIFICATION_PREFERENCES}
      FILTER IS_OBJECT(p.channels.email.config)
      FILTER LENGTH(INTERSECTION(ATTRIBUTES(p.channels.email.config), @keys)) > 0
      REPLACE p WITH MERGE(p, {{
        channels: MERGE(p.channels, {{
          email: MERGE(p.channels.email, {{config: UNSET(p.channels.email.config, @keys)}})
        }})
      }}) IN {col.NOTIFICATION_PREFERENCES}
    """

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        keys = list(EMAIL_RECIPIENT_KEYS)
        if not db.has_collection(col.NOTIFICATION_PREFERENCES):
            affected: list[str] = []
        else:
            affected = list(db.aql.execute(self._SCAN_QUERY, bind_vars={"keys": keys}))
        if affected and not dry_run:
            db.aql.execute(self._STRIP_QUERY, bind_vars={"keys": keys})
        logger.info("drop_free_text_email_recipients", rows=len(affected), dry_run=dry_run)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=len(affected),
            changed=0 if dry_run else len(affected),
            dry_run=dry_run,
            details={"rows_with_a_typed_recipient": len(affected)},
        )


migration = DropFreeTextEmailRecipientsMigration()
