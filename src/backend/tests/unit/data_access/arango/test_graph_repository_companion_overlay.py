"""REQ-053 WP 8.15 (#2658): the two batched reads of the companion overlay.

``load_companion_relations`` reads the companion edges of a whole bed in ONE query, both ends filtered with the
species list's visibility (#927, MT-054); ``get_slot_adjacency`` reads the ``adjacent_to`` edges among a bed's slots
in ONE query and folds the two stored directions to one pair. The query shape is asserted on a recording double; the
AQL itself runs against ArangoDB in CI (``tests/integration/test_garden_plan_tenant_isolation.py``).
"""

from __future__ import annotations

from typing import Any

import pytest

from app.data_access.arango.graph_repository import ArangoGraphRepository
from app.domain.interfaces.graph_repository import CompanionRelation, SlotAdjacency


class _Aql:
    def __init__(self, result: list[Any]) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self._result = result

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        self.calls.append((query, bind_vars or {}))
        return iter(self._result)


class _Db:
    def __init__(self, result: list[Any] | None = None) -> None:
        self.aql = _Aql(result or [])


class TestLoadCompanionRelations:
    def test_one_query_filters_the_species_with_the_tenant_union_and_binds_every_value(self) -> None:
        db = _Db([{"visible": [], "compatible": [], "incompatible": []}])

        ArangoGraphRepository(db).load_companion_relations(["basil", "tomato", "basil"], tenant_key="t-a")  # type: ignore[arg-type]

        ((query, binds),) = db.aql.calls
        assert "sp.tenant_key == @tenant_key" in query and "tenant_has_access" in query
        assert binds["tenant_key"] == "t-a" and binds["keys"] == ["basil", "tomato"]
        assert "e._from IN ids AND e._to IN ids" in query  # both ends among the visible species

    def test_the_rows_become_relations_and_names(self) -> None:
        db = _Db(
            [
                {
                    "visible": [{"key": "basil", "name": "Ocimum basilicum"}, {"key": "tomato", "name": None}],
                    "compatible": [{"from": "tomato", "to": "basil", "score": 0.9}],
                    "incompatible": [{"from": "basil", "to": "tomato", "reason": ""}],
                }
            ]
        )

        result = ArangoGraphRepository(db).load_companion_relations(["basil", "tomato"], tenant_key="t-a")  # type: ignore[arg-type]

        assert result.relations == [
            CompanionRelation("tomato", "basil", incompatible=False, score=0.9),
            CompanionRelation("basil", "tomato", incompatible=True, reason=None),  # an empty reason is no reason
        ]
        assert result.names == {"basil": "Ocimum basilicum"}

    def test_no_species_is_no_query(self) -> None:
        db = _Db()

        result = ArangoGraphRepository(db).load_companion_relations([], tenant_key="t-a")  # type: ignore[arg-type]

        assert (result.relations, result.names, db.aql.calls) == ([], {}, [])

    def test_an_empty_tenant_is_refused(self) -> None:
        with pytest.raises(ValueError, match="tenant_key"):
            ArangoGraphRepository(_Db()).load_companion_relations(["basil"], tenant_key="")  # type: ignore[arg-type]


class TestGetSlotAdjacency:
    def test_one_query_and_both_directions_fold_to_one_sorted_pair(self) -> None:
        db = _Db(
            [
                {"a": "s2", "b": "s1", "distance_cm": 30.0},
                {"a": "s1", "b": "s2", "distance_cm": 30.0},
                {"a": "s3", "b": "s1", "distance_cm": None},
                {"a": "s1", "b": "s1", "distance_cm": 0.0},
            ]
        )

        repo = ArangoGraphRepository(db)  # type: ignore[arg-type]
        pairs = repo.get_slot_adjacency("bed", ["s3", "s2", "s1"], tenant_key="t-a")

        ((query, binds),) = db.aql.calls
        assert binds["keys"] == ["s1", "s2", "s3"] and binds["@edges"] == "adjacent_to"
        assert "e._from IN ids AND e._to IN ids" in query
        assert pairs == [SlotAdjacency("s1", "s2", 30.0), SlotAdjacency("s1", "s3", None)]

    def test_the_read_is_anchored_on_the_tenants_bed(self) -> None:
        """A slot has no ``tenant_key`` (#706): the predicate sits on the bed's site, and only its slots count."""
        db = _Db()

        ArangoGraphRepository(db).get_slot_adjacency("bed", ["s1"], tenant_key="t-a")  # type: ignore[arg-type]

        ((query, binds),) = db.aql.calls
        assert "site.tenant_key == @tenant_key" in query and "s.location_key == @location_key" in query
        assert (binds["tenant_key"], binds["location_key"]) == ("t-a", "bed")

    def test_no_slot_is_no_query_and_an_empty_tenant_is_refused(self) -> None:
        db = _Db()

        assert ArangoGraphRepository(db).get_slot_adjacency("bed", [], tenant_key="t-a") == []  # type: ignore[arg-type]
        assert db.aql.calls == []
        with pytest.raises(ValueError, match="tenant_key"):
            ArangoGraphRepository(db).get_slot_adjacency("bed", ["s1"], tenant_key="")  # type: ignore[arg-type]
