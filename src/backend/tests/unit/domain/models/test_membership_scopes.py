"""INV-2: ``admin_scopes`` is duplicate-free and normalised (REQ-049 §5, #780)."""

from app.common.enums import AdminScope, TenantRole
from app.domain.models.membership import Membership


def _membership(scopes: list[AdminScope]) -> Membership:
    return Membership(user_key="u1", tenant_key="t1", role=TenantRole.GROWER, admin_scopes=scopes)


class TestScopeNormalisation:
    def test_duplicates_are_collapsed(self):
        m = _membership([AdminScope.MANAGEMENT, AdminScope.MANAGEMENT])

        assert m.admin_scopes == [AdminScope.MANAGEMENT]

    def test_order_is_normalised(self):
        # Two memberships conveying the same rights must compare and serialise
        # identically, not differ by the order someone ticked the boxes in.
        a = _membership([AdminScope.TECHNICAL, AdminScope.MANAGEMENT])
        b = _membership([AdminScope.MANAGEMENT, AdminScope.TECHNICAL])

        assert a.admin_scopes == b.admin_scopes

    def test_default_is_no_scopes(self):
        m = Membership(user_key="u1", tenant_key="t1")

        assert m.admin_scopes == []
        # A membership created without an explicit role reads, nothing more.
        assert m.role == TenantRole.VIEWER


class TestScopeProperties:
    def test_properties_reflect_the_list(self):
        m = _membership([AdminScope.TECHNICAL])

        assert m.has_technical is True
        assert m.has_management is False


class TestAxesAreIndependent:
    def test_every_combination_is_valid(self):
        # INV-3 — all six combinations exist in practice; a viewer with
        # MANAGEMENT is the club secretary.
        for role in (TenantRole.VIEWER, TenantRole.GROWER, TenantRole.LEAD):
            for scopes in ([], [AdminScope.MANAGEMENT], [AdminScope.MANAGEMENT, AdminScope.TECHNICAL]):
                m = Membership(user_key="u1", tenant_key="t1", role=role, admin_scopes=scopes)
                assert m.role == role
