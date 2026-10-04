"""Request, actor and tenant context travel into every log line and into Celery (#2130, MT-034).

Before #2130 the ``request_id`` the middleware binds ended at the request: a task
the request dispatched logged without it, so a worker line could not be joined to
the request that caused it. The tenant and the actor were not bound at all — a
line said *what* happened, never *in which tenant* or *for whom* (as pseudonyms).

**Why the tenant is not simply ``bind_contextvars``-ed in ``get_current_tenant``.**
That was the target state the issue named, and it is inert: measured on the
pre-fix tree, ``get_current_tenant`` is a *sync* dependency, FastAPI runs it in a
worker thread with a *copy* of the request's context, and a ContextVar set in
that copy is gone when the thread returns. A line logged by the endpoint saw
``{'request_id': …}`` and no ``tenant``. The binding therefore goes into a
per-request holder the middleware creates (a mutable object every copy of the
context shares), and a structlog processor merges it into each line.

Every case drives the production path: the real ``request_id_middleware``, the
real ``get_current_user``/``get_current_tenant`` dependencies, the real
``setup_logging`` processor chain, and — for Celery — a real publish through
``apply_async`` consumed by a real worker (in-memory broker), so the signal
handlers in :mod:`app.tasks` are the ones that run. Eager mode would not do:
``task_always_eager`` never publishes, so ``before_task_publish`` never fires.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any

import pytest
import structlog
from celery import Celery
from celery.contrib.testing.worker import start_worker
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

import app.tasks  # noqa: F401 — connects the Celery signal handlers under test
from app.common import auth as auth_mod
from app.common.dependencies import get_auth_provider, get_tenant_service
from app.common.enums import TenantRole
from app.common.log_privacy import log_subject, log_tenant
from app.common.middleware import request_id_middleware
from app.config.settings import settings
from app.domain.models.tenant_context import TenantContext
from app.domain.models.user import User
from tests.unit.guards.test_logs_carry_no_secrets_runtime import isolated_logging  # noqa: F401

_USER_KEY = "owner-2130"
_TENANT_KEY = "tenant-2130"
_TENANT_SLUG = "garden-2130"
#: Long enough for ``log_subject``/``log_tenant`` to produce real pseudonyms; built at
#: runtime so no credential-shaped literal sits in the source.
_SALT = "correlation-probe-" * 3


class _Capture(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.NOTSET)
        self.lines: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.lines.append(record.getMessage())

    def events(self, event: str) -> list[dict[str, Any]]:
        found = []
        for line in self.lines:
            try:
                parsed = json.loads(line)
            except ValueError:
                continue
            if isinstance(parsed, dict) and parsed.get("event") == event:
                found.append(parsed)
        return found


@pytest.fixture
def capture(isolated_logging: None, monkeypatch: pytest.MonkeyPatch) -> Iterator[_Capture]:  # noqa: F811
    """The API's logging setup with a handler that keeps the rendered JSON lines."""
    from app.config.logging import setup_logging

    monkeypatch.setattr(settings, "log_pseudonym_salt", _SALT)
    root = logging.getLogger()
    root.handlers = []
    root.setLevel(logging.WARNING)
    setup_logging(False)
    handler = _Capture()
    root.addHandler(handler)
    yield handler
    structlog.contextvars.clear_contextvars()


class _AuthProvider:
    def resolve_user(self, authorization: str | None, *, client_ip: str | None) -> User:
        return User(_key=_USER_KEY, email="owner@example.org", display_name="Owner")

    def resolve_user_optional(self, authorization: str | None, *, client_ip: str | None) -> User:
        return self.resolve_user(authorization, client_ip=client_ip)


class _TenantService:
    def get_tenant_by_slug(self, slug: str) -> SimpleNamespace:
        return SimpleNamespace(key=_TENANT_KEY, slug=slug)

    def get_membership(self, user_key: str, tenant_key: str) -> SimpleNamespace:
        return SimpleNamespace(role=TenantRole.LEAD, admin_scopes=[], is_active=True)


def _app(on_request: Any) -> FastAPI:
    app = FastAPI()
    app.middleware("http")(request_id_middleware)

    @app.get("/t/{tenant_slug}/probe")
    def probe(ctx: TenantContext = Depends(auth_mod.get_current_tenant)) -> dict[str, str]:
        return on_request()

    app.dependency_overrides[get_auth_provider] = _AuthProvider
    app.dependency_overrides[get_tenant_service] = _TenantService
    return app


