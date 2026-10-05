"""Service accounts of a tenant (REQ-023 §5b, #2137 / MT-041).

A service account is a ``User`` with ``account_type == "service"``: no password, no
session, no personal tenant. It is created by a tenant's lead holding the
``technical`` scope, holds exactly one membership (``viewer`` or ``grower``) in that
tenant and authenticates only with API keys scoped to it. These are the read
projections the routes return; the account itself is the ``User`` document.

Source code is English only (NFR-003).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.common.enums import TenantRole
from app.domain.models.auth import ApiKeyCreated, ApiKeySummary

#: The roles a tenant's lead may give a service account (REQ-023 §5b.3: "maximal ``grower``" — a
#: machine identity never holds the irreversibility boundary of axis 1).
SERVICE_ACCOUNT_ROLES: frozenset[TenantRole] = frozenset({TenantRole.VIEWER, TenantRole.GROWER})

#: The domain every service-account address lives in. RFC 2606's documentation domain:
#: undeliverable, and accepted by ``EmailStr`` (which refuses ``.local`` — REQ-023 §5b.3's
#: ``{name}@service.{tenant}.local`` cannot be stored). The local part is random, so the
#: address names neither the tenant nor the integration.
SERVICE_ACCOUNT_EMAIL_DOMAIN = "service.example.com"

#: The longest overlap a rotation may give the previous keys (24 h).
MAX_ROTATION_OVERLAP_MINUTES = 1440


class ServiceAccountInfo(BaseModel):
    """One service account of a tenant, with the keys it holds there."""

    key: str
    display_name: str
    role: TenantRole
    membership_key: str
    joined_at: datetime | None = None
    api_keys: list[ApiKeySummary]


class ServiceAccountCreated(BaseModel):
    """A new service account and its first key — the raw key is shown this once."""

    key: str
    display_name: str
    role: TenantRole
    membership_key: str
    api_key: ApiKeyCreated


class ServiceAccountKeyRotated(BaseModel):
    """The key a rotation minted, and when the keys it replaced stop working."""

    api_key: ApiKeyCreated
    #: The end of the overlap window; ``None`` when the previous keys were revoked at once.
    previous_keys_end_at: datetime | None
    #: How many live keys the rotation revoked or gave an end.
    replaced_key_count: int
