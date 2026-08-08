"""API tests for #1018 — ``PATCH /admin/platform/users/{key}`` must reach the
database through the service layer, not from the router.

Same shape as #997/#1017 (the tenant twin): the router took ``get_db()`` and did
``collection.update({"_key": key, **update_data})`` itself, so Presentation wrote
straight to Persistence (NFR-001), outside the repository guards.

**Why two database handles.** Unlike the tenant endpoint, ``update_user`` still
reads the user's memberships through ``get_db()`` to build the ``roles`` block of
the response (that duplicated read is #1019, out of scope here). So the tenant
test's "the router never opens a database handle" assertion cannot apply. Instead
this test wires the router's ``get_db`` and the ``UserService`` to **separate**
stores:

* ``router_store`` — reached only through the router's ``get_db``. A direct
  ``collection.update`` from the router lands here.
* ``service_store`` — reached only through the real :class:`ArangoUserRepository`
  the :class:`UserService` wraps.

The write is expected in ``service_store``; a write recorded against
``router_store`` is the router talking to Persistence itself. The user document is
driven through the **real** ``ArangoUserRepository`` / ``UserService`` and a real
``User`` model, so a persisted value observed in ``service_store`` is the
production path firing — not a ``MagicMock`` that never became a model (the #996
red-for-nothing trap).
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
from app.common.dependencies import get_user_service
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
    """Answers the membership-roles query and the repository's list lookups."""

    def __init__(self, store: dict[str, dict[str, Any]]) -> None:
        self._store = store

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        # The only AQL this flow emits is the router's membership-roles probe.
        # No memberships are needed to exercise the write path.
        return iter([])


class _FakeDb:
    def __init__(self, store: dict[str, dict[str, Any]], writes: list[str]) -> None:
        self._store = store
        self._writes = writes
        self.aql = _FakeAql(store)

    def collection(self, _name: str) -> _FakeCollection:
        return _FakeCollection(self._store, self._writes)


@pytest.fixture
def router_store() -> dict[str, dict[str, Any]]:
    return {USER_KEY: _user_doc()}


@pytest.fixture
def service_store() -> dict[str, dict[str, Any]]:
    return {USER_KEY: _user_doc()}


@pytest.fixture
def router_writes() -> list[str]:
    return []


@pytest.fixture
def service_writes() -> list[str]:
    return []


@pytest.fixture
def client(
    router_store: dict[str, dict[str, Any]],
    service_store: dict[str, dict[str, Any]],
    router_writes: list[str],
    service_writes: list[str],
    monkeypatch: pytest.MonkeyPatch,
) -> TestClient:
    router_db = _FakeDb(router_store, router_writes)
    service_db = _FakeDb(service_store, service_writes)

    monkeypatch.setattr(mod, "get_db", lambda: router_db)

    service = UserService(
        ArangoUserRepository(service_db),  # type: ignore[arg-type]
        MagicMock(),
    )

    app = FastAPI()
    app.include_router(mod.router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[require_platform_admin] = lambda: SimpleNamespace(key="admin-1")
    app.dependency_overrides[get_user_service] = lambda: service
    return TestClient(app)


def _patch(client: TestClient, payload: dict[str, Any]):
    return client.patch(f"/api/v1/admin/platform/users/{USER_KEY}", json=payload)


# ── #1018: the write must reach the database through the service ──────────────


class TestRoutesThroughTheServiceLayer:
    """NFR-001 — the router must not write to Persistence itself.

    The router writing ``collection.update`` lands in ``router_store``; the
    service writing through :class:`ArangoUserRepository` lands in
    ``service_store``. The write belongs in the latter.
    """

    def test_write_lands_in_the_service_store_not_the_router_store(
        self, client, router_store, service_store, router_writes, service_writes
    ):
        response = _patch(client, {"display_name": "Alice Renamed"})

        assert response.status_code == 200
        # The service's repository performed the write …
        assert service_writes == [USER_KEY]
        assert service_store[USER_KEY]["display_name"] == "Alice Renamed"
        # … and the router did not reach Persistence itself.
        assert router_writes == []
        assert router_store[USER_KEY]["display_name"] == ORIGINAL_NAME

    def test_response_reflects_the_persisted_value(self, client):
        response = _patch(client, {"display_name": "Alice Renamed"})

        assert response.status_code == 200
        assert response.json()["display_name"] == "Alice Renamed"


# ── Existing platform-admin behaviour: green before and after ────────────────


class TestExistingBehaviourIsPreserved:
    def test_updates_display_name_and_flags(self, client, service_store):
        response = _patch(
            client,
            {"display_name": "Alice Renamed", "is_active": False, "email_verified": False},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["display_name"] == "Alice Renamed"
        assert body["is_active"] is False
        assert body["email_verified"] is False
        assert service_store[USER_KEY]["display_name"] == "Alice Renamed"
        assert service_store[USER_KEY]["is_active"] is False

    def test_empty_payload_leaves_the_user_untouched(self, client, service_store, service_writes):
        response = _patch(client, {})

        assert response.status_code == 200
        assert response.json()["display_name"] == ORIGINAL_NAME
        assert service_writes == []
        assert service_store[USER_KEY] == _user_doc()

    def test_unknown_user_returns_404(self, client, service_store):
        response = client.patch(
            "/api/v1/admin/platform/users/ghost",
            json={"display_name": "Nobody"},
        )

        assert response.status_code == 404
        assert service_store[USER_KEY] == _user_doc()

    def test_schema_rejects_an_empty_display_name(self, client, service_store):
        """``AdminUserUpdate.display_name`` carries ``min_length=1``.

        Empty and over-length values are refused at the FastAPI boundary (422),
        which is why #1018 is drift rather than a live value defect — see the
        module docstring. The check has to keep working after the routing move.
        """
        response = _patch(client, {"display_name": ""})

        assert response.status_code == 422
        assert service_store[USER_KEY]["display_name"] == ORIGINAL_NAME


# ── #1035: whitespace-only display_name must be refused, not persisted ────────


class TestRejectsWhitespaceOnlyDisplayName:
    """#1035 — ``min_length=1`` is length-based, so ``"   "`` passed the boundary
    *and* the model and was persisted. The admin path is one of the shared write
    paths that must now refuse it with 422 and leave the stored value untouched.

    Red-first: against the pre-fix schema this returned 200 and the whitespace
    landed in ``service_store``; after the shared ``DisplayName`` validator it is
    422 at the boundary.
    """

    @pytest.mark.parametrize("value", [" ", "   ", "\t", " \t "])
    def test_whitespace_only_is_refused_and_not_persisted(self, client, service_store, service_writes, value):
        response = _patch(client, {"display_name": value})

        assert response.status_code == 422
        assert service_writes == []
        assert service_store[USER_KEY]["display_name"] == ORIGINAL_NAME

    def test_name_with_internal_spaces_is_still_accepted(self, client, service_store):
        """The positive that catches an over-broad validator: internal spaces are
        legitimate and must be stored verbatim (reject-only, not normalise)."""
        response = _patch(client, {"display_name": "Bob Smith"})

        assert response.status_code == 200
        assert service_store[USER_KEY]["display_name"] == "Bob Smith"
