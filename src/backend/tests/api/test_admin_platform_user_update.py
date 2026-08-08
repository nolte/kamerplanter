"""API tests for #1018 / #1019 — ``PATCH /admin/platform/users/{key}`` reaches
the database only through the service layer.

#1018 moved the *write* off ``get_db()`` and onto ``UserService.admin_update_user``.
#1019 moved the *roles block* too: ``update_user`` used to read the user's
memberships with raw AQL through ``get_db()``; it now routes through
``TenantService.list_user_memberships``. As a result the router no longer opens a
database handle at all — there is no ``get_db`` attribute on the module to
monkeypatch — so the test no longer needs the two-store split it once used to
tell a router write from a service write.

The user document is driven through the **real** ``ArangoUserRepository`` /
``UserService`` and a real ``User`` model over an in-memory ``StandardDatabase``
double, so a persisted value observed in ``store`` is the production path firing —
not a ``MagicMock`` that never became a model (the #996 red-for-nothing trap).
"""

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient

from app.api.v1.admin.platform import router as mod
from app.common.auth import require_platform_admin
from app.common.dependencies import get_tenant_service, get_user_service
from app.common.error_handlers import app_error_handler, validation_error_handler
from app.common.exceptions import KamerplanterError
from app.data_access.arango.user_repository import ArangoUserRepository
from app.domain.services.user_service import UserService

USER_KEY = "u-1"
ORIGINAL_NAME = "Alice Grower"
ORIGINAL_EMAIL = "alice@example.com"


def _user_doc() -> dict[str, Any]:
    """A valid, complete stored user document."""
    return {
        "_key": USER_KEY,
        "_id": f"users/{USER_KEY}",
        "email": ORIGINAL_EMAIL,
        "display_name": ORIGINAL_NAME,
        "password_hash": "hash",
        "email_verified": True,
        "is_active": True,
        "account_type": "user",
        "locale": "de",
        "timezone": "Europe/Berlin",
        "last_login_at": None,
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
    }


class _FakeCollection:
    """The subset of ``StandardCollection`` this flow touches, over a dict store."""

    def __init__(self, store: dict[str, dict[str, Any]], writes: list[str]) -> None:
        self._store = store
        self._writes = writes

    def get(self, key: str) -> dict[str, Any] | None:
        doc = self._store.get(key)
        return dict(doc) if doc is not None else None

    def has(self, key: str) -> bool:
        return key in self._store

    def update(
        self,
        document: dict[str, Any],
        return_new: bool = False,
        keep_none: bool = True,
    ) -> dict[str, Any]:
        key = document["_key"]
        self._writes.append(key)
        stored = self._store[key]
        patch = {field: value for field, value in document.items() if field != "_key"}
        if not keep_none:
            patch = {field: value for field, value in patch.items() if value is not None}
        stored.update(patch)
        return {"new": dict(stored)} if return_new else {"_key": key}


class _FakeAql:
    """The repository's user lookups emit no AQL on this flow; answer empty."""

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        return iter([])


class _FakeDb:
    def __init__(self, store: dict[str, dict[str, Any]], writes: list[str]) -> None:
        self._store = store
        self._writes = writes
        self.aql = _FakeAql()

    def collection(self, _name: str) -> _FakeCollection:
        return _FakeCollection(self._store, self._writes)


@pytest.fixture
def store() -> dict[str, dict[str, Any]]:
    return {USER_KEY: _user_doc()}


@pytest.fixture
def writes() -> list[str]:
    return []


