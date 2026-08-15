"""REQ-033 MCP tool dispatcher (§4.2 – §4.6).

The single choke point every tool call passes through. In order:

1. resolve the tool from the registry (unknown → ``not_found``);
2. validate the typed input;
3. bind the acting tenant (§4.3): for a tenant-scoped tool, resolve the
   ``tenant`` argument against the principal's memberships. A tenant the caller
   is not a member of yields ``not_found`` — never ``permission.denied`` — so the
   interface cannot be used to probe which tenants exist (§8.8 Szenario 6);
4. enforce the tool's MCP permission against the role the caller holds **in that
   tenant** (§4.4) — a refusal is audited with ``status="denied"`` and raised as
   ``permission.denied``;
5. run the handler, applying dry-run + idempotency orchestration for write tools;
6. audit the outcome (hash-only, no PII, §4.6).

Steps 3 and 4 are in this order on purpose: a principal may be admin in its own
garden and viewer in a community garden, so the permission set is only knowable
once the acting tenant is known. Checking permissions first would grant the most
permissive role everywhere.

Business logic stays in the delegated domain services — the dispatcher only owns
security binding, idempotency and audit.
"""

from __future__ import annotations

import json
from time import perf_counter
from typing import Any

import structlog
from pydantic import ValidationError as PydanticValidationError

from app.common.enums import McpToolStatus, TenantRole
from app.common.error_ids import new_error_id
from app.common.exceptions import ForbiddenError, KamerplanterError, NotFoundError, ValidationError
from app.core.permissions import assert_mcp_permission
from app.domain.models.mcp import McpToolResponse
from app.mcp_server.audit import MCPAuditLogger, hash_arguments
from app.mcp_server.base import (
    INTERNAL_UNAVAILABLE,
    McpToolError,
    ToolBase,
    WriteToolBase,
    classify_internal_failure,
    internal_failure_message,
)
from app.mcp_server.context import ToolContext
from app.mcp_server.idempotency import IdempotencyStore
from app.mcp_server.principal import McpPrincipal, McpTenantMembership
from app.mcp_server.registry import ToolRegistry

logger = structlog.get_logger(__name__)


