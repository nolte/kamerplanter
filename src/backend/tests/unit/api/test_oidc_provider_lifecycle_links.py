"""#1935 / #1969 — what deleting and repointing an OIDC provider configuration leaves behind.

**#1935.** A provider link is matched by (configuration slug, ``sub``) and, where it
recorded one, the issuer (#1869). Deleting a configuration removed only the
configuration document: its links stayed bound to the slug, and a configuration
created later under the *same slug* — possibly at another IdP — inherited them. A
link that had never recorded its issuer (bound by migration v0064, or made without
an ID token) was not protected: an identity at the new IdP whose ``sub`` equalled the
link's signed in as the link's owner.

**#1969.** Repointing a configuration's issuer wrote only the changed fields, so the
discovery document of the *old* issuer stayed stored and, for a provider without
explicit endpoints, still steered sign-in (authorization, token and userinfo
endpoints) and the expected ``iss``. And ``fetch_discovery_document`` accepted any
JSON — OIDC Discovery 4.3 requires the document's ``issuer`` to equal the issuer it
was fetched from.

The service and router are the real ones; the repositories are in-memory doubles
that merge like the Arango ones (``update_fields`` keeps ``None``).
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest
from cryptography.fernet import Fernet

from app.api.v1.auth.router import limiter
from app.common.exceptions import DuplicateError, NotFoundError
from app.domain.engines.encryption_engine import EncryptionEngine
from app.domain.engines.oauth_engine import OAuthEngine
from app.domain.models.oidc_config import OidcProviderConfig
from app.domain.models.user import User
from app.domain.services.oidc_provider_admin_service import OidcProviderAdminService
from tests.support.oidc_idp import FakeIdp
from tests.support.step_up import STEP_UP_PASSED, PassedStepUpVerifier
from tests.unit.api.test_oauth_login_binding import _RegisteringUsers
from tests.unit.api.test_step_up_oidc_reauth import CLIENT_ID, FRONTEND, _oidc_world, _World

ISSUER_A = "https://idp-a.example"
ISSUER_B = "https://idp-b.example"


@pytest.fixture(autouse=True)
def _public_base_url(monkeypatch: pytest.MonkeyPatch):
    from app.config.settings import settings

    monkeypatch.setattr(settings, "app_base_url", "https://kamerplanter.example")


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


class _ConfigStore:
    """``IOidcConfigRepository`` over a dict: stateful, merging like the Arango repository."""

    def __init__(self, *configs: OidcProviderConfig) -> None:
        self.rows = {c.key: c for c in configs if c.key}
        self._next = 0

    @property
    def by_slug(self) -> dict[str, OidcProviderConfig]:
        return {c.slug: c for c in self.rows.values()}

    def get_by_key(self, key: str) -> OidcProviderConfig | None:
        return self.rows.get(key)

    def get_by_slug(self, slug: str) -> OidcProviderConfig | None:
        return self.by_slug.get(slug)

    def list_all(self) -> list[OidcProviderConfig]:
        return list(self.rows.values())

    def list_enabled(self) -> list[OidcProviderConfig]:
        return [c for c in self.rows.values() if c.enabled]

    def create(self, config: OidcProviderConfig) -> OidcProviderConfig:
        """Refuses a second configuration of one slug, as the collection's unique index does (#1987)."""
        if config.slug in self.by_slug:
            raise DuplicateError("OidcProviderConfig", "slug", config.slug)
        self._next += 1
        stored = config.model_copy(update={"key": f"cfg-new-{self._next}"})
        self.rows[stored.key] = stored  # type: ignore[index]
        return stored

    def update_fields(self, key: str, fields: dict[str, Any]) -> OidcProviderConfig:
        merged = OidcProviderConfig.model_validate({**self.rows[key].model_dump(by_alias=True), **fields})
        self.rows[key] = merged
        return merged

    def update_discovery(
        self, key: str, *, issuer_url: str, discovery_document: dict[str, Any], refreshed_at: datetime
    ) -> bool:
        current = self.rows.get(key)
        if current is None or current.issuer_url != issuer_url:
            return False
        self.update_fields(key, {"discovery_document": discovery_document, "discovery_refreshed_at": refreshed_at})
        return True

    def delete(self, key: str) -> bool:
        return self.rows.pop(key, None) is not None


def _service(configs: _ConfigStore, world: _World) -> OidcProviderAdminService:
    return OidcProviderAdminService(
        configs,
        EncryptionEngine(Fernet.generate_key().decode()),
        OAuthEngine(),
        PassedStepUpVerifier(),  # type: ignore[arg-type]
        world.providers,  # type: ignore[arg-type]
    )


ADMIN = User.model_validate({"_key": "admin", "email": "admin@example.org", "display_name": "Admin"})


