"""#2027 — the activity, workflow-template and substrate seeds only ever match a *global* row.

Three loaders matched a seed across every tenant's rows (measured on ArangoDB 3.12,
P0 of #2027):

* ``run_seed_activities`` looked a name up with ``get_by_name`` (no tenant filter): a
  tenant's own activity named like a seed was rewritten from the seed model as a
  global ``is_system`` row;
* ``run_seed`` read ``get_all_workflow_templates(0, 200)`` without a tenant: a
  tenant's template named like a seed was overwritten as a global system template,
  and the seed's phases were hung on the tenant's key;
* ``run_seed_substrates`` read ``get_all_substrates(offset=0, limit=500)`` without a
  tenant: a tenant's mix with a seed's ``(type, name_de or brand)`` counted as the
  seed being present, and the global row was never written for anyone.

Each test plants the tenant row **before** the first boot — the order in which a later
release adds a seed a tenant already named — runs the production loader twice, and
asserts that the tenant row is byte-identical (``_rev`` included) and the global seed
row exists beside it. For activities and workflow templates the second half needs the
``(tenant_key, name)`` unique index (v0076, v0077); under the old ``name`` index the
global row could not be written at all.
"""

from __future__ import annotations

from typing import Any

import pytest
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.domain.models.substrate import Substrate
from app.migrations.seed_activities import run_seed_activities
from app.migrations.seed_data import run_seed
from app.migrations.seed_substrates import run_seed_substrates
from app.migrations.yaml_loader import load_yaml
from tests.support.arango_integration import run_database_name
from tests.support.seed_boot import bind_database, create_database

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the seed loaders are measured against a real server"),
]

_DB_NAME = run_database_name("seed_catalogue_loaders_ownership")
_TENANT = "t-grower"
_GLOBAL_FILTER = 'FILTER doc.tenant_key == "" OR doc.tenant_key == null'


@pytest.fixture
def db(monkeypatch: pytest.MonkeyPatch):
    system, database = create_database(_DB_NAME)
    bind_database(monkeypatch, database)
    yield database
    system.delete_database(_DB_NAME)


def _global_rows(db: StandardDatabase, collection: str, **match: str) -> list[dict[str, Any]]:
    clauses = " ".join(f"FILTER doc.{field} == @{field}" for field in match)
    return list(
        db.aql.execute(
            f"FOR doc IN @@c {_GLOBAL_FILTER} {clauses} RETURN doc",
            bind_vars={"@c": collection, **match},
        )
    )


def test_a_tenants_activity_named_like_a_seed_stays_its_own(db: StandardDatabase) -> None:
    seed = load_yaml("activities.yaml")["activities"][0]
    planted = db.collection(col.ACTIVITIES).insert(
        {
            "name": seed["name"],
            "tenant_key": _TENANT,
            "is_system": False,
            "category": seed["category"],
            "description": "my own technique",
        }
    )
    before = db.collection(col.ACTIVITIES).get(planted["_key"])

    run_seed_activities()
    run_seed_activities()

    assert db.collection(col.ACTIVITIES).get(planted["_key"]) == before
    rows = _global_rows(db, col.ACTIVITIES, name=seed["name"])
    assert len(rows) == 1, f"{seed['name']!r}: expected one global seed row, got {len(rows)}"
    assert rows[0]["_key"] != planted["_key"]
    assert rows[0]["is_system"] is True


def test_a_tenants_workflow_template_named_like_a_seed_stays_its_own(db: StandardDatabase) -> None:
    seed_name = load_yaml("workflows.yaml")["workflow_templates"][0]["name"]
    planted = db.collection(col.WORKFLOW_TEMPLATES).insert(
        {"name": seed_name, "tenant_key": _TENANT, "is_system": False, "description": "my own schedule"}
    )
    before = db.collection(col.WORKFLOW_TEMPLATES).get(planted["_key"])

    run_seed()
    run_seed()

    assert db.collection(col.WORKFLOW_TEMPLATES).get(planted["_key"]) == before
    rows = _global_rows(db, col.WORKFLOW_TEMPLATES, name=seed_name)
    assert len(rows) == 1, f"{seed_name!r}: expected one global seed row, got {len(rows)}"
    assert rows[0]["_key"] != planted["_key"]
    attached = list(
        db.aql.execute(
            "FOR doc IN @@c FILTER doc.workflow_template_key == @k RETURN doc._key",
            bind_vars={"@c": col.WORKFLOW_PHASES, "k": planted["_key"]},
        )
    ) + list(
        db.aql.execute(
            "FOR doc IN @@c FILTER doc.workflow_template_key == @k RETURN doc._key",
            bind_vars={"@c": col.TASK_TEMPLATES, "k": planted["_key"]},
        )
    )
    assert attached == [], "the seed hung its phases or task templates on the tenant's template"
    seeded_phases = list(
        db.aql.execute(
            "FOR doc IN @@c FILTER doc.workflow_template_key == @k RETURN doc._key",
            bind_vars={"@c": col.WORKFLOW_PHASES, "k": rows[0]["_key"]},
        )
    )
    assert seeded_phases, "the global seed template got no phases — the measurement would be vacuous"


def test_a_tenants_substrate_with_a_seeds_identity_does_not_suppress_the_global_row(db: StandardDatabase) -> None:
    seed = Substrate.model_validate(load_yaml("substrates.yaml")["substrates"][0])
    assert seed.name_de, "the first seed substrate must carry name_de, the identity this test plants"
    planted = db.collection(col.SUBSTRATES).insert(
        {"type": seed.type.value, "name_de": seed.name_de, "brand": seed.brand, "tenant_key": _TENANT}
    )
    before = db.collection(col.SUBSTRATES).get(planted["_key"])

    run_seed_substrates()
    run_seed_substrates()

    assert db.collection(col.SUBSTRATES).get(planted["_key"]) == before
    rows = _global_rows(db, col.SUBSTRATES, type=seed.type.value, name_de=seed.name_de)
    assert len(rows) == 1, f"{seed.name_de!r}: expected one global seed row, got {len(rows)}"
    assert rows[0]["_key"] != planted["_key"]
