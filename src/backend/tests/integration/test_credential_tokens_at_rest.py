"""#2158: the password-reset and e-mail-verification tokens are not readable off the stored account.

Measured before the change: ``AuthService.register_local`` and
``request_password_reset`` wrote the raw token into ``users`` and the lookups
matched it by value, so anyone with read access to the database or a backup held a
working reset link (1 h) or verification link (24 h) for the accounts that had one
pending.

Driven through the real ``AuthService`` over the real ``ArangoUserRepository``; the
raw token is taken from the mail the service hands to the e-mail adapter (the only
place it may go) and searched for in the stored document as the server returns it.
The legacy half runs the migration over a document written the old way and proves
the link mailed before the upgrade still works once, and only once.

Runs in CI against the service container; locally it needs a database of its own
(``docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12``).
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from arango import ArangoClient

from app.common.exceptions import InvalidTokenError
from app.data_access.arango import collections as col
from app.data_access.arango.auth_provider_repository import ArangoAuthProviderRepository
from app.data_access.arango.user_repository import ArangoUserRepository
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.services.auth_service import AuthService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("credential_tokens_at_rest")
# Assembled at runtime: a literal shaped like a credential trips the secret scanner (#1838).
PASSWORD = " ".join(["Correct", "horse", "battery", "staple", "9!"])
NEW_PASSWORD = " ".join(["Another", "horse", "battery", "staple", "7?"])
ADDRESS = "owner@example.org"

pytestmark = pytest.mark.usefixtures("arango_db")


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    from app.data_access.arango.collections import ensure_collections

    ensure_collections(db)
    yield db
    system.delete_database(TEST_DATABASE)


@pytest.fixture
def db(database):
    for name in (col.USERS, col.AUTH_PROVIDERS):
        database.collection(name).truncate()
    return database


def _service(db, mail: MagicMock) -> AuthService:
    return AuthService(
        user_repo=ArangoUserRepository(db),
        auth_provider_repo=ArangoAuthProviderRepository(db),
        refresh_token_repo=MagicMock(),
        password_engine=PasswordEngine(),
        token_engine=TokenEngine("x" * 64),
        throttle_engine=LoginThrottleEngine(),
        email_service=mail,
        frontend_url="https://app.test",
        require_email_verification=True,
    )


def _stored(db) -> dict:
    (doc,) = list(db.collection(col.USERS).all())
    return doc


def _sha256(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def test_the_verification_token_is_stored_as_its_hash_and_still_verifies(db) -> None:
    mail = MagicMock()
    service = _service(db, mail)

    service.register_local(ADDRESS, PASSWORD, "Owner")
    raw = mail.send_verification_email.call_args.kwargs["token"]
    stored = _stored(db)

    assert raw not in json.dumps(stored)
    assert stored["email_verification_token_hash"] == _sha256(raw)
    assert "email_verification_token" not in stored

    profile = service.verify_email(raw)

    assert profile.email_verified is True
    assert _stored(db).get("email_verification_token_hash") is None  # burnt
    with pytest.raises(InvalidTokenError):
        service.verify_email(raw)  # single use


def test_the_stored_hash_is_not_itself_a_working_verification_token(db) -> None:
    mail = MagicMock()
    service = _service(db, mail)
    service.register_local(ADDRESS, PASSWORD, "Owner")

    with pytest.raises(InvalidTokenError):
        service.verify_email(_stored(db)["email_verification_token_hash"])


def test_the_reset_token_is_stored_as_its_hash_and_still_resets_once(db) -> None:
    mail = MagicMock()
    service = _service(db, mail)
    service.register_local(ADDRESS, PASSWORD, "Owner")

    service.request_password_reset(ADDRESS, client_ip="203.0.113.7")
    raw = mail.send_password_reset_email.call_args.kwargs["token"]
    stored = _stored(db)

    assert raw not in json.dumps(stored)
    assert stored["password_reset_token_hash"] == _sha256(raw)
    assert "password_reset_token" not in stored
    with pytest.raises(InvalidTokenError):
        service.reset_password(stored["password_reset_token_hash"], NEW_PASSWORD)

    service.reset_password(raw, NEW_PASSWORD)

    assert PasswordEngine().verify_password(NEW_PASSWORD, _stored(db)["password_hash"])
    with pytest.raises(InvalidTokenError):
        service.reset_password(raw, NEW_PASSWORD)  # single use


def test_the_migration_hashes_a_link_mailed_before_the_upgrade(db) -> None:
    """A document written the pre-#2158 way: both tokens in clear, the reset one still inside its hour."""
    from app.migrations.versions.v0086_hash_account_tokens import HashAccountTokensMigration

    reset_raw = "legacy-reset-" + "r" * 30
    verify_raw = "legacy-verify-" + "v" * 29
    db.collection(col.USERS).insert(
        {
            "_key": "legacy",
            "email": ADDRESS,
            "display_name": "Owner",
            "password_hash": PasswordEngine().hash_password(PASSWORD),
            "email_verified": False,
            "is_active": True,
            "account_type": "human",
            "password_reset_token": reset_raw,
            "password_reset_expires": (datetime.now(UTC) + timedelta(minutes=30)).isoformat(),
            "email_verification_token": verify_raw,
            "email_verification_expires": (datetime.now(UTC) + timedelta(hours=20)).isoformat(),
        }
    )
    db.collection(col.USERS).insert(
        {"_key": "plain", "email": "plain@example.org", "display_name": "P", "is_active": True}
    )
    migration = HashAccountTokensMigration()

    dry = migration.up(db, dry_run=True)
    assert (dry.scanned, dry.changed) == (1, 0)
    assert db.collection(col.USERS).get("legacy")["password_reset_token"] == reset_raw

    report = migration.up(db)
    legacy = db.collection(col.USERS).get("legacy")

    assert report.changed == 1
    assert reset_raw not in json.dumps(legacy) and verify_raw not in json.dumps(legacy)
    assert "password_reset_token" not in legacy and "email_verification_token" not in legacy
    assert legacy["password_reset_token_hash"] == _sha256(reset_raw)
    assert legacy["email_verification_token_hash"] == _sha256(verify_raw)
    assert "password_reset_token_hash" not in db.collection(col.USERS).get("plain")
    assert migration.up(db).changed == 0  # idempotent

    service = _service(db, MagicMock())
    service.reset_password(reset_raw, NEW_PASSWORD)
    with pytest.raises(InvalidTokenError):
        service.reset_password(reset_raw, NEW_PASSWORD)
    assert service.verify_email(verify_raw).email_verified is True
