"""#1936 — the OIDC **login** checks the ID token it receives and the ``sub`` it trusts.

Until #1936 the login decoded the ID token without looking at its signature,
``iss``, ``aud``, ``nonce`` or ``exp``, took the identity from the userinfo
endpoint without comparing its ``sub`` with the ID token's (OIDC Core 5.3.2), and
turned a missing ``sub`` into ``""`` — so two identities without one at the same
configuration landed on the same link. The step-up (#1815) did the claim checks;
the login did not.

The requests run the real auth router, the real ``AuthService`` and the real
``OAuthEngine``. Only the network is doubled, by
:class:`tests.support.oidc_idp.FakeIdp`, which signs real JWTs and publishes the
key through a JWKS the engine fetches. Every refusal must look the same to the
caller — one generic error code, no session, no registration — and leave a
value-free log line.
"""

from __future__ import annotations

import base64
import json
import time
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest
import structlog

from app.api.v1.auth.router import limiter
from app.domain.engines.oauth_engine import OAuthEngine
from app.domain.models.user import User
from tests.support.oidc_idp import ACCESS_TOKEN, FakeIdp
from tests.unit.api.test_step_up_oidc_reauth import CLIENT_ID, CORP_A, FRONTEND, _Configs, _oidc_world, _World

SUB = "sub-a"
PUBLIC_BASE = "https://kamerplanter.example"
_DROP = object()


@pytest.fixture(autouse=True)
def _public_base_url(monkeypatch: pytest.MonkeyPatch):
    from app.config.settings import settings

    monkeypatch.setattr(settings, "app_base_url", PUBLIC_BASE)


@pytest.fixture(autouse=True)
def _limiter_off(monkeypatch: pytest.MonkeyPatch):
    limiter.reset()
    monkeypatch.setattr(limiter, "enabled", False)
    yield
    limiter.reset()


@pytest.fixture
def idp(monkeypatch: pytest.MonkeyPatch) -> FakeIdp:
    provider = FakeIdp()
    provider.install(monkeypatch)
    return provider


def _world(
    idp: FakeIdp,
    *,
    userinfo: bool = False,
    scopes: list[str] | None = None,
    link_issuer: str | None = "https://idp-a.example",
) -> _World:
    """The linked account, with the real engine in front of the doubled network."""
    world = _oidc_world(("corp-a", SUB, link_issuer))
    update: dict[str, Any] = {}
    if userinfo:
        update["userinfo_url"] = "https://idp-a.example/userinfo"
    if scopes is not None:
        update["scopes"] = scopes
    config = CORP_A.model_copy(update=update)
    world.configs = _Configs(config)
    world.auth._oidc_config_repo = world.configs
    engine = OAuthEngine()
    world.engine = engine  # type: ignore[assignment]
    world.auth._oauth_engine = engine
    return world


def _login(world: _World, idp: FakeIdp, **claims: Any):  # noqa: ANN202
    """Start the login at corp-a, let the provider answer with *claims*, run the callback."""
    started = world.client().get("/api/v1/auth/oauth/corp-a", follow_redirects=False)
    assert started.status_code == 302, started.text
    query = parse_qs(urlsplit(started.headers["location"]).query)
    now = int(time.time())
    valid: dict[str, Any] = {
        "iss": "https://idp-a.example",
        "aud": CLIENT_ID,
        "sub": SUB,
        "nonce": query["nonce"][0],
        "iat": now,
        "exp": now + 600,
        "email": world.email,
        "email_verified": True,
    }
    valid.update(claims)
    idp.claims = {k: v for k, v in valid.items() if v is not _DROP}
    return world.client().get(
        f"/api/v1/auth/oauth/corp-a/callback?code=provider-code&state={query['state'][0]}", follow_redirects=False
    )


def _error(callback) -> str | None:  # noqa: ANN001
    return parse_qs(urlsplit(callback.headers["location"]).query).get("error", [None])[0]


