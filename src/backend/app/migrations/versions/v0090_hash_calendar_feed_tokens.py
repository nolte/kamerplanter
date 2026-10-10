"""v0090 - #2171: hash the calendar feed tokens stored in clear.

Until #2171 ``calendar_feeds.token`` held the raw iCal token and the feed lookup
matched it by value: a read of the database or of a backup was a working
subscription URL for every feed of every tenant, and every ``GET`` of a feed
returned it as well. The model now keeps only the SHA-256 digest under
``token_hash``; the service hashes what a feed URL presents before looking it up,
and the token appears in clear only in the response of the create / rotate call
that issued it.

**Why hash rather than rotate.** The operator decision (2026-10-09) was to store
only a hash and to treat existing feeds by migration. Rotating them would kill
every URL already subscribed in a calendar app - silently, since a calendar
client does not tell its user that a feed stopped answering. Hashing the stored
value in place keeps those URLs working while no clear value stays at rest; a
member who has lost a URL gets a new one by rotating (the UI offers nothing
else, because the digest cannot be turned back into the token). The digest is
computed by AQL ``SHA256()``, the lowercase hex SHA-256 of the UTF-8 string -
the value ``TokenEngine.hash_token`` produces in Python - measured in
``tests/integration/test_calendar_feed_token_at_rest.py``.

**Order.** The old dense unique index on ``token`` must go before the attribute
does: with it in place, the second feed without a ``token`` would collide on
``null``. It is never dropped without its successor - ``ensure_collections``
creates the sparse unique ``token_hash`` index on every boot before the
migrations run, this version creates it itself when it is missing, and
:func:`~app.migrations.support.legacy_indexes.retire_legacy_index` refuses to
drop while no replacement exists (then the run reports ``precondition_unmet``
and a later boot retries). Only then are the digests written and the clear
attribute removed (``UNSET``: the repository's merge update keeps an attribute
the model does not declare, so leaving it would leave the clear value in place).
A ``token`` written by an older image after an earlier run wins over a stale
digest: only an older image writes ``token``, so it is the newer value.

Idempotent (M-3): a re-run finds no clear attribute and no legacy index and
changes nothing. Dry-run (M-5) counts and touches nothing. Logs counts only, never
a key or a token. Irreversible (M-6): a digest cannot be turned back into the
token.
"""

from __future__ import annotations

from typing import Any, cast

import structlog
from arango.collection import StandardCollection
from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport
from app.migrations.support.legacy_indexes import IndexShape, retire_legacy_index

logger = structlog.get_logger(__name__)

#: The attribute the model lost, and the digest it becomes.
_TOKEN = "token"
_TOKEN_HASH = "token_hash"

#: The index this version retires and the one that replaces it.
LEGACY_INDEX = IndexShape(fields=tuple(col.LEGACY_CALENDAR_FEED_TOKEN_INDEX_FIELDS), unique=True)
REPLACEMENT_INDEX = IndexShape(fields=tuple(col.CALENDAR_FEED_TOKEN_HASH_INDEX_FIELDS), unique=True, sparse=True)

#: Feeds that still carry the token attribute (a ``null`` or ``""`` counts: it is an
#: attribute the model no longer declares and is removed as well).
_COUNT_AQL = """
FOR f IN @@feeds
  FILTER HAS(f, @token)
  COLLECT WITH COUNT INTO n
  RETURN n
"""

_HASH_AQL = """
FOR f IN @@feeds
  FILTER HAS(f, @token)
  LET digest = IS_STRING(f[@token]) AND f[@token] != "" ? { [@token_hash]: SHA256(f[@token]) } : {}
  REPLACE f WITH MERGE(UNSET(f, @token), digest) IN @@feeds
  RETURN 1
"""


def _has_replacement(collection: StandardCollection) -> bool:
    rows = collection.indexes()
    return isinstance(rows, list) and any(isinstance(idx, dict) and REPLACEMENT_INDEX.matches(idx) for idx in rows)


class HashCalendarFeedTokensMigration(Migration):
    version = "0090"
    name = "hash_calendar_feed_tokens"
    description = (
        "Replace the clear iCal token on calendar_feeds with its SHA-256 digest and retire the unique "
        "token index (#2171); subscription URLs distributed before the upgrade keep working."
    )
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        if not db.has_collection(col.CALENDAR_FEEDS):
            return MigrationReport(version=self.version, name=self.name, scanned=0, changed=0, dry_run=dry_run)
        feeds = db.collection(col.CALENDAR_FEEDS)
        bind_vars: dict[str, Any] = {"@feeds": col.CALENDAR_FEEDS, "token": _TOKEN}
        pending = next(iter(cast(Cursor, db.aql.execute(_COUNT_AQL, bind_vars=bind_vars))), 0)

        needs_replacement = not _has_replacement(feeds)
        replacement_created = False
        if needs_replacement and not dry_run:
            feeds.add_persistent_index(
                fields=list(REPLACEMENT_INDEX.fields), unique=True, sparse=REPLACEMENT_INDEX.sparse
            )
            replacement_created = _has_replacement(feeds)

        outcome = retire_legacy_index(feeds, legacy=LEGACY_INDEX, replacement=REPLACEMENT_INDEX, dry_run=dry_run)
        # A dry run does not create the replacement; the real run would - a plan, not a refusal.
        refused = outcome.refused and not (dry_run and needs_replacement)
        details: dict[str, Any] = {
            "feeds_with_clear_token": pending,
            **outcome.details(),
            "refused_without_replacement": refused,
            "replacement_created": replacement_created,
        }
        scanned = pending + len(outcome.legacy_ids)
        if dry_run or refused:
            if dry_run:
                details["replacement_to_create"] = needs_replacement
            (logger.warning if refused else logger.info)(
                "hash_calendar_feed_tokens_migration", dry_run=dry_run, **details
            )
            return MigrationReport(
                version=self.version,
                name=self.name,
                scanned=scanned,
                changed=0,
                dry_run=dry_run,
                precondition_unmet=refused,
                details=details,
            )

        hashed = sum(cast(Cursor, db.aql.execute(_HASH_AQL, bind_vars={**bind_vars, "token_hash": _TOKEN_HASH})))
        details["feeds_hashed"] = hashed
        logger.info("hash_calendar_feed_tokens_migration_applied", **details)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=scanned,
            changed=hashed + outcome.dropped + int(replacement_created),
            dry_run=False,
            details=details,
        )


migration = HashCalendarFeedTokensMigration()
