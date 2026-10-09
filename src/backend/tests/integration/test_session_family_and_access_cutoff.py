"""#2116 (MT-019): refresh-token families with replay detection, and access tokens that die with their session.

Measured before the change, against a real ArangoDB:

* rotation revoked the presented token and minted an unrelated one; a replayed
  rotated token was answered "unknown" (``get_by_hash`` filters ``revoked ==
  false``) while the chain it was stolen from stayed valid;
* ``logout_all``, ``revoke_session``, ``change_password`` and ``reset_password``
  revoked refresh tokens only - every access token minted before kept resolving
  to the account for the rest of its 15 minutes (``FullAuthProvider`` checked the
  signature, the expiry and ``is_active``, nothing else).

Driven through the real ``AuthService`` over the real user and refresh-token
repositories; the access tokens are resolved by the real ``FullAuthProvider``.

Runs in CI against the service container; locally it needs a database of its own
(``docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12``).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest
from arango import ArangoClient

from app.common.exceptions import InvalidTokenError, UnauthorizedError
from app.data_access.arango import collections as col
from app.data_access.arango.auth_provider_repository import ArangoAuthProviderRepository
from app.data_access.arango.refresh_token_repository import ArangoRefreshTokenRepository
from app.data_access.arango.user_repository import ArangoUserRepository
from app.domain.engines.full_auth_provider import FullAuthProvider
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.services.auth_service import AuthService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("session_family")
# Assembled at runtime: a literal shaped like a credential trips the secret scanner (#1838).
PASSWORD = " ".join(["Correct", "horse", "battery", "staple", "9!"])
NEW_PASSWORD = " ".join(["Another", "horse", "battery", "staple", "7?"])
ADDRESS = "owner@example.org"
BROWSER = "Mozilla/5.0 (X11; Linux x86_64) Firefox/131.0"
PHONE = "Mozilla/5.0 (Linux; Android 14) Chrome/129.0"

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
    for name in (col.USERS, col.AUTH_PROVIDERS, col.REFRESH_TOKENS, col.HAS_SESSION):
        database.collection(name).truncate()
    return database


class _World:
    def __init__(self, db) -> None:
        self.db = db
        self.users = ArangoUserRepository(db)
        self.sessions = ArangoRefreshTokenRepository(db)
        self.tokens = TokenEngine("k" * 64)
        self.service = AuthService(
            user_repo=self.users,
            auth_provider_repo=ArangoAuthProviderRepository(db),
            refresh_token_repo=self.sessions,
            password_engine=PasswordEngine(),
            token_engine=self.tokens,
            throttle_engine=LoginThrottleEngine(),
            email_service=MagicMock(),
            frontend_url="https://app.test",
            require_email_verification=False,
        )
        self.provider = FullAuthProvider(self.tokens, self.users, self.service)
        self.key = self.service.register_local(ADDRESS, PASSWORD, "Owner").key

    def login(self, user_agent: str = BROWSER) -> tuple[str, str]:
        pair, raw, _ = self.service.login_local(ADDRESS, PASSWORD, user_agent, "203.0.113.7")
        return pair.access_token, raw

    def refresh(self, raw: str, user_agent: str = BROWSER, *, allow_grace: bool = False) -> tuple[str, str | None]:
        # The keyword only when it is asked for, so the plain paths also run against a service without it.
        grace = {"allow_grace": True} if allow_grace else {}
        pair, new_raw, _ = self.service.refresh_tokens(raw, user_agent, "203.0.113.7", **grace)
        return pair.access_token, new_raw

    def resolves(self, access_token: str) -> bool:
        try:
            self.provider.resolve_user(f"Bearer {access_token}", client_ip=None)
        except UnauthorizedError:
            return False
        return True

    def stored(self, raw: str) -> dict:
        (doc,) = self.db.collection(col.REFRESH_TOKENS).find({"token_hash": self.tokens.hash_token(raw)})
        return doc

    def age_rotation(self, raw: str, seconds: int) -> None:
        doc = self.stored(raw)
        rotated = datetime.fromisoformat(doc["rotated_at"]) - timedelta(seconds=seconds)
        self.db.collection(col.REFRESH_TOKENS).update({"_key": doc["_key"], "rotated_at": rotated.isoformat()})


@pytest.fixture
def world(db) -> _World:
    return _World(db)


# ── families and replay ─────────────────────────────────────────────────────


def test_rotation_keeps_the_family_and_links_the_successor(world: _World) -> None:
    _, t1 = world.login()
    _, t2 = world.refresh(t1)

    first, second = world.stored(t1), world.stored(t2)

    assert first["family_key"] and first["family_key"] == second["family_key"]
    assert first["rotated_at"] is not None and first["successor_key"] == second["_key"]
    assert second.get("rotated_at") is None and second["revoked"] is False


def test_replaying_a_rotated_token_revokes_the_whole_family(world: _World) -> None:
    _, t1 = world.login()
    _, t2 = world.refresh(t1)
    access3, t3 = world.refresh(t2)
    world.age_rotation(t1, 3600)

    with pytest.raises(InvalidTokenError):
        world.refresh(t1)

    with pytest.raises(InvalidTokenError):
        world.refresh(t3)  # the thief's (or the owner's) live end of the chain died with it
    assert not world.resolves(access3)  # and so did the access token minted from it


def test_a_replay_leaves_every_other_family_alone(world: _World) -> None:
    _, t1 = world.login(BROWSER)
    _, phone = world.login(PHONE)
    world.refresh(t1)
    world.age_rotation(t1, 3600)

    with pytest.raises(InvalidTokenError):
        world.refresh(t1)

    access, rotated = world.refresh(phone, PHONE)
    assert rotated is not None and world.resolves(access)


def test_two_tabs_racing_inside_the_grace_window_keep_the_session(world: _World) -> None:
    """The second tab presented the cookie the first one had just rotated (REQ-023 §3.2a)."""
    _, t1 = world.login()
    _, t2 = world.refresh(t1, allow_grace=True)

    access, new_raw = world.refresh(t1, allow_grace=True)

    assert new_raw is None  # no second successor: the browser already holds t2 in its cookie jar
    assert world.resolves(access)
    _, t3 = world.refresh(t2, allow_grace=True)
    assert t3 is not None


def test_the_grace_window_needs_the_same_client(world: _World) -> None:
    _, t1 = world.login(BROWSER)
    _, t2 = world.refresh(t1, BROWSER, allow_grace=True)

    with pytest.raises(InvalidTokenError):
        world.refresh(t1, PHONE, allow_grace=True)
    with pytest.raises(InvalidTokenError):
        world.refresh(t2, BROWSER, allow_grace=True)


def test_the_grace_window_ends(world: _World) -> None:
    _, t1 = world.login()
    _, t2 = world.refresh(t1, allow_grace=True)
    world.age_rotation(t1, 61)

    with pytest.raises(InvalidTokenError):
        world.refresh(t1, allow_grace=True)
    with pytest.raises(InvalidTokenError):
        world.refresh(t2, allow_grace=True)


def test_a_token_minted_before_families_existed_starts_one_on_its_first_rotation(world: _World) -> None:
    _, legacy = world.login()
    doc = world.stored(legacy)
    world.db.collection(col.REFRESH_TOKENS).replace(
        {k: v for k, v in doc.items() if k not in {"family_key", "rotated_at", "successor_key", "session_generation"}}
    )

    _, successor = world.refresh(legacy)

    assert world.stored(successor)["family_key"] == world.stored(legacy)["family_key"]
    assert world.stored(successor)["family_key"]


# ── access tokens die with their session ────────────────────────────────────


def test_logout_all_ends_the_access_tokens_already_issued(world: _World) -> None:
    browser_access, _ = world.login(BROWSER)
    phone_access, _ = world.login(PHONE)
    assert world.resolves(browser_access) and world.resolves(phone_access)

    world.service.logout_all(world.key)

    assert not world.resolves(browser_access)
    assert not world.resolves(phone_access)
    fresh, _ = world.login()
    assert world.resolves(fresh)


def test_revoking_one_session_ends_its_access_token_and_keeps_the_other_session(world: _World) -> None:
    _, browser_raw = world.login(BROWSER)
    phone_access, phone_raw = world.login(PHONE)
    phone_session = world.stored(phone_raw)["_key"]

    world.service.revoke_session(world.key, phone_session)

    assert not world.resolves(phone_access)
    with pytest.raises(InvalidTokenError):
        world.refresh(phone_raw, PHONE)
    # The browser's session survives: its next (silent) refresh is a working one.
    browser_access, rotated = world.refresh(browser_raw, BROWSER)
    assert rotated is not None and world.resolves(browser_access)


def test_a_password_reset_ends_the_access_tokens_already_issued(world: _World) -> None:
    access, _ = world.login()
    mail = world.service._email_service  # noqa: SLF001 - the MagicMock the world built
    world.service.request_password_reset(ADDRESS, client_ip="203.0.113.7")
    token = mail.send_password_reset_email.call_args.kwargs["token"]

    world.service.reset_password(token, NEW_PASSWORD)

    assert not world.resolves(access)


def test_a_concurrent_profile_write_cannot_bring_revoked_access_tokens_back(world: _World) -> None:
    """``update_fields`` rewrites the whole account from a read; the counters must not ride along."""
    access, _ = world.login()
    stale = world.users.get_by_key(world.key)
    assert stale is not None

    world.service.logout_all(world.key)
    # The shape of a writer that read the account before the logout-all and writes after it.
    world.users.update(world.key, stale)

    assert not world.resolves(access)


def test_a_successor_minted_past_a_logout_all_is_refused(world: _World) -> None:
    """The race ``revoke_all_for_user`` cannot close on its own: a rotation that read its token
    before the revocation and wrote the successor after it. Modelled by un-revoking a token
    after the logout-all - the state such a successor is in."""
    _, raw = world.login()
    world.service.logout_all(world.key)
    doc = world.stored(raw)
    world.db.collection(col.REFRESH_TOKENS).update({"_key": doc["_key"], "revoked": False})

    with pytest.raises(InvalidTokenError):
        world.refresh(raw)


def test_the_cleanup_keeps_a_rotated_token_until_its_expiry_so_a_late_replay_is_still_seen(world: _World) -> None:
    _, t1 = world.login()
    _, t2 = world.refresh(t1)
    _, logged_out = world.login(PHONE)
    world.service.logout(logged_out)

    world.sessions.cleanup_expired()

    hashes = {doc["token_hash"] for doc in world.db.collection(col.REFRESH_TOKENS).all()}
    assert world.tokens.hash_token(t1) in hashes  # rotated, kept as the replay signal
    assert world.tokens.hash_token(logged_out) not in hashes  # plainly revoked, gone
    world.age_rotation(t1, 3600)
    with pytest.raises(InvalidTokenError):
        world.refresh(t1)
    with pytest.raises(InvalidTokenError):
        world.refresh(t2)


def test_a_reactivation_does_not_revive_the_tokens_of_before_the_deactivation(world: _World) -> None:
    from app.domain.services.user_service import UserService
    from tests.support.step_up import PassedStepUpVerifier

    access, raw = world.login()
    from app.domain.models.user import User

    admin = UserService(world.users, step_up_verifier=PassedStepUpVerifier(), refresh_token_repo=world.sessions)
    # Another account acts: an admin deactivating their own account is refused since #2144 (MT-045.4).
    requester = User(_key="platform-admin", email="admin@example.org", display_name="Admin")
    step_up = {
        "requester": requester,
        "current_password": None,
        "step_up_code": None,
        "step_up_token": None,
        "authenticated_with_api_key": False,
        "client_ip": None,
    }

    admin.admin_update_user(world.key, {"is_active": False}, **step_up)
    admin.admin_update_user(world.key, {"is_active": True}, **step_up)

    assert not world.resolves(access)
    with pytest.raises(InvalidTokenError):
        world.refresh(raw)
