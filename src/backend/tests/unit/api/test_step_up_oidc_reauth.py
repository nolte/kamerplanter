"""#1815 (operator decision, variant 1) — a federated account re-authenticates at its identity provider.

The e-mailed code proves the mailbox, not the person at the keyboard. For an account
whose linked provider can do a *fresh* sign-in (OpenID Connect with ``prompt=login``
and ``max_age=0``, answered with an ``auth_time`` claim — Google and generic OIDC;
not GitHub, which is plain OAuth2 without an ID token, and not Apple, which sends no
``auth_time``), the step-up is that fresh sign-in:

1. ``POST /users/me/step-up/oidc {action}`` answers the provider's authorization URL
   (PKCE, state, nonce, ``prompt=login``, ``max_age=0``); the state entry carries
   ``purpose: "step_up"``, the account and the act.
2. The provider redirects to the login callback. A ``step_up`` state never signs
   anyone in: the ID token is checked (``iss``, ``aud``/``azp``, ``nonce``, ``exp``,
   ``sub`` = a provider link of *this* account, ``auth_time`` at most five minutes
   old) and a one-time step-up token — five minutes, one act, one use — goes back
   to the frontend in the URL **fragment**.
3. The act's body carries it as ``step_up_token``; the verifier accepts it for an
   account without a password (method ``oidc_reauth``).

The mailed code stays only for accounts whose providers cannot re-authenticate
freshly (GitHub/Apple only); an account with an OIDC-capable provider is refused
the code (``STEP_UP_REAUTH_REQUIRED``).

The requests run the real users, auth and privacy routers and the real services;
the provider is a real ``OAuthEngine`` whose token endpoint is doubled with a
runtime-built, unsigned ID token.
"""

from __future__ import annotations

import base64
import json
import time
import uuid
from typing import Any
from unittest.mock import MagicMock
from urllib.parse import parse_qs, urlsplit

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.v1.auth.router import limiter
from app.api.v1.auth.router import router as auth_router
from app.api.v1.privacy.router import router as privacy_router
from app.api.v1.users.router import router as users_router
from app.common.auth import get_current_user
from app.common.dependencies import get_auth_service, get_privacy_service
from app.common.enums import AuthProviderType
from app.common.exceptions import InvalidTokenError, KamerplanterError, NotFoundError
from app.data_access.external.step_up_code_store import MemoryStepUpCodeStore
from app.data_access.external.step_up_throttle import MemoryStepUpThrottleStore
from app.data_access.vectordb.noop_reference_index_store import NoopReferenceIndexStore
from app.domain.engines.consent_engine import ConsentEngine
from app.domain.engines.data_export_engine import DataExportEngine
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.oauth_engine import OAuthEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.models.auth import AuthProvider
from app.domain.models.oidc_config import OidcProviderConfig
from app.domain.models.user import User
from app.domain.services.auth_service import AuthService
from app.domain.services.privacy_service import PrivacyService
from app.domain.services.step_up_service import FederatedReauthPolicy, StepUpVerifier
from app.domain.services.step_up_targets import StepUpTargetAuthorizer
from tests.support.privacy_doubles import FakeErasureRepo, FakePersonalTenants

FRONTEND = "https://app.test"
CLIENT_ID = "kamerplanter-client"
GOOGLE_ISSUER = "https://accounts.google.com"
# Assembled at runtime (#1838).
SECRET = "-".join(["step", "up", "code", "secret", "for", "tests"])
NEW_PASSWORD = "-".join(["a", "fresh", "owner", "passphrase"])
API_KEY = "kp_" + "x" * 24

GOOGLE = OidcProviderConfig(
    slug="google",
    display_name="Google",
    provider_type="google",
    issuer_url=GOOGLE_ISSUER,
    client_id=CLIENT_ID,
    client_secret_encrypted="enc",
    enabled=True,
)
GITHUB = OidcProviderConfig(
    slug="github",
    display_name="GitHub",
    provider_type="github",
    issuer_url="https://github.com",
    client_id=CLIENT_ID,
    client_secret_encrypted="enc",
    scopes=["read:user", "user:email"],
    enabled=True,
)


@pytest.fixture(autouse=True)
def _public_base_url(monkeypatch: pytest.MonkeyPatch):
    """The public URL /api is reachable under — the step-up callback is built from it, not the Host header."""
    from app.config.settings import settings

    monkeypatch.setattr(settings, "app_base_url", "https://app.test")


@pytest.fixture(autouse=True)
def _limiter_off(monkeypatch: pytest.MonkeyPatch):
    limiter.reset()
    monkeypatch.setattr(limiter, "enabled", False)
    yield
    limiter.reset()


def _error_handler(_request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code, "message": exc.message, "details": exc.details},
    )


