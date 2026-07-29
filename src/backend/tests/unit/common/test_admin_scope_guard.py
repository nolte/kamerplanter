"""REQ-049 axis 2: the administrative-scope dependency (#780).

``require_admin_scope`` is the second, deliberately *disjoint* enforcement path
next to ``require_tenant_role``. The cases below pin the property the whole
split exists for: the two axes do not imply each other in either direction.
"""

import pytest

from app.common.auth import require_admin_scope, require_tenant_role
from app.common.enums import AdminScope, TenantRole
from app.common.exceptions import ForbiddenError
from app.domain.models.tenant_context import TenantContext


def _ctx(role: TenantRole, scopes: list[AdminScope]) -> TenantContext:
    return TenantContext(
        tenant_key="t1",
        tenant_slug="garden",
        user_key="u1",
        role=role,
        admin_scopes=scopes,
    )


class TestRequireAdminScope:
    def test_holder_passes(self):
        ctx = _ctx(TenantRole.VIEWER, [AdminScope.MANAGEMENT])

        assert require_admin_scope(AdminScope.MANAGEMENT)(ctx=ctx) is ctx

    def test_a_lead_without_the_scope_is_rejected(self):
        # The top domain rank grants nothing on axis 2. Without this, "lead"
        # would quietly become the old "admin" again.
        ctx = _ctx(TenantRole.LEAD, [])

        with pytest.raises(ForbiddenError):
            require_admin_scope(AdminScope.MANAGEMENT)(ctx=ctx)

    def test_the_other_scope_does_not_substitute(self):
        # Authority over people and access to technology come apart in practice.
        ctx = _ctx(TenantRole.LEAD, [AdminScope.TECHNICAL])

        with pytest.raises(ForbiddenError):
            require_admin_scope(AdminScope.MANAGEMENT)(ctx=ctx)

    def test_error_names_the_missing_scope(self):
        ctx = _ctx(TenantRole.GROWER, [])

        with pytest.raises(ForbiddenError, match="technical"):
            require_admin_scope(AdminScope.TECHNICAL)(ctx=ctx)


class TestAxesAreIndependent:
    def test_a_scope_holder_does_not_gain_domain_rank(self):
        # A viewer holding both scopes still may not create a plant.
        ctx = _ctx(TenantRole.VIEWER, [AdminScope.MANAGEMENT, AdminScope.TECHNICAL])

        with pytest.raises(ForbiddenError):
            require_tenant_role(TenantRole.GROWER)(ctx=ctx)

    def test_domain_rank_still_works_on_its_own_axis(self):
        ctx = _ctx(TenantRole.GROWER, [])

        assert require_tenant_role(TenantRole.GROWER)(ctx=ctx) is ctx


class TestTenantContextProperties:
    def test_can_delete_is_lead_only(self):
        assert _ctx(TenantRole.LEAD, []).can_delete is True
        assert _ctx(TenantRole.GROWER, []).can_delete is False
        assert _ctx(TenantRole.VIEWER, []).can_delete is False

    def test_can_edit_covers_grower_and_lead(self):
        assert _ctx(TenantRole.LEAD, []).can_edit is True
        assert _ctx(TenantRole.GROWER, []).can_edit is True
        assert _ctx(TenantRole.VIEWER, []).can_edit is False

    def test_scope_properties_read_axis_two_only(self):
        ctx = _ctx(TenantRole.VIEWER, [AdminScope.TECHNICAL])
        assert ctx.has_technical is True
        assert ctx.has_management is False
