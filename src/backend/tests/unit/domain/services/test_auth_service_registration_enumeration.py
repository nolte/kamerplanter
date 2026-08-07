"""Registering an already-taken email must reveal nothing about the account (SEC-H-009).

``register_local`` answers 201 for a duplicate email so the caller cannot tell a
fresh registration from an existing one (REQ-023 v1.8, TC-023-005). It used to
build that answer from the **stored record** — so an unauthenticated caller who
submitted a wrong password got back the owner's key, display name, locale,
timezone, last login and creation date, which both confirmed the address exists
and disclosed another person's data.

The tests below assert the property itself rather than the implementation: the
duplicate response must be indistinguishable, field for field, from the response
a genuinely new registration produces, and must carry no value that the stored
account holds.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
import structlog

from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.models.user import User, UserProfile
from app.domain.services.auth_service import AuthService

TAKEN_EMAIL = "victim@example.com"
FREE_EMAIL = "newcomer@example.com"
REAL_PASSWORD = "the-owners-real-password-2024"
WRONG_PASSWORD = "attacker-guess-password-2024"

#: Key ArangoDB assigned to the account that already exists.
STORED_KEY = "8271634"
#: Key ArangoDB assigns to the account created by a genuine registration.
CREATED_KEY = "9137450"


def _stored_user() -> User:
    """The victim's account — every leakable field deliberately off-default."""
    return User(
        _key=STORED_KEY,
        email=TAKEN_EMAIL,
        display_name="Victim Realname",
        password_hash=PasswordEngine().hash_password(REAL_PASSWORD),
        email_verified=True,
        is_active=False,
        avatar_url="https://cdn.example.com/avatars/victim.png",
        locale="en",
        timezone="America/New_York",
        last_login_at=datetime.now(UTC) - timedelta(days=3),
        created_at=datetime.now(UTC) - timedelta(days=900),
    )


@pytest.fixture
def stored() -> User:
    return _stored_user()


@pytest.fixture
def user_repo(stored: User) -> MagicMock:
    """Repo that knows exactly one account and mints a key on create (as Arango does)."""
    repo = MagicMock()

    def _get_by_email(email: str) -> User | None:
        return stored if email.lower() == TAKEN_EMAIL else None

    def _create(user: User) -> User:
        created = user.model_copy(deep=True)
        created.key = CREATED_KEY
        created.created_at = datetime.now(UTC)
        created.updated_at = created.created_at
        return created

    repo.get_by_email.side_effect = _get_by_email
    repo.create.side_effect = _create
    return repo


@pytest.fixture
def service(user_repo: MagicMock) -> AuthService:
    return AuthService(
        user_repo=user_repo,
        auth_provider_repo=MagicMock(),
        refresh_token_repo=MagicMock(),
        password_engine=PasswordEngine(),
        token_engine=TokenEngine("test-secret-key-for-unit-tests-32chars!", "HS256"),
        throttle_engine=LoginThrottleEngine(),
        email_service=MagicMock(),
        frontend_url="http://localhost:5173",
        access_token_expire_minutes=15,
        refresh_token_expire_days=30,
        session_token_expire_hours=24,
        tenant_service=MagicMock(),
    )


def _register_duplicate(service: AuthService) -> UserProfile:
    """What an attacker gets: a taken address, a wrong password, their own name."""
    return service.register_local(TAKEN_EMAIL, WRONG_PASSWORD, "Attacker Chosen Name")


def _register_fresh(service: AuthService) -> UserProfile:
    return service.register_local(FREE_EMAIL, REAL_PASSWORD, "Attacker Chosen Name")


