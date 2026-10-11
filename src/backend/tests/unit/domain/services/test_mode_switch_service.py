"""#1855 / REQ-027 §7a — the light/full switch and the take-over of the light-mode data, unit level.

The measured gap (before the fix, ``develop`` ``9c8965982``): no code read or wrote the deployment
mode; after a switch to ``full`` the light-mode system account stayed active with its ``lead``
membership, every ``kp_`` key minted unauthenticated in light mode stayed valid, and the light-mode
data were reachable only as that account. The real-database proof of the same behaviour is
``tests/integration/test_light_to_full_upgrade_reach.py``; this module covers the decisions.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
import structlog

from app.common.enums import SecurityAuditAction, SecurityAuditVia, TenantRole
from app.common.exceptions import ForbiddenError, NotFoundError, UnauthorizedError, WriteConflictError
from app.domain.interfaces.mode_switch_repository import IModeSwitchRepository
from app.domain.models.auth import ApiKey
from app.domain.models.membership import Membership
from app.domain.models.mode_switch import (
    SYSTEM_TENANT_KEY,
    SYSTEM_USER_KEY,
    DeploymentMode,
    PendingTakeover,
    TakeoverReceipt,
    TakeoverResourceCounts,
)
from app.domain.models.tenant import Tenant
from app.domain.models.user import User
from app.domain.services.mode_switch_service import ModeSwitchService, TakeoverConfirmation
from app.domain.services.tenant_service import TenantService


class _MemoryModeSwitchRepo(IModeSwitchRepository):
    """In memory; the claim follows the Arango repository's rule (one live claim, TTL), the eligibility
    query is the integration test's (``test_light_to_full_upgrade_reach.py``)."""

    def __init__(self, *, mode: DeploymentMode | None = None, earliest: str | None = None) -> None:
        self.mode = mode
        self.pending: PendingTakeover | None = None
        self.earliest = earliest
        self.persons = 0

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

    def claim_pending_takeover(self, *, claimant: str, now: datetime, stale_before: datetime) -> PendingTakeover | None:
        if self.pending is None:
            return None
        held = self.pending.claim_id is not None and (self.pending.claimed_at or now) >= stale_before
        if held:
            return None
        self.pending = self.pending.model_copy(update={"claim_id": claimant, "claimed_at": now})
        return self.pending

    def complete_pending_takeover(self, *, claimant: str) -> bool:
        if self.pending is not None and self.pending.claim_id == claimant:
            self.pending = None
            return True
        return False

    def release_pending_takeover(self, *, claimant: str) -> bool:
        if self.pending is not None and self.pending.claim_id == claimant:
            self.pending = self.pending.model_copy(update={"claim_id": None, "claimed_at": None})
            return True
        return False

    def holds_claim(self, *, claimant: str) -> bool:
        return self.pending is not None and self.pending.claim_id == claimant

    def mark_takeover_needs_attention(self, *, claimant: str, receipt: TakeoverReceipt) -> bool:
        if not self.holds_claim(claimant=claimant):
            return False
        self.pending = self.pending.model_copy(update={"needs_attention": True, "receipt": receipt.model_copy()})
        return True

    def resolve_takeover_attention(self, *, claimant: str) -> bool:
        if not self.holds_claim(claimant=claimant):
            return False
        self.pending = self.pending.model_copy(update={"needs_attention": False, "receipt": None})
        return True

    def clear_pending_takeover(self) -> bool:
        had, self.pending = self.pending is not None, None
        return had

    def count_tenant_resources(self, *, tenant_key: str) -> TakeoverResourceCounts:
        return TakeoverResourceCounts(plants=30, sites=3)

    def earliest_eligible_person_key(self, *, excluding: str, created_since: datetime) -> str | None:
        return self.earliest

    def count_active_person_accounts(self, *, excluding: str) -> int:
        return self.persons


def _take_over(**kwargs) -> TakeoverReceipt:
    """The tenant service's take-over, as the double: it fills the caller's receipt as it writes (R2-001)."""
    receipt: TakeoverReceipt = kwargs["receipt"]
    receipt.tenant_slug = "mein-garten"
    receipt.previous_owner_key = SYSTEM_USER_KEY
    receipt.previous_name = "Mein Garten"
    receipt.ended_system_membership_key = "m-system"
    receipt.created_membership_key = "m-anna"
    receipt.tenant_changed = True
    return receipt


