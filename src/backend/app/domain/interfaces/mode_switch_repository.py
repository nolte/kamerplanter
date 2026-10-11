"""Persistence of the deployment-mode bookkeeping (REQ-027 §7a, #1855)."""

from abc import ABC, abstractmethod

from app.domain.models.mode_switch import DeploymentMode, PendingTakeover, TakeoverResourceCounts


class IModeSwitchRepository(ABC):
    @abstractmethod
    def get_deployment_mode(self) -> DeploymentMode | None:
        """The mode the last start recorded, or ``None`` before the first recording."""

    @abstractmethod
    def set_deployment_mode(self, mode: DeploymentMode) -> None:
        """Record *mode* as the mode of this start (idempotent)."""

    @abstractmethod
    def get_pending_takeover(self) -> PendingTakeover | None:
        """The open take-over, or ``None``."""

    @abstractmethod
    def record_pending_takeover(self, takeover: PendingTakeover) -> bool:
        """Open *takeover* unless one is open already; ``True`` when this call opened it."""

    @abstractmethod
    def claim_pending_takeover(self) -> PendingTakeover | None:
        """Remove the open take-over and return it — atomically, so two decisions cannot both claim it."""

    @abstractmethod
    def clear_pending_takeover(self) -> bool:
        """Remove the open take-over without deciding it; ``True`` when one was removed."""

    @abstractmethod
    def count_tenant_resources(self, *, tenant_key: str) -> TakeoverResourceCounts:
        """How many plants, sites, runs, nutrient plans and tasks *tenant_key* holds."""

    @abstractmethod
    def earliest_active_person_key(self, *, excluding: str) -> str | None:
        """The key of the earliest-created active person account other than *excluding*, or ``None``.

        A person account is one whose ``account_type`` is not ``service`` (a missing value is a
        person, the model default). Ties on ``created_at`` are broken by the key.
        """