def _create_body(slug: str, issuer: str) -> dict[str, Any]:
    return {
        "slug": slug,
        "display_name": slug,
        "provider_type": "oidc",
        "issuer_url": issuer,
        "client_id": CLIENT_ID,
        "client_secret": "secret",
        "scopes": ["openid", "email", "profile"],
        "enabled": True,
        "authorization_url": f"{issuer}/authorize",
        "token_url": f"{issuer}/token",
    }


def _create(service: OidcProviderAdminService, slug: str, issuer: str) -> OidcProviderConfig:
    return service.create_provider(_create_body(slug, issuer), requester=ADMIN, client_ip=None, **STEP_UP_PASSED)


def _delete(service: OidcProviderAdminService, key: str) -> None:
    service.delete_provider(key, requester=ADMIN, client_ip=None, **STEP_UP_PASSED)


def _update(service: OidcProviderAdminService, key: str, data: dict[str, Any]) -> OidcProviderConfig:
    return service.update_provider(key, data, requester=ADMIN, client_ip=None, **STEP_UP_PASSED)


def _stored(slug: str = "corp-a", issuer: str = ISSUER_A, **extra: Any) -> OidcProviderConfig:
    return OidcProviderConfig(
        _key=f"cfg-{slug}",
        slug=slug,
        display_name=slug,
        provider_type="oidc",
        issuer_url=issuer,
        client_id=CLIENT_ID,
        client_secret_encrypted="enc",
        enabled=True,
        **extra,
    )


# ══ #1935 ═══════════════════════════════════════════════════════════════════


def _login(world: _World, idp: FakeIdp, slug: str, issuer: str, **claims: Any):  # noqa: ANN202
    started = world.client().get(f"/api/v1/auth/oauth/{slug}", follow_redirects=False)
    assert started.status_code == 302, started.text
    query = parse_qs(urlsplit(started.headers["location"]).query)
    now = int(time.time())
    idp.claims = {"iss": issuer, "aud": CLIENT_ID, "nonce": query["nonce"][0], "iat": now, "exp": now + 600, **claims}
    return world.client().get(
        f"/api/v1/auth/oauth/{slug}/callback?code=provider-code&state={query['state'][0]}", follow_redirects=False
    )


def _session_user(world: _World, callback) -> str | None:  # noqa: ANN001
    if callback.headers["location"] != f"{FRONTEND}/auth/callback":
        return None
    (call,) = world.refresh_tokens.create.call_args_list
    return call.args[0].user_key


def test_a_configuration_re_created_under_a_deleted_slug_inherits_none_of_its_links(idp: FakeIdp) -> None:
    """The acceptance of #1935, end to end: a link without an issuer, delete, re-create at another IdP, sign in."""
    world = _oidc_world(("corp-a", "sub-a", None))
    world.engine = OAuthEngine()  # type: ignore[assignment]
    world.auth._oauth_engine = world.engine
    registering = _RegisteringUsers(world)
    configs = _ConfigStore(_stored())
    world.configs = configs  # type: ignore[assignment]
    world.auth._oidc_config_repo = configs  # type: ignore[assignment]
    service = _service(configs, world)

    _delete(service, "cfg-corp-a")
    _create(service, "corp-a", ISSUER_B)
    callback = _login(world, idp, "corp-a", ISSUER_B, sub="sub-a", email="intruder@example.net", email_verified=True)

    signed_in = _session_user(world, callback)
    assert signed_in is not None
    assert signed_in != world.key
    assert [u.email for u in registering.created] == ["intruder@example.net"]
    # The old owner's link is gone, not merely unused: nothing is bound to the slug but the stranger's own.
    assert [(r.user_key, r.oidc_config_slug) for r in world.providers.rows if r.oidc_config_slug == "corp-a"] == [
        (signed_in, "corp-a")
    ]


def test_deleting_a_configuration_deletes_exactly_the_links_bound_to_its_slug() -> None:
    world = _oidc_world(("corp-a", "sub-a", None), ("corp-b", "sub-b", ISSUER_B), (None, "sub-legacy", None))
    configs = _ConfigStore(_stored(), _stored("corp-b", ISSUER_B))
    service = _service(configs, world)

    _delete(service, "cfg-corp-a")

    mine = [(r.oidc_config_slug, r.provider_user_id) for r in world.providers.list_by_user(world.key)]
    assert sorted(mine, key=str) == [("corp-b", "sub-b"), (None, "sub-legacy")]
    assert list(configs.by_slug) == ["corp-b"]


