"""#1987 item 2 — a provider link belongs to the configuration it was made through, not to a slug that can be re-used.

The callback loads the configuration once and writes the link seconds later, keyed by the
configuration's ``slug``. An admin who deletes the provider and creates another under the same slug in
between (the slug is the URL segment of ``/auth/oauth/{slug}`` and is free to re-use) used to end up with a
link — and, for a new identity, an account — under the *new* configuration, made through the old one's
trust. And two admins creating one slug at once: the loser's ``get_by_slug`` check had already passed, and
it purged the winner's links before its own ``create`` failed on the unique index.

Real service, router and engine; the repositories are the in-memory doubles of the lifecycle suite
(the configuration store refuses a second configuration of a slug, as the unique index does).
"""

from __future__ import annotations

from typing import Any

import pytest

from app.api.v1.auth.router import limiter
from app.common.enums import AuthProviderType
from app.common.exceptions import DuplicateError
from app.domain.engines.oauth_engine import OAuthEngine
from app.domain.models.oidc_config import OidcProviderConfig
from app.domain.services.oidc_provider_admin_service import OidcProviderAdminService
from tests.support.oidc_idp import FakeIdp
from tests.unit.api.test_oidc_provider_lifecycle_links import (
    ADMIN,
    ISSUER_A,
    ISSUER_B,
    _ConfigStore,
    _create,
    _delete,
    _login,
    _RegisteringUsers,
    _service,
    _session_user,
    _stored,
)
from tests.unit.api.test_step_up_oidc_reauth import _oidc_world, _World


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


def _cfg(slug: str = "corp-a", issuer: str = ISSUER_A) -> OidcProviderConfig:
    """A stored configuration the login can start at: explicit endpoints, like the ones ``_create_body`` makes."""
    return _stored(slug, issuer, authorization_url=f"{issuer}/authorize", token_url=f"{issuer}/token")


def _world_with_configs(*configs: OidcProviderConfig) -> tuple[_World, _ConfigStore, OidcProviderAdminService]:
    world = _oidc_world()
    engine = OAuthEngine()
    world.engine = engine  # type: ignore[assignment]
    world.auth._oauth_engine = engine
    store = _ConfigStore(*configs)
    world.configs = store  # type: ignore[assignment]
    world.auth._oidc_config_repo = store  # type: ignore[assignment]
    return world, store, _service(store, world)


def _recreate(service: OidcProviderAdminService, old_key: str, slug: str, issuer: str) -> None:
    _delete(service, old_key)
    _create(service, slug, issuer)


def _links_of(world: _World, slug: str) -> list[Any]:
    return [r for r in world.providers.rows if r.oidc_config_slug == slug]


# ── the callback ─────────────────────────────────────────────────────────────


def test_a_login_in_flight_while_the_slug_is_re_created_writes_no_link_and_no_account(idp: FakeIdp) -> None:
    """The configuration is loaded, the provider answers — and meanwhile the slug is deleted and re-created."""
    world, store, service = _world_with_configs(_cfg())
    registering = _RegisteringUsers(world)
    idp.on_token_request = lambda: _recreate(service, "cfg-corp-a", "corp-a", ISSUER_A)

    callback = _login(world, idp, "corp-a", ISSUER_A, sub="new-identity", email="newcomer@example.net")

    assert _session_user(world, callback) is None
    assert _links_of(world, "corp-a") == []
    assert registering.created == []
    assert store.by_slug["corp-a"].key != "cfg-corp-a"  # the re-creation did happen


def test_a_login_whose_configuration_was_switched_off_meanwhile_is_refused(idp: FakeIdp) -> None:
    world, store, _service_ = _world_with_configs(_cfg())
    registering = _RegisteringUsers(world)

    def switch_off() -> None:
        store.update_fields("cfg-corp-a", {"enabled": False})

    idp.on_token_request = switch_off

    callback = _login(world, idp, "corp-a", ISSUER_A, sub="new-identity", email="newcomer@example.net")

    assert _session_user(world, callback) is None
    assert registering.created == []


def test_a_link_is_stamped_with_the_key_of_the_configuration_it_was_made_through(idp: FakeIdp) -> None:
    world, _store, _service_ = _world_with_configs(_cfg())
    _RegisteringUsers(world)

    callback = _login(world, idp, "corp-a", ISSUER_A, sub="new-identity", email="newcomer@example.net")

    assert _session_user(world, callback) is not None
    (link,) = _links_of(world, "corp-a")
    assert (link.oidc_config_key, link.oidc_config_slug) == ("cfg-corp-a", "corp-a")


