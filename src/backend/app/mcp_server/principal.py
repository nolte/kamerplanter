"""REQ-033 MCP authenticated principal (§4.3).

A resolved MCP caller: the service account (a ``User`` with
``account_type='service'``), the single tenant it is bound to, and the tenant
role that decides its MCP permissions (§4.4).
"""

from __future__ import annotations

from pydantic import BaseModel

from app.common.enums import TenantRole


class McpPrincipal(BaseModel):
    """The identity behind a single MCP request.

    ``service_account_key`` is the service account's user ``_key`` and is what
    the audit log and idempotency store scope on (§3). It is never the raw API
    key — the raw key never leaves the authenticator (AC-S2).
    """

    service_account_key: str
    display_name: str
    tenant_key: str
    tenant_slug: str
    role: TenantRole

    model_config = {"frozen": True}