def _jwt(claims: dict[str, Any]) -> str:
    def part(data: dict[str, Any]) -> str:
        return base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()

    return f"{part({'alg': 'RS256', 'typ': 'JWT'})}.{part(claims)}.{'s' * 16}"


class _Users:
    def __init__(self, *users: User) -> None:
        self.rows = {u.key: u for u in users}
        self.writes: list[tuple[str, dict[str, Any]]] = []

    def get_or_raise(self, key: str) -> User:
        if key not in self.rows:
            raise NotFoundError("User", key)
        return self.rows[key]

    def get_by_key(self, key: str) -> User | None:
        return self.rows.get(key)

    def get_by_email(self, email: str) -> User | None:
        return next((u for u in self.rows.values() if u.email == email), None)

    def update_fields(self, key: str, fields: dict[str, Any]) -> User:
        self.writes.append((key, dict(fields)))
        self.rows[key] = User.model_validate({**self.rows[key].model_dump(by_alias=True), **fields})
        return self.rows[key]


class _Providers:
    """``IAuthProviderRepository`` over a list; records every write."""

    def __init__(self) -> None:
        self.rows: list[AuthProvider] = []
        self.writes: list[str] = []
        self.deleted: list[str] = []

    def add(
        self,
        user_key: str,
        provider: AuthProviderType,
        sub: str,
        *,
        config_slug: str | None = None,
        issuer: str | None = None,
    ) -> AuthProvider:
        row = AuthProvider.model_validate(
            {
                "_key": f"prov-{len(self.rows)}",
                "user_key": user_key,
                "provider": provider,
                "provider_user_id": sub,
                "oidc_config_slug": config_slug,
                "issuer": issuer,
            }
        )
        self.rows.append(row)
        return row

    def list_by_user(self, user_key: str) -> list[AuthProvider]:
        return [r for r in self.rows if r.user_key == user_key]

    def get_by_provider(self, provider: AuthProviderType, provider_user_id: str) -> AuthProvider | None:
        return next((r for r in self.rows if r.provider == provider and r.provider_user_id == provider_user_id), None)

    def create(self, row: AuthProvider) -> AuthProvider:
        self.writes.append("create")
        return row

    def update(self, key: str, row: AuthProvider) -> AuthProvider:
        self.writes.append("update")
        return row

    def delete(self, key: str) -> bool:
        self.writes.append("delete")
        self.deleted.append(key)
        return True


class _Configs:
    def __init__(self, *configs: OidcProviderConfig) -> None:
        self.by_slug = {c.slug: c for c in configs}

    def get_by_slug(self, slug: str) -> OidcProviderConfig | None:
        return self.by_slug.get(slug)

    def list_enabled(self) -> list[OidcProviderConfig]:
        return [c for c in self.by_slug.values() if c.enabled]


class _States:
    def __init__(self) -> None:
        self.rows: dict[str, dict] = {}

    def save_state(self, state: str, data: dict, ttl: int = 300) -> None:
        self.rows[state] = dict(data)

    def get_and_delete(self, state: str) -> dict | None:
        return self.rows.pop(state, None)


class _Provider(OAuthEngine):
    """The real engine; only the token endpoint is doubled."""

    def __init__(self) -> None:
        self.claims: dict[str, Any] = {}
        self.exchange_redirect_uris: list[str] = []

    def exchange_code_for_tokens(self, config, code, code_verifier, redirect_uri, client_secret):  # noqa: ANN001, ANN201
        self.exchange_redirect_uris.append(redirect_uri)
        return {"access_token": "at", "id_token": _jwt(self.claims), "token_type": "Bearer"}


