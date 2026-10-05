"""#1944 — a reading ingested around a sensor or tenant erasure leaves no row for the deleted owner.

``TimescaleObservationRepository.delete_by_sensor`` / ``delete_by_tenant`` remove
the raw rows and the owner's buckets in one transaction. Nothing used to stop a
reading from being written *afterwards* — by a request already past its ownership
check, or by the Home Assistant poll that had read the sensor list minutes
earlier — and that reading created a raw row and, once the continuous aggregates
refreshed, buckets for an owner no erasure step reaches again.

This module measures it through the real ingest paths over a real ArangoDB (the
sensor, site and tank documents the ownership walk reads) **and** a real
TimescaleDB (the rows and the aggregates), not through the repository alone:

* **the route** — ``POST /t/{slug}/observations/sensors/{key}/readings`` through
  the production router, ``ObservationService`` and repositories;
* **the Home Assistant poll** — the production Celery task body
  ``ingest_ha_readings`` with only the network client faked;
* **the two erasures** — ``SensorService.delete_sensor`` (readings first, then the
  document) and the tenant erasure's order (ArangoDB phase, then the readings).

Every scenario ends in the same assertion: no raw row and no aggregate bucket for
the deleted owner, after the aggregates were refreshed over their whole range (what
the next policy run does).

Locally it needs both servers::

    docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    docker compose --profile timescaledb up -d timescaledb
    pytest tests/integration/test_sensor_ingest_after_erase.py -v
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

import psycopg
import pytest
from arango import ArangoClient
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.v1.observations.tenant_router import router as observations_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_observation_service
from app.common.enums import TenantRole
from app.common.exceptions import KamerplanterError
from app.data_access.arango import collections as col
from app.data_access.arango.ha_entity_grant_repository import ArangoHaEntityGrantRepository
from app.data_access.arango.sensor_repository import ArangoSensorRepository
from app.data_access.arango.site_repository import ArangoSiteRepository
from app.data_access.arango.tank_repository import ArangoTankRepository
from app.data_access.timescale.observation_repository import TimescaleObservationRepository
from app.data_access.timescale.schema import ensure_timescale_schema
from app.domain.models.sensor import Sensor
from app.domain.models.tenant_context import TenantContext
from app.domain.services.ha_entity_grant_service import HaEntityGrantService
from app.domain.services.observation_service import ObservationService
from app.domain.services.sensor_service import SensorService
from app.domain.services.tenant_service import TenantService
from tests.support import timescale_integration as ts
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = pytest.mark.usefixtures("arango_db", "timescale_server")

ARANGO_DATABASE = run_database_name("sensor_ingest_after_erase")
SLUG = "gone-garden"
SITE = "site-1"
TENANT_COUNTER = iter(range(10_000))


@pytest.fixture(scope="module")
def arango():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(ARANGO_DATABASE):
        system.delete_database(ARANGO_DATABASE)
    system.create_database(ARANGO_DATABASE)
    database = client.db(ARANGO_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    from app.data_access.arango.collections import ensure_collections

    ensure_collections(database)
    yield database
    system.delete_database(ARANGO_DATABASE)


@pytest.fixture(scope="module")
def timescale():
    name = ts.provision_database("tsingest")
    pool = ts.open_pool(name)
    ensure_timescale_schema(pool)
    # The policy jobs would refresh and drop in the background of this database
    # and move rows under the assertions; every refresh below is explicit.
    with psycopg.connect(ts.conninfo(name), autocommit=True) as conn:
        conn.execute(
            "SELECT alter_job(job_id, scheduled => false) FROM timescaledb_information.jobs WHERE job_id >= 1000"
        )
    yield name, pool
    pool.close()


class World:
    """One tenant with a site and a sensor (ArangoDB), a readings store (TimescaleDB), the production services."""

    def __init__(self, arango, timescale) -> None:
        name, pool = timescale
        self.arango = arango
        self.ts_name = name
        n = next(TENANT_COUNTER)
        self.tenant = f"tenant-{n}"
        self.site = f"{SITE}-{n}"
        arango.collection(col.SITES).insert({"_key": self.site, "tenant_key": self.tenant, "name": "Site"})
        self.sensor_repo = ArangoSensorRepository(arango)
        # The repository keys the document itself; the key it chose is the sensor's.
        created = self.sensor_repo.create(
            Sensor(name="Air", metric_type="temperature_celsius", site_key=self.site, ha_entity_id="sensor.air")
        )
        self.sensor = created.key or ""
        # MT-015 (#2112): ingest reads only entities granted to the sensor's tenant — the
        # real allowlist on this database, granted the way the platform admin would.
        self.grants = HaEntityGrantService(ArangoHaEntityGrantRepository(arango))
        self.grants.grant(self.tenant, ["sensor.air"])
        self.obs_repo = TimescaleObservationRepository(pool)
        self.observation_service = ObservationService(
            self.obs_repo,
            self.sensor_repo,
            tank_repo=ArangoTankRepository(arango),
            site_anchors=ArangoSiteRepository(arango),
        )
        self.sensor_service = SensorService(self.sensor_repo, None, observation_repo=self.obs_repo)
        self.client = self._client()

    def _client(self) -> TestClient:
        app = FastAPI()
        app.include_router(observations_router, prefix="/api/v1/t/{tenant_slug}")

        def handler(request: Request, exc: KamerplanterError) -> JSONResponse:
            return JSONResponse(status_code=exc.status_code, content={"error_code": exc.error_code})

        app.add_exception_handler(KamerplanterError, handler)
        app.dependency_overrides[get_current_tenant] = lambda: TenantContext(
            tenant_key=self.tenant, tenant_slug=SLUG, user_key="user-1", role=TenantRole.GROWER
        )
        app.dependency_overrides[get_observation_service] = lambda: self.observation_service
        return TestClient(app)

    # -- the real ingest route ------------------------------------------------

    def post_reading(self, value: float = 21.5) -> int:
        """``POST /t/{slug}/observations/sensors/{key}/readings`` — returns the status code."""
        return self.client.post(
            f"/api/v1/t/{SLUG}/observations/sensors/{self.sensor}/readings",
            json={"sensor_type": "temperature_celsius", "value": value},
        ).status_code

    # -- the two erasures, as production orders them -------------------------

    def erase_sensor(self) -> None:
        self.sensor_service.delete_sensor(
            self.sensor, parent_field="site_key", parent_key=self.site, tenant_key=self.tenant
        )

    def erase_tenant(self) -> None:
        """The tenant erasure's order: the ArangoDB phase first (the sensors go), the readings after."""
        self.arango.collection(col.SENSORS).delete(self.sensor, ignore_missing=True)
        self.arango.collection(col.SITES).delete(self.site, ignore_missing=True)
        TenantService(
            tenant_repo=MagicMock(),
            membership_repo=MagicMock(),
            invitation_repo=MagicMock(),
            assignment_repo=MagicMock(),
            tenant_engine=MagicMock(),
            membership_engine=MagicMock(),
            invitation_engine=MagicMock(),
            observation_repo=self.obs_repo,
        )._purge_tenant_readings(self.tenant)

    # -- what is left ---------------------------------------------------------

    def residue(self, *, sensor: bool = False) -> dict[str, int]:
        """Raw rows and aggregate buckets of the owner, after refreshing the aggregates over their whole range."""
        where = "tenant_key = %s" + (" AND sensor_key = %s" if sensor else "")
        params: tuple[Any, ...] = (self.tenant, self.sensor) if sensor else (self.tenant,)
        with psycopg.connect(ts.conninfo(self.ts_name), autocommit=True) as conn:
            for view in ("sensor_hourly", "sensor_daily"):
                conn.execute(f"CALL refresh_continuous_aggregate('{view}', NULL, NULL)")
            return {
                table: conn.execute(f"SELECT count(*) FROM {table} WHERE {where}", params).fetchone()[0]
                for table in ("sensor_readings", "sensor_hourly", "sensor_daily")
            }

    def readings_with_empty_tenant(self) -> int:
        with psycopg.connect(ts.conninfo(self.ts_name), autocommit=True) as conn:
            return conn.execute(
                "SELECT count(*) FROM sensor_readings WHERE sensor_key = %s AND tenant_key = ''", (self.sensor,)
            ).fetchone()[0]


