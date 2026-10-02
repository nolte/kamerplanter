"""#1805 — the v0004 default-tenant stamp on seed rows no longer survives into a tenant deletion.

Migration ``v0004`` stamped every row of the hybrid catalogues whose ``tenant_key``
was empty with the key of a "default tenant" — including the global seed rows.
Tenant deletion (#1769) removes the rows a tenant owns, so on a legacy volume it
would remove those seeds. Only a real ArangoDB says what the deletion does, so
this builds the legacy volume the way it came to be (rows without an owner, then
the **real** ``backfill_tenant_key``), runs the migration and then the **real**
tenant-erasure executor over the default tenant:

* the seed rows (named by the shipped seed YAML) and their children survive;
* the default tenant's own rows — same collections, names no seed has — go;
* another tenant's own rows are untouched, even one that borrowed a seed's name
  under its own tenant key (it was never stamped by v0004).

Locally it needs a database::

    docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_v0066_reset_legacy_seed_tenant_stamps.py -v
"""

from __future__ import annotations

from typing import Any

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.collections import ensure_collections
from app.data_access.arango.tenant_erasure_executor import ArangoTenantErasureExecutor
from app.domain.engines.tenant_erasure_engine import TenantErasureEngine
from app.migrations.backfill_tenant_key import backfill_tenant_key
from app.migrations.versions.v0066_reset_legacy_seed_tenant_stamps import (
    OPERATOR_COUNT_QUERY,
    migration,
    seed_identities,
)
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the stamp, the reset and the erasure are AQL over a real server"),
]

_DB_NAME = run_database_name("v0066_legacy_seed_stamps")

DEFAULT = "t-default"
OTHER = "t-other"


