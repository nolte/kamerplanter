"""#2132 (MT-036, REQ-023 AK-56): who may create an account is the operator's decision.

``POST /auth/register`` and the first OIDC sign-in created an account for anybody in full mode; there was no
switch. ``REGISTRATION_MODE`` now decides - ``open`` (the default, unchanged), ``invite_only``, ``closed`` -
plus an optional domain allowlist ``REGISTRATION_ALLOWED_DOMAINS``.

**The reading chosen for invitations (recorded in REQ-023 §3.2d):** an *e-mail* invitation that is pending,
unexpired and names the registering address is the exception to ``invite_only`` and to the allowlist; it is
**not** an exception to ``closed`` - otherwise ``closed`` and ``invite_only`` would be the same mode. Local
registration proves the invitation by its token; the first OIDC sign-in proves it by the provider's assertion
of the address (``email_verified``), with no token. A link invitation is meant to be shared and unlocks no
registration: one leaked link would reopen the instance to everybody holding it.

**Enumeration:** every refusal is the same 403 ``REGISTRATION_NOT_ALLOWED`` whether or not the address has an
account, and it is decided before the stored accounts are read.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.common.enums import AuthProviderType, InvitationStatus, InvitationType, RegistrationMode, TenantRole
from app.common.exceptions import KamerplanterError
from app.domain.engines.invitation_engine import InvitationEngine
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.oauth_engine import OAuthEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.registration_engine import RegistrationPolicy
from app.domain.engines.tenant_engine import TenantEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.models.auth import OAuthUserInfo
from app.domain.models.invitation import Invitation
from app.domain.models.oidc_config import OidcProviderConfig
from app.domain.models.user import User
from app.domain.services.auth_service import AuthService
from app.domain.services.tenant_service import TenantService

NEWCOMER = "newcomer@example.org"
TAKEN = "taken@example.org"
PASSWORD = "a-long-enough-password-2026"
TOKEN = "invitation-token-for-the-newcomer"


def _invitation(
    *,
    email: str | None = NEWCOMER,
    kind: InvitationType = InvitationType.EMAIL,
    status: InvitationStatus = InvitationStatus.PENDING,
    expires: datetime | None = None,
) -> Invitation:
    return Invitation(
        _key="i1",
        tenant_key="t-garden",
        invited_by_user_key="u-lead",
        invitation_type=kind,
        email=email,
        role=TenantRole.GROWER,
        token_hash=InvitationEngine.hash_token(TOKEN),
        status=status,
        expires_at=expires or datetime.now(UTC) + timedelta(days=3),
    )


class _World:
    """An AuthService over doubled repositories, a REAL TenantService for the invitation read."""

    def __init__(
        self,
        mode: RegistrationMode = RegistrationMode.OPEN,
        domains: frozenset[str] = frozenset(),
        invitations: list[Invitation] | None = None,
    ) -> None:
        stored = invitations or []
        self.invitation_repo = MagicMock()
        self.invitation_repo.get_by_token_hash.side_effect = lambda h: next(
            (i for i in stored if i.token_hash == h), None
        )
        self.invitation_repo.list_pending_email_invitations.side_effect = lambda email: [
            i
            for i in stored
            if i.invitation_type == InvitationType.EMAIL
            and i.status == InvitationStatus.PENDING
            and (i.email or "").lower() == email.lower()
        ]
        tenants = MagicMock()
        tenants.get_by_slug.return_value = None
        tenants.create_with_lead_membership.side_effect = lambda tenant, membership, audit=None: (
            tenant.model_copy(update={"key": "t-new"}),
            membership,
        )
        self.tenant_service = TenantService(
            tenant_repo=tenants,
            membership_repo=MagicMock(),
            invitation_repo=self.invitation_repo,
            assignment_repo=MagicMock(),
            tenant_engine=TenantEngine(),
            membership_engine=MembershipEngine(),
            invitation_engine=InvitationEngine(),
        )
        self.users = MagicMock()
        self.users.get_by_email.side_effect = lambda email: (
            User(_key="u-taken", email=TAKEN, display_name="Taken", email_verified=True)
            if email.lower() == TAKEN
            else None
        )
        self.users.create.side_effect = lambda user: user.model_copy(update={"key": "u-new"})
        self.password_engine = MagicMock(wraps=PasswordEngine())
        self.service = AuthService(
            user_repo=self.users,
            auth_provider_repo=MagicMock(),
            refresh_token_repo=MagicMock(),
            password_engine=self.password_engine,
            token_engine=TokenEngine("test-secret-key-for-unit-tests-32chars!", "HS256"),
            throttle_engine=LoginThrottleEngine(),
            email_service=MagicMock(),
            frontend_url="http://localhost:5173",
            tenant_service=self.tenant_service,
            require_email_verification=False,
            registration_policy=RegistrationPolicy(mode=mode, allowed_domains=domains),
        )

    def register(self, email: str = NEWCOMER, token: str | None = None):
        return self.service.register_local(email, PASSWORD, "Newcomer", invitation_token=token)

    def nothing_written(self) -> bool:
        return not self.users.create.called and not self.password_engine.hash_password.called


def _refused(excinfo: pytest.ExceptionInfo[KamerplanterError]) -> tuple[int, str]:
    return excinfo.value.status_code, excinfo.value.error_code


# ── local registration ───────────────────────────────────────────────────────


def test_open_is_the_default_and_registers_as_before() -> None:
    world = _World()

    profile = world.register()

    assert profile.email == NEWCOMER
    world.users.create.assert_called_once()


def test_invite_only_without_an_invitation_is_refused_with_403() -> None:
    world = _World(RegistrationMode.INVITE_ONLY)

    with pytest.raises(KamerplanterError) as refused:
        world.register()

    assert _refused(refused) == (403, "REGISTRATION_NOT_ALLOWED")
    assert world.nothing_written()


def test_the_refusal_is_the_same_for_a_taken_and_a_free_address() -> None:
    """No enumeration: decided before the stored accounts are read, one answer for both."""
    world = _World(RegistrationMode.INVITE_ONLY)

    with pytest.raises(KamerplanterError) as free:
        world.register(NEWCOMER)
    with pytest.raises(KamerplanterError) as taken:
        world.register(TAKEN)

    assert (free.value.status_code, free.value.error_code, free.value.message) == (
        taken.value.status_code,
        taken.value.error_code,
        taken.value.message,
    )
    assert not world.users.get_by_email.called


@pytest.mark.parametrize("spelling", [NEWCOMER, NEWCOMER.upper(), "Newcomer@Example.org"])
def test_invite_only_admits_the_holder_of_an_email_invitation_for_that_address(spelling: str) -> None:
    world = _World(RegistrationMode.INVITE_ONLY, invitations=[_invitation()])

    profile = world.register(spelling, TOKEN)

    assert profile.email.lower() == spelling.lower()  # the address model folds the domain's case
    world.users.create.assert_called_once()


@pytest.mark.parametrize(
    "invitation",
    [
        pytest.param(_invitation(email="someone.else@example.org"), id="issued for another address"),
        pytest.param(_invitation(kind=InvitationType.LINK, email=None), id="a shareable link invitation"),
        pytest.param(_invitation(status=InvitationStatus.ACCEPTED), id="already accepted"),
        pytest.param(_invitation(status=InvitationStatus.REVOKED), id="revoked"),
        pytest.param(_invitation(expires=datetime.now(UTC) - timedelta(minutes=1)), id="expired"),
    ],
)
def test_invite_only_refuses_every_token_that_is_no_valid_email_invitation_for_the_address(
    invitation: Invitation,
) -> None:
    world = _World(RegistrationMode.INVITE_ONLY, invitations=[invitation])

    with pytest.raises(KamerplanterError) as refused:
        world.register(NEWCOMER, TOKEN)

    assert _refused(refused) == (403, "REGISTRATION_NOT_ALLOWED")
    assert world.nothing_written()


def test_an_unknown_token_is_refused_like_a_missing_one() -> None:
    world = _World(RegistrationMode.INVITE_ONLY, invitations=[_invitation()])

    with pytest.raises(KamerplanterError) as refused:
        world.register(NEWCOMER, "a-token-nobody-issued")

    assert _refused(refused) == (403, "REGISTRATION_NOT_ALLOWED")


def test_closed_refuses_even_the_holder_of_a_valid_invitation() -> None:
    world = _World(RegistrationMode.CLOSED, invitations=[_invitation()])

    with pytest.raises(KamerplanterError) as refused:
        world.register(NEWCOMER, TOKEN)

    assert _refused(refused) == (403, "REGISTRATION_NOT_ALLOWED")
    assert world.nothing_written()


def test_the_allowlist_refuses_another_domain_in_open_mode() -> None:
    world = _World(domains=frozenset({"club.example"}))

    with pytest.raises(KamerplanterError) as refused:
        world.register("visitor@example.org")

    assert _refused(refused) == (403, "REGISTRATION_NOT_ALLOWED")


@pytest.mark.parametrize("address", ["member@club.example", "Member@CLUB.Example"])
def test_the_allowlist_admits_its_domain_whatever_its_case(address: str) -> None:
    world = _World(domains=frozenset({"club.example"}))

    world.register(address)

    world.users.create.assert_called_once()


def test_the_allowlist_does_not_admit_a_subdomain_or_a_lookalike() -> None:
    world = _World(domains=frozenset({"club.example"}))

    for address in ("member@mail.club.example", "member@club.example.evil", "member@notclub.example"):
        with pytest.raises(KamerplanterError):
            world.register(address)


def test_an_email_invitation_is_the_exception_to_the_allowlist() -> None:
    world = _World(domains=frozenset({"club.example"}), invitations=[_invitation()])

    world.register(NEWCOMER, TOKEN)

    world.users.create.assert_called_once()


# ── the first OIDC sign-in ───────────────────────────────────────────────────


def _oauth_world(
    world: _World, *, email: str = NEWCOMER, verified: bool | None = True, existing: User | None = None
) -> AuthService:
    oauth_user = OAuthUserInfo(
        provider=AuthProviderType.GOOGLE,
        provider_user_id="subject-1",
        email=email,
        display_name="Newcomer",
        email_verified=verified,
    )
    service = world.service
    oauth_engine = MagicMock(wraps=OAuthEngine())
    oauth_engine.exchange_code_for_tokens.return_value = {"access_token": "t", "id_token": ""}
    oauth_engine.authenticate_login.return_value = oauth_user
    state_store = MagicMock()
    state_store.get_and_delete.return_value = {
        "provider_slug": "acme",
        "code_verifier": "v",
        "redirect_uri": "https://app.example/api/v1/auth/oauth/acme/callback",
    }
    config_repo = MagicMock()
    config_repo.get_by_slug.return_value = OidcProviderConfig(
        slug="acme",
        display_name="Acme",
        issuer_url="https://acme.example",
        client_id="cid",
        client_secret_encrypted="secret",
        enabled=True,
    )
    service._oauth_engine = oauth_engine
    service._oauth_state_store = state_store
    service._oidc_config_repo = config_repo
    service._auth_provider_repo.list_by_provider.return_value = []
    world.users.get_by_email.side_effect = lambda address: existing
    token_engine = MagicMock()
    token_engine.create_refresh_token.return_value = ("raw-refresh", "refresh-hash")
    service._token_engine = token_engine
    return service


def test_invite_only_refuses_a_first_oidc_sign_in_without_an_invitation() -> None:
    world = _World(RegistrationMode.INVITE_ONLY)
    service = _oauth_world(world)

    with pytest.raises(KamerplanterError) as refused:
        service.complete_oauth("acme", "code", "state")

    assert _refused(refused) == (403, "REGISTRATION_NOT_ALLOWED")
    assert not world.users.create.called


def test_invite_only_admits_a_first_oidc_sign_in_whose_proven_address_was_invited() -> None:
    world = _World(RegistrationMode.INVITE_ONLY, invitations=[_invitation()])
    service = _oauth_world(world, email=NEWCOMER.upper())

    service.complete_oauth("acme", "code", "state")

    world.users.create.assert_called_once()


@pytest.mark.parametrize("claim", [False, None])
def test_an_invitation_does_not_admit_an_address_the_provider_did_not_prove(claim: bool | None) -> None:
    world = _World(RegistrationMode.INVITE_ONLY, invitations=[_invitation()])
    service = _oauth_world(world, verified=claim)

    with pytest.raises(KamerplanterError) as refused:
        service.complete_oauth("acme", "code", "state")

    assert _refused(refused) == (403, "REGISTRATION_NOT_ALLOWED")
    assert not world.users.create.called


@pytest.mark.parametrize(("claim", "admitted"), [(True, True), (False, False), (None, False)])
def test_the_allowlist_needs_the_provider_proof_for_a_first_oidc_sign_in(claim: bool | None, admitted: bool) -> None:
    world = _World(domains=frozenset({"example.org"}))
    service = _oauth_world(world, verified=claim)

    if admitted:
        service.complete_oauth("acme", "code", "state")
        world.users.create.assert_called_once()
    else:
        with pytest.raises(KamerplanterError):
            service.complete_oauth("acme", "code", "state")
        assert not world.users.create.called


def test_open_without_allowlist_keeps_the_first_oidc_sign_in_as_before() -> None:
    """No behaviour change for an installation that sets nothing: an unproven address still registers."""
    world = _World()
    service = _oauth_world(world, verified=None)

    service.complete_oauth("acme", "code", "state")

    world.users.create.assert_called_once()


def test_closed_still_signs_in_an_existing_account() -> None:
    """The mode decides who is *created*; an account that exists signs in in every mode."""
    existing = User(
        _key="u-existing",
        email=NEWCOMER,
        display_name="Existing",
        email_verified=True,
        email_confirmed_at=datetime(2026, 1, 1, tzinfo=UTC),
        is_active=True,
    )
    world = _World(RegistrationMode.CLOSED)
    service = _oauth_world(world, existing=existing)

    service.complete_oauth("acme", "code", "state")

    assert not world.users.create.called


# ── the policy itself ────────────────────────────────────────────────────────


def test_the_policy_reads_the_configured_allowlist_as_lower_case_exact_domains() -> None:
    policy = RegistrationPolicy.from_settings("invite_only", " Club.Example , @Garden.example,, ")

    assert policy.mode == RegistrationMode.INVITE_ONLY
    assert policy.allowed_domains == frozenset({"club.example", "garden.example"})
    assert policy.domain_restricted


def test_an_address_without_a_domain_is_never_on_the_allowlist() -> None:
    policy = RegistrationPolicy(allowed_domains=frozenset({"club.example"}))

    assert not policy.admits("no-at-sign", invited=False, provider_proven=None)
    assert not policy.admits("trailing@", invited=False, provider_proven=None)