def test_duplicate_registration_is_indistinguishable_from_a_fresh_one(service: AuthService) -> None:
    """Every field a caller can compare must match a genuine registration."""
    duplicate = _register_duplicate(service)
    fresh = _register_fresh(service)

    # ``email`` echoes the submitted address and ``key``/``created_at`` differ
    # between any two distinct registrations, so they are compared separately
    # below. Everything else must be byte-identical.
    compared = {"key", "email", "created_at"}
    assert {k: v for k, v in duplicate.model_dump().items() if k not in compared} == {
        k: v for k, v in fresh.model_dump().items() if k not in compared
    }

    # The echoed address is the one the caller submitted, exactly as a fresh
    # registration echoes the address it was given.
    assert duplicate.email == TAKEN_EMAIL

    # Same character class and width as a key ArangoDB generates — a decoy that
    # looked different would itself be the oracle.
    assert duplicate.key.isdigit()
    assert len(duplicate.key) == len(fresh.key)

    # A fresh-looking creation timestamp, not the stored account's age.
    assert duplicate.created_at is not None
    assert abs((duplicate.created_at - datetime.now(UTC)).total_seconds()) < 60


def test_duplicate_registration_returns_no_value_from_the_stored_record(
    service: AuthService,
    stored: User,
) -> None:
    """Not one field may be derived from the account that actually exists."""
    duplicate = _register_duplicate(service)

    assert duplicate.key != stored.key
    assert duplicate.display_name == "Attacker Chosen Name"
    assert duplicate.display_name != stored.display_name
    assert duplicate.avatar_url is None
    assert duplicate.avatar_url != stored.avatar_url
    assert duplicate.locale != stored.locale
    assert duplicate.timezone != stored.timezone
    assert duplicate.is_active != stored.is_active
    assert duplicate.last_login_at is None
    assert duplicate.last_login_at != stored.last_login_at
    assert duplicate.created_at != stored.created_at
    # ``is_platform_admin`` is not part of ``UserProfile`` at all, so the
    # response schema always defaults it to False — an attacker cannot use the
    # registration endpoint to rank targets by privilege.
    assert not hasattr(duplicate, "is_platform_admin")


def test_duplicate_registration_writes_nothing(service: AuthService, user_repo: MagicMock) -> None:
    """TC-023-005 postcondition: no second account, no provider, no tenant, no mail."""
    _register_duplicate(service)

    user_repo.create.assert_not_called()
    user_repo.update_fields.assert_not_called()
    service._auth_provider_repo.create.assert_not_called()  # type: ignore[attr-defined]
    service._tenant_service.create_personal_tenant.assert_not_called()  # type: ignore[union-attr]
    service._email_service.send_verification_email.assert_not_called()  # type: ignore[attr-defined]


def test_duplicate_registration_key_is_not_reused_across_attempts(service: AuthService) -> None:
    """Two probes of the same address must not return the same handle.

    A stable decoy key would be a fingerprint of the address: the attacker could
    recognise it again and confirm the account from a later, unrelated probe.
    """
    first = _register_duplicate(service)
    second = _register_duplicate(service)

    assert first.key != second.key


def test_duplicate_registration_does_not_log_the_raw_email(service: AuthService) -> None:
    """The probed address belongs to someone who never consented to this call.

    The event stays (it is the only signal an enumeration sweep leaves), but the
    address is reduced to a correlatable digest — NFR-011 data minimisation,
    matching the pseudonymisation used for audit records elsewhere.
    """
    with structlog.testing.capture_logs() as logs:
        _register_duplicate(service)

    events = [entry for entry in logs if entry["event"] == "registration_duplicate_suppressed"]
    assert len(events) == 1
    assert TAKEN_EMAIL not in str(events[0])
    assert events[0]["email_sha256"]


# ── The clock, not the body (#942 §3) ──────────────────────────────


def _service_with_spied_password_engine(user_repo: MagicMock) -> tuple[AuthService, MagicMock]:
    password_engine = MagicMock(wraps=PasswordEngine())
    service = AuthService(
        user_repo=user_repo,
        auth_provider_repo=MagicMock(),
        refresh_token_repo=MagicMock(),
        password_engine=password_engine,
        token_engine=TokenEngine("test-secret-key-for-unit-tests-32chars!", "HS256"),
        throttle_engine=LoginThrottleEngine(),
        email_service=MagicMock(),
        frontend_url="http://localhost:5173",
        tenant_service=MagicMock(),
    )
    return service, password_engine


