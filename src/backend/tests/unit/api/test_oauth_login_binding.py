"""The OAuth/OIDC **login** — the exchange repeats the authorization request's
``redirect_uri`` (#1865), and a provider link is matched by (configuration, ``sub``),
never by ``sub`` alone (#1869).

#1865: the authorization request sent ``{request.base_url}/api/v1/auth/oauth/{slug}/callback``
while the code exchange sent ``{FRONTEND_URL}/auth/callback``. RFC 6749 §4.1.3
requires the two to be identical; a provider answers ``invalid_grant`` otherwise.
The login now builds the callback from the configured public base URL (not the
Host header) and carries it in the OAuth state to the exchange.

#1869: OIDC guarantees ``sub`` unique per issuer only. Every generic OIDC
configuration stores its links under the type ``oidc``, and the login looked a link
up by (type, ``sub``) — so an identity at IdP A whose ``sub`` equals a victim's
``sub`` at IdP B signed in **as the victim**. A link is now matched only to the
configuration it was made through (and, where recorded, its issuer). A link made
before the configuration was recorded counts only when exactly one configuration
of its type exists; it is then bound on first use.

The requests run the real auth router and the real ``AuthService``; the identity
provider is the real ``OAuthEngine`` with only its token endpoint doubled — the
double records the ``redirect_uri`` it receives.
"""

from __future__ import annotations

import time
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest

from app.api.v1.auth.router import limiter
from app.common.enums import AuthProviderType
from app.domain.models.user import User
from tests.unit.api.test_step_up_oidc_reauth import (
    CLIENT_ID,
    CORP_A,
    CORP_B,
    FRONTEND,
    GITHUB,
    GOOGLE,
    _Configs,
    _oidc_world,
    _World,
)

#: Deliberately not the frontend URL and not the test client's host: the callback
#: must come from this setting and nothing else.
PUBLIC_BASE = "https://kamerplanter.example"


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


class _RegisteringUsers:
    """Adds the account creation the login's registration branch calls."""

    def __init__(self, world: _World) -> None:
        self.created: list[User] = []
        users = world.users

        def create(user: User) -> User:
            stored = user.model_copy(update={"key": f"new-{len(self.created)}"})
            self.created.append(stored)
            users.rows[stored.key] = stored
            return stored

        users.create = create  # type: ignore[attr-defined]


def _sign_in(world: _World, slug: str, *, host: str | None = None, **claims: Any):  # noqa: ANN202
    """Start the login at *slug*, let the provider answer with *claims*, run the callback."""
    headers = {"Host": host} if host else {}
    started = world.client().get(f"/api/v1/auth/oauth/{slug}", headers=headers, follow_redirects=False)
    assert started.status_code == 302, started.text
    query = parse_qs(urlsplit(started.headers["location"]).query)
    config = world.configs.by_slug[slug]
    now = int(time.time())
    world.engine.claims = {
        "iss": config.discovery_document["issuer"],
        "aud": CLIENT_ID,
        "nonce": query["nonce"][0],
        "iat": now,
        "exp": now + 600,
        **claims,
    }
    callback = world.client().get(
        f"/api/v1/auth/oauth/{slug}/callback?code=provider-code&state={query['state'][0]}",
        headers=headers,
        follow_redirects=False,
    )
    return query, callback


def _signed_in_as(world: _World, callback) -> str | None:  # noqa: ANN001
    """The account the callback opened a session for, or ``None`` when it opened none."""
    if callback.headers["location"] != f"{FRONTEND}/auth/callback":
        return None
    (call,) = world.refresh_tokens.create.call_args_list
    return call.args[0].user_key


# ── #1865: one redirect_uri, from the public base URL ──────────────────────


def test_the_login_exchange_repeats_the_redirect_uri_of_the_authorization_request() -> None:
    world = _oidc_world(("corp-a", "sub-a", "https://idp-a.example"))

    query, callback = _sign_in(world, "corp-a", sub="sub-a", email=world.email, email_verified=True)

    assert query["redirect_uri"] == [f"{PUBLIC_BASE}/api/v1/auth/oauth/corp-a/callback"]
    assert world.engine.exchange_redirect_uris == query["redirect_uri"]
    assert _signed_in_as(world, callback) == world.key


def test_the_host_header_does_not_steer_the_login_callback_url() -> None:
    world = _oidc_world(("corp-a", "sub-a", "https://idp-a.example"))

    query, _callback = _sign_in(world, "corp-a", host="backend.cluster.local:8000", sub="sub-a")

    assert query["redirect_uri"] == [f"{PUBLIC_BASE}/api/v1/auth/oauth/corp-a/callback"]
    assert world.engine.exchange_redirect_uris == query["redirect_uri"]


