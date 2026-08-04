"""REQ-033 tenant tools (§2.1). Reads the principal's own memberships."""

from __future__ import annotations

from app.common.enums import McpPermission
from app.core.permissions import list_mcp_permissions
from app.domain.models.mcp import McpToolResponse
from app.mcp_server.base import ToolBase, ToolInput, mcp_tool
from app.mcp_server.context import ToolContext


@mcp_tool(name="list_tenants", permission=McpPermission.READ)
class ListTenants(ToolBase):
    """List the gardens/tenants this API key may act in, with the role held in each."""

    class Input(ToolInput):
        pass

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        # Read straight off the principal: the authenticator already resolved the
        # account's active memberships, so this cannot show a tenant the caller
        # is not a member of.
        memberships = ctx.principal.memberships
        data = {
            "count": len(memberships),
            "items": [
                {
                    "slug": m.tenant_slug,
                    "name": m.tenant_name,
                    "role": m.role.value,
                    "mcp_permissions": [p.value for p in list_mcp_permissions(m.role)],
                }
                for m in memberships
            ],
        }
        if len(memberships) == 1:
            only = memberships[0]
            summary = f"This key acts in one tenant: '{only.tenant_slug}' (role {only.role.value})."
        else:
            slugs = ", ".join(m.tenant_slug for m in memberships)
            summary = (
                f"This key acts in {len(memberships)} tenants: {slugs}. Pass one as 'tenant' on tenant-scoped tools."
            )
        return self._response(summary=summary, data=data)
