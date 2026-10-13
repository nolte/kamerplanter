"""#2007 — the token and userinfo endpoints are checked before they are dialled, and read bounded.

The code exchange POSTs the **client secret and the authorization code** to the token endpoint;
the userinfo request carries the **access token**. Both URLs can come from the provider's own
discovery document. Until #2007 only their scheme was checked (#1987), so a document naming
``token_endpoint: https://169.254.169.254/...`` — or a host inside the network — had the server
send the client secret there, and a body of any size was buffered whole.

The rule is the key endpoint's (:func:`app.common.url_safety.validate_oidc_fetch_url`):

* an endpoint from the provider's **discovery document**: never a metadata / link-local address,
  a private one only on the issuer's own host (a self-hosted IdP on the LAN) or with ``DEBUG``;
* an endpoint the platform admin **configured** (behind a step-up): never a metadata / link-local
  address, a private one is theirs to choose;
* both responses are read through the key set's byte cap (``jwks_cache.JWKS_MAX_BYTES``).

The real auth router, ``AuthService`` and ``OAuthEngine`` run — login and step-up — and only the
network and DNS are doubled by :class:`tests.support.oidc_idp.FakeIdp`. "Never dialled" is asserted
on what reached the double (``token_requests``, ``userinfo_requests``), not on the refusal alone.
"""

from __future__ import annotations

import time
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest
import structlog

from app.api.v1.auth.router import limiter
from app.domain.engines import jwks_cache
from app.domain.engines.oauth_engine import InsecureEndpointError, OAuthEngine
from tests.support.oidc_idp import FakeIdp
from tests.unit.api.test_oauth_login_id_token import SUB, _login, _refused, _signed_in, _world
from tests.unit.api.test_step_up_oidc_reauth import CLIENT_ID, CORP_A, _error_of, _oidc_world, _World

ISSUER = "https://idp-a.example"


@pytest.fixture(autouse=True)
def _public_base_url(monkeypatch: pytest.MonkeyPatch):
    from app.config.settings import settings

    monkeypatch.setattr(settings, "app_base_url", "https://kamerplanter.example")
    monkeypatch.setattr(settings, "debug", False)


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


def _discovery(**endpoints: str) -> dict[str, Any]:
    """A stored discovery document of the configured issuer, with *endpoints* in it."""
    return {
        "issuer": ISSUER,
        "authorization_endpoint": f"{ISSUER}/authorize",
        "token_endpoint": f"{ISSUER}/token",
        "jwks_uri": f"{ISSUER}/jwks",
        **endpoints,
    }


def _login_world(idp: FakeIdp, **update: Any) -> _World:
    """The linked account at corp-a, its configuration changed by *update*."""
    world = _world(idp)
    config = world.configs.by_slug["corp-a"].model_copy(update=update)
    world.configs.by_slug["corp-a"] = config
    return world


def _refusal_reasons(world: _World, idp: FakeIdp) -> tuple[Any, list[str]]:
    with structlog.testing.capture_logs() as logs:
        callback = _login(world, idp)
    return callback, [str(e["reason"]) for e in logs if e["event"] == "oauth_endpoint_refused"]


#: Endpoint origins a provider-supplied URL must never reach, with the path left off.
_INTERNAL = {
    "cloud metadata address": "https://169.254.169.254",
    "cloud metadata, IPv6": "https://[fd00:ec2::254]",
    "metadata address carried in IPv6": "https://[::ffff:169.254.169.254]",
    "another host that resolves to a private address": "https://internal.example",
}


def _internal(path: str) -> list[Any]:
    return [pytest.param(f"{origin}{path}", id=name) for name, origin in _INTERNAL.items()]


# ── the token endpoint (the client secret and the code) ──────────────────────


@pytest.mark.parametrize("token_endpoint", _internal("/token"))
def test_a_token_endpoint_the_discovery_document_points_at_internally_is_never_sent_the_secret(
    idp: FakeIdp, token_endpoint: str
) -> None:
    idp.dns = {"internal.example": "10.0.0.5"}
    world = _login_world(idp, token_url=None, discovery_document=_discovery(token_endpoint=token_endpoint))

    callback, reasons = _refusal_reasons(world, idp)

    _refused(world, callback)
    assert idp.token_requests == []
    assert len(reasons) == 1 and reasons[0].startswith("The token endpoint"), reasons


