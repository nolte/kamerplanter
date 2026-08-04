"""REQ-033 MCP idempotency store (§2.6, §3).

Wraps :class:`ArangoMcpIdempotencyRepository` to give write tools safe LLM-retry
semantics: a repeated call with the same ``idempotency_key`` (scoped to the
service account + tool) within the TTL replays the original result instead of
writing twice (AC-19).
"""

from __future__ import annotations

from app.domain.models.mcp import McpIdempotencyRecord, McpToolResponse
from app.mcp_server.principal import McpPrincipal, McpTenantMembership


class IdempotencyStore:
    """Look up / persist idempotency records for MCP write tools."""

    def __init__(self, repo, *, ttl_hours: int = 24) -> None:
        self._repo = repo
        self._ttl_hours = ttl_hours

    def lookup(
        self,
        principal: McpPrincipal,
        membership: McpTenantMembership | None,
        tool_name: str,
        idempotency_key: str,
    ) -> McpToolResponse | None:
        """Return the replayed response for a known key, else ``None``.

        SEC-005: the lookup is scoped by the *acting* tenant in addition to the
        account + tool. This matters more now that one key can act in several
        tenants: reusing an idempotency key across two tenants must produce two
        separate writes, never a replay of the other tenant's result.
        """

        record = self._repo.get(
            principal.account_key,
            membership.tenant_key if membership else "",
            tool_name,
            idempotency_key,
        )
        if record is None:
            return None
        response = McpToolResponse(**record.result_payload)
        response.idempotent_replay = True
        return response

    def store(
        self,
        principal: McpPrincipal,
        membership: McpTenantMembership | None,
        tool_name: str,
        idempotency_key: str,
        input_hash: str,
        response: McpToolResponse,
    ) -> None:
        record = McpIdempotencyRecord(
            service_account_key=principal.account_key,
            tenant_key=membership.tenant_key if membership else "",
            tool_name=tool_name,
            idempotency_key=idempotency_key,
            input_hash=input_hash,
            result_payload=response.to_payload(),
        )
        self._repo.store(record, ttl_hours=self._ttl_hours)
