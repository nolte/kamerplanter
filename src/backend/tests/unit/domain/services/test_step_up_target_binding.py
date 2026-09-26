"""#1884 — a step-up code or re-authentication token confirms the target it was obtained for, only.

Before #1884 the digest was ``HMAC(key, "user_key:action:code")``: a token the admin
obtained to verify user A also verified user B within its five minutes, one obtained
to unlink provider X also unlinked provider Y. The verifier now binds the target of
every act on something other than the requester's own account
(:data:`TARGETED_ACTIONS`), and the factor is issued only for a target that exists and
the requester may act on (operator decision D2, :class:`StepUpTargetAuthorizer`).
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.common.enums import AdminScope, TenantRole
from app.common.exceptions import DuplicateError, ForbiddenError, NotFoundError, UnauthorizedError, ValidationError
from app.data_access.external.step_up_code_store import MemoryStepUpCodeStore
from app.data_access.external.step_up_throttle import MemoryStepUpThrottleStore
from app.domain.models.auth import AuthProvider
from app.domain.models.membership import Membership
from app.domain.models.oidc_config import OidcProviderConfig
from app.domain.models.tenant import Tenant
from app.domain.models.tenant_erasure import TenantErasureRecord
from app.domain.models.user import User
from app.domain.services.step_up_service import TARGETED_ACTIONS, StepUpVerifier
from app.domain.services.step_up_targets import StepUpTargetAuthorizer, oidc_provider_target
from tests.support.step_up import AdmitEveryTarget

IP = "203.0.113.7"


def _federated(key: str = "admin-1") -> User:
    return User.model_validate({"_key": key, "email": f"{key}@example.org", "display_name": "A", "password_hash": None})


def _verifier(policy=None) -> StepUpVerifier:
    return StepUpVerifier(
        MemoryStepUpThrottleStore(),
        code_store=MemoryStepUpCodeStore(),
        reauth_store=MemoryStepUpCodeStore(),
        code_secret="s" * 32,
        target_policy=policy if policy is not None else AdmitEveryTarget(),
    )


def _verify(verifier: StepUpVerifier, user: User, *, action: str, target: str | None, code=None, token=None) -> str:
    return verifier.verify(
        user,
        action=action,  # type: ignore[arg-type]
        target=target,
        echo_ok=None,
        password=None,
        code=code,
        reauth_token=token,
        authenticated_with_api_key=False,
        client_ip=IP,
    )


# ── the binding ───────────────────────────────────────────────────────────────


@pytest.mark.parametrize("action", sorted(TARGETED_ACTIONS))
def test_a_reauth_token_for_target_a_is_refused_for_target_b_and_not_spent(action: str) -> None:
    verifier, admin = _verifier(), _federated()
    token = verifier.issue_reauth_token(admin, action=action, target="target-A")  # type: ignore[arg-type]

    with pytest.raises(UnauthorizedError):
        _verify(verifier, admin, action=action, target="target-B", token=token)

    # Not consumed by the mismatch: the act on A still goes through with it.
    assert _verify(verifier, admin, action=action, target="target-A", token=token) == "oidc_reauth"


@pytest.mark.parametrize("action", sorted(TARGETED_ACTIONS))
def test_a_mailed_code_for_target_a_is_refused_for_target_b_and_not_spent(action: str) -> None:
    verifier, admin = _verifier(), _federated()
    code, _ = verifier.issue_code(
        admin, action=action, target="target-A", authenticated_with_api_key=False, client_ip=IP
    )  # type: ignore[arg-type]

    with pytest.raises(UnauthorizedError):
        _verify(verifier, admin, action=action, target="target-B", code=code)

    assert _verify(verifier, admin, action=action, target="target-A", code=code) == "email_code"


def test_the_target_does_not_collide_with_the_separator() -> None:
    """``new:<slug>`` holds the separator; ``a:b`` + code must not equal ``a`` + ``b:code``."""
    verifier, admin = _verifier(), _federated()
    token = verifier.issue_reauth_token(admin, action="oidc_provider_change", target="new:a")

    with pytest.raises(UnauthorizedError):
        _verify(verifier, admin, action="oidc_provider_change", target="new", token=f"a:{token}")


# ── the shape: a targeted act names its target, another names none ──────────


@pytest.mark.parametrize("action", sorted(TARGETED_ACTIONS))
@pytest.mark.parametrize("target", [None, "", "   "])
def test_a_targeted_act_without_a_target_is_refused_at_issuance(action: str, target: str | None) -> None:
    verifier, admin = _verifier(), _federated()

    with pytest.raises(ValidationError):
        verifier.issue_code(admin, action=action, target=target, authenticated_with_api_key=False, client_ip=IP)  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        verifier.admit_reauth(admin, action=action, target=target, authenticated_with_api_key=False, client_ip=IP)  # type: ignore[arg-type]


def test_an_act_on_the_own_account_naming_a_target_is_refused_at_issuance() -> None:
    verifier, user = _verifier(), _federated()

    with pytest.raises(ValidationError):
        verifier.issue_code(
            user, action="account_erasure", target="someone", authenticated_with_api_key=False, client_ip=IP
        )


@pytest.mark.parametrize("target", ["users/u-2", "a/b"])
def test_a_document_id_is_no_target(target: str) -> None:
    """Review O-2: a ``/`` would reach the repository as a document id of another collection (500)."""
    policy = MagicMock()
    with pytest.raises(ValidationError):
        _verifier(policy).issue_code(
            _federated(), action="admin_account_update", target=target, authenticated_with_api_key=False, client_ip=IP
        )
    policy.authorize.assert_not_called()


def test_a_too_long_target_is_refused_at_issuance() -> None:
    with pytest.raises(ValidationError):
        _verifier().issue_code(
            _federated(), action="provider_unlink", target="x" * 257, authenticated_with_api_key=False, client_ip=IP
        )


@pytest.mark.parametrize(("action", "target"), [("admin_account_update", None), ("account_erasure", "u-2")])
def test_verify_with_the_wrong_shape_is_a_programming_error(action: str, target: str | None) -> None:
    """The act's own code passes its target; the wrong shape never reaches a check."""
    with pytest.raises(ValueError, match="target"):
        _verify(_verifier(), _federated(), action=action, target=target, code="12345678")