def test_a_self_hosted_provider_may_take_the_code_on_its_own_private_host(idp: FakeIdp) -> None:
    """The one case a provider-supplied endpoint may be private: the issuer's own host."""
    idp.dns = {"idp-a.example": "10.0.0.5"}
    world = _login_world(idp, token_url=None, discovery_document=_discovery())

    assert _signed_in(world, _login(world, idp))
    assert len(idp.token_requests) == 1


@pytest.mark.parametrize(
    "token_url",
    [
        pytest.param("https://169.254.169.254/token", id="cloud metadata address"),
        pytest.param("https://metadata.example/token", id="a name that resolves to the metadata address"),
    ],
)
def test_a_configured_token_endpoint_on_the_metadata_address_is_never_sent_the_secret(
    idp: FakeIdp, token_url: str
) -> None:
    idp.dns = {"metadata.example": "169.254.169.254"}
    world = _login_world(idp, token_url=token_url)

    callback, _reasons = _refusal_reasons(world, idp)

    _refused(world, callback)
    assert idp.token_requests == []


def test_a_configured_token_endpoint_on_a_private_host_is_the_admins_choice(idp: FakeIdp) -> None:
    idp.dns = {"sso.lan.example": "10.0.0.7"}
    world = _login_world(idp, token_url="https://sso.lan.example/token")

    assert _signed_in(world, _login(world, idp))
    assert len(idp.token_requests) == 1


def test_a_token_response_larger_than_the_cap_is_refused(idp: FakeIdp) -> None:
    idp.token_padding = jwks_cache.JWKS_MAX_BYTES + 1
    world = _login_world(idp)

    callback, _reasons = _refusal_reasons(world, idp)

    _refused(world, callback)


def test_a_token_response_just_inside_the_cap_is_accepted(idp: FakeIdp) -> None:
    idp.token_padding = jwks_cache.JWKS_MAX_BYTES - 4096
    world = _login_world(idp)

    assert _signed_in(world, _login(world, idp))


def test_the_token_request_asks_for_an_uncompressed_body(idp: FakeIdp) -> None:
    """The cap counts decoded bytes, and a decoder inflates a whole raw chunk at once."""
    world = _login_world(idp)

    assert _signed_in(world, _login(world, idp))
    assert [h["accept-encoding"] for h in idp.token_request_headers] == ["identity"]


# ── the userinfo endpoint (the access token) ─────────────────────────────────


def _userinfo_world(idp: FakeIdp, **update: Any) -> _World:
    world = _login_world(idp, **update)
    idp.userinfo = {"sub": SUB, "email": world.email, "email_verified": True}
    return world


@pytest.mark.parametrize("userinfo_endpoint", _internal("/userinfo"))
def test_a_userinfo_endpoint_the_discovery_document_points_at_internally_is_never_sent_the_token(
    idp: FakeIdp, userinfo_endpoint: str
) -> None:
    idp.dns = {"internal.example": "10.0.0.5"}
    world = _userinfo_world(idp, discovery_document=_discovery(userinfo_endpoint=userinfo_endpoint))

    callback, reasons = _refusal_reasons(world, idp)

    _refused(world, callback)
    assert idp.userinfo_requests == 0
    assert idp.userinfo_request_headers == []
    assert len(reasons) == 1 and reasons[0].startswith("The userinfo endpoint"), reasons


def test_a_userinfo_endpoint_on_the_issuers_own_private_host_is_read(idp: FakeIdp) -> None:
    idp.dns = {"idp-a.example": "10.0.0.5"}
    world = _userinfo_world(idp, discovery_document=_discovery(userinfo_endpoint=f"{ISSUER}/userinfo"))

    assert _signed_in(world, _login(world, idp))
    assert idp.userinfo_requests == 1


