"""#2103 — every MCP tool that writes tenant-independent data is a platform admin's, and listed here.

A tool without a ``tenant`` argument has no tenant role to bind to. The dispatcher once
admitted it on the strongest role the principal held anywhere, which for a write meant
``lead`` of the caller's own personal tenant — every account has one. The dispatcher now
admits a tenant-less tool that is not a plain read only for a platform admin, and discovery
hides it from everyone else.

**The rule, stated as a derivation.** The set of tenant-less non-read tools is read off the
registry. It must equal :data:`GLOBAL_WRITE_TOOLS`, so a *new* tool that writes shared data
fails here until somebody decides it belongs on the list — the decision "who may call this"
cannot be skipped by forgetting. Each listed tool is then run through the real dispatcher
and discovery as a non-admin (refused, hidden, audited ``DENIED``) and as an admin.
"""

from __future__ import annotations

import pytest

from app.common.enums import McpPermission, McpToolStatus, TenantRole
from app.common.exceptions import ForbiddenError
from app.mcp_server.audit import MCPAuditLogger
from app.mcp_server.base import GlobalWriteToolInput, ToolBase, WriteToolBase, WriteToolInput
from app.mcp_server.dispatcher import ToolDispatcher
from app.mcp_server.idempotency import IdempotencyStore
from app.mcp_server.principal import McpPrincipal, McpTenantMembership
from app.mcp_server.registry import ToolRegistry, load_tools

#: Tools that write data every tenant shares. Adding one is a decision about who may
#: call it: the dispatcher will admit it for a platform admin only.
GLOBAL_WRITE_TOOLS = frozenset({"assign_species_phase_sequence"})


def tenantless_non_read_tools(registry: ToolRegistry) -> set[str]:
    """Tools with no tenant argument that are anything other than a plain read."""
    found: set[str] = set()
    for name in registry.names():
        tool = registry.get(name)
        assert isinstance(tool, ToolBase)
        if not tool.tenant_scoped and (tool.permission != McpPermission.READ or tool.write):
            found.add(name)
    return found


class _Audit:
    def __init__(self) -> None:
        self.entries: list = []

    def record(self, entry) -> str:
        self.entries.append(entry)
        return "a"


class _Idem:
    def get(self, *args):
        return None

    def store(self, record, *, ttl_hours=24):
        return record


def _principal(*, admin: bool) -> McpPrincipal:
    member = McpTenantMembership(tenant_key="t1", tenant_slug="home", tenant_name="Home", role=TenantRole.LEAD)
    return McpPrincipal(account_key="u1", display_name="U", is_platform_admin=admin, memberships=(member,))


class TestTheListIsDerivedFromTheRegistry:
    def test_the_real_registry_has_exactly_the_declared_global_write_tools(self) -> None:
        assert tenantless_non_read_tools(load_tools()) == GLOBAL_WRITE_TOOLS, (
            "A tool without a tenant argument now writes (or a listed one stopped). "
            "Decide who may call it and update GLOBAL_WRITE_TOOLS: the dispatcher admits it for a platform admin only."
        )

    def test_the_derivation_sees_an_undeclared_global_write_tool(self) -> None:
        """Non-vacuity: a planted tenant-less write tool is found, a tenant-scoped one is not."""
        registry = ToolRegistry()

        # Declared by hand rather than through ``@mcp_tool``: the decorator registers into the
        # process-wide registry, and a planted tool must not outlive this test.
        class _Planted(WriteToolBase):
            tool_name = "planted_global_write"
            permission = McpPermission.SETUP

            class Input(GlobalWriteToolInput):
                pass

            async def preview(self, ctx, args):
                raise NotImplementedError

            async def execute(self, ctx, args):
                raise NotImplementedError

        class _Scoped(WriteToolBase):
            tool_name = "planted_tenant_write"
            permission = McpPermission.WRITE

            class Input(WriteToolInput):
                pass

            async def preview(self, ctx, args):
                raise NotImplementedError

            async def execute(self, ctx, args):
                raise NotImplementedError

        registry.register(_Planted())
        registry.register(_Scoped())
        assert tenantless_non_read_tools(registry) == {"planted_global_write"}


class TestEveryGlobalWriteToolIsAdminOnly:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("name", sorted(GLOBAL_WRITE_TOOLS))
    async def test_a_non_admin_is_refused_and_the_refusal_is_audited(self, name: str) -> None:
        audit = _Audit()
        dispatcher = ToolDispatcher(load_tools(), MCPAuditLogger(audit), IdempotencyStore(_Idem()))
        with pytest.raises(ForbiddenError):
            await dispatcher.dispatch(_principal(admin=False), name, {"species_key": "s", "sequence_key": "q"})
        assert audit.entries[-1].status == McpToolStatus.DENIED
        assert audit.entries[-1].error_class == "permission.denied"

    @pytest.mark.parametrize("name", sorted(GLOBAL_WRITE_TOOLS))
    def test_discovery_hides_it_from_a_non_admin_and_shows_it_to_an_admin(self, name: str) -> None:
        from app.api.v1.mcp.router import _visible_specs

        assert name not in {s["name"] for s in _visible_specs(_principal(admin=False))}
        assert name in {s["name"] for s in _visible_specs(_principal(admin=True))}