class _World:
    def __init__(self, *, password_hash: str | None = None, providers: tuple[str, ...] = ("google",)) -> None:
        self.key = f"owner-{uuid.uuid4().hex[:10]}"
        self.other_key = f"other-{uuid.uuid4().hex[:10]}"
        self.email = f"{self.key}@example.org"
        self.sub = f"google-{self.key}"
        owner = User.model_validate(
            {"_key": self.key, "email": self.email, "display_name": "Owner", "password_hash": password_hash}
        )
        other = User.model_validate(
            {"_key": self.other_key, "email": f"{self.other_key}@example.org", "display_name": "Other"}
        )
        self.users = _Users(owner, other)
        self.providers = _Providers()
        self.rows: dict[str, AuthProvider] = {}
        for name in providers:
            kind = {"google": AuthProviderType.GOOGLE, "github": AuthProviderType.GITHUB}[name]
            self.rows[name] = self.providers.add(self.key, kind, self.sub if name == "google" else f"gh-{self.key}")
        self.other_row = self.providers.add(self.other_key, AuthProviderType.GOOGLE, f"google-{self.other_key}")
        self.configs = _Configs(GOOGLE, GITHUB)
        self.states = _States()
        self.engine = _Provider()
        self.throttle = MemoryStepUpThrottleStore()
        self.verifier = StepUpVerifier(
            self.throttle,
            code_store=MemoryStepUpCodeStore(),
            reauth_store=MemoryStepUpCodeStore(),
            reauth_policy=FederatedReauthPolicy(self.providers, self.configs),
            code_secret=SECRET,
            # #1884 — the real target rules; only the provider links matter here.
            target_policy=StepUpTargetAuthorizer(
                user_repo=self.users,
                membership_repo=MagicMock(**{"get_by_user_and_tenant.return_value": None}),
                tenant_repo=MagicMock(),
                tenant_erasure_repo=None,
                auth_provider_repo=self.providers,
                oidc_config_repo=MagicMock(),
            ),
        )
        self.mail = MagicMock()
        self.refresh_tokens = MagicMock()
        self.auth = AuthService(
            user_repo=self.users,
            auth_provider_repo=self.providers,
            refresh_token_repo=self.refresh_tokens,
            password_engine=PasswordEngine(),
            token_engine=TokenEngine("test-secret-key-for-unit-tests-32chars!", "HS256"),
            throttle_engine=LoginThrottleEngine(),
            email_service=self.mail,
            frontend_url=FRONTEND,
            oauth_engine=self.engine,
            oauth_state_store=self.states,
            oidc_config_repo=self.configs,
            step_up_verifier=self.verifier,
        )
        self.erasures = FakeErasureRepo()
        self.privacy = PrivacyService(
            export_repo=MagicMock(),
            consent_repo=MagicMock(),
            restriction_repo=MagicMock(),
            erasure_repo=self.erasures,
            email_change_repo=MagicMock(),
            user_repo=self.users,
            refresh_token_repo=self.refresh_tokens,
            data_export_engine=DataExportEngine(),
            erasure_engine=ErasureEngine(),
            consent_engine=ConsentEngine(),
            password_engine=PasswordEngine(),
            token_engine=MagicMock(),
            email_service=MagicMock(),
            frontend_url=FRONTEND,
            membership_repo=MagicMock(**{"get_user_memberships.return_value": []}),
            reference_index_store=NoopReferenceIndexStore(),
            erasure_executor=MagicMock(),
            tenant_service=FakePersonalTenants(),
            tombstone_salt="s" * 32,
            step_up_verifier=self.verifier,
        )
        self.acting = self.key

    def client(self) -> TestClient:
        app = FastAPI()
        for router in (users_router, auth_router, privacy_router):
            app.include_router(router, prefix="/api/v1")
        app.add_exception_handler(KamerplanterError, _error_handler)
        app.dependency_overrides[get_current_user] = lambda: self.users.rows[self.acting]
        app.dependency_overrides[get_auth_service] = lambda: self.auth
        app.dependency_overrides[get_privacy_service] = lambda: self.privacy
        return TestClient(app, raise_server_exceptions=False, base_url="https://api.test")

    def post(self, path: str, body: dict[str, Any] | None, *, bearer: str | None = None):  # noqa: ANN201
        headers = {"Authorization": f"Bearer {bearer}"} if bearer else {}
        return self.client().post(path, json=body, headers=headers)

    # ── the flow ─────────────────────────────────────────────────────────

    def start(  # noqa: ANN201
        self, action: str = "account_erasure", provider_key: str | None = None, *, target: str | None = None
    ):
        body: dict[str, Any] = {"action": action}
        if provider_key is not None:
            body["provider_key"] = provider_key
        if target is not None:
            body["target"] = target
        return self.post("/api/v1/users/me/step-up/oidc", body)

    def fresh_claims(self, sent_nonce: str, /, **overrides: Any) -> dict[str, Any]:
        now = int(time.time())
        claims: dict[str, Any] = {
            "iss": GOOGLE_ISSUER,
            "aud": CLIENT_ID,
            "sub": self.sub,
            "nonce": sent_nonce,
            "iat": now,
            "exp": now + 600,
            "auth_time": now,
        }
        claims.update(overrides)
        return {k: v for k, v in claims.items() if v is not _DROP}

    def reauth(self, action: str = "account_erasure", *, target: str | None = None, **overrides: Any):  # noqa: ANN201
        started = self.start(action, target=target)
        assert started.status_code == 200, started.text
        query = parse_qs(urlsplit(started.json()["authorization_url"]).query)
        self.engine.claims = self.fresh_claims(query["nonce"][0], **overrides)
        return self.callback(query["state"][0])

    def callback(self, state: str):  # noqa: ANN201
        slug = self.states.rows[state]["provider_slug"]
        return self.client().get(
            f"/api/v1/auth/oauth/{slug}/callback?code=provider-code&state={state}", follow_redirects=False
        )

    def token(self, action: str = "account_erasure", *, target: str | None = None) -> str:
        callback = self.reauth(action, target=target)
        fragment = parse_qs(urlsplit(callback.headers["location"]).fragment)
        return fragment["step_up_token"][0]


