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


class PendingTakeover(BaseModel):
    """An open take-over of the light-mode tenant, written when the start detected light → full."""

    system_tenant_key: str = SYSTEM_TENANT_KEY
    created_at: datetime


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
