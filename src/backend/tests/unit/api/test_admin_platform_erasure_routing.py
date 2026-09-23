"""Unit tests for SEC-002 / SEC-003 — admin platform delete endpoints route
through the NFR-013 / REQ-025 pipelines, entirely via the service layer (#1019).

The endpoint functions are exercised directly (the ``Depends`` defaults are not
evaluated on a direct call), with the injected services mocked. After #1019 the
router holds no ``get_db``: the tenant existence / ``is_platform`` guard reads
through ``TenantService.get_tenant``. Since #1664 the user delete makes exactly
one erasure call, ``PrivacyService.erase_account`` — the shared entry that runs
the SEC-003 storage phases *and* the declared ArangoDB plan in the right order
(pinned in ``tests/unit/domain/services/test_privacy_erase_account.py``).
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.api.v1.admin.platform import router as mod
from app.common.exceptions import ForbiddenError, NotFoundError


class TestDeleteTenantRouting:
    """SEC-002 — admin tenant delete must go through TenantService.delete_tenant."""

    def test_routes_tenant_delete_through_service(self):
        tenant_service = MagicMock()
        tenant_service.get_tenant.return_value = SimpleNamespace(is_platform=False)

        mod.delete_tenant("t-1", _user=None, tenant_service=tenant_service)

        tenant_service.get_tenant.assert_called_once_with("t-1")
        tenant_service.delete_tenant.assert_called_once_with("t-1")

    def test_rejects_platform_tenant(self):
        tenant_service = MagicMock()
        tenant_service.get_tenant.return_value = SimpleNamespace(is_platform=True)

        with pytest.raises(ForbiddenError):
            mod.delete_tenant("t-0", _user=None, tenant_service=tenant_service)

        tenant_service.delete_tenant.assert_not_called()

    def test_missing_tenant_raises_not_found(self):
        tenant_service = MagicMock()
        tenant_service.get_tenant.side_effect = NotFoundError("Tenant", "ghost")

        with pytest.raises(NotFoundError):
            mod.delete_tenant("ghost", _user=None, tenant_service=tenant_service)

        tenant_service.delete_tenant.assert_not_called()


class TestDeleteUserRouting:
    """#1664 — admin user delete runs the one shared erasure entry, nothing beside it."""

    def test_routes_user_delete_through_the_shared_erasure_entry(self):
        calls: list[str] = []

        async def _erase(user_key):
            calls.append(user_key)

        privacy_service = MagicMock()
        privacy_service.erase_account.side_effect = _erase

        user_service = MagicMock()
        user_service.get_user.return_value = SimpleNamespace(key="u-1")

        current = SimpleNamespace(key="admin-9")
        mod.delete_user("u-1", current_user=current, privacy_service=privacy_service, user_service=user_service)

        # The coroutine was awaited, not merely created.
        assert calls == ["u-1"]
        privacy_service.erase_account.assert_called_once_with("u-1")
        # No second, partial erasure beside the shared one (the pre-#1664 shape
        # ran the storage phases and a narrow cascade as two separate calls).
        privacy_service.run_user_storage_erasure.assert_not_called()

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

        privacy_service.erase_account.assert_not_called()

    def test_missing_user_raises_not_found(self):
        privacy_service = MagicMock()
        user_service = MagicMock()
        user_service.get_user.side_effect = NotFoundError("User", "ghost")

        current = SimpleNamespace(key="admin-9")
        with pytest.raises(NotFoundError):
            mod.delete_user("ghost", current_user=current, privacy_service=privacy_service, user_service=user_service)

        privacy_service.erase_account.assert_not_called()
