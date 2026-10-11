"""The switch between light and full mode, and the take-over of the light-mode data (REQ-027 §7a, #1855).

**On every start** (:meth:`ModeSwitchService.reconcile`, run by the seed registry under the
migration lock):

* in ``full`` mode the light-mode system account is *sealed*: deactivated, its API keys revoked,
  its sessions ended, its calendar feeds deleted. Everything of it was issued without
  authentication (#1844) and proves nothing about who asked for it; in full mode it would be a
  working credential of a ``lead`` with both administrative scopes. Idempotent - a second start
  finds nothing left to do. The first full-mode start after a light-mode one also opens a
  *pending take-over*. (The authentication paths refuse the account in full mode on their own,
  whatever is stored - ``system_account_refused``, SEC-006.)
* in ``light`` mode the system account and its membership are made usable again (a switch back,
  REQ-027 Szenario 7) and an open take-over is dropped - nobody can decide it there. Person accounts
  beside the system account are reported as ``critical`` (SEC-007): light mode serves every request as
  the system account, without authentication.

**The take-over** (:meth:`ModeSwitchService.decide_takeover`, ``POST /system/takeover``): the
platform administrator - or, on an instance that has none, the earliest *eligible* account
registered after the take-over opened (verified address, own personal garden; SEC-002/008) -
accepts (the light-mode tenant becomes theirs, :meth:`TenantService.take_over_light_mode_tenant`)
or declines (the tenant stays, without owner, for a platform administrator to deal with). Either
decision makes an instance without a platform administrator hand that role to the deciding
account (Szenario 5 step 7e, Szenario 6 step 9; operator-accepted risk SEC-001, REQ-027 §7a). The
decision passes the account's own step-up (``light_mode_takeover``, SEC-003); an API key is refused.
The pending take-over is *claimed* (``claim_id`` / ``claimed_at``, with a TTL), re-checked after the
claim, and removed only once the decision succeeded; a decision that fails after writing undoes its
writes and reopens the take-over only when the undo succeeded (SEC-004).

Source code is English only (NFR-003).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import structlog

from app.common.enums import SecurityAuditAction, SecurityAuditVia, TenantRole
from app.common.exceptions import ForbiddenError, NotFoundError
from app.common.log_privacy import log_subject
from app.domain.interfaces.api_key_repository import IApiKeyRepository
from app.domain.interfaces.calendar_feed_repository import ICalendarFeedRepository
from app.domain.interfaces.mode_switch_repository import IModeSwitchRepository
from app.domain.interfaces.refresh_token_repository import IRefreshTokenRepository
from app.domain.interfaces.user_repository import IUserRepository
from app.domain.models.mode_switch import (
    SYSTEM_TENANT_KEY,
    SYSTEM_USER_KEY,
    TAKEOVER_CLAIM_TTL_SECONDS,
    DeploymentMode,
    ModeSwitchOutcome,
    PendingTakeover,
    SystemAccountSealing,
    TakeoverReceipt,
    TakeoverResult,
    TakeoverStatus,
)
from app.domain.models.user import User, allows_interactive_auth
from app.domain.services.security_audit_service import SecurityAuditService
from app.domain.services.step_up_service import StepUpVerifier
from app.domain.services.tenant_service import TenantService

if TYPE_CHECKING:
    from app.domain.services.onboarding_service import OnboardingService

logger = structlog.get_logger()

#: The technical tenant whose ``lead`` membership is the platform role (REQ-049 §2.5).
_PLATFORM_TENANT_KEY = "platform"


@dataclass(frozen=True)
class TakeoverConfirmation:
    """The deciding account's step-up (``light_mode_takeover``, #1855 SEC-003): one of the three factors."""

    password: str | None = None
    step_up_code: str | None = None
    step_up_token: str | None = None


