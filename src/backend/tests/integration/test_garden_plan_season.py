"""REQ-053 WP 7.16 (#2482) - "new season from the previous year" against a real ArangoDB.

What no double decides: that the slots land in one transaction with the revision bump and an audit row of counts,
that they arrive free (``season_copy``, no occupation) and attached to their bed, that nothing else changes
(plants, runs, the archived slots, zones), that a second run copies nothing, and that a foreign site is a 404.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from arango import ArangoClient

from app.common.enums import TenantRole
from app.common.exceptions import NotFoundError, PlanError, PlanRevisionConflictError
from app.data_access.arango import collections as col
from app.data_access.arango.garden_plan_repository import _BATCH_WRITE, ArangoGardenPlanRepository
from app.data_access.arango.site_repository import ArangoSiteRepository
from app.domain.services.garden_plan_season_service import GardenPlanSeasonService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = pytest.mark.usefixtures("arango_db")

TEST_DATABASE = run_database_name("garden_plan_season")
A, B = "ten_a", "ten_b"
USER = "u_sabine"
_DOCUMENTS = (
    col.SITES,
    col.LOCATIONS,
    col.SLOTS,
    col.GARDEN_OBJECTS,
    col.GARDEN_PLAN_AUDIT,
    col.CARE_EVENTS,
    col.LOCATION_TYPES,
    col.USERS,
    col.PLANT_INSTANCES,
    col.IRRIGATION_ZONES,
    col.ACTUATORS,
    col.SUBSTRATES,
)
_EDGES = tuple(
    definition["edge_collection"]
    for definition in col.GRAPH_EDGE_DEFINITIONS
    if definition["edge_collection"] in _BATCH_WRITE
)
_LAST_YEAR = datetime(2026, 8, 1, tzinfo=UTC).isoformat()
_BOUNDARY = {"kind": "rect", "origin": [0, 0], "width_m": 20, "length_m": 20, "rotation_deg": 0}


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    for name in _DOCUMENTS:
        db.create_collection(name)
    for name in dict.fromkeys(_EDGES):
        db.create_collection(name, edge=True)
    db.collection(col.SLOTS).add_persistent_index(fields=col.SLOT_ID_INDEX_FIELDS, unique=True)
    yield db
    system.delete_database(TEST_DATABASE)


def _slot(key: str, bed: str, slot_id: str, x: float, archived: str | None) -> dict[str, Any]:
    return {
        "_key": key,
        "slot_id": slot_id,
        "location_key": bed,
        "capacity_plants": 1,
        "currently_occupied": False,
        "slot_role": "position",
        "geometry": {"kind": "point", "origin": [x, 0.5]},
        "sequence": int(x * 2),
        "archived_at": archived,
    }


@pytest.fixture
def db(database):
    for entry in database.collections():
        if not entry["system"]:
            database.collection(entry["name"]).truncate()
    database.collection(col.USERS).insert({"_key": USER, "display_name": "Sabine"})
    database.collection(col.SITES).insert(
        {
            "_key": "site_a",
            "tenant_key": A,
            "name": "Garten A",
            "type": "outdoor",
            "total_area_m2": 0.0,
            "timezone": "UTC",
            "plan": {"plan_revision": 5, "boundary": _BOUNDARY},
        }
    )
    database.collection(col.SITES).insert(
        {"_key": "site_b", "tenant_key": B, "name": "Garten B", "type": "outdoor", "timezone": "UTC"}
    )
    for key, site in (("bed_1", "site_a"), ("bed_2", "site_a"), ("bed_x", "site_b")):
        database.collection(col.LOCATIONS).insert(
            {
                "_key": key,
                "site_key": site,
                "name": key,
                "location_type_key": "bed",
                "geometry": {"kind": "rect", "origin": [1, 1], "width_m": 4, "length_m": 2, "rotation_deg": 0},
                "path": f"{key}",
                "area_m2": 8.0,
                "depth": 0,
            }
        )
    database.collection(col.SLOTS).import_bulk(
        [
            _slot("o1", "bed_1", "B1_A", 0.5, _LAST_YEAR),
            _slot("o2", "bed_1", "B1_B", 1.5, _LAST_YEAR),
            _slot("o3", "bed_2", "B2_A", 0.5, _LAST_YEAR),
            _slot("ox", "bed_x", "BX_A", 0.5, _LAST_YEAR),
        ]
    )
    database.collection(col.PLANT_INSTANCES).insert(
        {"_key": "plant_1", "location_key": "bed_2", "removed_on": None, "tenant_key": A}
    )
    return database


@pytest.fixture
def service(db) -> GardenPlanSeasonService:
    return GardenPlanSeasonService(ArangoSiteRepository(db), ArangoGardenPlanRepository(db))


def _run(service: GardenPlanSeasonService, *, site="site_a", tenant=A, role=TenantRole.LEAD, **options: Any):
    arguments = {"year": 2027, "dry_run": False} | options
    return service.new_season(site, tenant_key=tenant, user_key=USER, role=role, **arguments)


def _live(db, bed: str) -> list[dict[str, Any]]:
    return [s for s in db.collection(col.SLOTS).find({"location_key": bed}) if s.get("archived_at") is None]


def test_free_slots_arrive_in_one_transaction_with_revision_and_audit(db, service) -> None:
    report = _run(service)

    assert (report.beds_copied, report.beds_skipped, report.slots_to_create) == (1, 1, 2) and report.applied
    created = _live(db, "bed_1")
    assert len(created) == 2
    assert all(s["geometry_source"] == "season_copy" and s["currently_occupied"] is False for s in created)
    assert {s["slot_id"] for s in created} == {"S2027_001", "S2027_002"}
    assert db.collection(col.SITES).get("site_a")["plan"]["plan_revision"] == report.plan_revision == 6
    edges = list(db.collection(col.HAS_SLOT).find({"_from": "locations/bed_1"}))
    assert len(edges) == 2
    (row,) = list(db.collection(col.GARDEN_PLAN_AUDIT).find({"op": "season_copy"}))
    assert (row["tenant_key"], row["site_key"], row["revision"], row["summary"]) == (
        A,
        "site_a",
        6,
        "year 2027: 1 beds, 2 slots",
    )


def test_the_bed_with_a_plant_and_the_history_stay_as_they_were(db, service) -> None:
    before = {s["_key"]: s for s in db.collection(col.SLOTS).all()}

    _run(service)

    assert _live(db, "bed_2") == []  # skipped: a plant stands there
    after = {s["_key"]: s for s in db.collection(col.SLOTS).all()}
    assert all(after[key] == before[key] for key in before)  # the archived slots are untouched
    assert db.collection(col.PLANT_INSTANCES).count() == 1
    assert _live(db, "bed_x") == []  # the other tenant's bed is not reached


def test_a_dry_run_writes_nothing_and_a_second_run_copies_nothing(db, service) -> None:
    dry = _run(service, dry_run=True)
    assert dry.slots_to_create == 2 and not dry.applied
    assert _live(db, "bed_1") == [] and db.collection(col.SITES).get("site_a")["plan"]["plan_revision"] == 5

    _run(service)
    again = _run(service)

    assert again.slots_to_create == 0 and len(_live(db, "bed_1")) == 2
    assert db.collection(col.SITES).get("site_a")["plan"]["plan_revision"] == 6


def test_a_stale_revision_is_a_409_and_writes_nothing(db, service) -> None:
    with pytest.raises(PlanRevisionConflictError):
        _run(service, expected_revision=4)

    assert _live(db, "bed_1") == []


def test_a_foreign_site_is_a_404_and_a_grower_a_403(db, service) -> None:
    with pytest.raises(NotFoundError):
        _run(service, site="site_b", tenant=A)
    with pytest.raises(PlanError) as error:
        _run(service, role=TenantRole.GROWER)
    assert error.value.status_code == 403 and _live(db, "bed_1") == []
