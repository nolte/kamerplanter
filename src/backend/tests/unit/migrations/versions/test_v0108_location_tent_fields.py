"""Tests for v0108_location_tent_fields (REQ-053 WP 10.11, #2832, W-016).

Against a fake ArangoDB: a location carrying a value the new ``Location`` model refuses under ``adjacency_factor`` or
``lighting`` loses exactly that value; a readable value (including an explicit ``null``) and a location without either
name are never touched; nothing is materialised. Plus the framework duties: idempotent (M-3), dry run writes nothing
(M-5), irreversible and honest about it (M-6), and the frozen bounds agree with today's model.
"""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from app.data_access.arango import collections as col
from app.domain.models.site import MAX_ADJACENCY_FACTOR, MAX_LAMP_HEIGHT_CM, Location
from app.migrations.framework.report import IrreversibleMigrationError
from app.migrations.versions.v0108_location_tent_fields import LocationTentFieldsMigration, migration


class _FakeAql:
    def __init__(self, documents: list[dict[str, Any]]) -> None:
        self._documents = documents
        self.writes = 0

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        bind_vars = bind_vars or {}
        assert bind_vars.get("@locations") == col.LOCATIONS
        if query.lstrip().startswith("UPDATE"):
            assert "keepNull: false" in query
            field = "adjacency_factor" if "adjacency_factor: null" in query else "lighting"
            for doc in self._documents:
                if doc["_key"] == bind_vars["key"]:
                    doc.pop(field, None)
                    self.writes += 1
            return iter([])
        rows = [
            {
                "key": doc["_key"],
                "has_factor": "adjacency_factor" in doc,
                "factor": doc.get("adjacency_factor"),
                "has_lighting": "lighting" in doc,
                "lighting": doc.get("lighting"),
            }
            for doc in sorted(self._documents, key=lambda d: d["_key"])
            if "adjacency_factor" in doc or "lighting" in doc
        ]
        return iter(rows)


class _FakeDb:
    def __init__(self, documents: list[dict[str, Any]] | None) -> None:
        self._documents = documents
        self.aql = _FakeAql(documents or [])

    def has_collection(self, name: str) -> bool:
        return self._documents is not None and name == col.LOCATIONS

    def doc(self, key: str) -> dict[str, Any]:
        return next(d for d in self._documents or [] if d["_key"] == key)


def _loc(key: str, **fields: Any) -> dict[str, Any]:
    return {"_key": key, "name": key, "site_key": "s1", "area_m2": 1.0, **fields}


READABLE_LIGHTING: list[Any] = [
    None,
    {},
    {"lamp_height_cm": 180},
    {"lamp_height_cm": 180, "canopy_distance_cm": 180},
    {"canopy_distance_cm": 0},
    {"fixture_geometry": {"kind": "rect", "origin": [0.1, 0.1], "width_m": 0.6, "length_m": 0.6}},
]
UNREADABLE_LIGHTING: list[Any] = [
    "LED 600W",
    {"lamp_height_cm": 0},
    {"lamp_height_cm": 1200},
    {"lamp_height_cm": "180"},
    {"lamp_height_cm": True},
    {"canopy_distance_cm": -5},
    {"lamp_height_cm": 50, "canopy_distance_cm": 80},
    {"lamp_height_cm": 50, "wattage": 600},
    {"fixture_geometry": {"kind": "point", "origin": [0.1, 0.1]}},
    {"fixture_geometry": "rect"},
]


