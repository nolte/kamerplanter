"""#2142 (REQ-056 AK-16, AK-22) — v0091 and the plan store, measured on a real ArangoDB.

* v0091 stamps ``plan_key = "standard"`` on every stored tenant without one - the platform
  tenant and a suspended one included - and changes nothing on a second run; the seed job
  that runs right after it creates ``standard`` (every limit ``null``, ``is_default: true``)
  (AK-16);
* the boot-time seed never overwrites a plan the platform admin changed and never makes a
  second default;
* ``make_default`` leaves exactly one default; ``delete_unused`` refuses the default and a plan
  a tenant points at (AK-22); the tenant counts treat a tenant without ``plan_key`` as ``standard``;
* the organisation count of an account leaves out a ``deleted`` organisation (REQ-056 §6.2).

Locally it needs a database::

    docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_v0091_tenant_plan_key.py -v
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.collections import ensure_collections
from app.data_access.arango.plan_repository import ArangoPlanRepository
from app.data_access.arango.tenant_repository import ArangoTenantRepository
from app.domain.models.plan import Plan
from app.migrations.seed_plans import seed_plans
from app.migrations.versions.v0091_tenant_plan_key import migration
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the migration and the single-statement plan writes are AQL over a real server"),
]

_DB_NAME = run_database_name("v0091_tenant_plan_key")


@pytest.fixture
def db():  # type: ignore[no-untyped-def]
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)
    system.create_database(_DB_NAME)
    database = client.db(_DB_NAME, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    ensure_collections(database)
    yield database
    system.delete_database(_DB_NAME)


def _tenant(db, key: str, **fields) -> None:  # type: ignore[no-untyped-def]
    db.collection(col.TENANTS).insert(
        {"_key": key, "name": key, "slug": key, "tenant_type": "organization", "owner_user_key": "u", **fields}
    )


def test_every_tenant_gets_the_default_plan_and_the_plan_exists(db) -> None:  # type: ignore[no-untyped-def]
    _tenant(db, "platform", is_platform=True, status="active")
    _tenant(db, "closed", status="suspended")
    _tenant(db, "kept", status="active", plan_key="community")

    report = migration.up(db)
    seed_plans(db)  # the boot order: migrations, then the seed jobs (app/main.py)

    plans = {doc["_key"]: doc for doc in db.collection(col.PLANS).all()}
    assert set(plans) == {"standard"}
    assert plans["standard"]["is_default"] is True
    assert set(plans["standard"]["limits"].values()) == {None}
    tenants = {doc["_key"]: doc["plan_key"] for doc in db.collection(col.TENANTS).all()}
    assert tenants == {"platform": "standard", "closed": "standard", "kept": "community"}
    assert (report.scanned, report.details["tenants_without_plan"]) == (2, 2)


def test_a_second_run_changes_nothing(db) -> None:  # type: ignore[no-untyped-def]
    _tenant(db, "a", status="active")
    migration.up(db)
    seed_plans(db)
    before = {doc["_key"]: doc["_rev"] for doc in db.collection(col.TENANTS).all()}
    plan_rev = db.collection(col.PLANS).get("standard")["_rev"]

    report = migration.up(db)
    seed_plans(db)

    assert report.changed == 0
    assert {doc["_key"]: doc["_rev"] for doc in db.collection(col.TENANTS).all()} == before
    assert db.collection(col.PLANS).get("standard")["_rev"] == plan_rev


def test_the_dry_run_writes_nothing(db) -> None:  # type: ignore[no-untyped-def]
    _tenant(db, "a", status="active")

    report = migration.up(db, dry_run=True)

    assert (report.scanned, report.changed, report.details["tenants_without_plan"]) == (1, 0, 1)
    assert "plan_key" not in db.collection(col.TENANTS).get("a")
    assert db.collection(col.PLANS).count() == 0


def test_the_seed_keeps_a_changed_plan_and_never_makes_a_second_default(db) -> None:  # type: ignore[no-untyped-def]
    repo = ArangoPlanRepository(db)
    seed_plans(db)
    repo.apply_plan_change("standard", fields={"name": "Renamed"}, limit_changes={"storage_mb": 7})
    repo.create(Plan(_key="pro", name="Pro"))
    repo.make_default("pro")
    db.collection(col.PLANS).delete("standard")  # a data error the boot seed repairs

    seed_plans(db)
    seed_plans(db)

    assert [plan.key for plan in repo.list_all() if plan.is_default] == ["pro"]
    assert repo.get("standard") is not None


def test_a_renamed_standard_plan_survives_the_seed(db) -> None:  # type: ignore[no-untyped-def]
    repo = ArangoPlanRepository(db)
    seed_plans(db)
    repo.apply_plan_change("standard", fields={"name": "Renamed"}, limit_changes={"storage_mb": 7})

    seed_plans(db)

    stored = repo.get("standard")
    assert stored is not None
    assert (stored.name, stored.limits.storage_mb, stored.is_default) == ("Renamed", 7, True)


def test_exactly_one_plan_is_default_after_a_switch(db) -> None:  # type: ignore[no-untyped-def]
    repo = ArangoPlanRepository(db)
    seed_plans(db)
    repo.create(Plan(_key="pro", name="Pro"))

    chosen = repo.make_default("pro")

    assert chosen is not None and chosen.is_default
    assert [plan.key for plan in repo.list_all() if plan.is_default] == ["pro"]
    assert repo.make_default("missing") is None
    assert [plan.key for plan in repo.list_all() if plan.is_default] == ["pro"]


def test_a_plan_in_use_or_the_default_is_not_removed(db) -> None:  # type: ignore[no-untyped-def]
    repo = ArangoPlanRepository(db)
    seed_plans(db)
    repo.create(Plan(_key="pro", name="Pro"))
    repo.create(Plan(_key="spare", name="Spare"))
    _tenant(db, "t-1", plan_key="pro")
    _tenant(db, "t-legacy")  # stored before v0091: counts as standard

    assert repo.delete_unused("standard") is False
    assert repo.delete_unused("pro") is False
    assert repo.delete_unused("spare") is True
    assert {plan.key for plan in repo.list_all()} == {"standard", "pro"}
    assert repo.tenant_counts() == {"pro": 1, "standard": 1}
    assert repo.count_tenants_on("standard") == 1


def test_a_duplicate_plan_key_is_a_conflict(db) -> None:  # type: ignore[no-untyped-def]
    from app.common.exceptions import DuplicateError

    repo = ArangoPlanRepository(db)
    seed_plans(db)

    with pytest.raises(DuplicateError):
        repo.create(Plan(_key="standard", name="Again"))


def test_the_organisation_count_leaves_out_a_deleted_organisation(db) -> None:  # type: ignore[no-untyped-def]
    for key, status in (("o-1", "active"), ("o-2", "suspended"), ("o-3", "deleted"), ("o-4", "pending_deletion")):
        _tenant(db, key, status=status, owner_user_key="u-owner")
    _tenant(db, "p-1", status="active", owner_user_key="u-owner", tenant_type="personal")

    assert ArangoTenantRepository(db).count_organizations_by_owner("u-owner") == 3
