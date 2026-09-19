"""``GET /t/{slug}/tasks/queue`` — category and origin are server-side scopes (#1503).

The defect shape, identical to the one #1484 closed for ``plant_key``: the queue
endpoint answers at most 200 rows (``TaskService.get_task_queue`` →
``get_pending_tasks(0, 200)``) and the page narrowed that answer *afterwards*. A
task matching the selected category or origin but sitting past row 200 was never
in the payload, so the filter reported "nothing here" for a filter that has
matches. A client filter over a capped list is not a filter, it is a guess about
what the cap left behind — the narrowing has to happen before the ``LIMIT``.

Every test below runs the real router, the real :class:`TaskService` and the real
:class:`ArangoTaskRepository` against the replaying database double
(:mod:`tests.support.tenant_replay`), whose ``LIMIT`` is applied to the *filtered*
row set exactly as ArangoDB applies it. That is what makes the cap tests
meaningful: drop the predicate from the AQL and the double pages the unfiltered
201 rows, so the row past the cap disappears again and the test goes red.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.v1.tasks.tenant_router import router as tasks_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_task_service
from app.common.enums import TenantRole
from app.common.exceptions import KamerplanterError
from app.data_access.arango import collections as col
from app.data_access.arango.task_repository import ArangoTaskRepository
from app.domain.engines.dependency_resolver import DependencyResolver
from app.domain.models.tenant_context import TenantContext
from app.domain.services.task_service import TaskService
from tests.support.tenant_replay import ReplayingAql, ReplayingDatabase, rows_and_count

TENANT_SLUG = "anna"
TENANT_KEY = "tenant-a"
FOREIGN_TENANT_KEY = "tenant-b"

#: The cap ``TaskService.get_task_queue`` applies to the unscoped branch.
QUEUE_CAP = 200

OWN_PLANT = "plant-a1"
OWN_RUN = "run-a1"

#: Text that must never reach a caller of the other tenant.
FOREIGN_MARKER = "geheime-fremde-notiz"


def _error_handler(request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code, "message": exc.message},
    )


def _url(path: str) -> str:
    return f"/api/v1/t/{TENANT_SLUG}{path}"


def _task(key: str, **overrides: Any) -> dict[str, Any]:
    """A pending task of the caller's tenant.

    ``entity_type`` is ``planting_run`` rather than ``plant_instance`` on
    purpose. ``get_all_tasks`` carries an orphan guard that resolves
    ``DOCUMENT(plant_instances/<entity_key>)`` for every plant-anchored row and
    drops the ones whose plant is gone. The replaying double does not model
    ``DOCUMENT``, so a plant-anchored fixture would pass here and return **no**
    rows at all against a real database — a green test about a query that
    answers nothing. The plant-branch cases below opt in explicitly, and say so.
    """
    doc = {
        "_key": key,
        "_id": f"{col.TASKS}/{key}",
        "tenant_key": TENANT_KEY,
        "name": f"Task {key}",
        "category": "maintenance",
        "origin": "user",
        "entity_type": "planting_run",
        "entity_key": OWN_RUN,
        "status": "pending",
        "due_date": "2026-08-03T06:00:00+00:00",
    }
    doc.update(overrides)
    return doc


def _client(rows: list[dict[str, Any]]) -> TestClient:
    aql = ReplayingAql()
    # Dependency resolution for the queue — no tenant dimension, no blockers.
    aql.route("FOR e IN task_blocks", lambda q, b: [])
    aql.route("FOR doc IN tasks", lambda q, b: rows_and_count(rows, q, b))

    repo = ArangoTaskRepository(ReplayingDatabase(aql))
    # The real dependency resolver: the queue filters its result through it, and a
    # MagicMock would return an empty set and mask what the query returned.
    service = TaskService(repo, MagicMock(), DependencyResolver())

    app = FastAPI()
    app.include_router(tasks_router, prefix="/api/v1/t/{tenant_slug}")
    app.add_exception_handler(KamerplanterError, _error_handler)
    app.dependency_overrides[get_current_tenant] = lambda: TenantContext(
        tenant_key=TENANT_KEY,
        tenant_slug=TENANT_SLUG,
        user_key="user-1",
        role=TenantRole.GROWER,
    )
    app.dependency_overrides[get_task_service] = lambda: service
    return TestClient(app)


def _keys(resp) -> list[str]:
    return [t["key"] for t in resp.json()]


# ── The cap: a match past row 200 ────────────────────────────────────────────


def _rows_with_target_past_the_cap(**target_fields: str) -> tuple[list[dict[str, Any]], str]:
    """``QUEUE_CAP`` ordinary rows, then one carrying ``target_fields``.

    The double pages the list in the order it is given — it does not sort — so
    the ordering here *is* the one the ``LIMIT`` cuts. The ``due_date`` values
    are chosen so that the real query's ``SORT doc.due_date ASC`` would produce
    the same order, and the target is therefore the row a real database drops
    too.
    """
    fillers = [_task(f"filler-{i:03d}", due_date=f"2026-08-03T06:00:{i % 60:02d}+00:00") for i in range(QUEUE_CAP)]
    target = _task("target", due_date="2026-09-01T06:00:00+00:00", **target_fields)
    return [*fillers, target], "target"


class TestTheCategoryFilterReachesPastTheCap:
    def test_the_unfiltered_queue_genuinely_drops_the_row(self):
        """The premise. Without it the filtered assertion proves nothing."""
        rows, target = _rows_with_target_past_the_cap(category="ipm")
        client = _client(rows)

        resp = client.get(_url("/tasks/queue"))

        assert resp.status_code == 200, resp.text
        assert len(resp.json()) == QUEUE_CAP
        assert target not in _keys(resp)

    def test_asking_for_the_category_returns_the_row_the_cap_hid(self):
        rows, target = _rows_with_target_past_the_cap(category="ipm")
        client = _client(rows)

        resp = client.get(_url("/tasks/queue"), params={"category": "ipm"})

        assert resp.status_code == 200, resp.text
        assert _keys(resp) == [target]

    def test_a_category_nobody_matches_answers_empty_rather_than_everything(self):
        rows, _ = _rows_with_target_past_the_cap(category="ipm")
        client = _client(rows)

        resp = client.get(_url("/tasks/queue"), params={"category": "harvest"})

        assert resp.status_code == 200, resp.text
        assert resp.json() == []


class TestTheOriginFilterReachesPastTheCap:
    def test_asking_for_one_origin_returns_the_row_the_cap_hid(self):
        rows, target = _rows_with_target_past_the_cap(origin="pipeline")
        client = _client(rows)

        resp = client.get(_url("/tasks/queue"), params={"origin": "pipeline"})

        assert resp.status_code == 200, resp.text
        assert _keys(resp) == [target]

    def test_the_machine_partition_is_one_request_for_both_of_its_values(self):
        """``origin`` is repeatable: the UI's "machine-generated" is
        ``system`` + ``pipeline``, and asking for it must not cost two requests
        whose union the client then has to assemble."""
        rows, _ = _rows_with_target_past_the_cap(origin="pipeline")
        rows.insert(0, _task("system-task", origin="system", due_date="2026-01-01T06:00:00+00:00"))
        client = _client(rows)

        resp = client.get(_url("/tasks/queue"), params=[("origin", "system"), ("origin", "pipeline")])

        assert resp.status_code == 200, resp.text
        assert sorted(_keys(resp)) == ["system-task", "target"]

    def test_asking_for_user_origin_excludes_the_machine_rows(self):
        """The machine row sits *inside* the cap and the last user row just
        outside it, so an answer that merely echoed the cap fails both halves:
        it would still carry ``machine`` and still be missing ``filler-199``."""
        rows, _ = _rows_with_target_past_the_cap(origin="pipeline")
        rows.insert(0, _task("machine", origin="system", due_date="2026-01-01T06:00:00+00:00"))
        client = _client(rows)

        resp = client.get(_url("/tasks/queue"), params={"origin": "user"})

        assert resp.status_code == 200, resp.text
        keys = _keys(resp)
        assert "machine" not in keys
        assert "target" not in keys
        assert f"filler-{QUEUE_CAP - 1:03d}" in keys


class TestTheFiltersComposeWithTheOtherScopes:
    def test_the_plant_branch_takes_the_category_too(self):
        """The plant branch is uncapped, but a filter that only exists on one of
        the two branches is a filter the page cannot rely on.

        These two rows are plant-anchored because the branch under test selects
        on exactly that anchor; they do not travel through ``get_all_tasks`` and
        its orphan guard, so the anchor costs nothing here.
        """
        rows = [
            _task("a", category="ipm", entity_type="plant_instance", entity_key=OWN_PLANT),
            _task("b", category="maintenance", entity_type="plant_instance", entity_key=OWN_PLANT),
        ]
        client = _client(rows)

        resp = client.get(_url("/tasks/queue"), params={"plant_key": OWN_PLANT, "category": "ipm"})

        assert resp.status_code == 200, resp.text
        assert _keys(resp) == ["a"]

    def test_the_plant_branch_takes_the_origin_too(self):
        rows = [
            _task("a", origin="system", entity_type="plant_instance", entity_key=OWN_PLANT),
            _task("b", origin="user", entity_type="plant_instance", entity_key=OWN_PLANT),
        ]
        client = _client(rows)

        resp = client.get(_url("/tasks/queue"), params={"plant_key": OWN_PLANT, "origin": "system"})

        assert resp.status_code == 200, resp.text
        assert _keys(resp) == ["a"]

    def test_a_filter_never_widens_the_tenant_scope(self):
        """The #324 direction: an added predicate must be an *extra* one, never
        a swap for the tenant predicate."""
        rows = [
            _task("own", category="ipm"),
            _task(
                "foreign",
                category="ipm",
                tenant_key=FOREIGN_TENANT_KEY,
                name=FOREIGN_MARKER,
                entity_key="run-b1",
            ),
        ]
        client = _client(rows)

        resp = client.get(_url("/tasks/queue"), params={"category": "ipm"})

        assert resp.status_code == 200, resp.text
        assert _keys(resp) == ["own"]
        assert FOREIGN_MARKER not in resp.text


class TestTheBoundaryRejectsWhatItCannotMean:
    def test_an_unknown_category_is_422_rather_than_an_empty_list(self):
        rows, _ = _rows_with_target_past_the_cap(category="ipm")
        client = _client(rows)

        resp = client.get(_url("/tasks/queue"), params={"category": "not-a-category"})

        assert resp.status_code == 422, resp.text

    def test_an_unknown_origin_is_422_rather_than_an_empty_list(self):
        rows, _ = _rows_with_target_past_the_cap(origin="pipeline")
        client = _client(rows)

        resp = client.get(_url("/tasks/queue"), params={"origin": "robot"})

        assert resp.status_code == 422, resp.text


class TestTheCompletedListTakesAnOriginToo:
    """``GET /t/{slug}/tasks`` already accepted ``category``; ``origin`` is the
    half the completed list was still narrowing client-side (#1503)."""

    def test_asking_for_one_origin_narrows_the_list(self):
        rows = [
            _task("machine", status="completed", origin="pipeline"),
            _task("human", status="completed", origin="user"),
        ]
        client = _client(rows)

        resp = client.get(_url("/tasks"), params={"status": "completed", "origin": "pipeline"})

        assert resp.status_code == 200, resp.text
        assert _keys(resp) == ["machine"]

    def test_the_machine_partition_is_one_request_there_as_well(self):
        rows = [
            _task("sys", status="completed", origin="system"),
            _task("pipe", status="completed", origin="pipeline"),
            _task("human", status="completed", origin="user"),
        ]
        client = _client(rows)

        resp = client.get(
            _url("/tasks"),
            params=[("status", "completed"), ("origin", "system"), ("origin", "pipeline")],
        )

        assert resp.status_code == 200, resp.text
        assert sorted(_keys(resp)) == ["pipe", "sys"]

    def test_an_unknown_status_is_422_rather_than_an_empty_list(self):
        """The same boundary rule the new parameters follow (REQ-006). ``status``
        and ``category`` predate #1503 as free strings, which meant a typo —
        ``complete`` for ``completed`` — answered **200 with an empty list**: a
        caller cannot tell "no such tasks" from "no such status"."""
        client = _client([_task("done", status="completed")])

        resp = client.get(_url("/tasks"), params={"status": "complete"})

        assert resp.status_code == 422, resp.text

    def test_an_unknown_category_is_422_rather_than_an_empty_list(self):
        client = _client([_task("a", category="ipm")])

        resp = client.get(_url("/tasks"), params={"category": "not-a-category"})

        assert resp.status_code == 422, resp.text

    def test_the_values_the_ui_actually_sends_still_answer(self):
        """The other half of the boundary: tightening a published parameter must
        not reject what the product sends. These are the exact triples the pages
        issue (`TaskQueuePage` completed list, `PlantInstanceDetailPage` care
        reminders)."""
        rows = [_task("done", status="completed"), _task("care", category="care_reminder")]
        client = _client(rows)

        assert client.get(_url("/tasks"), params={"status": "completed"}).status_code == 200
        assert (
            client.get(
                _url("/tasks"),
                params={"status": "pending", "category": "care_reminder"},
            ).status_code
            == 200
        )

    def test_an_unknown_origin_is_422_there_as_well(self):
        client = _client([])

        resp = client.get(_url("/tasks"), params={"origin": "robot"})

        assert resp.status_code == 422, resp.text
