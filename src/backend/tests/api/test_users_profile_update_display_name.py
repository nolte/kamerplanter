"""API tests for #1035 — the self-service profile update
(``PATCH /users/me``) must refuse a whitespace-only ``display_name`` with 422 and
never persist it.

``min_length=1`` is length-based, so ``"   "`` passed the boundary, the
``UserProfileUpdate`` model and the ``User`` re-validation, and was stored. This
wires the endpoint to the **real** :class:`UserService` /
:class:`ArangoUserRepository` over an in-memory document store and drives a real
``User`` model, so a persisted value observed here is the production path firing —
not a mock that never becomes a model (#996). Red-first: against the pre-fix
schema the whitespace was returned (200) and stored; after the shared
``DisplayName`` validator it is 422.
"""

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient

from app.api.v1.users import router as mod
from app.common.auth import get_current_user
from app.common.dependencies import get_user_service
from app.common.error_handlers import app_error_handler, validation_error_handler
from app.common.exceptions import KamerplanterError
from app.data_access.arango.user_repository import ArangoUserRepository
from app.domain.services.user_service import UserService

USER_KEY = "u-1"
ORIGINAL_NAME = "Alice Grower"
ORIGINAL_EMAIL = "alice@example.com"


def _user_doc() -> dict[str, Any]:
    return {
        "_key": USER_KEY,
        "_id": f"users/{USER_KEY}",
        "email": ORIGINAL_EMAIL,
        "display_name": ORIGINAL_NAME,
        "password_hash": "hash",
        "email_verified": True,
        "is_active": True,
        "account_type": "user",
        "avatar_url": None,
        "locale": "de",
        "timezone": "Europe/Berlin",
        "last_login_at": None,
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
    }


class _FakeCollection:
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
def client(store: dict[str, dict[str, Any]], writes: list[str]) -> TestClient:
    db = _FakeDb(store, writes)
    service = UserService(ArangoUserRepository(db), MagicMock())  # type: ignore[arg-type]

    app = FastAPI()
    app.include_router(mod.router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(key=USER_KEY)
    app.dependency_overrides[get_user_service] = lambda: service
    return TestClient(app)


def _patch(client: TestClient, payload: dict[str, Any]):
    return client.patch("/api/v1/users/me", json=payload)


class TestSelfServiceProfileUpdate:
    def test_normal_name_is_accepted_and_persisted(self, client, store):
        response = _patch(client, {"display_name": "Alice Renamed"})

        assert response.status_code == 200
        assert response.json()["display_name"] == "Alice Renamed"
        assert store[USER_KEY]["display_name"] == "Alice Renamed"

    def test_name_with_internal_spaces_is_accepted(self, client, store):
        """Positive that catches an over-broad validator."""
        response = _patch(client, {"display_name": "Bob Smith"})

        assert response.status_code == 200
        assert store[USER_KEY]["display_name"] == "Bob Smith"

    @pytest.mark.parametrize("value", [" ", "   ", "\t", " \t "])
    def test_whitespace_only_is_refused_and_not_persisted(self, client, store, writes, value):
        response = _patch(client, {"display_name": value})

        assert response.status_code == 422
        assert writes == []
        assert store[USER_KEY]["display_name"] == ORIGINAL_NAME

    def test_empty_string_is_refused(self, client, store):
        response = _patch(client, {"display_name": ""})

        assert response.status_code == 422
        assert store[USER_KEY]["display_name"] == ORIGINAL_NAME