def test_a_configured_userinfo_endpoint_on_the_metadata_address_is_never_sent_the_token(idp: FakeIdp) -> None:
    world = _userinfo_world(idp, userinfo_url="https://169.254.169.254/userinfo")

    callback, _reasons = _refusal_reasons(world, idp)

    _refused(world, callback)
    assert idp.userinfo_requests == 0


def test_a_configured_userinfo_endpoint_on_a_private_host_is_the_admins_choice(idp: FakeIdp) -> None:
    idp.dns = {"sso.lan.example": "10.0.0.7"}
    world = _userinfo_world(idp, userinfo_url="https://sso.lan.example/userinfo")

    assert _signed_in(world, _login(world, idp))
    assert idp.userinfo_requests == 1


def test_a_userinfo_answer_larger_than_the_cap_is_refused(idp: FakeIdp) -> None:
    world = _userinfo_world(idp, userinfo_url=f"{ISSUER}/userinfo")
    idp.userinfo_padding = jwks_cache.JWKS_MAX_BYTES + 1

    callback, _reasons = _refusal_reasons(world, idp)

    _refused(world, callback)


def test_the_userinfo_request_asks_for_an_uncompressed_body(idp: FakeIdp) -> None:
    world = _userinfo_world(idp, userinfo_url=f"{ISSUER}/userinfo")

    assert _signed_in(world, _login(world, idp))
    assert [h["accept-encoding"] for h in idp.userinfo_request_headers] == ["identity"]


# ── the step-up exchanges a code at the same endpoint ────────────────────────


def _step_up(idp: FakeIdp, **update: Any):  # noqa: ANN202
    """A step-up at corp-a with the real engine; returns the callback."""
    world = _oidc_world(("corp-a", "sub-a", ISSUER))
    engine = OAuthEngine()
    world.engine = engine  # type: ignore[assignment]
    world.auth._oauth_engine = engine
    world.configs.by_slug["corp-a"] = CORP_A.model_copy(update=update)
    started = world.start(provider_key=world.rows["corp-a"].key)
    assert started.status_code == 200, started.text
    query = parse_qs(urlsplit(started.json()["authorization_url"]).query)
    now = int(time.time())
    idp.claims = {
        "iss": ISSUER,
        "aud": CLIENT_ID,
        "sub": "sub-a",
        "nonce": query["nonce"][0],
        "iat": now,
        "exp": now + 600,
        "auth_time": now,
    }
    return world.callback(query["state"][0])


def test_a_step_up_never_sends_the_secret_to_a_metadata_token_endpoint_of_the_discovery_document(
    idp: FakeIdp,
) -> None:
    callback = _step_up(
        idp, token_url=None, discovery_document=_discovery(token_endpoint="https://169.254.169.254/token")
    )

    assert _error_of(callback) == "step_up_failed"
    assert idp.token_requests == []


def test_a_step_up_at_an_acceptable_discovery_token_endpoint_still_confirms(idp: FakeIdp) -> None:
    callback = _step_up(idp, token_url=None, discovery_document=_discovery())

    assert "step_up_token=" in callback.headers["location"], callback.headers["location"]
    assert len(idp.token_requests) == 1


# ── the discovery document itself (class sweep of #2007) ─────────────────────


def test_an_issuer_that_resolves_to_the_metadata_address_is_never_asked_for_its_document(idp: FakeIdp) -> None:
    """The admin typed the issuer, so a private address is theirs; the metadata address is nobody's."""
    idp.dns = {"idp-a.example": "169.254.169.254"}

    with pytest.raises(InsecureEndpointError):
        OAuthEngine().fetch_discovery_document(ISSUER)

    assert idp.discovery_requests == []


def test_an_issuer_on_a_private_host_still_serves_its_document(idp: FakeIdp) -> None:
    idp.dns = {"idp-a.example": "10.0.0.5"}

    document = OAuthEngine().fetch_discovery_document(ISSUER)

    assert document["issuer"] == ISSUER
    assert idp.discovery_requests == [ISSUER]
