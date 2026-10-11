"""#1855 / REQ-027 §7a — the light/full switch and the take-over of the light-mode data, unit level.

The measured gap (before the fix, ``develop`` ``9c8965982``): no code read or wrote the deployment
mode; after a switch to ``full`` the light-mode system account stayed active with its ``lead``
membership, every ``kp_`` key minted unauthenticated in light mode stayed valid, and the light-mode
data were reachable only as that account. The real-database proof of the same behaviour is
``tests/integration/test_light_to_full_upgrade_reach.py``; this module covers the decisions.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.common.enums import SecurityAuditAction, SecurityAuditVia, TenantRole
from app.common.exceptions import ForbiddenError, NotFoundError
from app.domain.interfaces.mode_switch_repository import IModeSwitchRepository
from app.domain.models.auth import ApiKey
from app.domain.models.membership import Membership
from app.domain.models.mode_switch import (
    SYSTEM_TENANT_KEY,
    SYSTEM_USER_KEY,
    DeploymentMode,
    PendingTakeover,
    TakeoverResourceCounts,
)
from app.domain.models.tenant import Tenant
from app.domain.models.user import User
from app.domain.services.mode_switch_service import ModeSwitchService
from app.domain.services.tenant_service import TenantService


class _MemoryModeSwitchRepo(IModeSwitchRepository):
    def __init__(self, *, mode: DeploymentMode | None = None, earliest: str | None = None) -> None:
        self.mode = mode
        self.pending: PendingTakeover | None = None
        self.earliest = earliest

    def get_deployment_mode(self) -> DeploymentMode | None:
        return self.mode

    def set_deployment_mode(self, mode: DeploymentMode) -> None:
        self.mode = mode

    def get_pending_takeover(self) -> PendingTakeover | None:
        return self.pending

    def record_pending_takeover(self, takeover: PendingTakeover) -> bool:
        if self.pending is not None:
            return False
        self.pending = takeover
        return True

    def claim_pending_takeover(self) -> PendingTakeover | None:
        claimed, self.pending = self.pending, None
        return claimed

    def clear_pending_takeover(self) -> bool:
        return self.claim_pending_takeover() is not None

    def count_tenant_resources(self, *, tenant_key: str) -> TakeoverResourceCounts:
        return TakeoverResourceCounts(plants=30, sites=3)

    def earliest_active_person_key(self, *, excluding: str) -> str | None:
        return self.earliest


def _user(key: str, *, active: bool = True, account_type: str = "human") -> User:
    return User.model_validate(
        {
            "_key": key,
            "email": f"{key}@example.com",
            "display_name": key.title(),
            "is_active": active,
            "account_type": account_type,
        }
    )


def _membership(user_key: str, tenant_key: str, *, active: bool = True, role: TenantRole = TenantRole.LEAD):
    return Membership(
        _key=f"{user_key}--{tenant_key}", user_key=user_key, tenant_key=tenant_key, role=role, is_active=active
    )


def _api_key(key: str, *, revoked: bool = False) -> ApiKey:
    return ApiKey(_key=key, user_key=SYSTEM_USER_KEY, label="mcp", key_hash="h", key_prefix="kp_abcd", revoked=revoked)


class _Stage:
    def __init__(
        self,
        *,
        mode: DeploymentMode | None = None,
        system_user: User | None = None,
        system_membership_active: bool = True,
        platform_admins: tuple[str, ...] = (),
        earliest: str | None = None,
    ) -> None:
        self.repo = _MemoryModeSwitchRepo(mode=mode, earliest=earliest)
        self.users: dict[str, User] = {}
        if system_user is not None:
            self.users[SYSTEM_USER_KEY] = system_user
        self.user_repo = MagicMock()
        self.user_repo.get_by_key.side_effect = self.users.get
        self.api_keys = MagicMock()
        self.api_keys.list_by_user.return_value = [_api_key("k1"), _api_key("k2", revoked=True)]
        self.api_keys.revoke.return_value = True
        self.sessions = MagicMock()
        self.sessions.list_active_for_user.return_value = []
        self.sessions.revoke_all_for_user.return_value = 2
        self.feeds = MagicMock()
        self.feeds.delete_by_user.return_value = 1
        self.audit = MagicMock()
        self.tenants = MagicMock(spec=TenantService)
        memberships = {
            (SYSTEM_USER_KEY, SYSTEM_TENANT_KEY): _membership(
                SYSTEM_USER_KEY, SYSTEM_TENANT_KEY, active=system_membership_active
            )
        }
        for admin in platform_admins:
            memberships[(admin, "platform")] = _membership(admin, "platform")
        self.tenants.get_membership.side_effect = lambda user_key, tenant_key: memberships.get((user_key, tenant_key))
        self.tenants.has_platform_admin.return_value = bool(platform_admins)
        self.tenants.get_tenant.return_value = Tenant(
            _key=SYSTEM_TENANT_KEY, name="Mein Garten", slug="mein-garten", owner_user_key=SYSTEM_USER_KEY
        )
        self.tenants.take_over_light_mode_tenant.return_value = Tenant(
            _key=SYSTEM_TENANT_KEY, name="Anna", slug="mein-garten", owner_user_key="anna"
        )
        self.tenants.grant_first_platform_admin.return_value = not platform_admins
        self.onboarding = MagicMock()
        self.service = ModeSwitchService(
            repo=self.repo,
            user_repo=self.user_repo,
            tenant_service=self.tenants,
            api_key_repo=self.api_keys,
            refresh_token_repo=self.sessions,
            calendar_feed_repo=self.feeds,
            security_audit=self.audit,
            onboarding_service=self.onboarding,
        )


# ── reconcile: what a start does ──────────────────────────────────────────


def test_first_full_start_after_light_seals_the_system_account_and_opens_the_takeover() -> None:
    stage = _Stage(mode="light", system_user=_user(SYSTEM_USER_KEY))

    outcome = stage.service.reconcile("full")

    assert outcome.previous_mode == "light"
    stage.user_repo.update_fields.assert_called_once_with(SYSTEM_USER_KEY, {"is_active": False})
    assert outcome.sealing.deactivated is True
    stage.api_keys.revoke.assert_called_once_with("k1")  # the revoked one is not touched again
    assert outcome.sealing.api_keys_revoked == 1
    stage.sessions.revoke_all_for_user.assert_called_once_with(SYSTEM_USER_KEY)
    stage.feeds.delete_by_user.assert_called_once_with(SYSTEM_USER_KEY, tenant_key=SYSTEM_TENANT_KEY)
    assert outcome.pending_takeover_recorded is True
    assert stage.repo.pending is not None and stage.repo.pending.system_tenant_key == SYSTEM_TENANT_KEY
    assert stage.repo.mode == "full"
    stage.audit.record_account_change.assert_called_once_with(
        action=SecurityAuditAction.ACCOUNT_DEACTIVATED,
        via=SecurityAuditVia.MODE_SWITCH,
        actor_user_key=SYSTEM_USER_KEY,
        target_user_key=SYSTEM_USER_KEY,
    )


def test_an_installation_without_recorded_mode_counts_as_light_when_the_system_account_exists() -> None:
    """Every installation upgraded to this code has no ``deployment_mode`` yet; the account decides."""
    stage = _Stage(mode=None, system_user=_user(SYSTEM_USER_KEY))

    outcome = stage.service.reconcile("full")

    assert (outcome.previous_mode, outcome.previous_mode_inferred) == ("light", True)
    assert outcome.pending_takeover_recorded is True


def test_a_repeated_full_start_writes_nothing_more() -> None:
    stage = _Stage(mode="full", system_user=_user(SYSTEM_USER_KEY, active=False))
    stage.api_keys.list_by_user.return_value = [_api_key("k1", revoked=True)]
    stage.feeds.delete_by_user.return_value = 0

    outcome = stage.service.reconcile("full")

    stage.user_repo.update_fields.assert_not_called()
    stage.api_keys.revoke.assert_not_called()
    stage.sessions.revoke_all_for_user.assert_not_called()
    stage.audit.record_account_change.assert_not_called()
    assert outcome.pending_takeover_recorded is False
    assert stage.repo.pending is None


def test_a_full_start_without_system_account_does_nothing() -> None:
    stage = _Stage(mode=None, system_user=None)

    outcome = stage.service.reconcile("full")

    assert outcome.previous_mode is None
    stage.user_repo.update_fields.assert_not_called()
    stage.api_keys.list_by_user.assert_not_called()
    assert stage.repo.mode == "full"


def test_no_takeover_is_opened_for_a_tenant_already_taken_over() -> None:
    stage = _Stage(mode="light", system_user=_user(SYSTEM_USER_KEY), system_membership_active=False)

    outcome = stage.service.reconcile("full")

    assert outcome.pending_takeover_recorded is False
    assert outcome.sealing.deactivated is True


def test_a_light_start_restores_the_system_account_and_drops_an_open_takeover() -> None:
    stage = _Stage(mode="full", system_user=_user(SYSTEM_USER_KEY, active=False))
    stage.repo.pending = PendingTakeover(created_at=datetime.now(UTC))
    stage.tenants.restore_light_mode_membership.return_value = True

    outcome = stage.service.reconcile("light")

    stage.user_repo.update_fields.assert_called_once_with(SYSTEM_USER_KEY, {"is_active": True})
    stage.tenants.restore_light_mode_membership.assert_called_once_with(
        tenant_key=SYSTEM_TENANT_KEY, system_user_key=SYSTEM_USER_KEY
    )
    assert outcome.system_account_restored is True
    assert stage.repo.pending is None
    assert stage.repo.mode == "light"
    stage.audit.record_account_change.assert_called_once()
    assert stage.audit.record_account_change.call_args.kwargs["action"] == SecurityAuditAction.ACCOUNT_REACTIVATED


# ── who may decide ────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("caller", "platform_admins", "earliest", "expected"),
    [
        ("anna", (), "anna", True),  # the first account of an instance without administrator
        ("max", (), "anna", False),  # a later account
        ("admin", ("admin",), "anna", True),  # the platform administrator
        ("anna", ("admin",), "anna", False),  # the first account beside an administrator
        (SYSTEM_USER_KEY, (), SYSTEM_USER_KEY, False),  # never the system account itself
    ],
)
def test_who_may_decide_the_takeover(caller, platform_admins, earliest, expected) -> None:
    stage = _Stage(platform_admins=platform_admins, earliest=earliest)

    assert stage.service.may_decide_takeover(_user(caller)) is expected


def test_a_service_account_may_not_decide() -> None:
    stage = _Stage(earliest="bot")

    assert stage.service.may_decide_takeover(_user("bot", account_type="service")) is False


def test_status_hides_the_tenant_from_an_account_that_may_not_decide() -> None:
    stage = _Stage(earliest="anna")
    stage.repo.pending = PendingTakeover(created_at=datetime.now(UTC))

    hidden = stage.service.takeover_status(_user("max"))
    shown = stage.service.takeover_status(_user("anna"))

    assert (hidden.pending, hidden.eligible, hidden.tenant_name, hidden.resource_counts) == (True, False, None, None)
    assert (shown.eligible, shown.tenant_slug) == (True, "mein-garten")
    assert shown.resource_counts is not None and shown.resource_counts.plants == 30


def test_status_without_takeover() -> None:
    assert _Stage().service.takeover_status(_user("anna")).pending is False


# ── the decision ──────────────────────────────────────────────────────────


def test_accepting_hands_over_the_tenant_and_the_platform_role() -> None:
    stage = _Stage(earliest="anna")
    stage.repo.pending = PendingTakeover(created_at=datetime.now(UTC))
    anna = _user("anna")

    result = stage.service.decide_takeover(anna, accept=True)

    stage.tenants.take_over_light_mode_tenant.assert_called_once_with(
        tenant_key=SYSTEM_TENANT_KEY, system_user_key=SYSTEM_USER_KEY, new_owner=anna
    )
    stage.tenants.grant_first_platform_admin.assert_called_once_with(anna)
    assert (result.accepted, result.tenant_slug, result.platform_admin_granted) == (True, "mein-garten", True)
    assert stage.repo.pending is None
    stage.onboarding.ensure_onboarding_state_for_user.assert_called_once_with(
        "anna", SYSTEM_TENANT_KEY, takeover_accepted=True
    )


def test_declining_keeps_the_tenant_and_still_hands_over_the_platform_role() -> None:
    stage = _Stage(earliest="anna")
    stage.repo.pending = PendingTakeover(created_at=datetime.now(UTC))

    result = stage.service.decide_takeover(_user("anna"), accept=False)

    stage.tenants.take_over_light_mode_tenant.assert_not_called()
    assert (result.accepted, result.tenant_slug, result.platform_admin_granted) == (False, None, True)
    assert stage.repo.pending is None
    stage.onboarding.ensure_onboarding_state_for_user.assert_not_called()


def test_an_account_that_may_not_decide_is_refused_and_the_takeover_stays_open() -> None:
    stage = _Stage(earliest="anna")
    stage.repo.pending = PendingTakeover(created_at=datetime.now(UTC))

    with pytest.raises(ForbiddenError):
        stage.service.decide_takeover(_user("max"), accept=True)

    assert stage.repo.pending is not None
    stage.tenants.take_over_light_mode_tenant.assert_not_called()


def test_a_second_decision_finds_nothing_open() -> None:
    stage = _Stage(earliest="anna")

    with pytest.raises(NotFoundError):
        stage.service.decide_takeover(_user("anna"), accept=True)


def test_a_failed_decision_reopens_the_takeover() -> None:
    stage = _Stage(earliest="anna")
    pending = PendingTakeover(created_at=datetime.now(UTC))
    stage.repo.pending = pending
    stage.tenants.take_over_light_mode_tenant.side_effect = ForbiddenError("frozen")

    with pytest.raises(ForbiddenError):
        stage.service.decide_takeover(_user("anna"), accept=True)

    assert stage.repo.pending == pending
