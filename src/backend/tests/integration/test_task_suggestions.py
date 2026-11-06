"""REQ-053 WP 8.17 (#2660) — accept and dismiss a suggested task against a real ArangoDB (GP-API-040, GP-FR-086).

Real router, real :class:`TaskService`, real :class:`ArangoTaskRepository`, real database; only the authenticated
tenant context is supplied. What no double can decide, measured here:

* the conditional statement (``resolve_suggestion``) writes only while the task still is a suggestion of the
  caller's tenant — a stale decision (someone accepted it in between) matches nothing and writes nothing;
* a dismissal is a ``skipped`` task and nothing else: no ``care_events`` row, no ``task_logged_as`` edge, and the
  task is gone from every open-task reader (the bed queue, the pending listing);
* a foreign key answers like an unknown one and its document stays byte-identical; a viewer is refused before any
  read or write.

Every "nothing is there" assertion is paired with a positive control read through the same path.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from arango import ArangoClient
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.tasks.tenant_router import router as tasks_router
from app.common.auth import get_current_tenant, get_current_user
from app.common.dependencies import get_task_service
from app.common.enums import TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError
from app.data_access.arango import collections as col
from app.data_access.arango.task_repository import ArangoTaskRepository
from app.domain.engines.dependency_resolver import DependencyResolver
from app.domain.engines.hst_validator import HSTValidator
from app.domain.models.tenant_context import TenantContext
from app.domain.services.task_service import TaskService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = pytest.mark.usefixtures("arango_db")

TEST_DATABASE = run_database_name("task_suggestions")
A, B = "ten_a", "ten_b"
SLUG = "anna"
BED = "bed_a"

_DOCUMENTS = (col.TASKS, col.CARE_EVENTS, col.PLANT_INSTANCES, col.TASK_AUDIT_ENTRIES)
_EDGES = (col.TASK_LOGGED_AS, col.HAS_TASK)


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


def _task(key: str, tenant: str, *, suggested: bool | None, status: str = "pending") -> dict:
    doc = {
        "_key": key,
        "tenant_key": tenant,
        "name": f"Water {key}",
        "category": "watering",
        "status": status,
        "origin": "system",
        "source": "irrigation_demand",
        "entity_type": "location",
        "entity_key": BED,
    }
    if suggested is not None:
        doc["suggested"] = suggested
        doc["suggestion_reason"] = "ET0 demand 4.2 L/m2 over 3 days" if suggested else None
    return doc


@pytest.fixture
def db(database):
    for entry in database.collections():
        if not entry["system"]:
            database.collection(entry["name"]).truncate()
    tasks = database.collection(col.TASKS)
    tasks.insert(_task("t_sugg", A, suggested=True))
    tasks.insert(_task("t_sugg_2", A, suggested=True))
    tasks.insert(_task("t_plain", A, suggested=False))
    # Imported from an older archive: the attribute is absent. Null-safe — it is no suggestion.
    tasks.insert(_task("t_legacy", A, suggested=None))
    tasks.insert(_task("t_b", B, suggested=True))
    return database


@pytest.fixture
def repo(db) -> ArangoTaskRepository:
    return ArangoTaskRepository(db)


def _client(repo: ArangoTaskRepository, role: TenantRole = TenantRole.GROWER) -> TestClient:
    service = TaskService(repo, HSTValidator(), DependencyResolver())
    app = FastAPI()
    app.include_router(tasks_router, prefix="/api/v1/t/{tenant_slug}")
    app.add_exception_handler(KamerplanterError, app_error_handler)
    app.dependency_overrides[get_current_tenant] = lambda: TenantContext(
        tenant_key=A, tenant_slug=SLUG, user_key="u_sabine", role=role
    )
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(key="u_sabine", account_type="human")
    app.dependency_overrides[get_task_service] = lambda: service
    return TestClient(app)


def _url(key: str, action: str) -> str:
    return f"/api/v1/t/{SLUG}/tasks/{key}/{action}"


def _stored(db, key: str) -> dict:
    doc = db.collection(col.TASKS).get(key)
    return {name: value for name, value in doc.items() if name not in ("_rev", "_id")}


def _open_keys(repo: ArangoTaskRepository) -> set[str]:
    """What the bed queue reads (GP-API-030) — suggestions included, closed tasks not."""
    return {t.key for t in repo.get_pending_tasks_in_locations([BED], 200, tenant_key=A) if t.key}


class TestAccept:
    def test_accepting_clears_the_flag_and_keeps_the_task_open(self, db, repo):
        client = _client(repo)

        resp = client.post(_url("t_sugg", "accept-suggestion"))

        assert resp.status_code == 200, resp.text
        stored = _stored(db, "t_sugg")
        assert stored["suggested"] is False
        assert stored["suggestion_reason"] is None
        assert stored["status"] == "pending"
        assert stored["origin"] == "system" and stored["source"] == "irrigation_demand"
        assert "t_sugg" in _open_keys(repo)
        # The neighbour is untouched: the statement addresses one key.
        assert _stored(db, "t_sugg_2")["suggested"] is True

    @pytest.mark.parametrize("key", ["t_plain", "t_legacy"])
    def test_a_task_that_is_no_suggestion_is_a_409_and_unchanged(self, db, repo, key):
        before = _stored(db, key)

        resp = _client(repo).post(_url(key, "accept-suggestion"))

        assert resp.status_code == 409
        assert resp.json()["error_code"] == "task.not_a_suggestion"
        assert _stored(db, key) == before


class TestDismiss:
    def test_a_dismissed_suggestion_is_skipped_writes_no_care_event_and_leaves_the_open_list(self, db, repo):
        assert {"t_sugg", "t_sugg_2"} <= _open_keys(repo)  # positive control: the reader sees suggestions

        resp = _client(repo).post(_url("t_sugg", "dismiss-suggestion"), json={"reason": "Rain is forecast"})

        assert resp.status_code == 200, resp.text
        stored = _stored(db, "t_sugg")
        assert stored["status"] == "skipped"
        assert stored["completion_notes"] == "Rain is forecast"
        assert stored["suggested"] is True
        assert db.collection(col.CARE_EVENTS).count() == 0
        assert db.collection(col.TASK_LOGGED_AS).count() == 0
        open_keys = _open_keys(repo)
        assert "t_sugg" not in open_keys
        assert "t_sugg_2" in open_keys
        pending, _ = repo.get_all_tasks(0, 50, {"status": "pending"}, tenant_key=A)
        assert "t_sugg" not in {t.key for t in pending}

    def test_a_task_that_is_no_suggestion_is_a_409_and_unchanged(self, db, repo):
        before = _stored(db, "t_plain")

        resp = _client(repo).post(_url("t_plain", "dismiss-suggestion"))

        assert resp.status_code == 409
        assert resp.json()["error_code"] == "task.not_a_suggestion"
        assert _stored(db, "t_plain") == before

    def test_dismissing_twice_is_a_409_the_second_time(self, repo):
        client = _client(repo)

        assert client.post(_url("t_sugg", "dismiss-suggestion")).status_code == 200
        resp = client.post(_url("t_sugg", "dismiss-suggestion"))

        assert resp.status_code == 409
        assert resp.json()["error_code"] == "task.suggestion_closed"


class TestTheTenantAndTheRole:
    @pytest.mark.parametrize("action", ["accept-suggestion", "dismiss-suggestion"])
    def test_a_foreign_suggestion_answers_like_an_unknown_one_and_stays_untouched(self, db, repo, action):
        before = _stored(db, "t_b")
        client = _client(repo)

        foreign = client.post(_url("t_b", action))
        unknown = client.post(_url("t_nope", action))

        assert foreign.status_code == unknown.status_code == 404
        # The same body with the key substituted: no existence oracle.
        assert foreign.json()["message"].replace("t_b", "<k>") == unknown.json()["message"].replace("t_nope", "<k>")
        assert _stored(db, "t_b") == before

    @pytest.mark.parametrize("action", ["accept-suggestion", "dismiss-suggestion"])
    def test_a_viewer_is_refused_with_403_and_nothing_is_written(self, db, repo, action):
        before = _stored(db, "t_sugg")

        resp = _client(repo, TenantRole.VIEWER).post(_url("t_sugg", action))

        assert resp.status_code == 403
        assert _stored(db, "t_sugg") == before
        # Positive control: the same call as a grower is allowed.
        assert _client(repo).post(_url("t_sugg", action)).status_code == 200


class TestTheConditionalWrite:
    """The statement decides on the stored document, not on the copy the service loaded."""

    def test_a_decision_on_a_stale_copy_writes_nothing(self, db, repo):
        # Someone accepted it after this caller loaded it: the stored task is no suggestion any more.
        db.collection(col.TASKS).update({"_key": "t_sugg", "suggested": False, "suggestion_reason": None})
        before = _stored(db, "t_sugg")

        written = repo.resolve_suggestion(
            "t_sugg", tenant_key=A, changes={"status": "skipped"}, open_statuses=("pending", "in_progress")
        )

        assert written is None
        assert _stored(db, "t_sugg") == before

    def test_a_closed_suggestion_is_not_dismissed_again(self, db, repo):
        db.collection(col.TASKS).update({"_key": "t_sugg", "status": "completed"})

        written = repo.resolve_suggestion(
            "t_sugg", tenant_key=A, changes={"status": "skipped"}, open_statuses=("pending", "in_progress")
        )

        assert written is None
        assert _stored(db, "t_sugg")["status"] == "completed"

    def test_another_tenant_never_matches(self, db, repo):
        written = repo.resolve_suggestion("t_b", tenant_key=A, changes={"suggested": False})

        assert written is None
        assert _stored(db, "t_b")["suggested"] is True
        # Positive control: the owner's statement matches.
        assert repo.resolve_suggestion("t_b", tenant_key=B, changes={"suggested": False}) is not None

    def test_only_the_named_fields_are_written(self, db, repo):
        # A concurrent edit of another field (the name) survives the decision: no full-document rewrite.
        db.collection(col.TASKS).update({"_key": "t_sugg", "name": "Renamed meanwhile"})

        written = repo.resolve_suggestion("t_sugg", tenant_key=A, changes={"suggested": False})

        assert written is not None
        stored = _stored(db, "t_sugg")
        assert stored["name"] == "Renamed meanwhile"
        assert stored["suggested"] is False