def test_a_log_line_after_the_tenant_dependency_names_tenant_and_actor_by_pseudonym(capture: _Capture) -> None:
    def on_request() -> dict[str, str]:
        structlog.get_logger("probe").info("probe_request_line")
        return {}

    response = TestClient(_app(on_request)).get(f"/t/{_TENANT_SLUG}/probe")

    assert response.status_code == 200
    [line] = capture.events("probe_request_line")
    assert line["request_id"] == response.headers["X-Request-ID"]
    assert line["tenant"] == log_tenant(_TENANT_KEY)
    assert line["actor"] == log_subject(_USER_KEY)
    # Pseudonyms, never the keys themselves.
    rendered = json.dumps(line)
    assert _TENANT_KEY not in rendered
    assert _USER_KEY not in rendered


def test_an_explicit_tenant_on_the_line_wins_over_the_request_tenant(capture: _Capture) -> None:
    """A line about another tenant (an admin action) keeps the tenant it names."""

    def on_request() -> dict[str, str]:
        structlog.get_logger("probe").info("probe_other_tenant", tenant=log_tenant("someone-else"))
        return {}

    TestClient(_app(on_request)).get(f"/t/{_TENANT_SLUG}/probe")

    [line] = capture.events("probe_other_tenant")
    assert line["tenant"] == log_tenant("someone-else")


@pytest.fixture
def worker_app() -> Iterator[Celery]:
    """A Celery app on the in-memory broker with a real worker thread consuming it.

    A separate app rather than the production ``celery_app``: the signal handlers
    under test are connected without a sender filter, so they run for every app
    in the process — exactly as they do for the production one — while the
    production app's broker configuration stays untouched for every other test.
    """
    probe = Celery("probe-2130", broker="memory://", backend="cache+memory://", set_as_current=False)
    probe.conf.update(task_serializer="json", accept_content=["json"], result_serializer="json")

    @probe.task(name="probe_2130.log_line")
    def log_line(label: str) -> dict[str, Any]:
        structlog.get_logger("probe.task").info("probe_task_line", label=label)
        return dict(structlog.contextvars.get_contextvars())

    # Started before ``capture`` (see the parameter order of the tests): the worker's
    # own logging setup replaces the root handlers, and the capture handler must be
    # installed after it.
    with start_worker(probe, perform_ping_check=False, shutdown_timeout=10):
        yield probe


def test_a_task_dispatched_from_a_request_logs_with_the_request_context(worker_app: Celery, capture: _Capture) -> None:
    task = worker_app.tasks["probe_2130.log_line"]
    results: dict[str, Any] = {}

    def on_request() -> dict[str, str]:
        results["async"] = task.apply_async(kwargs={"label": "from-request"})
        return {}

    response = TestClient(_app(on_request)).get(f"/t/{_TENANT_SLUG}/probe")
    bound_in_task = results["async"].get(timeout=15)

    [line] = [e for e in capture.events("probe_task_line") if e.get("label") == "from-request"]
    assert line["request_id"] == response.headers["X-Request-ID"]
    assert line["actor"] == log_subject(_USER_KEY)
    assert line["tenant"] == log_tenant(_TENANT_KEY)
    assert line["task_id"] == results["async"].id
    assert bound_in_task["request_id"] == response.headers["X-Request-ID"]
    rendered = json.dumps(line)
    assert _TENANT_KEY not in rendered
    assert _USER_KEY not in rendered


def test_the_worker_does_not_carry_one_tasks_context_into_the_next(worker_app: Celery, capture: _Capture) -> None:
    """``task_postrun`` clears what ``task_prerun`` bound (the worker thread is reused)."""
    task = worker_app.tasks["probe_2130.log_line"]

    def on_request() -> dict[str, str]:
        task.apply_async(kwargs={"label": "first"}).get(timeout=15)
        return {}

    TestClient(_app(on_request)).get(f"/t/{_TENANT_SLUG}/probe")
    # Dispatched outside any request: nothing to carry.
    bound = task.apply_async(kwargs={"label": "second"}).get(timeout=15)

    [line] = [e for e in capture.events("probe_task_line") if e.get("label") == "second"]
    assert "request_id" not in line
    assert "actor" not in line
    assert "tenant" not in line
    assert set(bound) == {"task_id"}


def test_an_eager_task_inside_a_request_leaves_the_request_context_intact(
    worker_app: Celery, capture: _Capture
) -> None:
    """``.apply()`` (``tasks/tenant_router.py``) runs in the request's thread and context."""
    task = worker_app.tasks["probe_2130.log_line"]

    def on_request() -> dict[str, str]:
        task.apply(kwargs={"label": "eager"})
        structlog.get_logger("probe").info("probe_after_eager")
        return {}

    response = TestClient(_app(on_request)).get(f"/t/{_TENANT_SLUG}/probe")

    [inside] = [e for e in capture.events("probe_task_line") if e.get("label") == "eager"]
    [after] = capture.events("probe_after_eager")
    assert inside["request_id"] == after["request_id"] == response.headers["X-Request-ID"]
    assert "task_id" in inside
    assert "task_id" not in after