def test_without_a_target_policy_no_factor_is_issued_for_a_targeted_act() -> None:
    verifier = StepUpVerifier(MemoryStepUpThrottleStore(), code_store=MemoryStepUpCodeStore(), code_secret="s" * 32)

    with pytest.raises(ForbiddenError):
        verifier.issue_code(
            _federated(), action="admin_account_update", target="u-2", authenticated_with_api_key=False, client_ip=IP
        )
    # An act on the own account is unaffected.
    verifier.issue_code(
        _federated(), action="account_erasure", target=None, authenticated_with_api_key=False, client_ip=IP
    )


def test_the_policy_is_asked_with_the_stripped_target_before_the_code_is_issued() -> None:
    policy = MagicMock()
    policy.authorize.side_effect = NotFoundError("User", "u-9")
    verifier = _verifier(policy)

    with pytest.raises(NotFoundError):
        verifier.issue_code(
            _federated(), action="admin_account_update", target="  u-9 ", authenticated_with_api_key=False, client_ip=IP
        )

    policy.authorize.assert_called_once()
    assert policy.authorize.call_args.kwargs == {"action": "admin_account_update", "target": "u-9"}
    assert verifier._code_store._entries == {}  # type: ignore[attr-defined]


def test_the_api_key_refusal_comes_before_the_target_is_looked_at() -> None:
    """A leaked key learns nothing about which targets exist."""
    policy = MagicMock()
    with pytest.raises(ForbiddenError):
        _verifier(policy).issue_code(
            _federated(), action="admin_account_update", target="u-9", authenticated_with_api_key=True, client_ip=IP
        )
    policy.authorize.assert_not_called()


# ── the authorizer: exists, and the requester's to act on (D2) ──────────────


class _World:
    def __init__(self, *, platform_admin: bool = True, tenant_role: TenantRole | None = None) -> None:
        self.admin = _federated("admin-1")
        users = {"admin-1": self.admin, "u-2": _federated("u-2")}
        memberships: dict[tuple[str, str], Membership] = {}
        if platform_admin:
            memberships[("admin-1", "platform")] = Membership(
                user_key="admin-1", tenant_key="platform", role=TenantRole.LEAD
            )
        if tenant_role is not None:
            memberships[("admin-1", "t-1")] = Membership(
                user_key="admin-1", tenant_key="t-1", role=tenant_role, admin_scopes=[AdminScope.MANAGEMENT]
            )
        tenants = {
            "t-1": Tenant.model_validate(
                {"_key": "t-1", "name": "G", "slug": "g", "tenant_type": "organization", "owner_user_key": "o"}
            ),
            "platform": Tenant.model_validate(
                {
                    "_key": "platform",
                    "name": "P",
                    "slug": "platform",
                    "tenant_type": "organization",
                    "owner_user_key": "o",
                    "is_platform": True,
                }
            ),
        }
        self.erasures: dict[str, TenantErasureRecord] = {}
        configs = {
            "cfg-1": OidcProviderConfig.model_validate(
                {"_key": "cfg-1", "slug": "corp", "display_name": "Corp", "issuer_url": "https://idp", "client_id": "c"}
            )
        }
        user_repo = MagicMock(**{"get_by_key.side_effect": users.get})
        membership_repo = MagicMock(**{"get_by_user_and_tenant.side_effect": lambda u, t: memberships.get((u, t))})
        tenant_repo = MagicMock(**{"get_by_key.side_effect": tenants.get})
        erasure_repo = MagicMock(**{"get.side_effect": self.erasures.get})
        providers = MagicMock(
            **{
                "list_by_user.side_effect": lambda u: (
                    [AuthProvider(key="link-1", user_key=u, provider="google", provider_user_id="s")]
                    if u == "admin-1"
                    else []
                )
            }
        )
        oidc = MagicMock(
            **{
                "get_by_key.side_effect": configs.get,
                "get_by_slug.side_effect": lambda s: next((c for c in configs.values() if c.slug == s), None),
            }
        )
        self.policy = StepUpTargetAuthorizer(
            user_repo=user_repo,
            membership_repo=membership_repo,
            tenant_repo=tenant_repo,
            tenant_erasure_repo=erasure_repo,
            auth_provider_repo=providers,
            oidc_config_repo=oidc,
        )

    def authorize(self, action: str, target: str) -> None:
        self.policy.authorize(self.admin, action=action, target=target)


