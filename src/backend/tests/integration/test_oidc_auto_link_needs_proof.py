"""An OIDC sign-in is attached to an existing account only if that account's owner proved the address.

Driven through the real ``/auth/register`` and ``/auth/oauth/{slug}/callback`` routes over the
real ``AuthService`` and **real** ArangoDB repositories; only the provider (token exchange and the
verified identity it asserts) is faked. What the callback did is read off the stored documents:
``auth_providers`` rows and the ``users`` document, not off a double.

``users.email_confirmed_at`` is the proof that an address's owner confirmed it (#2080).
``users.email_verified`` is not: with ``REQUIRE_EMAIL_VERIFICATION=false`` registration stamps it
without anybody having confirmed anything. An auto-link that reads ``email_verified`` therefore lets
whoever registered ``victim@example.org`` first keep the account when the victim later signs in
through a provider.

Runs in CI against the service container; locally it needs a database of its own
(``docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12``).
"""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import patch

import pytest
from arango import ArangoClient
from fastapi.testclient import TestClient

from app.common.dependencies import get_auth_service
from app.common.enums import AuthProviderType
from app.data_access.arango import collections as col
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.oauth_engine import OAuthEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.models.auth import OAuthUserInfo
from app.domain.models.oidc_config import OidcProviderConfig
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("oidc_autolink_proof")
ADDRESS = "victim@example.org"
# Assembled at runtime: a literal shaped like a credential trips the secret scanner (#1838).
HELD_SECRET = " ".join(["attacker", "chosen", "passphrase", "2026"])
FRONTEND = "http://frontend.test"

pytestmark = pytest.mark.usefixtures("arango_db")


class _Mail:
    """Captures the verification token the way the owner would receive it."""

    def __init__(self) -> None:
        self.verification_token: str | None = None

    def send_verification_email(self, *, token: str, **kwargs) -> None:
        self.verification_token = token

    def __getattr__(self, _name):
        return lambda *args, **kwargs: None


class _State:
    def get_and_delete(self, state):
        return {"provider_slug": "acme", "code_verifier": "v", "nonce": "n", "redirect_uri": f"{FRONTEND}/cb"}


class _Configs:
    def __init__(self) -> None:
        self.config = OidcProviderConfig(
            _key="cfg-acme",
            slug="acme",
            display_name="Acme",
            issuer_url="https://acme.example",
            client_id="cid",
            client_secret_encrypted="x",
            enabled=True,
        )

    def get_by_slug(self, slug):
        return self.config if slug == "acme" else None


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
    for name in (col.USERS, col.AUTH_PROVIDERS, col.REFRESH_TOKENS):
        database.collection(name).truncate()
    return database


def _build(db, *, require_verification: bool, provider_asserts: bool | None):
    from app.data_access.arango.auth_provider_repository import ArangoAuthProviderRepository
    from app.data_access.arango.refresh_token_repository import ArangoRefreshTokenRepository
    from app.data_access.arango.user_repository import ArangoUserRepository
    from app.domain.services.auth_service import AuthService

    engine = OAuthEngine()
    engine.exchange_code_for_tokens = lambda *a, **k: {"access_token": "t", "id_token": ""}  # type: ignore[method-assign]
    engine.authenticate_login = lambda *a, **k: OAuthUserInfo(  # type: ignore[method-assign]
        provider=AuthProviderType.OIDC,
        provider_user_id="sub-of-whoever-the-provider-says",
        email=ADDRESS,
        display_name="Whoever",
        email_verified=provider_asserts,
    )
    mail = _Mail()
    service = AuthService(
        user_repo=ArangoUserRepository(db),
        auth_provider_repo=ArangoAuthProviderRepository(db),
        refresh_token_repo=ArangoRefreshTokenRepository(db),
        password_engine=PasswordEngine(),
        token_engine=TokenEngine(secret_key="integration-test-secret-not-a-credential"),
        throttle_engine=LoginThrottleEngine(),
        email_service=mail,
        frontend_url=FRONTEND,
        require_email_verification=require_verification,
        oauth_engine=engine,
        oauth_state_store=_State(),
        oidc_config_repo=_Configs(),
        encryption_engine=None,
    )
    return service, mail


@pytest.fixture
def client_for(db) -> Iterator:
    def make(*, require_verification: bool, provider_asserts: bool | None = True):
        service, mail = _build(db, require_verification=require_verification, provider_asserts=provider_asserts)
        with patch("app.main.get_connection"), patch("app.main.ensure_collections"):
            from app.main import app

            app.dependency_overrides[get_auth_service] = lambda: service
            return TestClient(app, raise_server_exceptions=False), mail

    yield make
    from app.main import app

    app.dependency_overrides.pop(get_auth_service, None)


def _register(client) -> None:
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": ADDRESS, "password": HELD_SECRET, "display_name": "Registrant"},
    )
    assert resp.status_code == 201, resp.text


def _callback(client):
    return client.get("/api/v1/auth/oauth/acme/callback?code=c&state=s", follow_redirects=False)


def _users(db) -> list[dict]:
    return list(db.collection(col.USERS).all())


def _links(db) -> list[dict]:
    return [d for d in db.collection(col.AUTH_PROVIDERS).all() if d.get("provider") != "local"]


def _outcome(db, resp) -> str:
    users = _users(db)
    return (
        f"status={resp.status_code} location={resp.headers.get('location')} "
        f"users={len(users)} provider_links={[(d['user_key'], d['provider']) for d in _links(db)]} "
        f"cookie_set={'kp_refresh=' in resp.headers.get('set-cookie', '')}"
    )


class TestAnOidcSignInNeedsAProvenAddress:
    def test_an_address_registered_while_verification_was_off_is_not_taken_over(self, db, client_for):
        client, _ = client_for(require_verification=False)
        _register(client)
        planted = _users(db)[0]
        # The premise, measured: stamped verified, never confirmed by anyone.
        assert planted["email_verified"] is True
        assert planted.get("email_confirmed_at") is None

        resp = _callback(client)
        print("MEASURE verification-off+registered:", _outcome(db, resp))

        assert _links(db) == [], "the provider identity was attached to an account nobody confirmed"
        assert "kp_refresh=" not in resp.headers.get("set-cookie", "")
        assert resp.headers["location"] == f"{FRONTEND}/auth/callback?error=link_requires_password"
        assert len(_users(db)) == 1

    def test_an_unverified_registration_is_refused(self, db, client_for):
        client, _ = client_for(require_verification=True)
        _register(client)
        resp = _callback(client)
        print("MEASURE verification-on+unverified:", _outcome(db, resp))
        assert _links(db) == []
        assert resp.headers["location"] == f"{FRONTEND}/auth/callback?error=link_requires_password"

    def test_an_account_whose_owner_followed_the_link_is_linked(self, db, client_for):
        client, mail = client_for(require_verification=True)
        _register(client)
        assert mail.verification_token
        assert client.post("/api/v1/auth/verify-email", json={"token": mail.verification_token}).status_code == 200
        assert _users(db)[0]["email_confirmed_at"] is not None

        resp = _callback(client)
        print("MEASURE verification-on+confirmed:", _outcome(db, resp))
        assert [d["user_key"] for d in _links(db)] == [_users(db)[0]["_key"]]
        assert resp.headers["location"] == f"{FRONTEND}/auth/callback"
        assert "kp_refresh=" in resp.headers.get("set-cookie", "")
