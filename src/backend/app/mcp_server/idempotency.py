"""REQ-033 MCP idempotency store (§2.6, §3).

Wraps :class:`ArangoMcpIdempotencyRepository` to give write tools safe LLM-retry
semantics: a repeated call with the same ``idempotency_key`` (scoped to the
service account + tool) within the TTL replays the original result instead of
writing twice (AC-19).

Since MT-045.5 (#2144) a replay needs the *same* arguments: a key re-sent with
other arguments is ``conflict.idempotency_key_reused`` (409 on the REST alias),
never a silent replay of a different call; and a record past its ``expires_at``
is not replayed even when the hourly sweep has not removed it yet (#2150).
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain.models.mcp import McpIdempotencyRecord, McpToolResponse
from app.mcp_server.base import McpToolError
from app.mcp_server.principal import McpPrincipal, McpTenantMembership

#: REQ-033 §2.6 — the contract code for a key re-used with different arguments.
IDEMPOTENCY_KEY_REUSED = "conflict.idempotency_key_reused"


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
        input_hash: str,
        *,
        now: datetime | None = None,
    ) -> McpToolResponse | None:
        """Return the replayed response for a known, live key, else ``None``.

        SEC-005: the lookup is scoped by the *acting* tenant in addition to the
        account + tool. This matters more now that one key can act in several
        tenants: reusing an idempotency key across two tenants must produce two
        separate writes, never a replay of the other tenant's result.

        MT-045.5 (#2144): a record past its ``expires_at`` (or without a readable
        one) is no replay — the store overwrites it with the new call's result. A
        live record whose ``input_hash`` differs raises
        :data:`IDEMPOTENCY_KEY_REUSED`: the caller sent other arguments under a key
        it already spent, and replaying the first result would tell it a write
        happened that did not.
        """

        record = self._repo.get(
            principal.account_key,
            membership.tenant_key if membership else "",
            tool_name,
            idempotency_key,
        )
        if record is None or not _is_live(record, now or datetime.now(UTC)):
            return None
        if record.input_hash != input_hash:
            raise McpToolError(
                IDEMPOTENCY_KEY_REUSED,
                f"The idempotency key was already used for a call to '{tool_name}' with different arguments. "
                "Send a new key for a new call, or the original arguments to replay it.",
                details={"tool": tool_name, "idempotency_key": idempotency_key},
            )
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


def _is_live(record: McpIdempotencyRecord, now: datetime) -> bool:
    """Whether a record is still inside its TTL — compared as instants, a naive stamp read as UTC."""
    expires_at = record.expires_at
    if expires_at is None:
        return False
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    return expires_at > now