def test_a_link_that_lands_after_the_slug_was_re_created_is_not_inherited(idp: FakeIdp) -> None:
    """The window the re-verification cannot close: the re-creation happens INSIDE the link write."""
    world, store, service = _world_with_configs(_cfg())
    registering = _RegisteringUsers(world)
    real_create = world.providers.create

    def create_after_recreation(row: Any) -> Any:
        world.providers.create = real_create  # type: ignore[method-assign]
        _recreate(service, "cfg-corp-a", "corp-a", ISSUER_B)
        return real_create(row)

    world.providers.create = create_after_recreation  # type: ignore[method-assign]
    first = _login(world, idp, "corp-a", ISSUER_A, sub="victim-sub", email="victim@example.net")
    (orphan,) = _links_of(world, "corp-a")
    assert orphan.oidc_config_key == "cfg-corp-a"  # made through the configuration that is gone
    assert store.by_slug["corp-a"].key != "cfg-corp-a"
    assert first is not None

    # The new configuration (at another provider) sees an identity with the same sub.
    idp.on_token_request = None
    world.refresh_tokens.create.reset_mock()
    second = _login(world, idp, "corp-a", ISSUER_B, sub="victim-sub", email="intruder@example.net", email_verified=True)

    signed_in = _session_user(world, second)
    victim = registering.created[0].key
    assert signed_in != victim
    assert [r.oidc_config_key for r in _links_of(world, "corp-a")] == [store.by_slug["corp-a"].key]


def test_a_link_without_a_configuration_key_keeps_working_as_before(idp: FakeIdp) -> None:
    """Rows made before #1987 carry no key and are matched by slug, exactly as they were."""
    world = _oidc_world(("corp-a", "sub-a", ISSUER_A))
    engine = OAuthEngine()
    world.engine = engine  # type: ignore[assignment]
    world.auth._oauth_engine = engine
    store = _ConfigStore(_cfg())
    world.configs = store  # type: ignore[assignment]
    world.auth._oidc_config_repo = store  # type: ignore[assignment]

    callback = _login(world, idp, "corp-a", ISSUER_A, sub="sub-a", email=world.email, email_verified=True)

    assert _session_user(world, callback) == world.key


# ── two creations of one slug ────────────────────────────────────────────────


class _InterleavingVerifier:
    """The step-up of admin A, which is the moment admin B's creation of the same slug lands."""

    def __init__(self, between: Any) -> None:
        self._between = between
        self.ran = False

    def verify(self, requester: Any, *, action: str, target: str | None, **_: Any) -> str:
        if not self.ran:
            self.ran = True
            self._between()
        return "password"


def test_the_loser_of_two_concurrent_creations_purges_none_of_the_winners_links() -> None:
    world = _oidc_world()
    store = _ConfigStore()
    loser = OidcProviderAdminService(
        store,  # type: ignore[arg-type]
        _service(store, world)._encryption,
        OAuthEngine(),
        _InterleavingVerifier(lambda: _winner_creates_and_gets_a_link(_service(store, world), world)),  # type: ignore[arg-type]
        world.providers,  # type: ignore[arg-type]
    )

    with pytest.raises(DuplicateError):
        loser.create_provider(_body("corp-a"), requester=ADMIN, client_ip=None, **_PASSED)

    assert [r.provider_user_id for r in _links_of(world, "corp-a")] == ["winner-sub"]
    assert [c.slug for c in store.rows.values()] == ["corp-a"]


def _winner_creates_and_gets_a_link(winner: OidcProviderAdminService, world: _World) -> None:
    created = _create(winner, "corp-a", ISSUER_A)
    world.providers.add(world.key, AuthProviderType.OIDC, "winner-sub", config_slug="corp-a", issuer=ISSUER_A)
    assert created.slug == "corp-a"


_PASSED: dict[str, Any] = {
    "current_password": None,
    "step_up_code": None,
    "step_up_token": None,
    "authenticated_with_api_key": False,
}


def _body(slug: str) -> dict[str, Any]:
    from tests.unit.api.test_oidc_provider_lifecycle_links import _create_body

    return _create_body(slug, ISSUER_A)


def test_a_creation_still_purges_links_orphaned_by_an_earlier_deletion() -> None:
    world = _oidc_world(("gone", "sub-orphan", None))
    service = _service(_ConfigStore(), world)

    _create(service, "gone", ISSUER_B)

    assert _links_of(world, "gone") == []


def test_a_new_configuration_is_never_enabled_while_orphans_of_its_slug_still_exist() -> None:
    """Created switched off, purged, then switched on: a sign-in cannot meet the orphans of a re-used slug."""
    world = _oidc_world(("gone", "sub-orphan", None))
    seen: list[tuple[bool, int]] = []
    store = _ConfigStore()
    real_delete = world.providers.delete_by_config_slug

    def watching_delete(slug: str, **kwargs: Any) -> int:
        seen.append((store.by_slug[slug].enabled, len(_links_of(world, slug))))
        return real_delete(slug, **kwargs)

    world.providers.delete_by_config_slug = watching_delete  # type: ignore[method-assign]
    service = _service(store, world)

    created = _create(service, "gone", ISSUER_B)

    assert seen == [(False, 1)]  # at the purge: the configuration existed, switched off, with one orphan
    assert created.enabled is True
    assert store.by_slug["gone"].enabled is True


def test_a_failed_purge_leaves_no_configuration_behind() -> None:
    world = _oidc_world(("gone", "sub-orphan", None))
    store = _ConfigStore()

    def failing(slug: str, **kwargs: Any) -> int:
        raise RuntimeError("database went away")

    world.providers.delete_by_config_slug = failing  # type: ignore[method-assign]
    service = _service(store, world)

    with pytest.raises(RuntimeError):
        _create(service, "gone", ISSUER_B)

    assert store.rows == {}
