"""Integration test for MT-032 (#2128) — the beats' tenant walk, measured on the server.

The actuator, tank and plant beats no longer read every tenant's rows. They ask
``ArangoTenantRepository.keys_in_status`` for the tenants they may touch and
``BaseArangoRepository.iter_for_tenants`` for exactly those tenants' rows. The unit tests
drive the beats through ``tests/support/tenant_walk.py`` (``TenantRows``,
``TenantStates``), doubles that claim the same semantics. This file holds the real AQL
to that claim:

* the tenant ``IN`` predicate and the extra filters (``removed_on == null`` reads a
  missing field as null), a row without a tenant never selected;
* the keyset cursor over several pages, every row once, in ``_key`` order;
* the tenant state read exactly as the ``Tenant`` model reads it: ``status`` wins, a
  pre-v0085 ``is_active == false`` is ``suspended``, neither is ``active``.

Run with: pytest tests/integration/test_tenant_walk_query.py -v
(requires an ArangoDB; see ``tests/integration/conftest.py``).
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.common.enums import TenantStatus
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name
from tests.support.tenant_walk import TenantRows

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("#2128 measures the tenant walk's AQL; the doubles claim its semantics"),
]

_DB_NAME = run_database_name("tenant_walk")

_TANK = {"tank_type": "nutrient", "volume_liters": 50.0}

TANKS = [
    *({"_key": f"a{i:04d}", "tenant_key": "t-open", "name": f"A{i}", **_TANK} for i in range(1203)),
    *({"_key": f"b{i:04d}", "tenant_key": "t-other", "name": f"B{i}", **_TANK} for i in range(7)),
    {"_key": "c-closed", "tenant_key": "t-closed", "name": "closed", **_TANK},
    {"_key": "d-empty", "tenant_key": "", "name": "tenantless", **_TANK},
    {"_key": "e-missing", "name": "no tenant field", **_TANK},
]

_PLANT = {"species_key": "s", "planted_on": "2026-03-01"}

PLANTS = [
    {"_key": "p-live", "tenant_key": "t-open", "instance_id": "P1", "removed_on": None, **_PLANT},
    {"_key": "p-nofield", "tenant_key": "t-open", "instance_id": "P2", **_PLANT},
    {"_key": "p-removed", "tenant_key": "t-open", "instance_id": "P3", "removed_on": "2026-01-01", **_PLANT},
    {"_key": "p-closed", "tenant_key": "t-closed", "instance_id": "P4", "removed_on": None, **_PLANT},
]


def _tenant(key: str, **fields):  # noqa: ANN003, ANN202
    return {"_key": key, "name": key, "slug": key, "owner_user_key": "u", "tenant_type": "organization", **fields}


TENANTS = [
    _tenant("t-open", status="active"),
    _tenant("t-other", status="active"),
    _tenant("t-closed", status="suspended"),
    _tenant("t-pending", status="pending_deletion"),
    _tenant("t-legacy-off", is_active=False),  # pre-v0085: no status, the retired bool says off
    _tenant("t-legacy-on", is_active=True),
    _tenant("t-bare"),  # neither field: the model default, active
    _tenant("t-status-wins", status="active", is_active=False),
]


@pytest.fixture(scope="module")
def db():
    from app.config.settings import Settings
    from app.data_access.arango import collections as col
    from app.data_access.arango.collections import ensure_collections
    from app.data_access.arango.connection import ArangoConnection

    conn = ArangoConnection(Settings(arangodb_database=_DB_NAME))
    database = conn.connect()
    ensure_collections(database)
    database.collection(col.TANKS).insert_many(TANKS, overwrite=True)
    database.collection(col.PLANT_INSTANCES).insert_many(PLANTS, overwrite=True)
    database.collection(col.TENANTS).insert_many(TENANTS, overwrite=True)
    yield database
    conn.close()
    system = ArangoClient(hosts=ARANGO_URL).db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)


def _tank_repo(db):  # noqa: ANN001, ANN202
    from app.data_access.arango.tank_repository import ArangoTankRepository

    return ArangoTankRepository(db)


def test_the_walk_reads_every_row_of_the_named_tenants_once_in_key_order(db) -> None:
    rows = list(_tank_repo(db).iter_for_tenants(["t-open", "t-other"], page_size=500))

    expected = sorted(t["_key"] for t in TANKS if t.get("tenant_key") in {"t-open", "t-other"})
    assert [r.key for r in rows] == expected
    assert len(rows) == 1210


def test_a_tenantless_row_is_never_selected(db) -> None:
    keys = {r.key for r in _tank_repo(db).iter_for_tenants(["t-open", "", "t-closed"])}

    assert "d-empty" not in keys
    assert "e-missing" not in keys
    assert "c-closed" in keys


def test_removed_on_null_reads_a_missing_field_as_null(db) -> None:
    from app.data_access.arango.plant_instance_repository import ArangoPlantInstanceRepository

    rows = ArangoPlantInstanceRepository(db).iter_for_tenants(["t-open"], filters=[("removed_on", "==", None)])

    assert sorted(r.key for r in rows) == ["p-live", "p-nofield"]


def test_keys_in_status_reads_the_state_like_the_model(db) -> None:
    from app.data_access.arango.tenant_repository import ArangoTenantRepository
    from app.domain.models.tenant import Tenant

    repo = ArangoTenantRepository(db)

    active = repo.keys_in_status({TenantStatus.ACTIVE})
    closed = repo.keys_in_status({TenantStatus.SUSPENDED, TenantStatus.PENDING_DELETION})

    assert set(active) == {"t-open", "t-other", "t-legacy-on", "t-bare", "t-status-wins"}
    assert closed == {
        "t-closed": TenantStatus.SUSPENDED,
        "t-legacy-off": TenantStatus.SUSPENDED,
        "t-pending": TenantStatus.PENDING_DELETION,
    }
    # The model, constructed from the same documents, agrees tenant by tenant.
    for doc in TENANTS:
        model = Tenant(**doc)
        assert (doc["_key"] in active) == model.is_active
        assert closed.get(doc["_key"], model.status) == model.status


@pytest.mark.parametrize(
    ("tenants", "filters"),
    [
        (["t-open"], []),
        (["t-open", "t-other", ""], []),
        (["t-closed", "nobody"], []),
        ([], []),
        (["t-open", "t-other"], [("name", "!=", "A5")]),
    ],
)
def test_the_unit_test_double_answers_like_the_server(db, tenants, filters) -> None:
    """``TenantRows`` stands in for this walk in every beat unit test; it must not answer differently."""
    server = [r.key for r in _tank_repo(db).iter_for_tenants(tenants, filters=filters, page_size=300)]
    double = [r["_key"] for r in TenantRows(TANKS).iter_for_tenants(tenants, filters=filters, page_size=300)]

    assert double == server