def test_the_deletion_log_names_the_count_and_no_account(idp: FakeIdp) -> None:
    import structlog

    world = _oidc_world(("corp-a", "sub-secret-value", None))
    service = _service(_ConfigStore(_stored()), world)

    with structlog.testing.capture_logs() as logs:
        _delete(service, "cfg-corp-a")

    (line,) = [entry for entry in logs if entry["event"] == "oidc_provider.deleted"]
    assert line["provider"] == "corp-a"
    assert line["links_deleted"] == 1
    assert "sub-secret-value" not in str(line)
    assert world.key not in str(line)


def test_a_refused_deletion_deletes_no_link() -> None:
    """The step-up runs first: a request it refuses leaves the configuration and every link in place."""
    world = _oidc_world(("corp-a", "sub-a", None))
    configs = _ConfigStore(_stored())
    service = _service(configs, world)

    with pytest.raises(NotFoundError):
        _delete(service, "no-such-key")

    assert [r.provider_user_id for r in world.providers.list_by_user(world.key)] == ["sub-a"]
    assert list(configs.by_slug) == ["corp-a"]


def test_creating_a_configuration_purges_links_orphaned_by_an_earlier_deletion() -> None:
    """Links left by a deletion made before #1935 are still bound to the slug: a re-creation clears them."""
    world = _oidc_world(("gone", "sub-orphan", None))
    configs = _ConfigStore()
    service = _service(configs, world)

    _create(service, "gone", ISSUER_B)

    assert [r for r in world.providers.rows if r.oidc_config_slug == "gone"] == []


def test_a_repoint_deletes_the_links_without_an_issuer_and_keeps_those_with_one(idp: FakeIdp) -> None:
    """A link with no recorded issuer matches any issuer: the first sign-in from the new IdP would claim it."""
    world = _oidc_world(("corp-a", "sub-bare", None), ("corp-a", "sub-bound", ISSUER_A))
    configs = _ConfigStore(_stored())
    service = _service(configs, world)

    _update(service, "cfg-corp-a", {"issuer_url": ISSUER_B})

    assert [r.provider_user_id for r in world.providers.list_by_user(world.key)] == ["sub-bound"]


def test_a_change_that_keeps_the_issuer_deletes_no_link() -> None:
    world = _oidc_world(("corp-a", "sub-bare", None))
    service = _service(_ConfigStore(_stored()), world)

    _update(service, "cfg-corp-a", {"display_name": "Renamed"})

    assert [r.provider_user_id for r in world.providers.list_by_user(world.key)] == ["sub-bare"]


# ══ #1969 ═══════════════════════════════════════════════════════════════════

_DISCOVERY_A = {
    "issuer": ISSUER_A,
    "authorization_endpoint": f"{ISSUER_A}/authorize",
    "token_endpoint": f"{ISSUER_A}/token",
    "userinfo_endpoint": f"{ISSUER_A}/userinfo",
    "jwks_uri": f"{ISSUER_A}/jwks",
}


def _discovered() -> OidcProviderConfig:
    """A generic provider with no explicit endpoints: discovery steers it."""
    return _stored(discovery_document=dict(_DISCOVERY_A), discovery_refreshed_at=datetime.now(UTC))


def test_the_sign_in_does_not_use_the_old_issuers_endpoints_after_a_repoint() -> None:
    """Measured through the real login entry: the redirect goes to the NEW issuer's authorization endpoint."""
    world = _oidc_world()
    configs = _ConfigStore(_discovered())
    world.configs = configs  # type: ignore[assignment]
    world.auth._oidc_config_repo = configs  # type: ignore[assignment]
    service = _service(configs, world)

    _update(service, "cfg-corp-a", {"issuer_url": ISSUER_B})
    started = world.client().get("/api/v1/auth/oauth/corp-a", follow_redirects=False)

    # No endpoint of the new issuer is known yet (the next discovery refresh or the
    # admin test fetches it); what must not happen is a redirect to the OLD one.
    assert "idp-a.example" not in started.headers.get("location", "")


def test_a_repoint_clears_the_stored_discovery_document_in_the_same_write() -> None:
    world = _oidc_world()
    configs = _ConfigStore(_discovered())
    service = _service(configs, world)

    updated = _update(service, "cfg-corp-a", {"issuer_url": ISSUER_B})

    assert updated.discovery_document is None
    assert updated.discovery_refreshed_at is None
    assert configs.rows["cfg-corp-a"].discovery_document is None


def test_a_change_of_provider_type_clears_the_stored_discovery_document() -> None:
    world = _oidc_world()
    configs = _ConfigStore(_discovered())
    service = _service(configs, world)

    updated = _update(service, "cfg-corp-a", {"provider_type": "google"})

    assert updated.discovery_document is None


