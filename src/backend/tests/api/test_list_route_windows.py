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
from app.common.auth import get_current_tenant, require_platform_admin
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
]

_CURSOR_ROUTES = [
    _Route(f"/api/v1/t/{SLUG}/plant-instances", deps.get_plant_instance_service, "list_plants_window", _kw),
    _Route(f"/api/v1/t/{SLUG}/watering-logs", deps.get_watering_log_service, "list_logs_window", _kw),
    _Route(f"/api/v1/t/{SLUG}/feeding-events", deps.get_feeding_service, "list_events_window", _kw),
    _Route(f"/api/v1/t/{SLUG}/watering-events", deps.get_watering_service, "list_events_window", _kw),
]

_ALL = _OFFSET_ROUTES + _CURSOR_ROUTES


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
