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
    # No second argument: the default is the real step-up verifier, which is what this
    # test measures. A positional mock here would become the verifier (the former
    # second parameter, `refresh_token_repo`, is gone since #2013) and enforce nothing.
    service = UserService(repo)
    app = FastAPI()
    app.include_router(mod.router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[require_platform_admin] = _admin
    app.dependency_overrides[get_user_service] = lambda: service
    app.dependency_overrides[get_tenant_service] = lambda: tenants
    return TestClient(app, raise_server_exceptions=False)


def _run_the_beat_with_result(repo: ArangoUserRepository, *, reap_local: bool = False) -> tuple[list[str], dict]:
    """The real cleanup task over the real repository; the accounts it erased and its report."""
    erase = AsyncMock(return_value=SimpleNamespace(status="completed"))
    privacy = MagicMock()
    privacy.erase_account_now = erase
    retention = MagicMock()
    retention.unverified_account_cutoff.return_value = CUTOFF
    retention.unverified_local_reap_enabled = reap_local
    with (
        patch("app.common.dependencies.get_user_repo", return_value=repo),
        patch("app.common.dependencies.get_privacy_service", return_value=privacy),
        patch("app.common.dependencies.get_retention_service", return_value=retention),
    ):
        result = cleanup_unverified_accounts.run()
    return [call.args[0] for call in erase.await_args_list], result


def _run_the_beat(repo: ArangoUserRepository) -> list[str]:
    """The real cleanup task over the real repository; returns the accounts it erased."""
    return _run_the_beat_with_result(repo)[0]


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


def test_an_account_that_ever_signed_in_is_spared_even_without_a_marker(db):
    """A demotion made before the marker existed left no record; ``last_login_at`` is the second signal."""
    db.collection(col.USERS).insert({**_doc("in-use", verified=False), "last_login_at": LONG_AGO})
    db.collection(col.USERS).insert(_doc("abandoned", verified=False))

    erased = [user.key for user in ArangoUserRepository(db).get_unverified_before(CUTOFF.isoformat())]

    assert erased == ["abandoned"]


def test_a_locally_registered_account_is_not_selected_at_all_today(db):
    """The DEFAULT selector (#2010): registration writes a LOCAL ``auth_providers`` row, and this selector
    counts *any* provider row as linked, so it still reaches provider-less accounts only. The widened
    selector below (``include_local_registrations=True``) is what the operator releases after the dry run;
    until then this default stays what it was, and the task only counts what the widened one would erase."""
    db.collection(col.USERS).insert(_doc("registered", verified=False))
    db.collection(col.AUTH_PROVIDERS).insert(
        {"_key": "local-registered", "user_key": "registered", "provider": "local", "provider_user_id": "registered"}
    )

    assert ArangoUserRepository(db).get_unverified_before(CUTOFF.isoformat()) == []


def _provider(db, user: str, provider: str) -> None:
    db.collection(col.AUTH_PROVIDERS).insert(
        {"_key": f"{provider}-{user}", "user_key": user, "provider": provider, "provider_user_id": user}
    )


def _seed_the_local_registration_class(db) -> None:
    """One account per member of the class the widened selector must tell apart."""
    users = db.collection(col.USERS)
    users.insert(_doc("registered", verified=False))  # local only: the abandoned registration
    users.insert(_doc("seed", verified=False))  # provider-less: reached by the default selector too
    users.insert(_doc("linked", verified=False))  # local + federated: someone can sign in with Google
    users.insert(_doc("federated", verified=False))  # federated only
    users.insert({**_doc("in-use", verified=False), "last_login_at": LONG_AGO})
    users.insert({**_doc("demoted", verified=False), "email_verified_lowered_at": LONG_AGO})
    users.insert({**_doc("machine", verified=False), "account_type": "service"})
    users.insert({**_doc("young", verified=False), "created_at": "2030-01-01T00:00:00+00:00"})
    users.insert({**_doc("undated", verified=False), "created_at": "not a date"})
    for user in ("registered", "linked", "in-use", "demoted", "machine", "young", "undated"):
        _provider(db, user, "local")
    _provider(db, "linked", "google")
    _provider(db, "federated", "github")


def test_the_widened_selector_reaches_a_local_registration_and_nothing_a_person_can_still_use(db):
    _seed_the_local_registration_class(db)
    repo = ArangoUserRepository(db)

    default = sorted(user.key for user in repo.get_unverified_before(CUTOFF.isoformat()))
    widened = sorted(
        user.key for user in repo.get_unverified_before(CUTOFF.isoformat(), include_local_registrations=True)
    )

    assert default == ["seed"]
    assert widened == ["registered", "seed"]


def test_the_dry_run_counts_exactly_what_the_widening_adds(db):
    _seed_the_local_registration_class(db)
    repo = ArangoUserRepository(db)

    assert repo.count_unverified_local_registrations_before(CUTOFF.isoformat()) == 1


def test_the_held_counter_follows_the_selector_it_belongs_to(db):
    _seed_the_local_registration_class(db)
    repo = ArangoUserRepository(db)

    assert repo.count_unverified_undated() == 0, "the default selector never saw the local-only account"
    assert repo.count_unverified_undated(include_local_registrations=True) == 1


def test_the_beat_counts_but_erases_no_local_registration_until_the_operator_releases_it(db):
    _seed_the_local_registration_class(db)
    repo = ArangoUserRepository(db)

    erased, result = _run_the_beat_with_result(repo)

    assert erased == ["seed"]
    assert result["local_registrations_pending"] == 1
    assert db.collection(col.USERS).get("registered") is not None


def test_a_released_run_erases_the_local_registration_too(db):
    _seed_the_local_registration_class(db)
    repo = ArangoUserRepository(db)

    erased, result = _run_the_beat_with_result(repo, reap_local=True)

    assert sorted(erased) == ["registered", "seed"]
    assert result["local_registrations_pending"] == 1