def test_a_login_state_without_its_redirect_uri_is_refused_before_any_exchange() -> None:
    """A state written before #1865 cannot say which URI the request carried: refused, not guessed."""
    world = _oidc_world(("corp-a", "sub-a", "https://idp-a.example"))
    world.states.save_state("old-state", {"code_verifier": "v", "nonce": "n", "provider_slug": "corp-a"})

    callback = world.client().get(
        "/api/v1/auth/oauth/corp-a/callback?code=provider-code&state=old-state", follow_redirects=False
    )

    assert parse_qs(urlsplit(callback.headers["location"]).query)["error"] == ["invalid_state"]
    assert world.engine.exchange_redirect_uris == []


# ── #1869: a link is matched by (configuration, sub) ───────────────────────


def test_a_colliding_sub_at_another_configuration_does_not_sign_in_as_the_link_owner() -> None:
    """The victim's link is at corp-b; an identity at corp-a presents the same sub."""
    world = _oidc_world(("corp-b", "sub-shared", "https://idp-b.example"))
    registering = _RegisteringUsers(world)

    _query, callback = _sign_in(world, "corp-a", sub="sub-shared", email="intruder@example.net", email_verified=True)

    signed_in = _signed_in_as(world, callback)
    assert signed_in != world.key
    # The identity at corp-a is a stranger: it gets an account of its own, bound to corp-a.
    assert [u.email for u in registering.created] == ["intruder@example.net"]
    assert signed_in == registering.created[0].key
    assert world.providers.writes == ["create"]
    assert world.rows["corp-b"].last_used_at is None


def test_a_legacy_link_with_two_configurations_of_its_type_is_not_guessed() -> None:
    """A link made before the configuration was recorded could belong to either OIDC provider."""
    world = _oidc_world((None, "sub-shared", None))
    registering = _RegisteringUsers(world)

    _query, callback = _sign_in(world, "corp-a", sub="sub-shared", email="intruder@example.net", email_verified=True)

    assert _signed_in_as(world, callback) != world.key
    assert [u.email for u in registering.created] == ["intruder@example.net"]
    assert world.rows["legacy-sub-shared"].oidc_config_slug is None


def test_a_link_whose_stored_issuer_differs_does_not_sign_in() -> None:
    """The configuration was re-pointed at another IdP since the link was made."""
    world = _oidc_world(("corp-a", "sub-a", "https://old-idp.example"))
    registering = _RegisteringUsers(world)

    _query, callback = _sign_in(world, "corp-a", sub="sub-a", email="someone@example.net", email_verified=True)

    assert _signed_in_as(world, callback) != world.key
    assert [u.email for u in registering.created] == ["someone@example.net"]


def test_a_legacy_link_with_the_only_configuration_of_its_type_signs_in_and_is_bound() -> None:
    world = _oidc_world((None, "sub-a", None))
    world.configs = _Configs(GOOGLE, GITHUB, CORP_A)
    world.auth._oidc_config_repo = world.configs

    _query, callback = _sign_in(world, "corp-a", sub="sub-a", email=world.email, email_verified=True)

    assert _signed_in_as(world, callback) == world.key
    row = world.rows["legacy-sub-a"]
    assert (row.oidc_config_slug, row.issuer) == ("corp-a", "https://idp-a.example")
    assert row.last_used_at is not None


def test_a_disabled_configuration_of_the_same_type_keeps_a_legacy_link_ambiguous() -> None:
    """A disabled configuration still made links; the legacy link may be one of them."""
    world = _oidc_world((None, "sub-shared", None))
    world.configs = _Configs(GOOGLE, GITHUB, CORP_A, CORP_B.model_copy(update={"enabled": False}))
    world.auth._oidc_config_repo = world.configs
    _RegisteringUsers(world)

    _query, callback = _sign_in(world, "corp-a", sub="sub-shared", email="intruder@example.net", email_verified=True)

    assert _signed_in_as(world, callback) != world.key


def test_the_same_sub_at_its_own_configuration_still_signs_in() -> None:
    world = _oidc_world(
        ("corp-a", "sub-shared", "https://idp-a.example"),
    )
    other = world.providers.add(
        world.other_key, AuthProviderType.OIDC, "sub-shared", config_slug="corp-b", issuer="https://idp-b.example"
    )

    _query, callback = _sign_in(world, "corp-b", sub="sub-shared")

    assert _signed_in_as(world, callback) == world.other_key
    assert other.last_used_at is not None
    assert world.rows["corp-a"].last_used_at is None


def test_the_owner_of_an_ambiguous_legacy_link_is_linked_afresh_through_the_verified_address() -> None:
    """Not locked out: the auto-link path adds a link bound to the configuration, beside the legacy one."""
    world = _oidc_world((None, "sub-x", None))
    world.users.rows[world.key].email_verified = True

    _query, callback = _sign_in(world, "corp-b", sub="sub-x", email=world.email, email_verified=True)

    assert _signed_in_as(world, callback) == world.key
    fresh = [r for r in world.providers.rows if r.oidc_config_slug == "corp-b"]
    assert [(r.user_key, r.provider_user_id, r.issuer) for r in fresh] == [
        (world.key, "sub-x", "https://idp-b.example")
    ]
