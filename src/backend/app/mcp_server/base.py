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

from collections.abc import Sequence
from typing import Any, ClassVar

from pydantic import BaseModel, Field

from app.common.enums import McpPermission
from app.common.exceptions import KamerplanterError
from app.domain.models.mcp import McpImageContent, McpToolLink, McpToolResponse, McpToolSpec
from app.mcp_server.context import ToolContext

#: The leading ``content`` block is always the ``summary`` text (REQ-033 §4.3b),
#: so the first image a tool appends lands at wire index 1.
FIRST_IMAGE_CONTENT_INDEX = 1

#: HTTP status per contract error code, for the non-protocol REST alias
#: (``POST /mcp/tools/{name}``). On the MCP wire the status is irrelevant — there
#: the failure is a *result* with ``isError: true`` (REQ-050 §4.0).
_ERROR_CODE_STATUS: dict[str, int] = {
    "not_found": 404,
    "permission.denied": 403,
}
_ERROR_PREFIX_STATUS: tuple[tuple[str, int], ...] = (
    ("conflict.", 409),
    ("payload.", 413),
    ("validation.", 422),
)


def image_content_index(position: int) -> int:
    """Wire ``content`` index of the image at ``position`` (0-based) in a response.

    A tool records this as ``content_index`` next to the photo's id so a recipe
    maps block to identifier explicitly instead of counting positions — the
    mapping must survive a further text block being added later (REQ-050 §4.4).
    """

    return FIRST_IMAGE_CONTENT_INDEX + position


def _http_status_for(error_code: str) -> int:
    """Map a contract error code to the HTTP status of the REST alias."""

    if error_code in _ERROR_CODE_STATUS:
        return _ERROR_CODE_STATUS[error_code]
    for prefix, status in _ERROR_PREFIX_STATUS:
        if error_code.startswith(prefix):
            return status
    return 422


class McpToolError(KamerplanterError):
    """A tool failure carrying the machine-readable MCP error contract (REQ-050 §4.0).

    Raise this whenever a documented ``error_code`` from REQ-050 §4.1–§4.5 must
    reach the caller — ``conflict.already_claimed``, ``payload.too_large``,
    ``validation.tenant_required`` and friends. The transport turns it into a
    tool *result* with ``isError: true`` and a ``structuredContent`` holding
    ``error_code``, ``message`` and ``details``. A recipe branches on
    ``error_code`` and never on ``message``, which is free to change.

    Why a dedicated class rather than the existing ``ValidationError`` and
    friends: those carry Kamerplanter's internal, SCREAMING_CASE codes
    (``VALIDATION_ERROR``) and a ``details`` **list** in the NFR-006
    ``ErrorResponse`` shape. The MCP contract needs lowercase dotted codes and a
    free-form ``details`` **object** (``claimed_by``, ``lease_expires_at``, …).
    Both are served here: :attr:`error_details` keeps the object for the MCP
    wire, while the inherited ``details`` list keeps the REST alias
    NFR-006-conformant.
    """

    def __init__(
        self,
        error_code: str,
        message: str,
        *,
        details: dict[str, Any] | None = None,
        status_code: int | None = None,
    ) -> None:
        #: The MCP-wire ``details`` object — original value types preserved.
        self.error_details: dict[str, Any] = dict(details or {})
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code or _http_status_for(error_code),
            # Projection into the NFR-006 detail list; values are stringified
            # because ErrorDetail is str-typed. The MCP wire uses error_details.
            details=[
                {"field": key, "reason": str(value), "code": error_code} for key, value in self.error_details.items()
            ],
        )


class ToolInput(BaseModel):
    """Base class for a tool's typed input arguments.

    Use this directly only for tools operating on **global** data (the species
    catalogue and friends), which carry no tenant. Anything touching a user's
    own records takes :class:`TenantToolInput`.
    """

    model_config = {"extra": "forbid"}


class TenantToolInput(ToolInput):
    """Input base for tools acting inside one tenant (§4.3).

    A principal may be a member of several tenants. ``tenant`` names the one this
    call acts in; it may be omitted only when the principal has exactly one
    membership. The dispatcher resolves it against the principal's memberships
    *before* the handler runs — a tool never sees, and cannot act on, a tenant
    the caller is not a member of.
    """

    tenant: str | None = Field(
        default=None,
        description=(
            "Slug of the tenant to act in. Optional when the API key grants exactly one tenant; "
            "required otherwise. Use the list_tenants tool to discover the available slugs."
        ),
    )


