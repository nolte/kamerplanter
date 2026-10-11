"""Persistence of the deployment-mode bookkeeping (REQ-027 §7a, #1855)."""

from abc import ABC, abstractmethod
from datetime import datetime

from app.domain.models.mode_switch import DeploymentMode, PendingTakeover, TakeoverReceipt, TakeoverResourceCounts


class IModeSwitchRepository(ABC):
    @abstractmethod
    def get_deployment_mode(self) -> DeploymentMode | None:
        """The mode the last start recorded, or ``None`` before the first recording."""

    @abstractmethod
    def set_deployment_mode(self, mode: DeploymentMode) -> None:
        """Record *mode* as the mode of this start (idempotent)."""

    @abstractmethod
    def get_pending_takeover(self) -> PendingTakeover | None:
        """The open take-over (claimed or not), or ``None``."""

    @abstractmethod
    def record_pending_takeover(self, takeover: PendingTakeover) -> bool:
        """Open *takeover* unless one is open already; ``True`` when this call opened it."""

    @abstractmethod
    def claim_pending_takeover(self, *, claimant: str, now: datetime, stale_before: datetime) -> PendingTakeover | None:
        """Mark the open take-over as being decided by *claimant* — atomically (#1855 SEC-004).

        Succeeds when nobody holds a claim or the held claim is older than *stale_before*; ``None``
        when there is no open take-over or another live claim holds it. The document stays.
        """

    @abstractmethod
    def complete_pending_takeover(self, *, claimant: str) -> bool:
        """Remove the take-over *claimant* holds — after its decision succeeded."""

    @abstractmethod
    def release_pending_takeover(self, *, claimant: str) -> bool:
        """Drop *claimant*'s claim and leave the take-over open — after a decision that changed nothing."""

    @abstractmethod
    def holds_claim(self, *, claimant: str) -> bool:
        """Whether *claimant* still holds the claim on the open take-over (#1855 R2-003)."""

    @abstractmethod
    def mark_takeover_needs_attention(self, *, claimant: str, receipt: TakeoverReceipt) -> bool:
        """Store *receipt* - what a failed decision could not undo - on the take-over *claimant* holds (R2-002).

        Sets ``needs_attention``; the claim stays. ``False`` when *claimant* no longer holds it.
        """

    @abstractmethod
    def resolve_takeover_attention(self, *, claimant: str) -> bool:
        """Drop ``needs_attention`` and the stored receipt once *claimant* undid it (R2-002); the claim stays."""

    @abstractmethod
    def clear_pending_takeover(self) -> bool:
        """Remove the open take-over without deciding it (a light-mode start); ``True`` when one was removed."""

    @abstractmethod
    def count_tenant_resources(self, *, tenant_key: str) -> TakeoverResourceCounts:
        """How many plants, sites, runs, nutrient plans and tasks *tenant_key* holds."""

    @abstractmethod
    def earliest_eligible_person_key(self, *, excluding: str, created_since: datetime) -> str | None:
        """The key of the earliest account that may decide a take-over without a platform admin.

        Created at or after *created_since* (the take-over's own ``created_at``, #1855 SEC-002), active,
        not a service account, with a verified address and an active membership in a personal tenant it
        owns (SEC-008), other than *excluding*. Ties on ``created_at`` are broken by the key.
        """

    @abstractmethod
    def count_active_person_accounts(self, *, excluding: str) -> int:
        """How many active, non-service accounts other than *excluding* exist (#1855 SEC-007)."""
