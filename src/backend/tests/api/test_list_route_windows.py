"""MT-035 (#2131) — the converted list routes hand a bounded window to their service.

The guard ``tests/unit/guards/test_list_routes_are_bounded.py`` proves a list
route *depends on* the pagination dependency; it cannot see whether the handler
then forwards ``offset``/``limit`` or ignores them and reads everything. These
tests drive each converted route through the assembled app and assert what the
service was asked for:

* no query parameters → ``offset=0, limit=50`` — the behavioural change for a
  client that sent none and used to receive every row;
* ``?offset=4&limit=3`` → exactly that window;
* ``?limit=201`` → 422 before the service is reached.

The four keyset routes additionally forward ``after`` and refuse ``after`` with a
non-zero ``offset``.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.v1.ki_assistent.deps import require_ai_tenant_enabled
from app.common import dependencies as deps
from app.common.auth import (
    get_active_tenant_context,
    get_active_tenant_key,
    get_current_tenant,
    get_current_user,
    require_platform_admin,
)
from app.common.enums import AdminScope, TenantRole
from app.domain.models.tenant_context import TenantContext

SLUG = "lisa"
TENANT_KEY = "tenant_lisa"


def _ctx() -> TenantContext:
    return TenantContext(
        tenant_key=TENANT_KEY,
        tenant_slug=SLUG,
        user_key="user_lisa",
        role=TenantRole.LEAD,
        admin_scopes=[AdminScope.MANAGEMENT],
    )


@dataclass(frozen=True)
class _Route:
    url: str
    provider: Callable[..., Any]
    method: str
    #: Reads ``(offset, limit)`` from the service call's ``call_args``.
    window: Callable[[Any], tuple[int, int]]


def _kw(call: Any) -> tuple[int, int]:
    return call.kwargs["offset"], call.kwargs["limit"]


_OFFSET_ROUTES = [
    _Route("/api/v1/admin/platform/tenants", deps.get_tenant_service, "list_all_tenants", _kw),
    _Route("/api/v1/admin/platform/users", deps.get_user_service, "list_all_users", _kw),
    _Route(f"/api/v1/tenants/{SLUG}/invitations", deps.get_tenant_service, "list_invitations", _kw),
    _Route(f"/api/v1/t/{SLUG}/ai/conversations", deps.get_ai_assistant_service, "list_conversations", _kw),
    _Route(f"/api/v1/t/{SLUG}/tasks/plants/plant_1", deps.get_task_service, "get_tasks_for_plant", _kw),
    _Route(
        f"/api/v1/t/{SLUG}/post-harvest/batch_1/observations",
        deps.get_post_harvest_service,
        "list_observations",
        _kw,
    ),
    # The second conversion round (#2131): five of the nine pinned ``remaining``
    # routes plus the platform-admin member list that reads the same rows.
    _Route(f"/api/v1/tenants/{SLUG}/members", deps.get_tenant_service, "list_members", _kw),
    _Route(f"/api/v1/tenants/{SLUG}/assignments", deps.get_tenant_service, "list_assignments", _kw),
    _Route("/api/v1/admin/platform/tenants/tenant_1/members", deps.get_tenant_service, "list_members", _kw),
    _Route(
        f"/api/v1/t/{SLUG}/tasks/workflows/wf_1/executions",
        deps.get_task_service,
        "get_executions_for_template",
        _kw,
    ),
    _Route(f"/api/v1/t/{SLUG}/inventree/references", deps.get_inventree_service, "list_references", _kw),
    _Route(
        f"/api/v1/t/{SLUG}/propagation/stats/by-cultivar",
        deps.get_propagation_service,
        "stats",
        _kw,
    ),
]

_CURSOR_ROUTES = [
    _Route(f"/api/v1/t/{SLUG}/plant-instances", deps.get_plant_instance_service, "list_plants_window", _kw),
    _Route(f"/api/v1/t/{SLUG}/watering-logs", deps.get_watering_log_service, "list_logs_window", _kw),
    _Route(f"/api/v1/t/{SLUG}/feeding-events", deps.get_feeding_service, "list_events_window", _kw),
    _Route(f"/api/v1/t/{SLUG}/watering-events", deps.get_watering_service, "list_events_window", _kw),
]


def _args(first: int) -> Callable[[Any], tuple[int, int]]:
    """Reads ``(offset, limit)`` from two adjacent positional arguments of the call."""

    def read(call: Any) -> tuple[int, int]:
        return call.args[first], call.args[first + 1]

    return read


@dataclass(frozen=True)
class _CountFree:
    route: _Route
    #: The counted sibling the route used to call: it must not be called any more.
    counted: str


#: The third conversion round (#2131): offset routes that were already bounded but
#: called a service method returning ``(rows, total)`` and dropped the total —
#: a second scan of every matching row per page. They now call the count-free window.
_COUNT_FREE = [
    _CountFree(
        _Route(f"/api/v1/t/{SLUG}/ipm/plants/p1/inspections", deps.get_ipm_service, "get_inspections_window", _args(1)),
        "get_inspections",
    ),
    _CountFree(
        _Route(
            f"/api/v1/t/{SLUG}/ipm/plants/p1/treatment-applications",
            deps.get_ipm_service,
            "get_applications_window",
            _args(1),
        ),
        "get_applications",
    ),
    _CountFree(
        _Route(
            f"/api/v1/t/{SLUG}/harvest/plants/p1/observations",
            deps.get_harvest_service,
            "get_observations_window",
            _args(1),
        ),
        "get_observations",
    ),
    _CountFree(
        _Route(f"/api/v1/t/{SLUG}/harvest/batches", deps.get_harvest_service, "list_batches_window", _args(0)),
        "list_batches",
    ),
    _CountFree(
        _Route(
            f"/api/v1/t/{SLUG}/plant-instances/p1/diary",
            deps.get_plant_diary_service,
            "list_entries_for_plant_window",
            _kw,
        ),
        "list_entries_for_plant",
    ),
    _CountFree(
        _Route(
            f"/api/v1/t/{SLUG}/planting-runs/r1/plants/p1/diary",
            deps.get_plant_diary_service,
            "list_entries_for_plant_window",
            _kw,
        ),
        "list_entries_for_plant",
    ),
    _CountFree(
        _Route(
            f"/api/v1/t/{SLUG}/planting-runs/r1/diary",
            deps.get_plant_diary_service,
            "list_entries_for_run_window",
            _kw,
        ),
        "list_entries_for_run",
    ),
    _CountFree(
        _Route(f"/api/v1/t/{SLUG}/post-harvest", deps.get_post_harvest_service, "list_batches_window", _kw),
        "list_batches",
    ),
    _CountFree(
        _Route(f"/api/v1/t/{SLUG}/propagation/events", deps.get_propagation_service, "list_events_window", _kw),
        "list_events",
    ),
    _CountFree(
        _Route(f"/api/v1/t/{SLUG}/propagation/batches", deps.get_propagation_service, "list_batches_window", _kw),
        "list_batches",
    ),
    _CountFree(
        _Route(f"/api/v1/t/{SLUG}/tasks", deps.get_task_service, "list_tasks_window", _args(0)),
        "list_tasks",
    ),
    _CountFree(
        _Route(f"/api/v1/t/{SLUG}/planting-runs", deps.get_planting_run_service, "list_runs_window", _args(0)),
        "list_runs",
    ),
    _CountFree(
        _Route("/api/v1/import/jobs", deps.get_import_service, "list_jobs_window", _args(0)),
        "list_jobs",
    ),
]

#: The fourth conversion round (#2131): the fifteen routes the discard guard had
#: classified as catalogue / tenant configuration. Cheap counts are still counts —
#: and the classification was the only thing keeping a new sibling from joining.
#: ``(route, counted sibling, the window reads the caller's tenant)``.
_CATALOGUE_AND_CONFIG = [
    (
        _Route("/api/v1/activities", deps.get_activity_service, "list_activities_window", _args(0)),
        "list_activities",
        True,
    ),
    (
        _Route(f"/api/v1/t/{SLUG}/fertilizers", deps.get_fertilizer_service, "list_fertilizers_window", _args(0)),
        "list_fertilizers",
        True,
    ),
    (
        _Route(f"/api/v1/t/{SLUG}/harvest/indicators", deps.get_harvest_service, "list_indicators_window", _args(0)),
        "list_indicators",
        False,
    ),
    (_Route("/api/v1/ipm/pests", deps.get_ipm_service, "list_pests_window", _args(0)), "list_pests", False),
    (_Route("/api/v1/ipm/diseases", deps.get_ipm_service, "list_diseases_window", _args(0)), "list_diseases", False),
    (
        _Route("/api/v1/ipm/treatments", deps.get_ipm_service, "list_treatments_window", _args(0)),
        "list_treatments",
        False,
    ),
    (
        _Route(f"/api/v1/t/{SLUG}/nutrient-plans", deps.get_nutrient_plan_service, "list_plans_window", _args(0)),
        "list_plans",
        True,
    ),
    (
        _Route(
            f"/api/v1/t/{SLUG}/overwintering-profiles",
            deps.get_overwintering_profile_service,
            "list_profiles_window",
            _args(0),
        ),
        "list_profiles",
        True,
    ),
    (
        _Route("/api/v1/phase-definitions", deps.get_phase_sequence_service, "list_definitions_window", _args(0)),
        "list_definitions",
        False,
    ),
    (
        _Route("/api/v1/phase-sequences", deps.get_phase_sequence_service, "list_sequences_window", _args(0)),
        "list_sequences",
        False,
    ),
    (
        _Route(f"/api/v1/t/{SLUG}/propagation/protocols", deps.get_propagation_service, "list_protocols_window", _kw),
        "list_protocols",
        True,
    ),
    (_Route(f"/api/v1/t/{SLUG}/sites", deps.get_site_service, "list_sites_window", _args(0)), "list_sites", True),
    (
        _Route(f"/api/v1/t/{SLUG}/succession-plans", deps.get_succession_plan_service, "list_plans_window", _args(0)),
        "list_plans",
        True,
    ),
    (_Route(f"/api/v1/t/{SLUG}/tanks", deps.get_tank_service, "list_tanks_window", _args(0)), "list_tanks", True),
    (
        _Route(f"/api/v1/t/{SLUG}/tasks/workflows", deps.get_task_service, "list_workflow_templates_window", _args(0)),
        "list_workflow_templates",
        True,
    ),
]
_COUNT_FREE += [_CountFree(route, counted) for route, counted, _ in _CATALOGUE_AND_CONFIG]
_TENANT_WINDOWS = [route for route, _, tenant_bound in _CATALOGUE_AND_CONFIG if tenant_bound]

_ALL = _OFFSET_ROUTES + _CURSOR_ROUTES + [c.route for c in _COUNT_FREE]


def _returning(service: MagicMock) -> Callable[[], MagicMock]:
    # A closure, not ``lambda service=service: ...``: FastAPI reads a defaulted
    # parameter as a query parameter and hands the handler a *copy* of the mock.
    def provide() -> MagicMock:
        return service

    return provide


@pytest.fixture
def client() -> Iterator[tuple[TestClient, dict[Any, MagicMock]]]:
    with patch("app.main.get_connection"), patch("app.main.ensure_collections"):
        from app.main import app

    services: dict[Any, MagicMock] = {}
    for route in _ALL:
        service = services.setdefault(route.provider, MagicMock())
        getattr(service, route.method).return_value = []
        app.dependency_overrides[route.provider] = _returning(service)
    app.dependency_overrides[get_current_tenant] = _ctx
    app.dependency_overrides[get_active_tenant_context] = _ctx
    app.dependency_overrides[get_active_tenant_key] = lambda: TENANT_KEY
    # The import router authenticates at router level before the tenant context.
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(key="user_lisa")
    # The diary routes resolve the plant / run against the tenant first; a mock answers.
    for provider in (deps.get_plant_instance_service, deps.get_planting_run_service):
        services.setdefault(provider, MagicMock())
        app.dependency_overrides[provider] = _returning(services[provider])
    # The KI router's own gate reads the tenant's AI settings; not what is tested here.
    app.dependency_overrides[require_ai_tenant_enabled] = lambda: None
    app.dependency_overrides[require_platform_admin] = lambda: SimpleNamespace(key="admin_1")
    yield TestClient(app, raise_server_exceptions=False), services


def _ids(routes: list[_Route]) -> list[str]:
    return [r.url.rsplit("/", 2)[-2] + "/" + r.url.rsplit("/", 1)[-1] for r in routes]


@pytest.mark.parametrize("route", _ALL, ids=_ids(_ALL))
def test_no_parameters_read_the_first_fifty_rows(client, route: _Route) -> None:
    test_client, services = client
    response = test_client.get(route.url)

    assert response.status_code == 200, response.text
    assert response.json() == []
    assert route.window(getattr(services[route.provider], route.method).call_args) == (0, 50)


@pytest.mark.parametrize("route", _ALL, ids=_ids(_ALL))
def test_the_requested_window_reaches_the_service(client, route: _Route) -> None:
    test_client, services = client
    response = test_client.get(route.url, params={"offset": 4, "limit": 3})

    assert response.status_code == 200, response.text
    assert route.window(getattr(services[route.provider], route.method).call_args) == (4, 3)


@pytest.mark.parametrize("route", _ALL, ids=_ids(_ALL))
def test_a_limit_past_the_cap_is_refused(client, route: _Route) -> None:
    test_client, services = client
    response = test_client.get(route.url, params={"limit": 201})

    assert response.status_code == 422, response.text
    getattr(services[route.provider], route.method).assert_not_called()


@pytest.mark.parametrize("route", _CURSOR_ROUTES, ids=_ids(_CURSOR_ROUTES))
def test_the_cursor_reaches_the_service(client, route: _Route) -> None:
    test_client, services = client
    response = test_client.get(route.url, params={"after": "12345", "limit": 2})

    assert response.status_code == 200, response.text
    call = getattr(services[route.provider], route.method).call_args
    assert call.kwargs["after"] == "12345"
    assert call.kwargs["tenant_key"] == TENANT_KEY
    assert _kw(call) == (0, 2)


@pytest.mark.parametrize("route", _CURSOR_ROUTES, ids=_ids(_CURSOR_ROUTES))
@pytest.mark.parametrize(
    "params",
    [{"after": "12345", "offset": 1}, {"after": "has space"}, {"after": ""}, {"after": "x" * 255}],
    ids=["with-offset", "outside-key-alphabet", "empty", "too-long"],
)
def test_an_unusable_cursor_is_refused(client, route: _Route, params: dict[str, Any]) -> None:
    test_client, services = client
    response = test_client.get(route.url, params=params)

    assert response.status_code == 422, response.text
    assert response.json()["error_code"] == "VALIDATION_ERROR"
    getattr(services[route.provider], route.method).assert_not_called()


@pytest.mark.parametrize("entry", _COUNT_FREE, ids=_ids([c.route for c in _COUNT_FREE]))
def test_a_count_free_route_never_calls_its_counted_sibling(client, entry: _CountFree) -> None:
    """The window is read without the ``total`` the counted method pays a second scan for."""
    test_client, services = client
    response = test_client.get(entry.route.url, params={"offset": 2, "limit": 5})

    assert response.status_code == 200, response.text
    service = services[entry.route.provider]
    assert entry.route.window(getattr(service, entry.route.method).call_args) == (2, 5)
    getattr(service, entry.counted).assert_not_called()


@pytest.mark.parametrize("route", _TENANT_WINDOWS, ids=_ids(_TENANT_WINDOWS))
def test_a_tenant_window_reads_the_callers_tenant(client, route: _Route) -> None:
    """The count-free window is a new read path: it must carry the tenant the counted one did."""
    test_client, services = client
    response = test_client.get(route.url)

    assert response.status_code == 200, response.text
    assert getattr(services[route.provider], route.method).call_args.kwargs["tenant_key"] == TENANT_KEY
