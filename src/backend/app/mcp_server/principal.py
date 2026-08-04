"""REQ-033 MCP authenticated principal (§4.3).

A resolved MCP caller: the account behind the API key (a personal user account
or an ``account_type='service'`` service account), every tenant that account may
act in, and the tenant role per tenant — the role decides its MCP permissions
(§4.4) and differs *per tenant*, so it is resolved per call, not per connection.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.common.enums import TenantRole


class McpTenantMembership(BaseModel):
    """One tenant the principal may act in, with the role it holds there."""

    tenant_key: str
    tenant_slug: str
    tenant_name: str
    role: TenantRole

    model_config = {"frozen": True}


class McpPrincipal(BaseModel):
    """The identity behind a single MCP request.

    ``account_key`` is the account's user ``_key`` and is what the audit log and
    the idempotency store scope on (§3). It is never the raw API key — the raw
    key never leaves the authenticator (AC-S2).

    A principal carries **every** tenant the account is an active member of. The
    acting tenant is chosen per tool call and resolved by the dispatcher through
    :meth:`membership_for`, which is the single place that binds a request to a
    tenant. A tenant the account is not a member of is indistinguishable from a
    tenant that does not exist (§8.8 Szenario 6) — the caller never learns which.
    """

    account_key: str
    display_name: str
    is_service_account: bool = False
    memberships: tuple[McpTenantMembership, ...] = Field(default_factory=tuple)

    model_config = {"frozen": True}

    @property
    def single_membership(self) -> McpTenantMembership | None:
        """The only membership, or ``None`` when the principal spans several."""

        return self.memberships[0] if len(self.memberships) == 1 else None

    def membership_for(self, tenant: str | None) -> McpTenantMembership | None:
        """Resolve ``tenant`` (slug or key) to a membership, else ``None``.

        With no ``tenant`` given, an unambiguous principal (exactly one
        membership) resolves to it; an ambiguous one resolves to ``None`` so the
        caller is forced to name the tenant rather than silently acting in an
        arbitrary one.
        """

        if tenant is None:
            return self.single_membership
        return next(
            (m for m in self.memberships if m.tenant_slug == tenant or m.tenant_key == tenant),
            None,
        )

    def roles(self) -> frozenset[TenantRole]:
        """Every role this principal holds anywhere (used for discovery, §1.2)."""

        return frozenset(m.role for m in self.memberships)
