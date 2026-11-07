"""v0106 — the unique client-event indexes on existing volumes (REQ-053 WP 9.3, #2743).

A client that buffers a write offline sends a ``client_event_id`` with every attempt; the server stores it on the
object the write creates, and a unique index per tenant makes a replay find that object instead of creating a
second one. Three indexes, all structural - **no document is read for its content or written**:

* ``care_events (tenant_key, client_event_id)`` - ``POST /care-events``;
* ``tasks (tenant_key, completion_client_event_id)`` - ``POST /tasks/{key}/complete`` and ``tasks/batch/status``;
* ``attachments (tenant_key, client_event_id)`` - ``POST /attachments`` (the bed photo) and the plant photo upload.

All three are **unique and sparse**: a row without the attribute (every row written before wave 9, every
server-made one) is not in the index, so the rows that carry none never collide. ``tenant_key`` leads
(``test_tenant_unique_indexes_are_scoped``): the id is unique per tenant, not across tenants.

Fresh volumes get the same indexes from ``ensure_collections``
(:data:`~app.data_access.arango.collections.CARE_EVENT_CLIENT_EVENT_INDEX_FIELDS` and its two siblings), which runs
before the migration runner; on such a volume this version is a no-op. On a volume that predates WP 9.3 no document
carries the attributes yet, so the creation cannot meet a duplicate; it still goes through
:func:`~app.data_access.arango.collections.ensure_unique_index_when_clean`, so a volume that somehow holds two rows
with one id is reported as **blocked** (logged with the count, never a row deleted, never a failed boot) and every
later boot retries.

Idempotent (M-3): a unique sparse index on exactly the fields makes that collection a no-op. Dry run (M-5) counts the
duplicate ids and creates nothing. Irreversible (M-6): the bootstrap creates the indexes on every boot, so dropping
them would not restore the pre-migration state.
"""

from __future__ import annotations

from typing import Any, cast

import structlog
from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.data_access.arango.collections import ensure_unique_index_when_clean, has_unique_index
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)

#: Frozen here (M-7) so a later change of the bootstrap constants does not change what this version did.
#: Equal to the ``collections`` constants (unit test). ``(collection, fields)``.
INDEXES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("care_events", ("tenant_key", "client_event_id")),
    ("tasks", ("tenant_key", "completion_client_event_id")),
    ("attachments", ("tenant_key", "client_event_id")),
)

#: Ids held by more than one row of a tenant - what would refuse the unique index. ``@id_field`` is a bound
#: attribute name, never spliced into the query text.
_DUPLICATE_IDS = """
RETURN LENGTH(
    FOR d IN @@collection
        FILTER d[@id_field] != null
        COLLECT tenant = d.tenant_key, id = d[@id_field] WITH COUNT INTO rows
        FILTER rows > 1
        RETURN 1
)
"""


class ClientEventIdIndexMigration(Migration):
    version = "0106"
    name = "client_event_id_index"
    description = (
        "Add the unique sparse (tenant_key, client_event_id) indexes on care_events and attachments and "
        "(tenant_key, completion_client_event_id) on tasks, so a replayed buffered write never creates a second "
        "object (REQ-053 WP 9.3)."
    )
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        present: dict[str, bool] = {}
        duplicates: dict[str, int] = {}
        absent: list[str] = []
        for collection, fields in INDEXES:
            if not db.has_collection(collection):
                absent.append(collection)
                continue
            present[collection] = has_unique_index(db.collection(collection), list(fields), sparse=True)
            if not present[collection]:
                duplicates[collection] = self._duplicate_ids(db, collection, fields[-1])
        details: dict[str, Any] = {
            "indexes": {collection: list(fields) for collection, fields in INDEXES},
            "collections_absent": absent,
            "index_present": present,
            "duplicate_ids": duplicates,
        }
        missing = [collection for collection, there in present.items() if not there]

        if dry_run:
            logger.info("client_event_id_index_dry_run", will_create=missing, duplicate_ids=duplicates)
            return MigrationReport(
                version=self.version,
                name=self.name,
                scanned=len(present),
                changed=0,
                dry_run=True,
                details={**details, "will_create": missing},
            )

        created: list[str] = []
        blocked: list[str] = []
        for collection, fields in INDEXES:
            if collection not in missing:
                continue
            if ensure_unique_index_when_clean(db.collection(collection), list(fields), sparse=True):
                created.append(collection)
            else:
                blocked.append(collection)
                logger.warning(
                    "client_event_id_index_blocked_by_duplicates",
                    collection=collection,
                    duplicate_ids=duplicates.get(collection, 0),
                    hint="two rows of a tenant carry one client event id; resolve by hand, every boot retries",
                )
        logger.info("client_event_id_index_applied", created=created, blocked=blocked)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=len(present),
            changed=len(created),
            dry_run=False,
            details={**details, "created": created, "blocked": blocked},
        )

    @staticmethod
    def _duplicate_ids(db: StandardDatabase, collection: str, id_field: str) -> int:
        cursor = cast(
            "Cursor",
            db.aql.execute(_DUPLICATE_IDS, bind_vars={"@collection": collection, "id_field": id_field}),
        )
        return int(next(iter(cursor), 0) or 0)


migration = ClientEventIdIndexMigration()
