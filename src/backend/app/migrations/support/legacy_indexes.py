"""Select and retire legacy indexes by shape, whatever type the server reports (#2034).

Why a shared selector
=====================

Until 2026-06-07 (``516bcd832``) ``ensure_collections`` created every index with
``add_hash_index``; since then with ``add_persistent_index``. On the RocksDB engine
both are the same index, but ArangoDB 3.12 still *reports* an index created as
``hash`` with ``type: "hash"`` — measured on 3.12.8, ``indexes()`` returns
``('hash', ['batch_id'], unique=True)`` for it. Every volume first booted before
that date therefore carries hash-typed indexes.

A migration that recognises a legacy index by ``type == "persistent"`` does not see
those, reports success, and leaves the old constraint in force — v0030 and v0064
did exactly that (v0069 too, corrected by v0072). The cost is not cosmetic: a
stricter unique index that stays behind keeps refusing what its replacement was
meant to allow. Even re-creating the index does not converge: on 3.12.8
``add_persistent_index`` with the very definition of an existing hash index creates
a *second* index (``new: True``) instead of returning the first.

So every new migration selects indexes through :func:`is_index_on` /
:func:`indexes_on`; ``tests/unit/guards/test_migration_index_selectors.py`` refuses
an inline type comparison in any version module that is not an allow-listed shipped
one.

Why ``skiplist`` is not matched
===============================

``skiplist`` is the third alias of ``persistent`` on RocksDB, but no commit of this
repository has ever created one (``git log --all -S skiplist -- src/backend`` is
empty). The selector feeds ``delete_index``; widening it to a type this code never
made would let a migration drop an index an operator added by hand. Add it here,
with the evidence, the day a ``skiplist`` index is shown to exist on a volume.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final

from arango.collection import StandardCollection

#: The index types one ``add_persistent_index`` / ``add_hash_index`` call can be
#: reported as. See the module docstring for why ``skiplist`` is absent.
PERSISTENT_INDEX_TYPES: Final[tuple[str, ...]] = ("persistent", "hash")


def is_index_on(index: Mapping[str, Any], fields: Sequence[str]) -> bool:
    """Whether ``index`` is a persistent-family index on exactly ``fields`` (in order).

    Args:
        index: One entry of ``StandardCollection.indexes()``.
        fields: The indexed attribute paths, in index order.

    Returns:
        ``True`` for a ``persistent`` or ``hash`` index on exactly ``fields``.
    """
    return index.get("type") in PERSISTENT_INDEX_TYPES and list(index.get("fields") or []) == list(fields)


def _index_rows(collection: StandardCollection) -> list[dict[str, Any]]:
    """``collection.indexes()`` of a synchronous database, as the list it then is."""
    rows = collection.indexes()
    if not isinstance(rows, list):
        raise TypeError("migrations run on a synchronous database; indexes() returned a job")
    return [idx for idx in rows if isinstance(idx, dict)]


def indexes_on(collection: StandardCollection, fields: Sequence[str]) -> list[dict[str, Any]]:
    """Every persistent-family index of ``collection`` on exactly ``fields``."""
    return [idx for idx in _index_rows(collection) if is_index_on(idx, fields)]


@dataclass(frozen=True)
class IndexShape:
    """An index definition as far as a constraint is concerned: fields, unique, sparse."""

    fields: tuple[str, ...]
    unique: bool
    sparse: bool = False

    def matches(self, index: Mapping[str, Any]) -> bool:
        """Whether ``index`` has exactly this shape (any persistent-family type)."""
        return (
            is_index_on(index, self.fields)
            and bool(index.get("unique")) == self.unique
            and bool(index.get("sparse")) == self.sparse
        )


@dataclass(frozen=True)
class LegacyIndexRetirement:
    """What :func:`retire_legacy_index` found and did. Counts only, no keys."""

    legacy_ids: tuple[str, ...]
    legacy_types: tuple[str, ...]
    replacement_count: int
    dropped: int

    @property
    def refused(self) -> bool:
        """A legacy index exists but no replacement does, so nothing was dropped."""
        return bool(self.legacy_ids) and self.replacement_count == 0

    def details(self) -> dict[str, Any]:
        """Report payload shared by the migrations that call this."""
        return {
            "legacy_indexes": len(self.legacy_ids),
            "legacy_index_types": sorted(self.legacy_types),
            "replacement_indexes": self.replacement_count,
            "legacy_indexes_dropped": self.dropped,
            "refused_without_replacement": self.refused,
        }


def retire_legacy_index(
    collection: StandardCollection,
    *,
    legacy: IndexShape,
    replacement: IndexShape,
    dry_run: bool,
) -> LegacyIndexRetirement:
    """Drop every index of shape ``legacy``, but only while a ``replacement`` exists.

    Never drops a constraint without its successor: when a legacy index is present
    and no index of shape ``replacement`` is, nothing is dropped and the outcome is
    :attr:`LegacyIndexRetirement.refused`. Idempotent — once the legacy indexes are
    gone a re-run finds none. ``dry_run`` computes the outcome and drops nothing.

    Args:
        collection: The collection carrying both indexes.
        legacy: The shape to retire.
        replacement: The shape that must exist first; must be unique.
        dry_run: When ``True``, nothing is written.

    Returns:
        The counts of what was found and dropped.

    Raises:
        ValueError: If ``replacement`` is not unique, or equals ``legacy`` — either
            would let the call remove the constraint it exists to keep.
    """
    if not replacement.unique:
        raise ValueError("a replacement for a retired constraint must itself be unique")
    if replacement == legacy:
        raise ValueError("the legacy shape and its replacement are the same index")
    indexes = _index_rows(collection)
    legacy_found = [idx for idx in indexes if legacy.matches(idx) and "id" in idx]
    replacement_count = sum(1 for idx in indexes if replacement.matches(idx))
    outcome = LegacyIndexRetirement(
        legacy_ids=tuple(str(idx["id"]) for idx in legacy_found),
        legacy_types=tuple(str(idx.get("type")) for idx in legacy_found),
        replacement_count=replacement_count,
        dropped=0,
    )
    if dry_run or outcome.refused or not legacy_found:
        return outcome
    for index_id in outcome.legacy_ids:
        collection.delete_index(index_id, ignore_missing=True)
    return LegacyIndexRetirement(
        legacy_ids=outcome.legacy_ids,
        legacy_types=outcome.legacy_types,
        replacement_count=replacement_count,
        dropped=len(outcome.legacy_ids),
    )
