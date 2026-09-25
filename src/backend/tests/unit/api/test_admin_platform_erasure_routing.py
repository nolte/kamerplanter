"""Unit tests for SEC-002 / SEC-003 — admin platform delete endpoints route
through the NFR-013 / REQ-025 pipelines, entirely via the service layer (#1019).

The endpoint functions are exercised directly (the ``Depends`` defaults are not
evaluated on a direct call), with the injected services mocked. After #1019 the
router holds no ``get_db``; since #1769 the tenant existence / ``is_platform``
guard lives in ``TenantService.delete_tenant`` itself. Since #1664 the user delete makes exactly
one erasure call — since #1767 ``PrivacyService.erase_account_now``, which
persists the request and runs ``erase_account``, the shared entry that runs
the SEC-003 storage phases *and* the declared ArangoDB plan in the right order
(pinned in ``tests/unit/domain/services/test_privacy_erase_account.py``).
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, call

import pytest

from app.api.v1.admin.platform import router as mod
from app.common.exceptions import ForbiddenError, NotFoundError


class TestDeleteTenantRouting:
    """SEC-002 / #1769 — both tenant-delete routes run the one service entry, nothing beside it.

    The platform-tenant refusal and the 404 live in ``TenantService.delete_tenant``
    (``test_tenant_erasure_service.py``), so the tenant-scoped route is guarded the
    same way — it had no platform check of its own before #1769.
    """

    def test_admin_route_runs_the_service_deletion_as_platform_admin(self):
        tenant_service = MagicMock()

        mod.delete_tenant("t-1", _user=None, tenant_service=tenant_service)

        assert tenant_service.mock_calls == [call.delete_tenant("t-1", origin="platform_admin")]

    def test_tenant_route_runs_the_service_deletion_as_tenant_management(self):
        from app.api.v1.tenants import router as tenant_router

        service = MagicMock()

        tenant_router.delete_tenant(ctx=SimpleNamespace(tenant_key="t-2"), service=service)

        assert service.mock_calls == [call.delete_tenant("t-2", origin="tenant_management")]

    def test_a_service_refusal_reaches_the_caller(self):
        tenant_service = MagicMock()
        tenant_service.delete_tenant.side_effect = ForbiddenError("The platform tenant cannot be deleted.")

        with pytest.raises(ForbiddenError):
            mod.delete_tenant("t-0", _user=None, tenant_service=tenant_service)


class TestDeleteUserRouting:
    """#1664 — admin user delete runs the one shared erasure entry, nothing beside it."""

    def test_routes_user_delete_through_the_shared_erasure_entry(self):
        calls: list[tuple[str, str]] = []

        async def _erase(user_key, *, origin):
            calls.append((user_key, origin))

        privacy_service = MagicMock()
        privacy_service.erase_account_now.side_effect = _erase

        user_service = MagicMock()
        user_service.get_user.return_value = SimpleNamespace(key="u-1")

        current = SimpleNamespace(key="admin-9")
        mod.delete_user("u-1", current_user=current, privacy_service=privacy_service, user_service=user_service)

        # The coroutine was awaited, not merely created — through the immediate
        # entry that persists the erasure record (#1767), not the bare run.
        assert calls == [("u-1", "platform_admin")]
        # No second, partial erasure beside the shared one (the pre-#1664 shape
        # ran the storage phases and a narrow cascade as two separate calls).
        # Read off every call the route made, not off one method name: the
        # storage-only entry it used to call no longer exists (#1645).
        assert [name for name, _args, _kwargs in privacy_service.method_calls] == ["erase_account_now"]

    def test_the_route_no_longer_reaches_a_separate_cascade(self):
        """The service method the route used to call beside the storage erasure is gone."""
        from app.domain.services.user_service import UserService

        assert not hasattr(UserService, "delete_account_permanently")

    def test_cannot_delete_self(self):
        privacy_service = MagicMock()
        user_service = MagicMock()
        user_service.get_user.return_value = SimpleNamespace(key="admin-9")

        current = SimpleNamespace(key="admin-9")
        with pytest.raises(ForbiddenError):
            mod.delete_user("admin-9", current_user=current, privacy_service=privacy_service, user_service=user_service)

        privacy_service.erase_account_now.assert_not_called()

    def test_missing_user_raises_not_found(self):
        privacy_service = MagicMock()
        user_service = MagicMock()
        user_service.get_user.side_effect = NotFoundError("User", "ghost")

        current = SimpleNamespace(key="admin-9")
        with pytest.raises(NotFoundError):
            mod.delete_user("ghost", current_user=current, privacy_service=privacy_service, user_service=user_service)

        privacy_service.erase_account_now.assert_not_called()
