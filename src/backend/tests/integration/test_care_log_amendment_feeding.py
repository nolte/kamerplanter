"""REQ-053 WP 10.12 (#2833) — both ways of recording a nutrient amendment store exactly one ``feeding_event``.

Against a real ArangoDB, through the services: ``POST /care-events`` (``CareEventService.log``) and
``POST /tasks/{key}/complete`` (``TaskService.complete_task``) with ``soil_amendment`` + ``compost``. What no double
can decide is measured here: the rows really stored per action (one ``feeding_events`` document, its ``fed_by``
edges, a care event whose ``source_ref`` names it - the reference the daily consistency job reads as "already
logged"), that the completion does not store a second one through the care-log path, and that a buffered replay
stores nothing more. Every "one row" count is paired with the reference the care event carries, so a count of one
cannot be some other row.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from arango import ArangoClient

from app.common.enums import TenantRole
from app.data_access.arango import collections as col
from app.data_access.arango.care_event_repository import ArangoCareEventRepository
from app.data_access.arango.task_completion_repository import ArangoTaskCompletionRepository
from app.data_access.arango.task_repository import ArangoTaskRepository
from app.domain.engines.dependency_resolver import DependencyResolver
from app.domain.engines.hst_validator import HSTValidator
from app.domain.models.care_event import CareEventInput
from app.domain.models.task_completion import CompletionActor, TaskCompletionDetails
from app.domain.services.care_event_service import CareEventService
from app.domain.services.task_service import TaskService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name
from tests.support.care_event_fakes import FakeAttachmentRepo, FakeAttachmentService, FakeFertilizers, FakeMemberships
from tests.support.garden_plan_fakes import TENANT, USER, FakePlanRepo, FakeSites, make_location, make_site
from tests.support.task_completion_fakes import FakeHarvests

pytestmark = pytest.mark.usefixtures("arango_db")

TEST_DATABASE = run_database_name("care_log_amendment_feeding")
ACTOR = CompletionActor(user_key=USER, role=TenantRole.GROWER)


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    # The production collections and indexes: the client-event index decides a replay.
    col.ensure_collections(db)
    yield db
    system.delete_database(TEST_DATABASE)


@pytest.fixture
def db(database):
    for name in (
        col.CARE_EVENTS,
        col.TASKS,
        col.PLANT_INSTANCES,
        col.FEEDING_EVENTS,
        col.FED_BY,
        col.FEEDING_USED,
        col.CARE_EVENT_AT,
        col.CARE_EVENT_FOR,
        col.TASK_LOGGED_AS,
    ):
        database.collection(name).truncate()
    database.collection(col.TASKS).insert(
        {
            "_key": "t_amend",
            "tenant_key": TENANT,
            "name": "Compost bed 3",
            "category": "soil_amendment",
            "status": "pending",
            "entity_type": "location",
            "entity_key": "bed",
            "photo_refs": [],
        }
    )
    for key in ("pi_1", "pi_2"):
        database.collection(col.PLANT_INSTANCES).insert(
            {"_key": key, "instance_id": key, "tenant_key": TENANT, "location_key": "bed"}
        )
    return database


def _care(handle: Any) -> CareEventService:
    sites = FakeSites(make_site())
    plan = FakePlanRepo(sites)
    plan.locations["bed"] = make_location("bed", name="Bed 3").model_copy(update={"area_m2": 2.0})
    return CareEventService(
        ArangoCareEventRepository(handle),
        sites,
        FakeMemberships(),
        FakeFertilizers(),
        FakeAttachmentRepo(),
        FakeAttachmentService(),
    )


def _tasks(handle: Any) -> TaskService:
    return TaskService(
        ArangoTaskRepository(handle),
        HSTValidator(),
        DependencyResolver(),
        completion=ArangoTaskCompletionRepository(handle),
        care_events=_care(handle),
        harvests=FakeHarvests(),
        fertilizers=FakeFertilizers(),
    )


def _amendment(**overrides: Any) -> CareEventInput:
    data: dict[str, Any] = {
        "location_key": "bed",
        "category": "soil_amendment",
        "summary": "Compost spread",
        "performed_at": datetime.now(UTC) - timedelta(hours=1),
        "material": "compost",
        "quantity": 3,
        "unit": "g_per_m2",
        **overrides,
    }
    return CareEventInput(**data)


def _feedings(db: Any) -> list[dict[str, Any]]:
    return list(db.collection(col.FEEDING_EVENTS).all())


def _fed_by(db: Any, feeding_key: str) -> list[str]:
    return sorted(e["_from"] for e in db.collection(col.FED_BY).all() if e["_to"] == f"feeding_events/{feeding_key}")


class TestBothWays:
    def test_the_care_log_way_stores_one_feeding_event_its_line_names(self, db) -> None:
        logged = _care(db).log(_amendment(), tenant_key=TENANT, user_key=USER, role=TenantRole.GROWER)

        (feeding,) = _feedings(db)
        stored = db.collection(col.CARE_EVENTS).get(logged.view.event.key)
        assert stored["source_ref"] == {"collection": "feeding_events", "key": feeding["_key"]}
        assert (feeding["tenant_key"], feeding["location_key"], feeding["material"]) == (TENANT, "bed", "compost")
        assert (feeding["quantity_total"], feeding["quantity_total_unit"]) == (6.0, "g")  # 3 g/m² x 2 m²
        assert "task_key" not in feeding
        assert _fed_by(db, feeding["_key"]) == ["plant_instances/pi_1", "plant_instances/pi_2"]

    def test_the_task_way_stores_one_feeding_event_and_nothing_through_the_care_log(self, db) -> None:
        _tasks(db).complete_task(
            "t_amend",
            tenant_key=TENANT,
            details=TaskCompletionDetails(material="compost", quantity=3, unit="g_per_m2"),
            actor=ACTOR,
        )

        (feeding,) = _feedings(db)
        (stored,) = list(db.collection(col.CARE_EVENTS).all())
        assert stored["source_ref"] == {"collection": "feeding_events", "key": feeding["_key"]}
        assert (stored["trigger"], stored["task_key"]) == ("task", "t_amend")
        assert feeding["task_key"] == "t_amend"
        assert _fed_by(db, feeding["_key"]) == ["plant_instances/pi_1", "plant_instances/pi_2"]

    def test_one_action_each_way_is_two_feeding_events_one_per_line(self, db) -> None:
        _care(db).log(_amendment(), tenant_key=TENANT, user_key=USER, role=TenantRole.GROWER)
        _tasks(db).complete_task(
            "t_amend",
            tenant_key=TENANT,
            details=TaskCompletionDetails(material="compost", quantity=3, unit="g_per_m2"),
            actor=ACTOR,
        )

        feedings = _feedings(db)
        events = list(db.collection(col.CARE_EVENTS).all())
        assert len(feedings) == 2 and len(events) == 2
        assert sorted(e["source_ref"]["key"] for e in events) == sorted(f["_key"] for f in feedings)

    def test_a_replayed_buffered_entry_stores_no_second_feeding_event(self, db) -> None:
        service = _care(db)
        body = _amendment(client_event_id=uuid.uuid4())

        answers = [service.log(body, tenant_key=TENANT, user_key=USER, role=TenantRole.GROWER) for _ in range(3)]

        assert [answer.replayed for answer in answers] == [False, True, True]
        (feeding,) = _feedings(db)
        (stored,) = list(db.collection(col.CARE_EVENTS).all())
        assert stored["source_ref"]["key"] == feeding["_key"]

    def test_an_amendment_without_a_nutrient_effect_stores_no_feeding_event(self, db) -> None:
        logged = _care(db).log(_amendment(material="sand"), tenant_key=TENANT, user_key=USER, role=TenantRole.GROWER)

        assert _feedings(db) == []
        # positive control: the line itself is there, read through the same collection
        assert db.collection(col.CARE_EVENTS).get(logged.view.event.key)["material"] == "sand"
