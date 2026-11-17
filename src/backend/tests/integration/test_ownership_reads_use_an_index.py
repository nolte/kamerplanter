"""#2562 — the ownership reads of the delete paths plan an index, measured on a real ArangoDB.

A site delete refuses while a plant still stands on it (``site_key OR location_key IN … OR slot_key IN …``), collects
the site's locations and garden objects by ``site_key``; a substrate delete counts the plants naming it by
``substrate_key``; a bed-template delete selects the beds placed from it by ``template_key``. All of them run inside
a stream transaction with the default 10 s budget. Before #2562 the plant reads, the substrate count and the
template read planned an ``EnumerateCollectionNode`` — a full scan of ``plant_instances`` or of every tenant's
``locations``. The plan shape does not depend on the data volume, so a small seeded set measures it.

The AQL is not written down here: it is captured from the real repository method (or is the module's own query
constant), so a change of the query shape is measured, not a copy of it. The falsification drops one #2562 index and
shows the refusal falls back to a scan — one unindexed ``OR`` branch is enough.

Run with: pytest tests/integration/test_ownership_reads_use_an_index.py -v
(requires an ArangoDB; see ``tests/integration/conftest.py``).
"""

from __future__ import annotations

import contextlib
from collections.abc import Callable, Iterator
from typing import Any
from unittest.mock import patch

import pytest
from arango.aql import AQL
from arango.database import StandardDatabase

from app.common.exceptions import PlanError
from app.data_access.arango import collections as col
from app.data_access.arango.bed_template_repository import ArangoBedTemplateRepository
from app.data_access.arango.site_repository import ArangoSiteRepository, _SiteDeleteScope
from app.data_access.arango.substrate_repository import _SUBSTRATE_REFERRERS
from tests.support.arango_integration import run_database_name
from tests.support.seed_boot import create_database

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("#2562 asserts the optimizer's plan for the delete paths' ownership reads"),
]

_DB_NAME = run_database_name("ownership_reads_use_an_index")
_SITE = "site1"
_OWNED = (col.PLANT_INSTANCES, col.LOCATIONS, col.GARDEN_OBJECTS)


@pytest.fixture(scope="module")
def db() -> Iterator[StandardDatabase]:
    system, database = create_database(_DB_NAME)
    locations = [
        {"_key": f"l{i}", "site_key": f"site{i % 10}", "name": f"L{i}", "template_key": "tpl1" if i % 5 == 0 else None}
        for i in range(200)
    ]
    plants = [
        {
            "_key": f"p{i}",
            "tenant_key": f"t{i % 4}",
            "instance_id": f"i{i}",
            "site_key": f"site{i % 10}" if i % 2 else None,
            "location_key": f"l{i % 200}" if i % 3 else None,
            "slot_key": f"s{i % 300}" if i % 4 else None,
            "substrate_key": "sub1" if i % 6 == 0 else None,
            "removed_on": None,
        }
        for i in range(1000)
    ]
    database.collection(col.LOCATIONS).import_bulk(locations, halt_on_error=True)
    database.collection(col.GARDEN_OBJECTS).import_bulk(
        [{"_key": f"g{i}", "site_key": f"site{i % 10}", "object_type": "tree"} for i in range(200)], halt_on_error=True
    )
    database.collection(col.PLANT_INSTANCES).import_bulk(plants, halt_on_error=True)
    try:
        yield database
    finally:
        system.delete_database(_DB_NAME)


def _captured(call: Callable[[], object]) -> list[tuple[str, dict[str, Any]]]:
    """The AQL *call* sends, as it sends it; a refusal (``PlanError``) still leaves its query captured."""
    executed: list[tuple[str, dict[str, Any]]] = []
    original = AQL.execute

    def spy(self: AQL, query: str, *args: Any, **kwargs: Any) -> Any:
        executed.append((query, dict(kwargs.get("bind_vars") or {})))
        return original(self, query, *args, **kwargs)

    with patch.object(AQL, "execute", spy), contextlib.suppress(PlanError):
        call()
    return executed


def _scans(db: StandardDatabase, query: str, bind_vars: dict[str, Any]) -> list[str]:
    """The ownership collections the plan enumerates in full."""
    plan = db.aql.explain(query, bind_vars=bind_vars)
    assert isinstance(plan, dict)
    return [
        node["collection"]
        for node in plan["nodes"]
        if node["type"] == "EnumerateCollectionNode" and node["collection"] in _OWNED
    ]


def _refusal_query(db: StandardDatabase) -> tuple[str, dict[str, Any]]:
    scope = _SiteDeleteScope(
        site_id=f"{col.SITES}/{_SITE}",
        tenant_key="t1",
        name="Site",
        revision=0,
        location_ids=[f"{col.LOCATIONS}/l1", f"{col.LOCATIONS}/l11"],
        slot_ids=[f"{col.SLOTS}/s1", f"{col.SLOTS}/s2"],
        object_ids=[],
        dependent_ids={},
    )
    executed = _captured(lambda: ArangoSiteRepository._refuse_active_plants(db, _SITE, scope))  # type: ignore[arg-type]
    assert len(executed) == 1
    return executed[0]


def test_the_active_plant_refusal_plans_an_index_on_every_branch(db: StandardDatabase) -> None:
    query, bind_vars = _refusal_query(db)

    assert _scans(db, query, bind_vars) == []


def test_the_site_scope_reads_plan_an_index(db: StandardDatabase) -> None:
    executed = _captured(lambda: ArangoSiteRepository._location_ids_of_site(db, _SITE))
    executed += _captured(lambda: ArangoSiteRepository._object_ids_of_site(db, _SITE))  # type: ignore[arg-type]

    by_field = [(q, b) for q, b in executed if "site_key == @site_key" in q and "@@contains" not in q]
    assert len(by_field) == 2, [q for q, _ in executed]
    assert [_scans(db, q, b) for q, b in by_field] == [[], []]


def test_the_substrate_referrer_count_plans_an_index(db: StandardDatabase) -> None:
    bind_vars = {
        "id": f"{col.SUBSTRATES}/sub1",
        "key": "sub1",
        "@batches": col.SUBSTRATE_BATCHES,
        "@plants": col.PLANT_INSTANCES,
        "@runs": col.PLANTING_RUNS,
        "@run_uses": col.RUN_USES_SUBSTRATE,
    }

    assert _scans(db, _SUBSTRATE_REFERRERS, bind_vars) == []


def test_the_template_unset_plans_an_index(db: StandardDatabase) -> None:
    executed = _captured(
        lambda: ArangoBedTemplateRepository._unset_template_key(db, "tpl1", owner_tenant_key=None)  # type: ignore[arg-type]
    )

    assert executed, "the template unset sent no query"
    assert [_scans(db, q, b) for q, b in executed] == [[] for _ in executed]


def test_without_one_index_the_refusal_scans_the_plants(db: StandardDatabase) -> None:
    """Falsification: one unindexed ``OR`` branch turns the whole refusal into a full scan."""
    query, bind_vars = _refusal_query(db)
    plants = db.collection(col.PLANT_INSTANCES)
    indexes = plants.indexes()
    assert isinstance(indexes, list)
    index = next(i for i in indexes if list(i["fields"]) == col.PLANT_INSTANCE_LOCATION_INDEX_FIELDS)
    plants.delete_index(index["id"])
    try:
        assert _scans(db, query, bind_vars) == [col.PLANT_INSTANCES]
    finally:
        col.ensure_collections(db)

    assert _scans(db, query, bind_vars) == []