def test_duplicate_registration_burns_the_same_bcrypt_round_as_a_real_one(user_repo: MagicMock) -> None:
    """The response is identical; without this the response time is not.

    The duplicate branch skips the account write, the personal tenant and the
    mail dispatch — single-digit milliseconds each. It also used to skip bcrypt,
    which is ~100 ms, so a fast 201 meant "taken" and a slow one meant "created".
    Asserting the *count* rather than a wall-clock delta keeps the check
    deterministic; a timing assertion would be flaky on a shared runner.
    """
    duplicate_service, duplicate_engine = _service_with_spied_password_engine(user_repo)
    fresh_service, fresh_engine = _service_with_spied_password_engine(user_repo)

    _register_duplicate(duplicate_service)
    _register_fresh(fresh_service)

    assert duplicate_engine.hash_password.call_count == fresh_engine.hash_password.call_count == 1
    assert duplicate_engine.hash_password.call_args[0][0] == WRONG_PASSWORD


def test_duplicate_registration_still_writes_nothing(user_repo: MagicMock) -> None:
    """The hash is thrown away — burning the round must not create an account."""
    service, _ = _service_with_spied_password_engine(user_repo)

    profile = _register_duplicate(service)

    user_repo.create.assert_not_called()
    assert profile.key != STORED_KEY
    assert profile.key != CREATED_KEY


# ── The REQ-023 §3.2 notice hand-off (#958) ────────────────────────
#
# The address that already owns an account gets told (see
# ``app.tasks.auth_tasks.send_duplicate_registration_notice``). The service only
# hands over a key; the enqueue happens after the response is written. These
# tests pin the hand-off, and that it changed nothing else.


def test_duplicate_registration_hands_the_existing_key_to_the_notifier(service: AuthService) -> None:
    notified: list[str] = []

    service.register_local(
        TAKEN_EMAIL,
        WRONG_PASSWORD,
        "Attacker Chosen Name",
        on_existing_address=notified.append,
    )

    assert notified == [STORED_KEY]


def test_fresh_registration_never_notifies(service: AuthService) -> None:
    """There is nobody to tell: the address had no owner a moment ago."""
    notified: list[str] = []

    service.register_local(
        FREE_EMAIL,
        REAL_PASSWORD,
        "Attacker Chosen Name",
        on_existing_address=notified.append,
    )

    assert notified == []


def test_notified_key_never_reaches_the_caller(service: AuthService) -> None:
    """The key goes to the worker, not into the response — that would be the leak."""
    notified: list[str] = []

    profile = service.register_local(
        TAKEN_EMAIL,
        WRONG_PASSWORD,
        "Attacker Chosen Name",
        on_existing_address=notified.append,
    )

    assert notified == [STORED_KEY]
    assert profile.key != STORED_KEY


def test_notifier_does_not_change_the_response(service: AuthService) -> None:
    """With and without a notifier the caller sees the same thing."""
    with_notifier = service.register_local(
        TAKEN_EMAIL,
        WRONG_PASSWORD,
        "Attacker Chosen Name",
        on_existing_address=lambda _key: None,
    )
    without = _register_duplicate(service)

    volatile = {"key", "created_at"}
    assert {k: v for k, v in with_notifier.model_dump().items() if k not in volatile} == {
        k: v for k, v in without.model_dump().items() if k not in volatile
    }


def test_notifier_does_not_add_a_bcrypt_round_to_either_branch(user_repo: MagicMock) -> None:
    """The compensating work stays exactly one hash on both sides.

    The notice is the reason #958 could have reopened the gap #957 closed. It
    cannot: the branch does the same single bcrypt round it did before, and the
    hand-off adds one list append. Where the actual enqueue happens — after the
    response — is asserted in ``tests/api/test_auth_register_duplicate_notice.py``.
    """
    duplicate_service, duplicate_engine = _service_with_spied_password_engine(user_repo)
    fresh_service, fresh_engine = _service_with_spied_password_engine(user_repo)

    duplicate_service.register_local(
        TAKEN_EMAIL,
        WRONG_PASSWORD,
        "Attacker Chosen Name",
        on_existing_address=lambda _key: None,
    )
    fresh_service.register_local(
        FREE_EMAIL,
        REAL_PASSWORD,
        "Attacker Chosen Name",
        on_existing_address=lambda _key: None,
    )

    assert duplicate_engine.hash_password.call_count == fresh_engine.hash_password.call_count == 1
