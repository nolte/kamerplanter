"""REQ-053 WP 4.2 (#2412) — the location queue and the ``task_cloned_from`` edge against a real ArangoDB.

What no double decides: that the AQL of ``get_pending_tasks_in_locations`` finds the tasks on a bed *and* on the plants
standing in it, hides a removed plant's task and a foreign tenant's task of the same key, and that a ``garden_object``
binding writes its ``has_task`` edge from ``garden_objects``. Every "nothing there" is paired with the own-tenant
positive control through the same path.
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.task_repository import ArangoTaskRepository
from app.domain.models.task import Task
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = pytest.mark.usefixtures("arango_db")

TEST_DATABASE = run_database_name("task_location_queue")
A, B = "ten_a", "ten_b"
_DOCUMENTS = (
    col.TASKS,
    col.PLANT_INSTANCES,
    col.GARDEN_OBJECTS,
    col.LOCATIONS,
    col.TASK_COMMENTS,
    col.TASK_AUDIT_ENTRIES,
)
_EDGES = (
    col.HAS_TASK,
    col.TASK_CLONED_FROM,
    col.INSTANCE_OF,
    col.WF_GENERATED,
    col.TASK_BLOCKS,
    col.TASK_HAS_COMMENT,
    col.TASK_HAS_AUDIT,
)


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
    for name in _EDGES:
        db.create_collection(name, edge=True)
    yield db
    system.delete_database(TEST_DATABASE)


@pytest.fixture
def repo(database) -> ArangoTaskRepository:
    for entry in database.collections():
        if not entry["system"]:
            database.collection(entry["name"]).truncate()
    return ArangoTaskRepository(database)


def _task(key: str, tenant: str = A, **fields) -> dict:
    return {"_key": key, "tenant_key": tenant, "name": key, "status": "pending", "category": "watering", **fields}


def _seed(database) -> None:
    plants = database.collection(col.PLANT_INSTANCES)
    plants.insert({"_key": "p_here", "tenant_key": A, "location_key": "bed", "removed_on": None})
    plants.insert({"_key": "p_child", "tenant_key": A, "location_key": "child", "removed_on": None})
    plants.insert({"_key": "p_gone", "tenant_key": A, "location_key": "bed", "removed_on": "2026-01-01"})
    plants.insert({"_key": "p_foreign", "tenant_key": B, "location_key": "bed", "removed_on": None})
    tasks = database.collection(col.TASKS)
    tasks.insert(_task("on_bed", entity_type="location", entity_key="bed"))
    tasks.insert(_task("on_child", entity_type="location", entity_key="child"))
    tasks.insert(_task("on_plant", entity_type="plant_instance", entity_key="p_here"))
    tasks.insert(_task("on_child_plant", entity_type="plant_instance", entity_key="p_child"))
    tasks.insert(_task("on_removed_plant", entity_type="plant_instance", entity_key="p_gone"))
    tasks.insert(_task("foreign_bed", B, entity_type="location", entity_key="bed"))
    tasks.insert(_task("foreign_plant", A, entity_type="plant_instance", entity_key="p_foreign"))
    tasks.insert(_task("elsewhere", entity_type="location", entity_key="other"))
    tasks.insert(_task("done", status="completed", entity_type="location", entity_key="bed"))
    tasks.insert(_task("on_compost", entity_type="garden_object", entity_key="bed"))


def _keys(tasks: list[Task]) -> list[str]:
    return sorted(t.key for t in tasks)


def test_the_bed_its_children_and_their_plants_are_found(database, repo) -> None:
    _seed(database)

    found = repo.get_pending_tasks_in_locations(["bed", "child"], 200, tenant_key=A)

    assert _keys(found) == ["on_bed", "on_child", "on_child_plant", "on_plant"]


def test_without_the_child_only_the_bed_and_its_own_plants(database, repo) -> None:
    _seed(database)

    assert _keys(repo.get_pending_tasks_in_locations(["bed"], 200, tenant_key=A)) == ["on_bed", "on_plant"]


def test_a_foreign_tenant_reads_its_own_not_ours(database, repo) -> None:
    _seed(database)

    assert _keys(repo.get_pending_tasks_in_locations(["bed"], 200, tenant_key=B)) == ["foreign_bed"]


def test_a_foreign_plant_standing_in_the_bed_does_not_bring_its_task_into_our_queue(database, repo) -> None:
    _seed(database)

    keys = _keys(repo.get_pending_tasks_in_locations(["bed"], 200, tenant_key=A))

    assert "foreign_plant" not in keys and "on_plant" in keys


def test_a_garden_object_task_is_not_a_location_task_even_under_the_same_key(database, repo) -> None:
    _seed(database)

    assert "on_compost" not in _keys(repo.get_pending_tasks_in_locations(["bed"], 200, tenant_key=A))


def test_no_locations_match_nothing(database, repo) -> None:
    _seed(database)

    assert repo.get_pending_tasks_in_locations([], 200, tenant_key=A) == []


def test_the_limit_is_applied_after_the_filter(database, repo) -> None:
    _seed(database)

    assert len(repo.get_pending_tasks_in_locations(["bed", "child"], 2, tenant_key=A)) == 2


def test_a_garden_object_task_gets_its_has_task_edge_from_the_object_collection(database, repo) -> None:
    created = repo.create_task(Task(tenant_key=A, name="Turn", entity_type="garden_object", entity_key="go_1"))

    (edge,) = list(database.collection(col.HAS_TASK).all())
    assert edge["_from"] == f"{col.GARDEN_OBJECTS}/go_1"
    assert edge["_to"] == f"{col.TASKS}/{created.key}"


def test_the_cloned_from_edge_runs_clone_to_source_and_dies_with_either_end(database, repo) -> None:
    source = repo.create_task(Task(tenant_key=A, name="Water", entity_type="location", entity_key="bed"))
    clone = repo.create_task(Task(tenant_key=A, name="Water", entity_type="plant_instance", entity_key="p_here"))
    repo.create_task_cloned_from_edge(clone.key, source.key)

    (edge,) = list(database.collection(col.TASK_CLONED_FROM).all())
    assert (edge["_from"], edge["_to"]) == (f"{col.TASKS}/{clone.key}", f"{col.TASKS}/{source.key}")

    repo.delete_task(source.key)

    assert list(database.collection(col.TASK_CLONED_FROM).all()) == []


def test_the_clone_entities_of_a_source_are_found_inside_the_tenant_only(database, repo) -> None:
    source = repo.create_task(Task(tenant_key=A, name="Water", entity_type="location", entity_key="bed"))
    own = repo.create_task(Task(tenant_key=A, name="Water", entity_type="plant_instance", entity_key="p_here"))
    foreign = repo.create_task(Task(tenant_key=B, name="Water", entity_type="plant_instance", entity_key="p_other"))
    repo.create_task_cloned_from_edge(own.key, source.key)
    repo.create_task_cloned_from_edge(foreign.key, source.key)

    assert repo.get_clone_entity_keys(source.key, tenant_key=A) == {"p_here"}
    assert repo.get_clone_entity_keys(source.key, tenant_key=B) == {"p_other"}
