"""REQ-033 MCP API-key authentication (§4.3).

MCP authenticates ``kp_`` API keys (REQ-023) — never an interactive session and
never a JWT access token. Two account types may hold such a key:

* a **personal account**: the user's own key, granting exactly the tenants that
  user is an active member of, with the user's own role in each;
* a **service account** (``account_type='service'``): the machine-to-machine
  path for Home Assistant, Grafana, CI and friends.

Both resolve to an :class:`McpPrincipal` carrying the account plus **every**
tenant membership it may act in. Which tenant a given call acts in is decided
later, per tool call, by the dispatcher — the role (and therefore the MCP
permission set, §4.4) differs per tenant.

An MCP key can therefore never reach data its owner could not reach through the
web UI: the membership list is the same one the REST API scopes on, and a
non-member tenant is reported as ``not_found`` rather than ``permission.denied``
so the interface leaks no tenant existence (§8.8 Szenario 6).

The raw key is hashed once and never stored, logged, or echoed (AC-S2).
"""

from __future__ import annotations

import hashlib
import ipaddress
from datetime import UTC, datetime

from app.common.exceptions import ForbiddenError, UnauthorizedError
from app.domain.interfaces.api_key_repository import IApiKeyRepository
from app.domain.interfaces.user_repository import IUserRepository
from app.domain.models.auth import ApiKey
from app.domain.services.tenant_service import TenantService
from app.mcp_server.principal import McpPrincipal, McpTenantMembership
from app.mcp_server.rate_limit import McpRateLimiter

_API_KEY_PREFIX = "kp_"


class McpAuthenticator:
    """Resolve a personal or service-account API key to an :class:`McpPrincipal`."""

    def __init__(
        self,
        api_key_repo: IApiKeyRepository,
        user_repo: IUserRepository,
        tenant_service: TenantService,
        rate_limiter: McpRateLimiter | None = None,
    ) -> None:
        self._api_key_repo = api_key_repo
        self._user_repo = user_repo
        self._tenant_service = tenant_service
        self._rate_limiter = rate_limiter

    def authenticate(
        self,
        raw_key: str | None,
        *,
        client_ip: str | None = None,
        service_accounts_only: bool = False,
        mask_non_service: bool = False,
    ) -> McpPrincipal:
        """Resolve a raw API key to an authenticated principal.

        Accepts a personal account's key as well as a service account's. The
        principal carries every tenant the account is an active member of; the
        acting tenant is chosen per tool call (§4.3).

        Args:
            raw_key: The raw ``kp_...`` API key (hashed once, never stored/logged).
            client_ip: The resolved client IP (from the trusted proxy). Enforced
                against the key's ``ip_allowlist`` when that control is set
                (SEC-004).
            service_accounts_only: Restrict to ``account_type='service'``. Used by
                the M2M validation endpoint (§5), which exists specifically to
                resolve *service* accounts; the MCP transport itself leaves this
                off so a user's own key works.
            mask_non_service: Only meaningful together with
                ``service_accounts_only``. When ``True`` a *valid but non-service*
                key is rejected with the SAME generic 401 as an invalid/revoked
                key, instead of a distinguishable 403 (SEC-003) — so an
                unauthenticated caller cannot use the endpoint as an oracle to
                prove a valid non-service key exists.
        """
        if not raw_key or not raw_key.startswith(_API_KEY_PREFIX):
            raise UnauthorizedError("Missing or malformed MCP API key.")

        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        api_key = self._api_key_repo.get_by_hash(key_hash)
        if api_key is None or api_key.revoked:
            raise UnauthorizedError("Invalid or revoked API key.")
        if api_key.expires_at and api_key.expires_at < datetime.now(UTC):
            raise UnauthorizedError("API key has expired.")

        # SEC-004: enforce the key's IP allowlist before doing any further
        # account resolution — a key used from an unlisted network is rejected
        # as if it did not authenticate (no oracle).
        self._enforce_ip_allowlist(api_key, client_ip)

        user = self._user_repo.get_by_key(api_key.user_key)
        if user is None or not user.is_active:
            raise UnauthorizedError("Account not found or inactive.")
        is_service = user.account_type == "service"
        if service_accounts_only and not is_service:
            if mask_non_service:
                # SEC-003: collapse into the generic invalid-key 401 so the
                # endpoint never reveals that a valid non-service key exists.
                raise UnauthorizedError("Invalid or revoked API key.")
            raise ForbiddenError("This endpoint accepts service-account API keys only.")

        # SEC-004: enforce the per-key rate limit (429 on breach, fail-closed).
        self._enforce_rate_limit(api_key)

        memberships = self._resolve_memberships(user.key or "", api_key.tenant_scope)

        if api_key.key:
            self._api_key_repo.update_last_used(api_key.key)

        return McpPrincipal(
            account_key=user.key or "",
            display_name=user.display_name,
            is_service_account=is_service,
            memberships=memberships,
        )

    def _enforce_ip_allowlist(self, api_key: ApiKey, client_ip: str | None) -> None:
        """Reject the call when the client IP is not on the key's allowlist (SEC-004).

        An empty/absent allowlist means "allow all" (the default). A configured
        allowlist fails **closed**: an unresolvable client IP, an unparsable
        allowlist entry, or a non-matching IP all reject with a generic 401 —
        never a distinguishable 403 — so the control cannot be probed.
        """
        allowlist = api_key.ip_allowlist or []
        if not allowlist:
            return
        if not client_ip:
            raise UnauthorizedError("Client IP could not be resolved for an IP-restricted API key.")
        try:
            addr = ipaddress.ip_address(client_ip)
        except ValueError as exc:
            raise UnauthorizedError("Client IP could not be resolved for an IP-restricted API key.") from exc
        for entry in allowlist:
            try:
                network = ipaddress.ip_network(entry, strict=False)
            except ValueError:
                # A malformed allowlist entry never silently widens access.
                continue
            if addr in network:
                return
        raise UnauthorizedError("Client IP is not permitted for this API key.")

    def _enforce_rate_limit(self, api_key: ApiKey) -> None:
        """Enforce the key's ``rate_limit_per_minute`` control (SEC-004, 429)."""
        limit = api_key.rate_limit_per_minute
        if not limit or self._rate_limiter is None:
            return
        self._rate_limiter.check_and_increment(api_key_key=api_key.key or "", limit=limit)

    def _resolve_memberships(self, user_key: str, tenant_scope: str | None) -> tuple[McpTenantMembership, ...]:
        """Resolve every tenant the account may act in (§1 tenant isolation).

        The list comes from :meth:`TenantService.list_my_tenants`, the same
        source the REST API scopes on — an MCP key therefore reaches exactly the
        tenants its owner reaches in the web UI, never more. Inactive
        memberships and inactive tenants are already filtered out there.

        A key carrying ``tenant_scope`` narrows this further to that single
        tenant, so a user who wants a one-tenant token can still issue one. A
        scope that matches no accessible tenant yields *no* memberships rather
        than a distinguishable error: the caller must not learn whether the
        named tenant exists but is foreign, or does not exist at all.
        """

        tenants = self._tenant_service.list_my_tenants(user_key)
        if tenant_scope:
            tenants = [t for t in tenants if t.slug == tenant_scope or t.key == tenant_scope]
        if not tenants:
            raise ForbiddenError("This account is not an active member of any tenant.")

        return tuple(
            McpTenantMembership(
                tenant_key=t.key,
                tenant_slug=t.slug,
                tenant_name=t.name,
                role=t.role,
            )
            for t in tenants
        )