class ToolDispatcher:
    """Executes a named tool for an authenticated principal."""

    def __init__(
        self,
        registry: ToolRegistry,
        audit_logger: MCPAuditLogger,
        idempotency: IdempotencyStore,
        *,
        services: dict[str, Any] | None = None,
    ) -> None:
        self._registry = registry
        self._audit = audit_logger
        self._idempotency = idempotency
        self._services = services

    async def dispatch(
        self,
        principal: McpPrincipal,
        tool_name: str,
        raw_args: dict[str, Any] | None,
    ) -> McpToolResponse:
        raw_args = raw_args or {}
        input_hash = hash_arguments(raw_args)

        tool = self._registry.get(tool_name)
        if tool is None:
            raise NotFoundError("MCP tool", tool_name)
        assert isinstance(tool, ToolBase)

        # 1. Typed input validation.
        try:
            args = tool.Input(**raw_args)
        except PydanticValidationError as exc:
            self._audit.record(
                principal,
                tool_name=tool_name,
                input_hash=input_hash,
                status=McpToolStatus.ERROR,
                error_class="validation.input",
            )
            raise ValidationError(f"Invalid arguments for tool '{tool_name}': {exc.errors()}") from exc

        # 2. Acting-tenant binding (§4.3) — before any permission decision.
        membership = self._resolve_membership(principal, tool, args, tool_name, input_hash)

        # 3. Permission binding against the role held in *that* tenant (§4.4).
        #    A global tool has no tenant role to bind to, so it is admitted on the
        #    strongest role the principal holds anywhere; global tools are
        #    read-only catalogue lookups that every member may perform.
        effective_role = membership.role if membership is not None else _strongest_role(principal)
        try:
            assert_mcp_permission(effective_role, tool.permission)
        except ForbiddenError:
            self._audit.record(
                principal,
                tool_name=tool_name,
                input_hash=input_hash,
                status=McpToolStatus.DENIED,
                error_class="permission.denied",
                membership=membership,
            )
            raise

        ctx = ToolContext(principal, membership, services=self._services)
        started = perf_counter()
        try:
            response, status = await self._run(tool, ctx, args, principal, membership, tool_name, input_hash)
        except KamerplanterError as exc:
            self._audit.record(
                principal,
                tool_name=tool_name,
                input_hash=input_hash,
                status=McpToolStatus.ERROR,
                duration_ms=int((perf_counter() - started) * 1000),
                error_class=exc.error_code,
                membership=membership,
            )
            raise
        except Exception as exc:  # noqa: BLE001 — audit unexpected failures too
            self._audit.record(
                principal,
                tool_name=tool_name,
                input_hash=input_hash,
                status=McpToolStatus.ERROR,
                duration_ms=int((perf_counter() - started) * 1000),
                error_class=type(exc).__name__,
                membership=membership,
            )
            raise self._as_internal_tool_error(exc, tool_name) from exc

        duration_ms = int((perf_counter() - started) * 1000)
        # AC-S9 — image payload is reported *separately*, not folded into
        # output_size_bytes. ``to_payload()`` excludes the content blocks, so the
        # existing metric keeps measuring the same thing it measured for the 12
        # text-only tools and stays comparable across the whole palette; a single
        # 4 MB photo call can no longer drown every other tool's statistic.
        # Capping the combined number instead would have been the other sanctioned
        # option, but it destroys information: a capped 4 MB call and a capped
        # 40 MB one look alike, and the structured part becomes unreadable behind
        # the cap. Both fields are sizes — never image data (AC-S5).
        output_size = len(json.dumps(response.to_payload(), default=str).encode())
        self._audit.record(
            principal,
            tool_name=tool_name,
            input_hash=input_hash,
            status=status,
            output_size_bytes=output_size,
            image_bytes=response.image_payload_bytes(),
            duration_ms=duration_ms,
            membership=membership,
        )
        return response

    def _resolve_membership(
        self,
        principal: McpPrincipal,
        tool: ToolBase,
        args: Any,
        tool_name: str,
        input_hash: str,
    ) -> McpTenantMembership | None:
        """Bind the call to exactly one tenant the principal is a member of (§4.3).

        Returns ``None`` for a tenant-agnostic tool (global catalogue data).

        A named tenant the principal is *not* a member of is reported as
        ``not_found`` — identical to a tenant that does not exist at all — so the
        MCP interface cannot be walked to enumerate foreign tenants (§8.8
        Szenario 6). An omitted tenant on a principal holding several
        memberships is a caller error, not a licence to pick one.
        """

        if not tool.tenant_scoped:
            return None

        requested = getattr(args, "tenant", None)
        membership = principal.membership_for(requested)
        if membership is not None:
            return membership

        if requested is None:
            # Its own contract code (REQ-050 §4.0): "you forgot the tenant" is the
            # one validation failure a recipe can *fix* by retrying with a slug.
            # Distinguishing it by parsing the message would be exactly the
            # message-branching the contract forbids.
            raise McpToolError(
                "validation.tenant_required",
                f"Tool '{tool_name}' acts inside one tenant and this API key grants "
                f"{len(principal.memberships)}. Pass 'tenant' — use list_tenants to see the options.",
            )

        self._audit.record(
            principal,
            tool_name=tool_name,
            input_hash=input_hash,
            status=McpToolStatus.DENIED,
            error_class="not_found",
        )
        raise NotFoundError("Tenant", requested)

    @staticmethod
    def _as_internal_tool_error(exc: BaseException, tool_name: str) -> McpToolError:
        """Turn an unexpected exception into a *typed* genuine-500 result (#1164).

        Before this, both #1145 defects — a ``TypeError`` from a missed keyword
        argument and a ``pydantic.ValidationError`` from a schema mismatch — fell
        through to the REST catch-all and reached the operator as
        ``INTERNAL_ERROR`` plus a bare reference ID. Five such IDs were collected
        across two tools before anyone could say more than "something is wrong",
        and because they were identical the two unrelated defects read as one
        incident. The reference ID is only actionable to someone holding the
        server logs, which for an MCP client is nobody in the loop.

        What is added is deliberately the *smallest* thing that lets a caller act:
        a stable class saying whether retrying can ever help, plus the tool name.
        What is deliberately **not** added:

        * **No 4xx.** These stay 500. A domain validation error caused by a bad
          request is typed and 4xx; one caused by our own code assembling
          something wrongly is a genuine server fault and must stay loud (#970's
          second horn). Reclassifying would have made #1145 quieter and no less
          broken.
        * **No exception text.** A ``TypeError`` repr names internal symbols and a
          ``ValidationError`` can quote stored field values. The message is a
          fixed sentence per class.
        * **No phase or symbol.** Localising further needs the log, and the
          reference ID is what joins the two.

        The reference ID is minted and logged *here*, so the value the caller is
        told to report is the value that appears in the log line — raising an
        ``McpToolError`` means the REST catch-all that used to mint it no longer
        runs.
        """
        error_code = classify_internal_failure(exc)
        reference_id = new_error_id()
        logger.error(
            "mcp_tool_internal_failure",
            error_id=reference_id,
            tool=tool_name,
            error_code=error_code,
            exc_info=True,
        )
        return McpToolError(
            error_code,
            internal_failure_message(error_code),
            details={
                "reference_id": reference_id,
                "tool": tool_name,
                # Explicit rather than implied by the code, so a client that does
                # not know this vocabulary yet still has the one bit it needs.
                "retryable": error_code == INTERNAL_UNAVAILABLE,
            },
        )

    async def _run(
        self,
        tool: ToolBase,
        ctx: ToolContext,
        args: Any,
        principal: McpPrincipal,
        membership: McpTenantMembership | None,
        tool_name: str,
        input_hash: str,
    ) -> tuple[McpToolResponse, McpToolStatus]:
        if not isinstance(tool, WriteToolBase):
            return await tool.run(ctx, args), McpToolStatus.OK

        # ── Write tool: dry-run + idempotency (§2.6) ─────────────────────
        if getattr(args, "dry_run", False):
            response = await tool.preview(ctx, args)
            response.dry_run = True
            response.idempotency_key = getattr(args, "idempotency_key", None)
            response.idempotent_replay = False
            return response, McpToolStatus.DRY_RUN

        idem_key = getattr(args, "idempotency_key", None)
        if idem_key:
            replay = self._idempotency.lookup(principal, membership, tool_name, idem_key)
            if replay is not None:
                return replay, McpToolStatus.OK
            response = await tool.execute(ctx, args)
            response.dry_run = False
            response.idempotency_key = idem_key
            response.idempotent_replay = False
            self._idempotency.store(principal, membership, tool_name, idem_key, input_hash, response)
            return response, McpToolStatus.OK

        response = await tool.execute(ctx, args)
        response.dry_run = False
        return response, McpToolStatus.OK


def _strongest_role(principal: McpPrincipal) -> TenantRole:
    """The most permissive role the principal holds in any tenant.

    Only used to admit tenant-agnostic tools, which read global catalogue data
    (species and friends) that carries no tenant and is visible to every member.
    """

    roles = principal.roles()
    for candidate in (TenantRole.LEAD, TenantRole.GROWER, TenantRole.VIEWER):
        if candidate in roles:
            return candidate
    return TenantRole.VIEWER
