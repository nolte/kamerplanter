"""Tests for v0061_mark_pest_prototype_contributions (#1759 backfill).

The pest-prototype marker is written by the promotion index task from #1759 on.
Deployments that indexed promotions before have none; v0061 sets it where the
backend reaches the inference-service and a contribution was ever promoted.
Pinned against a fake that answers the "any promoted" read and records the
write; the statement semantics are measured against a server in
``tests/integration/test_v0061_mark_pest_prototype_contributions.py``.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.config.settings import settings
from app.data_access.arango import collections as col
from app.migrations.framework.report import IrreversibleMigrationError
from app.migrations.versions.v0061_mark_pest_prototype_contributions import migration


class _Db:
    def __init__(self, *, marker: str | None = None, promoted: bool = True, collections: bool = True) -> None:
        self._collections = {col.SYSTEM_SETTINGS, col.PEST_IMAGE_CONTRIBUTIONS} if collections else set()
        self.doc: dict[str, Any] = {"_key": "default"}
        if marker is not None:
            self.doc["pest_prototype_contributions_since"] = marker
        self._promoted = promoted
        self.writes: list[tuple[str, dict[str, Any]]] = []
        self.created: list[str] = []
        self.aql = self

    def has_collection(self, name: str) -> bool:
        return name in self._collections

    def create_collection(self, name: str) -> None:
        self.created.append(name)
        self._collections.add(name)

    def collection(self, name: str):  # type: ignore[no-untyped-def]
        db = self

        class _C:
            def get(self, key: str):  # type: ignore[no-untyped-def]
                return db.doc

        return _C()

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):  # type: ignore[no-untyped-def]
        if "promoted_at != null" in query:
            assert bind_vars == {"@collection": col.PEST_IMAGE_CONTRIBUTIONS}
            return iter([self._promoted])
        self.writes.append((query, dict(bind_vars or {})))
        return iter([])


@pytest.fixture
def pest_enabled(monkeypatch):
    monkeypatch.setattr(settings, "pest_detection_enabled", True)
    monkeypatch.setattr(settings, "inference_service_enabled", False)


def test_metadata():
    assert migration.version == "0061"
    assert migration.reversible is False
    with pytest.raises(IrreversibleMigrationError):
        migration.down(_Db())


@pytest.mark.parametrize(("pest", "inference"), [(True, False), (False, True)])
def test_a_reaching_process_with_a_promoted_contribution_sets_the_marker(monkeypatch, pest, inference):
    monkeypatch.setattr(settings, "pest_detection_enabled", pest)
    monkeypatch.setattr(settings, "inference_service_enabled", inference)
    db = _Db()

    report = migration.up(db)

    ((query, binds),) = db.writes
    assert "UPSERT" in query and "OLD.pest_prototype_contributions_since == null" in query
    assert (binds["@collection"], binds["key"]) == (col.SYSTEM_SETTINGS, "default")
    assert report.changed == 1 and report.details["marked"] is True


def test_no_promoted_contribution_marks_nothing(pest_enabled):
    db = _Db(promoted=False)

    report = migration.up(db)

    assert db.writes == []
    assert report.details["reason"] == "no_promoted_contribution"


def test_a_missing_contributions_collection_marks_nothing(pest_enabled):
    db = _Db(collections=False)

    report = migration.up(db)

    assert db.writes == [] and db.created == []
    assert report.details["reason"] == "no_promoted_contribution"


def test_an_existing_marker_is_left_alone(pest_enabled):
    db = _Db(marker="2026-01-01T00:00:00+00:00")

    report = migration.up(db)

    assert db.writes == []
    assert report.details["reason"] == "marker_present"


def test_a_process_without_either_flag_marks_nothing(monkeypatch):
    monkeypatch.setattr(settings, "pest_detection_enabled", False)
    monkeypatch.setattr(settings, "inference_service_enabled", False)
    db = _Db()

    report = migration.up(db)

    assert db.writes == []
    assert report.details["reason"] == "inference_service_unreachable_from_backend"


def test_dry_run_writes_nothing(pest_enabled):
    db = _Db()

    report = migration.up(db, dry_run=True)

    assert db.writes == []
    assert report.changed == 0 and report.details["marked"] is True
