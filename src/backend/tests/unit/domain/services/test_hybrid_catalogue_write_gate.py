"""The shared hybrid-catalogue write gate answers the same four arms for every catalogue (#2100)."""

from __future__ import annotations

import pytest

from app.common.enums import TenantRole
from app.common.exceptions import ForbiddenError, NotFoundError
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.services.catalogue_authorization import authorize_hybrid_catalogue_write


def _gate(owner: str, *, tenant: str | None = "t1", role: TenantRole | None = TenantRole.GROWER, admin: bool = False):
    authorize_hybrid_catalogue_write(
        owner,
        entity="Fertilizer",
        plural_noun="fertilizers",
        key="k",
        tenant_key=tenant,
        caller_role=role,
        is_platform_admin=admin,
        can_role_write=MembershipEngine.can_edit_resource,
    )


def test_the_system_context_passes() -> None:
    _gate("anyone", tenant=None, role=None)


def test_a_foreign_row_is_not_found_even_for_a_platform_admin() -> None:
    with pytest.raises(NotFoundError):
        _gate("t2")
    with pytest.raises(NotFoundError):
        _gate("t2", admin=True)


def test_a_global_row_is_a_platform_admins() -> None:
    with pytest.raises(ForbiddenError):
        _gate("", role=TenantRole.LEAD)
    _gate("", role=TenantRole.VIEWER, admin=True)


def test_an_own_row_needs_a_writing_role() -> None:
    _gate("t1", role=TenantRole.GROWER)
    with pytest.raises(ForbiddenError):
        _gate("t1", role=TenantRole.VIEWER)
