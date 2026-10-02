"""#1957 — the nutrient-plan seed loaders only ever match a *global* plan, and see all of them.

The five loaders matched a seed to a row through ``{p.name: p}`` over
``get_all(limit=100|200, all_tenants=True)``. ``nutrient_plans.name`` is not
unique, so a tenant's plan named like a seed was found by name and rewritten from
the seed model as global (its own phase entries outside the YAML deleted), and a
seed past row 100/200 of the name-sorted catalogue was not found and created again
on every boot.
"""

from __future__ import annotations

import pytest

from app.migrations.seed_fertilizers import run_seed_fertilizers
from app.migrations.seed_gardol import run_seed_gardol
from app.migrations.seed_nutrient_plans_outdoor import run_seed_nutrient_plans_outdoor
from app.migrations.seed_nutrient_plans_ro import run_seed_nutrient_plans_ro
from app.migrations.seed_plagron import run_seed_plagron
from app.migrations.versions.v0066_reset_legacy_seed_tenant_stamps import seed_identities
from tests.support.arango_integration import run_database_name
from tests.support.seed_boot import bind_database, create_database

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the plan loaders are measured against a real server"),
]

_DB_NAME = run_database_name("seed_plan_loaders_ownership")
_LOADERS = (
    run_seed_fertilizers,
    run_seed_plagron,
    run_seed_gardol,
    run_seed_nutrient_plans_outdoor,
    run_seed_nutrient_plans_ro,
)
_TENANT = "t-grower"
#: More than the largest ``limit`` any loader used (200), all sorting before every real name.
_FILLER = 230


@pytest.fixture
def db(monkeypatch):
    system, database = create_database(_DB_NAME)
    bind_database(monkeypatch, database)
    yield database
    system.delete_database(_DB_NAME)


def _boot() -> None:
    for loader in _LOADERS:
        loader()


def _seed_names() -> list[str]:
    return sorted(seed_identities().nutrient_plans)


def _global_plans(db, name: str) -> list[dict]:
    return list(
        db.aql.execute(
            'FOR p IN nutrient_plans FILTER p.name == @name AND (p.tenant_key == "" OR p.tenant_key == null) RETURN p',
            bind_vars={"name": name},
        )
    )


def _snapshot(db, collection: str, keys: list[str]) -> list[dict]:
    return [db.collection(collection).get(key) for key in keys]


def test_a_tenants_plan_named_like_a_seed_is_left_untouched_by_a_boot(db) -> None:
    names = _seed_names()
    plan_keys: list[str] = []
    entry_keys: list[str] = []
    for name in names:
        plan = db.collection("nutrient_plans").insert(
            {"name": name, "tenant_key": _TENANT, "description": "mine", "species_keys": [], "tags": ["own"]}
        )
        plan_keys.append(plan["_key"])
        for seq in (1, 99):  # 99 is a phase the seed YAML does not carry
            entry = db.collection("nutrient_plan_phase_entries").insert(
                {
                    "plan_key": plan["_key"],
                    "phase_name": "vegetative",
                    "sequence_order": seq,
                    "week_start": 1,
                    "week_end": 2,
                    "npk_ratio": [1, 1, 1],
                    "delivery_channels": [],
                }
            )
            entry_keys.append(entry["_key"])
    plans_before = _snapshot(db, "nutrient_plans", plan_keys)
    entries_before = _snapshot(db, "nutrient_plan_phase_entries", entry_keys)

    _boot()
    _boot()

    assert _snapshot(db, "nutrient_plans", plan_keys) == plans_before
    assert _snapshot(db, "nutrient_plan_phase_entries", entry_keys) == entries_before
    for name in names:
        globals_ = _global_plans(db, name)
        assert len(globals_) == 1, f"{name!r}: expected exactly one global seed plan, got {len(globals_)}"
        assert globals_[0]["_key"] not in plan_keys


def test_a_seed_beyond_the_old_lookup_limit_is_found_and_not_created_again(db) -> None:
    for i in range(_FILLER):
        db.collection("nutrient_plans").insert({"name": f"000-filler-{i:04d}", "tenant_key": ""})

    _boot()
    after_first = db.collection("nutrient_plans").count()
    _boot()

    assert db.collection("nutrient_plans").count() == after_first
    for name in _seed_names():
        assert len(_global_plans(db, name)) == 1, name


def test_a_global_seed_plan_is_still_upserted_from_the_yaml(db) -> None:
    name = _seed_names()[0]
    _boot()
    (plan,) = _global_plans(db, name)
    db.collection("nutrient_plans").update({"_key": plan["_key"], "description": "drifted"})

    _boot()

    (after,) = _global_plans(db, name)
    assert after["_key"] == plan["_key"]
    assert after["description"] != "drifted"
