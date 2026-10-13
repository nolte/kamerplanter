"""#2015 — the fertilizer seed loaders see the whole catalogue, not the first 1000 rows.

Four loaders read ``fert_repo.get_all(offset=0, limit=1000, all_tenants=True)`` once.
The repository sorts by ``product_name``, so once 1000 rows sort before a seed
product (every tenant's own products count, the read spans all tenants):

* ``upsert_fertilizers`` did not find the existing seed row, created it again, and
  the collection-wide ``(product_name, brand)`` unique index refused the insert —
  the second boot failed;
* ``run_seed_fertilizers``' cross-file lookup lost ``PK 13-14`` (a Plagron product a
  ``fertilizers.yaml`` plan doses), so the dosage was dropped;
* ``run_seed_nutrient_plans_outdoor`` found no Plagron product and returned early,
  seeding none of its plans;
* ``run_seed_nutrient_plans_ro`` found its required products "missing" and returned
  early, seeding none of its plans.

All four now read the whole global catalogue through ``get_global_fertilizers`` (#2000
replaced the all-tenant ``load_all_fertilizers`` / ``get_all_pages`` read #2015 introduced,
so the match is global-only as well as complete). The test puts
1001 filler rows in front of every real product name and runs the production loaders
against a real ArangoDB, so the sort order, the ``total`` and the unique index are the
server's, not a double's.

The paging test pins the tie-break that makes ``get_all_pages`` sound on this
repository: ``product_name`` is not unique (one name, several brands), and offset
paging over a partial order may hand an equal-named row to two pages and skip another.
"""

from __future__ import annotations

import json
from collections import Counter

import pytest

from app.data_access.arango.base_repository import get_all_pages
from app.data_access.arango.fertilizer_repository import ArangoFertilizerRepository
from app.migrations.seed_fertilizers import run_seed_fertilizers
from app.migrations.seed_gardol import run_seed_gardol
from app.migrations.seed_nutrient_plans_outdoor import run_seed_nutrient_plans_outdoor
from app.migrations.seed_nutrient_plans_ro import run_seed_nutrient_plans_ro
from app.migrations.seed_plagron import run_seed_plagron
from app.migrations.yaml_loader import load_yaml
from tests.support.arango_integration import run_database_name
from tests.support.seed_boot import bind_database, create_database

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("#2015 measures the fertilizer seed loaders against a real server"),
]

_DB_NAME = run_database_name("seed_fertilizer_loaders_paging")
_LOADERS = (
    run_seed_fertilizers,
    run_seed_plagron,
    run_seed_gardol,
    run_seed_nutrient_plans_outdoor,
    run_seed_nutrient_plans_ro,
)
#: One more than the old window; every filler sorts before every real product name.
_FILLER = 1001


@pytest.fixture
def db(monkeypatch):
    system, database = create_database(_DB_NAME)
    bind_database(monkeypatch, database)
    yield database
    system.delete_database(_DB_NAME)


def _boot() -> None:
    for loader in _LOADERS:
        loader()


def _insert_filler(db, n: int) -> None:
    db.collection("fertilizers").insert_many(
        [
            {"product_name": f"000-filler-{i:04d}", "brand": "filler", "fertilizer_type": "base", "tenant_key": ""}
            for i in range(n)
        ]
    )


def _seed_fertilizer_identities() -> set[tuple[str, str]]:
    identities: set[tuple[str, str]] = set()
    for name in ("fertilizers.yaml", "plagron.yaml", "gardol.yaml"):
        for fert in load_yaml(name)["fertilizers"]:
            identities.add((fert["product_name"], fert.get("brand", "")))
    return identities


def _global_plan_names(db) -> set[str]:
    return set(
        db.aql.execute('FOR p IN nutrient_plans FILTER p.tenant_key == "" OR p.tenant_key == null RETURN p.name')
    )


def _yaml_plan_names(name: str) -> set[str]:
    return {plan["name"] for plan in load_yaml(name)["nutrient_plans"]}


def test_a_second_boot_finds_every_seed_product_past_the_old_window(db) -> None:
    """``upsert_fertilizers``: an existing seed row past row 1000 is updated, not inserted again."""
    _insert_filler(db, _FILLER)

    _boot()
    _boot()  # the old single window raised on the unique index here

    rows = Counter(
        (doc["product_name"], doc.get("brand", ""))
        for doc in db.collection("fertilizers").all()
        if doc["brand"] != "filler"
    )
    for identity in _seed_fertilizer_identities():
        assert rows[identity] == 1, f"{identity}: expected exactly one row, got {rows[identity]}"


def test_outdoor_and_ro_plans_are_seeded_when_their_products_sort_past_the_old_window(db) -> None:
    """``run_seed_nutrient_plans_outdoor`` / ``_ro``: the products are found, the plans exist."""
    _insert_filler(db, _FILLER)

    _boot()

    present = _global_plan_names(db)
    assert _yaml_plan_names("nutrient_plans_outdoor.yaml") <= present
    assert _yaml_plan_names("nutrient_plans_ro.yaml") <= present


def test_cross_file_reference_resolves_past_the_old_window(db) -> None:
    """``run_seed_fertilizers``: a plan dose of ``PK 13-14`` (from plagron.yaml) keeps its key."""
    _insert_filler(db, _FILLER)

    _boot()  # PK 13-14 does not exist yet when run_seed_fertilizers runs first
    _boot()

    (pk_key,) = list(db.aql.execute('FOR f IN fertilizers FILTER f.product_name == "PK 13-14" RETURN f._key'))
    plan_names = _yaml_plan_names("fertilizers.yaml")
    entries = list(
        db.aql.execute(
            """
            FOR p IN nutrient_plans
                FILTER p.name IN @names AND (p.tenant_key == "" OR p.tenant_key == null)
                FOR e IN nutrient_plan_phase_entries FILTER e.plan_key == p._key RETURN e
            """,
            bind_vars={"names": sorted(plan_names)},
        )
    )
    assert any(pk_key in json.dumps(e) for e in entries), "no fertilizers.yaml plan entry doses PK 13-14"


def test_paging_over_equal_product_names_returns_every_row_once(db) -> None:
    """``SORT product_name, _key``: equal names split across pages are neither repeated nor skipped."""
    db.collection("fertilizers").insert_many(
        [
            {"product_name": f"Same {i % 3}", "brand": f"brand-{i:04d}", "fertilizer_type": "base", "tenant_key": ""}
            for i in range(250)
        ]
    )
    repo = ArangoFertilizerRepository(db)

    rows = get_all_pages(repo, all_tenants=True, page_size=7)

    keys = [r.key for r in rows]
    assert len(keys) == len(set(keys)) == 250
    names = [r.product_name for r in rows]
    assert names == sorted(names)