def test_a_change_that_does_not_move_the_issuer_keeps_the_discovery_document() -> None:
    world = _oidc_world()
    configs = _ConfigStore(_discovered())
    service = _service(configs, world)

    updated = _update(service, "cfg-corp-a", {"display_name": "Renamed", "client_id": "another"})

    assert updated.discovery_document == _DISCOVERY_A


def test_a_stored_document_of_another_issuer_is_not_used_for_the_endpoints_or_the_expected_iss() -> None:
    """A document stored before the clearing existed: the engine does not trust it for a repointed provider."""
    stale = _stored(issuer=ISSUER_B, discovery_document=dict(_DISCOVERY_A))
    engine = OAuthEngine()

    with pytest.raises(ValueError, match="authorization URL"):
        engine.build_authorization_url(stale, "https://kamerplanter.example/cb")
    assert engine.expected_issuers(stale) == frozenset({ISSUER_B})


def test_a_stored_document_that_names_no_issuer_is_not_used() -> None:
    no_issuer = _stored(discovery_document={k: v for k, v in _DISCOVERY_A.items() if k != "issuer"})

    with pytest.raises(ValueError, match="authorization URL"):
        OAuthEngine().build_authorization_url(no_issuer, "https://kamerplanter.example/cb")


@pytest.mark.parametrize(
    ("document", "why"),
    [
        pytest.param({**_DISCOVERY_A, "issuer": "https://idp-evil.example"}, "issuer", id="another issuer"),
        pytest.param({k: v for k, v in _DISCOVERY_A.items() if k != "issuer"}, "issuer", id="no issuer"),
        pytest.param({k: v for k, v in _DISCOVERY_A.items() if k != "token_endpoint"}, "token_endpoint", id="no token"),
        pytest.param({k: v for k, v in _DISCOVERY_A.items() if k != "jwks_uri"}, "jwks_uri", id="no jwks"),
        pytest.param({**_DISCOVERY_A, "token_endpoint": "http://idp-a.example/token"}, "not https", id="http token"),
        pytest.param(["not", "an", "object"], "JSON object", id="a list"),
    ],
)
def test_a_discovery_document_that_is_not_the_issuers_is_rejected(
    monkeypatch: pytest.MonkeyPatch, document: Any, why: str
) -> None:
    import ipaddress

    import httpx

    from app.common import url_safety
    from app.domain.engines import oauth_engine
    from tests.support.oidc_idp import PUBLIC_ADDRESS

    real = httpx.Client
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=document))
    monkeypatch.setattr(oauth_engine.httpx, "Client", lambda *a, **k: real(*a, **{**k, "transport": transport}))
    # The issuer is resolved before it is dialled (#2007): without this double an unresolvable
    # fixture host would raise "issuer host could not be resolved" — which matches ``why="issuer"``
    # and would pass two of these cases without the document ever being read.
    monkeypatch.setattr(url_safety, "_resolved_addresses", lambda host: [ipaddress.ip_address(PUBLIC_ADDRESS)])

    with pytest.raises(ValueError, match=why):
        OAuthEngine().fetch_discovery_document(ISSUER_A)


def test_the_issuers_own_document_is_accepted(idp: FakeIdp) -> None:
    document = OAuthEngine().fetch_discovery_document(ISSUER_A)

    assert document["issuer"] == ISSUER_A
    assert document["jwks_uri"] == f"{ISSUER_A}/jwks"


def test_the_rotation_counts_a_foreign_document_as_an_error_and_writes_nothing(
    monkeypatch: pytest.MonkeyPatch, idp: FakeIdp
) -> None:
    from app.common import dependencies
    from app.tasks.auth_tasks import rotate_oidc_discovery

    idp.discovery_extra = {"issuer": "https://idp-evil.example"}
    configs = _ConfigStore(_stored())
    monkeypatch.setattr(dependencies, "get_oidc_config_repo", lambda: configs)
    monkeypatch.setattr(dependencies, "get_oauth_engine", OAuthEngine)

    result = rotate_oidc_discovery()

    assert result == {"updated": 0, "errors": 1}
    assert configs.rows["cfg-corp-a"].discovery_document is None


def test_the_admin_test_route_rejects_a_foreign_document_and_stores_nothing(idp: FakeIdp) -> None:
    from tests.support.oidc_admin import admin_client

    idp.discovery_extra = {"issuer": "https://idp-evil.example"}
    config = _stored()
    configs = _ConfigStore(config)
    from unittest.mock import MagicMock

    repo = MagicMock(wraps=configs)
    client = admin_client(repo)

    response = client.post(f"/api/v1/admin/oidc-providers/{config.key}/test")

    assert response.status_code == 200, response.text
    assert "Discovery fetch failed" in response.json()["message"]
    assert configs.rows[config.key].discovery_document is None  # type: ignore[index]
