"""NFR-013 / REQ-024 — FastAPI permission guards for attachment endpoints.

Bridges the REQ-024 RBAC matrix (``app.core.permissions``) to FastAPI's
dependency system: each factory resolves the caller's ``TenantRole`` from the
``TenantContext`` (already validated by ``get_current_tenant``) and asserts the
required (resource, action) against the matrix, raising ``ForbiddenError`` (403)
when denied.

A ``viewer`` may READ attachments but not CREATE or DELETE them (REQ-024 §4).
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends

from app.common.auth import get_current_tenant
from app.common.exceptions import ForbiddenError
from app.core.permissions import Action, ResourceType, has_permission
from app.domain.models.tenant_context import TenantContext


def require_attachment_permission(action: Action) -> Callable[..., TenantContext]:
    """Return a dependency asserting ``action`` on ``ATTACHMENT`` for the caller."""

    def _dependency(ctx: TenantContext = Depends(get_current_tenant)) -> TenantContext:
        if not has_permission(ctx.role, ResourceType.ATTACHMENT, action):
            raise ForbiddenError(f"Tenant role '{ctx.role.value}' may not '{action.value}' attachments.")
        return ctx

    return _dependency
