"""v0106 — the unique client-event indexes on existing volumes (REQ-053 WP 9.3, #2743).

A client that buffers a write offline sends a ``client_event_id`` with every attempt; the server stores it on the
object the write creates, and a unique index per tenant makes a replay find that object instead of creating a
second one. Three indexes, all structural - **no document is read for its content or written**:

* ``care_events (tenant_key, client_event_id)`` - ``POST /care-events``;
* ``tasks (tenant_key, completion_client_event_id)`` - ``POST /tasks/{key}/complete`` and ``tasks/batch/status``;
* ``attachments (tenant_key, client_event_id)`` - ``POST /attachments`` (the bed photo) and the plant photo upload;
* ``care_confirmations (completion_client_event_id, plant_key)`` - the care-reminder confirmation of a buffered task
  completion exists once, so its replay can run the follow-up again (``plant_key`` is the parent scope);
* ``client_event_tombstones`` - the collection itself, unique ``(tenant_key, client_event_id)`` and a TTL index on
  ``deleted_at`` (395 days): a late replay of a deleted object answers 404 ``client_event.deleted``.

All three are **unique and sparse**: a row without the attribute (every row written before wave 9, every
server-made one) is not in the index, so the rows that carry none never collide. ``tenant_key`` leads
(``test_tenant_unique_indexes_are_scoped``): the id is unique per tenant, not across tenants.

Fresh volumes get the same indexes from ``ensure_collections``
(:data:`~app.data_access.arango.collections.CARE_EVENT_CLIENT_EVENT_INDEX_FIELDS` and its two siblings), which runs
before the migration runner; on such a volume this version is a no-op. On a volume that predates WP 9.3 no document
carries the attributes yet, so the creation cannot meet a duplicate; it still goes through
:func:`~app.data_access.arango.collections.ensure_unique_index_when_clean`, so a volume that somehow holds two rows
with one id is reported as **blocked** (logged with the count, never a row deleted, never a failed boot) and every
later boot retries. A blocked index is logged at ERROR and sets the gauge ``client_event_index_blocked{collection}``
to 1 - the operator's alert; the lookups sort before ``LIMIT 1``, so a replay answers deterministically meanwhile.

Idempotent (M-3): a unique sparse index on exactly the fields makes that collection a no-op. Dry run (M-5) counts the
duplicate ids and creates nothing. Irreversible (M-6): the bootstrap creates the indexes on every boot, so dropping
them would not restore the pre-migration state.
"""

from __future__ import annotations

from typing import Any, cast

import structlog
from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.data_access.arango.collections import ensure_unique_index_when_clean, has_ttl_index, has_unique_index
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport
from app.observability.garden_plan_metrics import record_client_event_index_blocked

logger = structlog.get_logger(__name__)

#: Frozen here (M-7) so a later change of the bootstrap constants does not change what this version did.
#: Equal to the ``collections`` constants (unit test). ``(collection, fields)``.
INDEXES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("care_events", ("tenant_key", "client_event_id")),
    ("tasks", ("tenant_key", "completion_client_event_id")),
    ("attachments", ("tenant_key", "client_event_id")),
    ("care_confirmations", ("completion_client_event_id", "plant_key")),
)
#: The tombstone collection: unique (not sparse - every row carries both fields) and a TTL index.
TOMBSTONES = "client_event_tombstones"
TOMBSTONE_FIELDS: tuple[str, ...] = ("tenant_key", "client_event_id")
TOMBSTONE_TTL_FIELDS: tuple[str, ...] = ("deleted_at",)
TOMBSTONE_TTL_SECONDS = (365 + 30) * 86400

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
        "(tenant_key, completion_client_event_id) on tasks, the per-completion care confirmation index and the "
        "client_event_tombstones collection with its TTL index, so a replayed buffered write never creates a second "
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
                duplicates[collection] = self._duplicate_ids(db, collection, _id_field(fields))
        tombstones_ready = self._tombstones_ready(db)
        details: dict[str, Any] = {
            "indexes": {collection: list(fields) for collection, fields in INDEXES},
            "collections_absent": absent,
            "index_present": present,
            "duplicate_ids": duplicates,
            "tombstones_present": tombstones_ready,
        }
        missing = [collection for collection, there in present.items() if not there]

        if dry_run:
            logger.info("client_event_id_index_dry_run", will_create=missing, duplicate_ids=duplicates)
            will_create = [*missing, *([] if tombstones_ready else [TOMBSTONES])]
            return MigrationReport(
                version=self.version,
                name=self.name,
                scanned=len(present),
                changed=0,
                dry_run=True,
                details={**details, "will_create": will_create},
            )

        created: list[str] = []
        blocked: list[str] = []
        for collection, fields in INDEXES:
            if collection not in missing:
                if collection in present:
                    record_client_event_index_blocked(collection, blocked=False)
                continue
            if ensure_unique_index_when_clean(db.collection(collection), list(fields), sparse=True):
                created.append(collection)
                record_client_event_index_blocked(collection, blocked=False)
            else:
                blocked.append(collection)
                record_client_event_index_blocked(collection, blocked=True)
                # ERROR, not WARNING: replays on this collection are not guarded by the database until resolved.
                logger.error(
                    "client_event_id_index_blocked_by_duplicates",
                    collection=collection,
                    duplicate_ids=duplicates.get(collection, 0),
                    hint="two rows carry one client event id; resolve by hand, every boot retries",
                )
        if not tombstones_ready:
            self._create_tombstones(db)
            created.append(TOMBSTONES)
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
    def _tombstones_ready(db: StandardDatabase) -> bool:
        if not db.has_collection(TOMBSTONES):
            return False
        tombstones = db.collection(TOMBSTONES)
        return has_unique_index(tombstones, list(TOMBSTONE_FIELDS)) and has_ttl_index(
            tombstones, list(TOMBSTONE_TTL_FIELDS)
        )

    @staticmethod
    def _create_tombstones(db: StandardDatabase) -> None:
        if not db.has_collection(TOMBSTONES):
            db.create_collection(TOMBSTONES)
        tombstones = db.collection(TOMBSTONES)
        ensure_unique_index_when_clean(tombstones, list(TOMBSTONE_FIELDS))  # a fresh collection holds no duplicate
        if not has_ttl_index(tombstones, list(TOMBSTONE_TTL_FIELDS)):
            tombstones.add_index(
                {"type": "ttl", "fields": list(TOMBSTONE_TTL_FIELDS), "expireAfter": TOMBSTONE_TTL_SECONDS}
            )

    @staticmethod
    def _duplicate_ids(db: StandardDatabase, collection: str, id_field: str) -> int:
        cursor = cast(
            "Cursor",
            db.aql.execute(_DUPLICATE_IDS, bind_vars={"@collection": collection, "id_field": id_field}),
        )
        return int(next(iter(cursor), 0) or 0)


def _id_field(fields: tuple[str, ...]) -> str:
    """The client-event attribute of an index (the one that is no scope)."""
    return next(field for field in fields if "client_event_id" in field)


migration = ClientEventIdIndexMigration()