@pytest.fixture
def client(
    store: dict[str, dict[str, Any]],
    writes: list[str],
) -> TestClient:
    service_db = _FakeDb(store, writes)

    service = UserService(
        ArangoUserRepository(service_db),  # type: ignore[arg-type]
        MagicMock(),
    )

    # #1019: the roles block now routes through TenantService; no memberships are
    # needed to exercise the write path, so the double returns an empty list.
    tenant_service = MagicMock()
    tenant_service.list_user_memberships.return_value = []

    app = FastAPI()
    app.include_router(mod.router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[require_platform_admin] = lambda: SimpleNamespace(key="admin-1")
    app.dependency_overrides[get_user_service] = lambda: service
    app.dependency_overrides[get_tenant_service] = lambda: tenant_service
    return TestClient(app)


def _patch(client: TestClient, payload: dict[str, Any]):
    return client.patch(f"/api/v1/admin/platform/users/{USER_KEY}", json=payload)


# ── #1019: the router no longer reaches Persistence itself ────────────────────


class TestRoutesThroughTheServiceLayer:
    """NFR-001 — the router talks to services, never to ``get_db``."""

    def test_router_module_holds_no_database_handle(self):
        """The structural guarantee: with every path routed, the router module has
        no ``get_db`` to reach Persistence through (enforced by
        ``check_layer_imports`` for the import, asserted here for the symbol)."""
        assert not hasattr(mod, "get_db")

    def test_write_lands_in_the_service_store(self, client, store, writes):
        response = _patch(client, {"display_name": "Alice Renamed"})

        assert response.status_code == 200
        assert writes == [USER_KEY]
        assert store[USER_KEY]["display_name"] == "Alice Renamed"

    def test_response_reflects_the_persisted_value(self, client):
        response = _patch(client, {"display_name": "Alice Renamed"})

        assert response.status_code == 200
        assert response.json()["display_name"] == "Alice Renamed"


# ── Existing platform-admin behaviour: green before and after ────────────────


class TestExistingBehaviourIsPreserved:
    def test_updates_display_name_and_flags(self, client, store):
        response = _patch(
            client,
            {"display_name": "Alice Renamed", "is_active": False, "email_verified": False},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["display_name"] == "Alice Renamed"
        assert body["is_active"] is False
        assert body["email_verified"] is False
        assert store[USER_KEY]["display_name"] == "Alice Renamed"
        assert store[USER_KEY]["is_active"] is False

    def test_empty_payload_leaves_the_user_untouched(self, client, store, writes):
        response = _patch(client, {})

        assert response.status_code == 200
        assert response.json()["display_name"] == ORIGINAL_NAME
        assert writes == []
        assert store[USER_KEY] == _user_doc()

    def test_unknown_user_returns_404(self, client, store):
        response = client.patch(
            "/api/v1/admin/platform/users/ghost",
            json={"display_name": "Nobody"},
        )

        assert response.status_code == 404
        assert store[USER_KEY] == _user_doc()

    def test_schema_rejects_an_empty_display_name(self, client, store):
        """``AdminUserUpdate.display_name`` carries ``min_length=1``.

        Empty and over-length values are refused at the FastAPI boundary (422),
        which is why #1018 is drift rather than a live value defect — see the
        module docstring. The check has to keep working after the routing move.
        """
        response = _patch(client, {"display_name": ""})

        assert response.status_code == 422
        assert store[USER_KEY]["display_name"] == ORIGINAL_NAME


# ── #1035: whitespace-only display_name must be refused, not persisted ────────


class TestRejectsWhitespaceOnlyDisplayName:
    """#1035 — ``min_length=1`` is length-based, so ``"   "`` passed the boundary
    *and* the model and was persisted. The admin path is one of the shared write
    paths that must now refuse it with 422 and leave the stored value untouched.

    Red-first: against the pre-fix schema this returned 200 and the whitespace
    landed in ``store``; after the shared ``DisplayName`` validator it is 422 at
    the boundary.
    """

    @pytest.mark.parametrize("value", [" ", "   ", "\t", " \t "])
    def test_whitespace_only_is_refused_and_not_persisted(self, client, store, writes, value):
        response = _patch(client, {"display_name": value})

        assert response.status_code == 422
        assert writes == []
        assert store[USER_KEY]["display_name"] == ORIGINAL_NAME

    def test_name_with_internal_spaces_is_still_accepted(self, client, store):
        """The positive that catches an over-broad validator: internal spaces are
        legitimate and must be stored verbatim (reject-only, not normalise)."""
        response = _patch(client, {"display_name": "Bob Smith"})

        assert response.status_code == 200
        assert store[USER_KEY]["display_name"] == "Bob Smith"
