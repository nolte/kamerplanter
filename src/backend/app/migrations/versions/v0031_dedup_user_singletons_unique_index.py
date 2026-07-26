"""v0031 — dedup per-user singletons and enforce a unique ``user_key`` index.

Bug (duplicate-singleton race): ``user_preferences`` and ``onboarding_states``
hold at most one document per ``user_key``, but neither collection carried a
unique index and both services auto-created the singleton on the first cold read
(``find_by_field("user_key", …)`` → if empty, insert a default). Under
concurrent cold reads — multiple browsers/workers starting at once — several
requests each found the collection empty and each inserted, minting *two* (or
more) documents for the same ``user_key``. Afterwards every request read/wrote a
non-deterministic ``docs[0]`` of an unordered scan, so preferences and onboarding
state flapped between requests (root cause of the flaky REQ-021 E2E tests, and a
contributor to the REQ-020 xdist race).

The code fix (a) adds a unique persistent index on ``user_key`` to both
collections at bootstrap so the storage layer rejects the losing insert, (b)
turns the auto-create path into an upsert (re-read on ``DuplicateError``) and (c)
makes the read deterministic (smallest ``_key`` wins). This migration repairs
existing volumes that already accumulated duplicates before the index existed.

Per collection (``user_preferences`` then ``onboarding_states``), two ordered
jobs, both idempotent:

1. **Collapse duplicate singleton groups.** Every ``user_key`` group with more
   than one document keeps a single survivor — the one with the most recent
   ``updated_at`` (fallback: lexicographically smallest ``_key``) — and the
   losers are removed in a single batched AQL ``REMOVE``. ``scanned`` counts the
   loser documents found; ``changed`` counts those removed.

   **Groups without a ``user_key`` are excluded** (``FILTER uk != null AND uk !=
   ""``): AQL collects a *missing* attribute as ``null``, so legacy documents
   that never carried a ``user_key`` would otherwise form one artificial "group"
   spanning several unrelated users and be deleted down to a single survivor —
   irreversibly, since this migration has no inverse. They are counted per
   collection and reported as ``unassigned_user_key_docs`` instead, for an
   operator to inspect; the migration never touches them.

2. **Ensure the unique index.** A unique **sparse** persistent index on
   ``["user_key"]`` is created if absent (safe now — step 1 removed the colliding
   duplicates) and any redundant non-unique or non-sparse persistent index on the
   same field is dropped. ``sparse`` (as in v0030 for ``batch_id``) leaves
   documents *without* the attribute out of the index, so the attribute-less
   legacy documents step 1 deliberately spares cannot block the constraint that
   protects every real user. Index introspection mirrors v0026/v0030:
   ``indexes()`` filtered by ``type``/``fields``, ``unique``/``sparse`` flags
   compared, ``delete_index(..., ignore_missing=True)``.

Idempotent (M-3): a re-run finds no duplicate groups (step 1 no-op) and the
unique+sparse index already present with no redundant sibling (step 2 no-op) →
``changed == 0``. Dry-run (M-5): both jobs are previewed and nothing is written.
Irreversible (M-6): step 1 deletes the loser documents (their pre-merge content
is discarded) and step 2 drops the non-unique bootstrap index that predates this
migration, so there is no honest inverse.

Residual (reported, not repaired): several documents carrying an *empty-string*
``user_key`` are indexed by a sparse index just like real values, so they would
make the unique-index creation fail loudly. That is the intended outcome — a
loud failure with the ``unassigned_user_key_docs`` count in the report beats
deleting documents of different users.

NOTE (merge): this version number (``0031``) is provisional — it is the next free
slot above the current branch head (``0030``). If a parallel lane lands another
``0031`` first, RENUMBER this module (and its test) to the next free contiguous
slot before merge; the discovery layer enforces gapless numbering (M-1).
"""

from __future__ import annotations

from typing import Any

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger()

#: Field of the singleton index this migration enforces as unique.
_INDEX_FIELDS: list[str] = ["user_key"]

#: Collections that hold exactly one document per ``user_key``.
_SINGLETON_COLLECTIONS: tuple[str, ...] = (col.USER_PREFERENCES, col.ONBOARDING_STATES)


def _pick_survivor(docs: list[dict[str, Any]]) -> dict[str, Any]:
    """Return the document a duplicate ``user_key`` group collapses onto.

    Most recent ``updated_at`` wins; ties (or missing timestamps, both compared
    as ``""``) fall back to the lexicographically smallest ``_key`` for
    determinism.
    """
    best = docs[0]
    for doc in docs[1:]:
        best_ts = best.get("updated_at") or ""
        doc_ts = doc.get("updated_at") or ""
        newer = doc_ts > best_ts
        tie_smaller_key = doc_ts == best_ts and str(doc.get("_key", "")) < str(best.get("_key", ""))
        if newer or tie_smaller_key:
            best = doc
    return best


