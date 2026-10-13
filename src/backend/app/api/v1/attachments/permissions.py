"""NFR-013 / REQ-024 — FastAPI permission guards for attachment endpoints.

Each factory resolves the caller's ``TenantRole`` from the ``TenantContext``
(already validated by ``get_current_tenant``) and decides the action through
:func:`app.common.auth.role_permits` — the decision ``require_permission`` takes
for every other router (MT-045.6, #2144: until then this guard read the
descriptive matrix ``app.core.permissions`` instead, a second source nothing
compared). Refusal is ``ForbiddenError`` (403).

A ``viewer`` may READ attachments but not CREATE or DELETE them (REQ-024 §4).
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends

from app.common.auth import get_current_tenant, role_permits
from app.common.exceptions import ForbiddenError
from app.core.permissions import Action
from app.domain.models.tenant_context import TenantContext


def require_attachment_permission(action: Action) -> Callable[..., TenantContext]:
    """Return a dependency asserting ``action`` on ``ATTACHMENT`` for the caller."""

    def _dependency(ctx: TenantContext = Depends(get_current_tenant)) -> TenantContext:
        if not role_permits(ctx.role, action):
            raise ForbiddenError(f"Tenant role '{ctx.role.value}' may not '{action.value}' attachments.")
        return ctx

    return _dependency
