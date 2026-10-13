"""#2000 — the fertilizer seed loaders only ever match a *global* fertilizer, and see all of them.

``upsert_fertilizers`` and the plan seeds' fertilizer lookups read
``get_all(offset=0, limit=1000, all_tenants=True)`` and matched by
``(product_name, brand)`` (the upsert) or ``product_name`` alone (a plan's dosages).
A tenant's own product with a seed's identity was found, rewritten from the seed model
as global and overwritten; a seed past row 1000 was treated as missing; and a global
seed plan's dosage could resolve to a tenant's private product.

Since v0069 the unique index is ``(tenant_key, product_name, brand)``, so the global
seed row and the tenant's own product coexist — the precondition of the first test.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.common.dependencies import get_fertilizer_repo
from app.migrations.seed_fertilizers import _build_fertilizer, run_seed_fertilizers
from app.migrations.seed_gardol import run_seed_gardol
from app.migrations.seed_nutrient_plans_outdoor import run_seed_nutrient_plans_outdoor
from app.migrations.seed_nutrient_plans_ro import run_seed_nutrient_plans_ro
from app.migrations.seed_plagron import run_seed_plagron
from app.migrations.versions.v0066_reset_legacy_seed_tenant_stamps import seed_identities
from app.migrations.yaml_loader import load_yaml
from tests.support.arango_integration import run_database_name
from tests.support.seed_boot import bind_database, create_database

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the fertilizer loaders are measured against a real server"),
]

_DB_NAME = run_database_name("seed_fertilizer_loaders_ownership")
_LOADERS = (
    run_seed_fertilizers,
    run_seed_plagron,
    run_seed_gardol,
    run_seed_nutrient_plans_outdoor,
    run_seed_nutrient_plans_ro,
)
_TENANT = "t-grower"
#: More than the old fixed window (1000), all sorting before every real product name.
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


def _seed_entries() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for name in ("fertilizers.yaml", "plagron.yaml", "gardol.yaml"):
        entries.extend(load_yaml(name).get("fertilizers", []))
    return entries


def _create_tenant_copies(*, brand: str | None = None) -> list[str]:
    """A tenant-owned product for every seed entry, written through the repository like the API does."""
    repo = get_fertilizer_repo()
    keys: list[str] = []
    for entry in _seed_entries():
        fert = _build_fertilizer(entry)
        fert.tenant_key = _TENANT
        fert.notes = "my own mix"
        if brand is not None:
            fert.brand = brand
        keys.append(repo.create(fert).key or "")
    return keys


def _global_rows(db, product_name: str, brand: str) -> list[dict]:
    return list(
        db.aql.execute(
            "FOR f IN fertilizers FILTER f.product_name == @n AND f.brand == @b "
            'AND (f.tenant_key == "" OR f.tenant_key == null) RETURN f',
            bind_vars={"n": product_name, "b": brand},
        )
    )


def _snapshot(db, keys: list[str]) -> list[dict]:
    return [db.collection("fertilizers").get(key) for key in keys]


def test_a_tenants_fertilizer_with_a_seeds_identity_stays_byte_identical_across_a_boot(db) -> None:
    tenant_keys = _create_tenant_copies()
    before = _snapshot(db, tenant_keys)

    _boot()
    _boot()

    assert _snapshot(db, tenant_keys) == before
    for product_name, brand in sorted(seed_identities().fertilizers):
        rows = _global_rows(db, product_name, brand)
        assert len(rows) == 1, f"{(product_name, brand)!r}: expected one global seed row, got {len(rows)}"
        assert rows[0]["_key"] not in tenant_keys


def test_a_tenant_may_hold_a_product_named_like_a_global_seed_after_the_seed_exists(db) -> None:
    _boot()

    tenant_keys = _create_tenant_copies()
    before = _snapshot(db, tenant_keys)
    _boot()

    assert _snapshot(db, tenant_keys) == before


def test_a_global_seed_plans_dosages_resolve_to_global_fertilizers_only(db) -> None:
    _boot()
    # Same product names, another brand: a distinct identity under either index shape.
    tenant_keys = set(_create_tenant_copies(brand="Tenant Own Brand"))

    _boot()

    global_keys = {
        row["_key"]
        for row in db.aql.execute('FOR f IN fertilizers FILTER f.tenant_key == "" OR f.tenant_key == null RETURN f')
    }
    referenced = list(
        db.aql.execute(
            """
            FOR p IN nutrient_plans FILTER p.tenant_key == "" OR p.tenant_key == null
                FOR e IN nutrient_plan_phase_entries FILTER e.plan_key == p._key
                    FOR ch IN e.delivery_channels[*]
                        FOR d IN ch.fertilizer_dosages[*]
                            RETURN d.fertilizer_key
            """
        )
    )
    assert referenced, "no dosage was seeded — the measurement would be vacuous"
    assert [key for key in referenced if key in tenant_keys] == []
    assert set(referenced) <= global_keys


def test_a_seed_beyond_the_old_fixed_window_is_found_and_not_created_again(db) -> None:
    kind = _seed_entries()[0]["fertilizer_type"]
    db.collection("fertilizers").import_bulk(
        [
            {"product_name": f"000-filler-{i:04d}", "brand": "Filler", "tenant_key": "", "fertilizer_type": kind}
            for i in range(_FILLER)
        ]
    )

    _boot()
    after_first = db.collection("fertilizers").count()
    _boot()

    assert db.collection("fertilizers").count() == after_first
    for product_name, brand in sorted(seed_identities().fertilizers):
        assert len(_global_rows(db, product_name, brand)) == 1, (product_name, brand)


def test_a_dosage_binds_to_the_brand_the_seed_ships_not_to_an_older_namesake(db) -> None:
    """Review follow-up to #2030: dosages name a product by ``product_name`` only.

    A global "CalMag" of another brand, created before the seed product (so with the
    lower ``_key``), took every RO plan's CalMag dosage.
    """
    kind = _seed_entries()[0]["fertilizer_type"]
    namesake = db.collection("fertilizers").insert(
        {"product_name": "CalMag", "brand": "Older Namesake", "tenant_key": "", "fertilizer_type": kind}
    )["_key"]

    _boot()

    seed_brand = next(e["brand"] for e in _seed_entries() if e["product_name"] == "CalMag")
    (seed_key,) = [row["_key"] for row in _global_rows(db, "CalMag", seed_brand)]
    dosed = set(
        db.aql.execute(
            """
            FOR p IN nutrient_plans FILTER p.name IN @names
                FOR e IN nutrient_plan_phase_entries FILTER e.plan_key == p._key
                    FOR ch IN e.delivery_channels[*]
                        FOR d IN ch.fertilizer_dosages[*]
                            FILTER d.fertilizer_key IN [@seed, @namesake]
                            RETURN d.fertilizer_key
            """,
            bind_vars={
                "names": [p["name"] for p in load_yaml("nutrient_plans_ro.yaml")["nutrient_plans"]],
                "seed": seed_key,
                "namesake": namesake,
            },
        )
    )
    assert dosed == {seed_key}