def _refused(world: _World, callback) -> None:  # noqa: ANN001
    """The one answer every refusal gives, and nothing written."""
    assert callback.headers["location"] == f"{FRONTEND}/auth/callback?error=provider_error"
    assert world.refresh_tokens.create.call_args_list == []
    assert world.providers.writes == []
    assert world.rows["corp-a"].last_used_at is None


def _signed_in(world: _World, callback) -> bool:  # noqa: ANN001
    if callback.headers["location"] != f"{FRONTEND}/auth/callback":
        return False
    (call,) = world.refresh_tokens.create.call_args_list
    return call.args[0].user_key == world.key


def test_a_valid_signed_token_signs_the_link_owner_in(idp: FakeIdp) -> None:
    world = _world(idp)

    callback = _login(world, idp)

    assert _signed_in(world, callback)
    assert idp.jwks_requests == 1  # the key came from the provider, over the network


@pytest.mark.parametrize(
    "claims",
    [
        pytest.param({"nonce": "not-the-one-we-sent"}, id="wrong nonce"),
        pytest.param({"nonce": _DROP}, id="no nonce"),
        pytest.param({"iss": "https://idp-evil.example"}, id="wrong issuer"),
        pytest.param({"iss": _DROP}, id="no issuer"),
        pytest.param({"aud": "someone-elses-client"}, id="wrong audience"),
        pytest.param({"aud": [CLIENT_ID, "other"], "azp": "other"}, id="wrong authorized party"),
        pytest.param({"aud": _DROP}, id="no audience"),
        pytest.param({"exp": int(time.time()) - 3600}, id="expired"),
        pytest.param({"exp": _DROP}, id="no expiry"),
        pytest.param({"iat": int(time.time()) + 3600}, id="issued in the future"),
        pytest.param({"iat": _DROP}, id="no issued-at"),
        pytest.param({"sub": ""}, id="empty sub"),
        pytest.param({"sub": _DROP}, id="missing sub"),
        pytest.param({"sub": "   "}, id="blank sub"),
    ],
)
def test_a_token_that_fails_a_claim_check_signs_nobody_in(idp: FakeIdp, claims: dict[str, Any]) -> None:
    world = _world(idp)

    callback = _login(world, idp, **claims)

    _refused(world, callback)


def test_a_token_signed_by_another_key_signs_nobody_in(idp: FakeIdp) -> None:
    world = _world(idp)
    idp.forge_with = "attacker-key"

    callback = _login(world, idp)

    _refused(world, callback)


def test_an_unsigned_token_signs_nobody_in(idp: FakeIdp) -> None:
    """``alg: none`` — the claims are right, there is just no signature."""
    world = _world(idp)
    started = world.client().get("/api/v1/auth/oauth/corp-a", follow_redirects=False)
    query = parse_qs(urlsplit(started.headers["location"]).query)
    now = int(time.time())

    def part(data: dict[str, Any]) -> str:
        return base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()

    claims = {
        "iss": "https://idp-a.example",
        "aud": CLIENT_ID,
        "sub": SUB,
        "nonce": query["nonce"][0],
        "iat": now,
        "exp": now + 600,
    }
    idp.id_token_override = f"{part({'alg': 'none', 'typ': 'JWT'})}.{part(claims)}."

    callback = world.client().get(
        f"/api/v1/auth/oauth/corp-a/callback?code=provider-code&state={query['state'][0]}", follow_redirects=False
    )

    _refused(world, callback)


def test_a_provider_that_issues_no_id_token_for_an_openid_request_signs_nobody_in(idp: FakeIdp) -> None:
    world = _world(idp, userinfo=True)
    idp.omit_id_token = True
    idp.userinfo = {"sub": SUB, "email": world.email, "email_verified": True}

    callback = _login(world, idp)

    _refused(world, callback)


def test_googles_scheme_less_issuer_spelling_still_passes(idp: FakeIdp) -> None:
    world = _world(idp)

    callback = _login(world, idp, iss="idp-a.example")

    assert _signed_in(world, callback)


