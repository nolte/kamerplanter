"""Tests for v0031_dedup_user_singletons_unique_index.

The migration (1) collapses duplicate ``user_preferences``/``onboarding_states``
singletons per ``user_key`` — keeping the most-recently-updated survivor — and (2)
ensures a unique persistent index on ``user_key`` (dropping any non-unique sibling)
so the auto-create race can no longer mint duplicate singletons.

Covered:
  * a volume with duplicate singletons in BOTH collections collapses onto the
    most-recent-``updated_at`` survivor AND the index is promoted to unique;
  * survivor tie-break falls back to the smallest ``_key`` when timestamps match;
  * idempotency — a re-run finds no duplicates and the unique index already
    present (``changed == 0``);
  * dry-run writes nothing — neither the losers nor the index are touched;
  * a fresh volume that already carries the unique index is a no-op;
  * ``down`` refuses (irreversible).
"""

from __future__ import annotations

from app.data_access.arango import collections as col
from app.migrations.framework.report import IrreversibleMigrationError
from app.migrations.versions.v0031_dedup_user_singletons_unique_index import (
    _INDEX_FIELDS,
    _SINGLETON_COLLECTIONS,
    migration,
)

# ── Fake database: AQL for the duplicate-group COLLECT + batched REMOVE, and a
#    collection API for index introspection (persistent handles so index state
#    survives calls). ──


class _FakeCollection:
    def __init__(self, store: dict[str, dict], indexes: list[dict]) -> None:
        self._store = store
        self._indexes = indexes
        self._seq = [0]

    def indexes(self) -> list[dict]:
        return [dict(i) for i in self._indexes]

    def add_persistent_index(self, *, fields, unique: bool = False, sparse: bool = False, **_):
        self._seq[0] += 1
        record = {
            "id": f"idx/{self._seq[0]}",
            "type": "persistent",
            "fields": list(fields),
            "unique": unique,
            "sparse": sparse,
        }
        self._indexes.append(record)
        return record

    def delete_index(self, index_id: str, ignore_missing: bool = False) -> bool:
        for i, idx in enumerate(self._indexes):
            if idx.get("id") == index_id:
                del self._indexes[i]
                return True
        if not ignore_missing:
            raise KeyError(index_id)
        return False


class _FakeAql:
    def __init__(self, db: _FakeDb) -> None:
        self._db = db

    def execute(self, query: str, bind_vars: dict | None = None):
        bind_vars = bind_vars or {}
        collection = bind_vars["@collection"]
        store = self._db.cols.get(collection, {})

        if "COLLECT uk = doc.user_key" in query:
            groups: dict[str, list[dict]] = {}
            for doc in store.values():
                groups.setdefault(doc.get("user_key"), []).append(doc)
            return iter([{"user_key": uk, "docs": list(docs)} for uk, docs in groups.items() if len(docs) > 1])

        if "REMOVE key IN" in query:
            for key in bind_vars["keys"]:
                store.pop(key, None)
            return iter([])

        raise AssertionError(f"unhandled query: {query!r}")


class _FakeDb:
    def __init__(self, cols: dict[str, dict[str, dict]], indexes: dict[str, list[dict]] | None = None) -> None:
        self.cols = cols
        self.index_store = indexes or {}
        self._handles: dict[str, _FakeCollection] = {}
        self.aql = _FakeAql(self)

    def has_collection(self, name: str) -> bool:
        return name in self.cols

    def collection(self, name: str) -> _FakeCollection:
        if name not in self._handles:
            store = self.cols.setdefault(name, {})
            idx = self.index_store.setdefault(name, [])
            self._handles[name] = _FakeCollection(store, idx)
        return self._handles[name]


def _non_unique_index(collection: str) -> dict:
    return {
        "id": f"{collection}/uk_nonunique",
        "type": "persistent",
        "fields": list(_INDEX_FIELDS),
        "unique": False,
        "sparse": False,
    }


def _unique_index(collection: str) -> dict:
    return {
        "id": f"{collection}/uk_unique",
        "type": "persistent",
        "fields": list(_INDEX_FIELDS),
        "unique": True,
        "sparse": False,
    }