_DROP = object()


def _error_of(callback) -> str | None:  # noqa: ANN001
    return parse_qs(urlsplit(callback.headers["location"]).query).get("error", [None])[0]


# ── the start ──────────────────────────────────────────────────────────────


def test_the_start_answers_a_fresh_login_url_at_the_linked_provider() -> None:
    world = _World()

    resp = world.start()

    assert resp.status_code == 200, resp.text
    url = urlsplit(resp.json()["authorization_url"])
    query = parse_qs(url.query)
    assert url.netloc == "accounts.google.com"
    assert query["prompt"] == ["login"]
    assert query["max_age"] == ["0"]
    assert query["code_challenge_method"] == ["S256"]
    assert query["redirect_uri"] == ["https://app.test/api/v1/auth/oauth/google/callback"]
    (entry,) = world.states.rows.values()
    assert entry["purpose"] == "step_up"
    assert entry["user_key"] == world.key
    assert entry["action"] == "account_erasure"


def test_the_exchange_uses_the_redirect_uri_of_the_authorization_request() -> None:
    world = _World()

    world.reauth()

    assert world.engine.exchange_redirect_uris == ["https://app.test/api/v1/auth/oauth/google/callback"]


def test_a_github_only_account_cannot_start_it_and_keeps_the_code() -> None:
    world = _World(providers=("github",))

    resp = world.start()

    assert resp.status_code == 422, resp.text
    assert not world.states.rows
    code = world.post("/api/v1/users/me/step-up-code", {"action": "account_erasure"})
    assert code.status_code == 202, code.text


def test_a_named_github_link_is_refused_and_a_named_google_link_accepted() -> None:
    world = _World(providers=("github", "google"))

    assert world.start(provider_key=world.rows["github"].key).status_code == 422
    assert world.start(provider_key=world.rows["google"].key).status_code == 200


def test_another_accounts_link_cannot_be_named() -> None:
    world = _World()

    assert world.start(provider_key=world.other_row.key).status_code == 422


def test_an_account_with_a_password_confirms_with_it_not_at_the_provider() -> None:
    world = _World(password_hash=PasswordEngine().hash_password(NEW_PASSWORD))

    assert world.start().status_code == 422


def test_an_api_key_cannot_start_it() -> None:
    world = _World()

    resp = world.post("/api/v1/users/me/step-up/oidc", {"action": "account_erasure"}, bearer=API_KEY)

    assert resp.status_code == 403, resp.text
    assert not world.states.rows


def test_a_locked_step_up_cannot_start_it() -> None:
    world = _World()
    world.throttle.lock(f"account:{world.key}", 900)

    resp = world.start()

    assert resp.status_code == 429, resp.text
    assert resp.json()["error_code"] == "STEP_UP_LOCKED"