class TestUp:
    def test_refused_values_are_removed_field_by_field(self) -> None:
        db = _FakeDb(
            [
                _loc("a", adjacency_factor=0, lighting={"lamp_height_cm": 180}),
                _loc("b", adjacency_factor=2.0, lighting={"lamp_height_cm": -1}),
                _loc("c"),
            ]
        )

        report = migration.up(db)

        assert "adjacency_factor" not in db.doc("a")
        assert db.doc("a")["lighting"] == {"lamp_height_cm": 180}
        assert db.doc("b")["adjacency_factor"] == 2.0
        assert "lighting" not in db.doc("b")
        assert db.doc("c") == _loc("c")
        assert report.scanned == 2
        assert report.changed == 2
        assert report.details == {"cleared_adjacency_factor": 1, "cleared_lighting": 1}

    def test_nothing_is_materialised_on_a_location_without_the_fields(self) -> None:
        db = _FakeDb([_loc("a"), _loc("b")])

        report = migration.up(db)

        assert db.doc("a") == _loc("a") and db.doc("b") == _loc("b")
        assert (report.scanned, report.changed, db.aql.writes) == (0, 0, 0)

    @pytest.mark.parametrize("factor", [None, 0.1, 1.5, 10.0, 10])
    def test_a_readable_factor_is_kept(self, factor: Any) -> None:
        db = _FakeDb([_loc("a", adjacency_factor=factor)])

        migration.up(db)

        assert db.doc("a")["adjacency_factor"] == factor

    @pytest.mark.parametrize("factor", [0, -1, 10.5, "1.5", True, float("nan"), float("inf"), [1.5]])
    def test_an_unreadable_factor_is_removed(self, factor: Any) -> None:
        db = _FakeDb([_loc("a", adjacency_factor=factor)])

        migration.up(db)

        assert "adjacency_factor" not in db.doc("a")

    @pytest.mark.parametrize("lighting", READABLE_LIGHTING)
    def test_a_readable_lighting_is_kept(self, lighting: Any) -> None:
        db = _FakeDb([_loc("a", lighting=lighting)])

        migration.up(db)

        assert db.doc("a")["lighting"] == lighting

    @pytest.mark.parametrize("lighting", UNREADABLE_LIGHTING)
    def test_an_unreadable_lighting_is_removed(self, lighting: Any) -> None:
        db = _FakeDb([_loc("a", lighting=lighting)])

        migration.up(db)

        assert "lighting" not in db.doc("a")

    def test_idempotent(self) -> None:
        db = _FakeDb([_loc("a", adjacency_factor=-1, lighting="x"), _loc("b", adjacency_factor=1.2)])

        first = migration.up(db)
        second = migration.up(db)

        assert first.changed == 2
        assert second.changed == 0
        assert second.details == {"cleared_adjacency_factor": 0, "cleared_lighting": 0}
        assert db.aql.writes == 2

    def test_dry_run_writes_nothing(self) -> None:
        db = _FakeDb([_loc("a", adjacency_factor=-1, lighting="x")])

        report = migration.up(db, dry_run=True)

        assert db.doc("a")["adjacency_factor"] == -1 and db.doc("a")["lighting"] == "x"
        assert (report.dry_run, report.scanned, report.changed, db.aql.writes) == (True, 1, 0, 0)
        assert report.details == {"will_clear_adjacency_factor": 1, "will_clear_lighting": 1}

    def test_missing_collection_is_a_noop(self) -> None:
        report = migration.up(_FakeDb(None))

        assert (report.scanned, report.changed) == (0, 0)


def test_down_is_honestly_irreversible() -> None:
    assert migration.reversible is False
    with pytest.raises(IrreversibleMigrationError):
        migration.down(_FakeDb([]))


class TestFrozenRulesAgreeWithTheModel:
    """The frozen bounds of v0108 must say what today's ``Location`` says, or the migration keeps a value that 500s."""

    def test_bounds(self) -> None:
        assert LocationTentFieldsMigration.MAX_FACTOR == MAX_ADJACENCY_FACTOR
        assert LocationTentFieldsMigration.MAX_LAMP_HEIGHT_CM == MAX_LAMP_HEIGHT_CM

    @pytest.mark.parametrize("lighting", READABLE_LIGHTING)
    def test_what_the_migration_keeps_the_model_reads(self, lighting: Any) -> None:
        Location(name="x", area_m2=1.0, lighting=lighting)

    @pytest.mark.parametrize("lighting", [v for v in UNREADABLE_LIGHTING if not isinstance(v, dict) or v])
    def test_what_the_migration_removes_the_model_refuses(self, lighting: Any) -> None:
        with pytest.raises(ValidationError):
            Location.model_validate({"name": "x", "area_m2": 1.0, "lighting": lighting})

    @pytest.mark.parametrize("factor", [0, -1, 10.5, "1.5", True, float("nan"), float("inf"), [1.5]])
    def test_a_removed_factor_is_one_the_model_refuses(self, factor: float) -> None:
        with pytest.raises(ValidationError):
            Location.model_validate({"name": "x", "area_m2": 1.0, "adjacency_factor": factor})
