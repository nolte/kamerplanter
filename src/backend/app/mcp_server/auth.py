"""REQ-033 MCP service-account authentication (§4.3).

MCP is a machine-to-machine interface: it authenticates **only** service-account
API keys (REQ-023 v1.10), never interactive sessions. The authenticator resolves
a raw key to an :class:`McpPrincipal` — service account + bound tenant + role —
or raises :class:`UnauthorizedError`/:class:`ForbiddenError`.

The raw key is hashed once and never stored, logged, or echoed (AC-S2).
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from app.common.exceptions import ForbiddenError, UnauthorizedError
from app.domain.interfaces.api_key_repository import IApiKeyRepository
from app.domain.interfaces.user_repository import IUserRepository
from app.domain.services.tenant_service import TenantService
from app.mcp_server.principal import McpPrincipal

_API_KEY_PREFIX = "kp_"


class McpAuthenticator:
    """Resolve a service-account API key to an :class:`McpPrincipal`."""

    def __init__(
        self,
        api_key_repo: IApiKeyRepository,
        user_repo: IUserRepository,
        tenant_service: TenantService,
    ) -> None:
        self._api_key_repo = api_key_repo
        self._user_repo = user_repo
        self._tenant_service = tenant_service

    def authenticate(self, raw_key: str | None) -> McpPrincipal:
        if not raw_key or not raw_key.startswith(_API_KEY_PREFIX):
            raise UnauthorizedError("Missing or malformed MCP service-account API key.")

        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        api_key = self._api_key_repo.get_by_hash(key_hash)
        if api_key is None or api_key.revoked:
            raise UnauthorizedError("Invalid or revoked API key.")
        if api_key.expires_at and api_key.expires_at < datetime.now(UTC):
            raise UnauthorizedError("API key has expired.")

        user = self._user_repo.get_by_key(api_key.user_key)
        if user is None or not user.is_active:
            raise UnauthorizedError("Service account not found or inactive.")
        if user.account_type != "service":
            # MCP accepts service accounts only (REQ-033 §1 grundprinzipien).
            raise ForbiddenError("The MCP interface accepts service-account API keys only.")

        tenant_slug, tenant_key, role = self._resolve_tenant(user.key or "", api_key.tenant_scope)

        if api_key.key:
            self._api_key_repo.update_last_used(api_key.key)

        return McpPrincipal(
            service_account_key=user.key or "",
            display_name=user.display_name,
            tenant_key=tenant_key,
            tenant_slug=tenant_slug,
            role=role,
        )

    def _resolve_tenant(self, user_key: str, tenant_scope: str | None):
        """Bind the service account to exactly one tenant (§1 tenant isolation)."""

        tenants = self._tenant_service.list_my_tenants(user_key)
        if not tenants:
            raise ForbiddenError("Service account is not a member of any tenant.")

        if tenant_scope:
            match = next(
                (t for t in tenants if t.slug == tenant_scope or t.key == tenant_scope),
                None,
            )
            if match is None:
                raise ForbiddenError("API key tenant scope does not match any accessible tenant.")
            return match.slug, match.key, match.role

        if len(tenants) != 1:
            # An MCP client must be bound to exactly one tenant; require the key
            # to carry a tenant_scope when the account spans several tenants.
            raise ForbiddenError("Service account spans multiple tenants — issue a tenant-scoped API key for MCP.")
        only = tenants[0]
        return only.slug, only.key, only.role