def _undone(receipt: TakeoverReceipt) -> None:
    """The tenant service's undo, as the double: it clears what it took back."""
    receipt.ended_system_membership_key = receipt.created_membership_key = None
    receipt.platform_created_membership_key = None
    receipt.tenant_changed = False


def _decide(stage, who: str, *, accept: bool, api_key: bool = False):
    return stage.service.decide_takeover(
        _user(who),
        accept=accept,
        confirmation=TakeoverConfirmation(password="pw"),
        authenticated_with_api_key=api_key,
        client_ip=None,
    )


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
        self.tenants.take_over_light_mode_tenant.side_effect = _take_over
        self.tenants.undo_light_mode_takeover.side_effect = _undone
        self.tenants.grant_first_platform_admin.return_value = not platform_admins
        self.onboarding = MagicMock()
        self.step_up = MagicMock()
        self.service = ModeSwitchService(
            repo=self.repo,
            user_repo=self.user_repo,
            tenant_service=self.tenants,
            api_key_repo=self.api_keys,
            refresh_token_repo=self.sessions,
            calendar_feed_repo=self.feeds,
            security_audit=self.audit,
            step_up_verifier=self.step_up,
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
    stage.repo.pending = PendingTakeover(created_at=datetime.now(UTC))

    assert stage.service.may_decide_takeover(_user(caller)) is expected


def test_a_service_account_may_not_decide() -> None:
    stage = _Stage(earliest="bot")
    stage.repo.pending = PendingTakeover(created_at=datetime.now(UTC))

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

    result = _decide(stage, "anna", accept=True)

    kwargs = stage.tenants.take_over_light_mode_tenant.call_args.kwargs
    assert (kwargs["tenant_key"], kwargs["system_user_key"], kwargs["new_owner"]) == (
        SYSTEM_TENANT_KEY,
        SYSTEM_USER_KEY,
        anna,
    )
    # one receipt for the whole decision: the grant writes into the take-over's
    grant = stage.tenants.grant_first_platform_admin.call_args
    assert grant.args == (anna,) and grant.kwargs["receipt"] is kwargs["receipt"]
    assert (result.accepted, result.tenant_slug, result.platform_admin_granted) == (True, "mein-garten", True)
    assert stage.repo.pending is None
    stage.onboarding.ensure_onboarding_state_for_user.assert_called_once_with(
        "anna", SYSTEM_TENANT_KEY, takeover_accepted=True
    )


def test_declining_keeps_the_tenant_and_still_hands_over_the_platform_role() -> None:
    stage = _Stage(earliest="anna")
    stage.repo.pending = PendingTakeover(created_at=datetime.now(UTC))

    result = _decide(stage, "anna", accept=False)

    stage.tenants.take_over_light_mode_tenant.assert_not_called()
    assert (result.accepted, result.tenant_slug, result.platform_admin_granted) == (False, None, True)
    assert stage.repo.pending is None
    stage.onboarding.ensure_onboarding_state_for_user.assert_not_called()


def test_an_account_that_may_not_decide_is_refused_and_the_takeover_stays_open() -> None:
    stage = _Stage(earliest="anna")
    stage.repo.pending = PendingTakeover(created_at=datetime.now(UTC))

    with pytest.raises(ForbiddenError):
        _decide(stage, "max", accept=True)

    assert stage.repo.pending is not None
    stage.tenants.take_over_light_mode_tenant.assert_not_called()


def test_a_second_decision_finds_nothing_open() -> None:
    stage = _Stage(earliest="anna")

    with pytest.raises(NotFoundError):
        _decide(stage, "anna", accept=True)


def test_a_decision_refused_before_writing_reopens_the_takeover() -> None:
    stage = _Stage(earliest="anna")
    pending = PendingTakeover(created_at=datetime.now(UTC))
    stage.repo.pending = pending
    stage.tenants.take_over_light_mode_tenant.side_effect = ForbiddenError("frozen")

    with pytest.raises(ForbiddenError):
        _decide(stage, "anna", accept=True)

    assert stage.repo.pending == pending  # released: open again, unclaimed
    stage.tenants.undo_light_mode_takeover.assert_not_called()


def test_grant_raises_after_a_successful_take_over() -> None:
    """#1855 SEC-004 — the take-over stood, the platform grant failed: undone, then reopened."""
    stage = _Stage(earliest="anna")
    pending = PendingTakeover(created_at=datetime.now(UTC))
    stage.repo.pending = pending
    stage.tenants.grant_first_platform_admin.side_effect = RuntimeError("store down")

    with pytest.raises(RuntimeError):
        _decide(stage, "anna", accept=True)

    undone = stage.tenants.undo_light_mode_takeover.call_args.args[0]
    assert undone.new_owner_key == "anna" and not undone.has_writes()
    assert stage.repo.pending == pending
    assert [c.kwargs["action"] for c in stage.audit.record_takeover_decision.call_args_list] == []


def test_an_undo_that_fails_keeps_the_takeover_claimed() -> None:
    """Reopened only on a consistent state: an undo that failed keeps the claim and stores the receipt (R2-002)."""
    stage = _Stage(earliest="anna")
    stage.repo.pending = PendingTakeover(created_at=datetime.now(UTC))
    stage.tenants.grant_first_platform_admin.side_effect = RuntimeError("store down")
    stage.tenants.undo_light_mode_takeover.side_effect = RuntimeError("still down")

    with pytest.raises(RuntimeError, match="store down"):
        _decide(stage, "anna", accept=True)

    pending = stage.repo.pending
    assert pending is not None and pending.claim_id is not None
    assert pending.needs_attention is True
    assert pending.receipt is not None and pending.receipt.created_membership_key == "m-anna"
    assert _audited(stage)[-1] == (SecurityAuditAction.TAKEOVER_UNDO_FAILED, "undo_failed")
    with pytest.raises(NotFoundError):  # a second decision cannot claim it meanwhile
        _decide(stage, "anna", accept=True)


def _audited(stage) -> list[tuple]:
    return [(c.kwargs["action"], c.kwargs.get("reason")) for c in stage.audit.record_takeover_decision.call_args_list]


def _lapse(stage) -> None:
    stage.repo.pending = stage.repo.pending.model_copy(update={"claimed_at": datetime.now(UTC) - timedelta(hours=1)})


def test_a_write_that_fails_inside_the_take_over_is_undone_from_the_partial_receipt() -> None:
    """#1855 R2-001 — the take-over wrote, then its own audit row failed: the caller still holds the receipt."""
    stage = _Stage(earliest="anna")
    stage.repo.pending = PendingTakeover(created_at=datetime.now(UTC))

    def half(**kwargs):
        kwargs["receipt"].ended_system_membership_key = "m-system"
        kwargs["receipt"].created_membership_key = "m-anna"
        raise RuntimeError("audit store down")

    stage.tenants.take_over_light_mode_tenant.side_effect = half

    with pytest.raises(RuntimeError, match="audit store down"):
        _decide(stage, "anna", accept=True)

    stage.tenants.undo_light_mode_takeover.assert_called_once()
    assert stage.tenants.undo_light_mode_takeover.call_args.args[0].new_owner_key == "anna"
    assert stage.repo.pending is not None and stage.repo.pending.claim_id is None  # undone, then reopened


def test_a_lapsed_claim_with_a_stored_receipt_is_undone_before_anyone_decides() -> None:
    """#1855 R2-002 — the TTL does not hand an inconsistent take-over to the next decision."""
    stage = _Stage(earliest="anna")
    stage.repo.pending = PendingTakeover(created_at=datetime.now(UTC))
    stage.tenants.grant_first_platform_admin.side_effect = RuntimeError("store down")
    stage.tenants.undo_light_mode_takeover.side_effect = RuntimeError("still down")
    with pytest.raises(RuntimeError):
        _decide(stage, "anna", accept=True)
    _lapse(stage)

    # The store is still down: the stored undo fails again - 409, nothing decided, receipt kept.
    with pytest.raises(WriteConflictError):
        _decide(stage, "anna", accept=False)
    assert stage.repo.pending is not None and stage.repo.pending.needs_attention is True
    assert stage.tenants.grant_first_platform_admin.call_count == 1

    # The store is back: the stored receipt is undone first, then the decision runs.
    _lapse(stage)
    stage.tenants.undo_light_mode_takeover.side_effect = _undone
    stage.tenants.grant_first_platform_admin.side_effect = None
    assert _decide(stage, "anna", accept=False).accepted is False
    stored = stage.tenants.undo_light_mode_takeover.call_args_list[-1].args[0]
    assert stored.created_membership_key is None  # the stored receipt was the one undone
    assert stage.repo.pending is None


def test_a_lost_claim_is_not_a_success() -> None:
    """#1855 R2-003 — ``complete_pending_takeover`` False: 409, no ``takeover_accepted`` row."""
    stage = _Stage(earliest="anna")
    stage.repo.pending = PendingTakeover(created_at=datetime.now(UTC))
    stage.tenants.grant_first_platform_admin.side_effect = lambda account, *, receipt: (
        stage.repo.clear_pending_takeover()
    )

    with pytest.raises(WriteConflictError):
        _decide(stage, "anna", accept=True)

    actions = [a for a, _ in _audited(stage)]
    assert SecurityAuditAction.TAKEOVER_ACCEPTED not in actions
    assert actions[-1] == SecurityAuditAction.TAKEOVER_UNDO_FAILED


def test_no_undo_without_the_claim() -> None:
    """#1855 R2-003 — a decision that lost its claim does not undo: another may be writing the tenant."""
    stage = _Stage(earliest="anna")
    stage.repo.pending = PendingTakeover(created_at=datetime.now(UTC))

    def lose_and_fail(account, *, receipt):
        stage.repo.pending = stage.repo.pending.model_copy(update={"claim_id": "other"})
        raise RuntimeError("store down")

    stage.tenants.grant_first_platform_admin.side_effect = lose_and_fail

    with pytest.raises(RuntimeError):
        _decide(stage, "anna", accept=True)

    stage.tenants.undo_light_mode_takeover.assert_not_called()
    assert _audited(stage)[-1] == (SecurityAuditAction.TAKEOVER_UNDO_FAILED, "claim_lost_before_undo")


def test_a_decision_past_its_deadline_is_undone() -> None:
    """#1855 R2-003 — the writes stop well inside the TTL; past the deadline they are undone (409)."""
    stage = _Stage(earliest="anna")
    stage.repo.pending = PendingTakeover(created_at=datetime.now(UTC))
    stage.service._claim_ttl = timedelta(seconds=-2)  # the deadline lies before the first write

    with pytest.raises(WriteConflictError):
        _decide(stage, "anna", accept=True)

    stage.tenants.undo_light_mode_takeover.assert_called_once()
    stage.tenants.grant_first_platform_admin.assert_not_called()


def test_refusals_are_audited() -> None:
    stage = _Stage(earliest="anna")
    stage.repo.pending = PendingTakeover(created_at=datetime.now(UTC))

    with pytest.raises(ForbiddenError):
        _decide(stage, "anna", accept=True, api_key=True)
    with pytest.raises(ForbiddenError):
        _decide(stage, "max", accept=True)

    assert _audited(stage) == [
        (SecurityAuditAction.TAKEOVER_REFUSED, "api_key"),
        (SecurityAuditAction.TAKEOVER_REFUSED, "not_eligible"),
    ]


def test_a_light_start_undoes_a_stored_receipt_before_dropping_the_takeover() -> None:
    stage = _Stage(mode="full", system_user=_user(SYSTEM_USER_KEY, active=False))
    receipt = TakeoverReceipt(
        tenant_key=SYSTEM_TENANT_KEY, new_owner_key="anna", system_user_key=SYSTEM_USER_KEY, created_membership_key="m"
    )
    stage.repo.pending = PendingTakeover(created_at=datetime.now(UTC), needs_attention=True, receipt=receipt)
    stage.tenants.undo_light_mode_takeover.side_effect = RuntimeError("down")

    stage.service.reconcile("light")
    assert stage.repo.pending is not None  # kept: the only record of what is left

    stage.tenants.undo_light_mode_takeover.side_effect = _undone
    stage.service.reconcile("light")
    assert stage.repo.pending is None


def test_a_claim_that_lapsed_may_be_taken_over() -> None:
    stage = _Stage(earliest="anna")
    stage.repo.pending = PendingTakeover(
        created_at=datetime.now(UTC), claim_id="dead:1", claimed_at=datetime.now(UTC) - timedelta(hours=1)
    )

    assert _decide(stage, "anna", accept=False).accepted is False
    assert stage.repo.pending is None


def test_an_api_key_is_refused_before_anything() -> None:
    stage = _Stage(earliest="anna")
    stage.repo.pending = PendingTakeover(created_at=datetime.now(UTC))

    with pytest.raises(ForbiddenError):
        _decide(stage, "anna", accept=True, api_key=True)

    stage.step_up.verify.assert_not_called()
    assert stage.repo.pending.claim_id is None


def test_the_decision_passes_the_step_up_bound_to_the_tenant() -> None:
    """#1855 SEC-003 — the act ``light_mode_takeover``, target the light-mode tenant; a refusal writes nothing."""
    stage = _Stage(earliest="anna")
    stage.repo.pending = PendingTakeover(created_at=datetime.now(UTC))
    stage.step_up.verify.side_effect = UnauthorizedError("wrong password")

    with pytest.raises(UnauthorizedError):
        _decide(stage, "anna", accept=True)

    kwargs = stage.step_up.verify.call_args.kwargs
    assert (kwargs["action"], kwargs["target"], kwargs["password"]) == ("light_mode_takeover", SYSTEM_TENANT_KEY, "pw")
    stage.tenants.take_over_light_mode_tenant.assert_not_called()
    assert stage.repo.pending.claim_id is None


def test_the_right_to_decide_is_rechecked_after_the_claim() -> None:
    """TOCTOU: a platform admin appearing between the check and the claim — released, 403."""
    stage = _Stage(earliest="anna")
    stage.repo.pending = PendingTakeover(created_at=datetime.now(UTC))
    stage.tenants.has_platform_admin.side_effect = [False, True]

    with pytest.raises(ForbiddenError):
        _decide(stage, "anna", accept=True)

    assert stage.repo.pending is not None and stage.repo.pending.claim_id is None
    stage.tenants.take_over_light_mode_tenant.assert_not_called()


def test_the_decision_is_audited() -> None:
    stage = _Stage(earliest="anna")
    stage.repo.pending = PendingTakeover(created_at=datetime.now(UTC))

    _decide(stage, "anna", accept=False)

    stage.audit.record_takeover_decision.assert_called_once_with(
        action=SecurityAuditAction.TAKEOVER_DECLINED,
        actor_user_key="anna",
        tenant_key=SYSTEM_TENANT_KEY,
        platform_admin_granted=True,
        step_up_method=stage.step_up.verify.return_value,
        reason=None,
    )


def test_the_seal_writes_one_aggregate_audit_row() -> None:
    stage = _Stage(mode="light", system_user=_user(SYSTEM_USER_KEY))

    stage.service.reconcile("full")

    stage.audit.record_system_account_sealed.assert_called_once_with(
        system_user_key=SYSTEM_USER_KEY, revoked_counts={"api_keys": 1, "sessions": 2, "calendar_feeds": 1}
    )


def test_a_light_start_with_person_accounts_is_reported_as_critical() -> None:
    """#1855 SEC-007 — critical, not fatal: the documented downgrade (REQ-027 Szenario 7/8) stays possible."""
    stage = _Stage(mode="full", system_user=_user(SYSTEM_USER_KEY, active=False))
    stage.repo.persons = 2

    with structlog.testing.capture_logs() as logs:
        stage.service.reconcile("light")

    critical = [line for line in logs if line["event"] == "light_mode_start_with_person_accounts"]
    assert critical and critical[0]["log_level"] == "critical" and critical[0]["person_accounts"] == 2
    assert stage.repo.mode == "light"
