"""#1792 — the ArangoDB run of a tenant deletion is bounded batches, not one unbounded transaction.

Until #1792 ``ArangoTenantErasureExecutor.run_tenant_erasure`` selected every row of
every inventoried collection, removed them and swept every edge collection with the
full id list in **one** stream transaction — measured on a seeded tenant of 200 000
rows and 100 000 edges: still running after 198 s, past the client's 60 s read
timeout, and the abort then failed too. Here a small ``batch_size`` makes the
bound visible on a small tenant: the deletion is many transactions, none larger
than the batch, and a run that stops between two of them is finished by the next one.

Runs against a real ArangoDB (see ``tests/integration/conftest.py``).
"""

from __future__ import annotations

from typing import Any

import pytest
from arango import ArangoClient

from app.common.exceptions import TenantErasureClaimLostError
from app.data_access.arango.tenant_erasure_executor import ArangoTenantErasureExecutor
from app.domain.engines.tenant_erasure_engine import TenantErasureEngine
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("tenant_erasure_batches")
TENANT = "t-big"
OTHER = "t-small"
ROWS = 25
BATCH = 4

pytestmark = pytest.mark.usefixtures("arango_db")


@pytest.fixture
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    database = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    from app.data_access.arango.collections import ensure_collections

    ensure_collections(database)
    yield database
    system.delete_database(TEST_DATABASE)


def _seed(database, tenant: str, rows: int) -> None:
    """*rows* sites, 2 locations under each (parent-reached, no tenant_key), and an edge per location."""
    if not database.collection("tenants").has(tenant):
        database.collection("tenants").insert({"_key": tenant, "slug": tenant, "name": tenant})
    for index in range(rows):
        site = f"{tenant}-s{index}"
        database.collection("sites").insert({"_key": site, "tenant_key": tenant, "name": site})
        for leg in range(2):
            location = f"{site}-l{leg}"
            database.collection("locations").insert({"_key": location, "site_key": site, "name": location})
            database.collection("contains").insert({"_from": f"sites/{site}", "_to": f"locations/{location}"})


def _executor(database, **kwargs: Any) -> ArangoTenantErasureExecutor:
    return ArangoTenantErasureExecutor(database, batch_size=BATCH, **kwargs)


class _CountingExecutor(ArangoTenantErasureExecutor):
    """Records the size of every batch transaction, and can fail the n-th one."""

    def __init__(self, db, *, fail_on: int | None = None) -> None:
        super().__init__(db, batch_size=BATCH)
        self.batch_sizes: list[int] = []
        self._fail_on = fail_on

    def _delete_batch(self, collection, batch, edge_collections):  # type: ignore[no-untyped-def]
        if self._fail_on is not None and len(self.batch_sizes) + 1 == self._fail_on:
            raise RuntimeError("the server refused this batch")
        self.batch_sizes.append(len(batch))
        return super()._delete_batch(collection, batch, edge_collections)


def test_a_large_tenant_is_erased_in_bounded_transactions(database):
    _seed(database, TENANT, ROWS)
    _seed(database, OTHER, 2)
    executor = _CountingExecutor(database)

    report = executor.run_tenant_erasure(
        TenantErasureEngine().build_plan(TENANT), pseudonymize=lambda key: "anon_" + "0" * 16
    )

    assert report.unreached == []
    assert report.tenant_document_removed is True
    assert max(executor.batch_sizes) <= BATCH
    # 25 sites and 50 locations at 4 rows per transaction: far more than the one transaction of before.
    assert len(executor.batch_sizes) >= (ROWS + 2 * ROWS) // BATCH
    assert database.collection("sites").count() == 2  # only the other tenant's
    assert database.collection("locations").count() == 4
    assert database.collection("contains").count() == 4  # every edge of the erased tenant went with its rows
    assert report.edges_removed == 2 * ROWS


def test_a_run_that_stopped_between_batches_is_finished_by_the_next(database):
    """Idempotent at every batch boundary: the failed batch left earlier ones committed, the retry reaches the rest."""
    _seed(database, TENANT, ROWS)
    saved: list[dict[str, list[str]]] = []
    first = _CountingExecutor(database, fail_on=9)  # the sites (7 batches) and two location batches went through

    with pytest.raises(RuntimeError, match="refused"):
        first.run_tenant_erasure(
            TenantErasureEngine().build_plan(TENANT),
            pseudonymize=lambda key: "anon_" + "0" * 16,
            on_progress=lambda keys: saved.append({name: list(rows) for name, rows in keys.items()}),
        )

    assert database.collection("sites").count() == 0  # the parents are already deleted ...
    assert database.collection("locations").count() > 0  # ... and their children are not
    assert database.collection("tenants").has(TENANT)  # the tenant document goes last
    # The parent keys were handed out BEFORE the first parent row was removed.
    assert saved and len(saved[0]["sites"]) == ROWS

    retry = _executor(database).run_tenant_erasure(
        TenantErasureEngine().build_plan(TENANT, known_parent_keys=saved[-1]),
        pseudonymize=lambda key: "anon_" + "0" * 16,
    )

    assert retry.unreached == []
    assert database.collection("locations").count() == 0
    assert database.collection("contains").count() == 0
    assert not database.collection("tenants").has(TENANT)


def test_the_progress_callback_runs_between_batches_and_may_stop_the_run(database):
    _seed(database, TENANT, ROWS)
    beats: list[int] = []

    def beat(keys: dict[str, list[str]]) -> None:
        beats.append(len(keys.get("sites", [])))
        if len(beats) == 5:
            raise TenantErasureClaimLostError

    with pytest.raises(TenantErasureClaimLostError):
        _executor(database).run_tenant_erasure(
            TenantErasureEngine().build_plan(TENANT), pseudonymize=lambda key: "x", on_progress=beat
        )

    # A beat after the parent keys and after each batch: the run stopped at the fifth,
    # having written at most the batches before it — not the whole tenant.
    assert len(beats) == 5
    assert database.collection("sites").count() >= ROWS - BATCH * 4
    assert database.collection("tenants").has(TENANT)
