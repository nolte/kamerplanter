"""REQ-053 WP 9.3 (#2743) — a replayed buffered write never creates a second object, against a real ArangoDB.

A client that buffers a write offline sends a ``client_event_id`` with every attempt. What no double can decide is
measured here, for each of the three write paths (care event, task completion — single and batch —, upload):

* **replay 3x → one row**: the same id three times stores one object; the first answer is a write, the next two
  are replays of the same object;
* **two attempts at once → one object**: two threads with the same id race on the real unique index
  ``(tenant_key, client_event_id)`` (v0106); exactly one object exists afterwards, and every attempt that answers
  at all answers that object (the loser of a 1200 may answer the retryable ``WRITE_CONFLICT`` instead);
* the same id with another request is 409 ``client_event.payload_mismatch`` and stores nothing;
* the id is unique **per tenant**: another tenant's write with the same id is its own object.

Every "one row" count is read through the id itself, and paired with the positive control that the row is there.
"""

from __future__ import annotations

import asyncio
import io
import threading
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import patch

import pytest
from arango import ArangoClient
from PIL import Image

from app.common.enums import AttachmentCategory, TenantRole
from app.common.exceptions import (
    ClientEventMismatchError,
    DuplicateError,
    TaskAlreadyClosedError,
    TaskMissingError,
    WriteConflictError,
)
from app.config.settings import Settings
from app.data_access.arango import collections as col
from app.data_access.arango.attachment_repository import ArangoAttachmentRepository
from app.data_access.arango.care_event_repository import ArangoCareEventRepository
from app.data_access.arango.task_completion_repository import ArangoTaskCompletionRepository
from app.data_access.arango.task_repository import ArangoTaskRepository
from app.data_access.storage.local_fs_adapter import LocalFsStorageAdapter
from app.domain.engines.dependency_resolver import DependencyResolver
from app.domain.engines.hst_validator import HSTValidator
from app.domain.models.care_event import CareEvent, CareEventInput
from app.domain.models.client_event import batch_item_client_event_id
from app.domain.models.task_completion import CompletionActor, TaskCompletionDetails
from app.domain.services.attachment_service import AttachmentService
from app.domain.services.care_event_service import CareEventService
from app.domain.services.task_service import TaskService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name
from tests.support.care_event_fakes import FakeAttachmentRepo, FakeAttachmentService, FakeFertilizers, FakeMemberships
from tests.support.garden_plan_fakes import (
    OTHER_TENANT,
    TENANT,
    USER,
    FakePlanRepo,
    FakeSites,
    make_location,
    make_site,
)
from tests.support.task_completion_fakes import FakeHarvests

pytestmark = pytest.mark.usefixtures("arango_db")

TEST_DATABASE = run_database_name("client_event_idempotency")
ACTOR = CompletionActor(user_key=USER, role=TenantRole.GROWER)


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    # The production collections *and indexes*: the unique client-event index is what is under test.
    col.ensure_collections(db)
    yield db
    system.delete_database(TEST_DATABASE)


def _handle() -> Any:
    """A database handle of its own (one HTTP session per thread)."""
    return ArangoClient(hosts=ARANGO_URL).db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)


