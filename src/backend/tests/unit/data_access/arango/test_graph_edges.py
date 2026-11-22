"""#2513 WP-1 — the graph-edge derivation shared by every delete cascade."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.data_access.arango import collections as col
from app.data_access.arango.graph_edges import edges_touching, remove_edges


def test_site_edges_include_structure_tenant_and_plant_location() -> None:
    edges = edges_touching(col.SITES)

    assert (col.CONTAINS, "_from") in edges
    assert (col.HAS_GARDEN_OBJECT, "_from") in edges
    assert (col.BELONGS_TO_TENANT, "_from") in edges
    assert (col.LOCATED_AT, "_to") in edges


def test_site_edges_exclude_care_events_which_point_at_locations() -> None:
    assert (col.CARE_EVENT_AT, "_to") not in edges_touching(col.SITES)


def test_location_edges_include_both_contains_ends_and_care_events() -> None:
    edges = edges_touching(col.LOCATIONS)

    assert (col.CONTAINS, "_from") in edges
    assert (col.CONTAINS, "_to") in edges
    assert (col.CARE_EVENT_AT, "_to") in edges


@pytest.mark.parametrize("vertex", [col.SITES, col.LOCATIONS, col.SLOTS, col.GARDEN_OBJECTS])
def test_result_is_ordered_by_the_graph_definitions(vertex: str) -> None:
    """The migration of WP-5 freezes this list; the order must not depend on set iteration."""
    edges = edges_touching(vertex)
    position = {str(d["edge_collection"]): i for i, d in enumerate(col.GRAPH_EDGE_DEFINITIONS)}

    assert isinstance(edges, tuple)
    assert edges == edges_touching(vertex)
    assert len(edges) == len(set(edges))
    assert edges == tuple(sorted(edges, key=lambda e: (position[e[0]], e[1] != "_from")))


def test_unknown_collection_has_no_edges() -> None:
    assert edges_touching("not_a_collection") == ()


def test_remove_edges_binds_collection_and_ids_and_filters_on_the_endpoint() -> None:
    txn = MagicMock()

    remove_edges(txn, col.CONTAINS, "_to", ("locations/a", "locations/b"))

    (query,) = txn.aql.execute.call_args.args
    assert "FILTER e._to IN @ids" in query
    assert txn.aql.execute.call_args.kwargs["bind_vars"] == {
        "@edges": col.CONTAINS,
        "ids": ["locations/a", "locations/b"],
    }


def test_remove_edges_refuses_a_field_that_is_not_an_endpoint() -> None:
    txn = MagicMock()

    with pytest.raises(ValueError, match="Not an edge endpoint"):
        remove_edges(txn, col.CONTAINS, "site_key", ["sites/a"])
    txn.aql.execute.assert_not_called()
