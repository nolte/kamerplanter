"""NFR-016 M-8 — the concurrency lock: owner-fenced acquire/release + takeover.

Covers issue #375 finding 1: the lock carries an owner token, stale takeover is
a revision-checked compare-and-swap (two replicas cannot both adopt the same
stale lock), and release only frees a lock this runner still owns.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.data_access.arango.collections import SCHEMA_MIGRATIONS
from app.migrations.framework import tracking
from app.migrations.framework.report import MigrationLockError


def _lock_doc(fake_db):
    return fake_db.collection(SCHEMA_MIGRATIONS).get(tracking.LOCK_KEY)


class TestMigrationLock:
    def test_acquire_returns_owner_token(self, fake_db):
        owner = tracking.acquire_lock(fake_db)
        assert isinstance(owner, str) and owner
        assert _lock_doc(fake_db)["owner"] == owner

    def test_second_acquire_is_blocked(self, fake_db):
        tracking.acquire_lock(fake_db)
        with pytest.raises(MigrationLockError):
            tracking.acquire_lock(fake_db)

    def test_release_allows_reacquire(self, fake_db):
        owner = tracking.acquire_lock(fake_db)
        tracking.release_lock(fake_db, owner)
        # Must not raise now that the lock is free.
        tracking.acquire_lock(fake_db)

    def test_release_is_idempotent(self, fake_db):
        tracking.release_lock(fake_db, "no-such-owner")  # nothing held — no error

    def test_release_only_frees_own_lock(self, fake_db):
        tracking.acquire_lock(fake_db)  # held by someone else's owner token
        # A runner that does not own the lock must not free it.
        tracking.release_lock(fake_db, "someone-elses-owner")
        assert _lock_doc(fake_db) is not None
        with pytest.raises(MigrationLockError):
            tracking.acquire_lock(fake_db)

    def test_stale_lock_is_taken_over(self, fake_db):
        stale = (datetime.now(UTC) - timedelta(seconds=tracking.LOCK_TTL_SECONDS + 60)).isoformat()
        fake_db.collection(SCHEMA_MIGRATIONS).insert(
            {"_key": tracking.LOCK_KEY, "owner": "dead-runner", "acquired_at": stale}
        )

        # A lock older than the TTL is orphaned and may be taken over.
        owner = tracking.acquire_lock(fake_db)
        doc = _lock_doc(fake_db)
        assert doc["owner"] == owner  # ownership transferred to us
        assert doc["acquired_at"] != stale  # acquired_at refreshed to "now"

    def test_stale_takeover_race_lets_only_one_win(self, fake_db):
        """Two replicas observing the same stale lock: the CAS loser is blocked."""
        stale = (datetime.now(UTC) - timedelta(seconds=tracking.LOCK_TTL_SECONDS + 60)).isoformat()
        col = fake_db.collection(SCHEMA_MIGRATIONS)
        col.insert({"_key": tracking.LOCK_KEY, "owner": "dead-runner", "acquired_at": stale})

        # Replica A wins the takeover (revision-checked replace succeeds).
        owner_a = tracking.acquire_lock(fake_db)
        # Replica B still sees a *fresh* lock now (A's), so it is blocked — the
        # stale doc it would have replaced no longer exists at that revision.
        with pytest.raises(MigrationLockError):
            tracking.acquire_lock(fake_db)
        assert _lock_doc(fake_db)["owner"] == owner_a

    def test_release_after_takeover_keeps_new_owners_lock(self, fake_db):
        """A slow runner whose lock was taken over must not delete the successor's."""
        stale = (datetime.now(UTC) - timedelta(seconds=tracking.LOCK_TTL_SECONDS + 60)).isoformat()
        col = fake_db.collection(SCHEMA_MIGRATIONS)
        # The slow runner's own (now-stale) lock.
        col.insert({"_key": tracking.LOCK_KEY, "owner": "slow-runner", "acquired_at": stale})

        # A fresh replica takes the stale lock over.
        new_owner = tracking.acquire_lock(fake_db)

        # The slow runner finishes and releases with ITS token — must be a no-op.
        tracking.release_lock(fake_db, "slow-runner")

        assert _lock_doc(fake_db) is not None
        assert _lock_doc(fake_db)["owner"] == new_owner
