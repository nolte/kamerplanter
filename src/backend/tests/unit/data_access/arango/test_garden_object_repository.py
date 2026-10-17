"""REQ-053 §20.4 (WP 1.7, #2326) — ``ArangoGardenObjectRepository`` over a capturing database double.

The create writes the ``has_garden_object`` edge from the site; every read
takes the tenant keyword-only and joins the object's site on it inside the
query (E-01: the row has no ``tenant_key``); the delete cuts every edge on the
end it is written on (the #1535 shape: an edge removed on the wrong end
matches nothing and stays behind).
"""

from __future__ import annotations

from typing import Any

import pytest

from app.common.exceptions import NotFoundError
from app.data_access.arango import collections as col
from app.data_access.arango.garden_object_repository import ArangoGardenObjectRepository
from app.domain.models.garden_object import GardenObject

TENANT = "tenant_own"

_DOC = {
    "_key": "go_1",
    "site_key": "site_1",
    "object_type": "water_source",
    "label": "Regentonne",
    "geometry": {"kind": "point", "origin": [9.7, 0.4]},
    "props": {"object_type": "water_source", "water_source_kind": "rain_barrel"},
    "created_at": "2026-10-16T00:00:00Z",
    "updated_at": "2026-10-16T00:00:00Z",
}


class _CapturingAql:
    def __init__(self, rows: list[dict[str, Any]] | None = None, owner_tenant: str | None = None) -> None:
        self.calls: list[dict[str, Any]] = []
        self.rows = rows or []
        #: When set, the double plays the site join: rows come back only for the owning tenant.
        self.owner_tenant = owner_tenant

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        self.calls.append({"query": query, "bind_vars": bind_vars or {}})
        if self.owner_tenant is not None and (bind_vars or {}).get("tenant_key") != self.owner_tenant:
            return iter([])
        return iter(self.rows)


class _FakeCollection:
    def __init__(self) -> None:
        self.inserted: list[dict[str, Any]] = []
        self.deleted: list[str] = []
        self.docs: dict[str, dict[str, Any]] = {}

    def insert(self, data: dict[str, Any], return_new: bool = False) -> dict[str, Any]:
        self.inserted.append(data)
        new = {"_key": "go_new", "_id": f"{col.GARDEN_OBJECTS}/go_new", **data}
        return {"new": new}

    def delete(self, key: str) -> None:
        self.deleted.append(key)

    def update(self, data: dict[str, Any], return_new: bool = False, keep_none: bool = True) -> dict[str, Any]:
        stored = {**self.docs[data["_key"]], **data}
        if not keep_none:
            stored = {k: v for k, v in stored.items() if v is not None}
        self.docs[data["_key"]] = stored
        return {"new": stored}


class _CapturingDb:
    def __init__(self, rows: list[dict[str, Any]] | None = None, owner_tenant: str | None = None) -> None:
        self.aql = _CapturingAql(rows, owner_tenant)
        self.collections: dict[str, _FakeCollection] = {}

    def collection(self, name: str) -> _FakeCollection:
        return self.collections.setdefault(name, _FakeCollection())


def _edge_calls(db: _CapturingDb, edge_collection: str) -> list[dict[str, Any]]:
    return [c for c in db.aql.calls if c["bind_vars"].get("@edge") == edge_collection]


def _object() -> GardenObject:
    return GardenObject.model_validate({k: v for k, v in _DOC.items() if k not in ("_key", "created_at", "updated_at")})


class TestCreate:
    def test_writes_the_document_and_the_site_edge(self) -> None:
        db = _CapturingDb()
        repo = ArangoGardenObjectRepository(db)

        created = repo.create_garden_object(_object())

        assert created.key == "go_new"
        inserted = db.collections[col.GARDEN_OBJECTS].inserted[0]
        assert inserted["site_key"] == "site_1"
        assert inserted["props"] == {"object_type": "water_source", "water_source_kind": "rain_barrel"}
        assert inserted["bbox"] == [9.45, 0.15, 9.95, 0.65]
        assert "tenant_key" not in inserted
        edges = db.collections[col.HAS_GARDEN_OBJECT].inserted
        assert [(e["_from"], e["_to"]) for e in edges] == [(f"{col.SITES}/site_1", f"{col.GARDEN_OBJECTS}/go_new")]

    def test_an_object_without_a_site_is_rejected_not_orphaned(self) -> None:
        db = _CapturingDb()
        repo = ArangoGardenObjectRepository(db)

        with pytest.raises(ValueError, match="site_key"):
            repo.create_garden_object(_object().model_copy(update={"site_key": ""}))

        assert col.GARDEN_OBJECTS not in db.collections


