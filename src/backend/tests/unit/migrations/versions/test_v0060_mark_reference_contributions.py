"""Tests for v0060_mark_reference_contributions (#1753 backfill).

The contribution marker (``system_settings.reference_contributions_since``) is
written by the contribution path from #1753 on. Deployments that accepted
contributions before have none, so a flagless celery-worker would still report
"nothing to delete". v0060 sets it once where the migrating process — the
backend, which runs migrations in its lifespan — has the inference-service
flag. Pinned here against a fake that records the statement and its binds;
the atomic "only when absent" semantics are measured against a server in
``tests/integration/test_v0060_mark_reference_contributions.py``.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.config.settings import settings
from app.data_access.arango import collections as col
from app.migrations.framework.report import IrreversibleMigrationError
from app.migrations.versions.v0060_mark_reference_contributions import migration


class _Db:
    def __init__(self, *, marker: str | None = None, has_collection: bool = True) -> None:
        self._has = has_collection
        self.doc: dict[str, Any] | None = {"_key": "default"} if has_collection else None
        if marker is not None and self.doc is not None:
            self.doc["reference_contributions_since"] = marker
        self.statements: list[tuple[str, dict[str, Any]]] = []
        self.created: list[str] = []
        self.aql = self

    def has_collection(self, name: str) -> bool:
        return self._has

    def create_collection(self, name: str) -> None:
        self.created.append(name)
        self._has = True

    def collection(self, name: str):
        db = self

        class _C:
            def get(self, key: str):
                return db.doc

        return _C()

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        self.statements.append((query, dict(bind_vars or {})))
        return iter([])


@pytest.fixture
def enabled(monkeypatch):
    monkeypatch.setattr(settings, "inference_service_enabled", True)


def test_metadata():
    assert migration.version == "0060"
    assert migration.name == "mark_reference_contributions"
    assert migration.reversible is False
    with pytest.raises(IrreversibleMigrationError):
        migration.down(_Db())


def test_enabled_process_without_marker_sets_it_through_the_conditional_upsert(enabled):
    db = _Db()

    report = migration.up(db)

    ((query, binds),) = db.statements
    assert "UPSERT" in query and "OLD.reference_contributions_since == null" in query
    assert binds["@collection"] == col.SYSTEM_SETTINGS
    assert binds["key"] == "default"
    assert binds["now"]
    assert report.changed == 1
    assert report.details["marked"] is True


def test_an_existing_marker_is_left_alone(enabled):
    db = _Db(marker="2026-01-01T00:00:00+00:00")

    report = migration.up(db)

    assert db.statements == []
    assert report.changed == 0
    assert report.details["reason"] == "marker_present"


def test_a_process_without_the_flag_marks_nothing(monkeypatch):
    monkeypatch.setattr(settings, "inference_service_enabled", False)
    db = _Db()

    report = migration.up(db)

    assert db.statements == []
    assert report.changed == 0
    assert report.details["reason"] == "inference_service_disabled"


def test_dry_run_writes_nothing(enabled):
    db = _Db(has_collection=False)

    report = migration.up(db, dry_run=True)

    assert db.statements == [] and db.created == []
    assert report.dry_run is True
    assert report.changed == 0
    assert report.details["marked"] is True


def test_a_missing_collection_is_created_before_the_marker(enabled):
    db = _Db(has_collection=False)

    report = migration.up(db)

    assert db.created == [col.SYSTEM_SETTINGS]
    assert len(db.statements) == 1
    assert report.changed == 1
