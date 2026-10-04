"""The catalogue of retired index shapes, enforced on every boot after the migrations (#2064).

Why a migration alone is not enough
===================================

A migration that retires an index runs **once**: the runner records it as applied
and never runs it again. ``ensure_collections`` however runs on every replica at
every start, without the migration lock, and an **older image** still carries the
``add_persistent_index`` call of the index the migration dropped. Measured on
ArangoDB 3.12.8 (#2064): after every migration up to v0078 had run, the
``ensure_collections`` of the image before v0069 re-created ``tanks(name)``,
``fertilizers(product_name, brand)``, ``activities(name)`` and
``workflow_templates(name)`` — unique and collection-wide again — beside their
tenant-scoped replacements; older images added ``auth_providers(provider,
provider_user_id)``, the dense ``harvest_batches(batch_id)``, the global
``species(scientific_name_normalized)`` and the unique ``attachments(storage_key)``;
a pre-June image re-created them typed ``hash``. A new-image reboot afterwards
changed nothing: the migrations were applied.
The defect each migration had closed (the cross-tenant ``409`` existence oracle and
the refused name) was back for good. That happens on an image rollback and on a
rolling update that restarts an old pod after a new one migrated.

Where cross-tenant duplicates already exist the old image cannot re-create the
index at all: its ``ensure_collections`` raises ``ERR 1210`` and the old pod does not
start (measured: two tenants' ``Tank 1`` → ``unique constraint violated``). The new
image cannot help that pod; the release note forbids that rollback.

What every boot does
====================

:func:`enforce_retired_indexes` walks :data:`RETIRED_INDEXES` after the migrations,
inside :meth:`~app.migrations.framework.runner.MigrationRunner.upgrade` — so under the
migration lock the runner already holds, not under a lock of its own. An entry is
enforced only once **every** migration that retired it is recorded as applied: before
that, the migration owns the work (v0030 nulls blank labels before the sparse index
may replace the dense one). Each enforced entry goes through
:func:`~app.migrations.support.legacy_indexes.retire_legacy_index`, whose selector
sees ``persistent`` and ``hash`` alike and which never drops a legacy index unless a
different unique index of the replacement shape exists.

**When the replacement is missing** — or the server fails the read or the drop — the
retirement refuses and nothing is dropped:
the stricter legacy constraint stays in force, which refuses more than it should but
loses nothing. The boot logs ``retired_index_refused_without_replacement`` at error
level and the readiness payload reports the count (:func:`last_enforcement`), with
the probe still answering ``200``. Neither a crash nor a ``503``: no restart can
create the missing replacement (``ensure_collections`` already tried, just before),
so a crash-loop or every replica out of rotation would turn a too-strict constraint
into an outage. It is an operator's case, and the signal is where an operator looks.

**What this cannot do.** An old pod that starts *after* the new pods booted
re-creates the index again, and nothing retires it until the next new-image boot —
the check runs at boot, not continuously. The release note is the other half: no
image rollback below the first migration of a retired index.

Every version module that drops an index is either an entry's ``retired_by`` or
named in ``tests/unit/guards/test_retired_indexes_are_catalogued.py`` with the
reason it is not one.
"""

from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import Final

import structlog
from arango.database import StandardDatabase
from arango.exceptions import ArangoError

from app.data_access.arango import collections as col
from app.migrations.support.legacy_indexes import PERSISTENT_INDEX_TYPES, IndexShape, retire_legacy_index

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class RetiredIndex:
    """One retired index shape, the shape that replaces it today, and who retired it.

    ``replacement`` is the **current** successor as ``ensure_collections`` creates it,
    not the one the first retiring migration created: when that successor is itself
    retired later, the entry moves to the newest shape (the guard refuses a
    replacement that is another entry's legacy shape). Both shapes match an index of
    any type in :data:`~app.migrations.support.legacy_indexes.PERSISTENT_INDEX_TYPES`.
    """

    collection: str
    legacy: IndexShape
    replacement: IndexShape
    retired_by: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.retired_by:
            raise ValueError("a retired index names the migration that retired it")
        if not self.replacement.unique:
            raise ValueError("a retired index is replaced by a unique index (retire_legacy_index refuses otherwise)")

    @property
    def types(self) -> tuple[str, ...]:
        """The index types the legacy shape is recognised as."""
        return PERSISTENT_INDEX_TYPES

    @property
    def label(self) -> str:
        """``collection(field, …)`` — what the log and the readiness payload name."""
        return f"{self.collection}({', '.join(self.legacy.fields)})"