@pytest.mark.parametrize(
    ("action", "target"),
    [
        ("admin_account_update", "u-2"),
        ("admin_account_erasure", "u-2"),
        ("tenant_deletion", "t-1"),
        ("provider_unlink", "link-1"),
        ("oidc_provider_change", "cfg-1"),
        ("oidc_provider_change", "new:other"),
    ],
)
def test_a_platform_admin_obtains_a_factor_for_an_existing_target(action: str, target: str) -> None:
    _World().authorize(action, target)


@pytest.mark.parametrize(
    ("action", "target"),
    [
        ("admin_account_update", "u-2"),
        ("admin_account_update", "u-404"),
        ("admin_account_erasure", "u-2"),
        ("oidc_provider_change", "cfg-1"),
        ("oidc_provider_change", "new:other"),
        ("tenant_deletion", "t-1"),
        ("tenant_deletion", "t-404"),
    ],
)
def test_who_is_no_platform_admin_is_refused_before_existence_is_told(action: str, target: str) -> None:
    """403 for an existing and a missing target alike: the refusal is no existence oracle."""
    with pytest.raises(ForbiddenError):
        _World(platform_admin=False).authorize(action, target)


@pytest.mark.parametrize(
    ("action", "target", "error"),
    [
        ("admin_account_update", "u-404", NotFoundError),
        ("admin_account_erasure", "u-404", NotFoundError),
        ("admin_account_erasure", "admin-1", ForbiddenError),
        ("tenant_deletion", "t-404", NotFoundError),
        ("tenant_deletion", "platform", ForbiddenError),
        ("provider_unlink", "link-of-someone-else", NotFoundError),
        ("oidc_provider_change", "cfg-404", NotFoundError),
        ("oidc_provider_change", "new:corp", DuplicateError),
        ("oidc_provider_change", "new:Not A Slug", ValidationError),
    ],
)
def test_a_target_the_act_would_refuse_gets_no_factor(action: str, target: str, error: type[Exception]) -> None:
    with pytest.raises(error):
        _World().authorize(action, target)


def test_a_tenant_lead_with_management_obtains_a_factor_for_its_own_tenant() -> None:
    _World(platform_admin=False, tenant_role=TenantRole.LEAD).authorize("tenant_deletion", "t-1")


def test_a_grower_does_not() -> None:
    with pytest.raises(ForbiddenError):
        _World(platform_admin=False, tenant_role=TenantRole.GROWER).authorize("tenant_deletion", "t-1")


def test_an_open_erasure_of_a_removed_tenant_is_still_a_target() -> None:
    """A deletion an earlier attempt left partial is resumed by the same act."""
    world = _World()
    world.erasures["ter_t-gone"] = TenantErasureRecord(
        tenant_key="t-gone", tenant_type="organization", origin="platform_admin", status="partially_completed"
    )
    world.authorize("tenant_deletion", "t-gone")

    world.erasures["ter_t-gone"] = world.erasures["ter_t-gone"].model_copy(update={"status": "completed"})
    with pytest.raises(NotFoundError):
        world.authorize("tenant_deletion", "t-gone")


def test_the_oidc_target_of_a_creation_is_the_prefixed_slug() -> None:
    assert oidc_provider_target(None, slug="corp") == "new:corp"
    assert oidc_provider_target("cfg-1") == "cfg-1"
    with pytest.raises(ValueError):
        oidc_provider_target(None)
