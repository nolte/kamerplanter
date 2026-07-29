"""Tests for v0032_two_axis_role_model (REQ-049, #780).

The migration maps the retired membership role ``admin`` onto the two axes —
role ``lead`` plus both administrative scopes — backfills ``admin_scopes`` on
every other membership, and indexes the scopes for the INV-1 guard.

Covered:
  * the mapping is rights-preserving and lossless (AK-07): every ``admin``
    becomes ``lead`` + both scopes, ``grower``/``viewer`` keep their role and
    get an empty scope list, and no membership disappears;
  * the ``platform`` tenant migrates like any other — excluding it would leave
    the installation with no platform admin at all;
  * a membership that already carries ``admin_scopes`` is left alone, so a
    re-run cannot restore scopes an operator has since removed;
  * idempotency — a second run finds nothing to do (``changed == 0``);
  * dry-run writes nothing, neither documents nor the index;
  * a fresh volume that already carries the bootstrap index creates no second one;
  * ``down`` refuses (irreversible).
"""

from __future__ import annotations

import pytest

from app.data_access.arango import collections as col
from app.migrations.framework.report import IrreversibleMigrationError
from app.migrations.versions.v0032_two_axis_role_model import _INDEX_FIELDS, migration


class _FakeCollection:
    def __init__(self, indexes: list[dict]) -> None:
        self._indexes = indexes
        self._seq = [0]

    def indexes(self) -> list[dict]:
        return [dict(i) for i in self._indexes]

    def add_persistent_index(self, *, fields, unique: bool = False, **_):
        self._seq[0] += 1
        record = {"id": f"idx/{self._seq[0]}", "type": "persistent", "fields": list(fields), "unique": unique}
        self._indexes.append(record)
        return record


class _FakeAql:
    def __init__(self, db: _FakeDb) -> None:
        self._db = db

    def execute(self, query: str, bind_vars: dict | None = None):
        bind_vars = bind_vars or {}
        store = self._db.memberships

        # The UPDATE query mentions both count predicates, so it has to be
        # matched first — dispatching on the counts would silently turn the
        # write into a read and make every mapping assertion vacuous.
        if "UPDATE doc WITH" in query:
            retired = bind_vars["retired"]
            replacement = bind_vars["replacement"]
            full_scopes = bind_vars["full_scopes"]
            touched = 0
            for doc in store.values():
                was_admin = doc.get("role") == retired
                needs_role = was_admin
                needs_scopes = doc.get("admin_scopes") is None
                if not (needs_role or needs_scopes):
                    continue
                if needs_role:
                    doc["role"] = replacement
                if needs_scopes:
                    doc["admin_scopes"] = list(full_scopes) if was_admin else []
                touched += 1
            return iter([touched])

        if "doc.role == @role" in query:
            return iter([sum(1 for d in store.values() if d.get("role") == bind_vars["role"])])

        if "doc.admin_scopes == null" in query:
            return iter([sum(1 for d in store.values() if d.get("admin_scopes") is None)])

        raise AssertionError(f"unexpected query: {query}")


class _FakeDb:
    def __init__(self, memberships: dict[str, dict], indexes: list[dict] | None = None) -> None:
        self.memberships = memberships
        self._indexes = indexes if indexes is not None else []
        self.aql = _FakeAql(self)

    def has_collection(self, name: str) -> bool:
        return name == col.MEMBERSHIPS

    def collection(self, name: str) -> _FakeCollection:
        assert name == col.MEMBERSHIPS
        return _FakeCollection(self._indexes)


def _legacy_volume() -> dict[str, dict]:
    return {
        "m1": {"_key": "m1", "user_key": "u1", "tenant_key": "t1", "role": "admin", "is_active": True},
        "m2": {"_key": "m2", "user_key": "u2", "tenant_key": "t1", "role": "grower", "is_active": True},
        "m3": {"_key": "m3", "user_key": "u3", "tenant_key": "t1", "role": "viewer", "is_active": False},
        # The platform membership is what marks a platform admin (REQ-049 §2.5).
        "m4": {"_key": "m4", "user_key": "u1", "tenant_key": "platform", "role": "admin", "is_active": True},
    }


class TestMapping:
    def test_admin_becomes_lead_with_both_scopes(self):
        db = _FakeDb(_legacy_volume())

        migration.up(db)

        assert db.memberships["m1"]["role"] == "lead"
        assert db.memberships["m1"]["admin_scopes"] == ["management", "technical"]

    def test_platform_membership_migrates_like_any_other(self):
        # Excluding it would leave the installation with no platform admin, and
        # the failure would surface as an inexplicable 403 rather than an error.
        db = _FakeDb(_legacy_volume())

        migration.up(db)

        assert db.memberships["m4"]["role"] == "lead"
        assert db.memberships["m4"]["admin_scopes"] == ["management", "technical"]

    def test_other_roles_keep_their_role_and_get_no_scopes(self):
        db = _FakeDb(_legacy_volume())

        migration.up(db)

        assert db.memberships["m2"]["role"] == "grower"
        assert db.memberships["m2"]["admin_scopes"] == []
        assert db.memberships["m3"]["role"] == "viewer"
        assert db.memberships["m3"]["admin_scopes"] == []

    def test_no_membership_is_lost(self):
        db = _FakeDb(_legacy_volume())

        migration.up(db)

        assert set(db.memberships) == {"m1", "m2", "m3", "m4"}

    def test_existing_scopes_are_not_overwritten(self):
        # A re-run must not restore scopes an operator has since removed.
        db = _FakeDb(
            {
                "m1": {"_key": "m1", "tenant_key": "t1", "role": "lead", "admin_scopes": []},
            }
        )

        migration.up(db)

        assert db.memberships["m1"]["admin_scopes"] == []


class TestReporting:
    def test_report_counts_what_it_touched(self):
        db = _FakeDb(_legacy_volume())

        report = migration.up(db)

        # 2 admins + 4 memberships without scopes; 4 documents updated + 1 index.
        assert report.scanned == 6
        assert report.changed == 5
        assert report.details["memberships_with_retired_admin_role"] == 2
        assert report.details["scope_index_created"] is True


class TestIdempotency:
    def test_second_run_changes_nothing(self):
        db = _FakeDb(_legacy_volume())
        migration.up(db)

        report = migration.up(db)

        assert report.changed == 0
        assert report.scanned == 0


class TestDryRun:
    def test_dry_run_writes_nothing(self):
        db = _FakeDb(_legacy_volume())

        report = migration.up(db, dry_run=True)

        assert report.dry_run is True
        assert report.changed == 0
        assert db.memberships["m1"]["role"] == "admin"
        assert "admin_scopes" not in db.memberships["m1"]
        assert db._indexes == []

    def test_dry_run_previews_every_job(self):
        db = _FakeDb(_legacy_volume())

        report = migration.up(db, dry_run=True)

        assert report.details["memberships_with_retired_admin_role"] == 2
        assert report.details["memberships_without_admin_scopes"] == 4
        assert report.details["will_create_scope_index"] is True


class TestBootstrappedVolume:
    def test_existing_index_is_not_duplicated(self):
        db = _FakeDb(
            {},
            indexes=[{"id": "idx/0", "type": "persistent", "fields": list(_INDEX_FIELDS), "unique": False}],
        )

        report = migration.up(db)

        assert report.changed == 0
        assert len(db._indexes) == 1


class TestIrreversible:
    def test_down_refuses(self):
        with pytest.raises(IrreversibleMigrationError):
            migration.down(_FakeDb({}))
