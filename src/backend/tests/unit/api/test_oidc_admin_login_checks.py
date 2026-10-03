"""#1987 items 5 and 6 — a pinned key endpoint, endpoints cleared on a repoint, the login verdicts of the test route.

``POST /admin/oidc-providers/{key}/test`` reports a verdict on the signing keys (``jwks_check``) and on
the issuer (``issuer_check``) next to the scope and type verdicts. They run the engine's real steps
against :class:`tests.support.oidc_idp.FakeIdp`, so an operator is told about a failing sign-in
check before the first user is turned away rather than from ``oauth_login_refused``.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.domain.engines import jwks_cache
from app.domain.models.oidc_config import OidcProviderConfig
from tests.support.oidc_admin import BASE, admin_client, create_body, provider_repo
from tests.support.oidc_idp import FakeIdp
from tests.unit.api.test_oidc_provider_lifecycle_links import (
    ISSUER_A,
    ISSUER_B,
    _ConfigStore,
    _service,
    _stored,
    _update,
)
from tests.unit.api.test_step_up_oidc_reauth import _oidc_world


@pytest.fixture
def idp(monkeypatch: pytest.MonkeyPatch) -> FakeIdp:
    provider = FakeIdp()
    provider.install(monkeypatch)
    return provider


def _config(**overrides: Any) -> OidcProviderConfig:
    base: dict[str, Any] = {
        "_key": "cfg1",
        "slug": "corp",
        "display_name": "Corp",
        "provider_type": "oidc",
        "issuer_url": ISSUER_A,
        "client_id": "cid",
        "scopes": ["openid", "email"],
    }
    return OidcProviderConfig.model_validate({**base, **overrides})


def _test(config: OidcProviderConfig) -> dict[str, Any]:
    response = admin_client(provider_repo(config)).post(f"{BASE}/{config.key}/test")
    assert response.status_code == 200, response.text
    return response.json()


# ── jwks_url through the schemas ─────────────────────────────────────────────


def test_the_key_endpoint_can_be_pinned_on_create() -> None:
    repo = provider_repo()

    response = admin_client(repo).post(
        BASE, json=create_body(provider_type="oidc", scopes=["openid"], jwks_url="https://idp.example/keys")
    )

    assert response.status_code == 201, response.text
    assert repo.create.call_args.args[0].jwks_url == "https://idp.example/keys"


def test_the_key_endpoint_can_be_pinned_on_update() -> None:
    repo = provider_repo(_config())

    response = admin_client(repo).put(f"{BASE}/cfg1", json={"jwks_url": "https://idp-a.example/keys"})

    assert response.status_code == 200, response.text
    assert repo.update_fields.call_args.args[1] == {"jwks_url": "https://idp-a.example/keys"}


# ── a repoint clears the old issuer's explicit endpoints ─────────────────────


def _explicit(**extra: Any) -> OidcProviderConfig:
    return _stored(
        authorization_url=f"{ISSUER_A}/authorize",
        token_url=f"{ISSUER_A}/token",
        userinfo_url=f"{ISSUER_A}/userinfo",
        jwks_url=f"{ISSUER_A}/keys",
        **extra,
    )


def test_a_repoint_clears_the_explicit_endpoints_of_the_old_issuer() -> None:
    world = _oidc_world()
    configs = _ConfigStore(_explicit())

    updated = _update(_service(configs, world), "cfg-corp-a", {"issuer_url": ISSUER_B})

    assert (updated.authorization_url, updated.token_url, updated.userinfo_url, updated.jwks_url) == (None,) * 4
    stored = configs.rows["cfg-corp-a"]
    assert (stored.authorization_url, stored.token_url, stored.userinfo_url, stored.jwks_url) == (None,) * 4


def test_a_repoint_keeps_the_endpoints_the_same_request_names() -> None:
    world = _oidc_world()
    configs = _ConfigStore(_explicit())

    updated = _update(
        _service(configs, world),
        "cfg-corp-a",
        {"issuer_url": ISSUER_B, "token_url": f"{ISSUER_B}/token", "jwks_url": f"{ISSUER_B}/keys"},
    )

    assert updated.token_url == f"{ISSUER_B}/token"
    assert updated.jwks_url == f"{ISSUER_B}/keys"
    assert (updated.authorization_url, updated.userinfo_url) == (None, None)


@pytest.mark.parametrize("spelling", [ISSUER_A + "/", "idp-a.example"])
def test_a_respelling_of_the_same_issuer_clears_nothing(spelling: str) -> None:
    """Judged the way the login judges an ``iss``: a trailing ``/`` or a missing scheme is the same issuer."""
    world = _oidc_world()
    configs = _ConfigStore(_explicit())

    updated = _update(_service(configs, world), "cfg-corp-a", {"issuer_url": spelling})

    assert updated.token_url == f"{ISSUER_A}/token"
    assert updated.jwks_url == f"{ISSUER_A}/keys"


def test_a_change_that_leaves_the_issuer_alone_clears_nothing() -> None:
    world = _oidc_world()
    configs = _ConfigStore(_explicit())

    updated = _update(_service(configs, world), "cfg-corp-a", {"display_name": "Renamed", "client_id": "other"})

    assert updated.token_url == f"{ISSUER_A}/token"


# ── POST /{key}/test ─────────────────────────────────────────────────────────


def test_a_healthy_provider_reports_its_keys_and_an_accepted_issuer(idp: FakeIdp) -> None:
    body = _test(_config())

    assert body["jwks_check"] == {
        "ok": True,
        "applicable": True,
        "jwks_url": f"{ISSUER_A}/jwks",
        "key_count": 1,
        "skipped_key_count": 0,
        "key_ids": [idp.kid],
        "detail": "1 usable key(s) fetched.",
    }
    assert body["issuer_check"]["ok"] is True
    assert body["issuer_check"]["discovery_issuer"] == ISSUER_A
    assert body["issuer_check"]["accepted_issuers"] == [ISSUER_A]


def test_the_report_counts_a_key_it_could_not_use(idp: FakeIdp) -> None:
    idp.bad_jwks_entries = [{"kty": "quantum", "kid": "q"}]

    check = _test(_config())["jwks_check"]

    assert (check["ok"], check["key_count"], check["skipped_key_count"]) == (True, 1, 1)
    assert "skipped" in check["detail"]


@pytest.mark.parametrize(
    ("setup", "expected"),
    [
        pytest.param(lambda idp: setattr(idp, "jwks_status", 500), "HTTPStatusError", id="the key endpoint fails"),
        pytest.param(lambda idp: setattr(idp, "jwks_padding", 10_000_000), "larger than the limit", id="far too large"),
        pytest.param(
            lambda idp: setattr(idp, "discovery_extra", {"jwks_uri": "https://169.254.169.254/jwks"}),
            "not acceptable",
            id="the metadata address",
        ),
        pytest.param(
            lambda idp: (setattr(idp, "published_kids", []), setattr(idp, "bad_jwks_entries", [{"kty": "quantum"}])),
            "no usable key",
            id="no usable key",
        ),
    ],
)
def test_a_key_set_the_login_could_not_use_is_reported_before_a_user_meets_it(
    idp: FakeIdp, setup: Any, expected: str
) -> None:
    setup(idp)

    check = _test(_config())["jwks_check"]

    assert check["ok"] is False
    assert expected in check["detail"]
    assert idp.jwks_requests <= 1


def test_an_issuer_the_provider_does_not_announce_is_reported_with_the_announced_one(idp: FakeIdp) -> None:
    idp.discovery_extra = {"issuer": "https://idp-a.example/realms/corp"}

    body = _test(_config())

    assert "Discovery fetch failed" in body["message"]
    check = body["issuer_check"]
    assert check["ok"] is False
    assert check["discovery_issuer"] == "https://idp-a.example/realms/corp"
    assert "every sign-in would be refused" in check["detail"]


def test_a_provider_whose_discovery_fails_still_has_its_pinned_key_endpoint_checked(idp: FakeIdp) -> None:
    idp.discovery_extra = {"issuer": "https://elsewhere.example"}

    body = _test(_config(jwks_url=f"{ISSUER_A}/jwks"))

    assert "Discovery fetch failed" in body["message"]
    assert body["jwks_check"]["ok"] is True
    assert body["jwks_check"]["jwks_url"] == f"{ISSUER_A}/jwks"


def test_without_a_discovery_document_or_a_pinned_endpoint_the_keys_cannot_be_resolved(idp: FakeIdp) -> None:
    idp.discovery_extra = {"issuer": "https://elsewhere.example"}

    check = _test(_config())["jwks_check"]

    assert check["ok"] is False
    assert "No key endpoint could be resolved" in check["detail"]


def test_a_stored_http_issuer_is_reported_not_dialled(idp: FakeIdp) -> None:
    body = _test(_config(issuer_url="http://idp-a.example"))

    assert "Discovery fetch failed" in body["message"]
    assert body["jwks_check"]["ok"] is False
    assert idp.discovery_requests == []
    assert idp.jwks_requests == 0


def test_a_provider_without_an_id_token_has_nothing_to_check(idp: FakeIdp) -> None:
    body = _test(_config(provider_type="github", issuer_url="https://github.com", scopes=["read:user", "user:email"]))

    for check in ("jwks_check", "issuer_check"):
        assert (body[check]["ok"], body[check]["applicable"]) == (True, False)
    assert idp.jwks_requests == 0


def test_the_test_route_does_not_fill_the_login_key_cache(idp: FakeIdp) -> None:
    _test(_config())

    assert idp.jwks_requests == 1
    assert jwks_cache._CACHE._entries == {}