class DedupUserSingletonsUniqueIndexMigration(Migration):
    version = "0031"
    name = "dedup_user_singletons_unique_index"
    description = (
        "Collapse duplicate user_preferences/onboarding_states singletons per user_key "
        "and enforce a unique user_key index so the auto-create race can no longer mint "
        "duplicate singletons."
    )
    reversible = False

    # ── read helpers (no-op-safe on an empty/fresh database) ──────────────────

    def _loser_keys(self, db: StandardDatabase, collection: str) -> list[str]:
        """Keys of every non-survivor in a duplicate ``user_key`` group (read-only).

        Documents without a usable ``user_key`` are excluded up front: AQL groups
        a missing attribute as ``null``, so they would form one artificial group
        across *different* users and be deleted down to a single survivor. They
        are surfaced by :meth:`_unassigned_keys` instead.

        M-5-safe: pure read, returns ``[]`` when the collection is absent or holds
        no duplicates.
        """
        if not db.has_collection(collection):
            return []
        groups = db.aql.execute(
            "FOR doc IN @@collection "
            "COLLECT uk = doc.user_key INTO grp = doc "
            'FILTER uk != null AND uk != "" '
            "FILTER LENGTH(grp) > 1 "
            "RETURN {user_key: uk, docs: grp}",
            bind_vars={"@collection": collection},
        )
        losers: list[str] = []
        for group in groups:
            docs = list(group["docs"])
            survivor = _pick_survivor(docs)
            survivor_key = str(survivor.get("_key", ""))
            losers.extend(str(doc.get("_key", "")) for doc in docs if str(doc.get("_key", "")) != survivor_key)
        return losers

    def _unassigned_keys(self, db: StandardDatabase, collection: str) -> list[str]:
        """Keys of every singleton document without a usable ``user_key`` (read-only).

        Legacy documents whose ``user_key`` is missing, ``null`` or ``""`` cannot
        be attributed to a user, so they are never deduplicated (that would delete
        across users). Reported per collection so an operator can decide; a sparse
        unique index keeps the ``null``/absent ones from blocking the constraint.

        M-5-safe: pure read, returns ``[]`` when the collection is absent.
        """
        if not db.has_collection(collection):
            return []
        return list(
            db.aql.execute(
                'FOR doc IN @@collection FILTER doc.user_key == null OR doc.user_key == "" RETURN doc._key',
                bind_vars={"@collection": collection},
            )
        )

    def _persistent_user_key_indexes(self, collection_handle: Any) -> list[dict[str, Any]]:
        """Return the persistent index dicts on ``user_key`` for one collection."""
        return [
            idx
            for idx in collection_handle.indexes()
            if isinstance(idx, dict) and idx.get("type") == "persistent" and idx.get("fields") == _INDEX_FIELDS
        ]

    # ── entry point ───────────────────────────────────────────────────────────

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        scanned = 0
        changed = 0
        details: dict[str, Any] = {}

        for collection in _SINGLETON_COLLECTIONS:
            loser_keys = self._loser_keys(db, collection)
            unassigned = len(self._unassigned_keys(db, collection))
            scanned += len(loser_keys)

            handle = db.collection(collection)
            indexes = self._persistent_user_key_indexes(handle)
            has_sparse_unique = any(idx.get("unique") and idx.get("sparse") for idx in indexes)
            redundant = [idx for idx in indexes if not (idx.get("unique") and idx.get("sparse"))]

            if dry_run:
                details[collection] = {
                    "duplicate_losers": len(loser_keys),
                    "unassigned_user_key_docs": unassigned,
                    "index_already_sparse_unique": has_sparse_unique,
                    "will_create_sparse_unique_index": not has_sparse_unique,
                    "will_drop_redundant_indexes": len(redundant),
                }
                continue

            # 1. Remove the losing duplicates in a single batched REMOVE. Documents
            #    without a usable user_key are never part of ``loser_keys``.
            if loser_keys:
                db.aql.execute(
                    "FOR key IN @keys REMOVE key IN @@collection",
                    bind_vars={"keys": loser_keys, "@collection": collection},
                )

            # 2. Ensure the unique+sparse index and drop any redundant sibling.
            index_changes = 0
            if not has_sparse_unique:
                handle.add_persistent_index(fields=_INDEX_FIELDS, unique=True, sparse=True)
                index_changes += 1
            for idx in self._persistent_user_key_indexes(handle):
                if not (idx.get("unique") and idx.get("sparse")):
                    handle.delete_index(idx["id"], ignore_missing=True)
                    index_changes += 1

            changed += len(loser_keys) + index_changes
            details[collection] = {
                "removed_losers": len(loser_keys),
                "unassigned_user_key_docs": unassigned,
                "index_changes": index_changes,
                "sparse_unique_index_enforced": True,
            }

        if dry_run:
            logger.info("dedup_user_singletons_unique_index_dry_run", scanned=scanned, details=details)
            return MigrationReport(
                version=self.version,
                name=self.name,
                scanned=scanned,
                changed=0,
                dry_run=True,
                details=details,
            )

        logger.info("dedup_user_singletons_unique_index_applied", scanned=scanned, changed=changed, details=details)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=scanned,
            changed=changed,
            dry_run=False,
            details=details,
        )


migration = DedupUserSingletonsUniqueIndexMigration()