class CatalogueToolInput(ToolInput):
    """Input base for a *hybrid-catalogue* read: global rows plus one tenant's own (#1121).

    Deliberately **not** :class:`TenantToolInput`, and the difference is the whole
    point of this class existing.

    ``TenantToolInput`` makes a tool tenant-*scoped*: the dispatcher binds a
    membership before the handler runs, and a principal holding several
    memberships that omits ``tenant`` is refused with ``validation.tenant_required``.
    That is right for a tool that acts *inside* a tenant — there is no sensible
    default for "which garden did you mean". It is wrong here. The species and
    cultivar catalogues have a meaningful answer with no tenant at all: the shared
    seed catalogue, which is what these tools returned before #1121 and what every
    existing client is calling them for. Promoting them to ``TenantToolInput``
    would turn a working global-only call into an error for exactly those clients
    — the back-compatibility this issue's acceptance criteria rule out.

    So ``tenant`` here is a *widening*, not a binding:

    * omitted → the global catalogue (``tenant_key == ""``), unchanged behaviour;
    * a slug the principal is a member of → global ∪ that tenant's own rows, the
      #324 both-direction union the HTTP routes apply since #1091;
    * a slug the principal is **not** a member of → ``not_found``, identical to a
      slug that names no tenant, so the tool cannot be walked to enumerate
      tenants (§8.8 Szenario 6).

    Note the asymmetry that keeps this safe: *absence* narrows to global-only, a
    *rejected* value fails the call, and only a validated slug widens anything.
    That is the same rule REQ-049 §2.11 states for ``X-Active-Tenant``, which is
    what makes the two surfaces answer alike.
    """

    tenant: str | None = Field(
        default=None,
        description=(
            "Slug of the tenant whose own catalogue entries should be included alongside the "
            "shared ones. Omit for the shared catalogue only. Use list_tenants to discover slugs."
        ),
    )


class _WriteFields(BaseModel):
    """The two fields every write tool carries — dry-run preview + idempotency (§2.6)."""

    dry_run: bool = Field(
        default=False,
        description="Return the planned effect without persisting anything.",
    )
    idempotency_key: str | None = Field(
        default=None,
        description="Repeating a call with the same key within 24h replays the original result.",
    )


class WriteToolInput(TenantToolInput, _WriteFields):
    """Input base for a write tool acting inside one tenant (the usual case)."""


class GlobalWriteToolInput(ToolInput, _WriteFields):
    """Input base for a write tool on global, tenant-independent data.

    Only for the shared catalogue (e.g. creating a species every tenant sees).
    Anything touching a user's own records uses :class:`WriteToolInput` instead.
    """


class ToolBase:
    """Base class for every MCP tool.

    Subclasses set :attr:`tool_name`/:attr:`permission` via the :func:`mcp_tool`
    decorator, declare a nested ``Input`` model and implement :meth:`run`.
    """

    tool_name: ClassVar[str] = ""
    permission: ClassVar[McpPermission] = McpPermission.READ
    write: ClassVar[bool] = False
    destructive: ClassVar[bool] = False
    #: Derived from the Input model — never set by hand (see __init_subclass__).
    tenant_scoped: ClassVar[bool] = False
    Input: ClassVar[type[ToolInput]] = ToolInput

    def __init_subclass__(cls, **kwargs) -> None:
        """Derive :attr:`tenant_scoped` from the tool's declared ``Input``.

        Done here rather than in :func:`mcp_tool` so it holds for *every* tool
        class, including any registered directly against a registry. The flag is
        what the dispatcher keys tenant binding on: if it could drift from the
        Input model, a tool taking a ``tenant`` argument might run with no tenant
        bound at all — the exact failure this derivation makes impossible.
        """

        super().__init_subclass__(**kwargs)
        cls.tenant_scoped = issubclass(cls.Input, TenantToolInput)

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

    @staticmethod
    def _image_response(
        summary: str,
        images: Sequence[tuple[bytes, str]],
        data: dict | None = None,
        links: list[dict[str, str]] | None = None,
    ) -> McpToolResponse:
        """Build a response whose images travel as MCP content blocks (§4.3b).

        ``images`` are ``(raw_rendition_bytes, mime_type)`` pairs **in delivery
        order**; Base-64 encoding happens here so no tool builds a content block
        by hand. The transport prepends the ``summary`` text block, so the image
        at position *i* appears at wire index :func:`image_content_index`\\ ``(i)``.

        The bytes must come from a WebP rendition (NFR-013 §8.2), never from an
        original upload (AC-S7). They deliberately do **not** enter ``data``:
        ``to_payload()`` feeds both ``structuredContent`` and the persisted
        idempotency record, and neither may carry image payload.
        """

        response = ToolBase._response(summary, data, links)
        response.content_blocks = [McpImageContent.from_bytes(raw, mime_type) for raw, mime_type in images]
        return response

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

    ``tenant_scoped`` is likewise derived, but from the class definition itself
    (:meth:`ToolBase.__init_subclass__`) so it also holds for a tool registered
    without this decorator.
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
        # cls.write comes from the ClassVar on ToolBase/WriteToolBase,
        # cls.tenant_scoped from ToolBase.__init_subclass__.
        from app.mcp_server.registry import registry

        registry.register(cls())
        return cls

    return _decorate
