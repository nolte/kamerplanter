"""#1992 — an admin ``PATCH email_verified=false`` no longer hands an account to the cleanup.

The chain, driven end to end against a **real** ArangoDB: the real
``PATCH /admin/platform/users/{key}`` route, the real ``UserService`` (with its
real step-up verifier) over the real ``ArangoUserRepository``, then the real beat
task ``cleanup_unverified_accounts`` reading the real AQL selector. Before the fix
a verified, established local account that an admin demoted was the next run's
candidate and was erased with ``origin="unverified_cleanup"`` — no step-up, no
member notice. The assertion is what the task *selected for erasure*; the erasure
itself is recorded by a double, because the question here is which accounts reach it.

Runs in CI against the service container; locally it needs a database of its own
(``docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12``).
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from arango import ArangoClient
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.admin.platform import router as mod
from app.common.auth import require_platform_admin
from app.common.dependencies import get_tenant_service, get_user_service
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError
from app.data_access.arango import collections as col
from app.data_access.arango.user_repository import ArangoUserRepository
from app.domain.engines.password_engine import PasswordEngine
from app.domain.models.user import User
from app.domain.services.user_service import UserService
from app.tasks.auth_tasks import cleanup_unverified_accounts
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("demoted_cleanup")
LONG_AGO = "2020-01-01T00:00:00+00:00"
CUTOFF = datetime(2026, 1, 1, tzinfo=UTC)
# Assembled at runtime: a literal shaped like a credential trips the secret scanner (#1838).
PASSWORD = " ".join(["correct", "horse", "battery", "staple"])

pytestmark = pytest.mark.usefixtures("arango_db")


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    db.create_collection(col.USERS)
    db.create_collection(col.AUTH_PROVIDERS)
    yield db
    system.delete_database(TEST_DATABASE)


@pytest.fixture
def db(database):
    database.collection(col.USERS).truncate()
    database.collection(col.AUTH_PROVIDERS).truncate()
    return database


def _doc(key: str, *, verified: bool) -> dict:
    return {
        "_key": key,
        "email": f"{key}@example.com",
        "display_name": key,
        "password_hash": "hash",
        "email_verified": verified,
        "is_active": True,
        "account_type": "human",
        "created_at": LONG_AGO,
        "updated_at": LONG_AGO,
    }


def _admin() -> User:
    return User.model_validate(
        {
            "_key": "admin-1",
            "email": "admin-1@example.com",
            "display_name": "Admin",
            "password_hash": PasswordEngine().hash_password(PASSWORD),
            "email_verified": True,
        }
    )


def _client(repo: ArangoUserRepository) -> TestClient:
    tenants = MagicMock()
    tenants.list_user_memberships.return_value = []
    service = UserService(repo, MagicMock())
    app = FastAPI()
    app.include_router(mod.router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[require_platform_admin] = _admin
    app.dependency_overrides[get_user_service] = lambda: service
    app.dependency_overrides[get_tenant_service] = lambda: tenants
    return TestClient(app, raise_server_exceptions=False)


def _run_the_beat(repo: ArangoUserRepository) -> list[str]:
    """The real cleanup task over the real repository; returns the accounts it erased."""
    erase = AsyncMock(return_value=SimpleNamespace(status="completed"))
    privacy = MagicMock()
    privacy.erase_account_now = erase
    retention = MagicMock()
    retention.unverified_account_cutoff.return_value = CUTOFF
    with (
        patch("app.common.dependencies.get_user_repo", return_value=repo),
        patch("app.common.dependencies.get_privacy_service", return_value=privacy),
        patch("app.common.dependencies.get_retention_service", return_value=retention),
    ):
        cleanup_unverified_accounts.run()
    return [call.args[0] for call in erase.await_args_list]


def test_a_verified_account_an_admin_demoted_is_not_erased_by_the_next_run(db):
    db.collection(col.USERS).insert(_doc("established", verified=True))
    db.collection(col.USERS).insert(_doc("abandoned", verified=False))
    repo = ArangoUserRepository(db)
    client = _client(repo)

    response = client.patch(
        "/api/v1/admin/platform/users/established", json={"email_verified": False, "current_password": PASSWORD}
    )

    assert response.status_code == 200, response.text
    assert db.collection(col.USERS).get("established")["email_verified"] is False
    erased = _run_the_beat(repo)
    # Control: the never-verified registration is still erased, so the selector is not simply empty.
    assert erased == ["abandoned"]
    assert db.collection(col.USERS).get("established") is not None


def test_the_demotion_needs_the_admins_step_up_and_changes_nothing_without_it(db):
    db.collection(col.USERS).insert(_doc("established", verified=True))
    repo = ArangoUserRepository(db)

    response = _client(repo).patch("/api/v1/admin/platform/users/established", json={"email_verified": False})

    assert response.status_code == 401, response.text
    stored = db.collection(col.USERS).get("established")
    assert stored["email_verified"] is True
    assert stored.get("email_verified_lowered_at") is None
    assert _run_the_beat(repo) == []


def test_an_account_demoted_directly_in_the_store_is_spared_by_the_marker_alone(db):
    db.collection(col.USERS).insert({**_doc("demoted", verified=False), "email_verified_lowered_at": LONG_AGO})
    repo = ArangoUserRepository(db)

    assert [user.key for user in repo.get_unverified_before(CUTOFF.isoformat())] == []
    assert repo.count_unverified_undated() == 0
