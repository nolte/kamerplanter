"""Edges of the named graph that can end at a vertex collection, and their removal inside a transaction.

A delete that removes a vertex must cut every edge that can point at it. Listing those edges by hand is how
``delete_location`` came to miss every relation added after it was written (run reservations, sensors,
equipment, actuators, care events …), which then dangle on a document that is gone. The set is therefore
derived from ``GRAPH_EDGE_DEFINITIONS`` — the same definitions the bootstrap builds the graph from — so a new
relation is cut by every cascade the moment it is registered (#2513).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Final, Literal

from app.data_access.arango import collections as col
from app.data_access.arango.query_builder import aql_field
from app.data_access.arango.transactions import StreamTransaction

EdgeEndpoint = Literal["_from", "_to"]

_ENDPOINTS: Final = ("_from", "_to")


def edges_touching(vertex_collection: str) -> tuple[tuple[str, EdgeEndpoint], ...]:
    """Return ``(edge collection, "_from" | "_to")`` for every named-graph edge that can end at *vertex_collection*.

    The order is deterministic: the order of ``GRAPH_EDGE_DEFINITIONS``, and within one definition ``_from``
    before ``_to``. A self-referencing edge (e.g. ``contains`` on ``locations``) yields both endpoints.

    Args:
        vertex_collection: Name of a vertex collection of the named graph.

    Returns:
        The edge collections and the endpoint field on which they reference *vertex_collection*; empty when
        no edge definition names the collection.
    """
    found: list[tuple[str, EdgeEndpoint]] = []
    for definition in col.GRAPH_EDGE_DEFINITIONS:
        edge = str(definition["edge_collection"])
        if vertex_collection in definition["from_vertex_collections"]:
            found.append((edge, "_from"))
        if vertex_collection in definition["to_vertex_collections"]:
            found.append((edge, "_to"))
    return tuple(found)


def remove_edges(txn: StreamTransaction, edge_collection: str, field: str, ids: Sequence[str]) -> None:
    """Remove every edge of *edge_collection* whose *field* references one of *ids*, inside *txn*.

    Args:
        txn: The open stream transaction; *edge_collection* must be declared in its write set.
        edge_collection: The edge collection to remove from.
        field: ``"_from"`` or ``"_to"`` — the endpoint as returned by :func:`edges_touching`.
        ids: Full document ids (``"<collection>/<key>"``) of the vertices being removed.

    Raises:
        ValueError: If *field* is not an edge endpoint.
    """
    if field not in _ENDPOINTS:
        raise ValueError(f"Not an edge endpoint: {field!r}")
    # ``field`` is one of two literals checked above — never a request value — so it is interpolated;
    # the collection and the ids are bound.
    txn.aql.execute(
        f"FOR e IN @@edges FILTER e.{aql_field(field)} IN @ids REMOVE e IN @@edges",
        bind_vars={"@edges": edge_collection, "ids": list(ids)},
    )
