"""REQ-033 MCP tool base classes + registration decorator (§4.2).

Tools are thin, typed wrappers over the existing domain services. A read tool
implements :meth:`ToolBase.run`; a write tool implements :meth:`WriteToolBase.preview`
(dry-run effect, no persistence) and :meth:`WriteToolBase.execute` (the real
write). Dry-run/idempotency orchestration lives in the dispatcher, so tools stay
focused on delegation.

Every tool declares exactly one MCP permission class (``mcp.read`` /
``mcp.write`` / ``mcp.setup``, §4.4) which the dispatcher enforces against the
caller's tenant role before the handler runs.
"""

from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel, Field

from app.common.enums import McpPermission
from app.domain.models.mcp import McpToolLink, McpToolResponse, McpToolSpec
from app.mcp_server.context import ToolContext


class ToolInput(BaseModel):
    """Base class for a tool's typed input arguments."""

    model_config = {"extra": "forbid"}


class WriteToolInput(ToolInput):
    """Input mixin for write tools — dry-run preview + idempotency (§2.6)."""

    dry_run: bool = Field(
        default=False,
        description="Return the planned effect without persisting anything.",
    )
    idempotency_key: str | None = Field(
        default=None,
        description="Repeating a call with the same key within 24h replays the original result.",
    )


class ToolBase:
    """Base class for every MCP tool.

    Subclasses set :attr:`tool_name`/:attr:`permission` via the :func:`mcp_tool`
    decorator, declare a nested ``Input`` model and implement :meth:`run`.
    """

    tool_name: ClassVar[str] = ""
    permission: ClassVar[McpPermission] = McpPermission.READ
    write: ClassVar[bool] = False
    destructive: ClassVar[bool] = False
    Input: ClassVar[type[ToolInput]] = ToolInput

    @property
    def description(self) -> str:
        return (self.__doc__ or "").strip().split("\n")[0]

    async def run(self, ctx: ToolContext, args: ToolInput) -> McpToolResponse:  # pragma: no cover - overridden
        raise NotImplementedError

    # ── helpers ──────────────────────────────────────────────────────────
    @staticmethod
    def _response(
        summary: str,
        data: dict | None = None,
        links: list[dict[str, str]] | None = None,
    ) -> McpToolResponse:
        return McpToolResponse(
            summary=summary,
            data=data or {},
            links=[McpToolLink(**link) for link in (links or [])],
        )

    def spec(self) -> McpToolSpec:
        return McpToolSpec(
            name=self.tool_name,
            description=self.description,
            permission=self.permission,
            write=self.write,
            destructive=self.destructive,
            input_schema=self.Input.model_json_schema(),
        )


class WriteToolBase(ToolBase):
    """Base class for mutating tools with dry-run + idempotency support (§2.6)."""

    write: ClassVar[bool] = True
    Input: ClassVar[type[WriteToolInput]] = WriteToolInput

    async def preview(self, ctx: ToolContext, args: WriteToolInput) -> McpToolResponse:  # pragma: no cover
        raise NotImplementedError

    async def execute(self, ctx: ToolContext, args: WriteToolInput) -> McpToolResponse:  # pragma: no cover
        raise NotImplementedError

    async def run(self, ctx: ToolContext, args: ToolInput) -> McpToolResponse:
        # The dispatcher normally calls preview()/execute() directly; run() keeps
        # the read-tool contract usable for a write tool in the non-dry-run path.
        return await self.execute(ctx, args)  # type: ignore[arg-type]


def mcp_tool(
    *,
    name: str,
    permission: McpPermission,
    destructive: bool = False,
):
    """Class decorator: bind metadata and register the tool instance (§4.2).

    ``write`` is derived from the class hierarchy (a :class:`WriteToolBase`
    subclass is always a write tool) so it cannot drift from the base contract.

    The permission is decoupled from the ``write``/``destructive`` flags so a
    tool could accidentally register a mutating handler under ``mcp.read`` (a
    silent privilege downgrade — a viewer-scoped key would then be allowed to
    write, SEC-006). We assert the invariant at import/registration time and
    fail fast (a wiring bug must never ship): a :class:`WriteToolBase` must never
    carry :attr:`McpPermission.READ`, and a ``destructive`` tool must be gated
    behind the admin-only :attr:`McpPermission.SETUP` class (AC-S6).
    """

    def _decorate(cls: type[ToolBase]) -> type[ToolBase]:
        is_write = issubclass(cls, WriteToolBase)
        if is_write and permission == McpPermission.READ:
            raise TypeError(
                f"MCP tool '{name}' is a write tool but declares McpPermission.READ — "
                "a mutating tool must be gated behind mcp.write or mcp.setup (SEC-006)."
            )
        if destructive and permission != McpPermission.SETUP:
            raise TypeError(
                f"MCP tool '{name}' is destructive but declares '{permission.value}' — "
                "a destructive tool must require the admin-only mcp.setup permission (SEC-006, AC-S6)."
            )

        cls.tool_name = name
        cls.permission = permission
        cls.destructive = destructive
        # cls.write comes from the ClassVar on ToolBase/WriteToolBase.
        from app.mcp_server.registry import registry

        registry.register(cls())
        return cls

    return _decorate
