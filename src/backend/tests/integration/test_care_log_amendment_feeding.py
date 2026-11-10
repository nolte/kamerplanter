"""REQ-053 WP 10.12 (#2833) — both ways of recording a nutrient amendment store exactly one ``feeding_event``.

Against a real ArangoDB, through the services: ``POST /care-events`` (``CareEventService.log``) and
``POST /tasks/{key}/complete`` (``TaskService.complete_task``) with ``soil_amendment`` + ``compost``. What no double
can decide is measured here: the rows really stored per action (one ``feeding_events`` document, its ``fed_by``
edges, a care event whose ``source_ref`` names it - the reference the daily consistency job reads as "already
logged"), that the completion does not store a second one through the care-log path, and that a buffered replay
stores nothing more. Every "one row" count is paired with the reference the care event carries, so a count of one
cannot be some other row.

Taking the entry back: a void (the snackbar undo included) removes the entry's feeding event and its edges in the
same transaction, a correction replaces it by one for the corrected dose (or by none), a backfilled line's mirrored
document stays, the task undo still withdraws exactly once, a server caller's ``source_ref`` is never replaced and a
whole bed beyond ``MAX_PLANTS_PER_EVENT`` is refused before anything is written.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from arango import ArangoClient

from app.common.enums import TenantRole
from app.common.exceptions import PlanError
from app.data_access.arango import collections as col
from app.data_access.arango.care_event_repository import (
    WITHDRAWABLE_WRITE_COLLECTIONS,
    ArangoCareEventRepository,
    plant_keys_standing_in,
    withdraw_domain_document,
)
from app.data_access.arango.task_completion_repository import ArangoTaskCompletionRepository
from app.data_access.arango.task_repository import ArangoTaskRepository
from app.data_access.arango.transactions import stream_transaction
from app.domain.engines.dependency_resolver import DependencyResolver
from app.domain.engines.hst_validator import HSTValidator
from app.domain.models.care_event import (
    MAX_PLANTS_PER_EVENT,
    CareEvent,
    CareEventCorrection,
    CareEventInput,
    CareEventOrigin,
)
from app.domain.models.task_completion import CompletionActor, TaskCompletionDetails
from app.domain.services.care_event_service import CareEventService
from app.domain.services.task_service import TaskService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name
from tests.support.care_event_fakes import FakeAttachmentRepo, FakeAttachmentService, FakeFertilizers, FakeMemberships
from tests.support.garden_plan_fakes import (
    SITE,
    TENANT,
    USER,
    FakePlanRepo,
    FakeSites,
    make_location,
    make_site,
)
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


def _correction(**overrides: Any) -> CareEventCorrection:
    data: dict[str, Any] = {
        "category": "soil_amendment",
        "summary": "Compost spread",
        "performed_at": datetime.now(UTC) - timedelta(hours=1),
        "material": "compost",
        "quantity": 3,
        "unit": "g_per_m2",
        **overrides,
    }
    return CareEventCorrection(**data)


def _edges_of(db: Any, collection: str) -> list[dict[str, Any]]:
    return list(db.collection(collection).all())


class TestTakingTheEntryBack:
    def test_the_undo_of_a_logged_amendment_removes_its_feeding_event_and_edges(self, db) -> None:
        care = _care(db)
        logged = care.log(_amendment(), tenant_key=TENANT, user_key=USER, role=TenantRole.GROWER)
        (feeding,) = _feedings(db)
        assert len(_fed_by(db, feeding["_key"])) == 2  # positive control: the edges were there

        care.void(logged.view.event.key, reason="undo", tenant_key=TENANT, user_key=USER, role=TenantRole.GROWER)

        assert _feedings(db) == []
        assert _edges_of(db, col.FED_BY) == [] and _edges_of(db, col.FEEDING_USED) == []
        stored = db.collection(col.CARE_EVENTS).get(logged.view.event.key)
        assert (stored["void_reason"], stored["source_ref"]["key"]) == ("undo", feeding["_key"])

    def test_voiding_a_backfilled_line_keeps_the_feeding_event_it_mirrors(self, db) -> None:
        db.collection(col.FEEDING_EVENTS).insert({"_key": "fe_own_form", "tenant_key": TENANT})
        db.collection(col.FED_BY).insert({"_from": "plant_instances/pi_1", "_to": "feeding_events/fe_own_form"})
        line = ArangoCareEventRepository(db).insert(
            CareEvent(
                tenant_key=TENANT,
                site_key=SITE,
                location_key="bed",
                category="feeding",
                summary="Feeding",
                performed_at=datetime.now(UTC) - timedelta(days=3),
                trigger="backfill",
                source_ref={"collection": "feeding_events", "key": "fe_own_form"},
                created_by=USER,
            ),
            tenant_key=TENANT,
        )

        _care(db).void(line.key or "", reason="wrong bed", tenant_key=TENANT, user_key=USER, role=TenantRole.LEAD)

        assert [f["_key"] for f in _feedings(db)] == ["fe_own_form"]
        assert _fed_by(db, "fe_own_form") == ["plant_instances/pi_1"]

    def test_a_task_undo_still_leaves_no_feeding_event_and_withdraws_once(self, db) -> None:
        tasks = _tasks(db)
        tasks.complete_task(
            "t_amend",
            tenant_key=TENANT,
            details=TaskCompletionDetails(material="compost", quantity=3, unit="g_per_m2"),
            actor=ACTOR,
        )
        assert len(_feedings(db)) == 1  # positive control

        tasks.reopen_task("t_amend", tenant_key=TENANT, undo=True, actor=ACTOR)

        assert _feedings(db) == []
        assert _edges_of(db, col.FED_BY) == [] and _edges_of(db, col.FEEDING_USED) == []
        (line,) = list(db.collection(col.CARE_EVENTS).all())
        assert line["void_reason"] == "undo"

    def test_a_second_withdrawal_of_the_same_document_is_no_error_and_no_effect(self, db) -> None:
        logged = _care(db).log(_amendment(), tenant_key=TENANT, user_key=USER, role=TenantRole.GROWER)
        reference = db.collection(col.CARE_EVENTS).get(logged.view.event.key)["source_ref"]

        outcomes = []
        for _ in range(2):
            with stream_transaction(db, write=WITHDRAWABLE_WRITE_COLLECTIONS, entity="care_event") as txn:
                outcomes.append(withdraw_domain_document(txn, reference, tenant_key=TENANT))

        assert outcomes == [True, False]
        assert _feedings(db) == [] and _edges_of(db, col.FED_BY) == []

    def test_another_tenants_document_is_not_withdrawn(self, db) -> None:
        logged = _care(db).log(_amendment(), tenant_key=TENANT, user_key=USER, role=TenantRole.GROWER)
        reference = db.collection(col.CARE_EVENTS).get(logged.view.event.key)["source_ref"]

        with stream_transaction(db, write=WITHDRAWABLE_WRITE_COLLECTIONS, entity="care_event") as txn:
            assert withdraw_domain_document(txn, reference, tenant_key="t_other") is False

        assert len(_feedings(db)) == 1 and len(_edges_of(db, col.FED_BY)) == 2


class TestCorrectingTheEntry:
    def test_a_corrected_quantity_leaves_exactly_one_feeding_event_with_the_new_dose(self, db) -> None:
        care = _care(db)
        logged = care.log(_amendment(), tenant_key=TENANT, user_key=USER, role=TenantRole.GROWER)
        (old,) = _feedings(db)

        view = care.supersede(
            logged.view.event.key, _correction(quantity=5), tenant_key=TENANT, user_key=USER, role=TenantRole.GROWER
        )

        (feeding,) = _feedings(db)
        assert feeding["_key"] != old["_key"]
        assert (feeding["dose_quantity"], feeding["quantity_total"]) == (5, 10.0)  # 5 g/m² x 2 m²
        successor = db.collection(col.CARE_EVENTS).get(view.event.key)
        assert successor["source_ref"] == {"collection": "feeding_events", "key": feeding["_key"]}
        assert _fed_by(db, old["_key"]) == []
        assert _fed_by(db, feeding["_key"]) == ["plant_instances/pi_1", "plant_instances/pi_2"]
        assert len(_edges_of(db, col.FED_BY)) == 2

    def test_a_correction_to_another_category_leaves_no_feeding_event(self, db) -> None:
        care = _care(db)
        logged = care.log(_amendment(), tenant_key=TENANT, user_key=USER, role=TenantRole.GROWER)

        view = care.supersede(
            logged.view.event.key,
            _correction(category="mulching", unit="cm", quantity=5),
            tenant_key=TENANT,
            user_key=USER,
            role=TenantRole.GROWER,
        )

        assert _feedings(db) == [] and _edges_of(db, col.FED_BY) == []
        assert "source_ref" not in db.collection(col.CARE_EVENTS).get(view.event.key)


class TestAServerCaller:
    def test_an_origin_keeps_its_source_ref_and_stores_no_feeding_event(self, db) -> None:
        reference = {"collection": "feeding_events", "key": "fe_caller"}

        view = _care(db).create(
            _amendment(),
            tenant_key=TENANT,
            user_key=USER,
            role=TenantRole.GROWER,
            origin=CareEventOrigin(trigger="system", source_ref=reference),
        )

        assert _feedings(db) == []
        assert db.collection(col.CARE_EVENTS).get(view.event.key)["source_ref"] == reference

    def test_the_repository_refuses_a_feeding_event_for_a_line_that_names_a_source(self, db) -> None:
        care = _care(db)
        event = care.build_event(_amendment(), tenant_key=TENANT, user_key=USER, role=TenantRole.GROWER)
        feeding = care._amendment_feeding(event, tenant_key=TENANT)
        assert feeding is not None
        named = event.model_copy(update={"source_ref": {"collection": "feeding_events", "key": "fe_caller"}})

        with pytest.raises(ValueError, match="names a source document already"):
            ArangoCareEventRepository(db).insert_with_feeding_event(named, feeding, tenant_key=TENANT)

        assert _feedings(db) == [] and list(db.collection(col.CARE_EVENTS).all()) == []


class TestTheBedBound:
    @staticmethod
    def _plant_bed(db: Any, count: int) -> None:
        db.collection(col.PLANT_INSTANCES).truncate()
        plants = [
            {"_key": f"pi_{n:04d}", "instance_id": f"pi_{n:04d}", "tenant_key": TENANT, "location_key": "bed"}
            for n in range(count)
        ]
        outcomes = db.collection(col.PLANT_INSTANCES).insert_many(plants)
        # ``insert_many`` reports a refused document inline: a half-planted bed would make the bound look kept
        assert not [outcome for outcome in outcomes if isinstance(outcome, Exception)]
        assert db.collection(col.PLANT_INSTANCES).count() == count

    def test_the_bounded_read_returns_at_most_the_limit(self, db) -> None:
        self._plant_bed(db, 5)

        assert plant_keys_standing_in(db, ["bed"], tenant_key=TENANT, limit=3) == ["pi_0000", "pi_0001", "pi_0002"]
        assert len(plant_keys_standing_in(db, ["bed"], tenant_key=TENANT)) == 5

    def test_a_whole_bed_dose_over_the_bound_is_refused_with_422_and_stores_nothing(self, db) -> None:
        self._plant_bed(db, MAX_PLANTS_PER_EVENT + 1)

        with pytest.raises(PlanError) as exc:
            _care(db).log(_amendment(), tenant_key=TENANT, user_key=USER, role=TenantRole.GROWER)

        assert (exc.value.status_code, exc.value.error_code) == (422, "care_event.too_many_plants")
        assert _feedings(db) == [] and list(db.collection(col.CARE_EVENTS).all()) == []