@pytest.fixture
def world(arango, timescale):
    """A fresh tenant per test; its documents are removed afterwards so the Home Assistant poll,
    which walks **every** sensor of the database, sees only the test's own."""
    world = World(arango, timescale)
    yield world
    arango.collection(col.SENSORS).delete(world.sensor, ignore_missing=True)
    arango.collection(col.SITES).delete(world.site, ignore_missing=True)


def _hook(target: Any, name: str, before: Callable[[], None]) -> None:
    """Run *before* once, immediately before ``target.name`` — the statement a concurrent writer slips into."""
    real = getattr(target, name)
    done: list[bool] = []

    def hooked(*args: Any, **kwargs: Any) -> Any:
        if not done:
            done.append(True)
            before()
        return real(*args, **kwargs)

    setattr(target, name, hooked)


def _nothing_left(residue: dict[str, int]) -> None:
    assert residue == {"sensor_readings": 0, "sensor_hourly": 0, "sensor_daily": 0}


# ── the unraced paths hold (control) ───────────────────────────────────────


def test_a_reading_after_the_tenant_erasure_is_refused_and_writes_nothing(world: World):
    assert world.post_reading() == 201
    world.erase_tenant()

    assert world.post_reading() == 404

    _nothing_left(world.residue())


def test_a_reading_after_the_sensor_erasure_is_refused_and_writes_nothing(world: World):
    assert world.post_reading() == 201
    world.erase_sensor()

    assert world.post_reading() == 404

    _nothing_left(world.residue(sensor=True))


