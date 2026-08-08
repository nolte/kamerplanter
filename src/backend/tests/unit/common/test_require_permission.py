"""Unit tests for the app.common.auth.require_permission gate (REQ-024 §1a.6).

Drives the dependency's inner check with real :class:`TenantContext` objects
(not a mock that never becomes a model, #996) to pin the role→action mapping
onto :class:`MembershipEngine`, including the fail-closed default.
"""

import pytest

from app.common.auth import require_permission
from app.common.enums import TenantRole
from app.common.exceptions import ForbiddenError
from app.core.permissions import Action, ResourceType
from app.domain.models.tenant_context import TenantContext


def _ctx(role: TenantRole) -> TenantContext:
    return TenantContext(tenant_key="t", tenant_slug="s", user_key="u", role=role)


def _run(resource: ResourceType | str, action: Action, role: TenantRole) -> TenantContext:
    # The factory returns a FastAPI dependency whose only parameter (ctx) is
    # itself resolved from get_current_tenant; call the inner callable directly
    # with a concrete context to exercise the pure decision.
    dependency = require_permission(resource, action)
    return dependency(ctx=_ctx(role))


@pytest.mark.parametrize("action", [Action.CREATE, Action.UPDATE])
@pytest.mark.parametrize("role", [TenantRole.LEAD, TenantRole.GROWER])
def test_edit_allowed_for_lead_and_grower(action: Action, role: TenantRole) -> None:
    ctx = _run(ResourceType.PLANT, action, role)
    assert ctx.role is role


@pytest.mark.parametrize("action", [Action.CREATE, Action.UPDATE])
def test_edit_refused_for_viewer(action: Action) -> None:
    with pytest.raises(ForbiddenError):
        _run(ResourceType.PLANT, action, TenantRole.VIEWER)


def test_delete_allowed_only_for_lead() -> None:
    assert _run(ResourceType.PLANT, Action.DELETE, TenantRole.LEAD).role is TenantRole.LEAD
    for role in (TenantRole.GROWER, TenantRole.VIEWER):
        with pytest.raises(ForbiddenError):
            _run(ResourceType.PLANT, Action.DELETE, role)


@pytest.mark.parametrize("role", [TenantRole.LEAD, TenantRole.GROWER, TenantRole.VIEWER])
def test_read_open_to_every_member(role: TenantRole) -> None:
    assert _run(ResourceType.PLANT, Action.READ, role).role is role


def test_unmapped_verb_fails_closed() -> None:
    # INVITE belongs on the admin-scope axis, not this gate: it must be refused
    # for every domain role rather than silently allowed.
    for role in (TenantRole.LEAD, TenantRole.GROWER, TenantRole.VIEWER):
        with pytest.raises(ForbiddenError):
            _run(ResourceType.MEMBERSHIP, Action.INVITE, role)


def test_accepts_plain_string_resource_label() -> None:
    # Features without a ResourceType entry pass a kebab label for documentation.
    ctx = _run("feeding-event", Action.CREATE, TenantRole.GROWER)
    assert ctx.role is TenantRole.GROWER
    with pytest.raises(ForbiddenError):
        _run("feeding-event", Action.CREATE, TenantRole.VIEWER)
