"""The list projections of #3015 against a real server: one read each, and each one tenant's.

The frontend used to assemble three views from a request per run, per site or per tenant-wide page: the run of every
plant (``listRunPlants`` per run), the plants and tanks of one location (the whole tenant's list filtered in the
browser) and the locations of every site (``listBeds`` / ``listLocations`` per site). Each now has a server read.
What no double decides is the AQL: that the tenant predicate sits where the tenant is actually recorded (the run, the
plant, the site - an edge and a location carry none), that a detached membership is not a run, and that the pages are
a total order.

Every "not there" assertion is paired with the tenant's own row read through the same call, so an empty answer
cannot come from a reader that sees nothing at all.
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.garden_plan_repository import ArangoGardenPlanRepository
from app.data_access.arango.plant_instance_repository import ArangoPlantInstanceRepository
from app.data_access.arango.planting_run_repository import ArangoPlantingRunRepository
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = pytest.mark.usefixtures("arango_db")

TEST_DATABASE = run_database_name("list_projections_tenant_scope")
A, B = "t_a", "t_b"


def _plant(key: str, tenant: str, location: str | None) -> dict:
    return {
        "_key": key,
        "tenant_key": tenant,
        "instance_id": key.upper(),
        "species_key": "basil",
        "planted_on": "2026-03-01",
        "location_key": location,
    }


def _run(key: str, tenant: str, started_at: str) -> dict:
    return {
        "_key": key,
        "tenant_key": tenant,
        "name": f"Run {key}",
        "run_type": "monoculture",
        "status": "active",
        "started_at": started_at,
    }


@pytest.fixture(scope="module")
def db():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    database = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    for name in (col.PLANT_INSTANCES, col.PLANTING_RUNS, col.SITES, col.LOCATIONS, col.LOCATION_TYPES):
        database.create_collection(name)
    database.create_collection(col.RUN_CONTAINS, edge=True)
    database.create_collection(col.CONTAINS, edge=True)

    database.collection(col.PLANT_INSTANCES).insert_many(
        [
            _plant("p_1", A, "loc_1"),
            _plant("p_2", A, "loc_1"),
            _plant("p_3", A, "loc_2"),
            _plant("p_4", B, "loc_1"),
        ]
    )
    database.collection(col.PLANTING_RUNS).insert_many(
        [
            _run("run_old", A, "2026-01-01T00:00:00+00:00"),
            _run("run_new", A, "2026-04-01T00:00:00+00:00"),
            _run("run_gone", A, "2026-05-01T00:00:00+00:00"),
            _run("run_foreign", B, "2026-06-01T00:00:00+00:00"),
        ]
    )
    runs = f"{col.PLANTING_RUNS}/"
    plants = f"{col.PLANT_INSTANCES}/"
    database.collection(col.RUN_CONTAINS).insert_many(
        [
            {"_from": runs + "run_old", "_to": plants + "p_1", "detached_at": None},
            {"_from": runs + "run_new", "_to": plants + "p_1", "detached_at": None},
            # A detached membership is history, not the plant's run.
            {"_from": runs + "run_gone", "_to": plants + "p_2", "detached_at": "2026-05-02T00:00:00+00:00"},
            # Another tenant's run naming one of A's plants is not named to A.
            {"_from": runs + "run_foreign", "_to": plants + "p_3", "detached_at": None},
        ]
    )

    database.collection(col.LOCATION_TYPES).insert_many(
        [{"_key": "bed", "is_bed": True}, {"_key": "tent", "is_bed": False}]
    )
    database.collection(col.SITES).insert_many(
        [
            {"_key": "site_a1", "tenant_key": A, "name": "Garten"},
            {"_key": "site_a2", "tenant_key": A, "name": "Feld"},
            {"_key": "site_b", "tenant_key": B, "name": "Fremd"},
        ]
    )
    database.collection(col.LOCATIONS).insert_many(
        [
            {"_key": "bed_c", "name": "Carrots", "site_key": "site_a1", "location_type_key": "bed"},
            {"_key": "bed_a", "name": "Asparagus", "site_key": "site_a2", "location_type_key": "bed", "area_m2": 6.5},
            # A nested bed is a bed too: the care log names its entries as well.
            {
                "_key": "bed_b",
                "name": "Beans",
                "site_key": "site_a1",
                "location_type_key": "bed",
                "parent_location_key": "bed_c",
            },
            {"_key": "tent_1", "name": "Aaa tent", "site_key": "site_a1", "location_type_key": "tent"},
            {"_key": "bed_foreign", "name": "Aaa foreign", "site_key": "site_b", "location_type_key": "bed"},
            # Unsited legacy roots (D1, #2561): the site's ``contains`` edge is their only link to a site.
            {"_key": "legacy_a", "name": "Old shed", "location_type_key": "tent"},
            {"_key": "legacy_b", "name": "Old foreign shed", "site_key": "", "location_type_key": "tent"},
            {"_key": "legacy_orphan", "name": "Nobody's shed", "location_type_key": "tent"},
        ]
    )
    database.collection(col.CONTAINS).insert_many(
        [
            {"_from": f"{col.SITES}/site_a1", "_to": f"{col.LOCATIONS}/legacy_a"},
            {"_from": f"{col.SITES}/site_b", "_to": f"{col.LOCATIONS}/legacy_b"},
        ]
    )
    yield database
    system.delete_database(TEST_DATABASE)


def test_run_refs_name_the_attached_runs_of_the_tenant_newest_first(db) -> None:
    refs = ArangoPlantingRunRepository(db).get_run_refs_for_plants(["p_1", "p_2", "p_3"], tenant_key=A)

    assert refs == {
        "p_1": [
            {"key": "run_new", "name": "Run run_new", "status": "active"},
            {"key": "run_old", "name": "Run run_old", "status": "active"},
        ]
    }


def test_run_refs_of_the_other_tenant_are_its_own(db) -> None:
    refs = ArangoPlantingRunRepository(db).get_run_refs_for_plants(["p_1", "p_3"], tenant_key=B)

    assert refs == {"p_3": [{"key": "run_foreign", "name": "Run run_foreign", "status": "active"}]}


def test_run_refs_refuse_an_empty_tenant(db) -> None:
    with pytest.raises(ValueError):
        ArangoPlantingRunRepository(db).get_run_refs_for_plants(["p_1"], tenant_key="")


def test_plants_at_a_location_are_the_tenants_and_page_by_key(db) -> None:
    repo = ArangoPlantInstanceRepository(db)

    first = repo.list_window_at_location(tenant_key=A, location_key="loc_1", limit=1)
    rest = repo.list_window_at_location(tenant_key=A, location_key="loc_1", limit=1, after=first[-1].key)
    beyond = repo.list_window_at_location(tenant_key=A, location_key="loc_1", limit=1, after=rest[-1].key)

    assert [p.key for p in first + rest] == ["p_1", "p_2"]
    assert beyond == []
    # B's plant stands at the same location key and is B's alone.
    assert [p.key for p in repo.list_window_at_location(tenant_key=B, location_key="loc_1")] == ["p_4"]


def test_bed_options_span_every_site_of_the_tenant_and_page_by_name(db) -> None:
    repo = ArangoGardenPlanRepository(db)

    everything = repo.list_location_options(tenant_key=A, offset=0, limit=50, is_bed=True)
    second_page = repo.list_location_options(tenant_key=A, offset=1, limit=1, is_bed=True)

    assert [(o.key, o.name, o.site_key, o.parent_location_key, o.area_m2) for o in everything] == [
        ("bed_a", "Asparagus", "site_a2", None, 6.5),
        ("bed_b", "Beans", "site_a1", "bed_c", None),
        ("bed_c", "Carrots", "site_a1", None, None),
    ]
    assert [o.key for o in second_page] == ["bed_b"]
    assert [o.key for o in repo.list_location_options(tenant_key=B, offset=0, limit=50, is_bed=True)] == ["bed_foreign"]


def test_location_options_filter_by_bed_flag_and_depth(db) -> None:
    repo = ArangoGardenPlanRepository(db)

    def keys(**kwargs) -> list[str]:
        return [o.key for o in repo.list_location_options(tenant_key=A, offset=0, limit=50, **kwargs)]

    assert keys() == ["tent_1", "bed_a", "bed_b", "bed_c", "legacy_a"]
    assert keys(is_bed=False) == ["tent_1", "legacy_a"]
    assert keys(top_level_only=True) == ["tent_1", "bed_a", "bed_c", "legacy_a"]


def test_location_options_name_an_unsited_legacy_root_by_the_site_whose_edge_reaches_it(db) -> None:
    repo = ArangoGardenPlanRepository(db)

    def sited(tenant: str) -> list[tuple[str, str]]:
        return [
            (o.key, o.site_key) for o in repo.list_location_options(tenant_key=tenant, offset=0, limit=50, is_bed=False)
        ]

    # The reader this replaced (``get_locations_by_site``) counted such a root; an orphan without an edge is no one's.
    assert sited(A) == [("tent_1", "site_a1"), ("legacy_a", "site_a1")]
    assert sited(B) == [("legacy_b", "site_b")]


def test_location_options_refuse_an_empty_tenant(db) -> None:
    with pytest.raises(ValueError):
        ArangoGardenPlanRepository(db).list_location_options(tenant_key="", offset=0, limit=50)
