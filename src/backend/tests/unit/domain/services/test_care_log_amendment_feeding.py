"""REQ-053 WP 10.12 (#2833) — a nutrient amendment writes ONE feeding event, whichever way it is recorded (W-007).

Measured before the change: ``POST /care-events`` with ``soil_amendment`` + ``compost`` stored the care event alone,
while the task completion of the same amendment also stored a ``feeding_event`` (``TaskCompletionEngine``, §12.1).
Both ways now build the document with :meth:`TaskCompletionEngine.feeding_document`; the care-log way stores it in
the same transaction as its line (``insert_with_feeding_event``), the completion keeps its own transaction and never
passes through :meth:`CareEventService.create` / :meth:`CareEventService.log`.

Pinned here, against the in-memory doubles: the direct way writes exactly one feeding event and points its line at
it; the completion writes exactly one and the care-log way none on top; both build the same document for the same
dose; the rules that keep a line without a specialist document (no quantity, no nutrient material, a direct
``feeding``) hold; and a replayed buffered write does not write a second feeding event. That each way stores exactly
one ``feeding_events`` row in a real database is ``tests/integration/test_care_log_amendment_feeding.py``.

Taking the entry back (security review of the first commit): the service decides which way a void or a correction
goes - a correction of a client's entry writes its own feeding event for the corrected dose, a line mirroring another
writer's document writes none, a server caller's ``origin`` never gets one, a whole bed beyond
``MAX_PLANTS_PER_EVENT`` is refused. That the document and its edges really go is the integration tier's (the fake
only records which key a void or a correction withdrew).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.common.enums import TaskCategory, TenantRole
from app.common.exceptions import PlanError, PlanValidationError
from app.domain.engines.dependency_resolver import DependencyResolver
from app.domain.engines.hst_validator import HSTValidator
from app.domain.engines.task_completion_engine import NUTRIENT_MATERIALS
from app.domain.models.care_event import (
    MAX_PLANTS_PER_EVENT,
    CareEvent,
    CareEventCorrection,
    CareEventInput,
    CareEventOrigin,
)
from app.domain.models.feeding_event import FeedingEvent
from app.domain.models.task_completion import CompletionActor, TaskCompletionDetails
from app.domain.services.care_event_service import CareEventService
from app.domain.services.task_service import TaskService
from tests.support.care_event_fakes import (
    FakeAttachmentRepo,
    FakeAttachmentService,
    FakeCareEventRepo,
    FakeFertilizers,
    FakeMemberships,
)
from tests.support.garden_plan_fakes import (
    OTHER_TENANT,
    SITE,
    TENANT,
    USER,
    FakePlanRepo,
    FakeSites,
    make_location,
    make_site,
    rect,
)
from tests.support.task_completion_fakes import FakeCompletionRepo, FakeHarvests, FakeTaskRepo, bed_task

GROWER = TenantRole.GROWER
ACTOR = CompletionActor(user_key=USER, role=GROWER)
WHEN = datetime.now(UTC).replace(microsecond=0) - timedelta(hours=1)
#: Fields that differ between two writes of the same dose by construction: the stamps and the task reference.
_PER_WRITE = {"created_at", "updated_at", "task_key"}


@pytest.fixture
def world():
    site = make_site()
    sites = FakeSites(site, make_site(tenant=OTHER_TENANT).model_copy(update={"key": "site_foreign"}))
    plan = FakePlanRepo(sites)
    plan.locations["bed"] = make_location("bed", name="Bed", geometry=rect(1, 1, 2, 1)).model_copy(
        update={"area_m2": 2.5}
    )
    plan.locations["bed_child"] = make_location("bed_child", name="Row", parent_location_key="bed")
    plan.locations["bed_other"] = make_location("bed_other", name="Other bed")
    plants = {
        "pi_here": (TENANT, "bed"),
        "pi_child": (TENANT, "bed_child"),
        "pi_elsewhere": (TENANT, "bed_other"),
        "pi_foreign": (OTHER_TENANT, "bed"),
    }
    care_repo = FakeCareEventRepo()
    care_repo.plants = dict(plants)
    care = CareEventService(
        care_repo, sites, FakeMemberships(), FakeFertilizers(), FakeAttachmentRepo(), FakeAttachmentService()
    )
    tasks = FakeTaskRepo(bed_task("t_amend", TaskCategory.SOIL_AMENDMENT))
    completion = FakeCompletionRepo(tasks, plants)
    service = TaskService(
        tasks,
        HSTValidator(),
        DependencyResolver(),
        completion=completion,
        care_events=care,
        harvests=FakeHarvests(),
        fertilizers=FakeFertilizers(),
    )
    return care, care_repo, service, completion


def amendment(**overrides) -> CareEventInput:
    data = {
        "location_key": "bed",
        "category": "soil_amendment",
        "summary": "Compost spread",
        "performed_at": WHEN,
        "material": "compost",
        "quantity": 3,
        "unit": "g_per_m2",
    }
    return CareEventInput(**{**data, **overrides})


def log(care: CareEventService, data: CareEventInput):
    return care.log(data, tenant_key=TENANT, user_key=USER, role=GROWER)


def comparable(document: dict) -> dict:
    return {key: value for key, value in document.items() if key not in _PER_WRITE}


class TestTheCareLogWay:
    @pytest.mark.parametrize("material", sorted(NUTRIENT_MATERIALS))
    def test_a_nutrient_amendment_writes_one_feeding_event_its_line_points_at(self, world, material):
        care, repo, *_ = world

        logged = log(care, amendment(material=material))

        (feeding,) = repo.feedings
        assert feeding.collection == "feeding_events"
        parsed = FeedingEvent.model_validate(feeding.document)
        assert (parsed.tenant_key, parsed.location_key, parsed.material) == (TENANT, "bed", material)
        assert (parsed.dose_quantity, parsed.dose_unit) == (3, "g_per_m2")
        # the area dose is the bed's total, as the care event computed it (3 g/m² x 2.5 m²)
        assert (parsed.quantity_total, parsed.quantity_total_unit) == (7.5, "g")
        assert parsed.task_key is None  # no task: the line is the record
        assert parsed.application_method.value == "top_dress"
        stored = repo.events[logged.view.event.key]
        assert stored.source_ref == {"collection": "feeding_events", "key": "fe_1"}
        assert stored.trigger == "manual"

    def test_a_whole_bed_dose_is_attributed_to_the_plants_standing_in_the_bed(self, world):
        care, repo, *_ = world

        log(care, amendment())

        parsed = FeedingEvent.model_validate(repo.feedings[0].document)
        # the bed and its children; never another bed's plant, never another tenant's plant in the same bed
        assert parsed.plant_keys == ["pi_child", "pi_here"]
        assert [frm for _, frm, _ in repo.feedings[0].edges_in] == [
            "plant_instances/pi_child",
            "plant_instances/pi_here",
        ]

    def test_named_plants_are_the_ones_the_dose_is_attributed_to(self, world):
        care, repo, *_ = world

        log(care, amendment(plant_keys=["pi_here"]))

        parsed = FeedingEvent.model_validate(repo.feedings[0].document)
        assert (parsed.plant_key, parsed.plant_keys) == ("pi_here", ["pi_here"])

    @pytest.mark.parametrize(
        "data",
        [
            pytest.param({"material": "sand"}, id="no-nutrient-material"),
            pytest.param({"material": "sulfur"}, id="sulfur-lowers-the-ph-feeds-nothing"),
            pytest.param({"quantity": None, "unit": None}, id="no-quantity"),
            pytest.param({"category": "mulching", "unit": "cm"}, id="compost-as-mulch"),
            pytest.param(
                {"category": "feeding", "material": None, "unit": "l", "summary": "Nettle tea"},
                id="a-direct-feeding-keeps-its-own-form",
            ),
        ],
    )
    def test_any_other_line_is_the_care_event_alone(self, world, data):
        care, repo, *_ = world

        logged = log(care, amendment(**data))

        assert repo.feedings == []
        assert repo.events[logged.view.event.key].source_ref is None

    def test_a_replayed_buffered_write_writes_no_second_feeding_event(self, world):
        care, repo, *_ = world
        body = amendment(client_event_id=uuid.uuid4())

        answers = [log(care, body) for _ in range(3)]

        assert [answer.replayed for answer in answers] == [False, True, True]
        assert len(repo.feedings) == 1
        assert len(repo.events) == 1

    def test_a_refused_entry_writes_no_feeding_event(self, world):
        care, repo, *_ = world

        with pytest.raises(PlanValidationError):  # 422 reference.not_found
            log(care, amendment(plant_keys=["pi_foreign"]))

        assert repo.feedings == [] and repo.events == {}


class TestTheTaskWay:
    def test_a_completed_amendment_task_writes_one_feeding_event_and_the_care_log_way_none(self, world):
        _, care_repo, service, completion = world

        service.complete_task(
            "t_amend",
            tenant_key=TENANT,
            details=TaskCompletionDetails(material="compost", quantity=3, unit="g_per_m2", performed_at=WHEN),
            actor=ACTOR,
        )

        (write,) = completion.completed
        assert write.domain is not None and write.domain.collection == "feeding_events"
        # the completion stores its line inside its own transaction: the care-log write path is not taken
        assert care_repo.feedings == [] and care_repo.events == {}

    def test_both_ways_build_the_same_feeding_event_for_the_same_dose(self, world):
        care, care_repo, service, completion = world

        log(care, amendment(summary="Bed 3"))
        service.complete_task(
            "t_amend",
            tenant_key=TENANT,
            details=TaskCompletionDetails(material="compost", quantity=3, unit="g_per_m2", performed_at=WHEN),
            actor=ACTOR,
        )

        by_log = care_repo.feedings[0]
        by_task = completion.completed[0].domain
        assert by_task is not None
        assert comparable(by_log.document) == comparable(by_task.document)
        assert by_log.edges_in == by_task.edges_in and by_log.edges_out == by_task.edges_out
        assert by_task.document["task_key"] == "t_amend" and "task_key" not in by_log.document


def correction(**overrides) -> CareEventCorrection:
    data = {
        "category": "soil_amendment",
        "summary": "Compost spread",
        "performed_at": WHEN,
        "material": "compost",
        "quantity": 3,
        "unit": "g_per_m2",
    }
    return CareEventCorrection(**{**data, **overrides})


def mirrored_line(repo: FakeCareEventRepo, trigger: str) -> CareEvent:
    """A compost line that points at a feeding event another writer stored (backfill, task, reconciliation)."""
    return repo.insert(
        CareEvent(
            tenant_key=TENANT,
            site_key=SITE,
            location_key="bed",
            category="soil_amendment",
            summary="Compost spread",
            performed_at=WHEN,
            material="compost",
            quantity=3,
            unit="g_per_m2",
            trigger=trigger,
            task_key="t_amend" if trigger == "task" else None,
            source_ref={"collection": "feeding_events", "key": "fe_elsewhere"},
            created_by=USER,
        ),
        tenant_key=TENANT,
    )


class TestTakingTheEntryBack:
    def test_undoing_a_logged_amendment_withdraws_its_feeding_event(self, world):
        care, repo, *_ = world
        logged = log(care, amendment())
        assert repo.live_feedings() == ["fe_1"]  # positive control: the dose counted before the undo

        care.void(logged.view.event.key, reason="undo", tenant_key=TENANT, user_key=USER, role=GROWER)

        assert repo.live_feedings() == []
        assert repo.events[logged.view.event.key].voided_at is not None

    def test_voiding_a_line_without_a_feeding_event_withdraws_nothing(self, world):
        care, repo, *_ = world
        logged = log(care, amendment(material="sand"))

        care.void(logged.view.event.key, reason="undo", tenant_key=TENANT, user_key=USER, role=GROWER)

        assert repo.withdrawn == []

    @pytest.mark.parametrize("trigger", ["backfill", "task", "system"])
    def test_voiding_a_line_that_mirrors_another_writers_document_leaves_it(self, world, trigger):
        care, repo, *_ = world
        line = mirrored_line(repo, trigger)

        care.void(line.key, reason="wrong bed", tenant_key=TENANT, user_key=USER, role=TenantRole.LEAD)

        assert repo.withdrawn == []


class TestCorrectingTheEntry:
    def test_a_corrected_dose_replaces_the_feeding_event(self, world):
        care, repo, *_ = world
        logged = log(care, amendment())

        view = care.supersede(
            logged.view.event.key, correction(quantity=5), tenant_key=TENANT, user_key=USER, role=GROWER
        )

        assert repo.live_feedings() == ["fe_2"]
        assert FeedingEvent.model_validate(repo.feedings[1].document).dose_quantity == 5
        assert repo.events[view.event.key].source_ref == {"collection": "feeding_events", "key": "fe_2"}

    def test_a_correction_that_is_no_nutrient_amendment_keeps_no_feeding_event(self, world):
        care, repo, *_ = world
        logged = log(care, amendment())

        view = care.supersede(
            logged.view.event.key,
            correction(category="mulching", unit="cm", quantity=5),
            tenant_key=TENANT,
            user_key=USER,
            role=GROWER,
        )

        assert repo.live_feedings() == []
        assert len(repo.feedings) == 1  # nothing new written
        assert repo.events[view.event.key].source_ref is None

    def test_a_correction_that_turns_a_plain_line_into_an_amendment_writes_one(self, world):
        care, repo, *_ = world
        logged = log(care, amendment(material="sand"))

        view = care.supersede(logged.view.event.key, correction(), tenant_key=TENANT, user_key=USER, role=GROWER)

        assert repo.live_feedings() == ["fe_1"]
        assert repo.events[view.event.key].source_ref == {"collection": "feeding_events", "key": "fe_1"}

    def test_correcting_a_line_that_mirrors_another_writers_document_writes_none(self, world):
        care, repo, *_ = world
        line = mirrored_line(repo, "backfill")

        view = care.supersede(line.key, correction(quantity=5), tenant_key=TENANT, user_key=USER, role=TenantRole.LEAD)

        assert repo.feedings == [] and repo.withdrawn == []
        assert repo.events[view.event.key].source_ref is None


class TestAServerCaller:
    def test_an_origin_keeps_its_own_source_ref_and_writes_no_feeding_event(self, world):
        care, repo, *_ = world
        reference = {"collection": "feeding_events", "key": "fe_written_by_the_caller"}

        view = care.create(
            amendment(),
            tenant_key=TENANT,
            user_key=USER,
            role=GROWER,
            origin=CareEventOrigin(trigger="system", source_ref=reference),
        )

        assert repo.feedings == []
        assert repo.events[view.event.key].source_ref == reference


class TestTheBedBound:
    def _fill(self, repo: FakeCareEventRepo, count: int) -> None:
        repo.plants = {f"pi_{n:04d}": (TENANT, "bed") for n in range(count)}

    def test_a_bed_with_more_plants_than_one_event_names_is_refused_with_422(self, world):
        care, repo, *_ = world
        self._fill(repo, MAX_PLANTS_PER_EVENT + 1)

        with pytest.raises(PlanError) as exc:
            log(care, amendment())

        assert (exc.value.status_code, exc.value.error_code) == (422, "care_event.too_many_plants")
        assert exc.value.details[0]["field"] == "plant_keys"
        assert exc.value.details[0]["limit"] == MAX_PLANTS_PER_EVENT
        assert repo.feedings == [] and repo.events == {}
        # the read is bounded: one key more than the cap is enough to decide
        assert repo.standing_limits == [MAX_PLANTS_PER_EVENT + 1]

    def test_a_bed_with_exactly_the_bound_is_attributed_to_every_plant(self, world):
        care, repo, *_ = world
        self._fill(repo, MAX_PLANTS_PER_EVENT)

        log(care, amendment())

        assert len(FeedingEvent.model_validate(repo.feedings[0].document).plant_keys) == MAX_PLANTS_PER_EVENT

    def test_a_correction_to_an_oversized_bed_is_refused_and_keeps_the_old_dose(self, world):
        care, repo, *_ = world
        logged = log(care, amendment())
        self._fill(repo, MAX_PLANTS_PER_EVENT + 1)

        with pytest.raises(PlanError):
            care.supersede(logged.view.event.key, correction(quantity=5), tenant_key=TENANT, user_key=USER, role=GROWER)

        assert repo.live_feedings() == ["fe_1"]
        assert repo.events[logged.view.event.key].superseded_by_key is None
