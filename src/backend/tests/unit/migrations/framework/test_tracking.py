"""NFR-016 M-2 — schema_migrations tracking: record/applied/current/history."""

from __future__ import annotations

from app.migrations.framework import tracking


class TestTracking:
    def test_record_and_applied_versions(self, fake_db, make_migration):
        tracking.record(fake_db, make_migration("0001"), 12.0)
        tracking.record(fake_db, make_migration("0002"), 8.0)

        assert tracking.applied_versions(fake_db) == {"0001", "0002"}

    def test_record_is_idempotent_overwrite(self, fake_db, make_migration):
        tracking.record(fake_db, make_migration("0001"), 12.0)
        tracking.record(fake_db, make_migration("0001"), 99.0)

        history = tracking.history(fake_db)
        assert len(history) == 1
        assert history[0]["duration_ms"] == 99.0

    def test_current_returns_highest_version(self, fake_db, make_migration):
        assert tracking.current(fake_db) is None
        tracking.record(fake_db, make_migration("0001"), 1.0)
        tracking.record(fake_db, make_migration("0003"), 1.0)
        tracking.record(fake_db, make_migration("0002"), 1.0)

        assert tracking.current(fake_db) == "0003"

    def test_history_is_ordered_and_excludes_lock(self, fake_db, make_migration):
        tracking.record(fake_db, make_migration("0002"), 1.0)
        tracking.record(fake_db, make_migration("0001"), 1.0)
        tracking.acquire_lock(fake_db)  # inserts the __lock__ sentinel

        history = tracking.history(fake_db)
        assert [row["version"] for row in history] == ["0001", "0002"]

    def test_checksum_of_roundtrip(self, fake_db, make_migration):
        migration = make_migration("0001", checksum_override="abc123")
        tracking.record(fake_db, migration, 1.0)

        assert tracking.checksum_of(fake_db, "0001") == "abc123"
        assert tracking.checksum_of(fake_db, "9999") is None

    def test_remove_deletes_record(self, fake_db, make_migration):
        tracking.record(fake_db, make_migration("0001"), 1.0)
        tracking.remove(fake_db, "0001")

        assert tracking.applied_versions(fake_db) == set()
        # Removing a non-existent version is a safe no-op.
        tracking.remove(fake_db, "0001")
