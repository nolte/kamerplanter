"""NFR-016 M-8 — the concurrency lock blocks a second runner, frees on release."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.data_access.arango.collections import SCHEMA_MIGRATIONS
from app.migrations.framework import tracking
from app.migrations.framework.report import MigrationLockError


class TestMigrationLock:
    def test_second_acquire_is_blocked(self, fake_db):
        tracking.acquire_lock(fake_db)
        with pytest.raises(MigrationLockError):
            tracking.acquire_lock(fake_db)

    def test_release_allows_reacquire(self, fake_db):
        tracking.acquire_lock(fake_db)
        tracking.release_lock(fake_db)
        # Must not raise now that the lock is free.
        tracking.acquire_lock(fake_db)

    def test_release_is_idempotent(self, fake_db):
        tracking.release_lock(fake_db)  # nothing held — no error

    def test_stale_lock_is_taken_over(self, fake_db):
        stale = (datetime.now(UTC) - timedelta(seconds=tracking.LOCK_TTL_SECONDS + 60)).isoformat()
        fake_db.collection(SCHEMA_MIGRATIONS).insert({"_key": tracking.LOCK_KEY, "acquired_at": stale})

        # A lock older than the TTL is orphaned and may be taken over.
        lock = tracking.acquire_lock(fake_db)
        assert lock["_key"] == tracking.LOCK_KEY
        # The acquired_at was refreshed to "now".
        refreshed = fake_db.collection(SCHEMA_MIGRATIONS).get(tracking.LOCK_KEY)["acquired_at"]
        assert refreshed != stale
