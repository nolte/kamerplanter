"""REQ-053 WP 4.3 (#2413) — the atomic task completion against a real ArangoDB (GP-FR-083, GP-ACC-024, GP-FR-149).

What no double can decide, measured here: that the task, the care event, the specialist document and every edge are
**one commit** — a failure anywhere (a duplicate key in the document, a second task of the batch that is no longer
open) leaves the task pending and writes no event, no document, no edge; that a task of another tenant answers like an
absent one and is left untouched; and that the undo (reopen + void) is one commit as well.

Every "nothing is there" assertion is paired with the positive control — the tenant's own row read through the same
path — so an empty answer cannot be a reader that sees nothing at all.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from arango import ArangoClient

from app.common.exceptions import DuplicateError, NotFoundError, PlanError, ValidationError
from app.data_access.arango import collections as col
from app.data_access.arango.task_completion_repository import ArangoTaskCompletionRepository
from app.data_access.arango.task_repository import ArangoTaskRepository
from app.domain.models.care_event import CareEvent
from app.domain.models.task_completion import CompletionWrite, DomainDocument, UndoWrite
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = pytest.mark.usefixtures("arango_db")

TEST_DATABASE = run_database_name("task_completion_repository")
A, B = "ten_a", "ten_b"
USER = "u_sabine"
NOW = datetime(2026, 10, 18, 12, 0, tzinfo=UTC)

_DOCUMENTS = (
    col.TASKS,
    col.CARE_EVENTS,
    col.PLANT_INSTANCES,
    col.WATERING_EVENTS,
    col.FEEDING_EVENTS,
    col.HARVEST_BATCHES,
    col.FERTILIZERS,
    col.LOCATIONS,
    col.QUALITY_ASSESSMENTS,
    col.YIELD_METRICS,
    col.POST_HARVEST_BATCHES,
)
_EDGES = (
    col.CARE_EVENT_AT,
    col.CARE_EVENT_FOR,
    col.TASK_LOGGED_AS,
    col.WATERED_PLANT,
    col.FED_BY,
    col.FEEDING_USED,
    col.HARVESTED_AS,
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
def db(database):
    for entry in database.collections():
        if not entry["system"]:
            database.collection(entry["name"]).truncate()
    for key, tenant, status in (
        ("t1", A, "pending"),
        ("t2", A, "pending"),
        ("t_done", A, "completed"),
        ("t_b", B, "pending"),
    ):
        database.collection(col.TASKS).insert(
            {"_key": key, "tenant_key": tenant, "name": key, "status": status, "category": "watering"}
        )
    for key, tenant, location in (("pi_1", A, "bed"), ("pi_2", A, "bed"), ("pi_gone", A, "bed"), ("pi_b", B, "bed_b")):
        doc = {"_key": key, "tenant_key": tenant, "location_key": location}
        if key == "pi_gone":
            doc["removed_on"] = "2026-01-01"
        database.collection(col.PLANT_INSTANCES).insert(doc)
    return database


@pytest.fixture
def repo(db) -> ArangoTaskCompletionRepository:
    return ArangoTaskCompletionRepository(db)


def event(task_key: str = "t1", tenant: str = A, **overrides) -> CareEvent:
    data = {
        "tenant_key": tenant,
        "site_key": "site_a",
        "location_key": "bed",
        "category": "watering",
        "summary": "Watered",
        "performed_at": NOW - timedelta(hours=1),
        "performed_by_user_key": USER,
        "created_by": USER,
        "trigger": "task",
        "task_key": task_key,
        **overrides,
    }
    return CareEvent(**data)


def watering_document(**overrides) -> DomainDocument:
    return DomainDocument(
        collection=col.WATERING_EVENTS,
        document={"tenant_key": A, "volume_liters": 5.0, "plant_keys": ["pi_1", "pi_2"], "task_key": "t1", **overrides},
        edges_out=tuple((col.WATERED_PLANT, f"plant_instances/{key}", {}) for key in ("pi_1", "pi_2")),
    )


def completion(task_key: str = "t1", **overrides) -> CompletionWrite:
    data = {
        "task_key": task_key,
        "task_patch": {"status": "completed", "completed_at": NOW.isoformat(), "completion_notes": "done"},
        "event": event(task_key),
        "domain": None,
    }
    return CompletionWrite(**{**data, **overrides})


def count(db, collection: str) -> int:
    return len(list(db.collection(collection).all()))


def nothing_was_written(db) -> None:
    for name in (
        col.CARE_EVENTS,
        col.WATERING_EVENTS,
        col.CARE_EVENT_AT,
        col.CARE_EVENT_FOR,
        col.TASK_LOGGED_AS,
        col.WATERED_PLANT,
    ):
        assert count(db, name) == 0, name


class TestComplete:
    def test_the_task_the_event_the_document_and_every_edge_are_one_commit(self, db, repo) -> None:
        write = completion(event=event(plant_keys=["pi_1"], quantity=5, unit="l"), domain=watering_document())

        (done,) = repo.complete([write], tenant_key=A)

        task = db.collection(col.TASKS).get("t1")
        assert (task["status"], task["completion_notes"], task["completed_at"]) == (
            "completed",
            "done",
            NOW.isoformat(),
        )
        assert "updated_at" in task
        (stored_event,) = list(db.collection(col.CARE_EVENTS).all())
        (watering,) = list(db.collection(col.WATERING_EVENTS).all())
        assert done.event_key == stored_event["_key"]
        assert done.domain_ref == {"collection": "watering_events", "key": watering["_key"]}
        assert stored_event["source_ref"] == done.domain_ref  # the event points at the document it is the line of
        assert stored_event["trigger"] == "task" and stored_event["task_key"] == "t1"
        assert sorted(e["_to"] for e in db.collection(col.WATERED_PLANT).all()) == [
            "plant_instances/pi_1",
            "plant_instances/pi_2",
        ]
        assert all(e["_from"] == f"watering_events/{watering['_key']}" for e in db.collection(col.WATERED_PLANT).all())
        (logged,) = list(db.collection(col.TASK_LOGGED_AS).all())
        assert (logged["_from"], logged["_to"]) == ("tasks/t1", f"care_events/{stored_event['_key']}")
        (at,) = list(db.collection(col.CARE_EVENT_AT).all())
        assert at["_to"] == "locations/bed"
        assert [e["_to"] for e in db.collection(col.CARE_EVENT_FOR).all()] == ["plant_instances/pi_1"]

    def test_inbound_and_attributed_edges_of_a_feeding_are_written(self, db, repo) -> None:
        feeding = DomainDocument(
            collection=col.FEEDING_EVENTS,
            document={"tenant_key": A, "plant_key": "pi_1", "volume_applied_liters": 5.0},
            edges_out=((col.FEEDING_USED, "fertilizers/fert_x", {"ml_applied": 5000.0}),),
            edges_in=((col.FED_BY, "plant_instances/pi_1", {}),),
        )

        (done,) = repo.complete([completion(domain=feeding)], tenant_key=A)

        (fed,) = list(db.collection(col.FED_BY).all())
        assert (fed["_from"], fed["_to"]) == ("plant_instances/pi_1", f"feeding_events/{done.domain_ref['key']}")
        (used,) = list(db.collection(col.FEEDING_USED).all())
        assert (used["_from"], used["_to"], used["ml_applied"]) == (
            f"feeding_events/{done.domain_ref['key']}",
            "fertilizers/fert_x",
            5000.0,
        )

    def test_a_task_without_a_bed_closes_alone(self, db, repo) -> None:
        (done,) = repo.complete([completion(event=None)], tenant_key=A)

        assert db.collection(col.TASKS).get("t1")["status"] == "completed"
        assert done.event_key is None
        nothing_was_written(db)

    def test_a_failure_in_the_specialist_document_leaves_the_task_pending(self, db, repo) -> None:
        # GP-ACC-024: an error at the feeding_event → the task stays pending, no care_event.
        db.collection(col.WATERING_EVENTS).insert({"_key": "dup", "tenant_key": A})
        before = count(db, col.WATERING_EVENTS)

        with pytest.raises(DuplicateError):
            repo.complete([completion(domain=watering_document(_key="dup"))], tenant_key=A)

        assert db.collection(col.TASKS).get("t1")["status"] == "pending"
        assert count(db, col.WATERING_EVENTS) == before
        for name in (col.CARE_EVENTS, col.CARE_EVENT_AT, col.TASK_LOGGED_AS, col.WATERED_PLANT):
            assert count(db, name) == 0, name

    def test_a_batch_is_all_or_nothing(self, db, repo) -> None:
        with pytest.raises(ValidationError):
            repo.complete([completion("t1"), completion("t_done")], tenant_key=A)

        assert db.collection(col.TASKS).get("t1")["status"] == "pending"  # the first task was rolled back
        nothing_was_written(db)

    def test_a_batch_commits_every_task_with_its_event(self, db, repo) -> None:
        done = repo.complete([completion("t1"), completion("t2")], tenant_key=A)

        assert [d.task_key for d in done] == ["t1", "t2"]
        assert {db.collection(col.TASKS).get(k)["status"] for k in ("t1", "t2")} == {"completed"}
        assert count(db, col.CARE_EVENTS) == 2 and count(db, col.TASK_LOGGED_AS) == 2

    def test_a_task_that_is_no_longer_open_is_refused_inside_the_transaction(self, db, repo) -> None:
        # The service judged "pending" before it opened the transaction; a concurrent completion won the race.
        with pytest.raises(ValidationError):
            repo.complete([completion("t_done")], tenant_key=A)

        nothing_was_written(db)

    def test_another_tenants_task_is_absent_and_untouched(self, db, repo) -> None:
        with pytest.raises(NotFoundError):
            repo.complete([completion("t_b")], tenant_key=A)  # t_b is tenant B's
        with pytest.raises(NotFoundError):
            repo.complete([completion("nope")], tenant_key=A)

        assert db.collection(col.TASKS).get("t_b")["status"] == "pending"
        nothing_was_written(db)
        repo.complete([completion("t1")], tenant_key=A)  # the positive control: the own task completes
        assert db.collection(col.TASKS).get("t1")["status"] == "completed"

    def test_an_event_of_another_tenant_cannot_be_written_under_this_one(self, db, repo) -> None:
        with pytest.raises(ValueError, match="another tenant"):
            repo.complete([completion("t1", event=event("t1", tenant=B))], tenant_key=A)

        assert db.collection(col.TASKS).get("t1")["status"] == "pending"
        nothing_was_written(db)

    def test_an_empty_tenant_is_refused(self, repo) -> None:
        with pytest.raises(ValueError, match="tenant_key"):
            repo.complete([completion()], tenant_key="")


class TestUndo:
    def done(self, db, repo, task_key: str = "t1") -> str:
        (done,) = repo.complete([completion(task_key)], tenant_key=A)
        return done.event_key or ""

    def write(self, event_key: str | None, task_key: str = "t1") -> UndoWrite:
        return UndoWrite(
            task_key=task_key,
            task_patch={
                "status": "pending",
                "reopened_at": NOW.isoformat(),
                "completed_at": None,
                "completion_notes": None,
            },
            event_key=event_key,
            voided_by=USER,
            voided_at=NOW,
        )

    def test_the_task_is_reopened_and_the_event_voided_in_one_commit(self, db, repo) -> None:
        event_key = self.done(db, repo)

        repo.reopen(self.write(event_key), tenant_key=A)

        task = db.collection(col.TASKS).get("t1")
        assert task["status"] == "pending" and "completed_at" not in task and "completion_notes" not in task
        voided = db.collection(col.CARE_EVENTS).get(event_key)
        assert (voided["voided_by"], voided["void_reason"]) == (USER, "undo")
        assert voided["voided_at"] == NOW.isoformat()
        assert repo.task_event("t1", tenant_key=A) is None  # a voided line is no head any more

    def test_an_event_that_is_closed_meanwhile_aborts_the_reopen(self, db, repo) -> None:
        event_key = self.done(db, repo)
        db.collection(col.CARE_EVENTS).update({"_key": event_key, "voided_at": NOW.isoformat()})

        with pytest.raises(PlanError) as exc:
            repo.reopen(self.write(event_key), tenant_key=A)

        assert exc.value.details[0]["code"] == "care_event.sequence"
        assert db.collection(col.TASKS).get("t1")["status"] == "completed"  # the task was not reopened either

    def test_a_task_that_logged_nothing_is_just_reopened(self, db, repo) -> None:
        repo.complete([completion(event=None)], tenant_key=A)

        repo.reopen(self.write(None), tenant_key=A)

        assert db.collection(col.TASKS).get("t1")["status"] == "pending"

    def test_a_task_that_is_not_closed_cannot_be_reopened(self, db, repo) -> None:
        with pytest.raises(ValidationError):
            repo.reopen(self.write(None), tenant_key=A)

    def test_another_tenants_task_and_event_are_out_of_reach(self, db, repo) -> None:
        foreign_event = db.collection(col.CARE_EVENTS).insert(
            {"tenant_key": B, "task_key": "t1", "category": "watering", "location_key": "bed_b"}
        )["_key"]
        self.done(db, repo)

        with pytest.raises(NotFoundError):
            repo.reopen(self.write(foreign_event), tenant_key=A)  # the event is B's: not found under A
        db.collection(col.TASKS).update({"_key": "t_b", "status": "completed"})
        with pytest.raises(NotFoundError):
            repo.reopen(self.write(None, "t_b"), tenant_key=A)

        assert db.collection(col.TASKS).get("t1")["status"] == "completed"
        assert db.collection(col.CARE_EVENTS).get(foreign_event).get("voided_at") is None


class TestWithdrawal:
    """The undo is the inverse of the completion: the specialist document goes with the care line (GP-FR-149)."""

    @staticmethod
    def completed(repo, domain: DomainDocument, task_key: str = "t1") -> tuple[str, dict[str, str]]:
        (done,) = repo.complete([completion(task_key, domain=domain)], tenant_key=A)
        return done.event_key or "", done.domain_ref or {}

    @staticmethod
    def undo(event_key: str, task_key: str = "t1") -> UndoWrite:
        return TestUndo().write(event_key, task_key)

    def test_the_undo_removes_the_watering_event_and_its_edges(self, db, repo) -> None:
        event_key, ref = self.completed(repo, watering_document())
        assert count(db, col.WATERED_PLANT) == 2

        repo.reopen(self.undo(event_key), tenant_key=A)

        assert db.collection(col.WATERING_EVENTS).get(ref["key"]) is None
        assert count(db, col.WATERED_PLANT) == 0
        assert db.collection(col.CARE_EVENTS).get(event_key)["void_reason"] == "undo"  # the voided line stays
        assert db.collection(col.TASKS).get("t1")["status"] == "pending"

    def test_the_undo_removes_a_feeding_event_with_both_kinds_of_edge(self, db, repo) -> None:
        feeding = DomainDocument(
            collection=col.FEEDING_EVENTS,
            document={"tenant_key": A, "plant_key": "pi_1", "volume_applied_liters": 5.0},
            edges_out=((col.FEEDING_USED, "fertilizers/fert_x", {"ml_applied": 5000.0}),),
            edges_in=((col.FED_BY, "plant_instances/pi_1", {}),),
        )
        event_key, ref = self.completed(repo, feeding)

        repo.reopen(self.undo(event_key), tenant_key=A)

        assert db.collection(col.FEEDING_EVENTS).get(ref["key"]) is None
        assert count(db, col.FEEDING_USED) == 0 and count(db, col.FED_BY) == 0

    def harvest(self) -> DomainDocument:
        return DomainDocument(
            collection=col.HARVEST_BATCHES,
            document={"tenant_key": A, "plant_key": "pi_1", "batch_id": "HARVEST-1"},
            edges_in=((col.HARVESTED_AS, "plant_instances/pi_1", {}),),
        )

    def test_the_undo_removes_a_bare_harvest_batch(self, db, repo) -> None:
        event_key, ref = self.completed(repo, self.harvest())

        repo.reopen(self.undo(event_key), tenant_key=A)

        assert db.collection(col.HARVEST_BATCHES).get(ref["key"]) is None
        assert count(db, col.HARVESTED_AS) == 0

    def test_a_harvest_batch_with_follow_up_records_blocks_the_undo_and_nothing_changes(self, db, repo) -> None:
        event_key, ref = self.completed(repo, self.harvest())
        db.collection(col.QUALITY_ASSESSMENTS).insert({"batch_key": ref["key"]})

        with pytest.raises(PlanError) as exc:
            repo.reopen(self.undo(event_key), tenant_key=A)

        assert exc.value.details[0]["code"] == "task.undo_blocked"
        assert db.collection(col.HARVEST_BATCHES).get(ref["key"]) is not None
        assert db.collection(col.TASKS).get("t1")["status"] == "completed"
        assert db.collection(col.CARE_EVENTS).get(event_key).get("voided_at") is None

    def test_a_document_of_another_tenant_is_never_removed(self, db, repo) -> None:
        event_key, ref = self.completed(repo, watering_document())
        db.collection(col.WATERING_EVENTS).update({"_key": ref["key"], "tenant_key": B})  # the pointer lies

        repo.reopen(self.undo(event_key), tenant_key=A)

        assert db.collection(col.WATERING_EVENTS).get(ref["key"]) is not None
        assert db.collection(col.TASKS).get("t1")["status"] == "pending"

    def test_completing_again_after_a_plain_reopen_replaces_the_earlier_line_and_document(self, db, repo) -> None:
        first_event, first_ref = self.completed(repo, watering_document())
        db.collection(col.TASKS).update({"_key": "t1", "status": "pending"})  # a plain reopen: the line stays

        (done,) = repo.complete(
            [completion(domain=watering_document(volume_liters=7.0), replaces_event_key=first_event)], tenant_key=A
        )

        first = db.collection(col.CARE_EVENTS).get(first_event)
        assert (first["void_reason"], first["voided_by"]) == ("reopened", USER)
        assert db.collection(col.WATERING_EVENTS).get(first_ref["key"]) is None
        assert db.collection(col.WATERING_EVENTS).get(done.domain_ref["key"])["volume_liters"] == 7.0
        assert db.collection(col.CARE_EVENTS).get(done.event_key).get("voided_at") is None
        assert count(db, col.WATERED_PLANT) == 2  # only the second document's edges are left
        assert repo.task_event("t1", tenant_key=A).key == done.event_key  # one open line per task

    def test_without_the_replacement_flag_the_earlier_line_is_left_alone(self, db, repo) -> None:
        # The service sets the flag only for the line's author or a lead; any other completion adds a line.
        first_event, first_ref = self.completed(repo, watering_document())
        db.collection(col.TASKS).update({"_key": "t1", "status": "pending"})

        repo.complete([completion(domain=watering_document())], tenant_key=A)

        assert db.collection(col.CARE_EVENTS).get(first_event).get("voided_at") is None
        assert db.collection(col.WATERING_EVENTS).get(first_ref["key"]) is not None

    def test_a_line_that_was_closed_meanwhile_is_not_touched_twice(self, db, repo) -> None:
        first_event, _ = self.completed(repo, watering_document())
        db.collection(col.CARE_EVENTS).update({"_key": first_event, "voided_at": NOW.isoformat(), "voided_by": "u_x"})
        db.collection(col.TASKS).update({"_key": "t1", "status": "pending"})

        repo.complete([completion(replaces_event_key=first_event)], tenant_key=A)

        assert db.collection(col.CARE_EVENTS).get(first_event)["voided_by"] == "u_x"  # untouched
        assert db.collection(col.TASKS).get("t1")["status"] == "completed"

    def test_a_harvest_batch_with_follow_up_records_blocks_the_re_completion(self, db, repo) -> None:
        first_event, first_ref = self.completed(repo, self.harvest())
        db.collection(col.YIELD_METRICS).insert({"batch_key": first_ref["key"]})
        db.collection(col.TASKS).update({"_key": "t1", "status": "pending"})

        with pytest.raises(PlanError) as exc:
            repo.complete([completion(domain=self.harvest(), replaces_event_key=first_event)], tenant_key=A)

        assert exc.value.details[0]["code"] == "task.undo_blocked"
        assert db.collection(col.HARVEST_BATCHES).get(first_ref["key"]) is not None
        assert db.collection(col.CARE_EVENTS).get(first_event).get("voided_at") is None
        assert count(db, col.HARVEST_BATCHES) == 1  # no second batch
        assert db.collection(col.TASKS).get("t1")["status"] == "pending"


class TestReads:
    def test_task_event_is_the_open_head_of_the_tenants_chain(self, db, repo) -> None:
        first = self.log(repo)
        head = repo.task_event("t1", tenant_key=A)
        assert head is not None and head.key == first
        assert repo.task_event("t1", tenant_key=B) is None  # the positive control above, the foreign tenant below
        assert repo.task_event("t2", tenant_key=A) is None

    @staticmethod
    def log(repo) -> str:
        (done,) = repo.complete([completion("t1")], tenant_key=A)
        return done.event_key or ""

    def test_plants_of_a_bed_are_the_tenants_and_not_removed(self, repo) -> None:
        assert repo.plants_in_locations(["bed"], tenant_key=A) == ["pi_1", "pi_2"]  # pi_gone is removed
        assert repo.plants_in_locations(["bed"], tenant_key=B) == []
        assert repo.plants_in_locations(["bed_b"], tenant_key=B) == ["pi_b"]
        assert repo.plants_in_locations([], tenant_key=A) == []

    def test_a_plants_location_is_visible_to_its_tenant_only(self, repo) -> None:
        assert repo.plant_location("pi_1", tenant_key=A) == "bed"
        assert repo.plant_location("pi_1", tenant_key=B) is None
        assert repo.plant_location("nope", tenant_key=A) is None


class TestParkedRecurrence:
    def test_the_parked_value_goes_and_the_rest_of_the_task_stays(self, db) -> None:
        db.collection(col.TASKS).update(
            {"_key": "t1", "recurrence_rule": "FREQ=DAILY", "recurrence_rule_unconvertible": "0 8 * * 1#2"}
        )

        ArangoTaskRepository(db).clear_parked_recurrence("t1")

        task = db.collection(col.TASKS).get("t1")
        assert "recurrence_rule_unconvertible" not in task
        assert (task["recurrence_rule"], task["name"], task["status"]) == ("FREQ=DAILY", "t1", "pending")

    def test_a_task_without_a_parked_value_is_not_an_error(self, db) -> None:
        ArangoTaskRepository(db).clear_parked_recurrence("t2")

        assert db.collection(col.TASKS).get("t2")["status"] == "pending"
