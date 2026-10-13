"""#1987 item 1 — an OIDC endpoint must be ``https``, at the API boundary and at login.

#1969 made the *fetched* discovery document refuse a non-https endpoint; an explicit
configuration was never held to the same rule: ``issuer_url``, ``authorization_url``,
``token_url``, ``userinfo_url`` were plain ``str``, and the login applied the TLS
check (``_token_endpoint_is_tls``) to the step-up only. Over ``http`` the discovery
document, the code exchange (which carries the client secret) and the key set can all
be answered by whoever sits on the path.

The create and update bodies now refuse such a URL with 422; loopback ``http`` is
allowed only when the application runs in ``settings.debug`` (the existing
development switch). A configuration stored before the rule — one an operator never
had to edit — is refused at login rather than dialled, and says so on the test route.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.api.v1.auth.router import limiter
from app.config.settings import settings
from tests.support.oidc_admin import BASE, admin_client, create_body, provider_repo, stored_provider
from tests.support.oidc_idp import FakeIdp
from tests.unit.api.test_oauth_login_id_token import _error, _login, _refused, _signed_in, _world

URL_FIELDS = ("issuer_url", "authorization_url", "token_url", "userinfo_url", "jwks_url")


@pytest.fixture(autouse=True)
def _limiter_off(monkeypatch: pytest.MonkeyPatch):
    limiter.reset()
    monkeypatch.setattr(limiter, "enabled", False)
    yield
    limiter.reset()


def _body(**overrides: Any) -> dict[str, Any]:
    return {**create_body(provider_type="oidc", scopes=["openid"]), "issuer_url": "https://idp.example", **overrides}


# ── the boundary ─────────────────────────────────────────────────────────────


@pytest.mark.parametrize("field", URL_FIELDS)
@pytest.mark.parametrize("url", ["http://idp.example/x", "ftp://idp.example/x", "idp.example/x", "https:///x"])
def test_create_refuses_a_non_https_url(field: str, url: str) -> None:
    repo = provider_repo()

    response = admin_client(repo).post(BASE, json=_body(**{field: url}))

    assert response.status_code == 422, response.text
    assert field in response.text
    repo.create.assert_not_called()


@pytest.mark.parametrize("field", URL_FIELDS)
def test_update_refuses_a_non_https_url(field: str) -> None:
    repo = provider_repo(stored_provider("oidc"))

    response = admin_client(repo).put(f"{BASE}/cfg1", json={field: "http://idp.example/x"})

    assert response.status_code == 422, response.text
    repo.update_fields.assert_not_called()


@pytest.mark.parametrize("field", URL_FIELDS)
def test_create_accepts_an_https_url(field: str) -> None:
    repo = provider_repo()

    response = admin_client(repo).post(BASE, json=_body(**{field: "https://idp.example/x"}))

    assert response.status_code == 201, response.text


@pytest.mark.parametrize("url", ["http://localhost:8080/realm", "http://127.0.0.1:8080/realm", "http://[::1]:8080/r"])
def test_loopback_http_is_a_development_convenience_only(monkeypatch: pytest.MonkeyPatch, url: str) -> None:
    monkeypatch.setattr(settings, "debug", False)
    refused = admin_client(provider_repo()).post(BASE, json=_body(issuer_url=url))
    monkeypatch.setattr(settings, "debug", True)
    allowed = admin_client(provider_repo()).post(BASE, json=_body(issuer_url=url))

    assert refused.status_code == 422, refused.text
    assert allowed.status_code == 201, allowed.text


def test_development_mode_does_not_allow_http_to_a_remote_host(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "debug", True)

    response = admin_client(provider_repo()).post(BASE, json=_body(issuer_url="http://idp.example"))

    assert response.status_code == 422, response.text


def test_a_host_that_only_starts_like_localhost_is_not_loopback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "debug", True)

    response = admin_client(provider_repo()).post(BASE, json=_body(issuer_url="http://localhost.evil.example"))

    assert response.status_code == 422, response.text


# ── at login: a stored explicit endpoint is held to the rule too ─────────────


@pytest.mark.parametrize(
    "stored",
    [
        pytest.param({"token_url": "http://idp-a.example/token"}, id="http token endpoint"),
        pytest.param({"jwks_url": "http://idp-a.example/jwks"}, id="http key endpoint"),
        pytest.param(
            {"userinfo_url": "http://idp-a.example/userinfo", "scopes": ["openid", "email"]},
            id="http userinfo endpoint",
        ),
    ],
)
def test_a_stored_http_endpoint_is_refused_at_login_and_never_dialled(
    idp_fixture: FakeIdp, stored: dict[str, Any]
) -> None:
    world = _world(idp_fixture, userinfo="userinfo_url" in stored)
    world.configs.by_slug["corp-a"] = world.configs.by_slug["corp-a"].model_copy(update=stored)

    callback = _login(world, idp_fixture)

    assert not _signed_in(world, callback)
    assert _error(callback) == "provider_error"
    _refused(world, callback)
    # A request to an http endpoint is the exposure: nothing was sent to it. (The token
    # request precedes the key request, which precedes the userinfo one — each case asserts
    # its own endpoint was not dialled.)
    dialled = {
        "token_url": len(idp_fixture.token_requests),
        "jwks_url": idp_fixture.jwks_requests,
        "userinfo_url": idp_fixture.userinfo_requests,
    }
    (endpoint,) = [name for name in dialled if name in stored]
    assert dialled[endpoint] == 0


def test_a_stored_http_authorization_endpoint_does_not_start_a_login(idp_fixture: FakeIdp) -> None:
    world = _world(idp_fixture)
    world.configs.by_slug["corp-a"] = world.configs.by_slug["corp-a"].model_copy(
        update={"authorization_url": "http://idp-a.example/authorize"}
    )

    started = world.client().get("/api/v1/auth/oauth/corp-a", follow_redirects=False)

    assert not started.headers.get("location", "").startswith("http://idp-a.example")
    assert started.status_code != 302 or "provider_error" in started.headers["location"]


@pytest.fixture
def idp_fixture(monkeypatch: pytest.MonkeyPatch) -> FakeIdp:
    provider = FakeIdp()
    provider.install(monkeypatch)
    return provider