def _duplicate_db() -> _FakeDb:
    """A volume carrying duplicate singletons in BOTH collections, no unique index.

    * user_preferences: user ``u1`` has two docs — ``up_new`` (newer updated_at)
      and ``up_old`` (older) — plus a lone ``u2`` doc.
    * onboarding_states: user ``u1`` has two docs with equal timestamps, so the
      survivor is chosen by smallest ``_key`` (``os_a`` < ``os_b``).
    """
    return _FakeDb(
        cols={
            col.USER_PREFERENCES: {
                "up_old": {"_key": "up_old", "user_key": "u1", "updated_at": "2026-01-01T00:00:00+00:00"},
                "up_new": {"_key": "up_new", "user_key": "u1", "updated_at": "2026-06-01T00:00:00+00:00"},
                "up_solo": {"_key": "up_solo", "user_key": "u2", "updated_at": "2026-03-01T00:00:00+00:00"},
            },
            col.ONBOARDING_STATES: {
                "os_b": {"_key": "os_b", "user_key": "u1", "updated_at": "2026-02-02T00:00:00+00:00"},
                "os_a": {"_key": "os_a", "user_key": "u1", "updated_at": "2026-02-02T00:00:00+00:00"},
            },
        },
        indexes={
            col.USER_PREFERENCES: [_non_unique_index(col.USER_PREFERENCES)],
            col.ONBOARDING_STATES: [_non_unique_index(col.ONBOARDING_STATES)],
        },
    )


def _clean_unique_db() -> _FakeDb:
    """A fresh/already-migrated volume: no duplicates, unique index already present."""
    return _FakeDb(
        cols={
            col.USER_PREFERENCES: {"up1": {"_key": "up1", "user_key": "u1", "updated_at": "2026-01-01T00:00:00+00:00"}},
            col.ONBOARDING_STATES: {
                "os1": {"_key": "os1", "user_key": "u1", "updated_at": "2026-01-01T00:00:00+00:00"}
            },
        },
        indexes={
            col.USER_PREFERENCES: [_unique_index(col.USER_PREFERENCES)],
            col.ONBOARDING_STATES: [_unique_index(col.ONBOARDING_STATES)],
        },
    )


def _user_key_indexes(db: _FakeDb, collection: str) -> list[dict]:
    return [
        idx
        for idx in db.collection(collection).indexes()
        if idx.get("type") == "persistent" and idx.get("fields") == list(_INDEX_FIELDS)
    ]


class TestCollapseAndPromote:
    def test_duplicates_collapsed_and_index_promoted(self):
        db = _duplicate_db()
        report = migration.up(db)

        prefs = db.cols[col.USER_PREFERENCES]
        # Newest updated_at survives, older loser removed, lone doc untouched.
        assert "up_new" in prefs
        assert "up_old" not in prefs
        assert "up_solo" in prefs

        states = db.cols[col.ONBOARDING_STATES]
        # Equal timestamps → smallest _key wins.
        assert "os_a" in states
        assert "os_b" not in states

        for collection in _SINGLETON_COLLECTIONS:
            indexes = _user_key_indexes(db, collection)
            assert len(indexes) == 1
            assert indexes[0]["unique"] is True

        # 2 losers removed (up_old + os_b).
        assert report.scanned == 2
        assert report.details[col.USER_PREFERENCES]["removed_losers"] == 1
        assert report.details[col.ONBOARDING_STATES]["removed_losers"] == 1
        assert report.changed > 0

    def test_index_only_promoted_when_no_duplicates(self):
        db = _clean_unique_db()
        report = migration.up(db)

        for collection in _SINGLETON_COLLECTIONS:
            indexes = _user_key_indexes(db, collection)
            assert len(indexes) == 1
            assert indexes[0]["unique"] is True
        assert report.changed == 0
        assert report.noop is True


class TestIdempotency:
    def test_rerun_is_a_noop(self):
        db = _duplicate_db()
        migration.up(db)
        report = migration.up(db)

        assert report.changed == 0
        assert report.noop is True
        for collection in _SINGLETON_COLLECTIONS:
            indexes = _user_key_indexes(db, collection)
            assert len(indexes) == 1
            assert indexes[0]["unique"] is True


class TestDryRun:
    def test_dry_run_touches_neither_data_nor_index(self):
        db = _duplicate_db()
        report = migration.up(db, dry_run=True)

        assert report.dry_run is True
        assert report.changed == 0
        # Both duplicate losers still present; indexes still non-unique.
        assert "up_old" in db.cols[col.USER_PREFERENCES]
        assert "os_b" in db.cols[col.ONBOARDING_STATES]
        for collection in _SINGLETON_COLLECTIONS:
            indexes = _user_key_indexes(db, collection)
            assert len(indexes) == 1
            assert indexes[0]["unique"] is False
            assert report.details[collection]["will_create_unique_index"] is True
            assert report.details[collection]["will_drop_redundant_indexes"] == 1


class TestMetadataAndReversibility:
    def test_migration_metadata(self):
        assert migration.version == "0031"
        assert migration.name == "dedup_user_singletons_unique_index"
        assert migration.reversible is False

    def test_down_refuses(self):
        db = _clean_unique_db()
        try:
            migration.down(db)
        except IrreversibleMigrationError:
            return
        raise AssertionError("down() must raise IrreversibleMigrationError")
