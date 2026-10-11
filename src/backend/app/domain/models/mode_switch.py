"""The light-to-full upgrade of a Kamerplanter installation (REQ-027 §7a, #1855).

A light-mode installation runs as one seeded system account (``system-user``) in one
seeded tenant (``system-tenant``), without authentication. When the operator switches
``KAMERPLANTER_MODE`` to ``full``, the start seals that account (it can no longer be
signed into or reached with a key minted in light mode) and records a *pending
take-over*: the first account of the full-mode instance decides whether the light-mode
data become its own.

Source code is English only (NFR-003).
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

#: The deterministic keys the light-mode seed writes (``app/migrations/seed_data/light_mode.yaml``);
#: ``LightAuthProvider`` resolves every light-mode request to this account.
SYSTEM_USER_KEY = "system-user"
SYSTEM_TENANT_KEY = "system-tenant"

DeploymentMode = Literal["light", "full"]

#: How long a claim on the pending take-over holds before another decision may take it over (#1855
#: SEC-004). A decision runs a handful of writes; a claim this old belongs to a process that died.
TAKEOVER_CLAIM_TTL_SECONDS = 600
#: The share of the TTL a decision may spend writing (#1855 R2-003): past it the decision stops and undoes
#: its writes while it still holds the claim, so no second decision claims a document one is still writing.
TAKEOVER_DECISION_DEADLINE_SHARE = 0.5


def system_account_refused(user_key: str | None, *, mode: str) -> bool:
    """Whether an authentication resolving to *user_key* must be refused in *mode* (#1855 SEC-006).

    In ``full`` mode the light-mode system account never authenticates - whatever the database says
    about it. The start seals it (``ModeSwitchService.seal_system_account``); this is the second gate,
    independent of the stored state, for a replica that served before the seal, a restored backup or
    a mixed light/full rollout.
    """
    return mode == "full" and user_key == SYSTEM_USER_KEY


class TakeoverReceipt(BaseModel):
    """What one take-over decision wrote, so a failing decision can undo exactly that (#1855 SEC-004, R2-001).

    Built *before* the first write and filled in by :class:`~app.domain.services.tenant_service.TenantService`
    as each write happens (the caller passes it in), so a write that fails midway still leaves the caller a
    record of every write before it. :meth:`TenantService.undo_light_mode_takeover` clears each entry once it
    is undone, so a partly undone receipt names only what is left. Stored in the pending take-over only when
    an undo failed (``needs_attention``, R2-002); otherwise in memory for one decision.
    """

    tenant_key: str
    system_user_key: str
    #: The deciding account - in memory only, never stored (``exclude``, #1855 R3 W-3): it resolves a
    #: membership whose insert was intended but not confirmed (W-1). The undo's audit rows name the actor
    #: of the decision that runs the undo, not this field.
    new_owner_key: str | None = Field(default=None, exclude=True)
    #: The tenant's slug, owner and name before the take-over (read before any write).
    tenant_slug: str | None = None
    previous_owner_key: str | None = None
    previous_name: str | None = None
    #: ``True`` once the tenant's owner/name write was attempted: undo restores the previous values.
    tenant_changed: bool = False
    #: The system account's membership the take-over ends (recorded before the write).
    ended_system_membership_key: str | None = None
    #: Set *before* the insert of the new owner's ``lead`` membership (#1855 R3 W-1): a check after the insert
    #: may fail before its key is known; the undo then looks the membership up by account and tenant.
    lead_membership_intended: bool = False
    #: The new owner's membership the take-over created (``None``: none, or an existing one was raised).
    created_membership_key: str | None = None
    #: An existing membership of the new owner the take-over raised, with its previous values.
    raised_membership_key: str | None = None
    raised_previous_role: str | None = None
    raised_previous_scopes: list[str] | None = None
    raised_previous_active: bool | None = None
    #: The ``platform`` membership the first-admin grant created, or an existing one it raised (with its
    #: previous values). The platform tenant the grant may create is not undone: the grant finds it by
    #: slug next time, and without a membership it makes nobody an administrator.
    #: Set before the insert of the ``platform`` membership (W-1), like ``lead_membership_intended``.
    platform_membership_intended: bool = False
    platform_created_membership_key: str | None = None
    platform_raised_membership_key: str | None = None
    platform_raised_previous_role: str | None = None
    platform_raised_previous_scopes: list[str] | None = None
    platform_raised_previous_active: bool | None = None

    def has_writes(self) -> bool:
        """Whether anything is left to undo."""
        return bool(
            self.tenant_changed
            or self.lead_membership_intended
            or self.platform_membership_intended
            or self.ended_system_membership_key
            or self.created_membership_key
            or self.raised_membership_key
            or self.platform_created_membership_key
            or self.platform_raised_membership_key
        )


class TakeoverClaimLostError(Exception):
    """An undo found its decision's claim on the take-over gone before a step (#1855 R3 W-2).

    Raised by ``TenantService.undo_light_mode_takeover`` instead of writing: another decision may own the
    tenant now. The receipt then holds what was not undone.
    """


class PendingTakeover(BaseModel):
    """An open take-over of the light-mode tenant, written when the start detected light → full.

    ``claim_id`` / ``claimed_at`` mark a decision in progress (#1855 SEC-004): the document is
    removed only after the decision succeeded; a claim older than :data:`TAKEOVER_CLAIM_TTL_SECONDS`
    may be taken over. ``needs_attention`` with ``receipt`` (R2-002): a decision failed and so did the
    undo of its writes; the next decision that claims the document runs that undo first and decides
    only once it succeeded.
    """

    system_tenant_key: str = SYSTEM_TENANT_KEY
    created_at: datetime
    claim_id: str | None = None
    claimed_at: datetime | None = None
    needs_attention: bool = False
    receipt: TakeoverReceipt | None = None


class SystemAccountSealing(BaseModel):
    """What sealing the light-mode system account on a full-mode start changed (all zero: nothing to do)."""

    deactivated: bool = False
    api_keys_revoked: int = 0
    sessions_revoked: int = 0
    calendar_feeds_deleted: int = 0


class ModeSwitchOutcome(BaseModel):
    """What one start's reconciliation of the deployment mode found and did."""

    current_mode: DeploymentMode
    previous_mode: DeploymentMode | None = None
    #: ``True`` when the stored mode was absent and the previous mode was inferred from the data.
    previous_mode_inferred: bool = False
    sealing: SystemAccountSealing = Field(default_factory=SystemAccountSealing)
    pending_takeover_recorded: bool = False
    system_account_restored: bool = False


class TakeoverResourceCounts(BaseModel):
    """How much the light-mode tenant holds, shown in the take-over dialog (REQ-027 §7a.4)."""

    plants: int = 0
    sites: int = 0
    planting_runs: int = 0
    nutrient_plans: int = 0
    tasks: int = 0


class TakeoverStatus(BaseModel):
    """Whether a take-over is open and whether the asking account may decide it."""

    pending: bool
    #: Only an eligible account sees the tenant and its counts; the others only learn that one is open.
    eligible: bool = False
    #: The key a step-up factor for the decision is bound to (``light_mode_takeover``, #1855 SEC-003).
    tenant_key: str | None = None
    tenant_name: str | None = None
    tenant_slug: str | None = None
    resource_counts: TakeoverResourceCounts | None = None


class TakeoverResult(BaseModel):
    """The decided take-over."""

    accepted: bool
    #: The slug of the tenant the account took over; ``None`` when it declined.
    tenant_slug: str | None = None
    #: Whether the decision made the account the instance's first platform administrator.
    platform_admin_granted: bool = False