class TestReadsJoinTheSiteOnTheTenant:
    """The predicate is on the *same expression* the rule is about: the site join and the bound tenant."""

    def test_by_site_filters_on_the_site_key_and_the_site_s_tenant(self) -> None:
        db = _CapturingDb(rows=[dict(_DOC)])
        repo = ArangoGardenObjectRepository(db)

        objects = repo.get_garden_objects_by_site("site_1", tenant_key=TENANT)

        assert [o.key for o in objects] == ["go_1"]
        call = db.aql.calls[0]
        assert "FILTER o.site_key == @site_key" in call["query"]
        assert "DOCUMENT(CONCAT(@sites, o.site_key))" in call["query"]
        assert "site.tenant_key == @tenant_key" in call["query"]
        assert call["bind_vars"] == {
            "@col": col.GARDEN_OBJECTS,
            "site_key": "site_1",
            "sites": f"{col.SITES}/",
            "tenant_key": TENANT,
        }

    def test_by_key_reads_through_the_site_s_tenant(self) -> None:
        db = _CapturingDb(rows=[dict(_DOC)])
        repo = ArangoGardenObjectRepository(db)

        obj = repo.get_garden_object_by_key("go_1", tenant_key=TENANT)

        assert obj is not None and obj.key == "go_1" and obj.bbox == (9.45, 0.15, 9.95, 0.65)
        call = db.aql.calls[0]
        assert "DOCUMENT(CONCAT(@objects, @key))" in call["query"]
        assert "site.tenant_key == @tenant_key" in call["query"]
        assert call["bind_vars"]["tenant_key"] == TENANT

    def test_a_foreign_or_missing_object_answers_none_and_404(self) -> None:
        db = _CapturingDb(rows=[dict(_DOC)], owner_tenant=TENANT)
        repo = ArangoGardenObjectRepository(db)

        assert repo.get_garden_object_by_key("go_1", tenant_key="tenant_other") is None
        with pytest.raises(NotFoundError):
            repo.get_garden_object_or_raise("go_1", tenant_key="tenant_other")
        # Counter-probe: the same double hands the row to the owner, so the None above is the tenant's doing.
        owned = repo.get_garden_object_by_key("go_1", tenant_key=TENANT)
        assert owned is not None and owned.key == "go_1"
        assert repo.get_garden_objects_by_site("site_1", tenant_key="tenant_other") == []

    @pytest.mark.parametrize("tenant_key", ["", None])
    def test_an_empty_tenant_is_refused_before_the_query(self, tenant_key: str | None) -> None:
        db = _CapturingDb(rows=[dict(_DOC)])
        repo = ArangoGardenObjectRepository(db)

        with pytest.raises(ValueError):
            repo.get_garden_objects_by_site("site_1", tenant_key=tenant_key)  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            repo.get_garden_object_by_key("go_1", tenant_key=tenant_key)  # type: ignore[arg-type]
        assert db.aql.calls == []


class TestUpdate:
    def test_full_replace_clears_a_parent_set_to_none(self) -> None:
        """``parent_location_key = None`` means "directly on the site" and must reach the document."""
        db = _CapturingDb()
        repo = ArangoGardenObjectRepository(db)
        db.collection(col.GARDEN_OBJECTS).docs["go_1"] = {**_DOC, "parent_location_key": "loc_gh"}

        updated = repo.update_garden_object("go_1", _object())

        assert updated.parent_location_key is None
        assert "parent_location_key" not in db.collection(col.GARDEN_OBJECTS).docs["go_1"]


class TestDelete:
    def test_cuts_every_edge_on_the_end_it_hangs_off(self) -> None:
        db = _CapturingDb()
        repo = ArangoGardenObjectRepository(db)
        object_id = f"{col.GARDEN_OBJECTS}/go_1"

        assert repo.delete_garden_object("go_1") is True

        assert db.collections[col.GARDEN_OBJECTS].deleted == ["go_1"]
        (site_edge,) = _edge_calls(db, col.HAS_GARDEN_OBJECT)
        assert "e._to == @vertex" in site_edge["query"] and site_edge["bind_vars"]["vertex"] == object_id
        (task_edge,) = _edge_calls(db, col.HAS_TASK)
        assert "e._from == @vertex" in task_edge["query"] and task_edge["bind_vars"]["vertex"] == object_id
        (zone_edge,) = _edge_calls(db, col.ZONE_SUPPLIED_BY)
        assert "e._to == @vertex" in zone_edge["query"] and zone_edge["bind_vars"]["vertex"] == object_id