#: The unique index ``ensure_collections`` created on ``auth_providers`` before #1869
#: (``LEGACY_UNIQUE_FIELDS`` of v0064, spelled out here: a support module does not
#: import a version module).
_LEGACY_PROVIDER_LINK_FIELDS: Final[tuple[str, ...]] = ("provider", "provider_user_id")

#: Today's lot label index (#2065). The dense label index v0030/v0073 retired points
#: here too, not at the sparse collection-wide index v0079 retired in turn.
_HARVEST_BATCH_ID_INDEX: Final[IndexShape] = IndexShape(
    fields=tuple(col.HARVEST_BATCH_ID_INDEX_FIELDS), unique=True, sparse=True
)

#: Every retired index shape whose re-creation by an older image re-imposes a
#: constraint the application no longer wants. Ordered by the first retiring version.
RETIRED_INDEXES: Final[tuple[RetiredIndex, ...]] = (
    RetiredIndex(
        collection=col.HARVEST_BATCHES,
        legacy=IndexShape(fields=tuple(col.LEGACY_HARVEST_BATCH_ID_INDEX_FIELDS), unique=True, sparse=False),
        replacement=_HARVEST_BATCH_ID_INDEX,
        retired_by=("0030", "0073"),
    ),
    RetiredIndex(
        collection=col.SPECIES,
        legacy=IndexShape(fields=tuple(col.LEGACY_GLOBAL_NAME_INDEX_FIELDS), unique=True),
        replacement=IndexShape(fields=tuple(col.SCIENTIFIC_NAME_NORMALIZED_INDEX_FIELDS), unique=True),
        retired_by=("0041",),
    ),
    RetiredIndex(
        collection=col.AUTH_PROVIDERS,
        legacy=IndexShape(fields=_LEGACY_PROVIDER_LINK_FIELDS, unique=True),
        replacement=IndexShape(fields=tuple(col.AUTH_PROVIDER_UNIQUE_FIELDS), unique=True),
        retired_by=("0064", "0074"),
    ),
    RetiredIndex(
        collection=col.FERTILIZERS,
        legacy=IndexShape(fields=tuple(col.LEGACY_GLOBAL_FERTILIZER_INDEX_FIELDS), unique=True),
        replacement=IndexShape(fields=tuple(col.FERTILIZER_IDENTITY_INDEX_FIELDS), unique=True),
        retired_by=("0069", "0072"),
    ),
    RetiredIndex(
        collection=col.TANKS,
        legacy=IndexShape(fields=tuple(col.LEGACY_TANK_NAME_INDEX_FIELDS), unique=True),
        replacement=IndexShape(fields=tuple(col.TANK_NAME_INDEX_FIELDS), unique=True),
        retired_by=("0075",),
    ),
    RetiredIndex(
        collection=col.ACTIVITIES,
        legacy=IndexShape(fields=tuple(col.LEGACY_ACTIVITY_NAME_INDEX_FIELDS), unique=True),
        replacement=IndexShape(fields=tuple(col.ACTIVITY_NAME_INDEX_FIELDS), unique=True),
        retired_by=("0076",),
    ),
    RetiredIndex(
        collection=col.WORKFLOW_TEMPLATES,
        legacy=IndexShape(fields=tuple(col.LEGACY_WORKFLOW_TEMPLATE_NAME_INDEX_FIELDS), unique=True),
        replacement=IndexShape(fields=tuple(col.WORKFLOW_TEMPLATE_NAME_INDEX_FIELDS), unique=True),
        retired_by=("0077",),
    ),
    RetiredIndex(
        collection=col.PLANT_INSTANCES,
        legacy=IndexShape(fields=tuple(col.LEGACY_PLANT_INSTANCE_ID_INDEX_FIELDS), unique=True),
        replacement=IndexShape(fields=tuple(col.PLANT_INSTANCE_ID_INDEX_FIELDS), unique=True),
        retired_by=("0079",),
    ),
    RetiredIndex(
        collection=col.HARVEST_BATCHES,
        legacy=IndexShape(fields=tuple(col.LEGACY_HARVEST_BATCH_ID_INDEX_FIELDS), unique=True, sparse=True),
        replacement=_HARVEST_BATCH_ID_INDEX,
        retired_by=("0079",),
    ),
    RetiredIndex(
        collection=col.SLOTS,
        legacy=IndexShape(fields=tuple(col.LEGACY_SLOT_ID_INDEX_FIELDS), unique=True),
        replacement=IndexShape(fields=tuple(col.SLOT_ID_INDEX_FIELDS), unique=True),
        retired_by=("0079",),
    ),
)


