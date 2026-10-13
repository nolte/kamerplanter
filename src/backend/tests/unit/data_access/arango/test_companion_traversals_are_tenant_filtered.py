"""MT-054 (#2144): companion traversals return only species the caller can see.

``get_compatible_species`` / ``get_incompatible_species`` walk one ``compatible_with``
/ ``incompatible_with`` edge from a species and returned every vertex at the other
end; ``get_companion_counts`` counted every edge. The anchor was scoped (a foreign
anchor answers 404), the far end was not. Edges are written by a platform admin
only, so the leak needed an admin edge to a tenant-owned species (POTENTIAL) — but
then every tenant reading the global anchor saw the other tenant's private species
in its companion list. The traversal now filters the vertex with the hybrid union
(own ∪ global ∪ granted, the species list's visibility); the counts count only
edges whose both ends the caller can see. ``None`` is the system context.

The write side is closed too: a companion edge is global reference data and may
join only two global species (``CompanionEdgeService``).
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from app.common.exceptions import ValidationError
from app.data_access.arango.graph_repository import ArangoGraphRepository
from app.domain.models.species import Species
from app.domain.services.companion_edge_service import CompanionEdgeService


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


@pytest.mark.parametrize("method", ["get_compatible_species", "get_incompatible_species"])
def test_a_tenant_traversal_filters_the_far_vertex(method: str) -> None:
    db = _Db()

    getattr(ArangoGraphRepository(db), method)("tomato", tenant_key="t-a")  # type: ignore[arg-type]

    query, binds = db.aql.calls[0]
    assert "FILTER" in query and "v.tenant_key == @tenant_key" in query
    assert binds["tenant_key"] == "t-a"


def test_the_counts_count_only_edges_between_visible_species() -> None:
    db = _Db([{"compatible": [], "incompatible": []}])

    ArangoGraphRepository(db).get_companion_counts(tenant_key="t-a")  # type: ignore[arg-type]

    query, binds = db.aql.calls[0]
    assert "DOCUMENT(edge._to)" in query and "DOCUMENT(edge._from)" in query
    assert binds["tenant_key"] == "t-a"


@pytest.mark.parametrize("method", ["get_compatible_species", "get_incompatible_species"])
def test_the_system_context_traversal_is_unfiltered(method: str) -> None:
    db = _Db()

    getattr(ArangoGraphRepository(db), method)("tomato", tenant_key=None)  # type: ignore[arg-type]

    query, binds = db.aql.calls[0]
    assert "tenant_key" not in binds


def _species_service(species: dict[str, Species]) -> tuple[CompanionEdgeService, MagicMock]:
    repo = MagicMock()
    repo.get_or_raise.side_effect = lambda key: species[key]
    graph = MagicMock()
    return CompanionEdgeService(repo, graph), graph


@pytest.mark.parametrize("method", ["set_compatibility", "set_incompatibility"])
@pytest.mark.parametrize("owned", ["from", "to"])
def test_a_companion_edge_may_not_touch_a_tenant_species(method: str, owned: str) -> None:
    species = {
        "global": Species(_key="global", scientific_name="Solanum lycopersicum", tenant_key=""),
        "private": Species(_key="private", scientific_name="Ocimum x", tenant_key="t-a"),
    }
    service, graph = _species_service(species)
    ends = ("private", "global") if owned == "from" else ("global", "private")

    with pytest.raises(ValidationError, match="global"):
        getattr(service, method)(*ends, 0.8 if method == "set_compatibility" else "shade")

    getattr(graph, method).assert_not_called()


def test_a_companion_edge_between_two_global_species_is_written() -> None:
    species = {
        "a": Species(_key="a", scientific_name="Solanum lycopersicum", tenant_key=""),
        "b": Species(_key="b", scientific_name="Ocimum basilicum", tenant_key=""),
    }
    service, graph = _species_service(species)

    service.set_compatibility("a", "b", 0.9)

    graph.set_compatibility.assert_called_once_with("a", "b", 0.9)