# ── the route, raced ───────────────────────────────────────────────────────


def test_a_reading_between_the_readings_purge_and_the_document_delete_of_a_sensor_leaves_nothing(world: World):
    """``delete_sensor`` purges the readings first and removes the document after; the route runs in between."""
    assert world.post_reading() == 201
    statuses: list[int] = []
    _hook(world.sensor_repo, "delete", lambda: statuses.append(world.post_reading()))

    world.erase_sensor()

    assert statuses == [404], "the sensor is on its way out; its readings must be refused"
    _nothing_left(world.residue(sensor=True))


def test_a_request_already_past_its_ownership_check_when_the_tenant_is_erased_leaves_nothing(world: World):
    """The in-flight request: owner checked, then the erasure runs to its end, then the insert lands."""
    assert world.post_reading() == 201
    statuses: list[int] = []

    # The route's service reads the sensor (ownership), then inserts. The erasure
    # (ArangoDB phase + readings purge) runs between the two.
    _hook(world.obs_repo, "insert", world.erase_tenant)
    statuses.append(world.post_reading())

    assert statuses == [404]
    _nothing_left(world.residue())


def test_a_batch_already_past_its_ownership_check_when_the_tenant_is_erased_leaves_nothing(world: World):
    _hook(world.obs_repo, "insert_batch", world.erase_tenant)

    status = world.client.post(
        f"/api/v1/t/{SLUG}/observations/sensors/{world.sensor}/readings/batch",
        json={"readings": [{"sensor_type": "temperature_celsius", "value": 20.0}]},
    ).status_code

    assert status == 404
    _nothing_left(world.residue())


# ── the Home Assistant poll ────────────────────────────────────────────────


@pytest.fixture
def ha_poll(world: World, monkeypatch):
    """The production task body with only the network client faked; returns a ``run(get_state_hook)`` callable."""
    import app.common.dependencies as dependencies
    import app.tasks.sensor_ingestion_tasks as task

    monkeypatch.setattr(task.settings, "timescaledb_enabled", True, raising=False)

    def run(during_poll: Callable[[], None] | None = None) -> dict:
        ha_client = MagicMock()

        waited: list[bool] = []

        def get_state(entity_id: str) -> dict:
            if during_poll is not None and not waited:
                waited.append(True)
                during_poll()
            return {"value": 23.0, "unit": "°C"}

        ha_client.get_state.side_effect = get_state
        monkeypatch.setattr(dependencies, "get_ha_client", lambda: ha_client)
        monkeypatch.setattr(dependencies, "get_sensor_repo", lambda: world.sensor_repo)
        monkeypatch.setattr(dependencies, "get_observation_repo", lambda: world.obs_repo)
        monkeypatch.setattr(dependencies, "get_observation_service", lambda: world.observation_service, raising=False)
        monkeypatch.setattr(dependencies, "get_ha_entity_grant_service", lambda: world.grants)
        return task.ingest_ha_readings()

    return run


def test_the_home_assistant_poll_stores_a_reading_under_the_tenant_that_owns_the_sensor(world: World, ha_poll):
    """A sensor document has no ``tenant_key``; its owner is its parent's. No erasure reaches an empty key."""
    result = ha_poll()

    assert result["status"] == "ok"
    assert world.readings_with_empty_tenant() == 0, "the reading was stored under tenant_key ''"
    assert world.residue(sensor=True)["sensor_readings"] == 1

    world.erase_tenant()
    _nothing_left(world.residue(sensor=True))


def test_a_sensor_erased_while_the_poll_waits_for_home_assistant_leaves_nothing(world: World, ha_poll):
    """The poll lists the sensors, then waits on the network; the sensor is erased during that wait."""
    ha_poll(during_poll=world.erase_sensor)

    assert world.sensor_repo.get(world.sensor) is None, "the erasure inside the wait must have run"
    _nothing_left(world.residue(sensor=True))
    assert world.readings_with_empty_tenant() == 0