@pytest.fixture
def db(database):
    for name in (col.CARE_EVENTS, col.TASKS, col.ATTACHMENTS, col.CARE_EVENT_AT, col.TASK_LOGGED_AS):
        database.collection(name).truncate()
    for key in ("t1", "t2", "t3"):
        database.collection(col.TASKS).insert(
            {
                "_key": key,
                "tenant_key": TENANT,
                "name": "Water bed 3",
                "category": "watering",
                "status": "pending",
                "entity_type": "location",
                "entity_key": "bed",
                "photo_refs": [],
            }
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


def _rows(db: Any, collection: str, field: str, value: str) -> int:
    cursor = db.aql.execute(
        "FOR d IN @@c FILTER d[@field] == @value COLLECT WITH COUNT INTO n RETURN n",
        bind_vars={"@c": collection, "field": field, "value": value},
    )
    return int(next(iter(cursor), 0))


def _note(client_event_id: uuid.UUID, **overrides: Any) -> CareEventInput:
    data: dict[str, Any] = {
        "location_key": "bed",
        "category": "note",
        "summary": "Snails on the lettuce",
        "performed_at": datetime.now(UTC) - timedelta(hours=2),
        "client_event_id": client_event_id,
        **overrides,
    }
    return CareEventInput(**data)


def _race(attempt: Callable[[], Any]) -> list[Any]:
    """Run ``attempt`` in two threads released at once; each result is the return value or the exception."""
    barrier = threading.Barrier(2)
    results: list[Any] = [None, None]

    def run(index: int) -> None:
        barrier.wait()
        try:
            results[index] = attempt()
        except Exception as exc:  # noqa: BLE001 - the test inspects what each attempt answered
            results[index] = exc

    threads = [threading.Thread(target=run, args=(index,)) for index in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=60)
    return results


# ── POST /care-events ────────────────────────────────────────────────────────


class TestCareEvent:
    def test_a_replay_three_times_stores_one_row(self, db) -> None:
        service = _care(db)
        client_id = uuid.uuid4()
        body = _note(client_id)

        answers = [service.log(body, tenant_key=TENANT, user_key=USER, role=TenantRole.GROWER) for _ in range(3)]

        assert [answer.replayed for answer in answers] == [False, True, True]
        assert len({answer.view.event.key for answer in answers}) == 1
        assert _rows(db, col.CARE_EVENTS, "client_event_id", str(client_id)) == 1

    def test_two_attempts_at_once_store_one_row(self, db) -> None:
        client_id = uuid.uuid4()
        body = _note(client_id)

        results = _race(lambda: _care(_handle()).log(body, tenant_key=TENANT, user_key=USER, role=TenantRole.GROWER))

        answered = [result for result in results if not isinstance(result, Exception)]
        assert answered, results  # at least one attempt wrote the event
        assert all(isinstance(result, WriteConflictError) for result in results if isinstance(result, Exception))
        assert len({answer.view.event.key for answer in answered}) == 1
        assert _rows(db, col.CARE_EVENTS, "client_event_id", str(client_id)) == 1

    def test_the_same_id_with_another_body_is_refused_and_stores_nothing(self, db) -> None:
        service = _care(db)
        client_id = uuid.uuid4()
        service.log(_note(client_id), tenant_key=TENANT, user_key=USER, role=TenantRole.GROWER)

        with pytest.raises(ClientEventMismatchError):
            service.log(_note(client_id, summary="Slugs"), tenant_key=TENANT, user_key=USER, role=TenantRole.GROWER)

        assert _rows(db, col.CARE_EVENTS, "client_event_id", str(client_id)) == 1

    def test_the_index_refuses_a_second_row_under_one_id(self, db) -> None:
        # The storage half on its own: two inserts under one id, past any read the service makes first.
        repo = ArangoCareEventRepository(db)
        event = CareEvent(
            tenant_key=TENANT,
            site_key="site_1",
            location_key="bed",
            category="note",
            summary="x",
            performed_at=datetime.now(UTC),
            client_event_id="ce-fixed",
        )
        repo.insert(event, tenant_key=TENANT)

        with pytest.raises(DuplicateError):
            repo.insert(event, tenant_key=TENANT)
        repo.insert(event.model_copy(update={"tenant_key": OTHER_TENANT}), tenant_key=OTHER_TENANT)  # per tenant

        assert _rows(db, col.CARE_EVENTS, "client_event_id", "ce-fixed") == 2


# ── POST /tasks/{key}/complete and tasks/batch/status ────────────────────────


class TestTaskCompletion:
    def test_a_replay_three_times_closes_once_and_logs_one_row(self, db) -> None:
        service = _tasks(db)
        client_id = uuid.uuid4()

        answers = [
            service.complete_task_once(
                "t1",
                tenant_key=TENANT,
                client_event_id=client_id,
                details=TaskCompletionDetails(),
                actor=ACTOR,
            )
            for _ in range(3)
        ]

        assert [answer.replayed for answer in answers] == [False, True, True]
        assert {answer.task.status for answer in answers} == {"completed"}
        assert _rows(db, col.TASKS, "completion_client_event_id", str(client_id)) == 1
        assert _rows(db, col.CARE_EVENTS, "task_key", "t1") == 1

    def test_two_attempts_at_once_close_once(self, db) -> None:
        client_id = uuid.uuid4()

        results = _race(
            lambda: _tasks(_handle()).complete_task_once(
                "t1", tenant_key=TENANT, client_event_id=client_id, details=TaskCompletionDetails(), actor=ACTOR
            )
        )

        answered = [result for result in results if not isinstance(result, Exception)]
        assert answered, results
        assert all(isinstance(result, WriteConflictError) for result in results if isinstance(result, Exception))
        assert {answer.task.key for answer in answered} == {"t1"}
        assert _rows(db, col.CARE_EVENTS, "task_key", "t1") == 1
        assert _rows(db, col.TASKS, "completion_client_event_id", str(client_id)) == 1

    def test_a_task_closed_by_someone_else_is_already_closed(self, db) -> None:
        service = _tasks(db)
        service.complete_task_once(
            "t1", tenant_key=TENANT, client_event_id=uuid.uuid4(), details=TaskCompletionDetails(), actor=ACTOR
        )

        with pytest.raises(TaskAlreadyClosedError):
            service.complete_task_once(
                "t1", tenant_key=TENANT, client_event_id=uuid.uuid4(), details=TaskCompletionDetails(), actor=ACTOR
            )
        assert _rows(db, col.CARE_EVENTS, "task_key", "t1") == 1

    def test_a_deleted_task_is_missing(self, db) -> None:
        db.collection(col.TASKS).delete("t3")

        with pytest.raises(TaskMissingError):
            _tasks(db).complete_task_once(
                "t3", tenant_key=TENANT, client_event_id=uuid.uuid4(), details=TaskCompletionDetails(), actor=ACTOR
            )

    def test_the_id_of_one_task_cannot_close_another(self, db) -> None:
        service = _tasks(db)
        client_id = uuid.uuid4()
        service.complete_task_once(
            "t1", tenant_key=TENANT, client_event_id=client_id, details=TaskCompletionDetails(), actor=ACTOR
        )

        with pytest.raises(ClientEventMismatchError):
            service.complete_task_once(
                "t2", tenant_key=TENANT, client_event_id=client_id, details=TaskCompletionDetails(), actor=ACTOR
            )
        assert _rows(db, col.CARE_EVENTS, "task_key", "t2") == 0
        assert db.collection(col.TASKS).get("t2")["status"] == "pending"

    def test_a_batch_replay_three_times_closes_each_task_once(self, db) -> None:
        service = _tasks(db)
        batch_id = uuid.uuid4()

        answers = [
            service.batch_status_change(
                ["t1", "t2"],
                "complete",
                tenant_key=TENANT,
                details=TaskCompletionDetails(),
                actor=ACTOR,
                client_event_id=batch_id,
            )
            for _ in range(3)
        ]

        assert answers == [(["t1", "t2"], [])] * 3
        for key in ("t1", "t2"):
            assert _rows(db, col.CARE_EVENTS, "task_key", key) == 1
            assert _rows(db, col.TASKS, "completion_client_event_id", batch_item_client_event_id(batch_id, key)) == 1

    def test_a_batch_decides_per_task(self, db) -> None:
        # t2 was closed by someone else before the batch ran: the first attempt closes t1 and reports t2. The replay
        # of the same batch keeps t1 a success without a second write and reports t2 again - per task.
        service = _tasks(db)
        service.complete_task("t2", tenant_key=TENANT, details=TaskCompletionDetails(), actor=ACTOR)
        batch_id = uuid.uuid4()

        answers = [
            service.batch_status_change(
                ["t1", "t2"],
                "complete",
                tenant_key=TENANT,
                details=TaskCompletionDetails(),
                actor=ACTOR,
                client_event_id=batch_id,
            )
            for _ in range(2)
        ]

        for succeeded, failed in answers:
            assert succeeded == ["t1"]
            assert [(item["key"], item["code"]) for item in failed] == [("t2", "task.already_closed")]
        assert [_rows(db, col.CARE_EVENTS, "task_key", key) for key in ("t1", "t2")] == [1, 1]

    def test_the_same_batch_id_over_other_tasks_is_refused(self, db) -> None:
        service = _tasks(db)
        batch_id = uuid.uuid4()
        service.batch_status_change(
            ["t1"],
            "complete",
            tenant_key=TENANT,
            details=TaskCompletionDetails(),
            actor=ACTOR,
            client_event_id=batch_id,
        )

        with pytest.raises(ClientEventMismatchError):
            service.batch_status_change(
                ["t1", "t3"],
                "complete",
                tenant_key=TENANT,
                details=TaskCompletionDetails(),
                actor=ACTOR,
                client_event_id=batch_id,
            )
        assert db.collection(col.TASKS).get("t3")["status"] == "pending"


# ── POST /attachments and the plant photo upload ─────────────────────────────

_shade = iter(range(1, 250))


def _photo() -> bytes:
    shade = next(_shade)
    buffer = io.BytesIO()
    Image.new("RGB", (40, 30), color=(shade, 200, 255 - shade)).save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.fixture
def uploads(db, tmp_path) -> Callable[[Any], AttachmentService]:
    root = str(tmp_path / "storage")

    def build(handle: Any) -> AttachmentService:
        repo = ArangoAttachmentRepository(handle)
        storage = LocalFsStorageAdapter(
            root=root,
            public_base_url="http://localhost",
            signing_secret="client-event-test-signing-secret",
            max_object_size_bytes=10 * 1024 * 1024,
            attachment_repo=repo,
        )
        return AttachmentService(storage=storage, attachment_repo=repo, settings=Settings())

    with patch("app.tasks.storage_tasks.generate_thumbnails.delay"):
        yield build


def _upload(service: AttachmentService, data: bytes, client_id: uuid.UUID, **scope: str) -> Any:
    return asyncio.run(
        service.upload_once(
            tenant_key=TENANT,
            user_key=USER,
            data=data,
            mime_type="image/jpeg",
            original_filename="bed.jpg",
            category=AttachmentCategory.LOCATION,
            client_event_id=client_id,
            scope=scope or None,
        )
    )


class TestUpload:
    def test_a_replay_three_times_stores_one_record(self, db, uploads) -> None:
        service = uploads(db)
        client_id, data = uuid.uuid4(), _photo()

        answers = [_upload(service, data, client_id) for _ in range(3)]

        assert [answer.replayed for answer in answers] == [False, True, True]
        assert len({answer.attachment.key for answer in answers}) == 1
        assert _rows(db, col.ATTACHMENTS, "client_event_id", str(client_id)) == 1

    def test_two_attempts_at_once_store_one_record(self, db, uploads) -> None:
        client_id, data = uuid.uuid4(), _photo()

        results = _race(lambda: _upload(uploads(_handle()), data, client_id))

        answered = [result for result in results if not isinstance(result, Exception)]
        assert answered, results
        assert all(isinstance(result, WriteConflictError) for result in results if isinstance(result, Exception))
        assert len({answer.attachment.key for answer in answered}) == 1
        # One record for these bytes, not one per attempt.
        assert _rows(db, col.ATTACHMENTS, "sha256", answered[0].attachment.sha256) == 1

    def test_the_same_id_with_other_bytes_or_another_plant_is_refused(self, db, uploads) -> None:
        service = uploads(db)
        client_id, data = uuid.uuid4(), _photo()
        _upload(service, data, client_id, plant_instance_key="pi_1")

        with pytest.raises(ClientEventMismatchError):
            _upload(service, _photo(), client_id, plant_instance_key="pi_1")
        with pytest.raises(ClientEventMismatchError):
            _upload(service, data, client_id, plant_instance_key="pi_2")
        assert _rows(db, col.ATTACHMENTS, "client_event_id", str(client_id)) == 1
