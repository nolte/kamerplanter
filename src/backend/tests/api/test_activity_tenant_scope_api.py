"""GET /api/v1/activities is a hybrid-catalogue read — own ∪ global, end to end (#2119, MT-023).

``Activity`` declares ``tenant_key`` and the catalogue may hold a tenant's own
rows (v0076 indexes them per tenant, the tenant erasure deletes them). The list
and by-key routes used to read every row of every tenant. They now resolve the
caller's active tenant with :func:`get_active_tenant_key` and the repository
filters with the shared ``tenant_union_predicate``.

Exercised through the real router, the real :class:`ActivityService` and the real
:class:`ArangoActivityRepository`. The database double applies the tenant arm the
query **actually** carries (and refuses a query without one), so a route that
stopped threading the tenant fails here rather than reading every row.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.activities.router import router as activities_router
from app.common.auth import get_active_tenant_key, get_current_user
from app.common.dependencies import get_activity_service
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError
from app.data_access.arango.activity_repository import ArangoActivityRepository
from app.domain.services.activity_service import ActivityService
from tests.support.tenant_replay import apply_predicates

_UNION_ARM = '(doc.tenant_key == @tenant_key OR doc.tenant_key == "" OR doc.tenant_key == null)'

_ROWS: dict[str, dict[str, Any]] = {
    "global": {"_key": "global", "name": "Topping", "tenant_key": "", "category": "training_hst"},
    "own": {"_key": "own", "name": "Own LST", "tenant_key": "tenant-a", "category": "training_lst"},
    "foreign": {"_key": "foreign", "name": "Foreign LST", "tenant_key": "tenant-b", "category": "training_lst"},
}


class _CatalogueAql:
    """Answers the activity list/count queries by the predicates they carry.

    The tenant union is an ``OR`` the small replay parser does not read, so it is
    applied here and cut out of the text; every other ``doc.<field> == @<bind>``
    (the category filter) is replayed by :func:`apply_predicates`.
    """

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        bind_vars = bind_vars or {}
        assert _UNION_ARM in query, f"activity read without the tenant union: {query}"
        rows = [r for r in _ROWS.values() if r["tenant_key"] in (bind_vars["tenant_key"], "", None)]
        rows = apply_predicates(rows, query.replace(_UNION_ARM, ""), bind_vars)
        if "COLLECT WITH COUNT" in query:
            return iter([len(rows)])
        return iter(sorted(rows, key=lambda r: r["_key"]))


def _client(*, active_tenant_key: str) -> TestClient:
    db = MagicMock()
    db.aql = _CatalogueAql()
    db.collection.return_value.get.side_effect = lambda key: _ROWS.get(key)
    service = ActivityService(ArangoActivityRepository(db))

    app = FastAPI()
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.include_router(activities_router, prefix="/api/v1")
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(key="user-1")
    app.dependency_overrides[get_activity_service] = lambda: service
    app.dependency_overrides[get_active_tenant_key] = lambda: active_tenant_key
    return TestClient(app)


def _keys(response) -> list[str]:
    assert response.status_code == 200, response.text
    return sorted(item["key"] for item in response.json())


def test_tenant_a_lists_its_own_and_the_global_activities() -> None:
    assert _keys(_client(active_tenant_key="tenant-a").get("/api/v1/activities")) == ["global", "own"]


def test_tenant_b_never_lists_tenant_a() -> None:
    assert _keys(_client(active_tenant_key="tenant-b").get("/api/v1/activities")) == ["foreign", "global"]


def test_a_caller_without_a_tenant_lists_the_global_activities_only() -> None:
    assert _keys(_client(active_tenant_key="").get("/api/v1/activities")) == ["global"]


def test_a_filtered_list_stays_tenant_scoped() -> None:
    client = _client(active_tenant_key="tenant-a")
    assert _keys(client.get("/api/v1/activities", params={"category": "training_lst"})) == ["own"]


def test_a_global_activity_is_readable_by_key() -> None:
    response = _client(active_tenant_key="tenant-a").get("/api/v1/activities/global")
    assert response.status_code == 200
    assert response.json()["key"] == "global"


def test_the_own_activity_is_readable_by_key() -> None:
    response = _client(active_tenant_key="tenant-a").get("/api/v1/activities/own")
    assert response.status_code == 200
    assert response.json()["key"] == "own"


def test_a_foreign_activity_by_key_answers_not_found() -> None:
    """404, not 403: a 403 would confirm the row exists in another tenant."""
    response = _client(active_tenant_key="tenant-a").get("/api/v1/activities/foreign")
    assert response.status_code == 404
    assert "Foreign LST" not in response.text