def test_a_tenant_erased_while_the_poll_waits_for_home_assistant_leaves_nothing(world: World, ha_poll):
    ha_poll(during_poll=world.erase_tenant)

    assert world.arango.collection(col.SITES).get(world.site) is None, "the erasure inside the wait must have run"
    _nothing_left(world.residue())
    assert world.readings_with_empty_tenant() == 0


def test_a_sensor_marked_for_deletion_is_not_polled(world: World, ha_poll):
    """A delete that failed after marking the sensor keeps it out of the poll until the retry removes it."""
    sensor = world.sensor_repo.get(world.sensor)
    sensor.deletion_pending = True
    world.sensor_repo.update(world.sensor, sensor)

    result = ha_poll()

    assert result["inserted"] == 0
    _nothing_left(world.residue(sensor=True))


# ── the delete itself stays retryable ──────────────────────────────────────


def test_a_failed_readings_purge_leaves_the_sensor_deletable_and_closed_to_new_readings(world: World):
    assert world.post_reading() == 201

    def failing(*args: Any, **kwargs: Any) -> int:
        raise RuntimeError("TimescaleDB unavailable")

    real = world.obs_repo.delete_by_sensor
    world.obs_repo.delete_by_sensor = failing  # type: ignore[method-assign]
    with pytest.raises(RuntimeError):
        world.erase_sensor()

    assert world.sensor_repo.get(world.sensor) is not None, "the document must stay for the retry"
    assert world.post_reading() == 404, "a sensor whose delete began takes no new readings"

    world.obs_repo.delete_by_sensor = real  # type: ignore[method-assign]
    world.erase_sensor()

    assert world.sensor_repo.get(world.sensor) is None
    _nothing_left(world.residue(sensor=True))


def test_a_reading_for_a_live_sensor_is_stored(world: World):
    """Not every refusal is right: an untouched sensor still records and the readings read back."""
    assert world.post_reading(19.5) == 201

    assert world.residue(sensor=True)["sensor_readings"] == 1
    latest = world.obs_repo.get_latest(world.sensor, world.tenant)
    assert latest is not None and latest.value == 19.5
    assert latest.time <= datetime.now(UTC)


# ── the hot-window refresh race: bounded by the policy, not guarded (#1944 acceptance 3) ──


def test_a_bucket_of_the_hot_window_is_removed_by_the_next_policy_refresh_after_the_raw_delete(world: World):
    """Why the refresh race needs no guard of its own.

    A policy refresh that began before an erasure's raw delete can materialise a
    bucket of the last 3 hours / 3 days after the erasure committed. The raw delete
    logs an invalidation for its range, so the **next** policy refresh over that
    window recomputes it from rows that no longer exist and drops the bucket. This
    reproduces the end of that sequence on the real aggregates: a bucket whose raw
    rows were deleted *without* the aggregate purge is gone after the policy-shaped
    refresh. The exposure is therefore bounded by the policy's schedule (1 hour for
    ``sensor_hourly``, 1 day for ``sensor_daily``, migration 002), and the erasure
    record's retry repeats the purge on top — it is not an orphan series nothing
    reaches again, which is what the ingest-after-delete path produced.
    """
    with psycopg.connect(ts.conninfo(world.ts_name), autocommit=True) as conn:
        conn.execute(
            "INSERT INTO sensor_readings (time, tenant_key, sensor_key, sensor_type, value) "
            "VALUES (now() - interval '2 hours', %s, %s, 'temperature', 21.5)",
            (world.tenant, world.sensor),
        )
        window = "now() - interval '3 hours', now() - interval '1 hour'"
        conn.execute(f"CALL refresh_continuous_aggregate('sensor_hourly', {window})")
        before = conn.execute(
            "SELECT count(*) FROM sensor_hourly WHERE tenant_key = %s AND bucket < now() - interval '1 hour'",
            (world.tenant,),
        ).fetchone()[0]
        conn.execute("DELETE FROM sensor_readings WHERE tenant_key = %s", (world.tenant,))  # no aggregate purge

        conn.execute(f"CALL refresh_continuous_aggregate('sensor_hourly', {window})")
        after = conn.execute(
            "SELECT count(*) FROM sensor_hourly WHERE tenant_key = %s AND bucket < now() - interval '1 hour'",
            (world.tenant,),
        ).fetchone()[0]

    assert before == 1, "the seed must materialise a bucket, or the test proves nothing"
    assert after == 0
