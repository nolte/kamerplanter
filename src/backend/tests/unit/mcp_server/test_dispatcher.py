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
from app.mcp_server.base import TenantToolInput, ToolBase, ToolInput, WriteToolBase, WriteToolInput, mcp_tool
from app.mcp_server.dispatcher import ToolDispatcher
from app.mcp_server.idempotency import IdempotencyStore
from app.mcp_server.principal import McpPrincipal, McpTenantMembership
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


def _membership(slug: str = "home", role: TenantRole = TenantRole.LEAD) -> McpTenantMembership:
    return McpTenantMembership(tenant_key=slug, tenant_slug=slug, tenant_name=slug.title(), role=role)


def _principal(role: TenantRole = TenantRole.LEAD, *, slugs: tuple[str, ...] = ("home",)) -> McpPrincipal:
    return McpPrincipal(
        account_key="sa-1",
        display_name="bot",
        is_service_account=True,
        memberships=tuple(_membership(slug, role) for slug in slugs),
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

    # One key, two tenants: the same idempotency key must not bleed across them.
    principal = _principal(TenantRole.GROWER, slugs=("home", "garden"))

    first = await dispatcher.dispatch(principal, "counter_write", {**args, "tenant": "home"})
    writes_after_a = registry.get("counter_write").writes  # type: ignore[attr-defined]
    second = await dispatcher.dispatch(principal, "counter_write", {**args, "tenant": "garden"})
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


# ── Tenant binding: a key reaches only its owner's tenants (§4.3) ──────────────
@pytest.mark.asyncio
async def test_foreign_tenant_is_not_found_not_permission_denied():
    # §8.8 Szenario 6: naming a tenant the caller is not a member of must be
    # indistinguishable from naming one that does not exist, so the interface
    # cannot be walked to enumerate other users' gardens.
    dispatcher, audit_repo, _, _ = _dispatcher()
    with pytest.raises(NotFoundError):
        await dispatcher.dispatch(
            _principal(TenantRole.LEAD, slugs=("home",)),
            "counter_write",
            {"label": "x", "tenant": "someone-elses-garden"},
        )
    assert audit_repo.entries[-1].error_class == "not_found"


@pytest.mark.asyncio
async def test_permission_is_evaluated_per_tenant_not_per_key():
    # The heart of the multi-tenant model: one key, admin in the user's own
    # garden and viewer in a community garden. The write must succeed in the
    # first and be refused in the second — evaluating the key's "strongest" role
    # globally would silently grant write access to the community garden.
    registry = _build_registry()
    dispatcher = ToolDispatcher(registry, MCPAuditLogger(_FakeAuditRepo()), IdempotencyStore(_FakeIdempotencyRepo()))
    principal = McpPrincipal(
        account_key="u-1",
        display_name="Gardener",
        memberships=(
            _membership("home", TenantRole.LEAD),
            _membership("community", TenantRole.VIEWER),
        ),
    )

    ok = await dispatcher.dispatch(principal, "counter_write", {"label": "mine", "tenant": "home"})
    assert ok.summary == "wrote"

    with pytest.raises(ForbiddenError):
        await dispatcher.dispatch(principal, "counter_write", {"label": "theirs", "tenant": "community"})


@pytest.mark.asyncio
async def test_ambiguous_tenant_must_be_named():
    # With several memberships and no 'tenant' argument the call is rejected
    # rather than silently acting in an arbitrary tenant.
    dispatcher, _, _, _ = _dispatcher()
    principal = _principal(TenantRole.GROWER, slugs=("home", "garden"))
    with pytest.raises(ValidationError):
        await dispatcher.dispatch(principal, "counter_write", {"label": "x"})


@pytest.mark.asyncio
async def test_tenant_is_taken_from_the_membership_not_the_arguments():
    # The tool sees the resolved membership, never the raw caller-supplied
    # string, so it cannot be tricked into writing outside the bound tenant.
    registry = ToolRegistry()
    seen: dict = {}

    class _Probe(ToolBase):
        tool_name = "probe_tenant"
        permission = McpPermission.READ

        class Input(TenantToolInput):
            pass

        async def run(self, ctx, args):
            seen["tenant_key"] = ctx.tenant_key
            seen["role"] = ctx.role
            return McpToolResponse(summary="ok")

    registry.register(_Probe())
    dispatcher = ToolDispatcher(registry, MCPAuditLogger(_FakeAuditRepo()), IdempotencyStore(_FakeIdempotencyRepo()))
    principal = McpPrincipal(
        account_key="u-1",
        display_name="Gardener",
        memberships=(_membership("home", TenantRole.LEAD), _membership("community", TenantRole.VIEWER)),
    )

    await dispatcher.dispatch(principal, "probe_tenant", {"tenant": "community"})
    assert seen == {"tenant_key": "community", "role": TenantRole.VIEWER}


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


def test_no_global_tool_uses_a_tenant_bound_link():
    """A tenant-agnostic tool must not reach for ctx.api_link / ctx.ui_link.

    Those helpers resolve through the bound membership, which the dispatcher
    leaves as None for a global tool — so the call raises RuntimeError and the
    tool dies on the real dispatch path while unit tests that build a
    ToolContext with a membership by hand keep passing. Five IPM tools shipped
    exactly that way; this check is the cheap guard against a repeat.
    """

    import inspect

    from app.mcp_server.registry import load_tools

    offenders = []
    for name in load_tools().names():
        tool = load_tools().get(name)
        if tool.tenant_scoped:  # type: ignore[attr-defined]
            continue
        source = inspect.getsource(type(tool))
        if "ctx.api_link" in source or "ctx.ui_link" in source:
            offenders.append(name)

    assert not offenders, f"Global tools using a tenant-bound link helper (use ctx.global_link): {offenders}"