@pytest.fixture
def db():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)
    system.create_database(_DB_NAME)
    database = client.db(_DB_NAME, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    ensure_collections(database)
    yield database
    system.delete_database(_DB_NAME)


def _insert(db, collection: str, **doc: Any) -> str:
    return db.collection(collection).insert(doc)["_id"]


def _row(db, doc_id: str) -> dict[str, Any] | None:
    collection, key = doc_id.split("/", 1)
    return db.collection(collection).get(key)


def _legacy_volume(db) -> dict[str, str]:
    """A volume as v0004 left it: seed and own rows without an owner, then stamped for real."""
    ids = seed_identities()
    seed_fert_name, seed_fert_brand = sorted(ids.fertilizers)[0]
    seed_plan = sorted(ids.nutrient_plans)[0]
    seed_wf = sorted(ids.workflow_templates)[0]
    seed_tt = next(name for wf, name in sorted(ids.task_templates) if wf == seed_wf)

    rows: dict[str, str] = {}
    rows["seed_fert"] = _insert(db, col.FERTILIZERS, product_name=seed_fert_name, brand=seed_fert_brand)
    rows["own_fert"] = _insert(db, col.FERTILIZERS, product_name="Mein Eigenbau", brand="Hausmarke")
    rows["seed_plan"] = _insert(db, col.NUTRIENT_PLANS, name=seed_plan)
    rows["own_plan"] = _insert(db, col.NUTRIENT_PLANS, name="Mein Plan")
    for tag, plan in (("seed", rows["seed_plan"]), ("own", rows["own_plan"])):
        rows[f"{tag}_entry"] = _insert(
            db, col.NUTRIENT_PLAN_PHASE_ENTRIES, plan_key=plan.split("/", 1)[1], sequence_order=1
        )
    rows["seed_wf"] = _insert(db, col.WORKFLOW_TEMPLATES, name=seed_wf, is_system=True)
    rows["own_wf"] = _insert(db, col.WORKFLOW_TEMPLATES, name="Mein Ablauf", is_system=False)
    rows["seed_tt"] = _insert(
        db, col.TASK_TEMPLATES, name=seed_tt, workflow_template_key=rows["seed_wf"].split("/", 1)[1]
    )
    rows["own_tt"] = _insert(
        db, col.TASK_TEMPLATES, name="Eigene Aufgabe", workflow_template_key=rows["own_wf"].split("/", 1)[1]
    )
    # Another tenant's data: owned from the start, so v0004 never touched it. Its plan
    # borrows a seed's name — a seed identity alone must not make it global.
    rows["other_plan"] = _insert(db, col.NUTRIENT_PLANS, name=seed_plan, tenant_key=OTHER)
    rows["other_fert"] = _insert(db, col.FERTILIZERS, product_name="Fremd", brand="X", tenant_key=OTHER)

    _insert(db, col.TENANTS, _key=DEFAULT, slug="default", created_at="2025-01-01T00:00:00+00:00")
    _insert(db, col.TENANTS, _key=OTHER, slug="other", created_at="2025-02-01T00:00:00+00:00")
    _insert(db, col.MEMBERSHIPS, user_key="u1", tenant_key=DEFAULT, role="admin")

    stats = backfill_tenant_key(db)
    assert stats["tenant_resolved"] == 1
    # The real v0004 landed on every unowned row — the premise of the whole issue.
    for name in ("seed_fert", "own_fert", "seed_plan", "own_plan", "seed_entry", "seed_wf", "seed_tt"):
        assert _row(db, rows[name])["tenant_key"] == DEFAULT, name
    return rows


def _delete_default_tenant(db) -> None:
    plan = TenantErasureEngine().build_plan(DEFAULT)
    ArangoTenantErasureExecutor(db).run_tenant_erasure(plan, pseudonymize=lambda value: f"pseudo-{value}")


def test_seed_rows_stamped_by_v0004_survive_the_deletion_of_the_default_tenant(db) -> None:
    rows = _legacy_volume(db)

    report = migration.up(db)
    _delete_default_tenant(db)

    survivors = ("seed_fert", "seed_plan", "seed_entry", "seed_wf", "seed_tt")
    for name in survivors:
        row = _row(db, rows[name])
        assert row is not None, f"{name} was deleted with the default tenant"
        assert row["tenant_key"] == ""
    assert report.changed >= len(survivors)


def test_the_default_tenants_own_rows_are_still_its_own(db) -> None:
    rows = _legacy_volume(db)

    migration.up(db)
    for name in ("own_fert", "own_plan", "own_entry", "own_wf", "own_tt"):
        assert _row(db, rows[name])["tenant_key"] == DEFAULT, name
    _delete_default_tenant(db)

    for name in ("own_fert", "own_plan", "own_entry", "own_wf", "own_tt"):
        assert _row(db, rows[name]) is None, f"{name} survived its tenant"


def test_another_tenants_rows_are_not_made_global_by_a_borrowed_name(db) -> None:
    rows = _legacy_volume(db)

    migration.up(db)

    assert _row(db, rows["other_plan"])["tenant_key"] == OTHER
    assert _row(db, rows["other_fert"])["tenant_key"] == OTHER


def test_the_second_run_changes_nothing_and_dry_run_writes_nothing(db) -> None:
    rows = _legacy_volume(db)

    dry = migration.up(db, dry_run=True)
    assert dry.changed == 0
    assert dry.details["to_update"] >= 5
    assert _row(db, rows["seed_plan"])["tenant_key"] == DEFAULT

    migration.up(db)
    assert migration.up(db).changed == 0


def test_the_rows_of_every_seed_file_are_recognised(db) -> None:
    """The identity set is the seed YAML itself: every named row is reset, none is skipped."""
    ids = seed_identities()
    assert len(ids.fertilizers) >= 30
    assert len(ids.nutrient_plans) >= 35
    assert len(ids.workflow_templates) == 4
    assert len(ids.task_templates) == 25


def test_a_volume_whose_parents_the_seed_loaders_already_reset_still_loses_the_entry_stamp(db) -> None:
    """The measured state of a deployed volume: loaders healed the parents, the children kept the stamp."""
    rows = _legacy_volume(db)
    for name in ("seed_fert", "seed_plan", "seed_wf", "seed_tt"):
        collection, key = rows[name].split("/", 1)
        db.collection(collection).update({"_key": key, "tenant_key": ""})

    migration.up(db)
    _delete_default_tenant(db)

    entry = _row(db, rows["seed_entry"])
    assert entry is not None
    assert entry["tenant_key"] == ""
    assert _row(db, rows["seed_plan"]) is not None
    assert _row(db, rows["other_plan"])["tenant_key"] == OTHER


def test_a_lone_seed_named_row_of_a_tenant_on_a_clean_volume_stays_that_tenants(db) -> None:
    seed_plan = sorted(seed_identities().nutrient_plans)[0]
    own = _insert(db, col.NUTRIENT_PLANS, name=seed_plan, tenant_key=OTHER)
    _insert(db, col.NUTRIENT_PLANS, name=sorted(seed_identities().nutrient_plans)[1], tenant_key="")
    _insert(db, col.NUTRIENT_PLANS, name=sorted(seed_identities().nutrient_plans)[2], tenant_key="")

    report = migration.up(db)

    assert report.changed == 0
    assert _row(db, own)["tenant_key"] == OTHER


def test_the_operator_count_query_runs_and_names_the_stamp(db) -> None:
    """The query the PR hands the operator for a restored backup answers on a real server."""
    _legacy_volume(db)

    (counts,) = db.aql.execute(OPERATOR_COUNT_QUERY)

    assert counts["entries_under_global_plan"] == 0
    stamped = {row["tenant_key"]: row["rows"] for row in counts["nutrient_plans_stamped_by_tenant"]}
    assert stamped == {DEFAULT: 2, OTHER: 1}
    assert counts["task_templates_stamped_by_tenant"] == [{"tenant_key": DEFAULT, "rows": 2}]