# ── the userinfo sub (OIDC Core 5.3.2) ─────────────────────────────────────


def test_a_userinfo_sub_equal_to_the_token_sub_signs_in(idp: FakeIdp) -> None:
    world = _world(idp, userinfo=True)
    idp.userinfo = {"sub": SUB, "email": world.email, "email_verified": True}

    callback = _login(world, idp)

    assert _signed_in(world, callback)
    assert idp.userinfo_requests == 1


@pytest.mark.parametrize(
    "userinfo_sub",
    [
        pytest.param("someone-else", id="differs from the token's"),
        pytest.param("", id="empty"),
        pytest.param(_DROP, id="missing"),
        pytest.param(None, id="null"),
    ],
)
def test_a_userinfo_sub_that_is_not_the_token_sub_signs_nobody_in(idp: FakeIdp, userinfo_sub: Any) -> None:
    world = _world(idp, userinfo=True)
    userinfo: dict[str, Any] = {"sub": userinfo_sub, "email": world.email, "email_verified": True}
    idp.userinfo = {k: v for k, v in userinfo.items() if v is not _DROP}

    callback = _login(world, idp)

    _refused(world, callback)


def test_two_identities_without_a_sub_do_not_land_on_one_link(idp: FakeIdp) -> None:
    """A plain-OAuth2 configuration (no ``openid`` scope, so no ID token): an empty ``sub`` is no identity."""
    world = _world(idp, userinfo=True, scopes=["profile", "email"])
    idp.omit_id_token = True
    idp.userinfo = {"email": "stranger@example.net", "email_verified": True}

    callback = _login(world, idp)

    _refused(world, callback)
    assert world.users.get_by_email("stranger@example.net") is None


def test_a_plain_oauth2_configuration_with_a_sub_still_signs_in(idp: FakeIdp) -> None:
    """No ID token means no issuer to record: the link is one that never had one."""
    world = _world(idp, userinfo=True, scopes=["profile", "email"], link_issuer=None)
    idp.omit_id_token = True
    idp.userinfo = {"sub": SUB, "email": world.email, "email_verified": True}

    callback = _login(world, idp)

    assert _signed_in(world, callback)


# ── what the log says ──────────────────────────────────────────────────────


def test_a_refusal_logs_its_reason_and_none_of_the_values(idp: FakeIdp) -> None:
    world = _world(idp)

    with structlog.testing.capture_logs() as logs:
        callback = _login(world, idp, sub="the-presented-sub-value", nonce="the-presented-nonce-value")

    _refused(world, callback)
    (line,) = [entry for entry in logs if entry["event"] == "oauth_login_refused"]
    assert line["reason"] == "nonce"
    assert line["provider"] == "corp-a"
    rendered = json.dumps(line, default=str)
    for value in ("the-presented-sub-value", "the-presented-nonce-value", ACCESS_TOKEN, world.email):
        assert value not in rendered


def test_the_caller_cannot_tell_the_refusals_apart(idp: FakeIdp) -> None:
    """One redirect target for a bad nonce, a bad issuer, a forged signature and a bad sub."""
    answers = set()
    for claims in ({"nonce": "x"}, {"iss": "https://evil.example"}, {"sub": ""}, {"aud": "x"}):
        world = _world(idp)
        answers.add(_login(world, idp, **claims).headers["location"])
    forged_world = _world(idp)
    idp.forge_with = "attacker-key"
    answers.add(_login(forged_world, idp).headers["location"])

    assert answers == {f"{FRONTEND}/auth/callback?error=provider_error"}


def test_the_world_double_is_a_real_account(idp: FakeIdp) -> None:
    """Guard on the harness: the refusals above are about the token, not about a missing account."""
    world = _world(idp)
    assert isinstance(world.users.rows[world.key], User)


def test_a_non_ascii_nonce_in_a_signed_token_is_a_refusal_not_a_crash(idp: FakeIdp) -> None:
    world = _world(idp)

    callback = _login(world, idp, nonce="nönce-é")

    _refused(world, callback)
