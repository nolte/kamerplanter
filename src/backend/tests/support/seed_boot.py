"""Run the real seed loaders against a real ArangoDB (integration tier helper).

The loaders resolve their repositories through ``app.common.dependencies`` — one
process-wide connection. :func:`bind_database` points that connection at the test's
own database for the length of a test, so the code under test is the production entry
point (``run_seeds`` / a ``run_seed_*`` function), not a re-implementation of it.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from arango import ArangoClient
from arango.database import StandardDatabase

from app.common import dependencies
from app.data_access.arango.collections import (
    EDGE_PAIR_FIELDS,
    HARVEST_INDICATOR_IDENTITY_FIELDS,
    HARVEST_INDICATORS,
    UNIQUE_PAIR_EDGE_COLLECTIONS,
    ensure_collections,
)
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME


def create_database(name: str) -> tuple[StandardDatabase, StandardDatabase]:
    """A fresh database with the application's collections; returns ``(system, database)``."""
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(name):
        system.delete_database(name)
    system.create_database(name)
    database = client.db(name, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    ensure_collections(database)
    return system, database


def bind_database(monkeypatch: pytest.MonkeyPatch, database: StandardDatabase) -> None:
    """Make ``get_db()`` and every repository factory built on it use ``database``."""
    monkeypatch.setattr(dependencies, "get_connection", lambda: SimpleNamespace(db=database))


def drop_seed_identity_indexes(database: StandardDatabase) -> None:
    """Remove the #2001 unique identity indexes, giving the shape of a volume from before v0070.

    ``ensure_collections`` creates them on every boot; a test that builds the duplicates
    the old loaders wrote has to take them away first, as a legacy volume never had them.
    """
    targets = [(HARVEST_INDICATORS, HARVEST_INDICATOR_IDENTITY_FIELDS)]
    targets += [(name, EDGE_PAIR_FIELDS) for name in UNIQUE_PAIR_EDGE_COLLECTIONS]
    for name, fields in targets:
        collection = database.collection(name)
        for idx in collection.indexes():
            if idx.get("fields") == fields and idx.get("unique"):
                collection.delete_index(idx["id"])
