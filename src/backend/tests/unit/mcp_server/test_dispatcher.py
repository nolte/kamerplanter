"""REQ-033 dispatcher tests — permission binding, audit, idempotency, dry-run.

Covers AC-2 (permission.denied), AC-18 (dry-run writes nothing), AC-19
(idempotent replay), AC-S5 (hash-only audit) and the not-found path — all with
in-memory fakes so no ArangoDB is required.
"""

from __future__ import annotations

import pytest

from app.common.enums import McpPermission, McpToolStatus, TenantRole
from app.common.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.domain.models.mcp import McpToolResponse
from app.mcp_server.audit import MCPAuditLogger
from app.mcp_server.base import ToolBase, ToolInput, WriteToolBase, WriteToolInput, mcp_tool
from app.mcp_server.dispatcher import ToolDispatcher
from app.mcp_server.idempotency import IdempotencyStore
from app.mcp_server.principal import McpPrincipal
from app.mcp_server.registry import ToolRegistry


# ── Fakes ─────────────────────────────────────────────────────────────────────
class _FakeAuditRepo:
    def __init__(self) -> None:
        self.entries: list = []

    def record(self, entry) -> str:
        self.entries.append(entry)
        return "audit-1"


class _FakeIdempotencyRepo:
    def __init__(self) -> None:
        self.records: dict = {}

    def get(self, sa_key, tenant_key, tool_name, idem_key):
        # SEC-005: the scope includes tenant_key so two tenants never cross-replay.
        return self.records.get((sa_key, tenant_key, tool_name, idem_key))

    def store(self, record, *, ttl_hours=24):
        self.records[(record.service_account_key, record.tenant_key, record.tool_name, record.idempotency_key)] = record
        return record


# ── Tools under test (registered into an isolated registry) ────────────────────
def _build_registry() -> ToolRegistry:
    registry = ToolRegistry()

    class _EchoRead(ToolBase):
        tool_name = "echo_read"
        permission = McpPermission.READ

        class Input(ToolInput):
            value: str = "x"

        async def run(self, ctx, args):
            return McpToolResponse(summary=f"read {args.value}", data={"value": args.value})

    class _CounterWrite(WriteToolBase):
        tool_name = "counter_write"
        permission = McpPermission.WRITE
        writes = 0

        class Input(WriteToolInput):
            label: str = "a"

        async def preview(self, ctx, args):
            return McpToolResponse(summary="would write", data={"label": args.label})

        async def execute(self, ctx, args):
            type(self).writes += 1
            return McpToolResponse(summary="wrote", data={"label": args.label, "id": type(self).writes})

    registry.register(_EchoRead())
    registry.register(_CounterWrite())
    return registry


def _principal(role: TenantRole = TenantRole.LEAD) -> McpPrincipal:
    return McpPrincipal(
        service_account_key="sa-1",
        display_name="bot",
        tenant_key="home",
        tenant_slug="home",
        role=role,
    )


def _dispatcher():
    registry = _build_registry()
    audit_repo = _FakeAuditRepo()
    idem_repo = _FakeIdempotencyRepo()
    dispatcher = ToolDispatcher(
        registry,
        MCPAuditLogger(audit_repo),
        IdempotencyStore(idem_repo),
    )
    return dispatcher, audit_repo, idem_repo, registry


@pytest.mark.asyncio
async def test_read_tool_ok_is_audited_with_hash_only():
    dispatcher, audit_repo, _, _ = _dispatcher()
    resp = await dispatcher.dispatch(_principal(TenantRole.VIEWER), "echo_read", {"value": "hi"})
    assert resp.summary == "read hi"
    assert len(audit_repo.entries) == 1
    entry = audit_repo.entries[0]
    assert entry.status == McpToolStatus.OK
    # AC-S5: only a sha256 hash, never the plaintext argument.
    assert entry.input_hash and "hi" not in entry.input_hash
    assert len(entry.input_hash) == 64


@pytest.mark.asyncio
async def test_permission_denied_for_wrong_role_and_audited():
    dispatcher, audit_repo, _, _ = _dispatcher()
    # A viewer may not invoke a write tool (mcp.write) → 403 permission.denied.
    with pytest.raises(ForbiddenError):
        await dispatcher.dispatch(_principal(TenantRole.VIEWER), "counter_write", {"label": "x"})
    assert audit_repo.entries[-1].status == McpToolStatus.DENIED
    assert audit_repo.entries[-1].error_class == "permission.denied"


@pytest.mark.asyncio
async def test_grower_may_write():
    dispatcher, _, _, _ = _dispatcher()
    resp = await dispatcher.dispatch(_principal(TenantRole.GROWER), "counter_write", {"label": "y"})
    assert resp.summary == "wrote"
    assert resp.dry_run is False