class ModeSwitchService:
    def __init__(
        self,
        *,
        repo: IModeSwitchRepository,
        user_repo: IUserRepository,
        tenant_service: TenantService,
        api_key_repo: IApiKeyRepository,
        refresh_token_repo: IRefreshTokenRepository,
        calendar_feed_repo: ICalendarFeedRepository,
        security_audit: SecurityAuditService | None,
        step_up_verifier: StepUpVerifier,
        onboarding_service: OnboardingService | None = None,
        claim_ttl: timedelta = timedelta(seconds=TAKEOVER_CLAIM_TTL_SECONDS),
    ) -> None:
        self._repo = repo
        self._user_repo = user_repo
        self._tenant_service = tenant_service
        self._api_key_repo = api_key_repo
        self._refresh_token_repo = refresh_token_repo
        self._calendar_feed_repo = calendar_feed_repo
        self._security_audit = security_audit
        self._step_up_verifier = step_up_verifier
        self._onboarding_service = onboarding_service
        self._claim_ttl = claim_ttl

    # ── start-up reconciliation ─────────────────────────────────────

    def reconcile(self, current_mode: DeploymentMode) -> ModeSwitchOutcome:
        """Bring the stored state in line with *current_mode* and record it (REQ-027 §7a.1).

        The previous mode is the recorded one. An installation that ran before this bookkeeping
        existed has none recorded; there the system account decides: only the light-mode seed
        writes it, so its presence means the instance ran in light mode (``previous_mode_inferred``).
        """
        stored = self._repo.get_deployment_mode()
        system_user = self._user_repo.get_by_key(SYSTEM_USER_KEY)
        previous: DeploymentMode | None = stored
        inferred = False
        if stored is None and system_user is not None:
            previous, inferred = "light", True
        outcome = ModeSwitchOutcome(current_mode=current_mode, previous_mode=previous, previous_mode_inferred=inferred)

        if current_mode == "full":
            if system_user is not None:
                outcome.sealing = self.seal_system_account(system_user)
                if previous == "light":
                    outcome.pending_takeover_recorded = self._open_takeover()
        else:
            self._warn_about_person_accounts_in_light_mode()
            if system_user is not None:
                outcome.system_account_restored = self._restore_system_account(system_user)
            if self._repo.clear_pending_takeover():
                logger.info("light_mode_takeover_dropped", reason="light_mode_start")

        self._repo.set_deployment_mode(current_mode)
        if previous is not None and previous != current_mode:
            logger.warning(
                "deployment_mode_switched",
                previous_mode=previous,
                current_mode=current_mode,
                previous_mode_inferred=inferred,
            )
        return outcome

    def _warn_about_person_accounts_in_light_mode(self) -> None:
        """Report person accounts on a light-mode start (#1855 SEC-007) - critical, not fatal.

        Light mode answers every request as the system account, without authentication; accounts
        created in full mode stay in the database but cannot sign in. REQ-027 Szenario 7/8 makes the
        downgrade a supported switch of one environment variable (NK-01), so the start does not refuse
        it - an operator who did not mean to expose the data sees this line instead.
        """
        persons = self._repo.count_active_person_accounts(excluding=SYSTEM_USER_KEY)
        if persons:
            logger.critical(
                "light_mode_start_with_person_accounts",
                person_accounts=persons,
                detail=(
                    "the instance runs without authentication while person accounts exist; every request acts "
                    "as the light-mode system account. Switch back to KAMERPLANTER_MODE=full unless intended."
                ),
            )

    def seal_system_account(self, system_user: User) -> SystemAccountSealing:
        """Leave no way into the light-mode system account in full mode (#1855, REQ-027 AK-16, AK-35).

        Deactivated (every sign-in, refresh and key check asks ``is_active``), and - so that a later
        switch back to light mode, which reactivates the account, does not revive them - every API key
        revoked, every session ended and every calendar feed deleted. Each step only acts on what is
        still live, so a repeated start writes nothing and records nothing. A start that changed
        anything writes one aggregate audit row (``system_account_sealed``, SEC-005).
        """
        user_key = system_user.key or SYSTEM_USER_KEY
        sealing = SystemAccountSealing()
        if system_user.is_active:
            self._user_repo.update_fields(user_key, {"is_active": False})
            self._audit_account(SecurityAuditAction.ACCOUNT_DEACTIVATED, user_key)
            sealing.deactivated = True
        for api_key in self._api_key_repo.list_by_user(user_key):
            if not api_key.revoked and api_key.key and self._api_key_repo.revoke(api_key.key):
                sealing.api_keys_revoked += 1
        if sealing.deactivated or self._refresh_token_repo.list_active_for_user(user_key):
            sealing.sessions_revoked = int(self._refresh_token_repo.revoke_all_for_user(user_key) or 0)
        sealing.calendar_feeds_deleted = int(
            self._calendar_feed_repo.delete_by_user(user_key, tenant_key=SYSTEM_TENANT_KEY) or 0
        )
        if sealing != SystemAccountSealing():
            if self._security_audit is not None:
                self._security_audit.record_system_account_sealed(
                    system_user_key=user_key,
                    revoked_counts={
                        "api_keys": sealing.api_keys_revoked,
                        "sessions": sealing.sessions_revoked,
                        "calendar_feeds": sealing.calendar_feeds_deleted,
                    },
                )
            logger.warning(
                "light_mode_system_account_sealed",
                deactivated=sealing.deactivated,
                api_keys_revoked=sealing.api_keys_revoked,
                sessions_revoked=sealing.sessions_revoked,
                calendar_feeds_deleted=sealing.calendar_feeds_deleted,
            )
        return sealing

    def _open_takeover(self) -> bool:
        """Open a take-over of the light-mode tenant, unless one is open or nobody holds it any more.

        Nothing to take over when the tenant is gone or not active, or when the system account's
        membership in it already ended (an earlier take-over, REQ-027 Szenario 8 phase 4 reopens it
        only after a switch back to light mode restored the membership).
        """
        membership = self._tenant_service.get_membership(SYSTEM_USER_KEY, SYSTEM_TENANT_KEY)
        if membership is None or not membership.is_active:
            return False
        try:
            system_tenant = self._tenant_service.get_tenant(SYSTEM_TENANT_KEY)
        except NotFoundError:
            return False
        if not system_tenant.is_active:
            return False
        opened = self._repo.record_pending_takeover(
            PendingTakeover(system_tenant_key=SYSTEM_TENANT_KEY, created_at=datetime.now(UTC))
        )
        if opened:
            logger.warning("light_mode_takeover_opened")
        return opened

    def _restore_system_account(self, system_user: User) -> bool:
        """Make the system account usable again in light mode: active, member of its tenant (Szenario 7)."""
        user_key = system_user.key or SYSTEM_USER_KEY
        restored = False
        if not system_user.is_active:
            self._user_repo.update_fields(user_key, {"is_active": True})
            self._audit_account(SecurityAuditAction.ACCOUNT_REACTIVATED, user_key)
            restored = True
        if self._tenant_service.restore_light_mode_membership(tenant_key=SYSTEM_TENANT_KEY, system_user_key=user_key):
            restored = True
        if restored:
            logger.warning("light_mode_system_account_restored")
        return restored

    def _audit_account(self, action: SecurityAuditAction, user_key: str) -> None:
        """The audit row of the start changing the system account's ``is_active`` (no person acted)."""
        if self._security_audit is None:
            return
        self._security_audit.record_account_change(
            action=action,
            via=SecurityAuditVia.MODE_SWITCH,
            actor_user_key=user_key,
            target_user_key=user_key,
        )

    # ── the take-over ───────────────────────────────────────────────

    def may_decide_takeover(self, account: User, pending: PendingTakeover | None = None) -> bool:
        """Whether *account* may decide the take-over (REQ-027 §7a.2, #1855 SEC-002/SEC-008).

        A person account other than the system account, and either the platform administrator or -
        on an instance without one - the earliest *eligible* account registered at or after the
        take-over opened: active, verified address, its own personal garden. An account that existed
        before the switch (or an unverified, inactive or service account) is never "the first account";
        such an instance needs a platform admin (``python -m app.migrations.add_platform_admin``).
        Deterministic: two accounts cannot both be the earliest.
        """
        account_key = account.key or ""
        if not account_key or account_key == SYSTEM_USER_KEY or not account.is_active:
            return False
        if not allows_interactive_auth(account):
            return False
        platform = self._tenant_service.get_membership(account_key, _PLATFORM_TENANT_KEY)
        if platform is not None and platform.is_active and platform.role == TenantRole.LEAD:
            return True
        if self._tenant_service.has_platform_admin():
            return False
        opened = pending or self._repo.get_pending_takeover()
        if opened is None:
            return False
        earliest = self._repo.earliest_eligible_person_key(excluding=SYSTEM_USER_KEY, created_since=opened.created_at)
        return earliest == account_key

    def takeover_status(self, account: User) -> TakeoverStatus:
        """Whether a take-over is open; the tenant and its size only for an account that may decide it."""
        pending = self._repo.get_pending_takeover()
        if pending is None:
            return TakeoverStatus(pending=False)
        if not self.may_decide_takeover(account, pending):
            return TakeoverStatus(pending=True, eligible=False)
        try:
            tenant = self._tenant_service.get_tenant(pending.system_tenant_key)
        except NotFoundError:
            return TakeoverStatus(pending=True, eligible=True)
        return TakeoverStatus(
            pending=True,
            eligible=True,
            tenant_key=tenant.key,
            tenant_name=tenant.name,
            tenant_slug=tenant.slug,
            resource_counts=self._repo.count_tenant_resources(tenant_key=pending.system_tenant_key),
        )

    def decide_takeover(
        self,
        account: User,
        *,
        accept: bool,
        confirmation: TakeoverConfirmation,
        authenticated_with_api_key: bool,
        client_ip: str | None,
    ) -> TakeoverResult:
        """Accept or decline the open take-over as *account* (REQ-027 Szenario 5 / 6).

        Order: an API key is refused (403); no open take-over is 404; an account that may not decide is
        refused (403); the account's step-up (``light_mode_takeover``, bound to the tenant) is verified;
        the take-over is claimed (404 while another live decision holds it) and the right to decide is
        re-checked on the claimed state (403, the claim released). Then the writes; when one fails, the
        writes before it are undone and the claim released - or, when the undo fails too, the claim is
        kept (it lapses after the TTL) and the failure logged as critical. Only a decision that succeeded
        removes the take-over (#1855 SEC-004).
        """
        if authenticated_with_api_key:
            raise ForbiddenError("The light-mode take-over is decided in a signed-in session, not with an API key.")
        pending = self._repo.get_pending_takeover()
        if pending is None:
            raise NotFoundError("PendingTakeover", "pending_takeover")
        if not self.may_decide_takeover(account, pending):
            raise ForbiddenError("Only the platform administrator or the first account can decide the take-over.")
        self._step_up_verifier.verify(
            account,
            action="light_mode_takeover",
            target=pending.system_tenant_key,
            echo_ok=None,
            password=confirmation.password,
            code=confirmation.step_up_code,
            reauth_token=confirmation.step_up_token,
            authenticated_with_api_key=authenticated_with_api_key,
            client_ip=client_ip,
        )

        account_key = account.key or ""
        claimant = uuid.uuid4().hex  # an opaque token: the stored claim names no account
        now = datetime.now(UTC)
        claimed = self._repo.claim_pending_takeover(claimant=claimant, now=now, stale_before=now - self._claim_ttl)
        if claimed is None:
            raise NotFoundError("PendingTakeover", "pending_takeover")
        if not self.may_decide_takeover(account, claimed):
            self._repo.release_pending_takeover(claimant=claimant)
            raise ForbiddenError("Only the platform administrator or the first account can decide the take-over.")

        receipt: TakeoverReceipt | None = None
        try:
            if accept:
                receipt = self._tenant_service.take_over_light_mode_tenant(
                    tenant_key=claimed.system_tenant_key, system_user_key=SYSTEM_USER_KEY, new_owner=account
                )
            granted = self._tenant_service.grant_first_platform_admin(account)
        except Exception:
            self._settle_failed_decision(claimant, receipt)
            raise

        self._repo.complete_pending_takeover(claimant=claimant)
        if self._security_audit is not None:
            self._security_audit.record_takeover_decision(
                action=SecurityAuditAction.TAKEOVER_ACCEPTED if accept else SecurityAuditAction.TAKEOVER_DECLINED,
                actor_user_key=account_key,
                tenant_key=claimed.system_tenant_key,
                platform_admin_granted=granted,
            )
        if accept:
            self._complete_onboarding(account_key, claimed.system_tenant_key)
        logger.warning(
            "light_mode_takeover_decided",
            accepted=accept,
            subject=log_subject(account_key),
            platform_admin_granted=granted,
        )
        return TakeoverResult(
            accepted=accept, tenant_slug=receipt.tenant_slug if receipt else None, platform_admin_granted=granted
        )

    def _settle_failed_decision(self, claimant: str, receipt: TakeoverReceipt | None) -> None:
        """Undo a failed decision's writes; reopen the take-over only on a consistent state (SEC-004)."""
        if receipt is not None:
            try:
                self._tenant_service.undo_light_mode_takeover(receipt)
            except Exception as exc:  # noqa: BLE001 - the original failure is re-raised by the caller
                logger.critical(
                    "light_mode_takeover_undo_failed",
                    subject=log_subject(receipt.new_owner_key),
                    error_type=type(exc).__name__,
                    detail="the take-over stays claimed until its claim lapses; check the light-mode tenant's members",
                )
                return
        self._repo.release_pending_takeover(claimant=claimant)

    def _complete_onboarding(self, account_key: str, tenant_key: str) -> None:
        """Mark the wizard done for an account that took a set-up garden over (best effort)."""
        if self._onboarding_service is None:
            return
        try:
            self._onboarding_service.ensure_onboarding_state_for_user(account_key, tenant_key, takeover_accepted=True)
        except Exception as exc:  # noqa: BLE001 - the take-over stands; the wizard is a convenience
            logger.warning("light_mode_takeover_onboarding_not_marked", error_type=type(exc).__name__)
