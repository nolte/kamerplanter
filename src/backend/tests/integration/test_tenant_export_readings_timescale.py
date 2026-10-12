"""#2138 (REQ-056 §8.3) — a tenant's TimescaleDB readings travel in its archive, and only its own.

``timeseries/readings.csv`` is the optional part of format 1: the raw readings and the hourly and
daily buckets NFR-011 still keeps. Only a real TimescaleDB can say whether the read is bound to the
tenant — the ``WHERE tenant_key = …`` predicate of ``iter_tenant_readings`` against rows of another
tenant on the **same sensor key** and against the pre-#2076 rows without a tenant key — whether the
continuous aggregates are read, and whether the server-side cursor pages. The export runs through
:class:`TenantExportService` over a real ArangoDB (the roundtrip module's wiring); the archive is
then imported into a second database, which lists the part and imports nothing from it.

Locally it needs both servers::

    docker compose --profile timescaledb up -d timescaledb
    docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_tenant_export_readings_timescale.py -v
"""

from __future__ import annotations

import csv
import io
import json
import zipfile

import psycopg
import pytest

from app.common.async_bridge import run_async
from app.data_access.timescale.observation_repository import TimescaleObservationRepository
from app.data_access.timescale.schema import ensure_timescale_schema
from app.domain.services.tenant_export_service import StepUpFactors
from tests.integration.test_tenant_export_roundtrip import (
    ADMIN,
    LEAD,
    _database,
    _export,
    _grant,
    _person,
    _seed_catalogue,
    _seed_tenant,
    _service,
)
from tests.support import timescale_integration as ts
from tests.support.arango_integration import run_database_name

pytestmark = pytest.mark.usefixtures("arango_db", "timescale_server")

A, B = "ten-ra", "ten-rb"
SHARED_SENSOR = "sensor-shared"  # both tenants report under this key: the tenant, not the sensor, decides
SOURCE_DB = run_database_name("tenant_readings_source")
TARGET_DB = run_database_name("tenant_readings_target")
#: Raw readings seeded for A (hours ago); one raw reading per hour, so each is its own hourly bucket.
A_HOURS = (1, 2, 3, 30)
B_MARKER = "B-ONLY-UNIT"  # a unit only B's rows carry
LEGACY_MARKER = "LEGACY-UNIT"  # a pre-#2076 row with an empty tenant key


@pytest.fixture(scope="module")
def readings():
    name = ts.provision_database("tenantreadings")
    pool = ts.open_pool(name)
    ensure_timescale_schema(pool)
    with psycopg.connect(ts.conninfo(name), autocommit=True) as conn:
        # No background refresh or retention moves rows under the assertions.
        conn.execute(
            "SELECT alter_job(job_id, scheduled => false) FROM timescaledb_information.jobs WHERE job_id >= 1000"
        )
        for hours in A_HOURS:
            conn.execute(
                "INSERT INTO sensor_readings "
                "(time, tenant_key, sensor_key, sensor_type, value, unit, source, metadata) "
                "VALUES (date_trunc('hour', now()) - make_interval(hours => %s), %s, %s, 'temperature', %s, '°C', "
                "'home_assistant', %s)",
                (hours, A, SHARED_SENSOR, 20.0 + hours, json.dumps({"entity_id": "sensor.a"})),
            )
        conn.execute(
            "INSERT INTO sensor_readings (time, tenant_key, sensor_key, sensor_type, value, unit) "
            "VALUES (now() - interval '2 hours', %s, %s, 'temperature', 99, %s)",
            (B, SHARED_SENSOR, B_MARKER),
        )
        conn.execute(
            "INSERT INTO sensor_readings (time, tenant_key, sensor_key, sensor_type, value, unit) "
            "VALUES (now() - interval '2 hours', '', %s, 'temperature', 77, %s)",
            (SHARED_SENSOR, LEGACY_MARKER),
        )
        conn.execute("CALL refresh_continuous_aggregate('sensor_hourly', NULL, NULL)")
        conn.execute("CALL refresh_continuous_aggregate('sensor_daily', NULL, NULL)")
    yield TimescaleObservationRepository(pool), name
    pool.close()


def _all(repo: TimescaleObservationRepository, tenant: str, page_size: int = 1000):
    pages = list(repo.iter_tenant_readings(tenant, page_size=page_size))
    return pages, [row for page in pages for row in page]