@pytest.mark.asyncio
async def test_dry_run_does_not_execute():
    dispatcher, audit_repo, _, registry = _dispatcher()
    before = registry.get("counter_write").writes  # type: ignore[attr-defined]
    resp = await dispatcher.dispatch(_principal(), "counter_write", {"label": "z", "dry_run": True})
    after = registry.get("counter_write").writes  # type: ignore[attr-defined]
    assert resp.dry_run is True
    assert after == before  # AC-18: no write happened
    assert audit_repo.entries[-1].status == McpToolStatus.DRY_RUN


@pytest.mark.asyncio
async def test_idempotent_replay_writes_once():
    dispatcher, _, idem_repo, registry = _dispatcher()
    args = {"label": "once", "idempotency_key": "k-1"}
    first = await dispatcher.dispatch(_principal(), "counter_write", args)
    writes_after_first = registry.get("counter_write").writes  # type: ignore[attr-defined]
    second = await dispatcher.dispatch(_principal(), "counter_write", args)
    writes_after_second = registry.get("counter_write").writes  # type: ignore[attr-defined]

    assert first.idempotent_replay is False
    assert second.idempotent_replay is True  # AC-19: replay, not a new write
    assert writes_after_second == writes_after_first
    assert first.data["id"] == second.data["id"]


@pytest.mark.asyncio
async def test_idempotency_is_tenant_scoped_no_cross_tenant_replay():
    # SEC-005: a multi-tenant service account holding two tenant-scoped keys must
    # never replay tenant-A's stored result for a tenant-B call — the same
    # idempotency key under a different tenant is a *distinct* write.
    dispatcher, _, _, registry = _dispatcher()
    args = {"label": "shared", "idempotency_key": "dup-key"}

    tenant_a = McpPrincipal(
        service_account_key="sa-1", display_name="bot", tenant_key="home", tenant_slug="home", role=TenantRole.GROWER
    )
    tenant_b = McpPrincipal(
        service_account_key="sa-1",
        display_name="bot",
        tenant_key="garden",
        tenant_slug="garden",
        role=TenantRole.GROWER,
    )

    first = await dispatcher.dispatch(tenant_a, "counter_write", args)
    writes_after_a = registry.get("counter_write").writes  # type: ignore[attr-defined]
    second = await dispatcher.dispatch(tenant_b, "counter_write", args)
    writes_after_b = registry.get("counter_write").writes  # type: ignore[attr-defined]

    assert first.idempotent_replay is False
    assert second.idempotent_replay is False  # NOT a replay — different tenant
    assert writes_after_b == writes_after_a + 1  # tenant-B produced its own write
    assert first.data["id"] != second.data["id"]


@pytest.mark.asyncio
async def test_unknown_tool_raises_not_found():
    dispatcher, _, _, _ = _dispatcher()
    with pytest.raises(NotFoundError):
        await dispatcher.dispatch(_principal(), "does_not_exist", {})


@pytest.mark.asyncio
async def test_invalid_arguments_raise_validation_error_and_audit():
    dispatcher, audit_repo, _, _ = _dispatcher()
    with pytest.raises(ValidationError):
        await dispatcher.dispatch(_principal(), "echo_read", {"unknown_field": 1})
    assert audit_repo.entries[-1].status == McpToolStatus.ERROR
    assert audit_repo.entries[-1].error_class == "validation.input"


def test_mcp_tool_decorator_registers_into_global_registry():
    from app.mcp_server.registry import registry as global_registry

    @mcp_tool(name="unit_probe_tool", permission=McpPermission.READ)
    class _Probe(ToolBase):
        class Input(ToolInput):
            pass

        async def run(self, ctx, args):
            return McpToolResponse(summary="ok")

    assert "unit_probe_tool" in global_registry.names()
    assert not _Probe().write


def test_write_tool_with_read_permission_fails_registration():
    # SEC-006: a mutating tool declared under mcp.read is a silent privilege
    # downgrade — registration must fail fast at import time.
    with pytest.raises(TypeError, match="write tool"):

        @mcp_tool(name="sec006_bad_write_read", permission=McpPermission.READ)
        class _BadWrite(WriteToolBase):
            class Input(WriteToolInput):
                pass

            async def preview(self, ctx, args):
                return McpToolResponse(summary="would write")

            async def execute(self, ctx, args):  # pragma: no cover - never registered
                return McpToolResponse(summary="wrote")


def test_destructive_tool_requires_setup_permission():
    # SEC-006 / AC-S6: a destructive tool must be gated behind admin-only mcp.setup.
    with pytest.raises(TypeError, match="destructive"):

        @mcp_tool(name="sec006_bad_destructive", permission=McpPermission.WRITE, destructive=True)
        class _BadDestructive(WriteToolBase):
            class Input(WriteToolInput):
                pass

            async def preview(self, ctx, args):
                return McpToolResponse(summary="would destroy")

            async def execute(self, ctx, args):  # pragma: no cover - never registered
                return McpToolResponse(summary="destroyed")