def test_light_mode_refuses_it(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config.settings import settings

    world = _World()
    monkeypatch.setattr(settings, "kamerplanter_mode", "light")

    assert world.start().status_code == 403


def test_an_unknown_act_is_refused() -> None:
    world = _World()

    assert world.post("/api/v1/users/me/step-up/oidc", {"action": "login"}).status_code == 422


# ── the callback ───────────────────────────────────────────────────────────


def test_a_fresh_sign_in_answers_a_step_up_token_in_the_fragment_and_signs_nobody_in() -> None:
    world = _World()

    callback = world.reauth()

    assert callback.status_code == 302
    location = urlsplit(callback.headers["location"])
    assert f"{location.scheme}://{location.netloc}{location.path}" == f"{FRONTEND}/auth/step-up/callback"
    assert location.query == ""  # never in the query: it would reach server, Referer and proxy logs
    fragment = parse_qs(location.fragment)
    assert fragment["action"] == ["account_erasure"]
    assert len(fragment["step_up_token"][0]) >= 40
    assert "kp_refresh" not in callback.headers.get("set-cookie", "")
    world.refresh_tokens.create.assert_not_called()
    assert world.users.writes == []  # no last_login_at, nothing
    assert world.providers.writes == []  # not even last_used_at


def test_the_token_confirms_the_erasure() -> None:
    world = _World()
    token = world.token()

    resp = world.post("/api/v1/privacy/erasure", {"confirm_email": world.email, "step_up_token": token})

    assert resp.status_code == 201, resp.text
    (erasure,) = world.erasures.stored.values()
    assert erasure.step_up == "oidc_reauth"


def test_the_echo_is_still_required_with_the_token() -> None:
    world = _World()
    token = world.token()

    resp = world.post("/api/v1/privacy/erasure", {"confirm_email": "wrong@example.org", "step_up_token": token})

    assert resp.status_code == 422, resp.text
    assert not world.erasures.stored


@pytest.mark.parametrize(
    ("overrides", "error"),
    [
        pytest.param({"auth_time": int(time.time()) - 400}, "step_up_stale", id="auth_time too old"),
        pytest.param({"auth_time": _DROP}, "step_up_failed", id="auth_time missing"),
        pytest.param({"sub": "google-someone-else"}, "step_up_failed", id="sub of no link of this account"),
        pytest.param({"nonce": "not-the-nonce"}, "step_up_failed", id="nonce wrong"),
        pytest.param({"aud": "another-client"}, "step_up_failed", id="aud wrong"),
        pytest.param({"aud": [CLIENT_ID, "x"], "azp": "x"}, "step_up_failed", id="azp wrong with several aud"),
        pytest.param({"iss": "https://evil.example"}, "step_up_failed", id="iss wrong"),
        pytest.param({"exp": int(time.time()) - 120}, "step_up_failed", id="exp passed"),
    ],
)
def test_a_callback_that_proves_no_fresh_sign_in_of_this_account_issues_nothing(overrides, error) -> None:
    world = _World()

    callback = world.reauth(**overrides)

    assert callback.status_code == 302
    assert _error_of(callback) == error
    assert "step_up_token" not in callback.headers["location"]
    assert "kp_refresh" not in callback.headers.get("set-cookie", "")
    assert world.users.writes == []


def test_the_sub_of_another_accounts_link_is_refused() -> None:
    world = _World()

    callback = world.reauth(sub=f"google-{world.other_key}")

    assert _error_of(callback) == "step_up_failed"


def test_several_audiences_with_the_right_azp_pass() -> None:
    world = _World()

    callback = world.reauth(aud=[CLIENT_ID, "other"], azp=CLIENT_ID)

    assert "step_up_token=" in callback.headers["location"]


def test_a_step_up_state_never_signs_in_through_the_login_entry() -> None:
    world = _World()
    started = world.start()
    state = parse_qs(urlsplit(started.json()["authorization_url"]).query)["state"][0]

    with pytest.raises(InvalidTokenError):
        world.auth.complete_oauth("google", "provider-code", state)
    world.refresh_tokens.create.assert_not_called()


# ── the token ──────────────────────────────────────────────────────────────


def test_the_token_is_spent_by_one_act() -> None:
    world = _World()
    token = world.token("password_change")

    first = world.post("/api/v1/users/me/password", {"new_password": NEW_PASSWORD, "step_up_token": token})
    second = world.post("/api/v1/users/me/password", {"new_password": NEW_PASSWORD + "x", "step_up_token": token})

    assert first.status_code == 200, first.text
    assert second.status_code == 401, second.text


def test_a_token_for_another_act_confirms_nothing() -> None:
    world = _World()
    token = world.token("password_change")

    resp = world.post("/api/v1/privacy/erasure", {"confirm_email": world.email, "step_up_token": token})

    assert resp.status_code == 401, resp.text
    assert not world.erasures.stored


def test_a_token_of_another_account_confirms_nothing() -> None:
    world = _World()
    world.sub = f"google-{world.other_key}"
    world.acting = world.other_key
    token = world.token()
    world.acting = world.key

    resp = world.post("/api/v1/privacy/erasure", {"confirm_email": world.email, "step_up_token": token})

    assert resp.status_code == 401, resp.text
    assert not world.erasures.stored


def test_a_wrong_token_counts_into_the_step_up_throttle() -> None:
    world = _World()
    for _ in range(5):
        resp = world.post("/api/v1/privacy/erasure", {"confirm_email": world.email, "step_up_token": "x" * 43})
        assert resp.status_code == 401, resp.text

    assert world.start().status_code == 429


def test_an_account_with_a_password_ignores_the_token() -> None:
    world = _World(password_hash=PasswordEngine().hash_password(NEW_PASSWORD))
    world.verifier._reauth_store.issue(world.key, "irrelevant", 300)

    resp = world.post("/api/v1/privacy/erasure", {"confirm_email": world.email, "step_up_token": "x" * 43})

    assert resp.status_code == 401, resp.text
    assert resp.json()["error_code"] == "UNAUTHORIZED"
    assert not world.erasures.stored


# ── variant 1: the mailed code only where no fresh re-authentication exists ──


def test_an_account_with_an_oidc_provider_gets_no_code() -> None:
    world = _World()

    resp = world.post("/api/v1/users/me/step-up-code", {"action": "account_erasure"})

    assert resp.status_code == 422, resp.text
    assert resp.json()["error_code"] == "STEP_UP_REAUTH_REQUIRED"
    world.mail.send_step_up_code_email.assert_not_called()


def test_an_account_with_an_oidc_provider_is_told_to_re_authenticate() -> None:
    world = _World()

    resp = world.post("/api/v1/privacy/erasure", {"confirm_email": world.email})

    assert resp.status_code == 401, resp.text
    assert resp.json()["error_code"] == "STEP_UP_REAUTH_REQUIRED"
    assert resp.json()["details"][0]["field"] == "step_up_token"


def test_an_account_with_an_oidc_provider_cannot_confirm_with_a_code() -> None:
    world = _World(providers=("github",))
    code = world.post("/api/v1/users/me/step-up-code", {"action": "account_erasure"})
    assert code.status_code == 202
    mailed = world.mail.send_step_up_code_email.call_args.kwargs["code"]
    world.rows["google"] = world.providers.add(world.key, AuthProviderType.GOOGLE, world.sub)  # linked since

    resp = world.post("/api/v1/privacy/erasure", {"confirm_email": world.email, "step_up_code": mailed})

    assert resp.status_code == 401, resp.text
    assert resp.json()["error_code"] == "STEP_UP_REAUTH_REQUIRED"
    assert not world.erasures.stored


def test_a_github_only_account_is_told_to_use_the_code() -> None:
    world = _World(providers=("github",))

    resp = world.post("/api/v1/privacy/erasure", {"confirm_email": world.email})

    assert resp.status_code == 401, resp.text
    assert resp.json()["error_code"] == "STEP_UP_CODE_REQUIRED"


def test_the_start_route_documents_its_refusals() -> None:
    schema = _World().client().app.openapi()

    responses = schema["paths"]["/api/v1/users/me/step-up/oidc"]["post"]["responses"]

    assert {"200", "403", "422", "429"} <= responses.keys(), sorted(responses)


# ══ review round (SEC-001 … SEC-006, /code-review) ══════════════════════════════


def _oidc(slug: str, issuer: str, *, token_url: str | None = None) -> OidcProviderConfig:
    return OidcProviderConfig(
        slug=slug,
        display_name=slug,
        provider_type="oidc",
        issuer_url=issuer,
        client_id=CLIENT_ID,
        client_secret_encrypted="enc",
        authorization_url=f"{issuer}/authorize",
        token_url=token_url or f"{issuer}/token",
        discovery_document={"issuer": issuer},
        enabled=True,
    )


CORP_A = _oidc("corp-a", "https://idp-a.example")
CORP_B = _oidc("corp-b", "https://idp-b.example")


def _oidc_world(*links: tuple[str | None, str, str | None]) -> _World:
    """An account with generic OIDC links: (config slug or None for a pre-review row, sub, stored issuer)."""
    world = _World(providers=())
    world.configs = _Configs(GOOGLE, GITHUB, CORP_A, CORP_B)
    world.verifier._reauth_policy = FederatedReauthPolicy(world.providers, world.configs)
    world.auth._oidc_config_repo = world.configs
    world.auth._reauth_policy = FederatedReauthPolicy(world.providers, world.configs)
    for slug, sub, issuer in links:
        world.rows[slug or f"legacy-{sub}"] = world.providers.add(
            world.key, AuthProviderType.OIDC, sub, config_slug=slug, issuer=issuer
        )
    return world


def _oidc_callback(world: _World, provider_key: str, **claims: Any):  # noqa: ANN202
    started = world.start(provider_key=provider_key)
    assert started.status_code == 200, started.text
    query = parse_qs(urlsplit(started.json()["authorization_url"]).query)
    entry = world.states.rows[query["state"][0]]
    config = world.configs.by_slug[entry["provider_slug"]]
    now = int(time.time())
    world.engine.claims = {
        "iss": config.discovery_document["issuer"],
        "aud": CLIENT_ID,
        "nonce": query["nonce"][0],
        "iat": now,
        "exp": now + 600,
        "auth_time": now,
        **claims,
    }
    return started, world.callback(query["state"][0])


# ── SEC-001: a link re-authenticates at its own configuration ────────────────


def test_a_link_of_the_second_oidc_configuration_re_authenticates_there() -> None:
    world = _oidc_world(("corp-b", "sub-b", "https://idp-b.example"))

    started, callback = _oidc_callback(world, world.rows["corp-b"].key, sub="sub-b")

    assert urlsplit(started.json()["authorization_url"]).netloc == "idp-b.example"
    assert "step_up_token=" in callback.headers["location"], callback.headers["location"]


def test_a_pre_review_link_with_two_matching_configurations_keeps_the_code() -> None:
    """Ambiguous: re-authenticating could go to the wrong IdP — so not re-auth capable, and not locked out."""
    world = _oidc_world((None, "sub-x", None))

    started = world.start()
    code = world.post("/api/v1/users/me/step-up-code", {"action": "account_erasure"})

    assert started.status_code == 422, started.text
    assert started.json()["error_code"] == "STEP_UP_REAUTH_UNAVAILABLE"
    assert code.status_code == 202, code.text


def test_a_colliding_sub_of_another_configuration_is_refused() -> None:
    """The IdP of corp-b answers with the sub the account holds at corp-a: not this link."""
    world = _oidc_world(("corp-a", "sub-shared", "https://idp-a.example"), ("corp-b", "sub-b", "https://idp-b.example"))

    _started, callback = _oidc_callback(world, world.rows["corp-b"].key, sub="sub-shared")

    assert _error_of(callback) == "step_up_failed"


def test_a_link_whose_stored_issuer_differs_is_refused() -> None:
    world = _oidc_world(("corp-a", "sub-a", "https://old-idp.example"))

    _started, callback = _oidc_callback(world, world.rows["corp-a"].key, sub="sub-a")

    assert _error_of(callback) == "step_up_failed"


# ── SEC-002: the callback URL is not taken from the Host header ─────────────


def test_the_host_header_does_not_steer_the_callback_url() -> None:
    world = _World()

    resp = world.client().post(
        "/api/v1/users/me/step-up/oidc", json={"action": "account_erasure"}, headers={"Host": "evil.example"}
    )

    assert resp.status_code == 200, resp.text
    query = parse_qs(urlsplit(resp.json()["authorization_url"]).query)
    assert query["redirect_uri"] == ["https://app.test/api/v1/auth/oauth/google/callback"]


# ── SEC-003: only over TLS ────────────────────────────────────────────────


def test_a_plain_http_token_endpoint_is_not_re_authentication_capable() -> None:
    world = _World(providers=())
    world.configs = _Configs(_oidc("corp-a", "https://idp-a.example", token_url="http://idp-a.example/token"))
    world.auth._reauth_policy = FederatedReauthPolicy(world.providers, world.configs)
    world.verifier._reauth_policy = world.auth._reauth_policy
    world.providers.add(world.key, AuthProviderType.OIDC, "sub-a", config_slug="corp-a")

    resp = world.start()

    assert resp.status_code == 422, resp.text
    assert resp.json()["error_code"] == "STEP_UP_REAUTH_UNAVAILABLE"


def test_a_token_endpoint_switched_to_http_before_the_callback_fails_it() -> None:
    world = _oidc_world(("corp-a", "sub-a", "https://idp-a.example"))
    started = world.start(provider_key=world.rows["corp-a"].key)
    state = parse_qs(urlsplit(started.json()["authorization_url"]).query)["state"][0]
    world.configs.by_slug["corp-a"] = CORP_A.model_copy(update={"token_url": "http://idp-a.example/token"})

    callback = world.callback(state)

    assert _error_of(callback) == "step_up_failed"
    assert world.engine.exchange_redirect_uris == []  # never exchanged over plain HTTP


# ── SEC-004: numbers are numbers ───────────────────────────────────────────


@pytest.mark.parametrize(
    "overrides",
    [
        pytest.param({"auth_time": True}, id="auth_time bool"),
        pytest.param({"auth_time": float("nan")}, id="auth_time NaN"),
        pytest.param({"auth_time": float("inf")}, id="auth_time Infinity"),
        pytest.param({"exp": float("inf")}, id="exp Infinity"),
        pytest.param({"exp": float("nan")}, id="exp NaN"),
        pytest.param({"exp": True}, id="exp bool"),
    ],
)
def test_a_non_finite_or_boolean_time_claim_is_refused(overrides) -> None:
    world = _World()

    callback = world.reauth(**overrides)

    assert _error_of(callback) == "step_up_failed", callback.headers["location"]


# ── /code-review: distinguishable 422s for the frontend ───────────────────────


def test_a_password_account_is_told_to_use_its_password() -> None:
    world = _World(password_hash=PasswordEngine().hash_password(NEW_PASSWORD))

    reauth = world.start()
    code = world.post("/api/v1/users/me/step-up-code", {"action": "account_erasure"})

    assert reauth.status_code == code.status_code == 422
    assert reauth.json()["error_code"] == code.json()["error_code"] == "STEP_UP_PASSWORD_REQUIRED"


def test_a_github_only_account_is_told_re_authentication_is_unavailable() -> None:
    world = _World(providers=("github",))

    resp = world.start()

    assert resp.status_code == 422, resp.text
    assert resp.json()["error_code"] == "STEP_UP_REAUTH_UNAVAILABLE"


def test_the_422s_are_documented() -> None:
    schema = _World().client().app.openapi()
    paths = schema["paths"]

    reauth_422 = paths["/api/v1/users/me/step-up/oidc"]["post"]["responses"]["422"]["description"]
    code_422 = paths["/api/v1/users/me/step-up-code"]["post"]["responses"]["422"]["description"]

    assert "STEP_UP_PASSWORD_REQUIRED" in reauth_422 and "STEP_UP_REAUTH_UNAVAILABLE" in reauth_422
    assert "STEP_UP_PASSWORD_REQUIRED" in code_422 and "STEP_UP_REAUTH_REQUIRED" in code_422


def test_a_colliding_sub_of_another_configuration_is_refused_without_a_stored_issuer() -> None:
    """The configuration check alone — the issuer check must not be what carries it."""
    world = _oidc_world(("corp-a", "sub-shared", None), ("corp-b", "sub-b", None))

    _started, callback = _oidc_callback(world, world.rows["corp-b"].key, sub="sub-shared")

    assert _error_of(callback) == "step_up_failed"


# ── the client nonce: the starting page recognises its own result (review SEC-005) ──


def _client_nonce() -> str:
    # Assembled at runtime: 32 lowercase hex characters, like the frontend's crypto nonce.
    return "".join(["0123456789abcdef"[(i * 7) % 16] for i in range(32)])


def test_the_client_nonce_comes_back_beside_the_token() -> None:
    world = _World()
    nonce = _client_nonce()
    started = world.post("/api/v1/users/me/step-up/oidc", {"action": "account_erasure", "client_nonce": nonce})
    assert started.status_code == 200, started.text
    query = parse_qs(urlsplit(started.json()["authorization_url"]).query)
    assert nonce not in started.json()["authorization_url"]  # never sent to the provider
    world.engine.claims = world.fresh_claims(query["nonce"][0])

    callback = world.callback(query["state"][0])

    location = urlsplit(callback.headers["location"])
    assert location.query == ""
    assert parse_qs(location.fragment)["client_nonce"] == [nonce]


def test_the_client_nonce_comes_back_beside_an_error() -> None:
    world = _World()
    nonce = _client_nonce()
    started = world.post("/api/v1/users/me/step-up/oidc", {"action": "account_erasure", "client_nonce": nonce})
    query = parse_qs(urlsplit(started.json()["authorization_url"]).query)
    world.engine.claims = world.fresh_claims(query["nonce"][0], auth_time=int(time.time()) - 3600)

    callback = world.callback(query["state"][0])

    location = urlsplit(callback.headers["location"])
    assert parse_qs(location.query)["error"] == ["step_up_stale"]
    assert parse_qs(location.query)["client_nonce"] == [nonce]


def test_a_malformed_client_nonce_is_refused() -> None:
    world = _World()

    resp = world.post("/api/v1/users/me/step-up/oidc", {"action": "account_erasure", "client_nonce": "not-hex"})

    assert resp.status_code == 422


# ── #1884: the token is bound to the target of the act ───────────────────────


def test_a_token_to_unlink_one_provider_does_not_unlink_another() -> None:
    """The acceptance of #1884: issued for target A, refused for target B, and not spent by that refusal."""
    world = _World(providers=("google", "github", "github"))
    first_github, second_github = [row for row in world.providers.list_by_user(world.key) if row.provider == "github"]
    token = world.token("provider_unlink", target=first_github.key)

    other = world.client().request(
        "DELETE", f"/api/v1/users/me/providers/{second_github.key}", json={"step_up_token": token}
    )
    assert other.status_code == 401, other.text
    assert world.providers.deleted == []

    meant = world.client().request(
        "DELETE", f"/api/v1/users/me/providers/{first_github.key}", json={"step_up_token": token}
    )
    assert meant.status_code == 200, meant.text
    assert world.providers.deleted == [first_github.key]


def test_the_target_rides_in_the_state_to_the_callback() -> None:
    world = _World(providers=("google", "github"))
    started = world.start("provider_unlink", target=world.rows["github"].key)

    assert started.status_code == 200, started.text
    (state,) = world.states.rows.values()
    assert state["target"] == world.rows["github"].key


def test_a_targeted_act_cannot_start_without_its_target() -> None:
    world = _World(providers=("google", "github"))

    resp = world.start("provider_unlink")

    assert resp.status_code == 422, resp.text
    assert world.states.rows == {}


def test_an_act_on_the_own_account_cannot_name_a_target() -> None:
    resp = _World().start("account_erasure", target="someone-else")

    assert resp.status_code == 422, resp.text


def test_the_start_refuses_another_accounts_link_as_the_target() -> None:
    """D2: the target is checked when the factor is issued — no browser round trip for a foreign link."""
    world = _World(providers=("google", "github"))

    resp = world.start("provider_unlink", target=world.other_row.key)

    assert resp.status_code == 404, resp.text
    assert world.states.rows == {}


def test_a_state_from_before_the_binding_issues_no_unbound_token() -> None:
    """A re-authentication started before #1884 carries no target: its callback fails rather than mint one."""
    world = _World(providers=("google", "github"))
    started = world.start("provider_unlink", target=world.rows["github"].key)
    query = parse_qs(urlsplit(started.json()["authorization_url"]).query)
    world.states.rows[query["state"][0]].pop("target")
    world.engine.claims = world.fresh_claims(query["nonce"][0])

    callback = world.callback(query["state"][0])

    assert _error_of(callback) == "step_up_failed"