#: The aggregate views, by the series name the archive gives their rows (fixed text, no input).
_VIEW_COUNTS = {
    "hourly": "SELECT count(*) FROM sensor_hourly WHERE tenant_key = %s",
    "daily": "SELECT count(*) FROM sensor_daily WHERE tenant_key = %s",
}


def _buckets(name: str, series: str, tenant: str) -> int:
    with psycopg.connect(ts.conninfo(name)) as conn:
        row = conn.execute(_VIEW_COUNTS[series], (tenant,)).fetchone()
    return int(row[0]) if row else 0


def test_the_read_returns_the_tenants_raw_rows_and_buckets_and_nothing_else(readings) -> None:
    repo, name = readings
    _pages, rows = _all(repo, A)

    raw = [row for row in rows if row.series == "raw"]
    assert sorted(row.value for row in raw) == sorted(20.0 + hours for hours in A_HOURS)
    assert all(row.unit == "°C" and row.metadata == {"entity_id": "sensor.a"} for row in raw)
    # The aggregates are read from the continuous aggregates themselves, every bucket of A.
    assert sum(1 for row in rows if row.series == "hourly") == _buckets(name, "hourly", A) == len(A_HOURS)
    assert sum(1 for row in rows if row.series == "daily") == _buckets(name, "daily", A) >= 1
    # Same sensor key, other tenant / no tenant: never in A's read.
    assert not any(row.unit in (B_MARKER, LEGACY_MARKER) for row in rows)
    assert all(row.value not in (99, 77) for row in raw)
    assert [row.series for row in rows] == sorted((row.series for row in rows), key=["raw", "hourly", "daily"].index)


def test_the_read_pages_through_a_server_side_cursor(readings) -> None:
    repo, _name = readings
    pages, rows = _all(repo, A, page_size=2)

    assert len(pages) > 1 and all(len(page) <= 2 for page in pages)
    assert len(rows) == len(_all(repo, A)[1])


def test_an_empty_tenant_key_is_refused_and_never_matches_the_legacy_rows(readings) -> None:
    repo, _name = readings
    with pytest.raises(ValueError, match="tenant key"):
        _all(repo, "")


@pytest.fixture
def arango_pair():
    sys_src, src = _database(SOURCE_DB)
    sys_dst, dst = _database(TARGET_DB)
    _seed_catalogue(src)
    _seed_catalogue(dst)
    yield src, dst
    sys_src.delete_database(SOURCE_DB)
    sys_dst.delete_database(TARGET_DB)


def test_the_archive_carries_the_tenants_readings_and_an_import_lists_but_skips_them(
    readings, arango_pair, tmp_path
) -> None:
    source, target = arango_pair
    repo, _name = readings
    _seed_tenant(source, A)
    _seed_tenant(source, B)
    _pages, expected = _all(repo, A)

    archive = _export(_service(source, tmp_path / "src", readings=repo), source, A)

    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        manifest = json.loads(z.read("manifest.json"))
        data = z.read("timeseries/readings.csv").decode("utf-8")
    rows = list(csv.DictReader(io.StringIO(data)))
    assert len(rows) == len(expected) == manifest["files"]["timeseries/readings.csv"]["rows"]
    assert manifest["timeseries"]["readings"]["rows"] == len(expected)
    assert B_MARKER not in data and LEGACY_MARKER not in data
    assert not any(row["collection"].startswith("timescale:") for row in manifest["excluded"])

    target.collection("users").insert(
        {"_key": "new-lead", "email": "new-lead@example.com", "display_name": "New lead", "account_type": "human"}
    )
    dst = _service(target, tmp_path / "dst")
    old_lead = f"{A}-{LEAD}"
    accepted = dst.request_import(
        io.BytesIO(archive),
        size_bytes=len(archive),
        requester=_person(ADMIN),
        authenticated_with_api_key=False,
        member_mapping={old_lead: _grant("new-lead@example.com")},
        plan_key=None,
        factors=StepUpFactors(password="pw"),
        client_ip=None,
    )
    assert accepted.verified is True  # the signature covers the readings part's hash

    finished = run_async(dst.run_import(accepted.key or ""))

    assert finished is not None and finished.status == "completed", finished
    assert finished.report["not_imported:timeseries/readings.csv"] == len(expected)