@dataclass(frozen=True)
class RetiredIndexEnforcement:
    """What one boot's enforcement found: labels only, no keys, no index ids."""

    enforced: tuple[str, ...]
    re_retired: tuple[str, ...]
    refused: tuple[str, ...]


_last: RetiredIndexEnforcement | None = None


def last_enforcement() -> RetiredIndexEnforcement | None:
    """The outcome of this process's last (non-dry) enforcement; ``None`` before the first."""
    return _last


def enforce_retired_indexes(
    db: StandardDatabase,
    *,
    applied: Collection[str],
    catalogue: Sequence[RetiredIndex] = RETIRED_INDEXES,
    dry_run: bool = False,
) -> RetiredIndexEnforcement:
    """Retire every catalogued legacy index that is present again; report what was done.

    The caller holds the migration lock (module docstring). An entry is skipped while
    any of its ``retired_by`` versions is not in ``applied``, and when its collection
    does not exist. ``dry_run`` drops nothing and leaves :func:`last_enforcement`
    untouched.

    Args:
        db: The application database.
        applied: The migration versions recorded as applied.
        catalogue: The retired shapes; :data:`RETIRED_INDEXES` outside tests.
        dry_run: When ``True``, nothing is written.

    Returns:
        The labels of the entries enforced, re-retired, and refused for want of a
        replacement.
    """
    global _last
    enforced: list[str] = []
    re_retired: list[str] = []
    refused: list[str] = []
    for entry in catalogue:
        if not set(entry.retired_by) <= set(applied) or not db.has_collection(entry.collection):
            continue
        enforced.append(entry.label)
        try:
            outcome = retire_legacy_index(
                db.collection(entry.collection),
                legacy=entry.legacy,
                replacement=entry.replacement,
                dry_run=dry_run,
            )
        except ArangoError as exc:
            # A heal that fails must not take the boot down with it (a crash-loop would
            # turn a too-strict constraint into an outage); it is reported like a refusal.
            refused.append(entry.label)
            logger.error("retired_index_enforcement_failed", index=entry.label, error_type=type(exc).__name__)
            continue
        if outcome.refused:
            refused.append(entry.label)
            logger.error(
                "retired_index_refused_without_replacement",
                index=entry.label,
                retired_by=list(entry.retired_by),
                dry_run=dry_run,
                **outcome.details(),
            )
        elif outcome.legacy_ids:
            re_retired.append(entry.label)
            logger.warning(
                "retired_index_reappeared",
                index=entry.label,
                retired_by=list(entry.retired_by),
                dry_run=dry_run,
                **outcome.details(),
            )
    result = RetiredIndexEnforcement(enforced=tuple(enforced), re_retired=tuple(re_retired), refused=tuple(refused))
    if not dry_run:
        _last = result
    return result
