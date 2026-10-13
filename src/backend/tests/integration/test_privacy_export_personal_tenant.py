"""#2135 (MT-039) — the personal garden reaches the Art. 15 bundle, and nothing else does, on a real ArangoDB.

``ArangoPersonalDataRepository._collect_personal_tenant`` is AQL over a parent chain
(``locations`` → ``sites``, ``slots`` → ``locations`` → ``sites``), so only a real server
says which rows it reaches. Built the way the data exists: a subject with a personal
tenant (a site with GPS, a location and slot whose own ``tenant_key`` is empty — no write
path fills it, #1397 — a plant, a task another member wrote), an organisation the subject
is a member of, and another user's personal garden.

Locally it needs a database::

    docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_privacy_export_personal_tenant.py -v
"""

from __future__ import annotations

from typing import Any

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.collections import ensure_collections
from app.data_access.arango.personal_data_repository import ArangoPersonalDataRepository
from app.domain.engines.data_export_engine import DataExportEngine
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the personal-tenant anchor is AQL over a parent chain"),
]

_DB_NAME = run_database_name("privacy_export_personal_tenant")
SUBJECT = "u-subject"
OWN = "t-own-personal"
ORG = "t-org"
FOREIGN = "t-foreign-personal"


@pytest.fixture
def db():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)
    system.create_database(_DB_NAME)
    database = client.db(_DB_NAME, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    ensure_collections(database)
    _garden(database)
    yield database
    system.delete_database(_DB_NAME)


def _ins(db, collection: str, **doc: Any) -> None:  # type: ignore[no-untyped-def]
    db.collection(collection).insert(doc)


def _garden(db) -> None:  # type: ignore[no-untyped-def]
    for key, coordinates in ((OWN, [52.52, 13.405]), (ORG, [48.137, 11.575]), (FOREIGN, [53.55, 9.993])):
        _ins(db, col.SITES, _key=f"site-{key}", tenant_key=key, name=f"Site {key}", gps_coordinates=coordinates)
        # Location and slot as the write paths store them: without a tenant_key (#1397).
        _ins(db, col.LOCATIONS, _key=f"loc-{key}", tenant_key="", name=f"Bed {key}", site_key=f"site-{key}")
        _ins(db, col.SLOTS, _key=f"slot-{key}", tenant_key="", slot_id=f"S-{key}", location_key=f"loc-{key}")
        _ins(db, col.PLANT_INSTANCES, _key=f"plant-{key}", tenant_key=key, instance_id=f"P-{key}", species_key="sp")
        _ins(
            db,
            col.TASKS,
            _key=f"task-{key}",
            tenant_key=key,
            name=f"Water {key}",
            assigned_to_user_key="someone-else",
            completion_notes=f"note {key}",
        )
        # #2165 — the tank logs hang off their tank (no tenant_key of their own); the
        # watering and feeding logs carry tenant_key; a sensor hangs off exactly one of a
        # tank, a site or a location and carries no tenant_key.
        _ins(db, col.TANKS, _key=f"tank-{key}", tenant_key=key, name=f"Tank {key}", tank_type="nutrient")
        _ins(db, col.TANK_STATES, _key=f"ts-{key}", tank_key=f"tank-{key}", ph=6.1)
        _ins(db, col.TANK_FILL_EVENTS, _key=f"tf-{key}", tank_key=f"tank-{key}", performed_by="someone-else")
        _ins(db, col.MAINTENANCE_LOGS, _key=f"ml-{key}", tank_key=f"tank-{key}", maintenance_type="cleaning")
        _ins(db, col.WATERING_EVENTS, _key=f"we-{key}", tenant_key=key, volume_liters=1.0)
        _ins(db, col.WATERING_LOGS, _key=f"wl-{key}", tenant_key=key, volume_liters=2.0, performed_by="u-x")
        _ins(db, col.FEEDING_EVENTS, _key=f"fe-{key}", tenant_key=key, plant_key=f"plant-{key}")
        _ins(db, col.SENSORS, _key=f"sensor-tank-{key}", name="EC", metric_type="ec_ms", tank_key=f"tank-{key}")
        _ins(db, col.SENSORS, _key=f"sensor-site-{key}", name="Air", metric_type="temp", site_key=f"site-{key}")
        _ins(db, col.SENSORS, _key=f"sensor-loc-{key}", name="Soil", metric_type="vwc", location_key=f"loc-{key}")
    # A location whose parent site is missing must not be attributed to anybody.
    _ins(db, col.LOCATIONS, _key="loc-dangling", tenant_key="", name="Dangling", site_key="site-gone")
    # Neither may a sensor whose parent is gone, nor a tank log of a missing tank.
    _ins(db, col.SENSORS, _key="sensor-dangling", name="Lost", metric_type="ph", tank_key="tank-gone")
    _ins(db, col.TANK_STATES, _key="ts-dangling", tank_key="tank-gone", ph=7.0)


def _rows(db, collection: str, keys: list[str]) -> list[dict[str, Any]]:  # type: ignore[no-untyped-def]
    (source,) = [
        s
        for s in DataExportEngine().build_export_manifest(SUBJECT)
        if s.collection == collection and s.personal_tenant_scope is not None
    ]
    return ArangoPersonalDataRepository(db).collect_for_user(source, SUBJECT, keys)


def test_the_own_personal_site_comes_with_its_coordinates(db) -> None:  # type: ignore[no-untyped-def]
    rows = _rows(db, "sites", [OWN])

    assert rows == [
        {"_key": f"site-{OWN}", "name": f"Site {OWN}", "gps_coordinates": [52.52, 13.405]},
    ]


@pytest.mark.parametrize(
    ("collection", "expected"),
    [
        ("locations", [f"loc-{OWN}"]),
        ("slots", [f"slot-{OWN}"]),
        ("plant_instances", [f"plant-{OWN}"]),
        ("tasks", [f"task-{OWN}"]),
        # #2165
        ("tanks", [f"tank-{OWN}"]),
        ("tank_states", [f"ts-{OWN}"]),
        ("tank_fill_events", [f"tf-{OWN}"]),
        ("maintenance_logs", [f"ml-{OWN}"]),
        ("watering_events", [f"we-{OWN}"]),
        ("watering_logs", [f"wl-{OWN}"]),
        ("feeding_events", [f"fe-{OWN}"]),
        ("sensors", sorted([f"sensor-loc-{OWN}", f"sensor-site-{OWN}", f"sensor-tank-{OWN}"])),
    ],
)
def test_only_the_own_personal_garden_is_reached(db, collection: str, expected: list[str]) -> None:  # type: ignore[no-untyped-def]
    rows = _rows(db, collection, [OWN])

    assert sorted(row["_key"] for row in rows) == expected


def test_another_members_assignment_is_not_handed_out(db) -> None:  # type: ignore[no-untyped-def]
    (task,) = _rows(db, "tasks", [OWN])

    assert "assigned_to_user_key" not in task
    assert task["completion_notes"] == f"note {OWN}"


def test_the_logs_carry_no_other_accounts_name(db) -> None:  # type: ignore[no-untyped-def]
    """#2165 — ``performed_by`` names whoever performed the step; it stays out (Art. 15(4))."""
    for collection in ("tank_fill_events", "watering_logs"):
        (row,) = _rows(db, collection, [OWN])
        assert "performed_by" not in row, collection


def test_no_personal_tenant_means_no_rows_not_all_of_them(db) -> None:  # type: ignore[no-untyped-def]
    for collection in (
        "sites",
        "locations",
        "slots",
        "plant_instances",
        "tasks",
        "tanks",
        "tank_states",
        "watering_logs",
        "feeding_events",
        "sensors",
    ):
        assert _rows(db, collection, []) == [], collection
